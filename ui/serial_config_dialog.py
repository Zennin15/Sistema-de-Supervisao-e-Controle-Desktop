# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'serial_config_dialog.ui'
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
from PySide6.QtWidgets import (QApplication, QComboBox, QDialog, QLabel,
    QPushButton, QSizePolicy, QSpinBox, QWidget)

class Ui_DialogSerial(object):
    def setupUi(self, DialogSerial):
        if not DialogSerial.objectName():
            DialogSerial.setObjectName(u"DialogSerial")
        DialogSerial.resize(420, 300)
        self.lblPortaCom = QLabel(DialogSerial)
        self.lblPortaCom.setObjectName(u"lblPortaCom")
        self.lblPortaCom.setGeometry(QRect(20, 20, 111, 20))
        self.cbPortaCom = QComboBox(DialogSerial)
        self.cbPortaCom.addItem("")
        self.cbPortaCom.addItem("")
        self.cbPortaCom.addItem("")
        self.cbPortaCom.addItem("")
        self.cbPortaCom.setObjectName(u"cbPortaCom")
        self.cbPortaCom.setGeometry(QRect(160, 18, 220, 24))
        self.lblBaudRate = QLabel(DialogSerial)
        self.lblBaudRate.setObjectName(u"lblBaudRate")
        self.lblBaudRate.setGeometry(QRect(20, 60, 111, 20))
        self.cbBaudRate = QComboBox(DialogSerial)
        self.cbBaudRate.addItem("")
        self.cbBaudRate.addItem("")
        self.cbBaudRate.setObjectName(u"cbBaudRate")
        self.cbBaudRate.setGeometry(QRect(160, 58, 220, 24))
        self.lblTimeout = QLabel(DialogSerial)
        self.lblTimeout.setObjectName(u"lblTimeout")
        self.lblTimeout.setGeometry(QRect(20, 100, 111, 20))
        self.spinTimeout = QSpinBox(DialogSerial)
        self.spinTimeout.setObjectName(u"spinTimeout")
        self.spinTimeout.setGeometry(QRect(160, 98, 100, 24))
        self.spinTimeout.setMinimum(1)
        self.spinTimeout.setMaximum(60)
        self.spinTimeout.setValue(5)
        self.lblStatus = QLabel(DialogSerial)
        self.lblStatus.setObjectName(u"lblStatus")
        self.lblStatus.setGeometry(QRect(20, 150, 81, 20))
        self.lblStatusValor = QLabel(DialogSerial)
        self.lblStatusValor.setObjectName(u"lblStatusValor")
        self.lblStatusValor.setGeometry(QRect(100, 150, 200, 20))
        self.lblStatusValor.setStyleSheet(u"color: #c0392b; font-weight: bold;")
        self.btnConectar = QPushButton(DialogSerial)
        self.btnConectar.setObjectName(u"btnConectar")
        self.btnConectar.setGeometry(QRect(160, 200, 100, 30))
        self.btnDesconectar = QPushButton(DialogSerial)
        self.btnDesconectar.setObjectName(u"btnDesconectar")
        self.btnDesconectar.setGeometry(QRect(280, 200, 100, 30))
        self.btnDesconectar.setEnabled(False)
        self.btnFechar = QPushButton(DialogSerial)
        self.btnFechar.setObjectName(u"btnFechar")
        self.btnFechar.setGeometry(QRect(160, 250, 220, 28))

        self.retranslateUi(DialogSerial)
        self.btnFechar.clicked.connect(DialogSerial.close)

        QMetaObject.connectSlotsByName(DialogSerial)
    # setupUi

    def retranslateUi(self, DialogSerial):
        DialogSerial.setWindowTitle(QCoreApplication.translate("DialogSerial", u"Configura\u00e7\u00e3o da Comunica\u00e7\u00e3o Serial", None))
        self.lblPortaCom.setText(QCoreApplication.translate("DialogSerial", u"Porta COM", None))
        self.cbPortaCom.setItemText(0, QCoreApplication.translate("DialogSerial", u"COM1", None))
        self.cbPortaCom.setItemText(1, QCoreApplication.translate("DialogSerial", u"COM2", None))
        self.cbPortaCom.setItemText(2, QCoreApplication.translate("DialogSerial", u"COM3", None))
        self.cbPortaCom.setItemText(3, QCoreApplication.translate("DialogSerial", u"COM4", None))

        self.lblBaudRate.setText(QCoreApplication.translate("DialogSerial", u"Baud Rate", None))
        self.cbBaudRate.setItemText(0, QCoreApplication.translate("DialogSerial", u"9600", None))
        self.cbBaudRate.setItemText(1, QCoreApplication.translate("DialogSerial", u"115200", None))

        self.lblTimeout.setText(QCoreApplication.translate("DialogSerial", u"Timeout (s)", None))
        self.lblStatus.setText(QCoreApplication.translate("DialogSerial", u"Status:", None))
        self.lblStatusValor.setText(QCoreApplication.translate("DialogSerial", u"Desconectado", None))
        self.btnConectar.setText(QCoreApplication.translate("DialogSerial", u"Conectar", None))
        self.btnDesconectar.setText(QCoreApplication.translate("DialogSerial", u"Desconectar", None))
        self.btnFechar.setText(QCoreApplication.translate("DialogSerial", u"Fechar", None))
    # retranslateUi

