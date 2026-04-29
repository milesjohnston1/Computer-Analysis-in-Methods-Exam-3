import sys
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QRadioButton,
    QGroupBox, QMessageBox, QCheckBox
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from Air import air


class CycleModel:
    def __init__(self):
        self.air = air()
        self.states = []
        self.upper = []
        self.lower = []
        self.W_comp = 0
        self.W_power = 0
        self.Q_in = 0
        self.Q_out = 0
        self.W_net = 0
        self.eff = 0

    def set_common(self, T1, P1, V1):
        self.air = air()
        s1 = self.air.set(T=T1, P=P1, name="State 1")
        self.n = V1 / s1.v
        return s1

    def calculate_otto(self, T1, P1, V1, CR, T_high):
        s1 = self.set_common(T1, P1, V1)
        s2 = self.air.set(v=s1.v / CR, s=s1.s, name="State 2")
        s3 = self.air.set(T=T_high, v=s2.v, name="State 3")
        s4 = self.air.set(v=s1.v, s=s3.s, name="State 4")

        self.states = [s1, s2, s3, s4]

        self.W_comp = self.n * (s2.u - s1.u)
        self.W_power = self.n * (s3.u - s4.u)
        self.Q_in = self.n * (s3.u - s2.u)
        self.Q_out = self.n * (s4.u - s1.u)

        self.finish()
        self.build_otto_curves()

    def calculate_diesel(self, T1, P1, V1, CR, cutoff):
        s1 = self.set_common(T1, P1, V1)
        s2 = self.air.set(v=s1.v / CR, s=s1.s, name="State 2")
        s3 = self.air.set(P=s2.P, v=s2.v * cutoff, name="State 3")
        s4 = self.air.set(v=s1.v, s=s3.s, name="State 4")

        self.states = [s1, s2, s3, s4]

        self.W_comp = self.n * (s2.u - s1.u)
        self.W_power = self.n * ((s3.u - s4.u) + s2.P * (s3.v - s2.v))
        self.Q_in = self.n * (s3.h - s2.h)
        self.Q_out = self.n * (s4.u - s1.u)

        self.finish()
        self.build_diesel_curves()

    def calculate_dual(self, T1, P1, V1, CR, pressure_ratio, cutoff):
        s1 = self.set_common(T1, P1, V1)
        s2 = self.air.set(v=s1.v / CR, s=s1.s, name="State 2")
        s3 = self.air.set(P=s2.P * pressure_ratio, v=s2.v, name="State 3")
        s4 = self.air.set(P=s3.P, v=s3.v * cutoff, name="State 4")
        s5 = self.air.set(v=s1.v, s=s4.s, name="State 5")

        self.states = [s1, s2, s3, s4, s5]

        self.W_comp = self.n * (s2.u - s1.u)
        self.W_power = self.n * ((s4.u - s5.u) + s3.P * (s4.v - s3.v))
        self.Q_in = self.n * ((s3.u - s2.u) + (s4.h - s3.h))
        self.Q_out = self.n * (s5.u - s1.u)

        self.finish()
        self.build_dual_curves()

    def finish(self):
        self.W_net = self.W_power - self.W_comp
        self.eff = 100 * self.W_net / self.Q_in

    def build_otto_curves(self):
        s1, s2, s3, s4 = self.states
        self.upper = []
        self.lower = []

        a = air()

        for T in np.linspace(s2.T, s3.T, 30):
            self.upper.append(a.set(T=T, v=s2.v))

        for v in np.linspace(s3.v, s4.v, 30):
            self.upper.append(a.set(v=v, s=s3.s))

        for T in np.linspace(s4.T, s1.T, 30):
            self.upper.append(a.set(T=T, v=s1.v))

        for v in np.linspace(s1.v, s2.v, 30):
            self.lower.append(a.set(v=v, s=s1.s))

    def build_diesel_curves(self):
        s1, s2, s3, s4 = self.states
        self.upper = []
        self.lower = []

        a = air()

        for v in np.linspace(s2.v, s3.v, 30):
            self.upper.append(a.set(P=s2.P, v=v))

        for v in np.linspace(s3.v, s4.v, 30):
            self.upper.append(a.set(v=v, s=s3.s))

        for T in np.linspace(s4.T, s1.T, 30):
            self.upper.append(a.set(T=T, v=s1.v))

        for v in np.linspace(s1.v, s2.v, 30):
            self.lower.append(a.set(v=v, s=s1.s))

    def build_dual_curves(self):
        s1, s2, s3, s4, s5 = self.states
        self.upper = []
        self.lower = []

        a = air()

        for T in np.linspace(s2.T, s3.T, 30):
            self.upper.append(a.set(T=T, v=s2.v))

        for v in np.linspace(s3.v, s4.v, 30):
            self.upper.append(a.set(P=s3.P, v=v))

        for v in np.linspace(s4.v, s5.v, 30):
            self.upper.append(a.set(v=v, s=s4.s))

        for T in np.linspace(s5.T, s1.T, 30):
            self.upper.append(a.set(T=T, v=s1.v))

        for v in np.linspace(s1.v, s2.v, 30):
            self.lower.append(a.set(v=v, s=s1.s))


