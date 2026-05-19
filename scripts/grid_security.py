"""
MICRO-HYDROPOWER DESIGN PART III
FAULT PROTECTION & CONTINGENCY MODELLING

Slack → Bus1 → Bus2 → Bus3 → Transformer → Micro-hydro (0.48 kV)
"""
import pypowsybl as psb
from pypowsybl.loadflow import VoltageInitMode
from pypowsybl.loadflow import ComponentStatus

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

    def generate_visuals(self, filename_prefix="grid"):
        print("\n--- Generating Network Diagrams ---")
        
        # 1. Global Network Area Diagram (Shows the whole topology)
        self.net.write_network_area_diagram_svg(f"{filename_prefix}_area.svg")
        print(f"Global diagram saved to: {filename_prefix}_area.svg")

        # 2. Detailed Single Line Diagram (SLD) for a specific Substation
        sld_params = psb.network.SldParameters(
            use_name=True,             # Uses "L1", "L2", etc.
            # show_labels=True,          # Explicitly force equipment IDs to show
            nodes_infos=True,          # Adds a legend in the corner
            tooltip_enabled=True       # If viewing in a browser, hover to see the ID
        )

        # Generate SLD for the main substation
        self.net.write_single_line_diagram_svg(
            "Sub_Hydro", 
            f"{filename_prefix}_substation.svg",
            parameters=sld_params
        )
        print(f"Substation SLD saved to: {filename_prefix}_substation.svg")



    # -----------------------------
    # BASE LOAD FLOW
    # -----------------------------
    def run_loadflow(self):
        result = psb.loadflow.run_ac(self.net)
        print("\nBASE CASE LOAD FLOW COMPLETED")
        print(result)

    def run_analysis(self):
        parameters = psb.loadflow.Parameters(voltage_init_mode=VoltageInitMode.UNIFORM_VALUES, distributed_slack=False, read_slack_bus=True)
        try:
            results = psb.loadflow.run_ac(self.net, parameters)
            print(f"\nResults: {results}\n")
            if results[0].status_text == "Converged":
                print("Load flow converged successfully!")
                # Format output for readability
                df_buses = gs_obj.net.get_buses()[['v_mag', 'v_angle', 'voltage_level_id']]
                print("\n--- Bus Voltage Results ---")
                print(df_buses.to_string())
                self.run_loadflow()
                self.check_violations()
            else:
                print(f"Load flow Failed: {results[0].status_text}")
                if results[0].slack_bus_results:
                    print(f"Mismatch Details: {results[0].slack_bus_results}")
        except Exception as e:
            print(f"An execution error occurred: {e}")


    def line_outage(self, line_id):
        print(f"\nLINE OUTAGE (LINE-ID: {line_id})")
        self.net.update_lines(
            id=line_id,
            connected1=False,
            connected2=False
            )
        self.run_analysis()
        # result = psb.loadflow.run_ac(self.net)

    # -----------------------------
    # SIMPLE SECURITY CHECKS
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


    def run_security_analysis(self):
        print("\n==============================")
        print("N-1 CONTINGENCY ANALYSIS")
        print("==============================")

        # 1. Create the Security Analysis object
        analysis = psb.security.create_analysis()

        # 2. Add Contingencies (N-1)
        # Use IDs of lines, transformers, and generators
        analysis.add_single_element_contingency('L1', 'Outage_L1')                  # Line 1 outage
        analysis.add_single_element_contingency('L2', 'Outage_L2')                  # Line 2 outage
        analysis.add_single_element_contingency('L3', 'Outage_L3')                  # Line 3 outage
        analysis.add_single_element_contingency('T1', 'Outage_T1')                  # Transformer outage
        analysis.add_single_element_contingency('Hydro_Gen', 'Outage_Hydro')        # Generator outage

        # 3. Add Monitored Elements
        # This tells the solver to record V, P, and Q for these specific areas
        analysis.add_monitored_elements(
            voltage_level_ids=['VL_Main', 'VL_Hydro_HV', 'VL_Hydro_LV'],
            branch_ids=['L1', 'L2', 'L3', 'T1']
        )

        # 4. Run the AC Analysis
        results = analysis.run_ac(self.net)
        print(f"\nResults: {results}\n")

        # 5. Display Security Violations (Overloads/Undervoltage)
        print("\n--- Limit Violations ---")
        if results.limit_violations is not None and not results.limit_violations.empty:
            print(results.limit_violations)
        else:
            print("No limit violations detected.")

        # 6. Detailed Bus Voltages (Check for Undervoltage)
        print("\n--- Bus Voltages (Post-Contingency) ---")
        # This DataFrame shows v_mag and v_angle for every contingency + bus combination
        print(results.bus_results)

        # 7. Detailed Branch Flows (Check for Overloads/Islanding)
        print("\n--- Branch Flows ---")
        print(results.branch_results)

        # 8. Detect Supply Interruption / Islanding
        for cont_id, post_res in results.post_contingency_results.items():
            print(f"\npost_res: {post_res}\n")
            if not post_res.status != ComponentStatus.CONVERGED:
                print(f"!! ALERT: Contingency {cont_id} caused load flow FAILURE (Supply Interruption)")



if __name__ == "__main__":
    gs_obj = GridSecurity()
    gs_obj.full_config_setup()    
    parameters = psb.loadflow.Parameters(voltage_init_mode=VoltageInitMode.UNIFORM_VALUES, distributed_slack=False, read_slack_bus=True)
    gs_obj.generate_visuals()
    gs_obj.run_analysis()
    gs_obj.run_security_analysis()

