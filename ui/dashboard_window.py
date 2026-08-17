# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'dashboard_window.ui'
##
## Created by: Qt User Interface Compiler version 6.11.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QDialog, QGroupBox, QHBoxLayout,
    QLCDNumber, QLabel, QPushButton, QSizePolicy,
    QSlider, QSpacerItem, QVBoxLayout, QWidget)

class Ui_DashboardWindow(object):
    def setupUi(self, DashboardWindow):
        if not DashboardWindow.objectName():
            DashboardWindow.setObjectName(u"DashboardWindow")
        DashboardWindow.resize(980, 780)
        self.verticalLayoutPrincipal = QVBoxLayout(DashboardWindow)
        self.verticalLayoutPrincipal.setObjectName(u"verticalLayoutPrincipal")
        self.labelTitulo = QLabel(DashboardWindow)
        self.labelTitulo.setObjectName(u"labelTitulo")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        self.labelTitulo.setFont(font)
        self.labelTitulo.setAlignment(Qt.AlignCenter)

        self.verticalLayoutPrincipal.addWidget(self.labelTitulo)

        self.horizontalLayoutIndicadores = QHBoxLayout()
        self.horizontalLayoutIndicadores.setObjectName(u"horizontalLayoutIndicadores")
        self.groupBoxTensao = QGroupBox(DashboardWindow)
        self.groupBoxTensao.setObjectName(u"groupBoxTensao")
        self.verticalLayoutTensao = QVBoxLayout(self.groupBoxTensao)
        self.verticalLayoutTensao.setObjectName(u"verticalLayoutTensao")
        self.lcdTensao = QLCDNumber(self.groupBoxTensao)
        self.lcdTensao.setObjectName(u"lcdTensao")
        self.lcdTensao.setMinimumSize(QSize(0, 80))
        self.lcdTensao.setStyleSheet(u"QLCDNumber { background-color: #101820; color: #00E5FF; border: 2px solid #00E5FF; border-radius: 6px; }")
        self.lcdTensao.setDigitCount(6)
        self.lcdTensao.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        self.lcdTensao.setProperty(u"value", 0.000000000000000)

        self.verticalLayoutTensao.addWidget(self.lcdTensao)

        self.labelUnidadeTensao = QLabel(self.groupBoxTensao)
        self.labelUnidadeTensao.setObjectName(u"labelUnidadeTensao")
        self.labelUnidadeTensao.setAlignment(Qt.AlignCenter)

        self.verticalLayoutTensao.addWidget(self.labelUnidadeTensao)


        self.horizontalLayoutIndicadores.addWidget(self.groupBoxTensao)

        self.groupBoxCorrente = QGroupBox(DashboardWindow)
        self.groupBoxCorrente.setObjectName(u"groupBoxCorrente")
        self.verticalLayoutCorrente = QVBoxLayout(self.groupBoxCorrente)
        self.verticalLayoutCorrente.setObjectName(u"verticalLayoutCorrente")
        self.lcdCorrente = QLCDNumber(self.groupBoxCorrente)
        self.lcdCorrente.setObjectName(u"lcdCorrente")
        self.lcdCorrente.setMinimumSize(QSize(0, 80))
        self.lcdCorrente.setStyleSheet(u"QLCDNumber { background-color: #101820; color: #FFC400; border: 2px solid #FFC400; border-radius: 6px; }")
        self.lcdCorrente.setDigitCount(6)
        self.lcdCorrente.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        self.lcdCorrente.setProperty(u"value", 0.000000000000000)

        self.verticalLayoutCorrente.addWidget(self.lcdCorrente)

        self.labelUnidadeCorrente = QLabel(self.groupBoxCorrente)
        self.labelUnidadeCorrente.setObjectName(u"labelUnidadeCorrente")
        self.labelUnidadeCorrente.setAlignment(Qt.AlignCenter)

        self.verticalLayoutCorrente.addWidget(self.labelUnidadeCorrente)


        self.horizontalLayoutIndicadores.addWidget(self.groupBoxCorrente)

        self.groupBoxPotencia = QGroupBox(DashboardWindow)
        self.groupBoxPotencia.setObjectName(u"groupBoxPotencia")
        self.verticalLayoutPotencia = QVBoxLayout(self.groupBoxPotencia)
        self.verticalLayoutPotencia.setObjectName(u"verticalLayoutPotencia")
        self.lcdPotencia = QLCDNumber(self.groupBoxPotencia)
        self.lcdPotencia.setObjectName(u"lcdPotencia")
        self.lcdPotencia.setMinimumSize(QSize(0, 80))
        self.lcdPotencia.setStyleSheet(u"QLCDNumber { background-color: #101820; color: #00E676; border: 2px solid #00E676; border-radius: 6px; }")
        self.lcdPotencia.setDigitCount(7)
        self.lcdPotencia.setSegmentStyle(QLCDNumber.SegmentStyle.Flat)
        self.lcdPotencia.setProperty(u"value", 0.000000000000000)

        self.verticalLayoutPotencia.addWidget(self.lcdPotencia)

        self.labelUnidadePotencia = QLabel(self.groupBoxPotencia)
        self.labelUnidadePotencia.setObjectName(u"labelUnidadePotencia")
        self.labelUnidadePotencia.setAlignment(Qt.AlignCenter)

        self.verticalLayoutPotencia.addWidget(self.labelUnidadePotencia)


        self.horizontalLayoutIndicadores.addWidget(self.groupBoxPotencia)

        self.groupBoxDisjuntor = QGroupBox(DashboardWindow)
        self.groupBoxDisjuntor.setObjectName(u"groupBoxDisjuntor")
        self.verticalLayoutDisjuntor = QVBoxLayout(self.groupBoxDisjuntor)
        self.verticalLayoutDisjuntor.setObjectName(u"verticalLayoutDisjuntor")
        self.horizontalLayoutLed = QHBoxLayout()
        self.horizontalLayoutLed.setObjectName(u"horizontalLayoutLed")
        self.horizontalSpacerLedEsq = QSpacerItem(10, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayoutLed.addItem(self.horizontalSpacerLedEsq)

        self.labelLedDisjuntor = QLabel(self.groupBoxDisjuntor)
        self.labelLedDisjuntor.setObjectName(u"labelLedDisjuntor")
        self.labelLedDisjuntor.setMinimumSize(QSize(42, 42))
        self.labelLedDisjuntor.setMaximumSize(QSize(42, 42))
        self.labelLedDisjuntor.setStyleSheet(u"QLabel { background-color: #00E676; border: 2px solid #0a3d1f; border-radius: 21px; }")

        self.horizontalLayoutLed.addWidget(self.labelLedDisjuntor)

        self.horizontalSpacerLedDir = QSpacerItem(10, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayoutLed.addItem(self.horizontalSpacerLedDir)


        self.verticalLayoutDisjuntor.addLayout(self.horizontalLayoutLed)

        self.labelTextoDisjuntor = QLabel(self.groupBoxDisjuntor)
        self.labelTextoDisjuntor.setObjectName(u"labelTextoDisjuntor")
        font1 = QFont()
        font1.setBold(True)
        self.labelTextoDisjuntor.setFont(font1)
        self.labelTextoDisjuntor.setAlignment(Qt.AlignCenter)

        self.verticalLayoutDisjuntor.addWidget(self.labelTextoDisjuntor)


        self.horizontalLayoutIndicadores.addWidget(self.groupBoxDisjuntor)


        self.verticalLayoutPrincipal.addLayout(self.horizontalLayoutIndicadores)

        self.groupBoxComandos = QGroupBox(DashboardWindow)
        self.groupBoxComandos.setObjectName(u"groupBoxComandos")
        self.horizontalLayoutComandos = QHBoxLayout(self.groupBoxComandos)
        self.horizontalLayoutComandos.setObjectName(u"horizontalLayoutComandos")
        self.botaoCorteEmergencial = QPushButton(self.groupBoxComandos)
        self.botaoCorteEmergencial.setObjectName(u"botaoCorteEmergencial")
        self.botaoCorteEmergencial.setMinimumSize(QSize(0, 50))
        self.botaoCorteEmergencial.setFont(font1)
        self.botaoCorteEmergencial.setStyleSheet(u"QPushButton { background-color: #D32F2F; color: white; border-radius: 6px; } QPushButton:hover { background-color: #B71C1C; }")

        self.horizontalLayoutComandos.addWidget(self.botaoCorteEmergencial)

        self.horizontalSpacerComandos = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayoutComandos.addItem(self.horizontalSpacerComandos)

        self.verticalLayoutLimite = QVBoxLayout()
        self.verticalLayoutLimite.setObjectName(u"verticalLayoutLimite")
        self.labelLimiteAlerta = QLabel(self.groupBoxComandos)
        self.labelLimiteAlerta.setObjectName(u"labelLimiteAlerta")
        self.labelLimiteAlerta.setAlignment(Qt.AlignCenter)

        self.verticalLayoutLimite.addWidget(self.labelLimiteAlerta)

        self.sliderLimiteAlerta = QSlider(self.groupBoxComandos)
        self.sliderLimiteAlerta.setObjectName(u"sliderLimiteAlerta")
        self.sliderLimiteAlerta.setMinimumSize(QSize(260, 0))
        self.sliderLimiteAlerta.setMinimum(500)
        self.sliderLimiteAlerta.setMaximum(3000)
        self.sliderLimiteAlerta.setSingleStep(50)
        self.sliderLimiteAlerta.setPageStep(100)
        self.sliderLimiteAlerta.setValue(1500)
        self.sliderLimiteAlerta.setOrientation(Qt.Horizontal)
        self.sliderLimiteAlerta.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.sliderLimiteAlerta.setTickInterval(250)

        self.verticalLayoutLimite.addWidget(self.sliderLimiteAlerta)


        self.horizontalLayoutComandos.addLayout(self.verticalLayoutLimite)


        self.verticalLayoutPrincipal.addWidget(self.groupBoxComandos)

        self.labelAlerta = QLabel(DashboardWindow)
        self.labelAlerta.setObjectName(u"labelAlerta")
        self.labelAlerta.setFont(font1)
        self.labelAlerta.setStyleSheet(u"QLabel { color: #D32F2F; }")
        self.labelAlerta.setAlignment(Qt.AlignCenter)
        self.labelAlerta.setVisible(False)

        self.verticalLayoutPrincipal.addWidget(self.labelAlerta)

        self.groupBoxGrafico = QGroupBox(DashboardWindow)
        self.groupBoxGrafico.setObjectName(u"groupBoxGrafico")
        self.verticalLayoutGrafico = QVBoxLayout(self.groupBoxGrafico)
        self.verticalLayoutGrafico.setObjectName(u"verticalLayoutGrafico")
        self.widgetGrafico = QWidget(self.groupBoxGrafico)
        self.widgetGrafico.setObjectName(u"widgetGrafico")
        self.widgetGrafico.setMinimumSize(QSize(0, 300))
        self.verticalLayoutGraficoContainer = QVBoxLayout(self.widgetGrafico)
        self.verticalLayoutGraficoContainer.setObjectName(u"verticalLayoutGraficoContainer")
        self.verticalLayoutGraficoContainer.setContentsMargins(0, 0, 0, 0)

        self.verticalLayoutGrafico.addWidget(self.widgetGrafico)


        self.verticalLayoutPrincipal.addWidget(self.groupBoxGrafico)

        self.horizontalLayoutRodape = QHBoxLayout()
        self.horizontalLayoutRodape.setObjectName(u"horizontalLayoutRodape")
        self.labelStatus = QLabel(DashboardWindow)
        self.labelStatus.setObjectName(u"labelStatus")

        self.horizontalLayoutRodape.addWidget(self.labelStatus)

        self.horizontalSpacerRodape = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayoutRodape.addItem(self.horizontalSpacerRodape)

        self.botaoVoltar = QPushButton(DashboardWindow)
        self.botaoVoltar.setObjectName(u"botaoVoltar")

        self.horizontalLayoutRodape.addWidget(self.botaoVoltar)


        self.verticalLayoutPrincipal.addLayout(self.horizontalLayoutRodape)


        self.retranslateUi(DashboardWindow)

        QMetaObject.connectSlotsByName(DashboardWindow)
    # setupUi

    def retranslateUi(self, DashboardWindow):
        DashboardWindow.setWindowTitle(QCoreApplication.translate("DashboardWindow", u"Dashboard de Telemetria", None))
        self.labelTitulo.setText(QCoreApplication.translate("DashboardWindow", u"Dashboard de Telemetria em Tempo Real", None))
        self.groupBoxTensao.setTitle(QCoreApplication.translate("DashboardWindow", u"Tens\u00e3o (VRMS)", None))
        self.labelUnidadeTensao.setText(QCoreApplication.translate("DashboardWindow", u"Volts (V)", None))
        self.groupBoxCorrente.setTitle(QCoreApplication.translate("DashboardWindow", u"Corrente (IRMS)", None))
        self.labelUnidadeCorrente.setText(QCoreApplication.translate("DashboardWindow", u"Amperes (A)", None))
        self.groupBoxPotencia.setTitle(QCoreApplication.translate("DashboardWindow", u"Pot\u00eancia Ativa (P = V x I)", None))
        self.labelUnidadePotencia.setText(QCoreApplication.translate("DashboardWindow", u"Watts (W)", None))
        self.groupBoxDisjuntor.setTitle(QCoreApplication.translate("DashboardWindow", u"Disjuntor / Chave de Prote\u00e7\u00e3o", None))
        self.labelLedDisjuntor.setText("")
        self.labelTextoDisjuntor.setText(QCoreApplication.translate("DashboardWindow", u"FECHADO", None))
        self.groupBoxComandos.setTitle(QCoreApplication.translate("DashboardWindow", u"Comandos de Acionamento", None))
        self.botaoCorteEmergencial.setText(QCoreApplication.translate("DashboardWindow", u"CORTE EMERGENCIAL DE CARGA", None))
        self.labelLimiteAlerta.setText(QCoreApplication.translate("DashboardWindow", u"Limite de Alerta de Consumo: 1500 W", None))
        self.labelAlerta.setText(QCoreApplication.translate("DashboardWindow", u"\u26a0 CONSUMO ACIMA DO LIMITE DE ALERTA!", None))
        self.groupBoxGrafico.setTitle(QCoreApplication.translate("DashboardWindow", u"Tend\u00eancia de Consumo (Curva de Demanda - \u00faltimas 24 horas)", None))
        self.labelStatus.setText(QCoreApplication.translate("DashboardWindow", u"Status: aguardando dados...", None))
        self.botaoVoltar.setText(QCoreApplication.translate("DashboardWindow", u"Voltar", None))
    # retranslateUi

