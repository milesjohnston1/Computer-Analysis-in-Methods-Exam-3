import sys
import numpy as np
from scipy.integrate import quad

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QMessageBox
)

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class TakeoffModel:
    def __init__(self):
        self.S = 1000
        self.CLmax = 2.4
        self.CD = 0.0279
        self.rho = 0.002377
        self.gc = 32.174

    def stall_velocity(self, weight):
        return np.sqrt(weight / (0.5 * self.rho * self.S * self.CLmax))

    def takeoff_velocity(self, weight):
        return 1.2 * self.stall_velocity(weight)

    def takeoff_distance(self, thrust, weight):
        V_TO = self.takeoff_velocity(weight)

        A = self.gc * (thrust / weight)
        B = (self.gc / weight) * (0.5 * self.rho * self.S * self.CD)

        # Check that denominator stays positive through takeoff speed
        if A - B * V_TO**2 <= 0:
            return np.nan

        def integrand(V):
            return V / (A - B * V**2)

        S_TO, _ = quad(integrand, 0, V_TO)
        return S_TO

    def make_curve(self, weight):
        thrust_values = np.linspace(1000, 30000, 400)
        valid_thrust = []
        sto_values = []

        for thrust in thrust_values:
            sto = self.takeoff_distance(thrust, weight)

            if not np.isnan(sto) and sto > 0 and sto < 50000:
                valid_thrust.append(thrust)
                sto_values.append(sto)

        return np.array(valid_thrust), np.array(sto_values)


class TakeoffView(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Takeoff Distance Calculator")
        self.setGeometry(200, 200, 900, 650)

        main_layout = QVBoxLayout()
        input_layout = QHBoxLayout()

        self.weight_input = QLineEdit("56000")
        self.thrust_input = QLineEdit("13000")

        input_layout.addWidget(QLabel("Weight:"))
        input_layout.addWidget(self.weight_input)

        input_layout.addWidget(QLabel("Thrust:"))
        input_layout.addWidget(self.thrust_input)

        self.calculate_button = QPushButton("Calculate")
        input_layout.addWidget(self.calculate_button)

        main_layout.addLayout(input_layout)

        self.result_label = QLabel("STO = ")
        main_layout.addWidget(self.result_label)

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        main_layout.addWidget(self.canvas)

        self.setLayout(main_layout)

    def get_inputs(self):
        weight = float(self.weight_input.text())
        thrust = float(self.thrust_input.text())
        return weight, thrust

    def display_result(self, sto):
        self.result_label.setText(f"STO = {sto:.2f}")

    def show_error(self, message):
        QMessageBox.warning(self, "Input Error", message)

    def plot_graph(self, thrust, specified_sto, curves):
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        for thrust_values, sto_values, label in curves:
            ax.plot(thrust_values, sto_values, label=label)

        ax.plot(thrust, specified_sto, "o", markersize=8, label="Specified Point")

        ax.set_xlabel("Thrust")
        ax.set_ylabel("STO")
        ax.set_title("Takeoff Distance vs Thrust")
        ax.grid(True)
        ax.legend()

        ax.set_xlim(0, 30000)
        ax.set_ylim(0, 6000)

        self.canvas.draw()


class TakeoffController:
    def __init__(self):
        self.model = TakeoffModel()
        self.view = TakeoffView()
        self.view.calculate_button.clicked.connect(self.calculate)

    def calculate(self):
        try:
            weight, thrust = self.view.get_inputs()

            if weight <= 10000:
                self.view.show_error("Weight must be greater than 10,000.")
                return

            if thrust <= 0:
                self.view.show_error("Thrust must be positive.")
                return

            specified_sto = self.model.takeoff_distance(thrust, weight)

            if np.isnan(specified_sto):
                self.view.show_error("Thrust is too low for this aircraft to take off.")
                return

            weights = [weight - 10000, weight, weight + 10000]
            curves = []

            for w in weights:
                thrust_values, sto_values = self.model.make_curve(w)
                curves.append((thrust_values, sto_values, f"Weight = {w:.0f}"))

            self.view.display_result(specified_sto)
            self.view.plot_graph(thrust, specified_sto, curves)

        except ValueError:
            self.view.show_error("Please enter valid numbers for weight and thrust.")

    def run(self):
        self.view.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    controller = TakeoffController()
    controller.run()

    sys.exit(app.exec_())