import statistics as stats
import random
from Polymer import macroMolecule


class PolymerSimulation:
    def __init__(self, target_N, num_molecules):
        self.target_N = target_N
        self.num_molecules = num_molecules
        self.std_N = 0.1 * target_N

        self.center_of_mass_values = []
        self.end_to_end_values = []
        self.radius_gyration_values = []
        self.degrees = []

    def run(self):
        for i in range(self.num_molecules):
            N = int(random.normalvariate(self.target_N, self.std_N))

            if N < 1:
                N = 1

            polymer = macroMolecule(degreeOfPolymerization=N)
            polymer.freelyJointedChainModel()

            self.degrees.append(N)

            # Convert meters to micrometers
            self.center_of_mass_values.append(polymer.centerOfMass)
            self.end_to_end_values.append(polymer.endToEndDistance * 1e6)
            rg_squared = sum(
                mer.MW * (mer.position.distTo(polymer.centerOfMass) ** 2)
                for mer in polymer.mers
            ) / polymer.MW

            rg = rg_squared ** 0.5

            self.radius_gyration_values.append(rg * 1e6)

    def average_center_of_mass(self):
        avg_x = sum(p.x for p in self.center_of_mass_values) / self.num_molecules
        avg_y = sum(p.y for p in self.center_of_mass_values) / self.num_molecules
        avg_z = sum(p.z for p in self.center_of_mass_values) / self.num_molecules

        # Convert meters to micrometers
        return avg_x * 1e6, avg_y * 1e6, avg_z * 1e6

    def average_end_to_end(self):
        return stats.mean(self.end_to_end_values)

    def std_end_to_end(self):
        return stats.stdev(self.end_to_end_values)

    def average_radius_gyration(self):
        return stats.mean(self.radius_gyration_values)

    def std_radius_gyration(self):
        return stats.stdev(self.radius_gyration_values)

    def pdi(self):
        # PDI = Mw / Mn
        # Since molecular weight is proportional to N,
        # PDI can be calculated using degree of polymerization values.
        Mn = sum(self.degrees) / len(self.degrees)
        Mw = sum(N ** 2 for N in self.degrees) / sum(self.degrees)
        return Mw / Mn


class PolymerCLI:
    def run(self):
        target_N = int(input("Degree of polymerization (1000)?: ") or 1000)
        num_molecules = int(input("How many molecules (50)?: ") or 50)

        sim = PolymerSimulation(target_N, num_molecules)
        sim.run()

        cm_x, cm_y, cm_z = sim.average_center_of_mass()

        print()
        print(f"Metrics for {num_molecules} molecules of degree of polymerization = {target_N}")
        print(f"Avg. Center of Mass (nm) = {cm_x:.3f}, {cm_y:.3f}, {cm_z:.3f}")

        print("End-to-end distance (um):")
        print(f"    Average = {sim.average_end_to_end():.3f}")
        print(f"    Std. Dev. = {sim.std_end_to_end():.3f}")

        print("Radius of gyration (um):")
        print(f"    Average = {sim.average_radius_gyration():.3f}")
        print(f"    Std. Dev. = {sim.std_radius_gyration():.3f}")

        print(f"PDI = {sim.pdi():.2f}")


if __name__ == "__main__":
    app = PolymerCLI()
    app.run()