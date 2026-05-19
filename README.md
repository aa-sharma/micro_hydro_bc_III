# MICRO-HYDROPOWER DESIGN PART III - FAULT PROTECTION & CONTINGENCY MODELLING
> This projects build on [Part I - Site Assessment](https://github.com/aa-sharma/micro_hydro_bc) and [Part II - Grid Integration & Power System Modelling](https://github.com/aa-sharma/micro_hydro_bc_II/tree/main) where we identified candidate locations for a micro-hydropower plant in rural Southwest British Columbia and conducted load flow analysis for a 100kW plant.
We will now conduct a simiplified grid security and protection analysis using PowSyBl for contingency and outage analysis. We will then apply foundational protection and reliability concepts relevant to distribution interconnection using the IEEE 1547 standards as a guide.

#### Network Area Diagram

 <img src="network_area_diagram.svg" width="100%">


#### Single Line Diagram

 <img src="single_line_diagram.svg" width="75%">




## Simulation
The pypowsybl library in python is used for simulation.

### Load Flow Validation (Base Case)
 <img src="outputs/base_case_lf.png" width="100%">
Since this simulation converged, we can conclude that the base case is stable under normal operating conditions.

### N-1 Contingency Analysis
#### Case 1: Line Outages
##### 1.1: Line 1 Outage (Bus_Slack - Bus1)
This simulation models the behaviour when the main feeder (or primary transmission line) is disconnected from the Slack (external grid)

 <img src="outputs/l1_outage.png" width="100%">

The simulation does not converge (SOLVER_FAILED). Due to the radial topology, when line 1 fails, all components downstream loses connection to the slack bus. Without the reference bus (slack) and a secondary path to the external grid, the simulation fails because the power can no longer be balanced in the subsequently formed island.


##### 1.2: Line 2 Outage (Bus1 - Bus2)
This simulation models the behaviour when the internal trunk line between local load centers fails

 <img src="outputs/l2_outage.png" width="100%">

The results for this case can be interpreted in the same way as for case 1.1.

##### 1.3: Line 3 Outage (Bus2 - Bus3)
This simulation models the behaviour when the dedicated feeder connecting the micro-hydro generator is disconnected

 <img src="outputs/l3_outage.png" width="100%">

This simulation converges. L3 is the link to the micro-hydro substation which fails but the rest of the grid (bus 1 and 2) stay online.

#### Case 2: Transformer Outage

 <img src="outputs/t1_outage.png" width="100%">
The simulation converges, indicating that a transformer outage isolates the micro-hydro generator from the the rest of the utility grid while the HV side continues to function with stability.

#### Case 3: Generator Outage

 <img src="outputs/gen_outage.png" width="100%">
The simulation converges, demonstrating that when the micro-hydro generator trips, the external grid picks up the extra load and the voltages stay relatively stable.

#### Summary of N-1 Contingency Analysis

| Contingency| Result | System Impact |
| ---------- | ----- | ----------|
| L1 Outage | Critical Failure | Blackout (main feeder lost) |
| L2 Outage | Critical Failure | Partial supply interruption (disconnect from grid) |
| L3 Outage | OK | Localized outage (only micro-hydro substation impacted) |
| T1 Outage | OK | Localized outage (LV bus impacted) |
| Micro-hydro Gen Outage | OK | Operational change (slack compensates for lost generation) |



## Proposed Protection Schemes

| Zone| Equipment | Protection |
| ---------- | ----- | ----------|
| Feeder | Lines and loads | OC relay, breaker |
| Transformer | Step-up transformer | Differential and OC |
| Generator | Micro-hydro generator | V/F/reverse power |
| PCC | Interconnection point to ex.t grid | Anti-islanding |


### Feeder Protection Zone
This zone covers the 12.47kV radial feeder:
* Slack Bus - Bus1
* Bus1 - Bus2
* Bus2 - Bus3
* Connected loads

The proposed protection mechanisms for this zone include:
1. Overcurrent Relay (OC) - If current exceeds threshold, trip breaker
2. Breaker - Installed between Slack Bus and Bus1

This mechanism will isolate the faulted segments, providing protection from line-to-ground faults, line-to-line faults, overloads, short circuits, and downstream faults.


### Transformer Protection Zone
This zone covers the 12.4k kV / 0.48kV step-up transformer. Differential protection is proposed for this zone, where the current entering the transformer is compared with the current leaving it. If they are not equal (after ratio adjustment), this indicates an internal fault which will trip the OC relay. This ensures that if the transformer faults, the micro-hydro plant is isolated immediately and the feeder is not exposed.

### Generator Protection Zone
This zone covers the 100kW micro-hydro generator and its associated terminals. The proposed protection mechanisms for this zone include:
1. Voltage protection (ex. 0.88 pu < V < 1.10 pu)
2. Frequency protection
3. Reverse power

If any abnormal conditions are detected (beyond given thresholds), the protective relay opens a breaker to disconnect and isolate the generator.

### PCC / Interconnection Protection Zone
This zone covers Bus3 / transformer HV side at the Point of Common Coupling (PCC) - interface between utility grid and DER (micro-hydro). Proposed protection functions include:
1. Anti-islanding - Disconnect micro-hydro generator if utility grid lost. Without anti-islanding, the generator might continue to power a "dead" section of the grid. This is dangerous for utility workers and can lead to unsynchronized re-closing
2. Rate of Change of Frequency (ROCOF) - Detects sudden grid separation. If frequency change is greater than threshold, relay should trip.
3. Synchronosim Check - Checks and matches voltage magnitude, phase angle, and frequency with the utility grid

These mechanisms ensure rapid disconnection of the micro-hydropower generator under abnormal grid conditions.

Grid -- Bus1 -- Bus2 -- Bus3 -- PCC Breaker + Protection Relay -- Transformer -- Micro-hydro Generator


### Other Recommendations
### Ring Topology
Implementing a ring topology instead of a radial topology, where either Bus2 or Bus3 is also connected back to the Slack bus via  a separate path ensures N-1 compliance. Even if a line in the loop fails, the micro-hydro plant will still be able to export power to the grid. The advantage with radial feeders is that fault current flows in one direction so coordination when something wrong happens is straightforward.
