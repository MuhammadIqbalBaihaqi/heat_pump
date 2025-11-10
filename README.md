

# Carnot Battery (CB) Thermodynamic Simulation

A Python simulation package for analyzing the round-trip (Power-to-Power) efficiency of a Carnot Battery system. This model simulates a complete energy storage cycle composed of a high-temperature heat pump (for charging) and a superheated-recuperated Organic Rankine Cycle (ORC) (for discharging).

This project is built for thermodynamic analysis and optimization, using **CoolProp** for fluid properties and providing visualization with **T-S diagrams**.

## Overview

This repository models a Carnot Battery, a type of Thermal Energy Storage (TES) system that stores electricity as heat and converts it back to electricity when needed.

The simulation operates in two main phases:

1.  **Charging Phase (Heat Pump):**

      * Uses electrical power (`cpr_pwr`) to run a high-temperature heat pump (modeled in `heat_pump.py`).
      * This heat pump upgrades low-grade waste heat (e.g., from a geothermal source) to a high temperature.
      * This high-temperature heat is then used to charge a latent heat Thermal Energy Storage (TES) unit by melting a Phase Change Material (PCM).

2.  **Discharging Phase (ORC):**

      * The high-temperature heat stored in the TES is used as the heat source for a superheated-recuperated Organic Rankine Cycle (ORC) (modeled in `orcsuperrec.py`).
      * The ORC expands a working fluid through a turbine to generate electricity, completing the storage cycle.

The primary goal is to simulate system performance and calculate the **Power-to-Power (P2P) round-trip efficiency**, which is the key metric for this energy storage system.

### Conceptual Workflow

```
(Power In)     +------------+     (High-Temp Heat)     +-------------+
Electricity ───►  Heat Pump ├───────────────────────►  Thermal     │
               │ (Charging)  │                          │ Storage (TES) │
Waste Heat  ───►  (heat_pump.py)├───────────────────────►  (PCM)         │
               +------------+                          +-------------+
                                                               │
                                                               ▼
(Power Out)    +------------+     (High-Temp Heat)     +-------------+
Electricity ◄───   ORC Cycle  ◄───────────────────────   (Discharging) │
               │(Discharging)│                          └─────────────┘
               │(orcsuperrec.py)│
               +------------+
```

## Features

  * **Coupled Simulation:** Integrates a heat pump model and an ORC model into a single simulation workflow.
  * **Thermodynamic Accuracy:** Uses the **CoolProp** library for all fluid property calculations.
  * **Detailed Modeling:** Includes models for a superheated, recuperated ORC and a high-temperature heat pump.
  * **Key Performance Indicators (KPIs):**
      * Calculates the **P2P Round-Trip Efficiency**.
      * Calculates the **Charging Time** for the TES.
      * Determines the Heat Pump **COP** and ORC **Thermal Efficiency**.
  * **Visualization:** Automatically generates **T-S (Temperature-Entropy) diagrams** for both the heat pump and ORC cycles using `TSdiagram.py`.
  * **Optimization-Ready:** The main simulation is wrapped in a `run_simulation` function, with an `objective_function` template ready for integration with optimization libraries (e.g., Genetic Algorithms).

## Project Structure

```
.
├── cb_var1.py         # Main simulation script (Entry Point)
├── heat_pump.py       # Module for the Heat Pump (Charging) cycle
├── orcsuperrec.py     # Module for the ORC (Discharging) cycle
├── TSdiagram.py       # Utility for plotting T-S diagrams
└── requirements.txt   # (Recommended) Python dependencies
```

### File Descriptions

  * **`cb_var1.py`**: This is the main script to run. It contains:
      * The `default_params` dictionary to define all system parameters (temperatures, pressures, fluids, efficiencies, etc.).
      * The `run_simulation` function, which calls the heat pump and ORC modules.
      * The `if __name__ == "__main__":` block that executes the simulation and prints the results.
      * An `objective_function` template for optimization.
  * **`heat_pump.py`**: A library defining the heat pump's thermodynamic cycle. The `hp_rec_after_cds` function is the primary one used by the main script.
  * **`orcsuperrec.py`**: A library defining the ORC's thermodynamic cycle. The `orcsuperrec` function calculates the cycle states, and `calc_thermal_efficiency` determines its performance.
  * **`TSdiagram.py`**: A plotting utility that uses `matplotlib` and `CoolProp` to draw the saturation curve of a fluid and overlay the T-S points of a given cycle.

## Installation

1.  Clone this repository to your local machine:

    ```bash
    git clone <your-repo-url>
    cd <your-repo-name>
    ```

2.  It is highly recommended to use a Python virtual environment:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  Install the required Python packages. You can create a `requirements.txt` file with the following content:

    **requirements.txt**

    ```
    numpy
    matplotlib
    coolprop
    tabulate
    ```

4.  Then, install them all at once:

    ```bash
    pip install -r requirements.txt
    ```

## How to Use

1.  Navigate to the project directory.

2.  Open the `cb_var1.py` file in your editor.

3.  Modify the parameters within the `default_params` dictionary (inside the `if __name__ == "__main__":` block) to match your desired simulation scenario.

    ```python
    default_params = {
        # General
        "T_cs": 20,            # °C, Ambient Temperature
        
        # Heat Pump
        "T_wh": 166,           # °C, Waste Heat Temperature
        "cpr_pwr": 100,        # kW
        "wf_hp": "Toluene",
        
        # TES
        "T_melting": 200,      # °C
        
        # ORC Cycle (Discharging)
        "cycle_hp": "Pentane",
        # ... and all other parameters
    }
    ```

4.  Run the script from your terminal:

    ```bash
    python cb_var1.py
    ```

5.  The script will execute the simulation and print the final KPI report to the console. Matplotlib windows will also open to display the T-S diagrams for the HP and ORC cycles.

    **Example Output:**

    ```
    --- Running single simulation with default parameters ---
    P2P Ratio: 0.1983
    Charging Time: 1.1213 hours
    Heat Pump COP: 3.1415
    ORC Thermal Efficiency: 0.0631
    Heat Rate to TES: 7.08 MW
    TES Mass: 7972.00 kg
    Secondary Fluid Mass Flow: 29.8430 kg/s
    Refactored code is ready for optimization.
    ```

## Optimization

This project is structured to be easily used with optimization algorithms. The `objective_function` in `cb_var1.py` serves as a fitness function for a Genetic Algorithm (GA) or other optimizers.

To use it, you would:

1.  Import an optimization library (e.g., `scipy.optimize`, `pygmo`, `deap`).
2.  Define the bounds for your `decision_variables` (e.g., `T_melting`, `eta_cpr`).
3.  In the `objective_function`, map the array of `decision_variables` to the `current_params` dictionary.
4.  Run your optimizer, telling it to **maximize** the value returned by `objective_function` (which is the `P2P_Ratio`).

<!-- end list -->

```python
def objective_function(decision_variables):
    """
    This is the fitness function for the GA.
    """
    current_params = copy.deepcopy(default_params)
    
    # 1. Update params with the GA's values
    #    EXAMPLE:
    # current_params["T_melting"] = decision_variables[0]
    # current_params["eta_cpr"] = decision_variables[1]
    
    # 2. Run the simulation
    sim_results = run_simulation(current_params)
    
    # 3. Apply constraints/penalties
    if sim_results["Status"] != "Success":
        return 0.0 # Return worst possible score
    
    # 4. Return the fitness score
    #    (We want to MAXIMIZE P2P_Ratio)
    return sim_results["P2P_Ratio"]
```

## License

This project is unlicensed. You are free to use, modify, and distribute this code as you see fit.
