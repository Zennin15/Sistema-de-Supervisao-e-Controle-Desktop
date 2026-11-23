import logging
import os
import sqlite3

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import QDialog, QLabel, QMessageBox

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from controllers.consulta_historico_worker import ConsultaHistoricoWorker
from database.connection import Database
from logs.logger import registrar_erro_emergencia
from models.config_manager import carregar_ou_criar_config
from models.repository import (
    ActuatorRepository,
    LimitRepository,
    Repository,
    TAG_DISJUNTOR_PRINCIPAL,
    TAG_RELE_EMERGENCIA,
)
from models.telemetry_model import TelemetryModel
from ui.dashboard_window import Ui_DashboardWindow
from ui.painel_grafico_view import PainelGraficoView


class DashboardWindowController(QDialog):
    """Controller do dashboard, incluindo a persistência dos comandos e alarmes."""

    COR_LED_FECHADO = "#00E676"
    COR_LED_ABERTO = "#D32F2F"

    # A tela principal escuta esse sinal para recarregar a tabela apos o commit.
    historico_atualizado = Signal()

    def __init__(self, parent=None, worker_ativo=None):
        super().__init__(parent)

        self.ui = Ui_DashboardWindow()
        self.ui.setupUi(self)
        self.model = TelemetryModel()
        self._alerta_ativo = False
        self._alerta_tensao_ativo = False
        self._alerta_corrente_ativo = False
        self.worker_ativo = worker_ativo
        self._amostra_pendente = None
        self._leitura_bruta = None
        self._modo_grafico = "tempo_real"
        self._worker_historico = None
        self._carregar_estado_persistido()
        self._carregar_limites_seguranca()

        self._configurar_grafico()
        self._configurar_alertas_seguranca()
        self._configurar_painel_historico()
        self._carregar_estado_inicial()

        self.ui.botaoVoltar.clicked.connect(self.close)
        self.ui.botaoCorteEmergencial.clicked.connect(self.acionar_corte_emergencial)
        self.ui.sliderLimiteAlerta.valueChanged.connect(self.ajustar_limite_alerta)

        # A serial pode entregar pacotes bem mais rápido do que a tela precisa
        # redesenhar. O recebimento fica barato (só guarda a última amostra) e
        # este timer, no ritmo configurado (taxa_amostragem_ms), é quem de fato
        # processa e redesenha - evita sobrecarregar o matplotlib/GUI thread.
        taxa_amostragem_ms = carregar_ou_criar_config().get("taxa_amostragem_ms", 1000)
        self.timer_telemetria = QTimer(self)
        self.timer_telemetria.setInterval(max(100, int(taxa_amostragem_ms)))
        self.timer_telemetria.timeout.connect(self._processar_amostra_pendente)
        self.timer_telemetria.start()

        if self.worker_ativo is not None and self.worker_ativo.isRunning():
            self.worker_ativo.dados_recebidos.connect(self._on_pacote_serial_recebido)
            self.ui.labelStatus.setText("Status: aguardando dados da porta serial...")
        else:
            self.ui.labelStatus.setText(
                "Status: sem conexão serial - abra Configurações para conectar"
            )

    def _carregar_estado_persistido(self):
        """Sincroniza o estado inicial do disjuntor com o banco."""
        try:
            atuador = ActuatorRepository.obter_por_tag(TAG_DISJUNTOR_PRINCIPAL)
            if atuador:
                self.model.disjuntor_fechado = atuador["status"] == "FECHADO"
                if not self.model.disjuntor_fechado:
                    self.model.registrar_amostra(0.0, 0.0)
        except sqlite3.Error:
            logging.exception("Não foi possível carregar o estado persistido do disjuntor.")

    def _carregar_limites_seguranca(self):
        """Carrega os limites de tensão/corrente cadastrados (tela de
        Limites) e aplica o mais restritivo de cada um como limite de
        segurança monitorado pelo Model."""
        try:
            limites = LimitRepository.listar_todos()
        except sqlite3.Error:
            logging.exception("Falha ao carregar limites de tensão/corrente.")
            limites = []

        tensoes = [float(l["Tensao"]) for l in limites if l.get("Tensao")]
        correntes = [float(l["Corrente"]) for l in limites if l.get("Corrente")]
        self.model.set_limites_seguranca(
            min(tensoes) if tensoes else None,
            min(correntes) if correntes else None,
        )

    def _configurar_alertas_seguranca(self):
        """Cria os labels de alerta de tensão/corrente, logo abaixo do
        alerta de consumo já existente."""
        self.labelAlertaTensao = QLabel(
            "⚠ TENSÃO ACIMA DO LIMITE DE SEGURANÇA!", self
        )
        self.labelAlertaTensao.setStyleSheet("QLabel { color: #D32F2F; font-weight: bold; }")
        self.labelAlertaTensao.setAlignment(Qt.AlignCenter)
        self.labelAlertaTensao.setVisible(False)

        self.labelAlertaCorrente = QLabel(
            "⚠ CORRENTE ACIMA DO LIMITE DE SEGURANÇA!", self
        )
        self.labelAlertaCorrente.setStyleSheet("QLabel { color: #D32F2F; font-weight: bold; }")
        self.labelAlertaCorrente.setAlignment(Qt.AlignCenter)
        self.labelAlertaCorrente.setVisible(False)

        indice = self.ui.verticalLayoutPrincipal.indexOf(self.ui.labelAlerta) + 1
        self.ui.verticalLayoutPrincipal.insertWidget(indice, self.labelAlertaTensao)
        self.ui.verticalLayoutPrincipal.insertWidget(indice + 1, self.labelAlertaCorrente)

    def _configurar_painel_historico(self):
        """Embute o painel de filtros (tempo real / consulta de histórico)
        acima do gráfico principal, compartilhando o mesmo canvas."""
        self.painel_grafico = PainelGraficoView(self)
        self.ui.verticalLayoutGrafico.insertWidget(0, self.painel_grafico)
        self.painel_grafico.modo_alterado.connect(self._on_modo_grafico_alterado)
        self.painel_grafico.consulta_solicitada.connect(self._executar_consulta_historica)

    # ------------------------------------------------------------------
    # Gráfico e estado inicial
    # ------------------------------------------------------------------
    def _configurar_grafico(self):
        self.figure = Figure(figsize=(5, 3))
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.eixo = self.figure.add_subplot(111)
        self.eixo.set_title("Curva de Demanda - Consumo de Potência (W)")
        self.eixo.set_xlabel("Amostra (histórico 24h + tempo real)")
        self.eixo.set_ylabel("Potência (W)")
        self.eixo.grid(True, linestyle="--", alpha=0.4)
        (self.linha_potencia,) = self.eixo.plot([], [], color="#00A86B", linewidth=1.8)
        self.linha_limite = self.eixo.axhline(
            self.model.limite_alerta_watts,
            color="#D32F2F",
            linestyle="--",
            linewidth=1.2,
            label="Limite de alerta",
        )
        self.eixo.legend(loc="upper right", fontsize=8)
        self.ui.widgetGrafico.layout().addWidget(self.canvas)

    def _carregar_estado_inicial(self):
        historico = self.model.get_historico()
        self._redesenhar_grafico(historico["tempo"], historico["potencia"])
        valores = self.model.get_valores_atuais()
        self._atualizar_indicadores(
            valores["tensao"], valores["corrente"], valores["potencia"]
        )
        self._atualizar_estado_disjuntor()

    # ------------------------------------------------------------------
    # Telemetria
    # ------------------------------------------------------------------
    def _on_pacote_serial_recebido(self, pacote: dict):
        """Recebe o pacote já decodificado pela SerialWorker. Apenas guarda a
        última amostra - o processamento/redesenho é feito pelo timer, no
        ritmo de taxa_amostragem_ms, para não sobrecarregar a GUI quando a
        placa envia dados mais rápido do que a tela precisa exibir."""
        self._amostra_pendente = (pacote.get("tensao", 0.0), pacote.get("corrente", 0.0))

    def _processar_amostra_pendente(self):
        if self._amostra_pendente is None:
            return
        tensao, corrente = self._amostra_pendente
        self._amostra_pendente = None
        self.receber_amostra_real(tensao, corrente)

    def receber_amostra_real(self, tensao: float, corrente: float):
        """Atualiza indicadores e gráfico com a amostra real lida da porta serial."""
        self._leitura_bruta = (tensao, corrente)
        amostra = self.model.registrar_amostra(tensao, corrente)
        self._atualizar_indicadores(
            amostra["tensao"], amostra["corrente"], amostra["potencia"]
        )
        # Enquanto o operador está revisando uma consulta de histórico, a
        # amostra ao vivo não redesenha o gráfico por cima (só os indicadores
        # e alertas continuam atualizando normalmente).
        if self._modo_grafico == "tempo_real":
            historico = self.model.get_historico()
            self._redesenhar_grafico(historico["tempo"], historico["potencia"])

            status = f"Status: última amostra serial #{amostra['tempo']}"
            if not self.model.disjuntor_fechado:
                potencia = self.model.calcular_potencia(*self._leitura_bruta)
                status = (
                    f"Status: disjuntor ABERTO - leitura na entrada: {potencia:.0f} W "
                    f"(limite {self.model.limite_alerta_watts:.0f} W)"
                )
            self.ui.labelStatus.setText(status)

    # ------------------------------------------------------------------
    # Consulta de histórico de leituras
    # ------------------------------------------------------------------
    def _on_modo_grafico_alterado(self, modo: str):
        self._modo_grafico = modo
        if modo == "tempo_real":
            self.eixo.set_xlabel("Amostra (histórico 24h + tempo real)")
            historico = self.model.get_historico()
            self._redesenhar_grafico(historico["tempo"], historico["potencia"])
        else:
            self.eixo.set_xlabel("Amostra (consulta de histórico de leituras)")

    def _executar_consulta_historica(self, filtros: dict):
        if self._worker_historico is not None and self._worker_historico.isRunning():
            self._worker_historico.wait(500)

        self._worker_historico = ConsultaHistoricoWorker(
            db_path=Database.DB_NAME,
            tipo_filtro=filtros["tipo_filtro"],
            limite_n=filtros["limite_n"],
            data_inicio=filtros["data_inicio"],
            data_fim=filtros["data_fim"],
        )
        self._worker_historico.historico_carregado.connect(self._on_historico_consultado)
        self._worker_historico.erro_consulta.connect(self._on_erro_consulta_historica)
        self.ui.labelStatus.setText("Status: consultando histórico de leituras...")
        self._worker_historico.start()

    def _on_historico_consultado(self, registros: list):
        if not registros:
            self.ui.labelStatus.setText("Status: consulta ao histórico sem resultados.")
            QMessageBox.information(
                self,
                "Consulta de Histórico",
                "Nenhuma leitura encontrada para o filtro informado.",
            )
            return

        eixo_x = list(range(len(registros)))
        eixo_y = [registro["potencia"] for registro in registros]
        self._redesenhar_grafico(eixo_x, eixo_y)
        self.ui.labelStatus.setText(
            f"Status: {len(registros)} leitura(s) de {registros[0]['timestamp']} "
            f"até {registros[-1]['timestamp']}"
        )

    def _on_erro_consulta_historica(self, mensagem: str):
        self.ui.labelStatus.setText("Status: falha na consulta de histórico.")
        QMessageBox.warning(self, "Erro na Consulta de Histórico", mensagem)

    # ------------------------------------------------------------------
    # Comandos persistidos
    # ------------------------------------------------------------------
    def acionar_corte_emergencial(self):
        """Acionado manualmente pelo botão - alterna o estado do disjuntor."""
        abrir = self.model.disjuntor_fechado
        if not abrir and not self._pode_rearmar():
            return
        self._executar_corte(abrir, automatico=False)

    def _pode_rearmar(self) -> bool:
        """Com o disjuntor aberto o Model zera V/I; a leitura bruta mostra se
        a carga ainda está acima do limite (religar só dispararia o corte)."""
        worker_ok = self.worker_ativo is not None and self.worker_ativo.isRunning()
        if self._leitura_bruta is None or not worker_ok:
            return True
        potencia = self.model.calcular_potencia(*self._leitura_bruta)
        limite = self.model.limite_alerta_watts
        if potencia <= limite:
            return True
        QMessageBox.warning(
            self,
            "Rearme bloqueado",
            f"A leitura atual na entrada é {potencia:.0f} W, acima do limite de "
            f"alerta ({limite:.0f} W). Reduza a carga ou ajuste o limite e tente "
            "rearmar novamente.",
        )
        return False

    def _executar_corte_automatico(self):
        """Acionado automaticamente quando a potência ultrapassa o limite
        de alerta configurado. Só age se o disjuntor ainda estiver fechado
        (evita acionar de novo enquanto a carga já está cortada)."""
        if not self.model.disjuntor_fechado:
            return
        self._executar_corte(True, automatico=True)

    def _executar_corte(self, abrir: bool, automatico: bool):
        """Atualiza disjuntor, relé e histórico em uma única transação ACID,
        e envia o comando real de corte/rearme para a placa via serial."""
        novo_status = "ABERTO" if abrir else "FECHADO"
        if abrir:
            tipo_evento = "Corte emergencial automático" if automatico else "Corte emergencial"
            descricao = (
                f"Corte automático: potência ({self.model.potencia_atual:.2f} W) acima do "
                f"limite configurado ({self.model.limite_alerta_watts:.2f} W)."
                if automatico
                else "Disjuntor principal e relé de emergência abertos; carga cortada."
            )
        else:
            tipo_evento = "Rearme do disjuntor"
            descricao = "Disjuntor principal e relé de emergência fechados; carga restabelecida."

        conn = Database.get_connection()
        try:
            with conn:
                atuador = ActuatorRepository.obter_por_tag(
                    TAG_DISJUNTOR_PRINCIPAL, conn
                )
                if atuador is None:
                    raise ValueError("Disjuntor principal não cadastrado no banco.")

                ActuatorRepository.atualizar_status_por_tag(
                    conn, TAG_DISJUNTOR_PRINCIPAL, novo_status
                )
                ActuatorRepository.atualizar_status_por_tag(
                    conn, TAG_RELE_EMERGENCIA, novo_status
                )

                # Gancho de teste para demonstrar ROLLBACK na apresentação.
                # Defina SMARTGRID_SIMULAR_FALHA_CORTE=1 antes de iniciar o app.
                if os.environ.get("SMARTGRID_SIMULAR_FALHA_CORTE", "").strip() == "1":
                    raise RuntimeError(
                        "Falha de teste simulada antes do registro de histórico."
                    )

                Repository.inserir_em_conexao(
                    conn,
                    tipo_evento,
                    descricao,
                    self.model.potencia_atual,
                    atuador["id"],
                )
        except Exception as exc:
            registrar_erro_emergencia(str(exc))
            QMessageBox.critical(
                self,
                "Falha no corte emergencial",
                "A operação não foi concluída. O banco foi revertido (ROLLBACK).\n"
                f"Motivo: {exc}",
            )
            return
        finally:
            conn.close()

        # Só envia o comando físico e altera o Model depois de confirmar
        # que o banco fez o commit.
        worker_ok = self.worker_ativo is not None and self.worker_ativo.isRunning()
        logging.info(
            "Corte emergencial (abrir=%s, automatico=%s): worker_ativo=%r, isRunning=%s",
            abrir, automatico, self.worker_ativo,
            self.worker_ativo.isRunning() if self.worker_ativo is not None else None,
        )
        if worker_ok:
            self.worker_ativo.solicitar_corte(abrir)
        else:
            QMessageBox.warning(
                self,
                "Comando não enviado à placa",
                "O disjuntor foi atualizado no sistema (banco/tela), mas NENHUM "
                "comando foi enviado à placa: não há uma conexão serial ativa "
                "reconhecida por esta tela no momento.",
            )

        if abrir:
            self.model.abrir_disjuntor()
        else:
            self.model.fechar_disjuntor()

        self._atualizar_estado_disjuntor()
        valores = self.model.get_valores_atuais()
        self._atualizar_indicadores(
            valores["tensao"], valores["corrente"], valores["potencia"]
        )
        historico = self.model.get_historico()
        self._redesenhar_grafico(historico["tempo"], historico["potencia"])
        self.ui.labelStatus.setText(
            "Status: disjuntor ABERTO - carga cortada"
            if abrir
            else "Status: disjuntor FECHADO - carga restabelecida"
        )
        logging.info("%s concluído com sucesso.", tipo_evento)
        self.historico_atualizado.emit()

    def ajustar_limite_alerta(self, valor: int):
        self.model.set_limite_alerta(valor)
        self.ui.labelLimiteAlerta.setText(f"Limite de Alerta de Consumo: {valor} W")
        self.linha_limite.set_ydata([valor, valor])
        self.canvas.draw_idle()
        self._atualizar_alerta_visual()

    # ------------------------------------------------------------------
    # Widgets, alertas e registro no banco
    # ------------------------------------------------------------------
    def _atualizar_indicadores(self, tensao: float, corrente: float, potencia: float):
        self.ui.lcdTensao.display(tensao)
        self.ui.lcdCorrente.display(corrente)
        self.ui.lcdPotencia.display(potencia)
        # Checa tensão/corrente ANTES do alerta de potência: o corte
        # automático por potência zera a amostra (V=I=0) como efeito
        # colateral, e isso mascararia uma violação de tensão/corrente que
        # tenha ocorrido na mesma amostra se fosse checada depois.
        self._atualizar_alertas_seguranca()
        self._atualizar_alerta_visual()

    def _atualizar_estado_disjuntor(self):
        if self.model.disjuntor_fechado:
            cor = self.COR_LED_FECHADO
            self.ui.labelTextoDisjuntor.setText("FECHADO")
            self.ui.botaoCorteEmergencial.setText("CORTE EMERGENCIAL DE CARGA")
        else:
            cor = self.COR_LED_ABERTO
            self.ui.labelTextoDisjuntor.setText("ABERTO")
            self.ui.botaoCorteEmergencial.setText("REARMAR DISJUNTOR")

        self.ui.labelLedDisjuntor.setStyleSheet(
            f"QLabel {{ background-color: {cor}; border: 2px solid #0a3d1f; border-radius: 21px; }}"
        )

    def _atualizar_alerta_visual(self):
        """Exibe o alarme e persiste apenas a transição para estado de alerta."""
        acima_do_limite = self.model.consumo_acima_do_limite()
        self.ui.labelAlerta.setVisible(acima_do_limite)

        cor = "#D32F2F" if acima_do_limite else "#00E676"
        self.ui.lcdPotencia.setStyleSheet(
            f"QLCDNumber {{ background-color: #101820; color: {cor}; "
            f"border: 2px solid {cor}; border-radius: 6px; }}"
        )

        alarme_novo = acima_do_limite and not self._alerta_ativo
        # Atualiza o flag antes de disparar efeitos reentrantes (o corte
        # automático chama de volta _atualizar_indicadores -> este método).
        self._alerta_ativo = acima_do_limite
        if alarme_novo:
            self._registrar_evento_alarme()
            self._executar_corte_automatico()

    def _atualizar_alertas_seguranca(self):
        """Exibe e persiste os alarmes de tensão/corrente acima dos limites
        de segurança cadastrados (tela de Limites), com a mesma lógica de
        transição usada no alarme de consumo (só registra 1x por violação)."""
        tensao_acima = self.model.tensao_acima_do_limite()
        self.labelAlertaTensao.setVisible(tensao_acima)
        alarme_tensao_novo = tensao_acima and not self._alerta_tensao_ativo
        self._alerta_tensao_ativo = tensao_acima
        if alarme_tensao_novo:
            self._registrar_evento_alarme(
                "Alarme de tensão",
                f"Tensão acima do limite de segurança: {self.model.tensao_atual:.2f} V "
                f"(limite configurado: {self.model.limite_tensao_maxima:.2f} V).",
                self.model.tensao_atual,
            )

        corrente_acima = self.model.corrente_acima_do_limite()
        self.labelAlertaCorrente.setVisible(corrente_acima)
        alarme_corrente_novo = corrente_acima and not self._alerta_corrente_ativo
        self._alerta_corrente_ativo = corrente_acima
        if alarme_corrente_novo:
            self._registrar_evento_alarme(
                "Alarme de corrente",
                f"Corrente acima do limite de segurança: {self.model.corrente_atual:.2f} A "
                f"(limite configurado: {self.model.limite_corrente_maxima:.2f} A).",
                self.model.corrente_atual,
            )

    def _registrar_evento_alarme(
        self,
        tipo_evento: str = "Alarme de consumo",
        descricao: str | None = None,
        valor: float | None = None,
    ):
        if descricao is None:
            potencia = self.model.potencia_atual
            limite = self.model.limite_alerta_watts
            descricao = (
                f"Potência acima do limite: {potencia:.2f} W "
                f"(limite configurado: {limite:.2f} W)."
            )
            valor = potencia
        try:
            atuador_id = ActuatorRepository.obter_id_por_tag(TAG_DISJUNTOR_PRINCIPAL)
            Repository.registrar_evento(tipo_evento, descricao, valor, atuador_id)
            logging.warning(descricao)
            self.historico_atualizado.emit()
        except (sqlite3.Error, ValueError) as exc:
            logging.exception("Falha ao persistir o evento de alarme: %s", exc)

    def _redesenhar_grafico(self, eixo_x, eixo_y):
        self.linha_potencia.set_data(eixo_x, eixo_y)
        self.eixo.relim()
        self.eixo.autoscale_view()
        self.canvas.draw_idle()

    def closeEvent(self, event):
        self.timer_telemetria.stop()
        if self.worker_ativo is not None:
            try:
                self.worker_ativo.dados_recebidos.disconnect(self._on_pacote_serial_recebido)
            except (TypeError, RuntimeError):
                pass
        if self._worker_historico is not None and self._worker_historico.isRunning():
            self._worker_historico.wait(1000)
        super().closeEvent(event)