class CycleView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Otto / Diesel / Dual Cycle Calculator")
        self.resize(1100, 850)

        main = QVBoxLayout()

        self.input_box = QGroupBox("Inputs")
        grid = QGridLayout()

        self.cmb_cycle = QComboBox()
        self.cmb_cycle.addItems(["Otto", "Diesel", "Dual"])

        self.rdo_si = QRadioButton("SI")
        self.rdo_eng = QRadioButton("English")
        self.rdo_si.setChecked(True)

        self.le_T1 = QLineEdit("300")
        self.le_P1 = QLineEdit("100000")
        self.le_V1 = QLineEdit("0.003")
        self.le_CR = QLineEdit("18")
        self.le_extra1 = QLineEdit("1500")
        self.le_extra2 = QLineEdit("1.2")

        self.lbl_T1 = QLabel("T1 (K)")
        self.lbl_P1 = QLabel("P1 (Pa)")
        self.lbl_V1 = QLabel("V1 (m^3)")
        self.lbl_CR = QLabel("Compression Ratio")
        self.lbl_extra1 = QLabel("T High (K)")
        self.lbl_extra2 = QLabel("Cutoff Ratio")

        grid.addWidget(QLabel("Cycle Type"), 0, 0)
        grid.addWidget(self.cmb_cycle, 0, 1)
        grid.addWidget(self.rdo_si, 0, 2)
        grid.addWidget(self.rdo_eng, 0, 3)

        grid.addWidget(self.lbl_T1, 1, 0)
        grid.addWidget(self.le_T1, 1, 1)

        grid.addWidget(self.lbl_P1, 2, 0)
        grid.addWidget(self.le_P1, 2, 1)

        grid.addWidget(self.lbl_V1, 3, 0)
        grid.addWidget(self.le_V1, 3, 1)

        grid.addWidget(self.lbl_CR, 4, 0)
        grid.addWidget(self.le_CR, 4, 1)

        grid.addWidget(self.lbl_extra1, 5, 0)
        grid.addWidget(self.le_extra1, 5, 1)

        grid.addWidget(self.lbl_extra2, 6, 0)
        grid.addWidget(self.le_extra2, 6, 1)

        self.btn_calc = QPushButton("Calculate")
        grid.addWidget(self.btn_calc, 7, 0, 1, 2)

        self.input_box.setLayout(grid)
        main.addWidget(self.input_box)

        self.output_box = QGroupBox("Outputs")
        out = QGridLayout()

        self.state_lines = []
        for i in range(5):
            label = QLabel(f"T{i + 1}")
            line = QLineEdit()
            line.setReadOnly(True)
            self.state_lines.append(line)
            out.addWidget(label, i, 0)
            out.addWidget(line, i, 1)

        self.le_Wcomp = QLineEdit()
        self.le_Wpower = QLineEdit()
        self.le_Qin = QLineEdit()
        self.le_Qout = QLineEdit()
        self.le_Wnet = QLineEdit()
        self.le_eff = QLineEdit()

        for line in [self.le_Wcomp, self.le_Wpower, self.le_Qin, self.le_Qout, self.le_Wnet, self.le_eff]:
            line.setReadOnly(True)

        out.addWidget(QLabel("Compression Work"), 0, 2)
        out.addWidget(self.le_Wcomp, 0, 3)

        out.addWidget(QLabel("Power Work"), 1, 2)
        out.addWidget(self.le_Wpower, 1, 3)

        out.addWidget(QLabel("Heat Added"), 2, 2)
        out.addWidget(self.le_Qin, 2, 3)

        out.addWidget(QLabel("Heat Rejected"), 3, 2)
        out.addWidget(self.le_Qout, 3, 3)

        out.addWidget(QLabel("Net Work"), 4, 2)
        out.addWidget(self.le_Wnet, 4, 3)

        out.addWidget(QLabel("Efficiency (%)"), 5, 2)
        out.addWidget(self.le_eff, 5, 3)

        self.output_box.setLayout(out)
        main.addWidget(self.output_box)

        plot_controls = QHBoxLayout()

        self.cmb_x = QComboBox()
        self.cmb_x.addItems(["s", "v", "T", "P"])

        self.cmb_y = QComboBox()
        self.cmb_y.addItems(["T", "P", "v", "s"])

        self.chk_logx = QCheckBox("Log X")
        self.chk_logy = QCheckBox("Log Y")

        plot_controls.addWidget(QLabel("X Axis"))
        plot_controls.addWidget(self.cmb_x)
        plot_controls.addWidget(QLabel("Y Axis"))
        plot_controls.addWidget(self.cmb_y)
        plot_controls.addWidget(self.chk_logx)
        plot_controls.addWidget(self.chk_logy)

        main.addLayout(plot_controls)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        main.addWidget(self.canvas)

        self.setLayout(main)
        self.update_labels()

    def update_labels(self):
        si = self.rdo_si.isChecked()
        cycle = self.cmb_cycle.currentText()

        self.lbl_T1.setText("T1 (K)" if si else "T1 (R)")
        self.lbl_P1.setText("P1 (Pa)" if si else "P1 (atm)")
        self.lbl_V1.setText("V1 (m^3)" if si else "V1 (ft^3)")

        if cycle == "Otto":
            self.lbl_extra1.setText("T High (K)" if si else "T High (R)")
            self.le_extra1.setText("1500" if si else "2700")
            self.lbl_extra2.hide()
            self.le_extra2.hide()

        elif cycle == "Diesel":
            self.lbl_extra1.setText("Cutoff Ratio")
            self.le_extra1.setText("2")
            self.lbl_extra2.hide()
            self.le_extra2.hide()

        else:
            self.lbl_extra1.setText("Pressure Ratio P3/P2")
            self.le_extra1.setText("1.5")
            self.lbl_extra2.setText("Cutoff Ratio")
            self.le_extra2.setText("1.2")
            self.lbl_extra2.show()
            self.le_extra2.show()

        if si:
            self.le_T1.setText("300")
            self.le_P1.setText("100000")
            self.le_V1.setText("0.003")
        else:
            self.le_T1.setText("540")
            self.le_P1.setText("1")
            self.le_V1.setText("0.106")

    def get_inputs(self):
        return {
            "cycle": self.cmb_cycle.currentText(),
            "SI": self.rdo_si.isChecked(),
            "T1": float(self.le_T1.text()),
            "P1": float(self.le_P1.text()),
            "V1": float(self.le_V1.text()),
            "CR": float(self.le_CR.text()),
            "extra1": float(self.le_extra1.text()),
            "extra2": float(self.le_extra2.text()) if self.le_extra2.isVisible() else None,
        }

    def show_error(self, msg):
        QMessageBox.warning(self, "Error", msg)

    def display_results(self, model, SI=True):
        for line in self.state_lines:
            line.clear()

        for i, state in enumerate(model.states):
            T = state.T if SI else state.T * 9 / 5
            self.state_lines[i].setText(f"{T:.3f}")

        energy_factor = 1 if SI else 1 / 1055.06
        unit = "J" if SI else "Btu"

        self.le_Wcomp.setText(f"{model.W_comp * energy_factor:.3f} {unit}")
        self.le_Wpower.setText(f"{model.W_power * energy_factor:.3f} {unit}")
        self.le_Qin.setText(f"{model.Q_in * energy_factor:.3f} {unit}")
        self.le_Qout.setText(f"{model.Q_out * energy_factor:.3f} {unit}")
        self.le_Wnet.setText(f"{model.W_net * energy_factor:.3f} {unit}")
        self.le_eff.setText(f"{model.eff:.3f}")

    def get_prop(self, state, prop, SI=True):
        if prop == "T":
            return state.T if SI else state.T * 9 / 5
        if prop == "P":
            return state.P if SI else state.P / 101325
        if prop == "v":
            return state.v if SI else state.v * 35.3147
        if prop == "s":
            return state.s if SI else state.s / 1055.06 * 453.592 * 5 / 9
        return state.T

    def axis_label(self, prop, SI=True):
        labels_si = {
            "T": "T (K)",
            "P": "P (Pa)",
            "v": "v (m^3/mol)",
            "s": "s (J/mol*K)"
        }

        labels_eng = {
            "T": "T (R)",
            "P": "P (atm)",
            "v": "v (ft^3/lbmol)",
            "s": "s (Btu/lbmol*R)"
        }

        return labels_si[prop] if SI else labels_eng[prop]

    def plot_cycle(self, model, SI=True):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        x_prop = self.cmb_x.currentText()
        y_prop = self.cmb_y.currentText()

        xu = [self.get_prop(s, x_prop, SI) for s in model.upper]
        yu = [self.get_prop(s, y_prop, SI) for s in model.upper]

        xl = [self.get_prop(s, x_prop, SI) for s in model.lower]
        yl = [self.get_prop(s, y_prop, SI) for s in model.lower]

        xs = [self.get_prop(s, x_prop, SI) for s in model.states]
        ys = [self.get_prop(s, y_prop, SI) for s in model.states]

        ax.plot(xu, yu, label="Cycle Path")
        ax.plot(xl, yl, label="Compression")
        ax.plot(xs, ys, "o", label="States")

        for i, (x, y) in enumerate(zip(xs, ys), start=1):
            ax.annotate(str(i), (x, y))

        ax.set_xlabel(self.axis_label(x_prop, SI))
        ax.set_ylabel(self.axis_label(y_prop, SI))
        ax.grid(True)
        ax.legend()

        if self.chk_logx.isChecked():
            ax.set_xscale("log")
        if self.chk_logy.isChecked():
            ax.set_yscale("log")

        self.canvas.draw()


