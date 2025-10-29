import CoolProp.CoolProp as CP
from typing import List, Dict
from tabulate import tabulate
import copy

"""
notes: hp_cycle method is soon to be deprecated, use hp_cycle_revised instead

State List Indexing for Refrigeration/ORC Cycle:

The thermodynamic cycle states are indexed as follows:
    - State 1 (index = 0): Inlet to compressor / Outlet of evaporator
    - State 2 (index = 1): Outlet of compressor / Inlet to desuperheater
    - State 23 (index = 2): Outlet of desuperheater / Inlet to condenser
    - State 3 (index = 3): Outlet of condenser / Inlet to throttle valve
    - State 4 (index = 4): Outlet of throttle valve / Inlet to evaporator

This mapping ensures consistent reference to fluid states across 
component models and cycle calculations.
"""

#ts diagramnya dikelarin
def hp_cycle(fluid, T_sf_in, T_wh_in, T_pinch_sf_in, T_pinch_wh_in, eta_cpr=0.85 ):
    # ideal case
    # inlet compressor AND outlet evaporator
    X1 = 1 # assumed saturated vapor 
    T1 = T_wh_in + T_pinch_wh_in
    P1 = CP.PropsSI('P', 'T', T1, 'Q', X1, fluid)
    S1 = CP.PropsSI('S', 'T', T1, 'Q', X1, fluid)
    H1 = CP.PropsSI('H', 'T', T1, 'Q', X1, fluid)
    PH_1 = CP.PhaseSI('P', P1, 'Q', X1, fluid)
    # outlet condenser AND inlet throttle valve
    X3 = 0 # assumed saturated liquid
    T3 = T_sf_in - T_pinch_sf_in
    P3 = CP.PropsSI('P', 'T', T3, 'Q', X3, fluid)
    S3 = CP.PropsSI('S', 'T', T3, 'Q', X3, fluid)
    H3 = CP.PropsSI('H', 'T', T3, 'Q', X3, fluid)
    PH_3 = CP.PhaseSI('P', P3, 'Q', X3, fluid)

    # outlet compressor AND inlet condenser (jadikan S,T sebagai guidance)
    S2 = S1 # isentropic compression = 1 (ideal case)
    P2 = P3 # condenser pressure = outlet compressor pressure
    T2 = CP.PropsSI('T', 'P', P2, 'S', S2, fluid)
    H2 = CP.PropsSI('H', 'P', P2, 'S', S2, fluid)
    H2_g = CP.PropsSI('H', 'P', P2, 'Q', 1, fluid) # enthalpy if saturated vapor
    H2_f = CP.PropsSI('H', 'P', P2, 'Q', 0, fluid)  # enthalpy if saturated liquid
    # default values biar aman
    H23, T23, S23, P23, PH_23, X23 = [None] * 6  
    if H2 > H2_g: #entering desuperheater
        X23 = 1 
        P23 = P3
        T23 = CP.PropsSI('T', 'P', P23, 'Q', X23, fluid)
        S23 = CP.PropsSI('S', 'P', P23, 'Q', X23, fluid)
        H23 = CP.PropsSI('H', 'P', P23, 'Q', X23, fluid)
        PH_23 = CP.PhaseSI('P', P23, 'Q', X23, fluid)
    elif H2 < H2_f: # entering condenser as subcooled liquid
        print("Warning: Subcooled liquid at condenser inlet. Adjust cycle parameters.")
    else: # entering condenser as saturated mixture
        X2 = (H2 - H2_f) / (H2_g - H2_f)

    PH_2 = CP.PhaseSI('P', P2, 'S', S2, fluid)



    # inlet evaporator AND outlet throttle valve (coba nanti compare guidancenya S,T)
    S4 = S3 # isentropic expansion = 1 (ideal case)
    T4 = T1
    H4 = CP.PropsSI('H', 'S', S4, 'T', T4, fluid) # isenthalpic expansion, derived from energy balance in throttle valve
    #T4 = CP.PropsSI('T', 'S', S4, 'H', H4, fluid)
    #S4 = CP.PropsSI('S', 'S', S4, 'H', H4, fluid)
    P4 = CP.PropsSI('P', 'S', S4, 'T', T4, fluid)
    #H4 = CP.PropsSI('H', 'P', P4, 'S', S4, fluid)
    H4_g = CP.PropsSI('H', 'T', T4, 'Q', 1, fluid) # enthalpy if saturated vapor
    H4_f = CP.PropsSI('H', 'T', T4, 'Q', 0, fluid)  # enthalpy if saturated liquid
    if H4 < H4_f or H4 > H4_g:
        pass
    else:
        X4 = (H4 - H4_f) / (H4_g - H4_f)

    PH_4 = CP.PhaseSI('P', P4, 'S', S4, fluid)


    # real case
    X1_r = 1 # assumed saturated vapor
    T1_r = T1 - 1
    P1_r = CP.PropsSI('P', 'T', T1_r, 'Q', X1_r, fluid)
    S1_r = CP.PropsSI('S', 'T', T1_r, 'Q', X1_r, fluid)
    H1_r = CP.PropsSI('H', 'T', T1_r, 'Q', X1_r, fluid)
    PH_1_r = CP.PhaseSI('P', P1_r, 'Q', X1_r, fluid)
    # outlet condenser
    X3_r = 0 # assumed saturated liquid
    T3_r = T3 - 1
    P3_r = CP.PropsSI('P', 'T', T3_r, 'Q', X3_r, fluid)
    S3_r = CP.PropsSI('S', 'T', T3_r, 'Q', X3_r, fluid)
    H3_r = CP.PropsSI('H', 'T', T3_r, 'Q', X3_r, fluid)
    PH_3_r = CP.PhaseSI('P', P3_r, 'Q', X3_r, fluid)

    #outlet compressor
    P2_r = P3_r
    S2s_r = S1_r # isentropic compression
    H2s_r = CP.PropsSI('H', 'P', P2_r, 'S', S2s_r, fluid)
    H2_r = H1_r + (H2s_r - H1_r) / eta_cpr
    #S2_r = S1_r + (S2s_r - S1_r) / eta_cpr
    S2_r = CP.PropsSI('S', 'P', P2_r, 'H', H2_r, fluid)
    T2_r = CP.PropsSI('T', 'P', P2_r, 'H', H2_r, fluid)
    #H2_r = CP.PropsSI('H', 'P', P2_r, 'S', S2_r, fluid)
    H2_g_r = CP.PropsSI('H', 'P', P2_r, 'Q', 1, fluid) # enthalpy if saturated vapor
    H2_f_r = CP.PropsSI('H', 'P', P2_r, 'Q', 0, fluid)  # enthalpy if saturated liquid
    # default values biar aman
    H23_r, T23_r, S23_r, P23_r, PH_23_r, X23_r = [None] * 6
    if H2_r > H2_g_r: #entering desuperheater
        X23_r = 1 
        P23_r = P3_r
        T23_r = CP.PropsSI('T', 'P', P23_r, 'Q', X23_r, fluid)
        S23_r = CP.PropsSI('S', 'P', P23_r, 'Q', X23_r, fluid)
        H23_r = CP.PropsSI('H', 'P', P23_r, 'Q', X23_r, fluid)
        PH_23_r = CP.PhaseSI('P', P23_r, 'Q', X23_r, fluid)
    elif H2_r < H2_f_r: # entering condenser as subcooled liquid
        print("Warning: Subcooled liquid at condenser inlet. Adjust cycle parameters.")
    else: # entering condenser as saturated mixture
        X2_r = (H2_r - H2_f_r) / (H2_g_r - H2_f_r)
    PH_2_r = CP.PhaseSI('P', P2_r, 'H', H2_r, fluid)

    #outlet throttle valve
    P4_r = 1.01 * P1_r #guidance nya T aja ini T1_r + 1 = T4_r
    H4_r = H3_r
    T4_r = CP.PropsSI('T', 'P', P4_r, 'H', H4_r, fluid)
    #S4_r = CP.PropsSI('S', 'T', T4_r, 'H', H4_r, fluid)
    #P4_r = CP.PropsSI('P', 'T', T4_r, 'H', H4_r, fluid)
    S4_r = CP.PropsSI('S', 'P', P4_r, 'H', H4_r, fluid)
    #S4_r = CP.PropsSI('S', 'P', P4_r, 'H', H4_r, fluid)
    #T4_r = CP.PropsSI('T', 'P', P4_r, 'H', H4_r, fluid)
    H4_g_r = CP.PropsSI('H', 'P', P4_r, 'Q', 1, fluid) # enthalpy if saturated vapor
    H4_f_r = CP.PropsSI('H', 'P', P4_r, 'Q', 0, fluid)  # enthalpy if saturated liquid
    if H4_r < H4_f_r:
        print("Warning: Out of saturation region at evaporator inlet. Adjust cycle parameters.")
    else:
        X4_r = (H4_r - H4_f_r) / (H4_g_r - H4_f_r)
    PH_4_r = CP.PhaseSI('T', T4_r, 'S', S4_r, fluid)

    # Packing all ideal states (index: 1, 2, 23, 3, 4)
    H_list_is = [H1, H2, H23 if H23 is not None else None, H3, H4]
    S_list_is = [S1, S2, S23 if S23 is not None else None, S3, S4]
    T_list_is = [T1, T2, T23 if T23 is not None else None, T3, T4]
    P_list_is = [P1, P2, P23 if P23 is not None else None, P3, P4]
    X_list_is = [X1, X2 if 'X2' in locals() else None, X23 if 'X23' in locals() else None, X3, X4]
    PH_list_is = [PH_1, PH_2, PH_23 if PH_23 is not None else None, PH_3, PH_4]

    # Packing all real states (index: 1, 2, 23, 3, 4)
    H_list_r = [H1_r, H2_r, H23_r if 'H23_r' in locals() else None, H3_r, H4_r]
    S_list_r = [S1_r, S2_r, S23_r if 'S23_r' in locals() else None, S3_r, S4_r]
    T_list_r = [T1_r, T2_r, T23_r if 'T23_r' in locals() else None, T3_r, T4_r]
    P_list_r = [P1_r, P2_r, P23_r if 'P23_r' in locals() else None, P3_r, P4_r]
    X_list_r = [X1_r, X2_r if 'X2_r' in locals() else None, X23_r if 'X23_r' in locals() else None, X3_r, X4_r if 'X4_r' in locals() else None]
    PH_list_r = [PH_1_r, PH_2_r, PH_23_r if 'PH_23_r' in locals() else None, PH_3_r, PH_4_r]


    return {
        "H_is": H_list_is,
        "S_is": S_list_is,
        "T_is": T_list_is,
        "P_is": P_list_is,
        "X_is": X_list_is,
        "PH_is": PH_list_is} , {
        "H_r": H_list_r,
        "S_r": S_list_r,
        "T_r": T_list_r,
        "P_r": P_list_r,
        "X_r": X_list_r,
        "PH_r": PH_list_r
    }

