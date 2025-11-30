import CoolProp.CoolProp as CP
from tabulate import tabulate
import traceback  # Untuk melihat detail error jika crash
class HeatPumpRec:
    """
    Membungkus simulasi Heat Pump (dengan recuperator setelah kondenser)
    ke dalam sebuah class.
    
    Class ini menyimpan semua parameter input, menjalankan simulasi (siklus
    dan fluida eksternal), dan menyimpan semua state serta hasil performa
    sebagai atribut.
    
    Alur Penggunaan:
    1. Buat instance dari class ini dengan semua parameter input.
    2. Panggil method .run_simulation() untuk melakukan semua perhitungan.
    3. Akses hasil simulasi dari atribut (misal: self.real_states, 
       self.performance, self.external_fluid_results).
    """

    def __init__(self, wf_hp_fluid, T_sf_out, T_wh_in, T_pinch_sf_out, T_pinch_wh_in,
                 T_pinch_sf_in, delta_sup, w_cpr_kw, eta_cpr,
                 wh_mass_flow, p_wh, p_sf, wh_fluid, sf_fluid):
        
        # --- 1. Simpan Semua Parameter Input ---
        # Input dari 'hp_rec_after_cds'
        self.fluid = wf_hp_fluid
        self.T_sf_out = T_sf_out
        self.T_wh_in = T_wh_in
        self.T_pinch_sf_out = T_pinch_sf_out
        self.T_pinch_wh_in = T_pinch_wh_in
        self.T_pinch_sf_in = T_pinch_sf_in
        self.delta_sup = delta_sup
        self.w_cpr_kw = w_cpr_kw
        self.eta_cpr = eta_cpr
        
        # Input dari 'mass_flow_calculation_revised'
        self.wh_mass_flow = wh_mass_flow
        self.p_wh = p_wh
        self.p_sf = p_sf
        self.wh_fluid = wh_fluid
        self.sf_fluid = sf_fluid

        # --- 2. Siapkan Atribut untuk Menyimpan Hasil ---
        self.real_states = {}
        self.sf_temps = {}
        self.performance = {}
        self.external_fluid_results = {}

    def run_simulation(self):
            """
            Menjalankan perhitungan termodinamika siklus DAN
            perhitungan fluida eksternal (WH dan SF) dengan Error Handling.
            """


            print(f"--- Memulai Simulasi HP Rec untuk Fluida: {self.fluid} ---")

            try:
                # ==========================================================
                # BAGIAN 1: LOGIKA DARI 'hp_rec_after_cds'
                # ==========================================================
                
                # --- Ideal Case ---
                
                # inlet compressor AND outlet evaporator
                X1 = 1 
                T1 = self.T_wh_in + self.T_pinch_wh_in
                P1 = CP.PropsSI('P', 'T', T1, 'Q', X1, self.fluid)
                S1 = CP.PropsSI('S', 'T', T1, 'Q', X1, self.fluid)
                H1 = CP.PropsSI('H', 'T', T1, 'Q', X1, self.fluid)
                PH_1 = CP.PhaseSI('P', P1, 'Q', X1, self.fluid)

                # outlet compressor AND inlet condenser
                S2 = S1 
                T2 = self.T_sf_out - self.T_pinch_sf_out
                P2 = CP.PropsSI('P', 'T', T2, 'S', S2, self.fluid)
                H2 = CP.PropsSI('H', 'T', T2, 'S', S2, self.fluid)
                
                # Cek batas fasa (bisa error jika dekat titik kritis)
                H2_g = CP.PropsSI('H', 'T', T2, 'Q', 1, self.fluid) 
                H2_f = CP.PropsSI('H', 'T', T2, 'Q', 0, self.fluid) 

                H1_sup, T1_sup, S1_sup, P1_sup, PH_1_sup, X1_sup = [None] * 6
                T_sat_at_P2 = CP.PropsSI('T', 'P', P2, 'Q', 1, self.fluid)

                if T2 > T_sat_at_P2:
                    # State 2 is SUPERHEATED
                    pass
                elif abs(T2 - T_sat_at_P2) < 0.01: 
                    # State 2 is SATURATED
                    # print(f"State 2 is SATURATED. Adding Superheat.")
                    P1_sup = P1
                    T1_sup = T1 + self.delta_sup
                    H1_sup = CP.PropsSI('H', 'T', T1_sup, 'P', P1_sup, self.fluid)
                    S1_sup = CP.PropsSI('S', 'T', T1_sup, 'P', P1_sup, self.fluid)
                    S2 = S1_sup
                    T2 = self.T_sf_out - self.T_pinch_sf_out
                    P2 = CP.PropsSI('P', 'T', T2, 'S', S2, self.fluid)
                    H2 = CP.PropsSI('H', 'T', T2, 'S', S2, self.fluid)
                else:
                    print(f"Warning: State 2 is SUBCOOLED (T2: {T2:.2f} K < T_sat)")
                
                # outlet condenser AND inlet throttle valve
                X3 = 0 
                P3 = P2
                T3 = CP.PropsSI('T', 'P', P3, 'Q', X3, self.fluid)
                S3 = CP.PropsSI('S', 'P', P3, 'Q', X3, self.fluid)
                H3 = CP.PropsSI('H', 'P', P3, 'Q', X3, self.fluid)
                PH_3 = CP.PhaseSI('P', P3, 'Q', X3, self.fluid)

                H23, T23, S23, P23, PH_23, X23 = [None] * 6  
                if H2 > H2_g: # entering desuperheater
                    X23 = 1 
                    P23 = P3
                    T23 = CP.PropsSI('T', 'P', P23, 'Q', X23, self.fluid)
                    S23 = CP.PropsSI('S', 'P', P23, 'Q', X23, self.fluid)
                    H23 = CP.PropsSI('H', 'P', P23, 'Q', X23, self.fluid)
                    PH_23 = CP.PhaseSI('P', P23, 'Q', X23, self.fluid)
                elif H2 < H2_f: 
                    print("Warning: Subcooled liquid at condenser inlet. Adjust cycle parameters.")
                else: 
                    # Potential DivByZero if H2_g == H2_f (Critical Point)
                    denom = H2_g - H2_f
                    if denom == 0: raise ZeroDivisionError("Critical point reached at Condenser Inlet")
                    X2 = (H2 - H2_f) / denom

                PH_2 = CP.PhaseSI('P', P2, 'S', S2, self.fluid)

                # inlet evaporator AND outlet throttle valve
                S4 = S3 
                T4 = T1
                H4 = CP.PropsSI('H', 'S', S4, 'T', T4, self.fluid)
                P4 = CP.PropsSI('P', 'S', S4, 'T', T4, self.fluid)
                H4_g = CP.PropsSI('H', 'T', T4, 'Q', 1, self.fluid) 
                H4_f = CP.PropsSI('H', 'T', T4, 'Q', 0, self.fluid)  
                
                X4 = None # Inisialisasi default
                if H4 < H4_f or H4 > H4_g:
                    pass
                else:
                    denom_evap = H4_g - H4_f
                    if denom_evap == 0: raise ZeroDivisionError("Critical point reached at Evaporator Inlet")
                    X4 = (H4 - H4_f) / denom_evap
                PH_4 = CP.PhaseSI('P', P4, 'S', S4, self.fluid)


                # --- Real Case ---
                X1_r = 1 
                T1_r = T1 - 1
                P1_r = CP.PropsSI('P', 'T', T1_r, 'Q', X1_r, self.fluid)
                S1_r = CP.PropsSI('S', 'T', T1_r, 'Q', X1_r, self.fluid)
                H1_r = CP.PropsSI('H', 'T', T1_r, 'Q', X1_r, self.fluid)
                PH_1_r = CP.PhaseSI('P', P1_r, 'Q', X1_r, self.fluid)
                
                # outlet condenser
                X3_r = 0 
                T3_r = T3 - 1 # Menggunakan T3 ideal dari atas
                P3_r = CP.PropsSI('P', 'T', T3_r, 'Q', X3_r, self.fluid)
                S3_r = CP.PropsSI('S', 'T', T3_r, 'Q', X3_r, self.fluid)
                H3_r = CP.PropsSI('H', 'T', T3_r, 'Q', X3_r, self.fluid)
                PH_3_r = CP.PhaseSI('P', P3_r, 'Q', X3_r, self.fluid)
                
                # outlet desup
                X23_r = 1
                P23_r = 1.01 * P3_r
                T23_r = CP.PropsSI('T', 'P', P23_r, 'Q', X23_r, self.fluid)
                S23_r = CP.PropsSI('S', 'P', P23_r, 'Q', X23_r, self.fluid)
                H23_r = CP.PropsSI('H', 'P', P23_r, 'Q', X23_r, self.fluid)
                PH_23_r = CP.PhaseSI('P', P23_r, 'Q', X23_r, self.fluid)

                # outlet compressor
                P2_r = 1.02 * P3_r
                S2s_r = S1_r 
                H2s_r = CP.PropsSI('H', 'P', P2_r, 'S', S2s_r, self.fluid)
                H2_r = H1_r + (H2s_r - H1_r) / self.eta_cpr
                S2_r = CP.PropsSI('S', 'P', P2_r, 'H', H2_r, self.fluid)
                T2_r = CP.PropsSI('T', 'P', P2_r, 'H', H2_r, self.fluid)
                H2_g_r = CP.PropsSI('H', 'P', P2_r, 'Q', 1, self.fluid) 
                H2_f_r = CP.PropsSI('H', 'P', P2_r, 'Q', 0, self.fluid)  
                PH_2_r = CP.PhaseSI('P', P2_r, 'H', H2_r, self.fluid)
                X2_r = None
                
                # check if compressor outlet is superheated or not
                H1r_sup, T1r_sup, S1r_sup, P1r_sup, PH_1r_sup, X1r_sup = [None] * 6
                T_sat_at_P2r = CP.PropsSI('T', 'P', P2_r, 'Q', 1, self.fluid)

                if T2_r > T_sat_at_P2r and H2_r > H2_g_r:
                    pass
                elif H2_f_r < H2_r < H2_g_r: 
                    P1r_sup = P1_r
                    T1r_sup = T1_r + self.delta_sup
                    H1r_sup = CP.PropsSI('H', 'T', T1r_sup, 'P', P1r_sup, self.fluid)
                    S1r_sup = CP.PropsSI('S', 'T', T1r_sup, 'P', P1r_sup, self.fluid)
                    PH_1r_sup = CP.PhaseSI('P', P1r_sup, 'T', T1r_sup, self.fluid)
                    S2s_r = S1r_sup
                    P2_r = P3_r
                    H2s_r = CP.PropsSI('H', 'P', P2_r, 'S', S2s_r, self.fluid)
                    H2_r = H1r_sup + (H2s_r - H1r_sup) / self.eta_cpr
                    S2_r = CP.PropsSI('S', 'P', P2_r, 'H', H2_r, self.fluid)
                    T2_r = CP.PropsSI('T', 'P', P2_r, 'H', H2_r, self.fluid)
                    PH_2_r = CP.PhaseSI('P', P2_r, 'H', H2_r, self.fluid)
                else:
                    # Jika subcooled, biarkan lanjut (meski logic fisik mungkin aneh untuk kompresor)
                    pass 
                
                # outlet throttle valve
                P4_r = 1.01 * P1_r 
                H4_r = H3_r
                T4_r = CP.PropsSI('T', 'P', P4_r, 'H', H4_r, self.fluid)
                S4_r = CP.PropsSI('S', 'P', P4_r, 'H', H4_r, self.fluid)
                H4_g_r = CP.PropsSI('H', 'P', P4_r, 'Q', 1, self.fluid) 
                H4_f_r = CP.PropsSI('H', 'P', P4_r, 'Q', 0, self.fluid)  
                
                X4_r = None
                if H4_r < H4_f_r:
                    pass # Liquid region
                elif H4_f_r < H4_r < H4_g_r:
                    denom_evap_r = H4_g_r - H4_f_r
                    if denom_evap_r == 0: raise ZeroDivisionError("Critical point reached at Real Evaporator Inlet")
                    X4_r = (H4_r - H4_f_r) / denom_evap_r
                PH_4_r = CP.PhaseSI('T', T4_r, 'S', S4_r, self.fluid)

                # state 3_rec, inlet REC to TRV
                H3rec_r = H1r_sup + H3_r - H1_r if H1r_sup else H1_r + H3_r - H1_r # Handle if H1r_sup is None
                P3rec_r = 1.01 * P3_r
                T3rec_r = CP.PropsSI('T', 'P', P3rec_r, 'H', H3rec_r, self.fluid)
                S3rec_r = CP.PropsSI('S', 'P', P3rec_r, 'H', H3rec_r, self.fluid)
                X3rec_r = CP.PropsSI('Q', 'P', P3rec_r, 'H', H3rec_r, self.fluid)
                PH_3rec_r = CP.PhaseSI('H', H3rec_r, 'P', P3rec_r, self.fluid)
                
                # --- Simpan Hasil Siklus (Cycle) ---
                
                H_list_r = [H1_r, H1r_sup, H2_r, H23_r,  H3rec_r, H3_r,H4_r]
                S_list_r = [S1_r, S1r_sup, S2_r, S23_r,  S3rec_r, S3_r, S4_r]
                T_list_r = [T1_r, T1r_sup, T2_r, T23_r, T3rec_r, T3_r, T4_r]
                P_list_r = [P1_r, P1r_sup, P2_r, P23_r,  P3rec_r, P3_r, P4_r]
                X_list_r = [X1_r, X1r_sup, X2_r, X23_r,  X3rec_r, X3_r, X4_r]
                PH_list_r = [PH_1_r, PH_1r_sup, PH_2_r,  PH_23_r, PH_3rec_r, PH_3_r,  PH_4_r]

                self.real_states = {
                    "H_r": H_list_r, "S_r": S_list_r, "T_r": T_list_r,
                    "P_r": P_list_r, "X_r": X_list_r, "PH_r": PH_list_r
                }
                
                # Secondary Fluid Temperature
                T_sf_out_r = T2_r + self.T_pinch_sf_out
                T_sf_in_r = T3_r + self.T_pinch_sf_in
                
                self.sf_temps = {
                    "T_sf_out_r": T_sf_out_r,
                    "T_sf_in_r": T_sf_in_r
                }

                # mass flow rate calculation kg/s
                delta_h_comp = H_list_r[2] - H_list_r[1]
                if delta_h_comp == 0: raise ZeroDivisionError("Compressor Delta H is zero")
                
                wf_mass_flow = self.w_cpr_kw * 1000 / delta_h_comp

                # COP HP calculation
                Q_h = (H_list_r[2] - H_list_r[-3]) # Indexing H3rec_r logic check needed here based on list order
                Q_h_dot = Q_h * wf_mass_flow / 1000  # in kW
                W_in = self.w_cpr_kw # in kW
                
                if W_in == 0: COP_hp = 0 # Avoid div by zero if work is 0
                else: COP_hp = Q_h_dot / W_in
                
                Q_l_dot = Q_h_dot - self.w_cpr_kw # in kW
                
                self.performance = {
                    "wf_mass_flow": wf_mass_flow, "COP_hp": COP_hp, 
                    "Q_h_dot": Q_h_dot, "Q_l_dot": Q_l_dot
                }

                # ==========================================================
                # BAGIAN 2: LOGIKA DARI 'mass_flow_calculation_revised'
                # ==========================================================
                
                # Calculate enthalpies and outlet temperature for the water heating side
                h_wh_in = CP.PropsSI('H', 'T', self.T_wh_in, 'P', self.p_wh, self.wh_fluid)
                
                if self.wh_mass_flow == 0: raise ZeroDivisionError("Water Heating Mass Flow is Zero")
                h_wh_out = h_wh_in - (wf_mass_flow / self.wh_mass_flow) * (H_list_r[0] - H_list_r[-1])
                T_wh_out = CP.PropsSI('T', 'H', h_wh_out, 'P', self.p_wh, self.wh_fluid)
                
                # Calculate enthalpies for the secondary fluid side
                h_sf_in = CP.PropsSI('H', 'T', self.sf_temps["T_sf_in_r"], 'P', self.p_sf, self.sf_fluid)
                h_sf_out = CP.PropsSI('H', 'T', self.sf_temps["T_sf_out_r"], 'P', self.p_sf, self.sf_fluid)
                
                # Calculate secondary fluid mass flow rate
                delta_h_sf = h_sf_out - h_sf_in
                if delta_h_sf == 0: raise ZeroDivisionError("Secondary Fluid Delta H is Zero")
                
                sf_mass_flow = self.performance["Q_h_dot"] * 1000 / delta_h_sf

                # --- Simpan Hasil Fluida Eksternal ---
                self.external_fluid_results = {
                    'T_wh_out': T_wh_out,
                    'sf_mass_flow': sf_mass_flow,
                    'h_wh_in': h_wh_in,
                    'h_wh_out': h_wh_out,
                    'h_sf_in': h_sf_in,
                    'h_sf_out': h_sf_out
                }
                
                print(">> Heat Pump simulation complete. Results are stored in the object.")
            
            # Catch Error Termofisika (CoolProp Errors)
            except ValueError as ve:
                print(f"\n[!] THERMOPHYSICAL ERROR (CoolProp Failure) in Heat Pump Cycle")
                print(f"    Detail: {ve}")
                error_msg = str(ve).lower()
                if "temperature" in error_msg and ("critical" in error_msg or "max" in error_msg):
                    print("    Analisis: Temperatur input mungkin melebihi limit fluida.")
                
                print("    Lokasi Error:")
                traceback.print_exc(limit=1)
                
                # Bersihkan hasil agar tidak membaca data lama/salah
                self.real_states = {}
                self.performance = {}
                self.external_fluid_results = {}

            # Catch Error Matematika (Pembagian Nol)
            except ZeroDivisionError as zde:
                print(f"\n[!] MATHEMATICAL ERROR: {zde}")
                print("    Saran: Cek parameter input (mass flow, delta T) jangan sampai nol.")
                self.real_states = {}
                self.performance = {}

            # Catch Error Lainnya
            except Exception as e:
                print(f"\n[!] UNKNOWN ERROR: {e}")
                traceback.print_exc()
                self.real_states = {}
                self.performance = {}
    
    # -----------------------------------------------------------------
    # --- PRINTER METHODS
    # -----------------------------------------------------------------

    def print_state_information(self):
        """
        Mencetak tabel informasi state point (real cycle)
        dengan unit yang sudah dikonversi (degC, bar, kJ/kg).
        """
        if not self.real_states:
            print("Error: Jalankan .run_simulation() terlebih dahulu.")
            return

        try:
            T_list = self.real_states["T_r"]
            P_list = self.real_states["P_r"]
            S_list = self.real_states["S_r"]
            H_list = self.real_states["H_r"]
            X_list = self.real_states["X_r"]
        except KeyError as e:
            print(f"Error: Data '{e.args[0]}' tidak ditemukan di self.real_states.")
            return

        # Label state point sesuai urutan di list H_r
        state_labels = [
            "1 (EVA out / REC cold in)",
            "1_sup (REC cold out / CPR in)",
            "2 (CPR out / CDS in)",
            "23 (CDS desup. out)",
            "3_rec (CDS out / REC hot in)",
            "3 (REC hot out / TRV in)",
            "4 (TRV out / EVA in)"
        ]
        
        table_data = []
        headers = ["State Index", "T (°C)", "P (bar)", "S (kJ/kg.K)", "H (kJ/kg)", "X (Quality)"]

        for i in range(len(state_labels)):
            label = state_labels[i]
            
            if T_list[i] is None:
                row = [label, "---", "---", "---", "---", "---"]
            else:
                T_C = T_list[i] - 273.15
                P_bar = P_list[i] / 100000  # Pa ke bar
                S_kJ = S_list[i] / 1000     # J/kg.K ke kJ/kg.K
                H_kJ = H_list[i] / 1000     # J/kg ke kJ/kg
                
                X_raw = X_list[i]
                if isinstance(X_raw, (int, float)):
                    X_val = f"{X_raw:.4f}"
                elif X_raw is None:
                    X_val = "---"
                else:
                    X_val = str(X_raw) 
                
                row = [label, T_C, P_bar, S_kJ, H_kJ, X_val]
            
            table_data.append(row)

        print("\n--- Informasi State Point (Heat Pump Cycle) ---")
        col_formats = [None, ".2f", ".3f", ".4f", ".2f", None]
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=col_formats))

    def print_energy_and_performance(self):
            """
            Mencetak tabel laju transfer energi dan COP untuk siklus HP.
            Satuan: kW
            """
            # Cek apakah simulasi sudah dijalankan
            if not self.performance:
                print("Error: Jalankan .run_simulation() terlebih dahulu.")
                return
                
            # Ambil data dari self.performance
            Q_h = self.performance.get('Q_h_dot')
            Q_l = self.performance.get('Q_l_dot')
            W_in = self.w_cpr_kw # Diambil dari input
            COP_hp = self.performance.get('COP_hp') # <-- DATA COP DIAMBIL
            
            if Q_h is None or Q_l is None or COP_hp is None:
                print("Error: Data performa tidak lengkap.")
                return

            # Siapkan data untuk tabulate
            table_data = [
                ["Q_h (Heat Rejected)", Q_h, "kW"],
                ["Q_l (Heat Absorbed)", Q_l, "kW"],
                ["W_in (Compressor)", W_in, "kW"],
                ["COP_hp (Q_h / W_in)", COP_hp, "---"], # <-- COP DITAMBAHKAN DI SINI
            ]
            
            headers = ["Komponen Energi / Performa", "Nilai", "Satuan"]

            print("\n--- Analisis Energi & Performa (Heat Pump) ---")
            print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=".4f"))
            
            # Verifikasi
            verification = Q_l + W_in
            print(f"Catatan: Q_l + W_in = {Q_l:.4f} + {W_in:.4f} = {verification:.4f} kW\n"
                f"         (Harus sama dengan Q_h)")
    def print_mass_flow(self):
        """
        Mencetak tabel mass flow rate untuk semua fluida terkait HP.
        Satuan: kg/s
        """
        if not self.performance or not self.external_fluid_results:
            print("Error: Jalankan .run_simulation() terlebih dahulu.")
            return

        m_cycle = self.performance.get('wf_mass_flow')
        m_sf = self.external_fluid_results.get('sf_mass_flow')
        m_wh = self.wh_mass_flow # Diambil dari input

        table_data = [
            [1, "Fluida Kerja (Cycle)", self.fluid, m_cycle],
            [2, "Secondary Fluid (SF)", self.sf_fluid, m_sf],
            [3, "Waste Heat (WH)", self.wh_fluid, m_wh],
        ]
        headers = ["Nomor", "Deskripsi", "Jenis Fluida", "Nilai (kg/s)"]
        
        print("\n--- Analisis Mass Flow Rate (Heat Pump) ---")
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=".4f"))

    def print_wh_prop(self):
        """
        Mencetak tabel properti untuk Waste Heat Source (Fluida Panas).
        Satuan: degC, kJ/kg
        """
        if not self.external_fluid_results:
            print("Error: Jalankan .run_simulation() terlebih dahulu.")
            return

        try:
            T_in = self.T_wh_in # Dari input (K)
            T_out = self.external_fluid_results["T_wh_out"]
            h_in = self.external_fluid_results["h_wh_in"]
            h_out = self.external_fluid_results["h_wh_out"]
            m_dot_wh = self.wh_mass_flow
        except (KeyError, AttributeError) as e:
            print(f"Error: Data simulasi WH tidak lengkap ({e}).")
            return

        # Konversi Unit
        T_in_C = T_in - 273.15
        T_out_C = T_out - 273.15
        h_in_kJ = h_in / 1000
        h_out_kJ = h_out / 1000
        
        table_data = [
            [1, "WH In",  T_in_C,  h_in_kJ],
            [2, "WH Out", T_out_C, h_out_kJ],
        ]
        headers = ["Nomor", "Index Waste Heat", "T (°C)", "H (kJ/kg)"]
        
        # Verifikasi Q_l (Heat Absorbed)
        Q_l_wh = m_dot_wh * (h_in_kJ - h_out_kJ)
        
        print("\n--- Properti Waste Heat Source (Sisi Q_l) ---")
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=".2f"))
        print("Catatan:")
        print(f"         1. Mass Flow Waste Heat (m_dot_wh): {m_dot_wh:.4f} kg/s")
        print(f"         2. Verifikasi Q_l (sisi WH): {Q_l_wh:.4f} kW")

    def print_sf_prop(self):
        """
        Mencetak tabel properti untuk Secondary Fluid (Fluida Dingin).
        Satuan: degC, kJ/kg
        """
        if not self.sf_temps or not self.external_fluid_results:
            print("Error: Jalankan .run_simulation() terlebih dahulu.")
            return

        try:
            T_in = self.sf_temps["T_sf_in_r"]
            T_out = self.sf_temps["T_sf_out_r"]
            h_in = self.external_fluid_results["h_sf_in"]
            h_out = self.external_fluid_results["h_sf_out"]
            m_dot_sf = self.external_fluid_results["sf_mass_flow"]
        except (KeyError, AttributeError) as e:
            print(f"Error: Data simulasi SF tidak lengkap ({e}).")
            return

        # Konversi Unit
        T_in_C = T_in - 273.15
        T_out_C = T_out - 273.15
        h_in_kJ = h_in / 1000
        h_out_kJ = h_out / 1000
        
        table_data = [
            [1, "SF In",  T_in_C,  h_in_kJ],
            [2, "SF Out", T_out_C, h_out_kJ],
        ]
        headers = ["Nomor", "Index Secondary Fluid", "T (°C)", "H (kJ/kg)"]
        
        # Verifikasi Q_h (Heat Rejected)
        Q_h_sf = m_dot_sf * (h_out_kJ - h_in_kJ)
        
        print("\n--- Properti Secondary Fluid (Sisi Q_h) ---")
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=".2f"))
        print("Catatan:")
        print(f"         1. Mass Flow Secondary Fluid (m_dot_sf): {m_dot_sf:.4f} kg/s")
        print(f"         2. Verifikasi Q_h (sisi SF): {Q_h_sf:.4f} kW")



