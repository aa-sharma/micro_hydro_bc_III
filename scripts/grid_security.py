"""
MICRO-HYDROPOWER DESIGN PART III
GRID SECURITY, CONTINGENCY & PROTECTION ANALYSIS (POWSYBL)

Matches Part II pandapower topology:
Slack → Bus1 → Bus2 → Bus3 → Transformer → Micro-hydro (0.48 kV)
"""
import pypowsybl as psb
from pypowsybl.loadflow import VoltageInitMode


class GridSecurity:
    def __init__(self):
        self.net = None

    def full_config_setup(self):
        self.net = psb.network.create_empty()
        vn_hv = 12.47
        vn_lv = 0.48

        # 1. Substations & Voltage Levels
        self.net.create_substations(id=["Sub_Main", "Sub_Hydro"])
        self.net.create_voltage_levels(
            id=["VL_Main", "VL_Hydro_HV", "VL_Hydro_LV"],
            substation_id=["Sub_Main", "Sub_Hydro", "Sub_Hydro"],
            nominal_v=[vn_hv, vn_hv, vn_lv],
            topology_kind=["BUS_BREAKER"] * 3
        )

        # 2. Buses
        self.net.create_buses(
            id=["Bus_Slack", "Bus_1", "Bus_2", "Bus_3", "Bus_LV"],
            voltage_level_id=["VL_Main", "VL_Main", "VL_Main", "VL_Hydro_HV", "VL_Hydro_LV"]
        )

        # 3. Slack Generator (The Master Reference)
        self.net.create_generators(
            id="Slack_Gen",
            voltage_level_id="VL_Main",
            bus_id="Bus_Slack",
            target_p=0.0,
            target_v=vn_hv,
            voltage_regulator_on=True, # This makes it the Slack
            rated_s=999.0,             # Infinite bus equivalent
            min_p=-999.0,
            max_p=999.0,
            energy_source="OTHER"
        )

        # 4. Lines
        self.net.create_lines(
            id=["L1", "L2", "L3"],
            voltage_level1_id=["VL_Main", "VL_Main", "VL_Main"],
            bus1_id=["Bus_Slack", "Bus_1", "Bus_2"],
            voltage_level2_id=["VL_Main", "VL_Main", "VL_Hydro_HV"],
            bus2_id=["Bus_1", "Bus_2", "Bus_3"],
            r=[0.4] * 3, x=[0.3] * 3, g1=[0.0] * 3, g2=[0.0] * 3, b1=[0.0] * 3, b2=[0.0] * 3
        )

        # 5. Transformer (The "Bridge")
        # We use a very low impedance to ensure the solver 'links' the two voltage levels
        self.net.create_2_windings_transformers(
            id="T1",
            voltage_level1_id="VL_Hydro_HV", bus1_id="Bus_3",
            voltage_level2_id="VL_Hydro_LV", bus2_id="Bus_LV",
            rated_u1=vn_hv, rated_u2=vn_lv, rated_s=0.15,
            r=0.01, x=0.05, g=0.0, b=0.0 
        )

        # 6. Loads
        self.net.create_loads(
            id=["Ld1", "Ld2", "Ld3"],
            voltage_level_id=["VL_Main", "VL_Main", "VL_Hydro_HV"],
            bus_id=["Bus_1", "Bus_2", "Bus_3"],
            p0=[0.04, 0.03, 0.05], q0=[0.01, 0.01, 0.01]
        )

        # 7. Micro-Hydro (Set as a PQ Generator)
        self.net.create_generators(
            id="Hydro_Gen",
            voltage_level_id="VL_Hydro_LV", bus_id="Bus_LV",
            target_p=0.1, target_q=-0.02, rated_s=0.12,
            min_p=0.0, max_p=0.1,
            voltage_regulator_on=False # PQ mode, ensures it doesn't fight the Slack
        )

    # -----------------------------
    # 2. BASE LOAD FLOW
    # -----------------------------
    def run_loadflow(self):
        result = psb.loadflow.run_ac(self.net)
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
        contingencies = psb.security.create_contingency_list()

        contingencies.add_line_contingency("LINE_1_2")
        contingencies.add_line_contingency("LINE_2_3")
        contingencies.add_line_contingency("LINE_0_1")
        contingencies.add_transformer_contingency("TRAFO")
        contingencies.add_generator_contingency("HYDRO")

        # Run security analysis
        results = psb.security.run_ac_security_analysis(self.net, contingencies)

        print(results)

    # -----------------------------
    # 4. SIMPLE SECURITY CHECKS
    # -----------------------------
    def check_violations(self):
        psb.loadflow.run_ac(self.net)

        buses = self.net.get_buses()
        lines = self.net.get_lines()

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



if __name__ == "__main__":
    gs_obj = GridSecurity()
    gs_obj.full_config_setup()
    
    # Use the Enum-based parameters that we established earlier
    parameters = psb.loadflow.Parameters(voltage_init_mode=VoltageInitMode.UNIFORM_VALUES, distributed_slack=False, read_slack_bus=True)
    
    try:
        results = psb.loadflow.run_ac(gs_obj.net, parameters)
        print(f"\nResults: {results}\n")
        
        if results[0].status_text == "Converged":
            print("Load flow converged successfully!")
            # Format output for readability
            df_buses = gs_obj.net.get_buses()[['v_mag', 'v_angle', 'voltage_level_id']]
            print("\n--- Bus Voltage Results ---")
            print(df_buses.to_string())


            gs_obj.run_loadflow()
            gs_obj.check_violations()
            gs_obj.run_contingencies()


        else:
            print(f"Load flow Failed: {results[0].status_text}")
            if results[0].slack_bus_results:
                print(f"Mismatch Details: {results[0].slack_bus_results}")
                
    except Exception as e:
        print(f"An execution error occurred: {e}")
