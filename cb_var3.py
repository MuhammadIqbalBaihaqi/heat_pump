import numpy as np
from TSdiagram import TSdiagram
import matplotlib.pyplot as plt
import CoolProp.CoolProp as CP
import copy  # For optimization
import printer as prt
from pymoo.core.problem import Problem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.visualization.scatter import Scatter
# --- [PERUBAHAN] Impor class, bukan modul ---
from heat_pump_rec import HeatPumpRec # <-- GANTI INI
from orc_model_complete import ORCSuperRec


def calculate_tes_performance(heat_rate_to_tes, fusion_heat, volume_tes, tes_density, heat_rate_demand):
    """
    Calculates TES mass and charging time based on heat input.
    """
    mass_tes = volume_tes * tes_density  # kg
    tes_energy = mass_tes * fusion_heat * 1000 # J

    discharging_time = tes_energy / heat_rate_demand  # s
    
    if heat_rate_to_tes <= 0:
        return mass_tes, float('inf') # Avoid division by zero
        
    charging_time_s = tes_energy / heat_rate_to_tes  # s
    return mass_tes, charging_time_s / 3600, discharging_time / 3600  # hours

# -----------------------------------------------------------------
# --- Main Simulation Function (REFACTORED for HP and ORC)
# -----------------------------------------------------------------

