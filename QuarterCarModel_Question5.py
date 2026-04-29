from scipy.integrate import odeint
from scipy.optimize import minimize
import matplotlib.pyplot as plt
import numpy as np
import math

from PyQt5 import QtWidgets as qtw
from PyQt5 import QtCore as qtc
from PyQt5 import QtGui as qtg

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure


class MassBlock(qtw.QGraphicsItem):
    def __init__(self, CenterX, CenterY, width=30, height=10, parent=None, pen=None, brush=None, name='CarBody', mass=10):
        super().__init__(parent)
        self.x = CenterX
        self.y = CenterY
        self.pen = pen
        self.brush = brush
        self.width = width
        self.height = height
        self.rect = qtc.QRectF(-self.width / 2, -self.height / 2, self.width, self.height)

    def boundingRect(self):
        return self.rect

    def paint(self, painter, option, widget=None):
        if self.pen:
            painter.setPen(self.pen)
        if self.brush:
            painter.setBrush(self.brush)
        painter.drawRect(self.rect)
        self.setPos(self.x, self.y)


class Wheel(qtw.QGraphicsItem):
    def __init__(self, CenterX, CenterY, radius=10, parent=None, pen=None, wheelBrush=None, massBrush=None, name='Wheel', mass=10):
        super().__init__(parent)
        self.x = CenterX
        self.y = CenterY
        self.pen = pen
        self.brush = wheelBrush
        self.radius = radius
        self.rect = qtc.QRectF(-self.radius, -self.radius, 2 * self.radius, 2 * self.radius)
        self.massBlock = MassBlock(CenterX, CenterY, width=2 * radius * 0.85, height=radius / 3,
                                   pen=pen, brush=massBrush)

    def boundingRect(self):
        return self.rect

    def addToScene(self, scene):
        scene.addItem(self)
        scene.addItem(self.massBlock)

    def paint(self, painter, option, widget=None):
        if self.pen:
            painter.setPen(self.pen)
        if self.brush:
            painter.setBrush(self.brush)
        painter.drawEllipse(self.rect)
        self.setPos(self.x, self.y)


class CarModel:
    def __init__(self):
        self.results = None
        self.tmax = 3.0
        self.t = np.linspace(0, self.tmax, 2000)
        self.timeData = self.t

        self.tramp = 1.0
        self.angrad = 0.1
        self.ymag = 6.0 / (12.0 * 3.3)
        self.yangdeg = 45.0

        self.m1 = 450.0
        self.m2 = 20.0
        self.c1 = 4500.0
        self.k1 = 15000.0
        self.k2 = 90000.0
        self.v = 120.0

        g = 9.81
        self.mink1 = (self.m1 * g) / 0.1524
        self.maxk1 = (self.m1 * g) / 0.0762
        self.mink2 = (self.m2 * g) / 0.0381
        self.maxk2 = (self.m2 * g) / 0.01905

        self.accel = None
        self.accelData = None
        self.accelMax = 0.0
        self.accelLim = 2.0
        self.SSE = 0.0

        self.roadData = None
        self.springForce = None
        self.damperForce = None
        self.tireForce = None