def print_thermo_table(data_dict, states=None, table_format="simple"):
    """
    Mencetak tabel termodinamika, melakukan konversi, formatting, 
    dan menangani nilai None secara otomatis.
    """
    # 1. Definisikan header yang lebih deskriptif
    headers = [
        "State",
        "P_is\n[bar]\nIsentropic", "P_r\n[bar]\nReal",
        "T_is\n[°C]\nIsentropic", "T_r\n[°C]\nReal",
        "S_is\n[kJ/kg·K]\nIsentropic", "S_r\n[kJ/kg·K]\nReal",
        "H_is\n[kJ/kg]\nIsentropic", "H_r\n[kJ/kg]\nReal",
        "PH_is\n[-]\nIsentropic", "PH_r\n[-]\nReal",
        "X_is\n[-]\nIsentropic", "X_r\n[-]\nReal",
    ]

    # Helper function untuk memproses setiap nilai: cek None, kalkulasi, dan format
    def process_value(value, prop_type):
        # Jika nilai adalah None, kembalikan string "-"
        if value is None:
            return "-"
        
        # Lakukan kalkulasi dan formatting berdasarkan tipe properti
        try:
            match prop_type:
                case 'P': return f"{value / 1e5:.2f}"
                case 'T': return f"{value - 273.15:.2f}"
                case 'S': return f"{value / 1000:.4f}"
                case 'H': return f"{value / 1000:.2f}"
                case 'X': return f"{value:.4f}"
                case _: return str(value) # Untuk Phase ('PH') atau lainnya
        except TypeError:
            # Menangani jika ada tipe data yang salah (misal: string di H)
            return "Invalid Data"

    try:
        num_rows = len(next(iter(data_dict.values())))

        if states is None:
            states = [str(i + 1) for i in range(num_rows)]
        
        if len(states) != num_rows:
            print("Error: Jumlah state tidak cocok dengan jumlah data.")
            return

        table_data = []
        for i in range(num_rows):
            # Setiap nilai sekarang diproses oleh helper function 'process_value'
            row = [
                states[i],
                process_value(data_dict["P_is"][i], 'P'), process_value(data_dict["P_r"][i], 'P'),
                process_value(data_dict["T_is"][i], 'T'), process_value(data_dict["T_r"][i], 'T'),
                process_value(data_dict["S_is"][i], 'S'), process_value(data_dict["S_r"][i], 'S'),
                process_value(data_dict["H_is"][i], 'H'), process_value(data_dict["H_r"][i], 'H'),
                process_value(data_dict.get("PH_is", [None]*num_rows)[i], 'PH'), process_value(data_dict.get("PH_r", [None]*num_rows)[i], 'PH'),
                process_value(data_dict["X_is"][i], 'X'), process_value(data_dict["X_r"][i], 'X'),
            ]
            table_data.append(row)

        print(tabulate(table_data, headers=headers, tablefmt=table_format))

    except (StopIteration, KeyError, IndexError, TypeError) as e:
        print(f"Error: Data input tidak valid atau tidak lengkap. ({e})")

def thermo_analysis(
    wf_mass_flow: float,
    H_list: List[float],
    S_list: List[float],
    T0: float,
    T_cond: float,
    T_desuperheater: float,
    T_evaporator: float) -> Dict[str, float]:
    """
    Perform thermodynamic analysis of the heat pump cycle.

    Parameters
    ----------
    wf_mass_flow : float
        Mass flow rate of the working fluid [kg/s].
    H_list : list of float
        Enthalpy values at states 1, 2, 23, 3, 4 [J/kg].
    S_list : list of float
        Entropy values at states 1, 2, 23, 3, 4 [J/kg-K].
    T0 : float
        Ambient (dead state) temperature [K].
    T_cond : float
        Condenser temperature [K].
    T_desuperheater : float
        Desuperheater temperature [K].
    T_evaporator : float
        Evaporator temperature [K].

    Returns
    -------
    dict
        Dictionary containing heat/work terms [W], performance indices,
        and exergy destruction values [W].
    """
    if len(H_list) != 5 or len(S_list) != 5:
        raise ValueError("H_list and S_list must each contain 5 elements (states 1, 2, 23, 3, 4).")

    H1, H2, H23, H3, H4 = H_list
    S1, S2, S23, S3, S4 = S_list

    # --- Energy balances ---
    W_cpr = wf_mass_flow * (H2 - H1)                       # Compressor work
    Q_desuperheater = wf_mass_flow * (H2 - H23)            # Heat rejected in desuperheater
    Q_condenser = wf_mass_flow * (H23 - H3)                # Heat rejected in condenser
    Q_evaporator = wf_mass_flow * (H1 - H4)                # Heat absorbed in evaporator

    # --- Performance metrics ---
    COP = (Q_condenser + Q_desuperheater) / W_cpr if W_cpr else float("inf")
    COP_II = COP * (1 - (T0 / T_cond))

    # --- Exergy destruction terms ---
    ex_dest_cpr = wf_mass_flow * ((H1 - H2) - T0 * (S1 - S2)) + W_cpr
    ex_dest_desuperheater = wf_mass_flow * ((H2 - H23) - T0 * (S2 - S23)) \
                            - Q_desuperheater * (1 - (T0 / T_desuperheater))
    ex_dest_condenser = wf_mass_flow * ((H23 - H3) - T0 * (S23 - S3)) \
                        - Q_condenser * (1 - (T0 / T_cond))
    ex_dest_throttle = wf_mass_flow * ((H3 - H4) - T0 * (S3 - S4))
    ex_dest_evaporator = wf_mass_flow * ((H4 - H1) - T0 * (S4 - S1)) \
                         + Q_evaporator * (1 - (T0 / T_evaporator))

    results = {
        "W_cpr [W]": W_cpr,
        "Q_desuperheater [W]": Q_desuperheater,
        "Q_condenser [W]": Q_condenser,
        "Q_evaporator [W]": Q_evaporator,
        "COP I [-]": COP,
        "COP II [-]": COP_II,
        "Ex_dest_cpr [W]": ex_dest_cpr,
        "Ex_dest_desuperheater [W]": ex_dest_desuperheater,
        "Ex_dest_condenser [W]": ex_dest_condenser,
        "Ex_dest_throttle [W]": ex_dest_throttle,
        "Ex_dest_evaporator [W]": ex_dest_evaporator,
    }

    # --- Print table ---
    table = [[key, f"{val:.4f}"] for key, val in results.items()]
    print(tabulate(table, headers=["Parameter", "Value"], tablefmt="github"))

    return results