def run_simulation(params):
    """
    Runs the complete Carnot Battery simulation for one set of parameters.
    (REFACTORED to use HeatPumpRec and ORCSuperRec classes)
    """
    try:
        # ==========================================================
        # 1. --- Prepare and Run Heat Pump Simulation (REFACTORED) ---
        # ==========================================================
        
        # Gabungkan SEMUA input untuk class HeatPumpRec
        hp_inputs = {
            # Input dari hp_rec_after_cds
            "fluid": params["wf_hp"],
            "T_sf_out": params["T_melting"] + 5 + 273.15,
            "T_wh_in": params["T_wh"] + 273.15,
            "T_pinch_sf_out": params["T_pinch_sf_out"],
            "T_pinch_wh_in": params["T_pinch_wh_in"],
            "T_pinch_sf_in": params["T_pinch_sf_in"],
            "delta_sup": params["delta_sup"],
            "w_cpr_kw": params["cpr_pwr"],
            "eta_cpr": params["eta_cpr"],
            
            # Input dari mass_flow_calculation_revised
            "wh_mass_flow": params["wh_mass_flow"],
            "p_wh": params["p_wh"],
            "p_sf": params["p_sf"],
            "wh_fluid": params["wh_fluid"],
            "sf_fluid": params["sf_fluid"],
        }
        
        # Buat objek HP dan jalankan simulasi
        my_heat_pump = HeatPumpRec(**hp_inputs)
        my_heat_pump.run_simulation()

        # Panggil semua method printer HP baru
        print("\n--- [START] Heat Pump Simulation Details ---")
        # my_heat_pump.print_state_information()
        # my_heat_pump.print_wh_prop()
        # my_heat_pump.print_sf_prop()
        # my_heat_pump.print_mass_flow()
        # my_heat_pump.print_energy_and_performance() # Ini yang ada COP-nya
        print("--- [END] Heat Pump Simulation Details ---\n")

        # ==========================================================
        # 2. --- Extract HP Results for TES Calculation ---
        # ==========================================================
        
        # Ambil data dari object, bukan dari tuple/dict lama
        h_sf_in = my_heat_pump.external_fluid_results['h_sf_in']
        h_sf_out = my_heat_pump.external_fluid_results['h_sf_out']
        sf_mass_flow = my_heat_pump.external_fluid_results['sf_mass_flow']
        
        # Hapus printer lama, karena sudah diganti method di atas
        # T_wh_out = my_heat_pump.external_fluid_results['T_wh_out']
        # T_wh_dict = {"T_wh_out": T_wh_out, "T_wh_in": params["T_wh"] + 273.15}
        # T_sf_dict = my_heat_pump.sf_temps
        # prt.print_temperature_table(T_wh_dict, ...)
        # prt.print_temperature_table(T_sf_dict, ...)
        
        print(f"TES melting Temperature: {params['T_melting']} °C")
        heat_rate_to_tes_W = sf_mass_flow * (h_sf_out - h_sf_in)
        
        # ==========================================================
        # 3. --- Prepare and Run ORC Simulation (Already Refactored) ---
        # ==========================================================
        
        orc_inputs = {
            "fluid": params["cycle_hp"],
            "hs_fluid": params["hs_fluid"],
            "cs_fluid": "Air",
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
            "p_cs_in": params["p_cs"],
            "wf_mass_flow": params["orc_mass_flow_assumption"],
        }
        
        my_orc_cycle = ORCSuperRec(**orc_inputs)
        my_orc_cycle.run_simulation()
        orc_performance_results = my_orc_cycle.calculate_performance()

        # Panggil semua method printer ORC
        print("\n--- [START] ORC Simulation Details ---")
        # my_orc_cycle.print_state_information()
        # my_orc_cycle.print_hs_prop()
        # my_orc_cycle.print_cs_prop()
        # my_orc_cycle.print_delta_enthalpy_real()
        # my_orc_cycle.print_mass_flow()
        # my_orc_cycle.print_energy_transfer()
        print("--- [END] ORC Simulation Details ---\n")

        # ==========================================================
        # 4. --- Calculate TES Charging Time ---
        # ==========================================================
        mass_tes, charging_time_hr, discharge_time_hr = calculate_tes_performance(
            heat_rate_to_tes_W,
            params["fusion_heat"],
            params["volume_tes"],
            params["tes_density"],
            my_orc_cycle.sim_results["Q_demand_hs"] 
        )

        # ==========================================================
        # 5. --- Calculate Final KPIs ---
        # ==========================================================
        eta_thermal_orc = orc_performance_results["eta_thermal"]
        power_net_orc = orc_performance_results["W_dot_net_kW"] # kW
        cop_hp = my_heat_pump.performance["COP_hp"] # Ambil dari object HP
        p2p_ratio = eta_thermal_orc * cop_hp

        # ==========================================================
        # 6. --- Collect and Return Results ---
        # ==========================================================
        return {
            "P2P_Ratio": p2p_ratio,
            "Charging_Time_hr": charging_time_hr,
            "COP_HP": cop_hp,
            "Power_Net_ORC_kW": power_net_orc,
            "Eta_Thermal_ORC": eta_thermal_orc,
            "Heat_Rate_to_TES_W": heat_rate_to_tes_W,
            "Mass_TES_kg": mass_tes,
            "TES_Discharging_Time_hr": discharge_time_hr,
            "SF_Mass_Flow_kgs": sf_mass_flow,
            "HP_Object": my_heat_pump,     # <-- GANTI KE OBJECT
            "ORC_Object": my_orc_cycle,
            "Status": "Success"
        }

    except Exception as e:
        # (Error handling tetap sama, tapi return di-update)
        return {
            "P2P_Ratio": 0.0,
            "Charging_Time_hr": 99999,
            "COP_HP": 0.0,
            "Power_Net_ORC_kW": 0.0,
            "Eta_Thermal_ORC": 0.0,
            "Heat_Rate_to_TES_W": 0.0,
            "Mass_TES_kg": 0.0,
            "SF_Mass_Flow_kgs": 0.0,
            "HP_Object": None,      # <-- GANTI KE OBJECT
            "ORC_Object": None,
            "Status": f"Failed: {e}"
        }

# -----------------------------------------------------------------
# --- Plotting Helper Functions (REFACTORED for HP)
# -----------------------------------------------------------------

def plot_hp_cycle(hp_object, fluid_name):
    """Plots the T-S diagram for the Heat Pump cycle from the HP_Object."""
    if hp_object is None:
        print("Cannot plot HP cycle: No data (object is None).")
        return

    # Ambil data state langsung dari object
    try:
        real_states = hp_object.real_states
        # Filter 'None' values, terutama dari state 1_sup
        T_r = np.array([t for t in real_states["T_r"] if t is not None], dtype=float)
        S_r = np.array([s for s in real_states["S_r"] if s is not None], dtype=float)
    
    except (AttributeError, KeyError, TypeError) as e:
        print(f"Cannot plot HP cycle: Data structure error. {e}")
        return

    real_data = (T_r, S_r / 1000) # S_r dari J/kg.K -> kJ/kg.K
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