class CycleController:
    def __init__(self):
        self.model = CycleModel()
        self.view = CycleView()

        self.view.btn_calc.clicked.connect(self.calculate)
        self.view.cmb_cycle.currentIndexChanged.connect(self.view.update_labels)
        self.view.rdo_si.toggled.connect(self.view.update_labels)
        self.view.rdo_eng.toggled.connect(self.view.update_labels)

        self.view.cmb_x.currentIndexChanged.connect(self.replot)
        self.view.cmb_y.currentIndexChanged.connect(self.replot)
        self.view.chk_logx.stateChanged.connect(self.replot)
        self.view.chk_logy.stateChanged.connect(self.replot)

    def convert_inputs(self, data):
        SI = data["SI"]

        if SI:
            T1 = data["T1"]
            P1 = data["P1"]
            V1 = data["V1"]
            extra1 = data["extra1"]
        else:
            T1 = data["T1"] * 5 / 9
            P1 = data["P1"] * 101325
            V1 = data["V1"] / 35.3147
            extra1 = data["extra1"] * 5 / 9 if data["cycle"] == "Otto" else data["extra1"]

        return T1, P1, V1, data["CR"], extra1, data["extra2"]

    def calculate(self):
        try:
            data = self.view.get_inputs()
            T1, P1, V1, CR, extra1, extra2 = self.convert_inputs(data)

            if data["cycle"] == "Otto":
                self.model.calculate_otto(T1, P1, V1, CR, extra1)

            elif data["cycle"] == "Diesel":
                self.model.calculate_diesel(T1, P1, V1, CR, extra1)

            else:
                self.model.calculate_dual(T1, P1, V1, CR, extra1, extra2)

            self.view.display_results(self.model, data["SI"])
            self.view.plot_cycle(self.model, data["SI"])

        except Exception as e:
            self.view.show_error(f"Could not calculate cycle.\n\n{e}")

    def replot(self):
        if len(self.model.states) > 0:
            SI = self.view.rdo_si.isChecked()
            self.view.plot_cycle(self.model, SI)

    def run(self):
        self.view.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = CycleController()
    controller.run()
    sys.exit(app.exec_())