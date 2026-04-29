# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'GraphicsView_GUI.ui'
#
# Created by: PyQt5 UI code generator 5.9.2
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(1723, 1408)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.pushButton = QtWidgets.QPushButton(Form)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)
        self.spnd_Zoom = QtWidgets.QDoubleSpinBox(Form)
        self.spnd_Zoom.setMinimum(0.01)
        self.spnd_Zoom.setMaximum(10.0)
        self.spnd_Zoom.setProperty("value", 1.0)
        self.spnd_Zoom.setObjectName("spnd_Zoom")
        self.horizontalLayout.addWidget(self.spnd_Zoom)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.gv_Main = QtWidgets.QGraphicsView(Form)
        self.gv_Main.setMouseTracking(True)
        self.gv_Main.setObjectName("gv_Main")
        self.verticalLayout.addWidget(self.gv_Main)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.pushButton.setText(_translate("Form", "PushButton"))