def plot_orc_cycle(orc_object, fluid_name):
    """Plots the T-S diagram for the ORC cycle from the ORCSuperRec object."""
    if orc_object is None:
        print("Cannot plot ORC cycle: No data (object is None).")
        return
        
    try:
        real_states = orc_object.real_states
        T_r = np.array([t for t in real_states["T"] if t is not None], dtype=float)
        S_r = np.array([s for s in real_states["S"] if s is not None], dtype=float)
    except (AttributeError, KeyError, TypeError) as e:
        print(f"Cannot plot ORC cycle: Data structure error. {e}")
        return
        
    real_data = (T_r, S_r / 1000) # S_r dari J/kg.K -> kJ/kg.K
    ts_plot_data = [real_data]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    TSdiagram(fluid_name,
              process_cycles=ts_plot_data,
              ax=ax,
              zoom_insets=[],
              name_ideal=[],
              name_real=[])
    plt.title(f"ORC T-S Diagram ({fluid_name})")
    plt.show()

class CarnotBatteryProblem(Problem):

    def __init__(self, default_params):
        
        self.default_params = default_params
        
        # Define the decision variables (n_var = 4)
        # x[0] = T_melting (°C)
        # x[1] = T_pinch_rec (K)
        # x[2] = cpr_pwr (kW)
        # x[3] = orc_mass_flow_assumption (kg/s)
        
        # [Lower Bounds]
        xl = np.array([180.0, 3.0, 50.0, 5.0])
        
        # [Upper Bounds]
        xu = np.array([300.0, 15.0, 500.0, 50.0])

        super().__init__(n_var=4,  # Number of decision variables
                         n_obj=2,  # Number of objectives
                         n_constr=1, # Number of constraints
                         xl=xl,    # Lower bounds
                         xu=xu)    # Upper bounds

    def _evaluate(self, x, out, *args, **kwargs):
        # 'x' is a 2D array: (n_solutions, n_variables)
        # We need to loop through each solution
        
        # Pre-allocate arrays for results
        f1_results = np.zeros(len(x)) # Objective 1 (P2P_Ratio)
        f2_results = np.zeros(len(x)) # Objective 2 (Power_Net_ORC_kW)
        g1_results = np.zeros(len(x)) # Constraint 1 (Discharge Time)

        for i, solution in enumerate(x):
            # 1. Create a copy of params for this run
            current_params = copy.deepcopy(self.default_params)
            
            # 2. Map the solution 'x[i]' to the params dict
            current_params["T_melting"] = solution[0]
            current_params["T_pinch_rec"] = solution[1]
            current_params["cpr_pwr"] = solution[2]
            current_params["orc_mass_flow_assumption"] = solution[3]
            # (you could also map all other pinch points to solution[1])
            current_params["T_pinch_hs_in"] = solution[1]
            current_params["T_pinch_sf_out"] = solution[1]
            
            # 3. Run the simulation
            sim_results = run_simulation(current_params)
            
            # 4. Handle simulation failures
            if sim_results["Status"] != "Success":
                # Assign worst possible values
                f1_results[i] = 0.0      # Minimize P2P_Ratio
                f2_results[i] = 0.0      # Minimize Power_Net_ORC_kW
                g1_results[i] = 1000.0   # Heavily violate constraint
            
            else:
                # 5. Get objective values
                # pymoo MINIMIZES by default. 
                # To MAXIMIZE, we return the NEGATIVE.
                f1_results[i] = -sim_results["P2P_Ratio"]
                f2_results[i] = -sim_results["Power_Net_ORC_kW"]
                
                # 6. Get constraint values
                # Constraints must be in the form g(x) <= 0
                # Let's say we require at least 4 hours of discharge time
                min_discharge_time = 4.0 # hours
                g1_results[i] = min_discharge_time - sim_results["TES_Discharging_Time_hr"]

        # 7. Assign all results to the 'out' dictionary
        out["F"] = np.column_stack([f1_results, f2_results])
        out["G"] = np.column_stack([g1_results])
