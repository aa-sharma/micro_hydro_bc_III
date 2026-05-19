# MICRO-HYDROPOWER DESIGN PART III - FAULT PROTECTION & CONTINGENCY MODELLING
> This projects build on [Part I - Site Assessment](https://github.com/aa-sharma/micro_hydro_bc) and [Part II - Grid Integration & Power System Modelling](https://github.com/aa-sharma/micro_hydro_bc_II/tree/main) where we identified candidate locations for a micro-hydropower plant in rural Southwest British Columbia and conducted load flow analysis for a 100kW plant.
We will now conduct a simiplified grid security and protection analysis using PowSyBl for contingency and outage analysis. We will then apply foundational protection and reliability concepts relevant to distribution interconnection using the IEEE 1547 standards as a guide.

#### Network Area Diagram

 <img src="network_area_diagram.svg" width="100%">


#### Single Line Diagram

 <img src="single_line_diagram.svg" width="100%">




## Simulation
The pypowsybl library in python is used for simulation.

### Load Flow Validation (Base Case)
 <img src="outputs/base_case_lf.png" width="100%">


### N-1 Contingency Analysis
#### Case 1: Line Outages
##### 1.1: Line 1 Outage (Bus_Slack - Bus1)
This simulation models the behaviour when the main feeder (or primary transmission line) is disconnected from the Slack (external grid)

 <img src="outputs/l1_outage.png" width="100%">



##### 1.2: Line 2 Outage (Bus1 - Bus2)
This simulation models the behaviour when the internal trunk line that between local load centers fails

 <img src="outputs/l2_outage.png" width="100%">



##### 1.3: Line 3 Outage (Bus2 - Bus3)
This simulation models the behaviour when the dedicated feeder connecting the micro-hydro generator is disconnected

 <img src="outputs/l3_outage.png" width="100%">



#### Case 2: Transformer Outage

 <img src="outputs/t1_outage.png" width="100%">


#### Case 3: Generator Outage

 <img src="outputs/gen_outage.png" width="100%">


#### Summary of N-1 Contingency Analysis

| Contingency| Result | System Impact |
| ---------- | ----- | ----------|
| L1 Outage | Critical Failure | Blackout (main feeder lost) |
| L2 Outage | Critical Failure | Partial supply interruption (disconnect from grid) |
| L3 Outage | OK | Localized outage (only micro-hydro substation impacted) |
| T1 Outage | OK | Localized outage (LV bus impacted) |
| Micro-hydro Gen Outage | OK | Operational change (slack compensates for lost generation) |



## Proposed Protection Schemes
