from tabulate import tabulate


def print_temperature_table(temp_dict, temp_labels_map, title="Temperature Properties"):
    """
    Prints a formatted table for a dictionary of temperatures.
    
    This function assumes input temperatures are in Kelvin and converts to Celsius.
    It uses a label map to create human-readable rows in the table.
    
    Args:
        temp_dict (dict): A dictionary of temperatures.
                          e.g., {"T_sf_out_r": 290.15, "T_sf_in_r": 300.15}
        temp_labels_map (dict): A dictionary mapping keys from temp_dict
                                to human-readable labels.
                                e.g., {"T_sf_out_r": "Source Fluid Outlet", 
                                       "T_sf_in_r": "Source Fluid Inlet"}
        title (str, optional): The title for the printed table.
    """
    
    table_data = []
    
    # Iterate through the labels_map. This allows the user to define
    # the order of rows by the order in their labels_map dictionary
    # (for Python 3.7+).
    for key, label in temp_labels_map.items():
        if key in temp_dict:
            temp_k = temp_dict[key]
            try:
                # Convert from Kelvin to Celsius
                temp_c = temp_k - 273.15
                table_data.append([label, f"{temp_c:.2f}"])
            except (TypeError, ValueError):
                # Handle non-numeric data gracefully (e.g., None, "N/A")
                table_data.append([label, str(temp_k)])
        else:
            # Handle if a key in the label map is missing from the data
            table_data.append([label, "N/A"])
            
    if not table_data:
        print(f"Error in {title}: No data to display. Check temp_labels_map.")
        return

    # Define the headers for the table
    headers = ["Property", "Temperature (°C)"]
    
    # --- Print Table ---
    print(f"\n--- {title} ---")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


def print_state_point_table(states_dict, state_labels, title="Thermodynamic State Points"):
    """
    Prints a general, formatted table for a set of state points.
    
    This function assumes input is in SI units (K, Pa, J/kg, J/kg.K)
    and converts them to (Celsius, bar, kJ/kg, kJ/kg.K) for printing.
    
    It can handle dictionaries with keys like 'H_r', 'T_r', etc., 
    'H_is', 'T_is', etc., or simple 'H', 'T', etc.
    
    Args:
        states_dict (dict): A dictionary containing the state lists in SI units.
        state_labels (list): A list of strings for the row labels.
        title (str, optional): The title for the printed table.
    """
    
    H_si, T_si, P_si, S_si, X = None, None, None, None, None
    
    # --- Auto-detect the key format ---
    # This logic checks for the most common key formats and uses the first one it finds.
    
    # 1. Check for 'Real' keys (e.g., H_r, T_r)
    if "H_r" in states_dict:
        try:
            H_si, T_si, P_si, S_si = states_dict["H_r"], states_dict["T_r"], states_dict["P_r"], states_dict["S_r"]
            X = states_dict.get("X_r") # Optional quality
        except KeyError as e:
            print(f"Error in {title}: Dictionary has 'H_r' but is missing other '_r' keys: {e}")
            return
            
    # 2. Check for 'Isentropic' keys (e.g., H_is, T_is)
    elif "H_is" in states_dict:
        try:
            H_si, T_si, P_si, S_si = states_dict["H_is"], states_dict["T_is"], states_dict["P_is"], states_dict["S_is"]
            X = states_dict.get("X_is") # Optional quality
        except KeyError as e:
            print(f"Error in {title}: Dictionary has 'H_is' but is missing other '_is' keys: {e}")
            return
            
    # 3. Check for 'General' keys (e.g., H, T)
    elif "H" in states_dict:
        try:
            H_si, T_si, P_si, S_si = states_dict["H"], states_dict["T"], states_dict["P"], states_dict["S"]
            X = states_dict.get("X") # Optional quality
        except KeyError as e:
            print(f"Error in {title}: Dictionary has 'H' but is missing other base keys: {e}")
            return
    else:
        print(f"Error in {title}: Could not find recognizable keys (e.g., 'H_r', 'H_is', or 'H') in states_dict.")
        return

    # --- Data Validation ---
    num_states = len(state_labels)
    if not (len(H_si) == num_states and len(T_si) == num_states and len(P_si) == num_states and len(S_si) == num_states):
        print(f"Error in {title}: Number of state labels ({num_states}) does not match data length.")
        print(f"  List lengths: H={len(H_si)}, T={len(T_si)}, P={len(P_si)}, S={len(S_si)}")
        print(f"  Labels provided: {state_labels}")
        return
    
    # --- Unit Conversion ---
    # T (K) -> T (°C)
    T_display = [temp_k - 273.15 for temp_k in T_si]
    # P (Pa) -> P (bar)
    P_display = [press_pa / 100000.0 for press_pa in P_si]
    # H (J/kg) -> H (kJ/kg)
    H_display = [enthalpy_j / 1000.0 for enthalpy_j in H_si]
    # S (J/kg.K) -> S (kJ/kg.K)
    S_display = [entropy_j / 1000.0 for entropy_j in S_si]

    # --- Build Table ---
    headers = [
        "State Point", 
        "Temp (°C)", 
        "Pressure (bar)", 
        "Enthalpy (kJ/kg)", 
        "Entropy (kJ/kg.K)"
    ]
    
    # Add Quality column only if X exists and has the correct length
    add_quality_column = (X is not None and len(X) == num_states)
    if add_quality_column:
        headers.append("Quality (X)")
        
    table_data = []
    for i in range(num_states):
        row = [
            state_labels[i],
            f"{T_display[i]:.2f}",  # Formatting to 2 decimal places
            f"{P_display[i]:.2f}",
            f"{H_display[i]:.2f}",
            f"{S_display[i]:.4f}"  # Entropy often needs more precision
        ]
        
        if add_quality_column:
            quality_val = X[i]
            # Handle non-numeric quality (e.g., None, 'N/A')
            if isinstance(quality_val, (int, float)):
                row.append(f"{quality_val:.3f}")
            else:
                row.append(str(quality_val))
                
        table_data.append(row)

    # --- Print Table ---
    print(f"\n--- {title} ---")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
