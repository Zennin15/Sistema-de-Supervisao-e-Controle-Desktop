# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'config_dialog.ui'
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
from PySide6.QtWidgets import (QAbstractButton, QApplication, QDialog, QDialogButtonBox,
    QDoubleSpinBox, QLabel, QSizePolicy, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(907, 434)
        self.buttonBox = QDialogButtonBox(Dialog)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setGeometry(QRect(-110, 40, 341, 32))
        self.buttonBox.setOrientation(Qt.Orientation.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.StandardButton.Cancel|QDialogButtonBox.StandardButton.Ok)
        self.inputCorrente = QLabel(Dialog)
        self.inputCorrente.setObjectName(u"inputCorrente")
        self.inputCorrente.setGeometry(QRect(150, 130, 121, 20))
        self.inputTensao = QLabel(Dialog)
        self.inputTensao.setObjectName(u"inputTensao")
        self.inputTensao.setGeometry(QRect(150, 160, 111, 16))
        self.spinCorrente = QDoubleSpinBox(Dialog)
        self.spinCorrente.setObjectName(u"spinCorrente")
        self.spinCorrente.setGeometry(QRect(270, 130, 62, 22))
        self.spinCorrente.setMaximum(100.989999999999995)
        self.spinTensao = QDoubleSpinBox(Dialog)
        self.spinTensao.setObjectName(u"spinTensao")
        self.spinTensao.setGeometry(QRect(270, 160, 62, 22))
        self.spinTensao.setMaximum(100.989999999999995)

        self.retranslateUi(Dialog)
        self.buttonBox.accepted.connect(Dialog.accept)
        self.buttonBox.rejected.connect(Dialog.reject)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.inputCorrente.setText(QCoreApplication.translate("Dialog", u"Limite de Corrente (A)", None))
        self.inputTensao.setText(QCoreApplication.translate("Dialog", u"Limite de Tens\u00e3o (V)", None))
    # retranslateUi