def COP_calculation(W_cpr, wf_mass_flow, H_list_r, superheat=False):
    """
    Calculate the Coefficient of Performance (COP) for real case.

    Parameters
    ----------
    W_cpr : float
        Compressor work input [W].
    wf_mass_flow :
        Mass flow rate of the working fluid in real case [kg/s].
    H_list_r : list of float
        Enthalpy values at states 1, 2, 23, 3, 4 for real case [J/kg].

    Returns
    -------
    dict
        Dictionary containing COP values for real case.
    """
    if superheat: #superheat case
        COP_r = (wf_mass_flow * (H_list_r[2] - H_list_r[4])) / W_cpr
    else:  # saturated case
        COP_r = (wf_mass_flow * (H_list_r[1] - H_list_r[3])) / W_cpr

    return COP_r 

def hapus_jika_kunci_pertama_none(dataset: dict) -> dict:
    """
    Mengecek nilai pada indeks ke-2 dari list PERTAMA dalam dictionary.

    Jika nilai tersebut adalah None, maka akan menghapus elemen pada 
    indeks ke-2 dari SEMUA list di dalam dataset.

    Args:
        dataset: Dictionary yang berisi list-list data (_r atau _is).

    Returns:
        Dictionary yang sudah dibersihkan atau dictionary asli.
    """
    # 1. Best practice: Buat salinan agar data asli tidak termodifikasi
    if not dataset:
        print("--> Dataset kosong, tidak ada yang diubah.")
        return {}
    
    data_bersih = copy.deepcopy(dataset)

    try:
        # 2. Ambil list pertama dari dictionary, apapun kuncinya
        list_pertama = list(data_bersih.values())[0]

        # 3. Cek kondisi pemicu:
        #    - Apakah listnya cukup panjang?
        #    - Apakah elemen di indeks ke-2 adalah None?
        if len(list_pertama) > 2 and list_pertama[2] is None:
            print(f"--> Terdeteksi 'None' di indeks ke-2 pada list pertama. Menghapus...")
            
            # 4. Jika pemicu terpenuhi, hapus elemen di indeks 2 dari semua list
            for key in data_bersih:
                # Pastikan setiap list juga cukup panjang sebelum dihapus
                if len(data_bersih[key]) > 2:
                    data_bersih[key].pop(2)
            
            return data_bersih
        else:
            print("--> Kondisi pemicu tidak terpenuhi. Dataset tidak diubah.")
            return data_bersih

    except (KeyError, IndexError):
        # Kalau ada error (misal: dictionary kosong atau list terlalu pendek)
        print("--> Dataset tidak memenuhi kriteria untuk dicek. Tidak diubah.")
        return data_bersih

def mass_flow_calculation(wh_mass_flow, cpr_pwr, T_wh_in, T_sf_dict_is, T_sf_dict_real, h_list_is,h_list_r, p_wh, p_sf = 101325,hs_fluid='Water'):
    """
    Calculate mass flow rates and outlet temperatures for the heat pump cycle.
    
    Parameters
    ----------
    wh_mass_flow : float
        Mass flow rate of the water heating side [kg/s].
    cpr_pwr : float
        Desired compressor power input [kW].
    T_wh_in : float
        Inlet temperature of the water heating side [K].
    T_sf_dict_is : dict
        Dictionary containing inlet and outlet temperatures for the secondary fluid in the isentropic case.
    T_sf_dict_real : dict
        Dictionary containing inlet and outlet temperatures for the secondary fluid in the real case.
    h_list : list of float
        Enthalpy values at states 1, 2, 23, 3, 4 [J/kg].
    p_wh : float
        Pressure of the water heating side [Pa].
    p_sf : float, optional
        Pressure of the secondary fluid side [Pa]. Default is 101325 Pa (1 atm).
    hs_fluid : str, optional
        Working fluid for the heat sink/cold source. Default is 'Water'.
    
    Returns
    -------
    tuple
        Tuple containing:
        - Mass flow rate of the working fluid [kg/s].
        - Outlet temperature of the water heating side [K].
        - Dictionary with mass flow rates for secondary fluid in isentropic and real cases [kg/s].
        - Dictionary with enthalpy values at various points in the heat sink/cold source [J/kg].
    Notes
    -----
    - Ensure that the keys in T_sf_dict_is and T_sf_dict_real match those used in the function.
    - The function assumes that the enthalpy values are in J/kg and mass flow rates are in kg/s.
    - The output temperatures are in Kelvin (K).
    """
    # finding HP cycle mass flow rate based on compressor power
    wf_mass_flow_is = cpr_pwr * 1000 / (h_list_is[1] - h_list_is[0])
    wf_mass_flow_r = cpr_pwr * 1000 / (h_list_r[1] - h_list_r[0])
    h_wh_in = CP.PropsSI('H', 'T', T_wh_in, 'P', p_wh, hs_fluid)
    h_wh_out_is = h_wh_in - (wh_mass_flow / wf_mass_flow_is) * (h_list_is[0] - h_list_is[3])
    h_wh_out_r = h_wh_in - (wh_mass_flow / wf_mass_flow_r) * (h_list_r[0] - h_list_r[3])
    T_wh_out_is = CP.PropsSI('T', 'H', h_wh_out_is, 'P', p_wh, hs_fluid)
    T_wh_out_r = CP.PropsSI('T', 'H', h_wh_out_r, 'P', p_wh, hs_fluid)
    h_sf_in_is = CP.PropsSI('H', 'T', T_sf_dict_is['T_sf_in_is'], 'P', p_sf, hs_fluid)
    h_sf_out_is = CP.PropsSI('H', 'T', T_sf_dict_is['T_sf_out_is'], 'P', p_sf, hs_fluid)
    h_sf_in_r = CP.PropsSI('H', 'T', T_sf_dict_real['T_sf_in_r'], 'P', p_sf, hs_fluid)
    h_sf_out_r = CP.PropsSI('H', 'T', T_sf_dict_real['T_sf_out_r'], 'P', p_sf, hs_fluid)
    sf_mass_flow_is = wf_mass_flow_is * (h_list_is[1] - h_list_is[3]) / (h_sf_out_is - h_sf_in_is)
    sf_mass_flow_r = wf_mass_flow_r * (h_list_r[1] - h_list_r[3]) / (h_sf_out_r - h_sf_in_r)

    return {"wf_mass_flow_is":wf_mass_flow_is,"wf_mass_flow_r": wf_mass_flow_r}, {"T_wh_out_is":T_wh_out_is, "T_wh_out_r":T_wh_out_r}, {"sf_mass_flow_is": sf_mass_flow_is, "sf_mass_flow_r": sf_mass_flow_r}, {"h_wh_in": h_wh_in, "h_wh_out_is": h_wh_out_is,"h_wh_out_r":h_wh_out_r, "h_sf_in_is": h_sf_in_is, "h_sf_out_is": h_sf_out_is, "h_sf_in_r": h_sf_in_r, "h_sf_out_r": h_sf_out_r}