class CarView:
    def __init__(self, args):
        self.input_widgets, self.display_widgets = args

        self.le_m1, self.le_v, self.le_k1, self.le_c1, self.le_m2, self.le_k2, self.le_ang, \
            self.le_tmax, self.chk_IncludeAccel = self.input_widgets

        self.gv_Schematic, self.chk_LogX, self.chk_LogY, self.chk_LogAccel, \
            self.chk_ShowAccel, self.lbl_MaxMinInfo, self.layout_horizontal_main = self.display_widgets

        self.tabs = qtw.QTabWidget()
        self.layout_horizontal_main.addWidget(self.tabs)

        self.position_tab = qtw.QWidget()
        self.force_tab = qtw.QWidget()

        self.position_layout = qtw.QVBoxLayout()
        self.force_layout = qtw.QVBoxLayout()

        self.position_tab.setLayout(self.position_layout)
        self.force_tab.setLayout(self.force_layout)

        self.tabs.addTab(self.position_tab, "Position vs. time")
        self.tabs.addTab(self.force_tab, "Force vs time")

        self.figure = Figure(tight_layout=True, frameon=True, facecolor='none')
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.position_layout.addWidget(self.canvas)

        self.forceFigure = Figure(tight_layout=True, frameon=True, facecolor='none')
        self.forceCanvas = FigureCanvasQTAgg(self.forceFigure)
        self.force_layout.addWidget(self.forceCanvas)

        self.ax = self.figure.add_subplot()
        self.ax1 = self.ax.twinx()

        self.forceAx = self.forceFigure.add_subplot()

        self.buildScene()

    def updateView(self, model=None):
        self.le_m1.setText(f"{model.m1:.2f}")
        self.le_k1.setText(f"{model.k1:.2f}")
        self.le_c1.setText(f"{model.c1:.2f}")
        self.le_m2.setText(f"{model.m2:.2f}")
        self.le_k2.setText(f"{model.k2:.2f}")
        self.le_v.setText(f"{model.v:.2f}")
        self.le_ang.setText(f"{model.yangdeg:.2f}")
        self.le_tmax.setText(f"{model.tmax:.2f}")

        self.lbl_MaxMinInfo.setText(
            f"k1_min = {model.mink1:.2f}, k1_max = {model.maxk1:.2f}\n"
            f"k2_min = {model.mink2:.2f}, k2_max = {model.maxk2:.2f}\n"
            f"SSE = {model.SSE:.4f}\n"
            f"Max Accel = {model.accelMax:.3f} g"
        )

        self.doPlot(model)
        self.doForcePlot(model)

    def buildScene(self):
        self.scene = qtw.QGraphicsScene()
        self.scene.setSceneRect(-200, -200, 400, 400)
        self.gv_Schematic.setScene(self.scene)

        self.setupPensAndBrushes()

        self.Wheel = Wheel(0, 50, 50, pen=self.penWheel,
                           wheelBrush=self.brushWheel,
                           massBrush=self.brushMass)

        self.CarBody = MassBlock(0, -70, 100, 30,
                                 pen=self.penWheel,
                                 brush=self.brushMass)

        self.Wheel.addToScene(self.scene)
        self.scene.addItem(self.CarBody)

        pen = qtg.QPen(qtg.QColor("black"))
        pen.setWidth(2)

        self.scene.addLine(-20, -55, -20, 25, pen)
        self.scene.addLine(20, -55, 20, 25, pen)
        self.scene.addLine(-50, 100, 50, 100, pen)
        self.scene.addText("Suspension").setPos(35, -40)
        self.scene.addText("Tire").setPos(35, 45)
        self.scene.addText("Road").setPos(35, 95)

    def setupPensAndBrushes(self):
        self.penWheel = qtg.QPen(qtg.QColor("orange"))
        self.penWheel.setWidth(1)
        self.brushWheel = qtg.QBrush(qtg.QColor.fromHsv(35, 255, 255, 64))
        self.brushMass = qtg.QBrush(qtg.QColor(200, 200, 200, 128))

    def doPlot(self, model=None):
        if model.results is None:
            return

        ax = self.ax
        ax1 = self.ax1

        ax.clear()
        ax1.clear()

        t = model.timeData
        ycar = model.results[:, 0]
        ywheel = model.results[:, 2]
        road = model.roadData
        accel = model.accelData

        if self.chk_LogX.isChecked():
            ax.set_xlim(0.001, model.tmax)
            ax.set_xscale('log')
        else:
            ax.set_xlim(0.0, model.tmax)
            ax.set_xscale('linear')

        if self.chk_LogY.isChecked():
            ax.set_ylim(0.0001, max(ycar.max(), ywheel.max(), road.max()) * 1.1)
            ax.set_yscale('log')
        else:
            ax.set_ylim(0.0, max(ycar.max(), ywheel.max(), road.max()) * 1.1)
            ax.set_yscale('linear')

        ax.plot(t, ycar, 'b-', label='Body Position')
        ax.plot(t, ywheel, 'r-', label='Wheel Position')
        ax.plot(t, road, 'k--', label='Road')

        if self.chk_ShowAccel.isChecked() and accel is not None:
            ax1.plot(t, accel, 'g-', label='Body Accel')
            ax1.axhline(y=model.accelLim, color='orange')
            ax1.set_yscale('log' if self.chk_LogAccel.isChecked() else 'linear')

        ax.set_ylabel("Vertical Position (m)")
        ax.set_xlabel("Time (s)")
        ax1.set_ylabel("Y'' (g)")

        ax.axvline(x=model.tramp)
        ax.axhline(y=model.ymag)

        ax.grid(True)
        ax.legend(loc="upper left")

        self.canvas.draw()

    def doForcePlot(self, model=None):
        if model.results is None:
            return

        ax = self.forceAx
        ax.clear()

        t = model.timeData

        ax.plot(t, model.springForce, label="Suspension Spring Force")
        ax.plot(t, model.damperForce, label="Dashpot Force")
        ax.plot(t, model.tireForce, label="Tire Spring Force")

        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Force (N)")
        ax.set_title("Forces vs. Time")
        ax.grid(True)
        ax.legend(loc="best")

        self.forceCanvas.draw()


