import pypowsybl as pp
import pandas as pd


# ============================================================
# 1. BUILD NETWORK
# ============================================================

def build_network():
    network = pp.network.create_empty()

    # ----------------------------
    # Substation
    # ----------------------------
    network.create_substations(id='SUB1')

    # ----------------------------
    # Voltage levels
    # ----------------------------
    network.create_voltage_levels(
        id='MV',
        substation_id='SUB1',
        nominal_v=12.47,
        topology_kind='BUS_BREAKER'
    )

    network.create_voltage_levels(
        id='LV',
        substation_id='SUB1',
        nominal_v=0.48,
        topology_kind='BUS_BREAKER'
    )

    # ----------------------------
    # Buses
    # ----------------------------
    network.create_buses(id='BUS1', voltage_level_id='MV')
    network.create_buses(id='BUS2', voltage_level_id='MV')
    network.create_buses(id='BUS3', voltage_level_id='MV')
    network.create_buses(id='BUS4', voltage_level_id='LV')

    # ----------------------------
    # Utility Grid / Slack
    # ----------------------------
    network.create_generators(
        id='GRID',
        voltage_level_id='MV',
        bus_id='BUS1',
        target_p=0.0,
        target_v=1.0,
        min_p=-1000.0,
        max_p=1000.0,
        voltage_regulator_on=True
    )

    # ----------------------------
    # Lines
    # ----------------------------
    network.create_lines(
        id='L1',
        voltage_level1_id='MV',
        bus1_id='BUS1',
        voltage_level2_id='MV',
        bus2_id='BUS2',
        r=0.05,
        x=0.08,
        g1=0,
        b1=0,
        g2=0,
        b2=0
    )

    network.create_lines(
        id='L2',
        voltage_level1_id='MV',
        bus1_id='BUS2',
        voltage_level2_id='MV',
        bus2_id='BUS3',
        r=0.05,
        x=0.08,
        g1=0,
        b1=0,
        g2=0,
        b2=0
    )

    # ----------------------------
    # Loads
    # ----------------------------
    network.create_loads(
        id='LOAD1',
        voltage_level_id='MV',
        bus_id='BUS2',
        p0=0.040,   # 40 kW
        q0=0.010
    )

    network.create_loads(
        id='LOAD2',
        voltage_level_id='MV',
        bus_id='BUS3',
        p0=0.035,   # 35 kW
        q0=0.008
    )

    network.create_loads(
        id='LOAD3',
        voltage_level_id='LV',
        bus_id='BUS4',
        p0=0.020,   # 20 kW
        q0=0.005
    )

    # ----------------------------
    # Transformer
    # 12.47 kV -> 0.48 kV
    # ----------------------------
    network.create_2_windings_transformers(
        id='T1',
        voltage_level1_id='MV',
        bus1_id='BUS3',
        voltage_level2_id='LV',
        bus2_id='BUS4',
        rated_u1=12.47,
        rated_u2=0.48,
        rated_s=0.150,   # 150 kVA
        r=0.01,
        x=0.04
    )

    # ----------------------------
    # 100 kW Microhydro generator
    # ----------------------------
    network.create_generators(
        id='HYDRO',
        voltage_level_id='LV',
        bus_id='BUS4',
        target_p=0.100,   # 100 kW
        target_v=1.0,
        min_p=0.0,
        max_p=0.100,
        voltage_regulator_on=False
    )

    return network


# ============================================================
# 2. RUN LOAD FLOW
# ============================================================

def run_loadflow(network, case_name):
    print("\n" + "=" * 60)
    print(f"CASE: {case_name}")
    print("=" * 60)

    result = pp.loadflow.run_ac(network)

    print("\nLoad Flow Status:")
    print(result)

    print("\nBus Results:")
    buses = network.get_buses()
    print(buses[['name', 'v_mag', 'connected_component']])

    print("\nLine Results:")
    lines = network.get_lines()
    print(lines[['name', 'connected1', 'connected2']])

    print("\nTransformer Results:")
    transformers = network.get_2_windings_transformers()
    print(transformers[['name', 'connected1', 'connected2']])


# ============================================================
# 3. CONTINGENCY CASES
# ============================================================

def contingency_line1_outage():
    net = build_network()
    net.disconnect('L1')
    run_loadflow(net, "Contingency A: Line 1 Outage")


def contingency_line2_outage():
    net = build_network()
    net.disconnect('L2')
    run_loadflow(net, "Contingency B: Line 2 Outage")


def contingency_transformer_outage():
    net = build_network()
    net.disconnect('T1')
    run_loadflow(net, "Contingency C: Transformer Outage")


def contingency_generator_outage():
    net = build_network()
    net.disconnect('HYDRO')
    run_loadflow(net, "Contingency D: Generator Outage")


# ============================================================
# 4. MAIN
# ============================================================

if __name__ == "__main__":

    # Base Case
    base_network = build_network()
    run_loadflow(base_network, "Base Case")

    # Contingencies
    contingency_line1_outage()
    contingency_line2_outage()
    contingency_transformer_outage()
    contingency_generator_outage()