def mass_flow_calculation_revised(
    wh_mass_flow,
    cpr_pwr, 
    T_wh_in, 
    T_sf_dict, 
    h_list, 
    p_wh, 
    p_sf=101325, 
    hs_fluid='Water'
):
    """
    Calculate mass flow rates and outlet temperatures for the real heat pump cycle.
    
    Parameters
    ----------
    wh_mass_flow : float
        Mass flow rate of the water heating side [kg/s].
    cpr_pwr : float
        Compressor power input [kW].
    T_wh_in : float
        Inlet temperature of the water heating side [K].
    T_sf_dict : dict
        Dictionary with secondary fluid inlet and outlet temperatures {'T_sf_in', 'T_sf_out'} [K].
    h_list : list of float
        Real enthalpy values at states 1, 2, 3, 4 [J/kg].
    p_wh : float
        Pressure of the water heating side [Pa].
    p_sf : float, optional
        Pressure of the secondary fluid side [Pa]. Default is 101325 Pa.
    hs_fluid : str, optional
        Fluid for the heat sink/source. Default is 'Water'.
    
    Returns
    -------
    dict
        A dictionary containing the calculated results:
        - 'wf_mass_flow': Mass flow of the working fluid [kg/s].
        - 'T_wh_out': Outlet temperature of the water heating side [K].
        - 'sf_mass_flow': Mass flow of the secondary fluid [kg/s].
        - 'h_wh_in': Inlet enthalpy of the water heating side [J/kg].
        - 'h_wh_out': Outlet enthalpy of the water heating side [J/kg].
        - 'h_sf_in': Inlet enthalpy of the secondary fluid [J/kg].
        - 'h_sf_out': Outlet enthalpy of the secondary fluid [J/kg].
    """
    # Calculate working fluid mass flow based on compressor power
    wf_mass_flow = cpr_pwr * 1000 / (h_list[1] - h_list[0])
    
    # Calculate enthalpies and outlet temperature for the water heating side
    h_wh_in = CP.PropsSI('H', 'T', T_wh_in, 'P', p_wh, hs_fluid)
    h_wh_out = h_wh_in - (wf_mass_flow / wh_mass_flow) * (h_list[0] - h_list[-1])
    T_wh_out = CP.PropsSI('T', 'H', h_wh_out, 'P', p_wh, hs_fluid)
    
    # Calculate enthalpies for the secondary fluid side
    h_sf_in = CP.PropsSI('H', 'T', T_sf_dict['T_sf_in_r'], 'P', p_sf, hs_fluid)
    h_sf_out = CP.PropsSI('H', 'T', T_sf_dict['T_sf_out_r'], 'P', p_sf, hs_fluid)
    
    # Calculate secondary fluid mass flow rate
    sf_mass_flow = wf_mass_flow * (h_list[1] - h_list[3]) / (h_sf_out - h_sf_in)

    results = {
        'wf_mass_flow': wf_mass_flow,
        'T_wh_out': T_wh_out,
        'sf_mass_flow': sf_mass_flow,
        'h_wh_in': h_wh_in,
        'h_wh_out': h_wh_out,
        'h_sf_in': h_sf_in,
        'h_sf_out': h_sf_out
    }
    
    return results

def power_to_tes(hs_cs_dict, sf_mass_flow_dict):
    """
    Calculate heat transfer rates to the TES based on mass flow rates and enthalpy changes.
    Parameters
    ----------
    hs_cs_dict : dict
        Dictionary containing enthalpy values at various points in the heat sink/cold source.
    sf_mass_flow_dict : dict
        Dictionary containing mass flow rates for the secondary fluid in both isentropic and real cases.
    Returns
    -------
    tuple
        Tuple containing heat transfer rates (q_dot_is, q_dot_r) in KiloWatts for isentropic and real cases.
    Notes
    -----
    - Ensure that the keys in the input dictionaries match those used in the function.
    - The function assumes that the enthalpy values are in J/kg and mass flow rates are in kg/s.
    - The output heat transfer rates are in KiloWatts (kW).
    """
    q_dot_is = sf_mass_flow_dict['sf_mass_flow_is'] * (hs_cs_dict['h_sf_out_is'] - hs_cs_dict['h_sf_in_is'])
    q_dot_r = sf_mass_flow_dict['sf_mass_flow_r'] * (hs_cs_dict['h_sf_out_r'] - hs_cs_dict['h_sf_in_r'])
    return q_dot_is/1000, q_dot_r/1000  # Convert to kW

def hp_cycle_revised(fluid, T_sf_out, T_wh_in, T_pinch_sf_out, T_pinch_wh_in, T_pinch_sf_in, eta_cpr=0.85 ):
    # ideal case
    # inlet compressor AND outlet evaporator
    X1 = 1 # assumed saturated vapor 
    T1 = T_wh_in + T_pinch_wh_in
    P1 = CP.PropsSI('P', 'T', T1, 'Q', X1, fluid)
    S1 = CP.PropsSI('S', 'T', T1, 'Q', X1, fluid)
    H1 = CP.PropsSI('H', 'T', T1, 'Q', X1, fluid)
    PH_1 = CP.PhaseSI('P', P1, 'Q', X1, fluid)

    # outlet compressor AND inlet condenser (jadikan S,T sebagai guidance)
    S2 = S1 # isentropic compression = 1 (ideal case)
    T2 = T_sf_out - T_pinch_sf_out
    P2 = CP.PropsSI('P', 'T', T2, 'S', S2, fluid)
    H2 = CP.PropsSI('H', 'T', T2, 'S', S2, fluid)
    H2_g = CP.PropsSI('H', 'T', T2, 'Q', 1, fluid) # enthalpy if saturated vapor
    H2_f = CP.PropsSI('H', 'T', T2, 'Q', 0, fluid)  # enthalpy if saturated liquid
    # outlet condenser AND inlet throttle valve
    X3 = 0 # assumed saturated liquid
    P3 = P2
    T3 = CP.PropsSI('T', 'P', P3, 'Q', X3, fluid)
    S3 = CP.PropsSI('S', 'P', P3, 'Q', X3, fluid)
    H3 = CP.PropsSI('H', 'P', P3, 'Q', X3, fluid)
    PH_3 = CP.PhaseSI('P', P3, 'Q', X3, fluid)


    # default values biar aman
    H23, T23, S23, P23, PH_23, X23 = [None] * 6  
    if H2 > H2_g: #entering desuperheater
        X23 = 1 
        P23 = P3
        T23 = CP.PropsSI('T', 'P', P23, 'Q', X23, fluid)
        S23 = CP.PropsSI('S', 'P', P23, 'Q', X23, fluid)
        H23 = CP.PropsSI('H', 'P', P23, 'Q', X23, fluid)
        PH_23 = CP.PhaseSI('P', P23, 'Q', X23, fluid)
    elif H2 < H2_f: # entering condenser as subcooled liquid
        print("Warning: Subcooled liquid at condenser inlet. Adjust cycle parameters.")
    else: # entering condenser as saturated mixture
        X2 = (H2 - H2_f) / (H2_g - H2_f)

    PH_2 = CP.PhaseSI('P', P2, 'S', S2, fluid)



    # inlet evaporator AND outlet throttle valve (coba nanti compare guidancenya S,T)
    S4 = S3 # isentropic expansion = 1 (ideal case)
    T4 = T1
    H4 = CP.PropsSI('H', 'S', S4, 'T', T4, fluid) # isenthalpic expansion, derived from energy balance in throttle valve
    #T4 = CP.PropsSI('T', 'S', S4, 'H', H4, fluid)
    #S4 = CP.PropsSI('S', 'S', S4, 'H', H4, fluid)
    P4 = CP.PropsSI('P', 'S', S4, 'T', T4, fluid)
    #H4 = CP.PropsSI('H', 'P', P4, 'S', S4, fluid)
    H4_g = CP.PropsSI('H', 'T', T4, 'Q', 1, fluid) # enthalpy if saturated vapor
    H4_f = CP.PropsSI('H', 'T', T4, 'Q', 0, fluid)  # enthalpy if saturated liquid
    if H4 < H4_f or H4 > H4_g:
        pass
    else:
        X4 = (H4 - H4_f) / (H4_g - H4_f)

    PH_4 = CP.PhaseSI('P', P4, 'S', S4, fluid)


    # real case
    X1_r = 1 # assumed saturated vapor
    T1_r = T1 - 1
    P1_r = CP.PropsSI('P', 'T', T1_r, 'Q', X1_r, fluid)
    S1_r = CP.PropsSI('S', 'T', T1_r, 'Q', X1_r, fluid)
    H1_r = CP.PropsSI('H', 'T', T1_r, 'Q', X1_r, fluid)
    PH_1_r = CP.PhaseSI('P', P1_r, 'Q', X1_r, fluid)
    # outlet condenser
    X3_r = 0 # assumed saturated liquid
    T3_r = T3 - 1
    P3_r = CP.PropsSI('P', 'T', T3_r, 'Q', X3_r, fluid)
    S3_r = CP.PropsSI('S', 'T', T3_r, 'Q', X3_r, fluid)
    H3_r = CP.PropsSI('H', 'T', T3_r, 'Q', X3_r, fluid)
    PH_3_r = CP.PhaseSI('P', P3_r, 'Q', X3_r, fluid)

    #outlet compressor
    P2_r = P3_r
    S2s_r = S1_r # isentropic compression
    H2s_r = CP.PropsSI('H', 'P', P2_r, 'S', S2s_r, fluid)
    H2_r = H1_r + (H2s_r - H1_r) / eta_cpr
    #S2_r = S1_r + (S2s_r - S1_r) / eta_cpr
    S2_r = CP.PropsSI('S', 'P', P2_r, 'H', H2_r, fluid)
    T2_r = CP.PropsSI('T', 'P', P2_r, 'H', H2_r, fluid)
    #H2_r = CP.PropsSI('H', 'P', P2_r, 'S', S2_r, fluid)
    H2_g_r = CP.PropsSI('H', 'P', P2_r, 'Q', 1, fluid) # enthalpy if saturated vapor
    H2_f_r = CP.PropsSI('H', 'P', P2_r, 'Q', 0, fluid)  # enthalpy if saturated liquid
    # default values biar aman
    H23_r, T23_r, S23_r, P23_r, PH_23_r, X23_r = [None] * 6
    if H2_r > H2_g_r: #entering desuperheater
        print("Entering desuperheater in real case")
        X23_r = 1 
        P23_r = P3_r
        T23_r = CP.PropsSI('T', 'P', P23_r, 'Q', X23_r, fluid)
        S23_r = CP.PropsSI('S', 'P', P23_r, 'Q', X23_r, fluid)
        H23_r = CP.PropsSI('H', 'P', P23_r, 'Q', X23_r, fluid)
        PH_23_r = CP.PhaseSI('P', P23_r, 'Q', X23_r, fluid)
    elif H2_r < H2_f_r: # entering condenser as subcooled liquid
        print("Warning: Subcooled liquid at condenser inlet. Adjust cycle parameters.")
    else: # entering condenser as saturated mixture
        print("Entering saturated mixture at condenser inlet in real case")
        X2_r = (H2_r - H2_f_r) / (H2_g_r - H2_f_r)
    PH_2_r = CP.PhaseSI('P', P2_r, 'H', H2_r, fluid)

    #outlet throttle valve
    P4_r = 1.01 * P1_r #guidance nya T aja ini T1_r + 1 = T4_r
    H4_r = H3_r
    T4_r = CP.PropsSI('T', 'P', P4_r, 'H', H4_r, fluid)
    #S4_r = CP.PropsSI('S', 'T', T4_r, 'H', H4_r, fluid)
    #P4_r = CP.PropsSI('P', 'T', T4_r, 'H', H4_r, fluid)
    S4_r = CP.PropsSI('S', 'P', P4_r, 'H', H4_r, fluid)
    #S4_r = CP.PropsSI('S', 'P', P4_r, 'H', H4_r, fluid)
    #T4_r = CP.PropsSI('T', 'P', P4_r, 'H', H4_r, fluid)
    H4_g_r = CP.PropsSI('H', 'P', P4_r, 'Q', 1, fluid) # enthalpy if saturated vapor
    H4_f_r = CP.PropsSI('H', 'P', P4_r, 'Q', 0, fluid)  # enthalpy if saturated liquid
    if H4_r < H4_f_r:
        print("Warning: Out of saturation region at evaporator inlet. Adjust cycle parameters.")
    else:
        X4_r = (H4_r - H4_f_r) / (H4_g_r - H4_f_r)
    PH_4_r = CP.PhaseSI('T', T4_r, 'S', S4_r, fluid)

    # Packing all ideal states (index: 1, 2, 23, 3, 4)
    H_list_is = [H1, H2, H23 if H23 is not None else None, H3, H4]
    S_list_is = [S1, S2, S23 if S23 is not None else None, S3, S4]
    T_list_is = [T1, T2, T23 if T23 is not None else None, T3, T4]
    P_list_is = [P1, P2, P23 if P23 is not None else None, P3, P4]
    X_list_is = [X1, X2 if 'X2' in locals() else None, X23 if 'X23' in locals() else None, X3, X4]
    PH_list_is = [PH_1, PH_2, PH_23 if PH_23 is not None else None, PH_3, PH_4]

    # Packing all real states (index: 1, 2, 23, 3, 4)
    H_list_r = [H1_r, H2_r, H23_r if 'H23_r' in locals() else None, H3_r, H4_r]
    S_list_r = [S1_r, S2_r, S23_r if 'S23_r' in locals() else None, S3_r, S4_r]
    T_list_r = [T1_r, T2_r, T23_r if 'T23_r' in locals() else None, T3_r, T4_r]
    P_list_r = [P1_r, P2_r, P23_r if 'P23_r' in locals() else None, P3_r, P4_r]
    X_list_r = [X1_r, X2_r if 'X2_r' in locals() else None, X23_r if 'X23_r' in locals() else None, X3_r, X4_r if 'X4_r' in locals() else None]
    PH_list_r = [PH_1_r, PH_2_r, PH_23_r if 'PH_23_r' in locals() else None, PH_3_r, PH_4_r]

    # Secondary Fluid Temperature
    T_sf_out_is = T2 + T_pinch_sf_out
    T_sf_out_r = T2_r + T_pinch_sf_out
    T_sf_in_is = T3 + T_pinch_sf_in
    T_sf_in_r = T3_r + T_pinch_sf_in
    return {
        "H_is": H_list_is,
        "S_is": S_list_is,
        "T_is": T_list_is,
        "P_is": P_list_is,
        "X_is": X_list_is,
        "PH_is": PH_list_is} , {
        "H_r": H_list_r,
        "S_r": S_list_r,
        "T_r": T_list_r,
        "P_r": P_list_r,
        "X_r": X_list_r,
        "PH_r": PH_list_r
    }, {
        "T_sf_out_is": T_sf_out_is,
        "T_sf_in_is": T_sf_in_is
    }, {
        "T_sf_out_r": T_sf_out_r,
        "T_sf_in_r": T_sf_in_r
    }




