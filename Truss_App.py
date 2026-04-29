from Truss_GUI import Ui_TrussStructuralDesign
from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from Truss_Classes import TrussController
import sys


class MainWindow(Ui_TrussStructuralDesign, qtw.QWidget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        self.controller = TrussController()
        self.controller.setDisplayWidgets(
            (
                self.te_DesignReport,
                self.le_LinkName,
                self.le_Node1Name,
                self.le_Node2Name,
                self.le_LinkLength,
                self.gv_Main,
                self.lbl_MousePos,
                self.spnd_Zoom
            )
        )

        self.btn_Open.clicked.connect(self.OpenFile)
        self.spnd_Zoom.valueChanged.connect(self.controller.setZoom)

        self.controller.installSceneEventFilter(self)

        self.gv_Main.setMouseTracking(True)
        self.show()

    def eventFilter(self, obj, event):
        self.controller.handleSceneEvent(obj, event)
        return super(MainWindow, self).eventFilter(obj, event)

    def OpenFile(self):
        filename = qtw.QFileDialog.getOpenFileName()[0]
        if len(filename) == 0:
            return

        self.te_Path.setText(filename)

        with open(filename, "r") as file:
            data = file.readlines()

        self.controller.ImportFromFile(data)


def Main():
    app = qtw.QApplication(sys.argv)
    mw = MainWindow()
    mw.setWindowTitle("Truss Structural Design")
    sys.exit(app.exec())


if __name__ == "__main__":
    Main()