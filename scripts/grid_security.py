"""
MICRO-HYDROPOWER DESIGN PART III
GRID SECURITY, CONTINGENCY & PROTECTION ANALYSIS (POWSYBL)

Matches Part II pandapower topology:
Slack → Bus1 → Bus2 → Bus3 → Transformer → Micro-hydro (0.48 kV)
"""

import pypowsybl as pp
import pypowsybl.loadflow as lf
import pypowsybl.security as sec


class HydroPowSyBlStudy:
    def __init__(self):
        self.network = None

    # -----------------------------
    # 1. BUILD NETWORK (MATCHES PANDAPOWER)
    # -----------------------------
    def build_network(self):
        self.network = pp.network.create_empty()

        # Substation
        self.network.create_substations(id="S1")

        # HV Level (12.47 kV)
        self.network.create_voltage_levels(
            id="VL_HV",
            substation_id="S1",
            nominal_v=12.47,
            topology_kind="BUS_BREAKER"
        )

        # LV Level (0.48 kV)
        self.network.create_voltage_levels(
            id="VL_LV",
            substation_id="S1",
            nominal_v=0.48,
            topology_kind="BUS_BREAKER"
        )

        # -----------------------------
        # BUSES (MATCHING YOUR MODEL)
        # -----------------------------
        self.network.create_buses(id="SLACK_BUS", voltage_level_id="VL_HV")
        self.network.create_buses(id="BUS_1", voltage_level_id="VL_HV")
        self.network.create_buses(id="BUS_2", voltage_level_id="VL_HV")
        self.network.create_buses(id="BUS_3", voltage_level_id="VL_HV")
        self.network.create_buses(id="BUS_LV", voltage_level_id="VL_LV")

        # -----------------------------
        # EXTERNAL GRID (Slack)
        # -----------------------------
        self.network.create_voltage_source(
            id="GRID",
            bus_id="SLACK_BUS",
            p=0.0,
            q=0.0,
            v=1.0,
            angle=0.0
        )

        # -----------------------------
        # LINES (same 1 km segments)
        # -----------------------------
        self.network.create_line(
            id="LINE_0_1",
            bus1_id="SLACK_BUS",
            bus2_id="BUS_1",
            r=0.40,
            x=0.30,
            g1=0.0,
            b1=0.0
        )

        self.network.create_line(
            id="LINE_1_2",
            bus1_id="BUS_1",
            bus2_id="BUS_2",
            r=0.40,
            x=0.30,
            g1=0.0,
            b1=0.0
        )

        self.network.create_line(
            id="LINE_2_3",
            bus1_id="BUS_2",
            bus2_id="BUS_3",
            r=0.40,
            x=0.30,
            g1=0.0,
            b1=0.0
        )

        # -----------------------------
        # LOADS (MATCH YOUR MW VALUES)
        # -----------------------------
        self.network.create_load(
            id="LOAD_1",
            bus_id="BUS_1",
            p0=0.04,
            q0=0.015
        )

        self.network.create_load(
            id="LOAD_2",
            bus_id="BUS_2",
            p0=0.03,
            q0=0.01
        )

        self.network.create_load(
            id="LOAD_3",
            bus_id="BUS_3",
            p0=0.05,
            q0=0.02
        )

        # -----------------------------
        # TRANSFORMER (12.47/0.48 kV)
        # -----------------------------
        self.network.create_2_windings_transformer(
            id="TRAFO",
            bus1_id="BUS_3",
            bus2_id="BUS_LV",
            rated_u1=12.47,
            rated_u2=0.48,
            r=0.012,
            x=0.06
        )

        # -----------------------------
        # MICRO-HYDRO GENERATOR (100 kW)
        # -----------------------------
        self.network.create_generator(
            id="HYDRO",
            bus_id="BUS_LV",
            p=0.10,
            q=0.0,
            voltage_regulator_on=True,
            target_v=1.02
        )

    # -----------------------------
    # 2. BASE LOAD FLOW
    # -----------------------------
    def run_loadflow(self):
        result = lf.run_ac(self.network)
        print("\nBASE CASE LOAD FLOW COMPLETED")
        print(result)

    # -----------------------------
    # 3. CONTINGENCY ANALYSIS
    # -----------------------------
    def run_contingencies(self):
        print("\n==============================")
        print("N-1 CONTINGENCY ANALYSIS")
        print("==============================")

        # Define contingencies
        contingencies = sec.create_contingency_list()

        contingencies.add_line_contingency("LINE_1_2")
        contingencies.add_line_contingency("LINE_2_3")
        contingencies.add_line_contingency("LINE_0_1")
        contingencies.add_transformer_contingency("TRAFO")
        contingencies.add_generator_contingency("HYDRO")

        # Run security analysis
        results = sec.run_ac_security_analysis(self.network, contingencies)

        print(results)

    # -----------------------------
    # 4. SIMPLE SECURITY CHECKS
    # -----------------------------
    def check_violations(self):
        lf.run_ac(self.network)

        buses = self.network.get_buses()
        lines = self.network.get_lines()

        print("\n==============================")
        print("VOLTAGE PROFILE")
        print("==============================")

        for _, row in buses.iterrows():
            v = row.get("v_mag", None)
            print(row.name, "V =", v)

        print("\n==============================")
        print("LINE FLOW CHECK")
        print("==============================")

        print(lines)


# -----------------------------
# MAIN EXECUTION
# -----------------------------
if __name__ == "__main__":
    study = HydroPowSyBlStudy()

    study.build_network()
    study.run_loadflow()
    study.check_violations()
    study.run_contingencies()