# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'limits_configuration_window.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QHeaderView, QPushButton,
    QSizePolicy, QTableWidget, QTableWidgetItem, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(400, 300)
        self.tableWidget = QTableWidget(Dialog)
        self.tableWidget.setObjectName(u"tableWidget")
        self.tableWidget.setGeometry(QRect(5, 11, 381, 231))
        self.botaoAdicionarLimite = QPushButton(Dialog)
        self.botaoAdicionarLimite.setObjectName(u"botaoAdicionarLimite")
        self.botaoAdicionarLimite.setGeometry(QRect(210, 210, 81, 26))
        self.botaoAplicarLimite = QPushButton(Dialog)
        self.botaoAplicarLimite.setObjectName(u"botaoAplicarLimite")
        self.botaoAplicarLimite.setGeometry(QRect(220, 260, 81, 26))
        self.botaoCancelarLimite = QPushButton(Dialog)
        self.botaoCancelarLimite.setObjectName(u"botaoCancelarLimite")
        self.botaoCancelarLimite.setGeometry(QRect(310, 260, 81, 26))
        self.botaoRemoverLimite = QPushButton(Dialog)
        self.botaoRemoverLimite.setObjectName(u"botaoRemoverLimite")
        self.botaoRemoverLimite.setGeometry(QRect(300, 210, 81, 26))

        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.botaoAdicionarLimite.setText(QCoreApplication.translate("Dialog", u"Adicionar", None))
        self.botaoAplicarLimite.setText(QCoreApplication.translate("Dialog", u"Aplicar", None))
        self.botaoCancelarLimite.setText(QCoreApplication.translate("Dialog", u"Cancelar", None))
        self.botaoRemoverLimite.setText(QCoreApplication.translate("Dialog", u"Remover", None))
    # retranslateUi