def hp_cycle_adapt(fluid, T_sf_out, T_wh_in, T_pinch_sf_out, T_pinch_wh_in, T_pinch_sf_in, delta_sup, eta_cpr=0.85):
    # ideal case
    # inlet compressor AND outlet evaporator
    X1 = 1 # assumed saturated vapor 
    T1 = T_wh_in + T_pinch_wh_in
    P1 = CP.PropsSI('P', 'T', T1, 'Q', X1, fluid)
    S1 = CP.PropsSI('S', 'T', T1, 'Q', X1, fluid)
    H1 = CP.PropsSI('H', 'T', T1, 'Q', X1, fluid)
    PH_1 = CP.PhaseSI('P', P1, 'Q', X1, fluid)

    # outlet compressor AND inlet condenser (jadikan S,T sebagai guidance)
    S2 = S1 # isentropic compression = 1 (ideal case)
    T2 = T_sf_out - T_pinch_sf_out
    P2 = CP.PropsSI('P', 'T', T2, 'S', S2, fluid)
    H2 = CP.PropsSI('H', 'T', T2, 'S', S2, fluid)
    H2_g = CP.PropsSI('H', 'T', T2, 'Q', 1, fluid) # enthalpy if saturated vapor
    H2_f = CP.PropsSI('H', 'T', T2, 'Q', 0, fluid)  # enthalpy if saturated liquid

    # --- TAMBAHKAN KODE DI BAWAH INI ---
    H1_sup, T1_sup, S1_sup, P1_sup, PH_1_sup, X1_sup = [None] * 6
    # Dapatkan temperatur saturasi (didih) pada tekanan P2
    T_sat_at_P2 = CP.PropsSI('T', 'P', P2, 'Q', 1, fluid)

    # Cek dan print status fasa di state 2
    if T2 > T_sat_at_P2:
        print(f"State 2 is SUPERHEATED. (T2: {T2:.2f} K > T_sat: {T_sat_at_P2:.2f} K)")
    elif abs(T2 - T_sat_at_P2) < 0.01: # Toleransi kecil untuk floating point
        print(f"State 2 is SATURATED. (T2: {T2:.2f} K ≈ T_sat: {T_sat_at_P2:.2f} K)")
        P1_sup = P1
        T1_sup = T1 + delta_sup
        H1_sup = CP.PropsSI('H', 'T', T1_sup, 'P', P1_sup, fluid)
        S1_sup = CP.PropsSI('S', 'T', T1_sup, 'P', P1_sup, fluid)
        S2 = S1_sup
        T2 = T_sf_out - T_pinch_sf_out
        P2 = CP.PropsSI('P', 'T', T2, 'S', S2, fluid)
        H2 = CP.PropsSI('H', 'T', T2, 'S', S2, fluid)
    else:
        print(f"State 2 is SUBCOOLED/COMPRESSED LIQUID. (T2: {T2:.2f} K < T_sat: {T_sat_at_P2:.2f} K)")
    # outlet condenser AND inlet throttle valve
    X3 = 0 # assumed saturated liquid
    P3 = P2
    T3 = CP.PropsSI('T', 'P', P3, 'Q', X3, fluid)
    S3 = CP.PropsSI('S', 'P', P3, 'Q', X3, fluid)
    H3 = CP.PropsSI('H', 'P', P3, 'Q', X3, fluid)
    PH_3 = CP.PhaseSI('P', P3, 'Q', X3, fluid)


    # default values biar aman
    H23, T23, S23, P23, PH_23, X23 = [None] * 6  
    if H2 > H2_g: #entering desuperheater
        X23 = 1 
        P23 = P3
        T23 = CP.PropsSI('T', 'P', P23, 'Q', X23, fluid)
        S23 = CP.PropsSI('S', 'P', P23, 'Q', X23, fluid)
        H23 = CP.PropsSI('H', 'P', P23, 'Q', X23, fluid)
        PH_23 = CP.PhaseSI('P', P23, 'Q', X23, fluid)
    elif H2 < H2_f: # entering condenser as subcooled liquid
        print("Warning: Subcooled liquid at condenser inlet. Adjust cycle parameters.")
    else: # entering condenser as saturated mixture
        X2 = (H2 - H2_f) / (H2_g - H2_f)

    PH_2 = CP.PhaseSI('P', P2, 'S', S2, fluid)



    # inlet evaporator AND outlet throttle valve (coba nanti compare guidancenya S,T)
    S4 = S3 # isentropic expansion = 1 (ideal case)
    T4 = T1
    H4 = CP.PropsSI('H', 'S', S4, 'T', T4, fluid) # isenthalpic expansion, derived from energy balance in throttle valve
    #T4 = CP.PropsSI('T', 'S', S4, 'H', H4, fluid)
    #S4 = CP.PropsSI('S', 'S', S4, 'H', H4, fluid)
    P4 = CP.PropsSI('P', 'S', S4, 'T', T4, fluid)
    #H4 = CP.PropsSI('H', 'P', P4, 'S', S4, fluid)
    H4_g = CP.PropsSI('H', 'T', T4, 'Q', 1, fluid) # enthalpy if saturated vapor
    H4_f = CP.PropsSI('H', 'T', T4, 'Q', 0, fluid)  # enthalpy if saturated liquid
    if H4 < H4_f or H4 > H4_g:
        pass
    else:
        X4 = (H4 - H4_f) / (H4_g - H4_f)

    PH_4 = CP.PhaseSI('P', P4, 'S', S4, fluid)


    # real case
    X1_r = 1 # assumed saturated vapor
    T1_r = T1 - 1
    P1_r = CP.PropsSI('P', 'T', T1_r, 'Q', X1_r, fluid)
    S1_r = CP.PropsSI('S', 'T', T1_r, 'Q', X1_r, fluid)
    H1_r = CP.PropsSI('H', 'T', T1_r, 'Q', X1_r, fluid)
    PH_1_r = CP.PhaseSI('P', P1_r, 'Q', X1_r, fluid)
    # outlet condenser
    X3_r = 0 # assumed saturated liquid
    T3_r = T3 - 1
    P3_r = CP.PropsSI('P', 'T', T3_r, 'Q', X3_r, fluid)
    S3_r = CP.PropsSI('S', 'T', T3_r, 'Q', X3_r, fluid)
    H3_r = CP.PropsSI('H', 'T', T3_r, 'Q', X3_r, fluid)
    PH_3_r = CP.PhaseSI('P', P3_r, 'Q', X3_r, fluid)

    #outlet compressor
    P2_r = P3_r
    S2s_r = S1_r # isentropic compression
    H2s_r = CP.PropsSI('H', 'P', P2_r, 'S', S2s_r, fluid)
    H2_r = H1_r + (H2s_r - H1_r) / eta_cpr
    #S2_r = S1_r + (S2s_r - S1_r) / eta_cpr
    S2_r = CP.PropsSI('S', 'P', P2_r, 'H', H2_r, fluid)
    T2_r = CP.PropsSI('T', 'P', P2_r, 'H', H2_r, fluid)
    #H2_r = CP.PropsSI('H', 'P', P2_r, 'S', S2_r, fluid)
    H2_g_r = CP.PropsSI('H', 'P', P2_r, 'Q', 1, fluid) # enthalpy if saturated vapor
    H2_f_r = CP.PropsSI('H', 'P', P2_r, 'Q', 0, fluid)  # enthalpy if saturated liquid

    # check if compressor outlet is superheated or not
    H1r_sup, T1r_sup, S1r_sup, P1r_sup, PH_1r_sup, X1r_sup = [None] * 6
    T_sat_at_P2r = CP.PropsSI('T', 'P', P2_r, 'Q', 1, fluid)

    if T2_r > T_sat_at_P2r:
        print(f"State 2_r is SUPERHEATED. (T2_r: {T2_r:.2f} K > T_sat: {T_sat_at_P2r:.2f} K)")
    elif abs(T2_r - T_sat_at_P2r) < 0.01: # Toleransi kecil untuk floating point
        print(f"State 2_r is SATURATED. (T2_r: {T2_r:.2f} K ≈ T_sat: {T_sat_at_P2r:.2f} K)")
        P1r_sup = P1_r
        T1r_sup = T1_r + delta_sup
        H1r_sup = CP.PropsSI('H', 'T', T1r_sup, 'P', P1r_sup, fluid)
        S1r_sup = CP.PropsSI('S', 'T', T1r_sup, 'P', P1r_sup, fluid)
        S2s_r = S1r_sup
        P2_r = P3_r
        H2s_r = CP.PropsSI('H', 'P', P2_r, 'S', S2s_r, fluid)
        H2_r = H1r_sup + (H2s_r - H1r_sup) / eta_cpr
        S2_r = CP.PropsSI('S', 'P', P2_r, 'H', H2_r, fluid)
        T2_r = CP.PropsSI('T', 'P', P2_r, 'H', H2_r, fluid)
    else:
        print(f"State 2_r is SUBCOOLED/COMPRESSED LIQUID. (T2_r: {T2_r:.2f} K < T_sat: {T_sat_at_P2r:.2f} K)")
    

    
    # default values biar aman
    H23_r, T23_r, S23_r, P23_r, PH_23_r, X23_r = [None] * 6
    if H2_r > H2_g_r: #entering desuperheater
        print("Entering desuperheater in real case")
        X23_r = 1 
        P23_r = P3_r
        T23_r = CP.PropsSI('T', 'P', P23_r, 'Q', X23_r, fluid)
        S23_r = CP.PropsSI('S', 'P', P23_r, 'Q', X23_r, fluid)
        H23_r = CP.PropsSI('H', 'P', P23_r, 'Q', X23_r, fluid)
        PH_23_r = CP.PhaseSI('P', P23_r, 'Q', X23_r, fluid)
        X2_r = None
    elif H2_r < H2_f_r: # entering condenser as subcooled liquid
        print("Warning: Subcooled liquid at condenser inlet. Adjust cycle parameters.")
    else: # entering condenser as saturated mixture
        print("Entering saturated mixture at condenser inlet in real case")
        X2_r = (H2_r - H2_f_r) / (H2_g_r - H2_f_r)
        print(f"X2_r: {X2_r:.4f}")
    PH_2_r = CP.PhaseSI('P', P2_r, 'H', H2_r, fluid)

    #outlet throttle valve
    P4_r = 1.01 * P1_r #guidance nya T aja ini T1_r + 1 = T4_r
    H4_r = H3_r
    T4_r = CP.PropsSI('T', 'P', P4_r, 'H', H4_r, fluid)
    #S4_r = CP.PropsSI('S', 'T', T4_r, 'H', H4_r, fluid)
    #P4_r = CP.PropsSI('P', 'T', T4_r, 'H', H4_r, fluid)
    S4_r = CP.PropsSI('S', 'P', P4_r, 'H', H4_r, fluid)
    #S4_r = CP.PropsSI('S', 'P', P4_r, 'H', H4_r, fluid)
    #T4_r = CP.PropsSI('T', 'P', P4_r, 'H', H4_r, fluid)
    H4_g_r = CP.PropsSI('H', 'P', P4_r, 'Q', 1, fluid) # enthalpy if saturated vapor
    H4_f_r = CP.PropsSI('H', 'P', P4_r, 'Q', 0, fluid)  # enthalpy if saturated liquid
    if H4_r < H4_f_r:
        print("Warning: Out of saturation region at evaporator inlet. Adjust cycle parameters.")
    else:
        X4_r = (H4_r - H4_f_r) / (H4_g_r - H4_f_r)
    PH_4_r = CP.PhaseSI('T', T4_r, 'S', S4_r, fluid)

    # Packing all ideal states (index: 1, 2, 23, 3, 4)
    H_list_is = [H1, H1_sup, H2, H23, H3, H4]
    S_list_is = [S1, S1_sup, S2, S23, S3, S4]
    T_list_is = [T1, T1_sup, T2, T23, T3, T4]
    P_list_is = [P1, P1_sup, P2, P23, P3, P4]
    X_list_is = [X1, X1_sup, X2 if 'X2' in locals() else None, X23 if 'X23' in locals() else None, X3, X4]
    PH_list_is = [PH_1,PH_1_sup, PH_2, PH_23, PH_3, PH_4]

    # Packing all real states (index: 1, 2, 23, 3, 4)
    H_list_r = [H1_r, H1r_sup, H2_r, H23_r, H3_r, H4_r]
    S_list_r = [S1_r, S1r_sup, S2_r, S23_r , S3_r, S4_r]
    T_list_r = [T1_r, T1r_sup, T2_r, T23_r, T3_r, T4_r]
    P_list_r = [P1_r, P1r_sup, P2_r, P23_r, P3_r, P4_r]
    X_list_r = [X1_r, X1r_sup, X2_r, X23_r , X3_r, X4_r if 'X4_r' in locals() else None]
    PH_list_r = [PH_1_r, PH_1r_sup, PH_2_r, PH_23_r , PH_3_r, PH_4_r]

    # Secondary Fluid Temperature
    T_sf_out_is = T2 + T_pinch_sf_out
    T_sf_out_r = T2_r + T_pinch_sf_out
    T_sf_in_is = T3 + T_pinch_sf_in
    T_sf_in_r = T3_r + T_pinch_sf_in
    return {
        "H_is": H_list_is,
        "S_is": S_list_is,
        "T_is": T_list_is,
        "P_is": P_list_is,
        "X_is": X_list_is,
        "PH_is": PH_list_is} , {
        "H_r": H_list_r,
        "S_r": S_list_r,
        "T_r": T_list_r,
        "P_r": P_list_r,
        "X_r": X_list_r,
        "PH_r": PH_list_r
    }, {
        "T_sf_out_is": T_sf_out_is,
        "T_sf_in_is": T_sf_in_is
    }, {
        "T_sf_out_r": T_sf_out_r,
        "T_sf_in_r": T_sf_in_r
    }


