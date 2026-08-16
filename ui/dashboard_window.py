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
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_DashboardWindow(object):
    def setupUi(self, DashboardWindow):
        if not DashboardWindow.objectName():
            DashboardWindow.setObjectName(u"DashboardWindow")
        DashboardWindow.resize(950, 680)
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


        self.verticalLayoutPrincipal.addLayout(self.horizontalLayoutIndicadores)

        self.groupBoxGrafico = QGroupBox(DashboardWindow)
        self.groupBoxGrafico.setObjectName(u"groupBoxGrafico")
        self.verticalLayoutGrafico = QVBoxLayout(self.groupBoxGrafico)
        self.verticalLayoutGrafico.setObjectName(u"verticalLayoutGrafico")
        self.widgetGrafico = QWidget(self.groupBoxGrafico)
        self.widgetGrafico.setObjectName(u"widgetGrafico")
        self.widgetGrafico.setMinimumSize(QSize(0, 320))
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
        self.groupBoxGrafico.setTitle(QCoreApplication.translate("DashboardWindow", u"Tend\u00eancia Temporal - Consumo de Pot\u00eancia", None))
        self.labelStatus.setText(QCoreApplication.translate("DashboardWindow", u"Status: aguardando dados...", None))
        self.botaoVoltar.setText(QCoreApplication.translate("DashboardWindow", u"Voltar", None))
    # retranslateUi

