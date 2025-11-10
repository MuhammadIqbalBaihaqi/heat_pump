import heat_pump as hp
import numpy as np
from TSdiagram import TSdiagram
import matplotlib.pyplot as plt
import CoolProp.CoolProp as CP
import orcsuperrec as osr
import copy  # For optimization

# -----------------------------------------------------------------
# --- Helper Functions
# -----------------------------------------------------------------

def calculate_tes_charging(heat_rate_to_tes, fusion_heat, volume_tes, tes_density):
    """
    Calculates TES mass and charging time based on heat input.
    (This is the refactored 'tes_mass_calc' function from your script)
    """
    mass_tes = volume_tes * tes_density  # kg
    tes_energy = mass_tes * fusion_heat  # J
    
    if heat_rate_to_tes <= 0:
        return mass_tes, float('inf') # Avoid division by zero
        
    charging_time_s = tes_energy / heat_rate_to_tes  # s
    return mass_tes, charging_time_s / 3600 # hours

# -----------------------------------------------------------------
# --- Main Simulation Function
# -----------------------------------------------------------------

def run_simulation(params):
    """
    Runs the complete Carnot Battery simulation for one set of parameters.
    
    Accepts:
        params (dict): A dictionary containing all input parameters.
    
    Returns:
        results (dict): A dictionary of key performance indicators (KPIs)
                        and raw data for plotting.
    """
    try:
        # 1. --- Run Heat Pump Simulation ---
        hp_results = hp.hp_rec_after_cds(
            fluid=params["wf_hp"],
            T_sf_out=params["T_melting"] + 5 + 273.15,  # T melting + 5 K
            T_wh_in=params["T_wh"] + 273.15,
            T_pinch_sf_out=params["T_pinch_sf_out"],
            T_pinch_wh_in=params["T_pinch_wh_in"],
            T_pinch_sf_in=params["T_pinch_sf_in"],
            delta_sup=params["delta_sup"],
            w_cpr_kw=params["cpr_pwr"],
            eta_cpr=params["eta_cpr"]
        )

        # 2. --- Calculate Mass Flows ---
        wh_out_results = hp.mass_flow_calculation_revised(
            params["wh_mass_flow"],
            params["cpr_pwr"],
            params["T_wh"] + 273.15,
            params["p_wh"],
            params["p_sf"],
            params["wh_fluid"],
            params["sf_fluid"],
            hp_results
        )

        h_sf_in = wh_out_results['h_sf_in']
        h_sf_out = wh_out_results['h_sf_out']
        sf_mass_flow = wh_out_results['sf_mass_flow']
        heat_rate_to_tes_W = sf_mass_flow * (h_sf_out - h_sf_in)

        # 3. --- Calculate TES Charging Time ---
        mass_tes, charging_time_hr = calculate_tes_charging(
            heat_rate_to_tes_W,
            params["fusion_heat"],
            params["volume_tes"],
            params["tes_density"]
        )

        # 4. --- Prepare and Run ORC Simulation ---
        # Build the input dictionary from the main params
        orc_inputs = {
            "fluid": params["cycle_hp"],
            "hs_fluid": "Water",  # Fixed as per original script
            "cs_fluid": "Air",    # Fixed as per original script
            "T_hs_in": params["T_melting"] - 5 + 273.15, # T melting - 5 K
            "T_cs_in": params["T_cs"] + 273.15,
            "T_pinch_hs_in": params["T_pinch_hs_in"],
            "T_pinch_hs_mid1": params["T_pinch_hs_mid1"],
            "T_estimation_hs": params["T_estimation_hs"],
            "T_estimation_cs": params["T_estimation_cs"],
            "T_pinch_cs_mid1": params["T_pinch_cs_mid1"],
            "eta_exp": params["eta_exp"],
            "eta_pmp": params["eta_pmp"],
            "T_pinch_rec": params["T_pinch_rec"],
            "p_hs_in": params["p_hs"],
            "p_cs_in": params["p_cs"]
        }
        
        # Run ORC calculation
        orc_full_results = osr.orcsuperrec(**orc_inputs)
        
        # Note: 'orc_mass_flow_assumption' was 10 in your original script.
        # It's now an explicit parameter.
        orc_thermo_results = osr.calc_thermal_efficiency(
            orc_full_results[1]["H_r"],
            params["orc_mass_flow_assumption"]
        )

        # 5. --- Calculate Final KPIs ---
        eta_thermal_orc = orc_thermo_results["eta_thermal"]
        cop_hp = hp_results[2]["COP_hp"]
        p2p_ratio = eta_thermal_orc * cop_hp

        # 6. --- Collect and Return Results ---
        return {
            "P2P_Ratio": p2p_ratio,
            "Charging_Time_hr": charging_time_hr,
            "COP_HP": cop_hp,
            "Eta_Thermal_ORC": eta_thermal_orc,
            "Heat_Rate_to_TES_W": heat_rate_to_tes_W,
            "Mass_TES_kg": mass_tes,
            "SF_Mass_Flow_kgs": sf_mass_flow,
            "HP_Results_Raw": hp_results,        # For plotting
            "ORC_Results_Raw": orc_full_results,  # For plotting
            "Status": "Success"
        }

    except Exception as e:
        # If any calculation fails, return a "bad" fitness score
        return {
            "P2P_Ratio": 0.0, # Penalize heavily
            "Charging_Time_hr": 99999, # Penalize
            "COP_HP": 0.0,
            "Eta_Thermal_ORC": 0.0,
            "Heat_Rate_to_TES_W": 0.0,
            "Mass_TES_kg": 0.0,
            "SF_Mass_Flow_kgs": 0.0,
            "HP_Results_Raw": None,
            "ORC_Results_Raw": None,
            "Status": f"Failed: {e}"
        }