def hp_sup_rec(fluid, T_sf_out, T_wh_in, T_pinch_sf_out, T_pinch_wh_in, T_pinch_sf_in, delta_sup, T_pinch_rec, eta_cpr=0.85):
    # ideal case
    # inlet compressor AND outlet evaporator
    X1 = 1 # assumed saturated vapor 
    T1 = T_wh_in + T_pinch_wh_in
    P1 = CP.PropsSI('P', 'T', T1, 'Q', X1, fluid)
    S1 = CP.PropsSI('S', 'T', T1, 'Q', X1, fluid)
    H1 = CP.PropsSI('H', 'T', T1, 'Q', X1, fluid)
    PH_1 = CP.PhaseSI('P', P1, 'Q', X1, fluid)

    # outlet compressor AND inlet condenser (jadikan S,T sebagai guidance)
    S2 = S1 # isentropic compression = 1 (ideal case)
    T2 = T_sf_out - T_pinch_sf_out
    P2 = CP.PropsSI('P', 'T', T2, 'S', S2, fluid)
    H2 = CP.PropsSI('H', 'T', T2, 'S', S2, fluid)
    H2_g = CP.PropsSI('H', 'T', T2, 'Q', 1, fluid) # enthalpy if saturated vapor
    H2_f = CP.PropsSI('H', 'T', T2, 'Q', 0, fluid)  # enthalpy if saturated liquid

    # --- TAMBAHKAN KODE DI BAWAH INI ---
    H1_sup, T1_sup, S1_sup, P1_sup, PH_1_sup, X1_sup = [None] * 6
    # Dapatkan temperatur saturasi (didih) pada tekanan P2
    T_sat_at_P2 = CP.PropsSI('T', 'P', P2, 'Q', 1, fluid)

    # Cek dan print status fasa di state 2
    if T2 > T_sat_at_P2:
        print(f"State 2 is SUPERHEATED. (T2: {T2:.2f} K > T_sat: {T_sat_at_P2:.2f} K)")
    elif abs(T2 - T_sat_at_P2) < 0.01: # Toleransi kecil untuk floating point
        print(f"State 2 is SATURATED. (T2: {T2:.2f} K ≈ T_sat: {T_sat_at_P2:.2f} K)")
        P1_sup = P1
        T1_sup = T1 + delta_sup
        H1_sup = CP.PropsSI('H', 'T', T1_sup, 'P', P1_sup, fluid)
        S1_sup = CP.PropsSI('S', 'T', T1_sup, 'P', P1_sup, fluid)
        S2 = S1_sup
        T2 = T_sf_out - T_pinch_sf_out
        P2 = CP.PropsSI('P', 'T', T2, 'S', S2, fluid)
        H2 = CP.PropsSI('H', 'T', T2, 'S', S2, fluid)
    else:
        print(f"State 2 is SUBCOOLED/COMPRESSED LIQUID. (T2: {T2:.2f} K < T_sat: {T_sat_at_P2:.2f} K)")
    # outlet condenser AND inlet throttle valve
    X3 = 0 # assumed saturated liquid
    P3 = P2
    T3 = CP.PropsSI('T', 'P', P3, 'Q', X3, fluid)
    S3 = CP.PropsSI('S', 'P', P3, 'Q', X3, fluid)
    H3 = CP.PropsSI('H', 'P', P3, 'Q', X3, fluid)
    PH_3 = CP.PhaseSI('P', P3, 'Q', X3, fluid)


    # default values biar aman
    H23, T23, S23, P23, PH_23, X23 = [None] * 6  
    if H2 > H2_g: #entering desuperheater
        X23 = 1 
        P23 = P3
        T23 = CP.PropsSI('T', 'P', P23, 'Q', X23, fluid)
        S23 = CP.PropsSI('S', 'P', P23, 'Q', X23, fluid)
        H23 = CP.PropsSI('H', 'P', P23, 'Q', X23, fluid)
        PH_23 = CP.PhaseSI('P', P23, 'Q', X23, fluid)
    elif H2 < H2_f: # entering condenser as subcooled liquid
        print("Warning: Subcooled liquid at condenser inlet. Adjust cycle parameters.")
    else: # entering condenser as saturated mixture
        X2 = (H2 - H2_f) / (H2_g - H2_f)

    PH_2 = CP.PhaseSI('P', P2, 'S', S2, fluid)



    # inlet evaporator AND outlet throttle valve (coba nanti compare guidancenya S,T)
    S4 = S3 # isentropic expansion = 1 (ideal case)
    T4 = T1
    H4 = CP.PropsSI('H', 'S', S4, 'T', T4, fluid) # isenthalpic expansion, derived from energy balance in throttle valve
    #T4 = CP.PropsSI('T', 'S', S4, 'H', H4, fluid)
    #S4 = CP.PropsSI('S', 'S', S4, 'H', H4, fluid)
    P4 = CP.PropsSI('P', 'S', S4, 'T', T4, fluid)
    #H4 = CP.PropsSI('H', 'P', P4, 'S', S4, fluid)
    H4_g = CP.PropsSI('H', 'T', T4, 'Q', 1, fluid) # enthalpy if saturated vapor
    H4_f = CP.PropsSI('H', 'T', T4, 'Q', 0, fluid)  # enthalpy if saturated liquid
    if H4 < H4_f or H4 > H4_g:
        pass
    else:
        X4 = (H4 - H4_f) / (H4_g - H4_f)

    PH_4 = CP.PhaseSI('P', P4, 'S', S4, fluid)


    # real case
    X1_r = 1 # assumed saturated vapor
    T1_r = T1 - 1
    P1_r = CP.PropsSI('P', 'T', T1_r, 'Q', X1_r, fluid)
    S1_r = CP.PropsSI('S', 'T', T1_r, 'Q', X1_r, fluid)
    H1_r = CP.PropsSI('H', 'T', T1_r, 'Q', X1_r, fluid)
    PH_1_r = CP.PhaseSI('P', P1_r, 'Q', X1_r, fluid)
    # outlet condenser
    X3_r = 0 # assumed saturated liquid
    T3_r = T3 - 1
    P3_r = CP.PropsSI('P', 'T', T3_r, 'Q', X3_r, fluid)
    S3_r = CP.PropsSI('S', 'T', T3_r, 'Q', X3_r, fluid)
    H3_r = CP.PropsSI('H', 'T', T3_r, 'Q', X3_r, fluid)
    PH_3_r = CP.PhaseSI('P', P3_r, 'Q', X3_r, fluid)

    #outlet compressor
    P2_r = 1.02 * P3_r
    S2s_r = S1_r # isentropic compression
    H2s_r = CP.PropsSI('H', 'P', P2_r, 'S', S2s_r, fluid)
    H2_r = H1_r + (H2s_r - H1_r) / eta_cpr
    S2_r = CP.PropsSI('S', 'P', P2_r, 'H', H2_r, fluid)
    T2_r = CP.PropsSI('T', 'P', P2_r, 'H', H2_r, fluid)
    #H2_r = CP.PropsSI('H', 'P', P2_r, 'S', S2_r, fluid)
    H2_g_r = CP.PropsSI('H', 'P', P2_r, 'Q', 1, fluid) # enthalpy if saturated vapor
    H2_f_r = CP.PropsSI('H', 'P', P2_r, 'Q', 0, fluid)  # enthalpy if saturated liquid
    PH_2_r = CP.PhaseSI('P', P2_r, 'H', H2_r, fluid)
    X2_r = None
    # check if compressor outlet is superheated or not
    H1r_sup, T1r_sup, S1r_sup, P1r_sup, PH_1r_sup, X1r_sup = [None] * 6
    T_sat_at_P2r = CP.PropsSI('T', 'P', P2_r, 'Q', 1, fluid)

    if T2_r > T_sat_at_P2r and H2_r > H2_g_r:
        print(f"State 2_r is SUPERHEATED. (T2_r: {T2_r:.2f} K > T_sat: {T_sat_at_P2r:.2f} K)")
    elif H2_f_r < H2_r < H2_g_r: # Toleransi kecil untuk floating point
        print(f"State 2_r is SATURATED. (T2_r: {T2_r:.2f} K ≈ T_sat: {T_sat_at_P2r:.2f} K)")
        print(f"Needs superheater before compressor.")
        P1r_sup = P1_r
        T1r_sup = T1_r + delta_sup
        H1r_sup = CP.PropsSI('H', 'T', T1r_sup, 'P', P1r_sup, fluid)
        S1r_sup = CP.PropsSI('S', 'T', T1r_sup, 'P', P1r_sup, fluid)
        PH_1r_sup = CP.PhaseSI('P', P1r_sup, 'T', T1r_sup, fluid)
        S2s_r = S1r_sup
        P2_r = P3_r
        H2s_r = CP.PropsSI('H', 'P', P2_r, 'S', S2s_r, fluid)
        H2_r = H1r_sup + (H2s_r - H1r_sup) / eta_cpr
        S2_r = CP.PropsSI('S', 'P', P2_r, 'H', H2_r, fluid)
        T2_r = CP.PropsSI('T', 'P', P2_r, 'H', H2_r, fluid)
        PH_2_r = CP.PhaseSI('P', P2_r, 'H', H2_r, fluid)
    else:
        print(f"State 2_r is SUBCOOLED/COMPRESSED LIQUID. (T2_r: {T2_r:.2f} K < T_sat: {T_sat_at_P2r:.2f} K)")
    
    #outlet throttle valve
    P4_r = 1.02 * P1_r #guidance nya T aja ini T1_r + 1 = T4_r
    H4_r = H3_r
    T4_r = CP.PropsSI('T', 'P', P4_r, 'H', H4_r, fluid)
    S4_r = CP.PropsSI('S', 'P', P4_r, 'H', H4_r, fluid)
    H4_g_r = CP.PropsSI('H', 'P', P4_r, 'Q', 1, fluid) # enthalpy if saturated vapor
    H4_f_r = CP.PropsSI('H', 'P', P4_r, 'Q', 0, fluid)  # enthalpy if saturated liquid
    if H4_r < H4_f_r:
        print("Warning: Out of saturation region at evaporator inlet. Adjust cycle parameters.")
    elif H4_f_r < H4_r < H4_g_r:
        print("Entering saturated mixture at recuperator inlet in real case")
        X4_r = (H4_r - H4_f_r) / (H4_g_r - H4_f_r)
        print(f"X4_r: {X4_r:.4f}")
    PH_4_r = CP.PhaseSI('T', T4_r, 'S', S4_r, fluid)

    # state after recuperator to condenser inlet
    X23rec_r = 1
    P23rec_r = P2_r
    T23rec_r = CP.PropsSI('T', 'P', P23rec_r, 'Q', X23rec_r, fluid) 
    qua_rec = 0.5
    H23rec_r = CP.PropsSI('H', 'P', P23rec_r, 'Q', qua_rec, fluid)
    S23rec_r = CP.PropsSI('S', 'P', P23rec_r, 'Q', qua_rec, fluid)
    H23recf_r = CP.PropsSI('H', 'P', P23rec_r, 'Q', 0, fluid)  # enthalpy if saturated liquid
    H23grec_r = CP.PropsSI('H', 'P', P23rec_r, 'Q', 1, fluid)  # enthalpy if saturated vapor
    PH_23rec_r = CP.PhaseSI('T', T23rec_r, 'P', P23rec_r, fluid)
    # check if state after recuperator is still superheated or not
    H23_r, T23_r, S23_r, P23_r, PH_23_r, X23_r = [None] * 6
    T23rec_sat_at_P23rec = CP.PropsSI('T', 'P', P23rec_r, 'Q', 1, fluid)
    print(f"Saturation temperature at P23rec_r ({P23rec_r:.2f} Pa) is {T23rec_sat_at_P23rec:.2f} K")
    if T23rec_r > T23rec_sat_at_P23rec and H23rec_r > H23grec_r:
        print(f"State after recuperator is SUPERHEATED. (T23rec_r: {T23rec_r:.2f} K > T_sat: {T23rec_sat_at_P23rec:.2f} K)")
        print(f"Needs Desuperheater after recuperator.")
        X23_r = 1
        P23_r = 1.01 * P3_r
        T23_r = CP.PropsSI('T', 'P', P23_r, 'Q', X23_r, fluid)
        S23_r = CP.PropsSI('S', 'P', P23_r, 'Q', X23_r, fluid)
        H23_r = CP.PropsSI('H', 'P', P23_r, 'Q', X23_r, fluid)
        PH_23_r = CP.PhaseSI('P', P23_r, 'Q', X23_r, fluid)
    elif H23recf_r < H23rec_r < H23grec_r:
        print(f"State after recuperator is SATURATED MIXTURE. (H23rec_r between H_f and H_g)")
        print(f"Doesn't need Desuperheater after recuperator. Direct to condenser (State 3).")
        X23rec_r = (H23rec_r - H23recf_r) / (H23grec_r - H23recf_r)
    elif H23rec_r < H23recf_r:
        print("Warning: Subcooled liquid at condenser inlet after recuperator. Adjust cycle parameters.")
    # state after recuperator to evaporator inlet
    P41rec_r = P1_r
    H41rec_r = H2_r + H4_r - H23rec_r
    T41rec_r = CP.PropsSI('T', 'P', P41rec_r, 'H', H41rec_r, fluid)
    S41rec_r = CP.PropsSI('S', 'P', P41rec_r, 'H', H41rec_r, fluid)
    PH41rec_r = CP.PhaseSI('T', T41rec_r, 'P', P41rec_r, fluid)
    X41rec_r = CP.PropsSI('Q', 'P', P41rec_r, 'H', H41rec_r, fluid)

    # Packing all real states (index: 1, 2, 23, 3, 4)
    H_list_r = [H1_r, H1r_sup, H2_r, H23rec_r, H23_r, H3_r, H4_r, H41rec_r]
    S_list_r = [S1_r, S1r_sup, S2_r, S23rec_r, S23_r, S3_r, S4_r, S41rec_r]
    T_list_r = [T1_r, T1r_sup, T2_r, T23rec_r, T23_r, T3_r, T4_r, T41rec_r]
    P_list_r = [P1_r, P1r_sup, P2_r, P23rec_r, P23_r, P3_r, P4_r, P41rec_r]
    X_list_r = [X1_r, X1r_sup, X2_r, X23rec_r if 'X23rec_r' in locals() else None, X23_r, X3_r, X4_r if 'X4_r' in locals() else None, X41rec_r]
    PH_list_r = [PH_1_r, PH_1r_sup, PH_2_r, PH_23rec_r, PH_23_r, PH_3_r, PH_4_r, PH41rec_r]

    # Secondary Fluid Temperature
    T_sf_out_r = T2_r + T_pinch_sf_out
    T_sf_in_r = T3_r + T_pinch_sf_in
    return  {
        "H_r": H_list_r,
        "S_r": S_list_r,
        "T_r": T_list_r,
        "P_r": P_list_r,
        "X_r": X_list_r,
        "PH_r": PH_list_r
    }, {
        "T_sf_out_r": T_sf_out_r,
        "T_sf_in_r": T_sf_in_r
    }
