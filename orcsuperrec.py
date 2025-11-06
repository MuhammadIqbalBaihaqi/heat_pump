import CoolProp.CoolProp as CP 
import numpy as np

"""
State list indexing for ORC Superheated Recuperated:
0 - Outlet of LH
1 - Outlet of EVA
1sup - Outlet of SUP
2 - Outlet of EXP
23rec - Outlet of REC to desuperheater (if any) or direct to condenser
23rec3 - Outlet of desuperheater (if any)
3 - Outlet of CDS
4 - Outlet of PMP
41rec - Outlet of REC to LH
"""

def orcsuperrec(fluid, hs_fluid, cs_fluid, T_hs_in, T_cs_in, T_pinch_hs_in, T_pinch_hs_mid1, T_estimation_hs, T_estimation_cs, T_pinch_cs_mid1, eta_exp, eta_pmp, T_pinch_rec, p_hs_in, p_cs_in):
    """Simulates a superheated and recuperated Organic Rankine Cycle (ORC).

    This function models an ORC, determining key thermodynamic states and performance metrics. It's designed for cycle analysis and optimization, considering component efficiencies and heat exchanger pinch points.

    Args:
        fluid (str): The working fluid's name (e.g., "R245fa").
        hs_fluid (str): The heat source fluid's name (e.g., "Water").
        cs_fluid (str): The cold source fluid's name (e.g., "Water").
        T_hs_in (float): Inlet temperature of the heat source [K].
        T_cs_in (float): Inlet temperature of the cold source [K].
        T_pinch_hs_in (float): Pinch point temperature difference in the evaporator [K].
        T_pinch_hs_mid1 (float): Pinch point temp difference in the liquid heater [K].
        T_estimation_hs (float): Estimated outlet temperature of the heat source [K].
        T_estimation_cs (float): Estimated outlet temperature of the cold source [K].
        T_pinch_cs_mid1 (float): Pinch point temp difference in the condenser [K].
        eta_exp (float): Isentropic efficiency of the expander/turbine (0 to 1).
        eta_pmp (float): Isentropic efficiency of the pump (0 to 1).
        T_pinch_rec (float): Pinch point temperature difference in the recuperator [K].
        p_hs_in (float): Inlet pressure of the heat source [Pa].
        p_cs_in (float): Inlet pressure of the cold source [Pa].

    Returns:
        tuple: A tuple containing:
            - dict: Ideal cycle state properties (enthalpy, temperature, pressure, entropy, quality).
            - dict: Real cycle state properties (enthalpy, temperature, pressure, entropy).
            - dict: Heat source temperature profile.
            - dict: Cold source temperature profile.
            - dict: Enthalpy profiles for heat source and cold source.

    """

    T_hs_mid1 = T_hs_in - T_estimation_hs
    T_high = T_hs_in - T_pinch_hs_in
    T_cs_mid1 = T_estimation_cs + T_cs_in
    T_low = T_cs_mid1 + T_pinch_cs_mid1

    # Ideal Case
    # State 0  - Outlet of LH
    X0 = 0
    T0 = T_hs_mid1 - T_pinch_hs_mid1
    P0 = CP.PropsSI('P','T',T0,'Q',X0,fluid)
    H0 = CP.PropsSI('H','T',T0,'Q',X0,fluid)
    S0 = CP.PropsSI('S','T',T0,'Q',X0,fluid)

    # State 1 - Outlet of EVA
    T1 = T0
    X1 = 1
    P1 = CP.PropsSI('P','T',T1,'Q',X1,fluid)
    H1 = CP.PropsSI('H','T',T1,'Q',X1,fluid)
    S1 = CP.PropsSI('S','T',T1,'Q',X1,fluid)

    # State 1sup - Outlet of SUP
    T1_sup = T_high
    P1_sup = P1
    H1_sup = CP.PropsSI('H', 'T', T1_sup, 'P', P1_sup, fluid)
    S1_sup = CP.PropsSI('S', 'T', T1_sup, 'P', P1_sup, fluid)
    X1_sup = CP.PhaseSI('T', T1_sup, 'P', P1_sup, fluid)

    # State 3 - Outlet of CDS
    T3 = T_low
    X3 = 0
    P3 = CP.PropsSI('P','T',T3,'Q',X3,fluid)
    H3 = CP.PropsSI('H','T',T3,'Q',X3,fluid)
    S3 = CP.PropsSI('S','T',T3,'Q',X3,fluid)

    # State 2 - Outlet of EXP
    S2 = S1_sup
    P2 = P3
    H2 = CP.PropsSI('H', 'P', P2, 'S', S2, fluid)
    T2 = CP.PropsSI('T', 'P', P2, 'S', S2, fluid)
    X2 = CP.PhaseSI('P', P2, 'S', S2, fluid)

    #State 4 - Outlet of PMP
    P4 = P0
    S4 = S3
    H4 = CP.PropsSI('H', 'P', P4, 'S', S4, fluid)
    T4 = CP.PropsSI('T', 'P', P4, 'S', S4, fluid)
    X4 = CP.PhaseSI('P', P4, 'S', S4, fluid)
    
    # State 23rec - Outlet of REC
    P23rec = P2
    T23rec = T4 + T_pinch_rec
    H23rec = CP.PropsSI('H', 'T', T23rec, 'P', P23rec, fluid)
    S23rec = CP.PropsSI('S', 'T', T23rec, 'P', P23rec, fluid)
    X23rec = CP.PropsSI('Q', 'T', T23rec, 'P', P23rec, fluid)

    # State 23rec3 Initialization
    X23rec3, T23rec3, P23rec3, H23rec3, S23rec3 = None, None, None, None, None
    if 0 < X23rec < 1:
        print("Warning: State 23rec is in the two-phase region. Adjust T_pinch_rec or other parameters.")
        pass
    T_sat = CP.PropsSI('T', 'P', P23rec, 'Q', 0, fluid)
    if T23rec > T_sat:
        X23rec3 = 1
        T23rec3 = T_low
        P23rec3 = CP.PropsSI('P', 'T', T23rec3, 'Q', X23rec3, fluid)
        H23rec3 = CP.PropsSI('H', 'T', T23rec3, 'Q', X23rec3, fluid)
        S23rec3 = CP.PropsSI('S', 'T', T23rec3, 'Q', X23rec3, fluid)
        print("Adding New Component: Desuperheater after REC")
    # State 41rec - Outlet of REC
    P41rec = P0
    H41rec = (H2 + H4) - H23rec
    S41rec = CP.PropsSI('S', 'P', P41rec, 'H', H41rec, fluid)
    T41rec = CP.PropsSI('T', 'P', P41rec, 'H', H41rec, fluid)
    X41rec = CP.PhaseSI('P', P41rec, 'H', H41rec, fluid)


    # Real Case
    # State 0 Real - Outlet of LH
    X0_r = 0 
    T0_r = T_hs_mid1 - T_pinch_hs_mid1 - 1 # Real case slighltly lower 
    P0_r = CP.PropsSI('P','T',T0_r,'Q',X0_r,fluid)
    H0_r = CP.PropsSI('H','T',T0_r,'Q',X0_r,fluid)
    S0_r = CP.PropsSI('S','T',T0_r,'Q',X0_r,fluid)

    # State 1 Real - Outlet of EVA
    T1_r = T0_r - 1
    X1_r = 1
    P1_r = CP.PropsSI('P','T',T1_r,'Q',X1_r,fluid)
    H1_r = CP.PropsSI('H','T',T1_r,'Q',X1_r,fluid)
    S1_r = CP.PropsSI('S','T',T1_r,'Q',X1_r,fluid)

    # State 3 Real - Outlet of CDS
    T3_r = T_low - 2
    X3_r = 0
    P3_r = CP.PropsSI('P','T',T3_r,'Q',X3_r,fluid)
    H3_r = CP.PropsSI('H','T',T3_r,'Q',X3_r,fluid)  
    S3_r = CP.PropsSI('S','T',T3_r,'Q',X3_r,fluid)

    # State 1sup Real - Outlet of SUP
    T1_sup_r = T_high - 1
    P1_sup_r = P1_r
    H1_sup_r = CP.PropsSI('H', 'T', T1_sup_r, 'P', P1_sup_r, fluid)
    S1_sup_r = CP.PropsSI('S', 'T', T1_sup_r, 'P', P1_sup_r, fluid)
    X1_sup_r = CP.PhaseSI('T', T1_sup_r, 'P', P1_sup_r, fluid)

    # State 2 Real - Outlet of EXP
    S2is_r = S1_sup_r
    P2_r = P3_r
    H2is_r = CP.PropsSI('H', 'P', P2_r, 'S', S2is_r, fluid)
    H2_r = H1_sup_r - eta_exp * (H1_sup_r - H2is_r)
    T2_r = CP.PropsSI('T', 'P', P2_r, 'H', H2_r, fluid)
    S2_r = CP.PropsSI('S', 'P', P2_r, 'H', H2_r, fluid)

    # State 4 Real - Outlet of PMP
    P4_r = P0_r
    S4s_r = S3_r
    H4s_r = CP.PropsSI('H', 'P', P4_r, 'S', S4s_r, fluid)
    H4_r = H3_r + (1/eta_pmp) * (H4s_r - H3_r)
    T4_r = CP.PropsSI('T', 'P', P4_r, 'H', H4_r, fluid)
    S4_r = CP.PropsSI('S', 'P', P4_r, 'H', H4_r, fluid)

    # State 23rec Real - Outlet of REC
    P23rec_r = P2_r
    T23rec_r = T4_r + T_pinch_rec
    H23rec_r = CP.PropsSI('H', 'T', T23rec_r, 'P', P23rec_r, fluid)
    S23rec_r = CP.PropsSI('S', 'T', T23rec_r, 'P', P23rec_r, fluid)
    X23rec_r = CP.PropsSI('Q', 'T', T23rec_r, 'P', P23rec_r, fluid)
    # State 23rec3 Real Initialization
    X23rec3_r, T23rec3_r, P23rec3_r, H23rec3_r, S23rec3_r = None, None, None, None, None
    if 0 < X23rec_r < 1:
        print("Warning: State 23rec_r is in the two-phase region. Adjust T_pinch_rec or other parameters.")
        pass
    T_sat_r = CP.PropsSI('T', 'P', P23rec_r, 'Q', 0, fluid)
    if T23rec_r > T_sat_r:
        X23rec3_r = 1
        T23rec3_r = T_low - 1
        P23rec3_r = CP.PropsSI('P', 'T', T23rec3_r, 'Q', X23rec3_r, fluid)
        H23rec3_r = CP.PropsSI('H', 'T', T23rec3_r, 'Q', X23rec3_r, fluid)
        S23rec3_r = CP.PropsSI('S', 'T', T23rec3_r, 'Q', X23rec3_r, fluid)
        print("Adding New Component: Desuperheater after REC")
    
    # State 41rec Real - Outlet of REC
    P41rec_r = P0_r
    H41rec_r = (H2_r + H4_r) - H23rec_r
    S41rec_r = CP.PropsSI('S', 'P', P41rec_r, 'H', H41rec_r, fluid)
    T41rec_r = CP.PropsSI('T', 'P', P41rec_r, 'H', H41rec_r, fluid)

    # Calculating T_hs_mid2
    p_hs_mid2 = 0.99 * p_hs_in # Assume 1% pressure drop in heat source
    h_hs_in = CP.PropsSI('H', 'T', T_hs_in, 'P', p_hs_in, hs_fluid)
    # Energy Balance in Superheater
    h_hs_mid2 = (h_hs_in + H1_r) - H1_sup_r
    T_hs_mid2 = CP.PropsSI('T', 'P', p_hs_mid2, 'H', h_hs_mid2, hs_fluid)
    # Calculating T_hs_out
    p_hs_out = 0.97 * p_hs_mid2 # Assume 3% pressure drop in heat source
    p_hs_mid1 = 0.98 * p_hs_out # Assume 2% pressure drop in heat source
    h_hs_mid1 = CP.PropsSI('H', 'P', p_hs_mid1, 'T', T_hs_mid1, hs_fluid)
    # Energy Balance in Liquid Heater
    h_hs_out = (H41rec_r + h_hs_mid1) - H0_r
    T_hs_out = CP.PropsSI('T', 'P', p_hs_out, 'H', h_hs_out, hs_fluid)
    # Calculating T_cs_out
    p_cs_out = 0.98 * p_cs_in # Assume 2% pressure drop in cold source
    h_cs_in = CP.PropsSI('H', 'T', T_cs_in, 'P', p_cs_in, cs_fluid)
    # Energy Balance in Desuperheater and Condenser
    h_cs_out = (h_cs_in + H23rec_r) - H3_r
    T_cs_out = CP.PropsSI('T', 'P', p_cs_out, 'H', h_cs_out, cs_fluid)
    # Preparing H_cs_mid1
    p_cs_mid1 = 0.99 * p_cs_out # Assume 1% pressure drop in cold source
    h_cs_mid1 = CP.PropsSI('H', 'P', p_cs_mid1, 'T', T_cs_mid1, cs_fluid)


    H_is = [H0, H1, H1_sup, H2, H23rec, H23rec3, H3, H4, H41rec]
    T_is = [T0, T1, T1_sup, T2, T23rec, T23rec3, T3, T4, T41rec]
    P_is = [P0, P1, P1_sup, P2, P23rec, P23rec3, P3, P4, P41rec]
    S_is = [S0, S1, S1_sup, S2, S23rec, S23rec3, S3, S4, S41rec]
    X_is = [X0, X1, X1_sup, X2, X23rec, X23rec3, X3, X4, X41rec]

    H_r = [H0_r, H1_r, H1_sup_r, H2_r, H23rec_r, H23rec3_r, H3_r, H4_r, H41rec_r]
    T_r = [T0_r, T1_r, T1_sup_r, T2_r, T23rec_r, T23rec3_r, T3_r, T4_r, T41rec_r]
    P_r = [P0_r, P1_r, P1_sup_r, P2_r, P23rec_r, P23rec3_r, P3_r, P4_r, P41rec_r]
    S_r = [S0_r, S1_r, S1_sup_r, S2_r, S23rec_r, S23rec3_r, S3_r, S4_r, S41rec_r]

    H_hs = [h_hs_in, h_hs_mid2, h_hs_mid1, h_hs_out]
    H_cs = [h_cs_in, h_cs_mid1, h_cs_out]
    return {"H_is": H_is, "T_is": T_is, "P_is": P_is, "S_is": S_is, "X_is": X_is}, {"H_r": H_r, "T_r": T_r, "P_r": P_r, "S_r": S_r}, {
        "T_hs_in": T_hs_in,
        "T_hs_mid2": T_hs_mid2,
        "T_hs_mid1": T_hs_mid1,
        "T_hs_out": T_hs_out}, {
        "T_cs_in": T_cs_in,
        "T_cs_mid1": T_cs_mid1,
        "T_cs_out": T_cs_out,
    }, {"H_hs": H_hs, "H_cs": H_cs}