# -----------------------------------------------------------------
# --- Main execution block (REFACTORED)
# -----------------------------------------------------------------
# if __name__ == "__main__":
    
#     # 1. Define all parameters in one place
#     default_params = {
#         # General
#         "T_cs": 20,            # °C, Ambient Temperature
        
#         # Heat Pump
#         "T_wh": 166,           # °C, Ulubelu Geothermal Plant, Indonesia
#         "cpr_pwr": 100,        # kW
#         "wf_hp": "Toluene",
#         "eta_cpr": 0.75,
#         "delta_sup": 20,
        
#         # TES
#         "T_melting": 222,      # °C, Kenisarin, 2009
#         "fusion_heat": 117,    # J/g
#         "volume_tes": 4,       # m3
#         "tes_density": 1993,   # kg/m3
        
#         # Waste Heat (wh)
#         "wh_mass_flow": 715.83, # kg/s
#         "p_wh": 780000,        # Pa (7.8 bar)
#         "wh_fluid": "Water",
        
#         # Secondary Fluid (sf)
#         "p_sf": 200000,        # Pa
#         "sf_fluid": "INCOMP::DowJ2",
        
#         # ORC Cycle (Discharging)
#         "cycle_hp": "Toluene",
#         "p_cs": 200000,        # 2 Bar
#         "p_hs": 200000,        # 2 Bar
#         "eta_exp": 0.85,
#         "eta_pmp": 0.75,
#         "orc_mass_flow_assumption": 10, # kg/s
        
#         # Pinch Points & Assumptions
#         "T_pinch_sf_out": 10,
#         "T_pinch_wh_in": 5,
#         "T_pinch_sf_in": 5,
#         "T_pinch_hs_in": 5,
#         "T_pinch_hs_mid1": 5,
#         "T_estimation_hs": 20,
#         "T_estimation_cs": 5,
#         "T_pinch_cs_mid1": 5,
#         "T_pinch_rec": 5,
#     }

#     # 2. Run a single simulation
#     print("--- Running single simulation with default parameters ---")
#     results = run_simulation(default_params)

#     # 3. Print the key results
#     if results["Status"] == "Success":
#         print("\n" + "="*50)
#         print("          FINAL KEY PERFORMANCE INDICATORS (KPIs)          ")
#         print("="*50)
#         print(f"P2P Ratio: {results['P2P_Ratio']:.4f}")
#         print(f"Charging Time: {results['Charging_Time_hr']:.4f} hours")
#         print(f"Heat Pump COP: {results['COP_HP']:.4f}")
#         print(f"ORC Thermal Efficiency: {results['Eta_Thermal_ORC']:.4f}")
#         print(f"ORC Net Power Output: {results['Power_Net_ORC_kW'] / 1e3:.2f} MW")
#         print(f"Heat Rate to TES: {results['Heat_Rate_to_TES_W'] / 1e6:.2f} MW")
#         print(f"TES Mass: {results['Mass_TES_kg']:.2f} kg")
#         print(f"TES Density: {default_params['tes_density']} kg/m3")
#         print(f"TES Volume: {default_params['volume_tes']} m3")
#         print(f"TES discharging Time: {results['TES_Discharging_Time_hr']:.4f} hours")
#         print(f"Secondary Fluid Mass Flow: {results['SF_Mass_Flow_kgs']:.4f} kg/s")
#         print("="*50)

#         # HAPUS PRINTER LAMA INI
#         # prt.print_state_point_table(results["ORC_Object"]... , orc_labels, ...)
#         # prt.print_state_point_table(results["HP_Object"]... , heat_pump_state_labels, ...)

#         # 4. Plot the results
#         plot_hp_cycle(results["HP_Object"], default_params["wf_hp"]) # <-- GANTI KE OBJECT
#         plot_orc_cycle(results["ORC_Object"], default_params["cycle_hp"])
#     else:
#         print(f"Simulation failed: {results['Status']}")

#     # 5. --- Template for Genetic Algorithm Objective Function ---
    
#     def objective_function(decision_variables):
#         """
#         This is the fitness function for the GA.
#         """
        
#         # Use deepcopy to avoid modifying the original params
#         current_params = copy.deepcopy(default_params)
        