class CarController:
    def __init__(self, args):
        self.input_widgets, self.display_widgets = args

        self.le_m1, self.le_v, self.le_k1, self.le_c1, self.le_m2, self.le_k2, self.le_ang, \
            self.le_tmax, self.chk_IncludeAccel = self.input_widgets

        self.gv_Schematic, self.chk_LogX, self.chk_LogY, self.chk_LogAccel, \
            self.chk_ShowAccel, self.lbl_MaxMinInfo, self.layout_horizontal_main = self.display_widgets

        self.model = CarModel()
        self.view = CarView(args)
        self.view.updateView(self.model)

    def road_y(self, t):
        if t < self.model.tramp:
            return self.model.ymag * (t / self.model.tramp)
        return self.model.ymag

    def ode_system(self, X, t):
        y = self.road_y(t)

        x1 = X[0]
        x1dot = X[1]
        x2 = X[2]
        x2dot = X[3]

        x1ddot = (
            -self.model.k1 * (x1 - x2)
            - self.model.c1 * (x1dot - x2dot)
        ) / self.model.m1

        x2ddot = (
            self.model.k1 * (x1 - x2)
            + self.model.c1 * (x1dot - x2dot)
            - self.model.k2 * (x2 - y)
        ) / self.model.m2

        return [x1dot, x1ddot, x2dot, x2ddot]

    def calculate(self, doCalc=True):
        self.model.m1 = float(self.le_m1.text())
        self.model.m2 = float(self.le_m2.text())
        self.model.c1 = float(self.le_c1.text())
        self.model.k1 = float(self.le_k1.text())
        self.model.k2 = float(self.le_k2.text())
        self.model.v = float(self.le_v.text())
        self.model.yangdeg = float(self.le_ang.text())
        self.model.tmax = float(self.le_tmax.text())

        g = 9.81
        self.model.mink1 = (self.model.m1 * g) / 0.1524
        self.model.maxk1 = (self.model.m1 * g) / 0.0762
        self.model.mink2 = (self.model.m2 * g) / 0.0381
        self.model.maxk2 = (self.model.m2 * g) / 0.01905

        self.model.ymag = 6.0 / (12.0 * 3.3)

        if doCalc:
            self.doCalc()

        self.SSE((self.model.k1, self.model.c1, self.model.k2), optimizing=False)
        self.view.updateView(self.model)

    def doCalc(self, doPlot=True, doAccel=True):
        v = 1000.0 * self.model.v / 3600.0
        self.model.angrad = self.model.yangdeg * math.pi / 180.0

        if v <= 0 or math.sin(self.model.angrad) <= 0:
            self.model.tramp = 1.0
        else:
            self.model.tramp = self.model.ymag / (math.sin(self.model.angrad) * v)

        self.model.t = np.linspace(0, self.model.tmax, 2000)
        self.model.timeData = self.model.t

        ic = [0, 0, 0, 0]
        self.model.results = odeint(self.ode_system, ic, self.model.t)

        self.calculateRoadData()
        self.calculateForceData()

        if doAccel:
            self.calcAccel()

        if doPlot:
            self.doPlot()

    def calculateRoadData(self):
        self.model.roadData = np.array([self.road_y(ti) for ti in self.model.t])

    def calculateForceData(self):
        x1 = self.model.results[:, 0]
        x1dot = self.model.results[:, 1]
        x2 = self.model.results[:, 2]
        x2dot = self.model.results[:, 3]
        y = self.model.roadData

        self.model.springForce = self.model.k1 * (x1 - x2)
        self.model.damperForce = self.model.c1 * (x1dot - x2dot)
        self.model.tireForce = self.model.k2 * (x2 - y)

    def calcAccel(self):
        N = len(self.model.t)
        self.model.accel = np.zeros(shape=N)
        vel = self.model.results[:, 1]

        for i in range(N):
            if i == N - 1:
                h = self.model.t[i] - self.model.t[i - 1]
                self.model.accel[i] = (vel[i] - vel[i - 1]) / (9.81 * h)
            else:
                h = self.model.t[i + 1] - self.model.t[i]
                self.model.accel[i] = (vel[i + 1] - vel[i]) / (9.81 * h)

        self.model.accelData = self.model.accel
        self.model.accelMax = np.max(np.abs(self.model.accel))
        return True

    def OptimizeSuspension(self):
        self.calculate(doCalc=False)

        x0 = np.array([
            self.model.k1,
            self.model.c1,
            self.model.k2
        ])

        answer = minimize(
            self.SSE,
            x0,
            method='Nelder-Mead',
            options={
                'maxiter': 300,
                'xatol': 1e-3,
                'fatol': 1e-3
            }
        )

        self.model.k1, self.model.c1, self.model.k2 = answer.x

        self.le_k1.setText(f"{self.model.k1:.2f}")
        self.le_c1.setText(f"{self.model.c1:.2f}")
        self.le_k2.setText(f"{self.model.k2:.2f}")

        self.calculate(doCalc=True)

    def SSE(self, vals, optimizing=True):
        k1, c1, k2 = vals

        self.model.k1 = k1
        self.model.c1 = c1
        self.model.k2 = k2

        self.doCalc(doPlot=False)

        SSE = 0.0

        for i in range(len(self.model.results[:, 0])):
            t = self.model.t[i]
            ycar = self.model.results[:, 0][i]

            if t < self.model.tramp:
                ytarget = self.model.ymag * (t / self.model.tramp)
            else:
                ytarget = self.model.ymag

            SSE += (ycar - ytarget) ** 2

        if optimizing:
            if k1 < self.model.mink1:
                SSE += 1000000.0 * (self.model.mink1 - k1) ** 2
            if k1 > self.model.maxk1:
                SSE += 1000000.0 * (k1 - self.model.maxk1) ** 2

            if k2 < self.model.mink2:
                SSE += 1000000.0 * (self.model.mink2 - k2) ** 2
            if k2 > self.model.maxk2:
                SSE += 1000000.0 * (k2 - self.model.maxk2) ** 2

            if c1 < 10:
                SSE += 1000000.0 * (10 - c1) ** 2

            if self.chk_IncludeAccel.isChecked():
                if self.model.accelMax > self.model.accelLim:
                    SSE += 1000.0 * (self.model.accelMax - self.model.accelLim) ** 2

        self.model.SSE = SSE
        return SSE

    def doPlot(self):
        self.view.doPlot(self.model)
        self.view.doForcePlot(self.model)


def main():
    pass


if __name__ == '__main__':
    main()