def mass_flow_calc(wf_mass_flow, H_list, H_hs_list, H_cs_list):
    """
    Calculate mass flow rate of the working fluid based on net power output.
    Args:
        wf_mass_flow (float): Mass flow rate of the working fluid [kg/s].
        H_list (list): List of enthalpy values at key states in the cycle [kJ/kg].
        H_hs_list (list): List of enthalpy values for the heat source [kJ/kg].
        H_cs_list (list): List of enthalpy values for the cold source [kJ/kg].
    Returns:
        
    """
    hs_mass_flow = (wf_mass_flow * (H_list[2] - H_list[-1])) / (H_hs_list[0] - H_hs_list[-1])
    cs_mass_flow = wf_mass_flow * (H_list[4] - H_list[6]) / (H_cs_list[0] - H_cs_list[-1])
    return hs_mass_flow, cs_mass_flow

def calc_thermal_efficiency(H_list, wf_mass_flow, T0, T_hs_in):
    """
    Calculate the thermal efficiency of the ORC Superheat Recuperated cycle.
    Args:
        H_list (list): List of enthalpy values at key states in the cycle [kJ/kg].
        wf_mass_flow (float): Mass flow rate of the working fluid [kg/s].
        T0 (float): Ambient temperature for exergy calculations [K].
        T_hs_in (float): Inlet temperature of the heat source [K].
    Returns:
        eta_thermal (float): Thermal efficiency of the cycle.
        eta_exergy (float): Exergy efficiency of the cycle.
        W_dot_net (float): Net work output of the cycle [kW].
        Q_dot_in (float): Heat input to the cycle [kW].
    """
    # First Law Efficiency Calculation
    W_dot_net = (H_list[2] - H_list[3]) - (H_list[7] - H_list[6]) # (EXP work) - (PMP work)
    Q_dot_in = H_list[2] - H_list[8] # Difference between SUP out and LH in
    eta_thermal = W_dot_net / Q_dot_in

    # Second Law Efficiency Calculation (Exergy Efficiency)
    eta_carnot = 1 - (T0 / T_hs_in)
    eta_exergy = eta_thermal / eta_carnot
    return eta_thermal, eta_exergy, W_dot_net * wf_mass_flow, Q_dot_in * wf_mass_flow