#         # 1. Update params with the GA's values
#         # EXAMPLE:
#         # current_params["T_melting"] = decision_variables[0]
#         # current_params["eta_cpr"] = decision_variables[1]
        
#         # 2. Run the simulation
#         sim_results = run_simulation(current_params)
        
#         # 3. Apply constraints/penalties
#         if sim_results["Status"] != "Success":
#             return 0.0 # Return worst possible score
        
#         # 4. Return the fitness score
#         return sim_results["P2P_Ratio"]

#     print("\nRefactored code is ready for optimization.")


# if __name__ == "__main__":
    
#     # --- [Run your single simulation first - as you already have] ---
#     print("--- Running single simulation with default parameters ---")
#     default_params = {
#         # General
#         "T_cs": 20,            # °C, Ambient Temperature
        
#         # Heat Pump
#         "T_wh": 166,           # °C, Ulubelu Geothermal Plant, Indonesia
#         "cpr_pwr": 100,        # kW
#         "wf_hp": "Toluene",
#         "eta_cpr": 0.75,
#         "delta_sup": 20,
        
#         # TES
#         "T_melting": 222,      # °C, Kenisarin, 2009
#         "fusion_heat": 117,    # J/g
#         "volume_tes": 4,       # m3
#         "tes_density": 1993,   # kg/m3
        
#         # Waste Heat (wh)
#         "wh_mass_flow": 715.83, # kg/s
#         "p_wh": 780000,        # Pa (7.8 bar)
#         "wh_fluid": "Water",
        
#         # Secondary Fluid (sf)
#         "p_sf": 200000,        # Pa
#         "sf_fluid": "INCOMP::DowJ2",
        
#         # ORC Cycle (Discharging)
#         "cycle_hp": "Toluene",
#         "p_cs": 200000,        # 2 Bar
#         "p_hs": 200000,        # 2 Bar
#         "eta_exp": 0.85,
#         "eta_pmp": 0.75,
#         "orc_mass_flow_assumption": 10, # kg/s
        
#         # Pinch Points & Assumptions
#         "T_pinch_sf_out": 10,
#         "T_pinch_wh_in": 5,
#         "T_pinch_sf_in": 5,
#         "T_pinch_hs_in": 5,
#         "T_pinch_hs_mid1": 5,
#         "T_estimation_hs": 20,
#         "T_estimation_cs": 5,
#         "T_pinch_cs_mid1": 5,
#         "T_pinch_rec": 5,
#     } # Your full default_params dict
#     single_results = run_simulation(default_params)
    
#     # ... [your single simulation print/plot logic] ...
    
    
#     # --- [Now, run the optimization] ---
#     print("\n" + "="*50)
#     print("          STARTING MULTI-OBJECTIVE OPTIMIZATION          ")
#     print("="*50)
    
#     # 1. Instantiate the problem
#     problem = CarnotBatteryProblem(default_params)
    
#     # 2. Set up the algorithm (NSGA-II)
#     algorithm = NSGA2(
#         pop_size=50,  # Population size (e.g., 50)
#         eliminate_duplicates=True
#     )
    
#     # 3. Run the optimization
#     res = minimize(problem,
#                    algorithm,
#                    ('n_gen', 40), # Number of generations (e.g., 40)
#                    seed=1,
#                    verbose=False)

#     # 4. Print and Plot the Pareto Front
#     print("="*50)
#     print("          OPTIMIZATION FINISHED          ")
#     print("="*50)
    
#     # 'res.F' stores the objective values. Remember to flip them back!
#     p2p_ratios = -res.F[:, 0]
#     net_power_kw = -res.F[:, 1]
    
#     # 'res.X' stores the decision variables for each solution
#     # x[0] = T_melting, x[1] = T_pinch, etc.
#     solutions = res.X
    
#     print("Found {} optimal trade-off solutions.".format(len(p2p_ratios)))
    
#     # Plot the results
#     plot = Scatter(title="Pareto Front: Efficiency vs. Power Output",
#                    xlabel="P2P Ratio (Efficiency)",
#                    ylabel="Net Power Output (kW)")
#     plot.add(np.column_stack([p2p_ratios, net_power_kw]))
#     plot.show()