# if __name__ == "__main__":
    
#     # --- 1. Definisikan Input HANYA untuk HeatPumpRec ---
#     # (Data diambil dari dictionary besar yang kamu berikan)

#     # Lakukan kalkulasi T yang diperlukan (sesuai logic main.py lama)
#     # Ubah dari Celcius ke Kelvin
#     T_wh_in_K = 166 + 273.15      # Dari "T_wh"
#     T_sf_out_K = 200 + 5 + 273.15 # Dari "T_melting" + 5 K
    
#     hp_inputs = {
#         # Input dari 'hp_rec_after_cds'
#         "fluid": "Toluene",             # dari "wf_hp"
#         "T_sf_out": T_sf_out_K,         # sudah dikalkulasi
#         "T_wh_in": T_wh_in_K,           # sudah dikalkulasi
#         "T_pinch_sf_out": 10,
#         "T_pinch_wh_in": 5,
#         "T_pinch_sf_in": 5,
#         "delta_sup": 25,
#         "w_cpr_kw": 100,                # dari "cpr_pwr"
#         "eta_cpr": 0.75,
        
#         # Input dari 'mass_flow_calculation_revised'
#         "wh_mass_flow": 715.83,
#         "p_wh": 780000,
#         "p_sf": 200000,
#         "wh_fluid": "Water",
#         "sf_fluid": "INCOMP::DowJ2",
#     }

#     # --- 2. Buat Objek (Instance) dari Siklus ---
#     print(f"Memulai simulasi Heat Pump untuk fluida: {hp_inputs['fluid']}")
#     my_heat_pump = HeatPumpRec(**hp_inputs)

#     # --- 3. Jalankan Simulasi ---
#     # (Ini akan menjalankan 'hp_rec_after_cds' DAN 'mass_flow_calculation_revised')
#     my_heat_pump.run_simulation()

#     # --- 4. Panggil semua method printer ---
#     print("\n" + "="*50)
#     print("      HASIL SIMULASI HEAT PUMP (STANDALONE TEST)      ")
#     print("="*50)
    
#     my_heat_pump.print_state_information()
#     my_heat_pump.print_wh_prop()
#     my_heat_pump.print_sf_prop()
#     my_heat_pump.print_mass_flow()
#     my_heat_pump.print_energy_and_performance()
    
#     print("\n" + "="*50)
#     print("               TEST SIMULASI HP SELESAI               ")
#     print("="*50)