# -----------------------------------------------------------------
# --- Plotting Helper Functions
# -----------------------------------------------------------------

def plot_hp_cycle(hp_results, fluid_name):
    """Plots the T-S diagram for the Heat Pump cycle."""
    if hp_results is None:
        print("Cannot plot HP cycle: No data.")
        return

    # Clean None values from results for plotting
    T_r_obj = np.array(hp_results[0]["T_r"])
    S_r_obj = np.array(hp_results[0]["S_r"])
    
    T_r = T_r_obj[T_r_obj != None].astype(float)
    S_r = S_r_obj[S_r_obj != None].astype(float)

    real_data = (T_r, S_r / 1000)
    ts_plot_data = [real_data]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    TSdiagram(fluid_name,
              process_cycles=ts_plot_data,
              ax=ax,
              zoom_insets=[],
              name_ideal=[],
              name_real=[])
    plt.title(f"Heat Pump T-S Diagram ({fluid_name})")
    plt.show()

def plot_orc_cycle(orc_results, fluid_name):
    """Plots the T-S diagram for the ORC cycle."""
    if orc_results is None:
        print("Cannot plot ORC cycle: No data.")
        return
        
    oser = orc_results[1] # [1] contains the state data
    ideal_data = (np.array(oser["T_r"]), np.array(oser["S_r"]) / 1000)
    ts_plot_data = [ideal_data]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    TSdiagram(fluid_name,
              process_cycles=ts_plot_data,
              ax=ax,
              zoom_insets=[],
              name_ideal=[],
              name_real=[])
    plt.title(f"ORC T-S Diagram ({fluid_name})")
    plt.show()


# -----------------------------------------------------------------
# --- Main execution block (How to use the new structure)
# -----------------------------------------------------------------
if __name__ == "__main__":
    
    # 1. Define all parameters in one place
    default_params = {
        # General
        "T_cs": 20,            # °C, Ambient Temperature
        
        # Heat Pump
        "T_wh": 166,           # °C, Ulubelu Geothermal Plant, Indonesia
        "cpr_pwr": 100,        # kW
        "wf_hp": "Toluene",
        "eta_cpr": 0.75,
        "delta_sup": 30,
        
        # TES
        "T_melting": 200,      # °C, Kenisarin, 2009
        "fusion_heat": 199,    # J/kg
        "volume_tes": 4,       # m3
        "tes_density": 1993,   # kg/m3
        
        # Waste Heat (wh)
        "wh_mass_flow": 715.83, # kg/s
        "p_wh": 780000,        # Pa (7.8 bar)
        "wh_fluid": "Water",
        
        # Secondary Fluid (sf)
        "p_sf": 200000,        # Pa
        "sf_fluid": "INCOMP::DowJ2",
        
        # ORC Cycle (Discharging)
        "cycle_hp": "Pentane",
        "p_cs": 200000,        # 2 Bar
        "p_hs": 200000,        # 2 Bar
        "eta_exp": 0.85,
        "eta_pmp": 0.75,
        "orc_mass_flow_assumption": 10, # kg/s (The '10' from your original script)
        
        # Pinch Points & Assumptions
        "T_pinch_sf_out": 10,
        "T_pinch_wh_in": 5,
        "T_pinch_sf_in": 5,
        "T_pinch_hs_in": 5,
        "T_pinch_hs_mid1": 5,
        "T_estimation_hs": 20,
        "T_estimation_cs": 5,
        "T_pinch_cs_mid1": 5,
        "T_pinch_rec": 5,
    }

    # 2. Run a single simulation
    print("--- Running single simulation with default parameters ---")
    results = run_simulation(default_params)

    # 3. Print the key results
    if results["Status"] == "Success":
        print(f"P2P Ratio: {results['P2P_Ratio']:.4f}")
        print(f"Charging Time: {results['Charging_Time_hr']:.4f} hours")
        print(f"Heat Pump COP: {results['COP_HP']:.4f}")
        print(f"ORC Thermal Efficiency: {results['Eta_Thermal_ORC']:.4f}")
        print(f"Heat Rate to TES: {results['Heat_Rate_to_TES_W'] / 1e6:.2f} MW")
        print(f"TES Mass: {results['Mass_TES_kg']:.2f} kg")
        print(f"Secondary Fluid Mass Flow: {results['SF_Mass_Flow_kgs']:.4f} kg/s")
        
        # 4. Plot the results
        plot_hp_cycle(results["HP_Results_Raw"], default_params["wf_hp"])
        plot_orc_cycle(results["ORC_Results_Raw"], default_params["cycle_hp"])
    else:
        print(f"Simulation failed: {results['Status']}")

    # 5. --- Template for Genetic Algorithm Objective Function ---
    # This is what your GA will call
    
    def objective_function(decision_variables):
        """
        This is the fitness function for the GA.
        It takes a list/array of decision variables, updates the
        parameters, runs the simulation, and returns the fitness score.
        """
        
        # Use deepcopy to avoid modifying the original params
        current_params = copy.deepcopy(default_params)
        
        # 1. Update params with the GA's values
        #    This is where you map the GA's gene array to your variables
        #    EXAMPLE:
        # current_params["T_melting"] = decision_variables[0]
        # current_params["eta_cpr"] = decision_variables[1]
        
        # 2. Run the simulation
        sim_results = run_simulation(current_params)
        
        # 3. Apply constraints/penalties (as discussed before)
        if sim_results["Status"] != "Success":
            return 0.0 # Return worst possible score
        
        # 4. Return the fitness score
        #    (We want to MAXIMIZE P2P_Ratio)
        return sim_results["P2P_Ratio"]

    print("\nRefactored code is ready for optimization.")
