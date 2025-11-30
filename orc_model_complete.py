import CoolProp.CoolProp as CP
from tabulate import tabulate
import traceback

class ORCBase():
    """Initialize the ORC system with the given parameters."""
    def __init__(self, eta_exp, eta_pmp, T_hs_in, T_cs_in, fluid_ref, wf_mass_flow, p_hs_in, p_cs_in, hs_fluid, cs_fluid, reference_temperature=273.15):
        self.fluid      = fluid_ref
        self.eta_exp    = eta_exp
        self.eta_pmp    = eta_pmp
        self.T_cs_in    = T_cs_in
        self.T_hs_in    = T_hs_in
        self.wf_mass_flow = wf_mass_flow
        self.p_hs_in    = p_hs_in
        self.p_cs_in    = p_cs_in
        self.hs_fluid   = hs_fluid
        self.cs_fluid   = cs_fluid
        self.reference_temperature = reference_temperature
        # --- 2. Siapkan Atribut untuk Menyimpan Hasil ---
        self.ideal_states = {}
        self.real_states = {}
        self.hs_temps = {}
        self.cs_temps = {}

    def run_simulation(self, T_estimation_cs, T_estimation_hs, T_pinch_hs, T_pinch_cs):
        """Solve the ORC cycle with ideal and real conditions.  """
        # Define cooling source temperature
        self.T_cs_mid1 = self.T_cs_in + T_estimation_cs
        self.T_hs_mid1 = self.T_hs_in - T_estimation_hs

        # Define high and low temperature
        T_high  = self.T_hs_mid1 - T_pinch_hs
        T_lower = self.T_cs_mid1 + T_pinch_cs

        ##########################################################
        #################### IDEAL CONDITIONS ####################
        ##########################################################
        # state 0 (Input: T0 dan X0)
        T0 = T_high
        X0 = 0
        P0 = CP.PropsSI('P', 'T', T0, 'Q', X0, self.fluid)
        H0 = CP.PropsSI('H', 'T', T0, 'Q', X0, self.fluid)
        S0 = CP.PropsSI('S', 'T', T0, 'Q', X0, self.fluid)

        # state 1 (Input: T1 dan X1)
        T1 = T0
        X1 = 1
        P1 = CP.PropsSI('P', 'T', T1, 'Q', X1, self.fluid)
        H1 = CP.PropsSI('H', 'T', T1, 'Q', X1, self.fluid)
        S1 = CP.PropsSI('S', 'T', T1, 'Q', X1, self.fluid)

        # state 3 (Input: T3 dan X3)
        T3 = T_lower
        X3 = 0
        P3 = CP.PropsSI('P', 'T', T3, 'Q', X3, self.fluid)
        H3 = CP.PropsSI('H', 'T', T3, 'Q', X3, self.fluid)
        S3 = CP.PropsSI('S', 'T', T3, 'Q', X3, self.fluid)

        # state 2 (Input: p2 dan s2)
        S2 = S1
        P2 = P3
        H2 = CP.PropsSI('H', 'S', S2, 'P', P2, self.fluid)
        T2 = CP.PropsSI('T', 'S', S2, 'P', P2, self.fluid)

        # state 23 (Input: X23 dan T2)
        P23 = P3
        X23 = 1
        T23 = T_lower
        H23 = CP.PropsSI('H', 'T', T23, 'Q', X23, self.fluid)
        S23 = CP.PropsSI('S', 'T', T23, 'Q', X23, self.fluid)

        # state 4 (Input: s4 dan p4)
        S4 = S3
        P4 = P0
        H4 = CP.PropsSI('H', 'S', S4, 'P', P4, self.fluid)
        T4 = CP.PropsSI('T', 'S', S4, 'P', P4, self.fluid)

        ##########################################################
        #################### REAL CONDITIONS #####################
        ##########################################################
        # state 0 (Input: T0 dan X0) before evaporator
        T0re = T0-1
        X0re = X0
        P0re = CP.PropsSI('P', 'T', T0re, 'Q', X0re, self.fluid)
        H0re = CP.PropsSI('H', 'T', T0re, 'Q', X0re, self.fluid)
        S0re = CP.PropsSI('S', 'T', T0re, 'Q', X0re, self.fluid)

        # state 1 (Input: T1 dan X1) before expander
        T1re = T0re-1
        X1re = 1
        P1re = CP.PropsSI('P', 'T', T1re, 'Q', X1re, self.fluid)
        H1re = CP.PropsSI('H', 'T', T1re, 'Q', X1re, self.fluid)
        S1re = CP.PropsSI('S', 'T', T1re, 'Q', X1re, self.fluid)

        # state 3 (Input: T3 dan X3) after condenser
        T3re = T3-2
        X3re = 0
        P3re = CP.PropsSI('P', 'T', T3re, 'Q', X3re, self.fluid)
        H3re = CP.PropsSI('H', 'T', T3re, 'Q', X3re, self.fluid)
        S3re = CP.PropsSI('S', 'T', T3re, 'Q', X3re, self.fluid)

        # state 2 (Input: p2 dan s2) after expander
        P2re    = P3 #perlu konfirmasi apakah referensi p2 real menggunakan p3 ideal atau p3 real. saya memakai 
                    # P2re = P3 karena P3 real sudah mengalami temperature drop 
                    # yang berarti juga adanya pressure drop. jadi, menurut saya p2 tdk sama dgn p3
                    # atau justru p2re = p23re 
        S2re_is = S1re
        H2re_is = CP.PropsSI('H', 'S', S2re_is, 'P', P2re, self.fluid)
        H2re    = H1re - self.eta_exp * (H1re - H2re_is)
        S2re    = CP.PropsSI('S', 'H', H2re, 'P', P2re, self.fluid)
        T2re    = CP.PropsSI('T', 'H', H2re, 'P', P2re, self.fluid)
        X2re = CP.PhaseSI('Q', 'H', H2re, 'P', P2re, self.fluid)

        # state 23 (Input: X23 dan T2) after desuperheater
        X23re = 1
        T23re = T23 - 1
        P23re = CP.PropsSI('P', 'T', T23re, 'Q', X23re, self.fluid)
        H23re = CP.PropsSI('H', 'T', T23re, 'Q', X23re, self.fluid)
        S23re = CP.PropsSI('S', 'T', T23re, 'Q', X23re, self.fluid)

        # state 4 (Input: s4 dan p4) after pump
        S4re_is = S3re
        P4re    = P0re
        H4re_is = CP.PropsSI('H', 'S', S4re_is, 'P', P4re, self.fluid)
        H4re    = H3re + (H4re_is - H3re)/self.eta_pmp
        S4re    = CP.PropsSI('S', 'H', H4re, 'P', P4re, self.fluid)
        T4re    = CP.PropsSI('T', 'H', H4re, 'P', P4re, self.fluid)
        X4re = CP.PhaseSI('Q', 'H', H4re, 'P', P4re, self.fluid)

        self.H_is_list = [H0, H1, H2, H23, H3, H4]
        self.s_is_list = [S0, S1, S2, S23, S3, S4]
        self.p_is_list = [P0, P1, P2, P23, P3, P4]
        self.T_is_list = [T0, T1, T2, T23, T3, T4]
        self.X_is_list = [X0, X1, None, X23, X3, None]

        self.H_re_list = [H0re, H1re, H2re, H23re, H3re, H4re]
        self.s_re_list = [S0re, S1re, S2re, S23re, S3re, S4re]
        self.p_re_list = [P0re, P1re, P2re, P23re, P3re, P4re]
        self.T_re_list = [T0re, T1re, T2re, T23re, T3re, T4re]
        self.X_re_list = [X0re, X1re, X2re, X23re, X3re, None]

        # Calculating T_hs_out and calculating other termophysical properties for heat source
        h_hs_in = CP.PropsSI('H', 'T', self.T_hs_in, 'P', self.p_hs_in, self.hs_fluid)
        p_hs_mid1 = 0.99 * self.p_hs_in # 1% Pressure drop
        p_hs_out = 0.98 * self.p_hs_in # 2% pressure drop
        h_hs_mid1 = CP.PropsSI('H', 'T', self.T_hs_mid1, 'P', p_hs_mid1, self.hs_fluid)
        # Calculate hs_mass_flow (kg/s)
        q_demand_hs = self.wf_mass_flow * (H1re - H4re)
        hs_mass_flow = q_demand_hs / (h_hs_in - h_hs_mid1)
        h_hs_out = h_hs_in - (self.wf_mass_flow * (H1re - H4re) / hs_mass_flow) 
        T_hs_out = CP.PropsSI('T', 'H', h_hs_out, 'P', p_hs_out, self.hs_fluid)

        # Calculating T_cs_out and calculating other termophysical properties for cooling source
        h_cs_in = CP.PropsSI('H', 'T', self.T_cs_in, 'P', self.p_cs_in, self.cs_fluid)
        p_cs_mid1 = 0.99 * self.p_cs_in # 1% Pressure drop
        p_cs_out = 0.98 * self.p_cs_in # 2% pressure drop
        h_cs_mid1 = CP.PropsSI('H', 'T', self.T_cs_mid1, 'P', p_cs_mid1, self.cs_fluid)
        # Calculate cs_mass_flow (kg/s)
        cs_mass_flow = self.wf_mass_flow * (H23re - H3re) / (h_cs_mid1 - h_cs_in)
        h_cs_out = (self.wf_mass_flow * (H2re - H3re) / cs_mass_flow) + h_cs_in
        T_cs_out = CP.PropsSI('T', 'H', h_cs_out, 'P', p_cs_out, self.cs_fluid)

        H_hs = [h_hs_in, h_hs_mid1, h_hs_out]
        H_cs = [h_cs_in, h_cs_mid1, h_cs_out]
        # Simpan ke atribut class
        self.ideal_states = {"H": self.H_is_list, "T": self.T_is_list, "P": self.p_is_list, "S": self.s_is_list, "X": self.X_is_list}
        self.real_states = {"H": self.H_re_list, "T": self.T_re_list, "P": self.p_re_list, "S": self.s_re_list, "X": self.X_re_list}
        self.hs_temps = {
            "T_hs_in": self.T_hs_in, 
            "T_hs_mid1": self.T_hs_mid1, "T_hs_out": T_hs_out
        }
        self.cs_temps = {
            "T_cs_in": self.T_cs_in, "T_cs_mid1": self.T_cs_mid1, "T_cs_out": T_cs_out
        }
        self.external_h = {"H_hs": H_hs, "H_cs": H_cs}
        self.sim_results = {
            "Q_demand_hs": q_demand_hs,
            "hs_mass_flow": hs_mass_flow,
            "cs_mass_flow": cs_mass_flow
        }
    def print_delta_enthalpy_real(self):
        """
        Mencetak tabel selisih entalpi antar komponen (Real Cycle).
        Satuan: kJ/kg
        """
        # Cek apakah simulasi sudah dijalankan
        if not self.real_states:
            print("Error: Jalankan .run_simulation() terlebih dahulu.")
            return

        # Ambil list H_r dari hasil simulasi

        H = self.real_states["H"]
        
        # Mapping variabel supaya rumus mudah dibaca (satuan masih J/kg)
        h0_r      = H[0]
        h1_r      = H[1]
        h2_r   = H[2]
        h3_r  = H[-2]
        h4_r = H[-1] # Tidak dipakai di rumus request


        # Kalkulasi Delta H (Dikonversi ke kJ/kg dengan membagi 1000)
        val_lh      = (h0_r - h4_r) / 1000
        val_eva     = (h1_r - h0_r) / 1000
        val_exp     = (h1_r - h2_r) / 1000
        val_cds     = (h2_r - h3_r) / 1000 # Total rejection dari post-recuperator
        val_pmp     = (h4_r - h3_r) / 1000

        # Siapkan data untuk tabulate
        table_data = [
            [1, "LH (Liquid Heater)", val_lh],
            [2, "EVA (Evaporator)",   val_eva],
            [3, "EXP (Expander)",     val_exp],
            [4, "CDS (Condenser)",    val_cds],
            [5, "PMP (Pump)",         val_pmp],
        ]

        headers = ["Nomor", "Nama Komponen", "Nilai (kJ/kg)"]
        
        print("\n--- Analisis Entalpi Komponen (Real Cycle) ---")
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=".4f"))
    def print_mass_flow(self):
        """
        Mencetak tabel mass flow rate untuk fluida kerja,
        fluida panas (heat source), dan fluida dingin (cooling source).
        Satuan: kg/s
        """
        # Cek apakah simulasi sudah dijalankan
        if not self.sim_results:
            print("Error: Jalankan .run_simulation() terlebih dahulu.")
            return

        # Ambil data dari atribut 'self'
        # 1. Fluida Kerja (Siklus)
        m_cycle = self.wf_mass_flow
        fluid_cycle = self.fluid

        # 2. Fluida Panas (Heat Source)
        m_hs = self.sim_results.get('hs_mass_flow')
        fluid_hs = self.hs_fluid

        # 3. Fluida Dingin (Cooling Source)
        m_cs = self.sim_results.get('cs_mass_flow')
        fluid_cs = self.cs_fluid
        
        # Siapkan data untuk tabulate
        table_data = [
            [1, "Fluida Kerja (Cycle)",   fluid_cycle, m_cycle],
            [2, "Heat Source (S. Panas)", fluid_hs,    m_hs],
            [3, "Cooling Source (S. Dingin)", fluid_cs,  m_cs],
        ]

        headers = ["Nomor", "Deskripsi", "Jenis Fluida", "Nilai (kg/s)"]
        
        print("\n--- Analisis Mass Flow Rate ---")
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=".4f"))
    def print_energy_transfer(self):
            """
            Mencetak tabel laju transfer energi untuk setiap komponen
            berdasarkan mass flow fluida kerja (wf_mass_flow).
            Satuan: kW
            """
            # Cek apakah simulasi sudah dijalankan
            if not self.real_states:
                print("Error: Jalankan .run_simulation() terlebih dahulu.")
                return

            # Ambil list H_r (J/kg) dan mass flow (kg/s)
            H = self.real_states["H"]
            m_dot = self.wf_mass_flow

            # Mapping variabel supaya rumus mudah dibaca (satuan masih J/kg)
            h0_r      = H[0]
            h1_r      = H[1]
            h1sup_r   = H[2]
            h2_r      = H[3]
            h23rec_r  = H[4]
            h3_r      = H[6]
            h4_r      = H[7]
            h41rec_r  = H[8]

            # 1. Hitung spesifik delta h (kJ/kg)
            dh_lh      = (h0_r - h41rec_r) / 1000
            dh_eva     = (h1_r - h0_r) / 1000
            dh_sup     = (h1sup_r - h1_r) / 1000
            dh_exp     = (h1sup_r - h2_r) / 1000
            dh_cds     = (-h23rec_r + h3_r) / 1000 # (h3_r - h23rec_r)
            dh_pmp     = (h3_r - h4_r) / 1000
            
            # Energi recuperator (untuk catatan)
            dh_rec     = (h41rec_r - h4_r) / 1000 

            # 2. Hitung Laju Energi (kW) = (kJ/kg) * (kg/s)
            E_lh   = dh_lh * m_dot
            E_eva  = dh_eva * m_dot
            E_sup  = dh_sup * m_dot
            E_exp  = dh_exp * m_dot
            E_cds  = dh_cds * m_dot
            E_pmp  = dh_pmp * m_dot
            
            # Energi recuperator (untuk catatan)
            E_rec  = dh_rec * m_dot 

            # Siapkan data untuk tabulate (TANPA RECUPERATOR)
            table_data = [
                [1, "LH (Liquid Heater)", E_lh],
                [2, "EVA (Evaporator)",   E_eva],
                [3, "SUP (Superheater)",  E_sup],
                [4, "EXP (Expander)",     E_exp],
                [5, "CDS (Condenser)",    E_cds],
                [6, "PMP (Pump)",         E_pmp],
            ]

            headers = ["Nomor", "Komponen", "Energi Transfer (kW)"]
            
            print("\n--- Analisis Laju Transfer Energi (Siklus) ---")
            print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=".4f"))
            
            # --- Catatan dimodifikasi di sini ---
            print(f"Catatan: (+) = Energi yang dikerjakan oleh sistem (Panas/Kerja OUT)\n"
                f"         (-) = Energi yang dikerjakan pada sistem (Panas/Kerja IN)")
    def print_hs_prop(self):
        """
        Mencetak tabel properti untuk Heat Source (Fluida Panas).
        Satuan: degC, kJ/kg
        """
        # Cek apakah simulasi sudah dijalankan
        if not self.hs_temps or not self.external_h or not self.sim_results:
            print("Error: Jalankan .run_simulation() terlebih dahulu.")
            return

        # Ambil data dari atribut 'self'
        try:
            # Ambil Temperatur (dalam K)
            T_in = self.hs_temps["T_hs_in"]
            T_mid1 = self.hs_temps["T_hs_mid1"]
            T_out = self.hs_temps["T_hs_out"]
            
            # Ambil Entalpi (dalam J/kg)
            H_list = self.external_h["H_hs"] # [h_in, h_mid2, h_mid1, h_out]
            h_in = H_list[0]
            h_mid1 = H_list[1]
            h_out = H_list[2]
            
            # Ambil mass flow (kg/s)
            m_dot_hs = self.sim_results["hs_mass_flow"]
            
        except (KeyError, IndexError) as e:
            print(f"Error: Data simulasi HS tidak lengkap ({e}).")
            return

        # 1. Konversi Unit
        # T (K -> degC)
        T_in_C = T_in - 273.15
        T_mid1_C = T_mid1 - 273.15
        T_out_C = T_out - 273.15
        
        # H (J/kg -> kJ/kg)
        h_in_kJ = h_in / 1000
        h_mid1_kJ = h_mid1 / 1000
        h_out_kJ = h_out / 1000
        
        # 2. Siapkan data tabel
        table_data = [
            [1, "HS In",      T_in_C,   h_in_kJ],
            [2, "HS Mid 1",   T_mid1_C, h_mid1_kJ],
            [3, "HS Out",     T_out_C,  h_out_kJ],
        ]
        
        headers = ["Nomor", "Index Heat Source", "T (°C)", "H (kJ/kg)"]

        # 3. Hitung Q_in verifikasi
        # Q (kW) = m_dot (kg/s) * delta_h (kJ/kg)
        Q_in_hs = m_dot_hs * (h_in_kJ - h_out_kJ)
        
        # 4. Print tabel dan catatan
        print("\n--- Properti Heat Source (Fluida Panas) ---")
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=".2f"))
        
        print("Catatan:")
        print(f"         1. Mass Flow Heat Source (m_dot_hs): {m_dot_hs:.4f} kg/s")
        print(f"         2. Verifikasi Q_in (sisi HS): {Q_in_hs:.4f} kW")
        print(f"         3. Tekanan Heat Source diasumsikan konstan pada {self.p_hs_in/100000:.2f} bar")
    def print_cs_prop(self):
        """
        Mencetak tabel properti untuk Cooling Source (Fluida Dingin).
        Satuan: degC, kJ/kg
        """
        # Cek apakah simulasi sudah dijalankan
        if not self.cs_temps or not self.external_h or not self.sim_results:
            print("Error: Jalankan .run_simulation() terlebih dahulu.")
            return

        # Ambil data dari atribut 'self'
        try:
            # Ambil Temperatur (dalam K)
            T_in = self.cs_temps["T_cs_in"]
            T_mid1 = self.cs_temps["T_cs_mid1"]
            T_out = self.cs_temps["T_cs_out"]
            
            # Ambil Entalpi (dalam J/kg)
            # Urutan di 'run_simulation': [h_cs_in, h_cs_mid1, h_cs_out]
            H_list = self.external_h["H_cs"] 
            h_in = H_list[0]
            h_mid1 = H_list[1]
            h_out = H_list[2]
            
            # Ambil mass flow (kg/s)
            m_dot_cs = self.sim_results["cs_mass_flow"]
            
        except (KeyError, IndexError) as e:
            print(f"Error: Data simulasi CS tidak lengkap ({e}).")
            return

        # 1. Konversi Unit
        # T (K -> degC)
        T_in_C = T_in - 273.15
        T_mid1_C = T_mid1 - 273.15
        T_out_C = T_out - 273.15
        
        # H (J/kg -> kJ/kg)
        h_in_kJ = h_in / 1000
        h_mid1_kJ = h_mid1 / 1000
        h_out_kJ = h_out / 1000
        
        # 2. Siapkan data tabel
        table_data = [
            [1, "CS In",      T_in_C,   h_in_kJ],
            [2, "CS Mid 1",   T_mid1_C, h_mid1_kJ],
            [3, "CS Out",     T_out_C,  h_out_kJ],
        ]
        
        headers = ["Nomor", "Index Cooling Source", "T (°C)", "H (kJ/kg)"]

        # 3. Hitung Q_out verifikasi
        # Q (kW) = m_dot (kg/s) * delta_h (kJ/kg)
        # (Energi yang diserap oleh fluida pendingin)
        Q_out_cs = m_dot_cs * (h_out_kJ - h_in_kJ)
        
        # 4. Print tabel dan catatan
        print("\n--- Properti Cooling Source (Fluida Dingin) ---")
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=".2f"))
        
        print("Catatan:")
        print(f"         1. Mass Flow Cooling Source (m_dot_cs): {m_dot_cs:.4f} kg/s")
        print(f"         2. Verifikasi Q_out (sisi CS): {Q_out_cs:.4f} kW")
        print(f"         3. Tekanan Cooling Source diasumsikan konstan pada {self.p_cs_in/100000:.2f} bar")
    def print_state_information(self):
        """
        Mencetak tabel informasi state point (real cycle)
        dengan unit yang sudah dikonversi (degC, bar, kJ/kg).
        """
        # Cek apakah simulasi sudah dijalankan
        if not self.real_states:
            print("Error: Jalankan .run_simulation() terlebih dahulu.")
            return

        # Ambil data list dari self.real_states
        # Pastikan run_simulation sudah mengisi "X"
        try:
            T_list = self.real_states["T"]
            P_list = self.real_states["P"]
            S_list = self.real_states["S"]
            H_list = self.real_states["H"]
            X_list = self.real_states["X"]
        except KeyError as e:
            print(f"Error: Data '{e.args[0]}' tidak ditemukan di self.real_states.")
            print("Pastikan run_simulation sudah menyimpan 'X' di self.real_states.")
            return

        # Label state point sesuai urutan di list
        state_labels = [
            "0 (Outlet LH)", 
            "1 (Outlet EVA)", 
            "2 (Outlet EXP)", 
            "23 (Desuperheater)", 
            "3 (Outlet CDS)", 
            "4 (Outlet PMP)"
        ]
        
        table_data = []
        headers = ["State Index", "T (°C)", "P (bar)", "S (kJ/kg.K)", "H (kJ/kg)", "X (Quality)"]

        # Loop untuk setiap state, konversi unit, dan format data
        for i in range(len(state_labels)):
            label = state_labels[i]
            
            # Cek jika state (seperti 23rec3) tidak dihitung (None)
            if T_list[i] is None:
                row = [label, "---", "---", "---", "---", "---"]
            else:
                # Lakukan konversi unit
                T_C = T_list[i] - 273.15
                P_bar = P_list[i] / 100000  # Pa ke bar
                S_kJ = S_list[i] / 1000     # J/kg.K ke kJ/kg.K
                H_kJ = H_list[i] / 1000     # J/kg ke kJ/kg
                
                # Format X (Quality)
                X_raw = X_list[i]
                if isinstance(X_raw, (int, float)):
                    # Jika X adalah angka (0, 1, atau nilai quality 0-1)
                    X_val = f"{X_raw:.4f}"
                elif X_raw is None:
                    # Jika X adalah None
                    X_val = "---"
                else:
                    # Jika X adalah string (misal 'gas', 'liquid', 'supercritical')
                    X_val = str(X_raw) 
                
                row = [label, T_C, P_bar, S_kJ, H_kJ, X_val]
            
            table_data.append(row)

        print("\n--- Informasi State Point (Real Cycle) ---")
        
        # Tentukan format angka untuk setiap kolom
        # [Index, T, P, S, H, X]
        col_formats = [None, ".2f", ".3f", ".4f", ".2f", None]
        
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=col_formats))
    def calculate_performance(self, use_ideal_states=False):
        """
        Menghitung performa siklus (efisiensi, W_net)
        berdasarkan hasil simulasi.
        
        Args:
            use_ideal_states (bool): Jika True, hitung performa ideal.
                                     Defaultnya False (hitung real).
        """
        if not self.real_states:
            print("Error: Jalankan .run_simulation() terlebih dahulu.")
            return None

        if use_ideal_states:
            H_list = self.ideal_states["H"]
        else:
            H_list = self.real_states["H"]
            
        # Indeks berdasarkan list H_r/H_is:
        # 2: H1_sup (SUP out)
        # 3: H2 (EXP out)
        # 6: H3 (CDS out)
        # 7: H4 (PMP out)
        # 8: H41rec (REC out to LH)

        W_dot_exp_spec = (H_list[2] - H_list[1]) / 1000  # kJ/kg
        W_dot_pmp_spec = (H_list[-1] - H_list[-2]) / 1000  # kJ/kg
        W_dot_net_spec = W_dot_exp_spec - W_dot_pmp_spec

        Q_dot_in_spec = (H_list[1] - H_list[-1]) / 1000 # Q_in = H_sup_out - H_rec_out
        # Hindari pembagian dengan nol jika Q_dot_in_spec adalah 0
        if Q_dot_in_spec == 0:
            eta_thermal = 0
        else:
            eta_thermal = W_dot_net_spec / Q_dot_in_spec

        # Kalkulasi 2nd law efficiency
        factor = 1 - (self.reference_temperature / self.T_hs_in)
        second_law_efficiency = eta_thermal / factor if factor != 0 else 0
        # Simpan hasil performa ke 'self'
        self.performance = {
            "eta_thermal": eta_thermal,
            "W_dot_net_kW": W_dot_net_spec * self.wf_mass_flow,
            "Q_dot_in_kW": Q_dot_in_spec * self.wf_mass_flow,
            "W_dot_exp_kW": W_dot_exp_spec * self.wf_mass_flow,
            "W_dot_pmp_kW": W_dot_pmp_spec * self.wf_mass_flow,
            "second_law_efficiency": second_law_efficiency
        }
        
        print(f"Performa (Real) berhasil dikalkulasi. Efisiensi Termal: {eta_thermal:.2%}")
        return self.performance

class ORCSuperheat():
    """Initialize the ORC system with the given parameters."""
    def __init__(self, eta_exp, eta_pmp, T_hs_in, T_cs_in, fluid_ref, wf_mass_flow, p_hs_in, hs_fluid, reference_temperature=273.15, cs_fluid='Air', p_cs_in=200000):
        self.fluid      = fluid_ref
        self.eta_exp    = eta_exp
        self.eta_pmp    = eta_pmp
        self.T_cs_in    = T_cs_in
        self.T_hs_in    = T_hs_in
        self.wf_mass_flow = wf_mass_flow
        self.p_hs_in    = p_hs_in
        self.p_cs_in    = p_cs_in
        self.hs_fluid   = hs_fluid
        self.cs_fluid   = cs_fluid
        self.reference_temperature = reference_temperature
        # --- 2. Siapkan Atribut untuk Menyimpan Hasil ---
        self.ideal_states = {}
        self.real_states = {}
        self.hs_temps = {}
        self.cs_temps = {}

    def run_simulation(self, T_pinch_hs_in, T_estimation_hs, T_estimation_cs, T_pinch_hs_mid1, T_pinch_cs_mid1):
        """Solve the ORC cycle with ideal and real conditions.  """
        # Define temperature levels
        T_high = self.T_hs_in - T_pinch_hs_in
        self.T_hs_mid1 = self.T_hs_in - T_estimation_hs
        self.T_cs_mid1 = self.T_cs_in + T_estimation_cs
        T_lower = self.T_cs_mid1 + T_pinch_cs_mid1

        ##########################################################
        #################### IDEAL CONDITIONS ####################
        ##########################################################
        # state 0 (Input: T0 dan X0)
        T0 = self.T_hs_mid1 - T_pinch_hs_mid1
        X0 = 0
        P0 = CP.PropsSI('P', 'T', T0, 'Q', X0, self.fluid)
        H0 = CP.PropsSI('H', 'T', T0, 'Q', X0, self.fluid)
        S0 = CP.PropsSI('S', 'T', T0, 'Q', X0, self.fluid)

        # state 1 (Input: T1 dan X1)
        T1 = T0
        X1 = 1
        P1 = CP.PropsSI('P', 'T', T1, 'Q', X1, self.fluid)
        H1 = CP.PropsSI('H', 'T', T1, 'Q', X1, self.fluid)
        S1 = CP.PropsSI('S', 'T', T1, 'Q', X1, self.fluid)

        # state 1sup (Input: T1sup dan P1sup)
        T1sup = T_high
        P1sup = P1
        H1sup = CP.PropsSI('H', 'T', T1sup, 'P', P1sup, self.fluid)
        S1sup = CP.PropsSI('S', 'T', T1sup, 'P', P1sup, self.fluid)
        X1sup = CP.PhaseSI('Q', 'T', T1sup, 'P', P1sup, self.fluid)

        # state 3 (Input: T3 dan X3)
        T3 = T_lower
        X3 = 0
        P3 = CP.PropsSI('P', 'T', T3, 'Q', X3, self.fluid)
        H3 = CP.PropsSI('H', 'T', T3, 'Q', X3, self.fluid)
        S3 = CP.PropsSI('S', 'T', T3, 'Q', X3, self.fluid)

        # state 2 (Input: p2 dan s2)
        S2 = S1
        P2 = P3
        H2 = CP.PropsSI('H', 'S', S2, 'P', P2, self.fluid)
        T2 = CP.PropsSI('T', 'S', S2, 'P', P2, self.fluid)
        X2 = CP.PhaseSI('Q', 'H', H2, 'P', P2, self.fluid)

        # state 23 (Input: X23 dan T2)
        P23 = P3
        X23 = 1
        T23 = T_lower
        H23 = CP.PropsSI('H', 'T', T23, 'Q', X23, self.fluid)
        S23 = CP.PropsSI('S', 'T', T23, 'Q', X23, self.fluid)

        # state 4 (Input: s4 dan p4)
        S4 = S3
        P4 = P0
        H4 = CP.PropsSI('H', 'S', S4, 'P', P4, self.fluid)
        T4 = CP.PropsSI('T', 'S', S4, 'P', P4, self.fluid)
        X4 = CP.PhaseSI('Q', 'H', H4, 'P', P4, self.fluid)

        ##########################################################
        #################### REAL CONDITIONS #####################
        ##########################################################
        # state 0 (Input: T0 dan X0) before evaporator
        T0re = T0-1
        X0re = 0
        P0re = CP.PropsSI('P', 'T', T0re, 'Q', X0re, self.fluid)
        H0re = CP.PropsSI('H', 'T', T0re, 'Q', X0re, self.fluid)
        S0re = CP.PropsSI('S', 'T', T0re, 'Q', X0re, self.fluid)

        # state 1 (Input: T1 dan X1) before expander
        T1re = T0re - 1
        X1re = 1
        P1re = CP.PropsSI('P', 'T', T1re, 'Q', X1re, self.fluid)
        H1re = CP.PropsSI('H', 'T', T1re, 'Q', X1re, self.fluid)
        S1re = CP.PropsSI('S', 'T', T1re, 'Q', X1re, self.fluid)

        # state 1sup 
        T1sup_re = T_high - 1
        P1sup_re = P1re
        H1sup_re = CP.PropsSI('H', 'T', T1sup_re, 'P', P1sup_re, self.fluid)
        S1sup_re = CP.PropsSI('S', 'T', T1sup_re, 'P', P1sup_re, self.fluid)
        X1sup_re = CP.PhaseSI('Q', 'T', T1sup_re, 'P', P1sup_re, self.fluid)

        # state 3 (Input: T3 dan X3) after condenser
        T3re = T3-2
        X3re = 0
        P3re = CP.PropsSI('P', 'T', T3re, 'Q', X3re, self.fluid)
        H3re = CP.PropsSI('H', 'T', T3re, 'Q', X3re, self.fluid)
        S3re = CP.PropsSI('S', 'T', T3re, 'Q', X3re, self.fluid)

        # state 2 (Input: p2 dan s2) after expander
        P2re    = P3re
        S2re_is = S1re
        H2re_is = CP.PropsSI('H', 'S', S2re_is, 'P', P2re, self.fluid)
        H2re    = H1re - self.eta_exp * (H1re - H2re_is)
        S2re    = CP.PropsSI('S', 'H', H2re, 'P', P2re, self.fluid)
        T2re    = CP.PropsSI('T', 'H', H2re, 'P', P2re, self.fluid)
        X2re = CP.PhaseSI('Q', 'H', H2re, 'P', P2re, self.fluid)

        # state 23 (Input: X23 dan T2) after desuperheater
        X23re = 1
        T23re = T23 - 1
        P23re = CP.PropsSI('P', 'T', T23re, 'Q', X23re, self.fluid)
        H23re = CP.PropsSI('H', 'T', T23re, 'Q', X23re, self.fluid)
        S23re = CP.PropsSI('S', 'T', T23re, 'Q', X23re, self.fluid)

        # state 4 (Input: s4 dan p4) after pump
        S4re_is = S3re
        P4re    = P0re
        H4re_is = CP.PropsSI('H', 'S', S4re_is, 'P', P4re, self.fluid)
        H4re    = H3re + (H4re_is - H3re)/self.eta_pmp
        S4re    = CP.PropsSI('S', 'H', H4re, 'P', P4re, self.fluid)
        T4re    = CP.PropsSI('T', 'H', H4re, 'P', P4re, self.fluid)
        X4re = CP.PhaseSI('Q', 'H', H4re, 'P', P4re, self.fluid)

        self.H_is_list = [H0, H1, H1sup, H2, H23, H3, H4]
        self.s_is_list = [S0, S1, S1sup, S2, S23, S3, S4]
        self.p_is_list = [P0, P1, P1sup, P2, P23, P3, P4]
        self.T_is_list = [T0, T1, T1sup, T2, T23, T3, T4]
        self.X_is_list = [X0, X1, X1sup, X2, X23, X3, X4]
        
        self.H_re_list = [H0re, H1re, H1sup_re, H2re, H23re, H3re, H4re]
        self.s_re_list = [S0re, S1re, S1sup_re, S2re, S23re, S3re, S4re]
        self.p_re_list = [P0re, P1re, P1sup_re, P2re, P23re, P3re, P4re]
        self.T_re_list = [T0re, T1re, T1sup_re, T2re, T23re, T3re, T4re]
        self.X_re_list = [X0re, X1re, X1sup_re, X2re, X23re, X3re, X4re]

        p_hs_out = 0.97 * self.p_hs_in
        p_hs_mid1 = 0.98 * self.p_hs_in
        h_hs_mid1 = CP.PropsSI('H', 'P', p_hs_mid1, 'T', self.T_hs_mid1, self.hs_fluid)
        h_hs_in = CP.PropsSI('H', 'T', self.T_hs_in, 'P', self.p_hs_in, self.hs_fluid)
        hs_mass_flow = (self.wf_mass_flow * (H1sup_re - H0re)) / (h_hs_in - h_hs_mid1)

        p_hs_mid2 = 0.99 * self.p_hs_in
        h_hs_mid2 = h_hs_in - ((self.wf_mass_flow * (H1sup_re - H1sup_re)) / hs_mass_flow)
        T_hs_mid2 = CP.PropsSI('T', 'P', p_hs_mid2, 'H', h_hs_mid2, self.hs_fluid)

        h_hs_out = h_hs_mid1 - ((self.wf_mass_flow * (H0re - H4re)) / hs_mass_flow)
        T_hs_out = CP.PropsSI('T', 'P', p_hs_out, 'H', h_hs_out, self.hs_fluid)

        p_cs_mid1 = 0.99 * self.p_cs_in
        h_cs_mid1 = CP.PropsSI('H', 'P', p_cs_mid1, 'T', self.T_cs_mid1, self.cs_fluid)
        h_cs_in = CP.PropsSI('H', 'T', self.T_cs_in, 'P', self.p_cs_in, self.cs_fluid)
        
        cs_mass_flow = (self.wf_mass_flow * (H23re - H3re)) / (h_cs_mid1 - h_cs_in)
        
        p_cs_out = 0.98 * self.p_cs_in
        h_cs_out = (self.wf_mass_flow * (H23re - H3re) / cs_mass_flow) + h_cs_in
        T_cs_out = CP.PropsSI('T', 'P', p_cs_out, 'H', h_cs_out, self.cs_fluid)

        q_demand_hs = self.wf_mass_flow * (H1sup_re - H4re)


        H_hs = [h_hs_in, h_hs_mid1, h_hs_mid2, h_hs_out]
        H_cs = [h_cs_in, h_cs_mid1, h_cs_out]
        # Simpan ke atribut class
        self.ideal_states = {"H": self.H_is_list, "T": self.T_is_list, "P": self.p_is_list, "S": self.s_is_list, "X": self.X_is_list}
        self.real_states = {"H": self.H_re_list, "T": self.T_re_list, "P": self.p_re_list, "S": self.s_re_list, "X": self.X_re_list}
        self.hs_temps = {
            "T_hs_in": self.T_hs_in, 
            "T_hs_mid1": self.T_hs_mid1, "T_hs_out": T_hs_out
        }
        self.cs_temps = {
            "T_cs_in": self.T_cs_in, "T_cs_mid1": self.T_cs_mid1, "T_cs_out": T_cs_out
        }
        self.external_h = {"H_hs": H_hs, "H_cs": H_cs}
        self.sim_results = {
            "Q_demand_hs": q_demand_hs,
            "hs_mass_flow": hs_mass_flow,
            "cs_mass_flow": cs_mass_flow
        }
    def print_delta_enthalpy_real(self):
        """
        Mencetak tabel selisih entalpi antar komponen (Real Cycle).
        Satuan: kJ/kg
        """
        # Cek apakah simulasi sudah dijalankan
        if not self.real_states:
            print("Error: Jalankan .run_simulation() terlebih dahulu.")
            return

        # Ambil list H_r dari hasil simulasi

        H = self.real_states["H"]
        
        # Mapping variabel supaya rumus mudah dibaca (satuan masih J/kg)
        h0_r      = H[0]
        h1_r      = H[1]
        h1sup_r   = H[2]
        h2_r      = H[3]
        h23_r  = H[4]
        h3_r      = H[5]
        h4_r      = H[6]


        # Kalkulasi Delta H (Dikonversi ke kJ/kg dengan membagi 1000)
        val_lh      = (h0_r - h4_r) / 1000
        val_eva     = (h1_r - h0_r) / 1000
        val_exp     = (h1_r - h2_r) / 1000
        val_cds     = (h2_r - h3_r) / 1000 # Total rejection dari post-recuperator
        val_pmp     = (h4_r - h3_r) / 1000

        # Siapkan data untuk tabulate
        table_data = [
            [1, "LH (Liquid Heater)", val_lh],
            [2, "EVA (Evaporator)",   val_eva],
            [3, "EXP (Expander)",     val_exp],
            [4, "CDS (Condenser)",    val_cds],
            [5, "PMP (Pump)",         val_pmp],
        ]

        headers = ["Nomor", "Nama Komponen", "Nilai (kJ/kg)"]
        
        print("\n--- Analisis Entalpi Komponen (Real Cycle) ---")
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=".4f"))
    def print_mass_flow(self):
        """
        Mencetak tabel mass flow rate untuk fluida kerja,
        fluida panas (heat source), dan fluida dingin (cooling source).
        Satuan: kg/s
        """
        # Cek apakah simulasi sudah dijalankan
        if not self.sim_results:
            print("Error: Jalankan .run_simulation() terlebih dahulu.")
            return

        # Ambil data dari atribut 'self'
        # 1. Fluida Kerja (Siklus)
        m_cycle = self.wf_mass_flow
        fluid_cycle = self.fluid

        # 2. Fluida Panas (Heat Source)
        m_hs = self.sim_results.get('hs_mass_flow')
        fluid_hs = self.hs_fluid

        # 3. Fluida Dingin (Cooling Source)
        m_cs = self.sim_results.get('cs_mass_flow')
        fluid_cs = self.cs_fluid
        
        # Siapkan data untuk tabulate
        table_data = [
            [1, "Fluida Kerja (Cycle)",   fluid_cycle, m_cycle],
            [2, "Heat Source (S. Panas)", fluid_hs,    m_hs],
            [3, "Cooling Source (S. Dingin)", fluid_cs,  m_cs],
        ]

        headers = ["Nomor", "Deskripsi", "Jenis Fluida", "Nilai (kg/s)"]
        
        print("\n--- Analisis Mass Flow Rate ---")
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=".4f"))
    def print_energy_transfer(self):
            """
            Mencetak tabel laju transfer energi untuk setiap komponen
            berdasarkan mass flow fluida kerja (wf_mass_flow).
            Satuan: kW
            """
            # Cek apakah simulasi sudah dijalankan
            if not self.real_states:
                print("Error: Jalankan .run_simulation() terlebih dahulu.")
                return

            # Ambil list H_r (J/kg) dan mass flow (kg/s)
            H = self.real_states["H"]
            m_dot = self.wf_mass_flow

            # Mapping variabel supaya rumus mudah dibaca (satuan masih J/kg)
            h0_r      = H[0]
            h1_r      = H[1]
            h1sup_r   = H[2]
            h2_r      = H[3]
            h23_r  = H[4]
            h3_r      = H[5]
            h4_r      = H[6]

            # 1. Hitung spesifik delta h (kJ/kg)
            dh_lh      = (h0_r - h4_r) / 1000
            dh_eva     = (h1_r - h0_r) / 1000
            dh_sup     = (h1sup_r - h1_r) / 1000
            dh_exp     = (h1sup_r - h2_r) / 1000
            dh_cds     = (h3_r - h2_r) / 1000 # (h3_r - h23_r)
            dh_pmp     = (h3_r - h4_r) / 1000
            


            # 2. Hitung Laju Energi (kW) = (kJ/kg) * (kg/s)
            E_lh   = dh_lh * m_dot
            E_eva  = dh_eva * m_dot
            E_sup  = dh_sup * m_dot
            E_exp  = dh_exp * m_dot
            E_cds  = dh_cds * m_dot
            E_pmp  = dh_pmp * m_dot


            # Siapkan data untuk tabulate (TANPA RECUPERATOR)
            table_data = [
                [1, "LH (Liquid Heater)", E_lh],
                [2, "EVA (Evaporator)",   E_eva],
                [3, "SUP (Superheater)",  E_sup],
                [4, "EXP (Expander)",     E_exp],
                [5, "CDS (Condenser)",    E_cds],
                [6, "PMP (Pump)",         E_pmp],
            ]

            headers = ["Nomor", "Komponen", "Energi Transfer (kW)"]
            
            print("\n--- Analisis Laju Transfer Energi (Siklus) ---")
            print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=".4f"))
            
            # --- Catatan dimodifikasi di sini ---
            print(f"Catatan: (+) = Energi yang dikerjakan oleh sistem (Panas/Kerja OUT)\n"
                f"         (-) = Energi yang dikerjakan pada sistem (Panas/Kerja IN)")
    def print_hs_prop(self):
        """
        Mencetak tabel properti untuk Heat Source (Fluida Panas).
        Satuan: degC, kJ/kg
        """
        # Cek apakah simulasi sudah dijalankan
        if not self.hs_temps or not self.external_h or not self.sim_results:
            print("Error: Jalankan .run_simulation() terlebih dahulu.")
            return

        # Ambil data dari atribut 'self'
        try:
            # Ambil Temperatur (dalam K)
            T_in = self.hs_temps["T_hs_in"]
            T_mid1 = self.hs_temps["T_hs_mid1"]
            T_out = self.hs_temps["T_hs_out"]
            
            # Ambil Entalpi (dalam J/kg)
            H_list = self.external_h["H_hs"] # [h_in, h_mid2, h_mid1, h_out]
            h_in = H_list[0]
            h_mid1 = H_list[1]
            h_out = H_list[2]
            
            # Ambil mass flow (kg/s)
            m_dot_hs = self.sim_results["hs_mass_flow"]
            
        except (KeyError, IndexError) as e:
            print(f"Error: Data simulasi HS tidak lengkap ({e}).")
            return

        # 1. Konversi Unit
        # T (K -> degC)
        T_in_C = T_in - 273.15
        T_mid1_C = T_mid1 - 273.15
        T_out_C = T_out - 273.15
        
        # H (J/kg -> kJ/kg)
        h_in_kJ = h_in / 1000
        h_mid1_kJ = h_mid1 / 1000
        h_out_kJ = h_out / 1000
        
        # 2. Siapkan data tabel
        table_data = [
            [1, "HS In",      T_in_C,   h_in_kJ],
            [2, "HS Mid 1",   T_mid1_C, h_mid1_kJ],
            [3, "HS Out",     T_out_C,  h_out_kJ],
        ]
        
        headers = ["Nomor", "Index Heat Source", "T (°C)", "H (kJ/kg)"]

        # 3. Hitung Q_in verifikasi
        # Q (kW) = m_dot (kg/s) * delta_h (kJ/kg)
        Q_in_hs = m_dot_hs * (h_in_kJ - h_out_kJ)
        
        # 4. Print tabel dan catatan
        print("\n--- Properti Heat Source (Fluida Panas) ---")
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=".2f"))
        
        print("Catatan:")
        print(f"         1. Mass Flow Heat Source (m_dot_hs): {m_dot_hs:.4f} kg/s")
        print(f"         2. Verifikasi Q_in (sisi HS): {Q_in_hs:.4f} kW")
        print(f"         3. Tekanan Heat Source diasumsikan konstan pada {self.p_hs_in/100000:.2f} bar")
    def print_cs_prop(self):
        """
        Mencetak tabel properti untuk Cooling Source (Fluida Dingin).
        Satuan: degC, kJ/kg
        """
        # Cek apakah simulasi sudah dijalankan
        if not self.cs_temps or not self.external_h or not self.sim_results:
            print("Error: Jalankan .run_simulation() terlebih dahulu.")
            return

        # Ambil data dari atribut 'self'
        try:
            # Ambil Temperatur (dalam K)
            T_in = self.cs_temps["T_cs_in"]
            T_mid1 = self.cs_temps["T_cs_mid1"]
            T_out = self.cs_temps["T_cs_out"]
            
            # Ambil Entalpi (dalam J/kg)
            # Urutan di 'run_simulation': [h_cs_in, h_cs_mid1, h_cs_out]
            H_list = self.external_h["H_cs"] 
            h_in = H_list[0]
            h_mid1 = H_list[1]
            h_out = H_list[2]
            
            # Ambil mass flow (kg/s)
            m_dot_cs = self.sim_results["cs_mass_flow"]
            
        except (KeyError, IndexError) as e:
            print(f"Error: Data simulasi CS tidak lengkap ({e}).")
            return

        # 1. Konversi Unit
        # T (K -> degC)
        T_in_C = T_in - 273.15
        T_mid1_C = T_mid1 - 273.15
        T_out_C = T_out - 273.15
        
        # H (J/kg -> kJ/kg)
        h_in_kJ = h_in / 1000
        h_mid1_kJ = h_mid1 / 1000
        h_out_kJ = h_out / 1000
        
        # 2. Siapkan data tabel
        table_data = [
            [1, "CS In",      T_in_C,   h_in_kJ],
            [2, "CS Mid 1",   T_mid1_C, h_mid1_kJ],
            [3, "CS Out",     T_out_C,  h_out_kJ],
        ]
        
        headers = ["Nomor", "Index Cooling Source", "T (°C)", "H (kJ/kg)"]

        # 3. Hitung Q_out verifikasi
        # Q (kW) = m_dot (kg/s) * delta_h (kJ/kg)
        # (Energi yang diserap oleh fluida pendingin)
        Q_out_cs = m_dot_cs * (h_out_kJ - h_in_kJ)
        
        # 4. Print tabel dan catatan
        print("\n--- Properti Cooling Source (Fluida Dingin) ---")
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=".2f"))
        
        print("Catatan:")
        print(f"         1. Mass Flow Cooling Source (m_dot_cs): {m_dot_cs:.4f} kg/s")
        print(f"         2. Verifikasi Q_out (sisi CS): {Q_out_cs:.4f} kW")
        print(f"         3. Tekanan Cooling Source diasumsikan konstan pada {self.p_cs_in/100000:.2f} bar")
    def print_state_information(self):
        """
        Mencetak tabel informasi state point (real cycle)
        dengan unit yang sudah dikonversi (degC, bar, kJ/kg).
        """
        # Cek apakah simulasi sudah dijalankan
        if not self.real_states:
            print("Error: Jalankan .run_simulation() terlebih dahulu.")
            return

        # Ambil data list dari self.real_states
        # Pastikan run_simulation sudah mengisi "X"
        try:
            T_list = self.real_states["T"]
            P_list = self.real_states["P"]
            S_list = self.real_states["S"]
            H_list = self.real_states["H"]
            X_list = self.real_states["X"]
        except KeyError as e:
            print(f"Error: Data '{e.args[0]}' tidak ditemukan di self.real_states.")
            print("Pastikan run_simulation sudah menyimpan 'X' di self.real_states.")
            return

        # Label state point sesuai urutan di list
        state_labels = [
            "0 (Outlet LH)", 
            "1 (Outlet EVA)", 
            "1sup (Outlet SUP)",
            "2 (Outlet EXP)", 
            "23 (Desuperheater)", 
            "3 (Outlet CDS)", 
            "4 (Outlet PMP)"
        ]
        
        table_data = []
        headers = ["State Index", "T (°C)", "P (bar)", "S (kJ/kg.K)", "H (kJ/kg)", "X (Quality)"]

        # Loop untuk setiap state, konversi unit, dan format data
        for i in range(len(state_labels)):
            label = state_labels[i]
            
            # Cek jika state (seperti 23rec3) tidak dihitung (None)
            if T_list[i] is None:
                row = [label, "---", "---", "---", "---", "---"]
            else:
                # Lakukan konversi unit
                T_C = T_list[i] - 273.15
                P_bar = P_list[i] / 100000  # Pa ke bar
                S_kJ = S_list[i] / 1000     # J/kg.K ke kJ/kg.K
                H_kJ = H_list[i] / 1000     # J/kg ke kJ/kg
                
                # Format X (Quality)
                X_raw = X_list[i]
                if isinstance(X_raw, (int, float)):
                    # Jika X adalah angka (0, 1, atau nilai quality 0-1)
                    X_val = f"{X_raw:.4f}"
                elif X_raw is None:
                    # Jika X adalah None
                    X_val = "---"
                else:
                    # Jika X adalah string (misal 'gas', 'liquid', 'supercritical')
                    X_val = str(X_raw) 
                
                row = [label, T_C, P_bar, S_kJ, H_kJ, X_val]
            
            table_data.append(row)

        print("\n--- Informasi State Point (Real Cycle) ---")
        
        # Tentukan format angka untuk setiap kolom
        # [Index, T, P, S, H, X]
        col_formats = [None, ".2f", ".3f", ".4f", ".2f", None]
        
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=col_formats))
    def calculate_performance(self, use_ideal_states=False):
        """
        Menghitung performa siklus (efisiensi, W_net)
        berdasarkan hasil simulasi.
        
        Args:
            use_ideal_states (bool): Jika True, hitung performa ideal.
                                     Defaultnya False (hitung real).
        """
        if not self.real_states:
            print("Error: Jalankan .run_simulation() terlebih dahulu.")
            return None

        if use_ideal_states:
            H_list = self.ideal_states["H"]
        else:
            H_list = self.real_states["H"]
            
        # Indeks berdasarkan list H_r/H_is:
        # 2: H1_sup (SUP out)
        # 3: H2 (EXP out)
        # 6: H3 (CDS out)
        # 7: H4 (PMP out)
        # 8: H41rec (REC out to LH)

        W_dot_exp_spec = (H_list[2] - H_list[3]) / 1000  # kJ/kg
        W_dot_pmp_spec = (H_list[-1] - H_list[-2]) / 1000  # kJ/kg
        W_dot_net_spec = W_dot_exp_spec - W_dot_pmp_spec

        Q_dot_in_spec = (H_list[2] - H_list[-1]) / 1000 # Q_in = H_sup_out - H_rec_out
        # Hindari pembagian dengan nol jika Q_dot_in_spec adalah 0
        if Q_dot_in_spec == 0:
            eta_thermal = 0
        else:
            eta_thermal = W_dot_net_spec / Q_dot_in_spec

        # Kalkulasi 2nd law efficiency
        factor = 1 - (self.reference_temperature / self.T_hs_in)
        second_law_efficiency = eta_thermal / factor if factor != 0 else 0
        # Simpan hasil performa ke 'self'
        self.performance = {
            "eta_thermal": eta_thermal,
            "W_dot_net_kW": W_dot_net_spec * self.wf_mass_flow,
            "Q_dot_in_kW": Q_dot_in_spec * self.wf_mass_flow,
            "W_dot_exp_kW": W_dot_exp_spec * self.wf_mass_flow,
            "W_dot_pmp_kW": W_dot_pmp_spec * self.wf_mass_flow,
            "second_law_efficiency": second_law_efficiency
        }
        
        print(f"Performa (Real) berhasil dikalkulasi. Efisiensi Termal: {eta_thermal:.2%}")
        return self.performance

class ORCSuperRec:
    """
    Membungkus simulasi ORC Superheated Recuperated dalam sebuah Class.

    Class ini menyimpan semua parameter input, menjalankan simulasi,
    dan menyimpan semua state (ideal & real) serta hasil performa
    sebagai atribut.

    Alur Penggunaan:
    1. Buat instance dari class ini dengan semua parameter input.
    2. Panggil method .run_simulation() untuk melakukan perhitungan.
    3. Panggil method .calculate_performance() untuk menghitung efisiensi.
    4. Akses hasil simulasi dari atribut (misal: self.real_states, self.performance).
    """

    def __init__(self, wf_cycle_fluid, hs_fluid,  T_hs_in, T_cs_in,
                 T_pinch_hs_in, T_pinch_hs_mid1, T_estimation_hs,
                 T_estimation_cs, T_pinch_cs_mid1, eta_exp, eta_pmp,
                 T_pinch_rec, p_hs_in, wf_mass_flow, cs_fluid='Air', p_cs_in=200000):
        
        # --- 1. Simpan Semua Parameter Input ---
        self.fluid = wf_cycle_fluid
        self.hs_fluid = hs_fluid
        self.cs_fluid = cs_fluid
        self.T_hs_in = T_hs_in
        self.T_cs_in = T_cs_in
        self.T_pinch_hs_in = T_pinch_hs_in
        self.T_pinch_hs_mid1 = T_pinch_hs_mid1
        self.T_estimation_hs = T_estimation_hs
        self.T_estimation_cs = T_estimation_cs
        self.T_pinch_cs_mid1 = T_pinch_cs_mid1
        self.eta_exp = eta_exp
        self.eta_pmp = eta_pmp
        self.T_pinch_rec = T_pinch_rec
        self.p_hs_in = p_hs_in
        self.p_cs_in = p_cs_in
        self.wf_mass_flow = wf_mass_flow
        
        # --- 2. Siapkan Atribut untuk Menyimpan Hasil ---
        self.ideal_states = {}
        self.real_states = {}
        self.hs_temps = {}
        self.cs_temps = {}
        self.external_h = {}
        self.sim_results = {}
        self.performance = {}
    def run_simulation(self):
            """
            Menjalankan perhitungan termodinamika siklus dengan Error Handling.
            Menangkap error termofisika (T > T_crit) dan error matematika.
            """


            print(f"--- Memulai Simulasi untuk Fluida: {self.fluid} ---")

            try:
                # Menggunakan variabel lokal untuk perhitungan
                T_hs_mid1 = self.T_hs_in - self.T_estimation_hs
                T_high = self.T_hs_in - self.T_pinch_hs_in
                T_cs_mid1 = self.T_estimation_cs + self.T_cs_in
                T_low = T_cs_mid1 + self.T_pinch_cs_mid1

                # ==========================================================
                # Ideal Case
                # ==========================================================
                # State 0
                T0 = T_hs_mid1 - self.T_pinch_hs_mid1
                # [ERROR CHECK] Cek apakah T0 valid sebelum panggil CoolProp
                # (Opsional, tapi CoolProp biasanya akan throw error sendiri)
                
                P0 = CP.PropsSI('P', 'T', T0, 'Q', 0, self.fluid)
                H0 = CP.PropsSI('H', 'T', T0, 'Q', 0, self.fluid)
                S0 = CP.PropsSI('S', 'T', T0, 'Q', 0, self.fluid)
                X0 = 0

                # State 1
                T1 = T0
                P1 = CP.PropsSI('P', 'T', T1, 'Q', 1, self.fluid)
                H1 = CP.PropsSI('H', 'T', T1, 'Q', 1, self.fluid)
                S1 = CP.PropsSI('S', 'T', T1, 'Q', 1, self.fluid)
                X1 = 1

                # State 1sup
                T1_sup = T_high
                P1_sup = P1
                
                # [RAWAN ERROR] T1_sup > T_crit sering terjadi di sini jika input T_hs terlalu tinggi
                H1_sup = CP.PropsSI('H', 'T', T1_sup, 'P', P1_sup, self.fluid)
                S1_sup = CP.PropsSI('S', 'T', T1_sup, 'P', P1_sup, self.fluid)
                X1_sup = CP.PhaseSI('T', T1_sup, 'P', P1_sup, self.fluid)

                # State 3
                T3 = T_low
                P3 = CP.PropsSI('P', 'T', T3, 'Q', 0, self.fluid)
                H3 = CP.PropsSI('H', 'T', T3, 'Q', 0, self.fluid)
                S3 = CP.PropsSI('S', 'T', T3, 'Q', 0, self.fluid)
                X3 = 0

                # State 2
                S2 = S1_sup
                P2 = P3
                H2 = CP.PropsSI('H', 'P', P2, 'S', S2, self.fluid)
                T2 = CP.PropsSI('T', 'P', P2, 'S', S2, self.fluid)
                X2 = CP.PhaseSI('P', P2, 'S', S2, self.fluid)

                # State 4
                P4 = P0
                S4 = S3
                H4 = CP.PropsSI('H', 'P', P4, 'S', S4, self.fluid)
                T4 = CP.PropsSI('T', 'P', P4, 'S', S4, self.fluid)
                X4 = CP.PhaseSI('P', P4, 'S', S4, self.fluid)
                
                # State 23rec
                P23rec = P2
                T23rec = T4 + self.T_pinch_rec
                H23rec = CP.PropsSI('H', 'T', T23rec, 'P', P23rec, self.fluid)
                S23rec = CP.PropsSI('S', 'T', T23rec, 'P', P23rec, self.fluid)
                X23rec = CP.PropsSI('Q', 'T', T23rec, 'P', P23rec, self.fluid)

                # State 23rec3 (Desuperheater Check)
                X23rec3, T23rec3, P23rec3, H23rec3, S23rec3 = None, None, None, None, None
                T_sat = CP.PropsSI('T', 'P', P23rec, 'Q', 0, self.fluid)
                if T23rec > T_sat:
                    X23rec3 = 1
                    T23rec3 = T_low
                    P23rec3 = CP.PropsSI('P', 'T', T23rec3, 'Q', X23rec3, self.fluid)
                    H23rec3 = CP.PropsSI('H', 'T', T23rec3, 'Q', X23rec3, self.fluid)
                    S23rec3 = CP.PropsSI('S', 'T', T23rec3, 'Q', X23rec3, self.fluid)

                # State 41rec
                P41rec = P0
                H41rec = (H2 + H4) - H23rec
                S41rec = CP.PropsSI('S', 'P', P41rec, 'H', H41rec, self.fluid)
                T41rec = CP.PropsSI('T', 'P', P41rec, 'H', H41rec, self.fluid)
                X41rec = CP.PhaseSI('P', P41rec, 'H', H41rec, self.fluid)

                # ==========================================================
                # Real Case
                # ==========================================================
                # State 0 Real
                T0_r = T_hs_mid1 - self.T_pinch_hs_mid1 - 1
                X0_r = 0
                P0_r = CP.PropsSI('P', 'T', T0_r, 'Q', X0_r, self.fluid)
                H0_r = CP.PropsSI('H', 'T', T0_r, 'Q', X0_r, self.fluid)
                S0_r = CP.PropsSI('S', 'T', T0_r, 'Q', X0_r, self.fluid)

                # State 1 Real
                T1_r = T0_r - 1
                X1_r = 1
                P1_r = CP.PropsSI('P', 'T', T1_r, 'Q', X1_r, self.fluid)
                H1_r = CP.PropsSI('H', 'T', T1_r, 'Q', X1_r, self.fluid)
                S1_r = CP.PropsSI('S', 'T', T1_r, 'Q', X1_r, self.fluid)

                # State 3 Real
                T3_r = T_low - 2
                X3_r = 0
                P3_r = CP.PropsSI('P', 'T', T3_r, 'Q', X3_r, self.fluid)
                H3_r = CP.PropsSI('H', 'T', T3_r, 'Q', X3_r, self.fluid)
                S3_r = CP.PropsSI('S', 'T', T3_r, 'Q', X3_r, self.fluid)

                # State 1sup Real
                T1_sup_r = T_high - 1
                P1_sup_r = P1_r
                H1_sup_r = CP.PropsSI('H', 'T', T1_sup_r, 'P', P1_sup_r, self.fluid)
                S1_sup_r = CP.PropsSI('S', 'T', T1_sup_r, 'P', P1_sup_r, self.fluid)
                X1_sup_r = CP.PhaseSI('T', T1_sup_r, 'P', P1_sup_r, self.fluid)

                # State 2 Real
                S2is_r = S1_sup_r
                P2_r = P3_r
                H2is_r = CP.PropsSI('H', 'P', P2_r, 'S', S2is_r, self.fluid)
                H2_r = H1_sup_r - self.eta_exp * (H1_sup_r - H2is_r)
                T2_r = CP.PropsSI('T', 'P', P2_r, 'H', H2_r, self.fluid)
                S2_r = CP.PropsSI('S', 'P', P2_r, 'H', H2_r, self.fluid)
                X2_r = CP.PhaseSI('P', P2_r, 'H', H2_r, self.fluid)

                # State 4 Real
                P4_r = P0_r
                S4s_r = S3_r
                H4s_r = CP.PropsSI('H', 'P', P4_r, 'S', S4s_r, self.fluid)
                H4_r = H3_r + (1 / self.eta_pmp) * (H4s_r - H3_r)
                T4_r = CP.PropsSI('T', 'P', P4_r, 'H', H4_r, self.fluid)
                S4_r = CP.PropsSI('S', 'P', P4_r, 'H', H4_r, self.fluid)
                X4_r = CP.PhaseSI('P', P4_r, 'H', H4_r, self.fluid)

                # State 23rec Real
                P23rec_r = P2_r
                T23rec_r = T4_r + self.T_pinch_rec
                H23rec_r = CP.PropsSI('H', 'T', T23rec_r, 'P', P23rec_r, self.fluid)
                S23rec_r = CP.PropsSI('S', 'T', T23rec_r, 'P', P23rec_r, self.fluid)
                X23rec_r = CP.PhaseSI('P', P23rec_r, 'H', H23rec_r, self.fluid)

                # State 23rec3 Real (Desuperheater Check Real)
                X23rec3_r, T23rec3_r, P23rec3_r, H23rec3_r, S23rec3_r = None, None, None, None, None
                T_sat_r = CP.PropsSI('T', 'P', P23rec_r, 'Q', 0, self.fluid)
                if T23rec_r > T_sat_r:
                    X23rec3_r = 1
                    T23rec3_r = T_low - 1
                    P23rec3_r = CP.PropsSI('P', 'T', T23rec3_r, 'Q', X23rec3_r, self.fluid)
                    H23rec3_r = CP.PropsSI('H', 'T', T23rec3_r, 'Q', X23rec3_r, self.fluid)
                    S23rec3_r = CP.PropsSI('S', 'T', T23rec3_r, 'Q', X23rec3_r, self.fluid)

                # State 41rec Real
                P41rec_r = P0_r
                H41rec_r = (H2_r + H4_r) - H23rec_r
                S41rec_r = CP.PropsSI('S', 'P', P41rec_r, 'H', H41rec_r, self.fluid)
                T41rec_r = CP.PropsSI('T', 'P', P41rec_r, 'H', H41rec_r, self.fluid)
                X41rec_r = CP.PhaseSI('P', P41rec_r, 'H', H41rec_r, self.fluid)

                # ==========================================================
                # External Fluid Calculations
                # ==========================================================
                p_hs_out = 0.97 * self.p_hs_in
                p_hs_mid1 = 0.98 * self.p_hs_in
                h_hs_mid1 = CP.PropsSI('H', 'P', p_hs_mid1, 'T', T_hs_mid1, self.hs_fluid)
                h_hs_in = CP.PropsSI('H', 'T', self.T_hs_in, 'P', self.p_hs_in, self.hs_fluid)
                
                # [RAWAN ERROR] Division by Zero jika h_hs_in == h_hs_mid1
                hs_mass_flow = (self.wf_mass_flow * (H1_sup_r - H0_r)) / (h_hs_in - h_hs_mid1)

                p_hs_mid2 = 0.99 * self.p_hs_in
                h_hs_mid2 = h_hs_in - ((self.wf_mass_flow * (H1_sup_r - H1_r)) / hs_mass_flow)
                T_hs_mid2 = CP.PropsSI('T', 'P', p_hs_mid2, 'H', h_hs_mid2, self.hs_fluid)

                h_hs_out = h_hs_mid1 - ((self.wf_mass_flow * (H0_r - H41rec_r)) / hs_mass_flow)
                T_hs_out = CP.PropsSI('T', 'P', p_hs_out, 'H', h_hs_out, self.hs_fluid)

                p_cs_mid1 = 0.99 * self.p_cs_in
                h_cs_mid1 = CP.PropsSI('H', 'P', p_cs_mid1, 'T', T_cs_mid1, self.cs_fluid)
                h_cs_in = CP.PropsSI('H', 'T', self.T_cs_in, 'P', self.p_cs_in, self.cs_fluid)
                
                H_cds_in = H23rec3_r if H23rec3_r is not None else H23rec_r
                cs_mass_flow = (self.wf_mass_flow * (H_cds_in - H3_r)) / (h_cs_mid1 - h_cs_in)
                
                p_cs_out = 0.98 * self.p_cs_in
                h_cs_out = (self.wf_mass_flow * (H_cds_in - H3_r) / cs_mass_flow) + h_cs_in
                T_cs_out = CP.PropsSI('T', 'P', p_cs_out, 'H', h_cs_out, self.cs_fluid)

                q_demand_hs = self.wf_mass_flow * (H1_sup_r - H41rec_r)

                # ==========================================================
                # Kumpulkan dan Simpan Hasil ke 'self'
                # ==========================================================
                
                H_is = [H0, H1, H1_sup, H2, H23rec, H23rec3, H3, H4, H41rec]
                T_is = [T0, T1, T1_sup, T2, T23rec, T23rec3, T3, T4, T41rec]
                P_is = [P0, P1, P1_sup, P2, P23rec, P23rec3, P3, P4, P41rec]
                S_is = [S0, S1, S1_sup, S2, S23rec, S23rec3, S3, S4, S41rec]
                X_is = [X0, X1, X1_sup, X2, X23rec, X23rec3, X3, X4, X41rec]

                H_r = [H0_r, H1_r, H1_sup_r, H2_r, H23rec_r, H23rec3_r, H3_r, H4_r, H41rec_r]
                T_r = [T0_r, T1_r, T1_sup_r, T2_r, T23rec_r, T23rec3_r, T3_r, T4_r, T41rec_r]
                P_r = [P0_r, P1_r, P1_sup_r, P2_r, P23rec_r, P23rec3_r, P3_r, P4_r, P41rec_r]
                S_r = [S0_r, S1_r, S1_sup_r, S2_r, S23rec_r, S23rec3_r, S3_r, S4_r, S41rec_r]
                X_r = [X0_r, X1_r, X1_sup_r, X2_r, X23rec_r, X23rec3_r, X3_r, X4_r, X41rec_r]

                H_hs = [h_hs_in, h_hs_mid2, h_hs_mid1, h_hs_out]
                H_cs = [h_cs_in, h_cs_mid1, h_cs_out]

                self.ideal_states = {"H": H_is, "T": T_is, "P": P_is, "S": S_is, "X": X_is}
                self.real_states = {"H": H_r, "T": T_r, "P": P_r, "S": S_r, "X": X_r}
                self.hs_temps = {
                    "T_hs_in": self.T_hs_in, "T_hs_mid2": T_hs_mid2,
                    "T_hs_mid1": T_hs_mid1, "T_hs_out": T_hs_out
                }
                self.cs_temps = {
                    "T_cs_in": self.T_cs_in, "T_cs_mid1": T_cs_mid1, "T_cs_out": T_cs_out
                }
                self.external_h = {"H_hs": H_hs, "H_cs": H_cs}
                self.sim_results = {
                    "Q_demand_hs": q_demand_hs,
                    "hs_mass_flow": hs_mass_flow,
                    "cs_mass_flow": cs_mass_flow
                }
                
                print(">> Simulasi Selesai Berhasil. Hasil disimpan dalam objek.")

            # Catch Error Termofisika (CoolProp Errors)
            except ValueError as ve:
                print(f"\n[!] THERMOPHYSICAL ERROR DETECTED (CoolProp Failure)")
                print(f"    Detail: {ve}")
                
                # Cek pesan error spesifik untuk T > T_crit
                error_msg = str(ve).lower()
                if "temperature" in error_msg and ("critical" in error_msg or "max" in error_msg):
                    print("    Analisis: Temperatur input mungkin melebihi Temperatur Kritis (T_crit) fluida.")
                    print("    Saran: Cek T_hs_in atau T_superheat kamu.")
                
                # Print traceback agar tahu baris mana yang error
                print("    Lokasi Error:")
                traceback.print_exc(limit=1)
                
                # Kosongkan hasil agar tidak ada data sampah
                self.real_states = {}

            # Catch Error Matematika (Pembagian Nol)
            except ZeroDivisionError:
                print(f"\n[!] MATHEMATICAL ERROR: Division by Zero")
                print("    Analisis: Kemungkinan Delta Enthalpy = 0 saat menghitung Mass Flow.")
                print("    Saran: Cek apakah T_in dan T_out pada Heat Source identik.")
                self.real_states = {}

            # Catch Error Lainnya
            except Exception as e:
                print(f"\n[!] UNKNOWN ERROR: {e}")
                traceback.print_exc()
                self.real_states = {}
    def print_delta_enthalpy_real(self):
        """
        Mencetak tabel selisih entalpi antar komponen (Real Cycle).
        Satuan: kJ/kg
        """
        # Cek apakah simulasi sudah dijalankan
        if not self.real_states:
            print("Error: Jalankan .run_simulation() terlebih dahulu.")
            return

        # Ambil list H_r dari hasil simulasi
        # Urutan di list H_r: 
        # [0:H0, 1:H1, 2:H1_sup, 3:H2, 4:H23rec, 5:H23rec3, 6:H3, 7:H4, 8:H41rec]
        H = self.real_states["H"]
        
        # Mapping variabel supaya rumus mudah dibaca (satuan masih J/kg)
        h0_r      = H[0]
        h1_r      = H[1]
        h1sup_r   = H[2]
        h2_r      = H[3]
        h23rec_r  = H[4]
        # h23rec3_r = H[5] # Tidak dipakai di rumus request
        h3_r      = H[6]
        h4_r      = H[7]
        h41rec_r  = H[8]

        # Kalkulasi Delta H (Dikonversi ke kJ/kg dengan membagi 1000)
        val_lh      = (h0_r - h41rec_r) / 1000
        val_eva     = (h1_r - h0_r) / 1000
        val_sup     = (h1sup_r - h1_r) / 1000
        val_exp     = (h1sup_r - h2_r) / 1000
        val_rec_cold= (h41rec_r - h4_r) / 1000
        val_rec_hot = (h2_r - h23rec_r) / 1000
        val_cds     = (h23rec_r - h3_r) / 1000 # Total rejection dari post-recuperator
        val_pmp     = (h4_r - h3_r) / 1000

        # Siapkan data untuk tabulate
        table_data = [
            [1, "LH (Liquid Heater)", val_lh],
            [2, "EVA (Evaporator)",   val_eva],
            [3, "SUP (Superheater)",  val_sup],
            [4, "EXP (Expander)",     val_exp],
            [5, "REC (Cold Side)",    val_rec_cold],
            [6, "REC (Hot Side)",     val_rec_hot],
            [7, "CDS (Condenser)",    val_cds],
            [8, "PMP (Pump)",         val_pmp],
        ]

        headers = ["Nomor", "Nama Komponen", "Nilai (kJ/kg)"]
        
        print("\n--- Analisis Entalpi Komponen (Real Cycle) ---")
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=".4f"))
    def print_mass_flow(self):
        """
        Mencetak tabel mass flow rate untuk fluida kerja,
        fluida panas (heat source), dan fluida dingin (cooling source).
        Satuan: kg/s
        """
        # Cek apakah simulasi sudah dijalankan
        if not self.sim_results:
            print("Error: Jalankan .run_simulation() terlebih dahulu.")
            return

        # Ambil data dari atribut 'self'
        # 1. Fluida Kerja (Siklus)
        m_cycle = self.wf_mass_flow
        fluid_cycle = self.fluid

        # 2. Fluida Panas (Heat Source)
        m_hs = self.sim_results.get('hs_mass_flow')
        fluid_hs = self.hs_fluid

        # 3. Fluida Dingin (Cooling Source)
        m_cs = self.sim_results.get('cs_mass_flow')
        fluid_cs = self.cs_fluid
        
        # Siapkan data untuk tabulate
        table_data = [
            [1, "Fluida Kerja (Cycle)",   fluid_cycle, m_cycle],
            [2, "Heat Source (S. Panas)", fluid_hs,    m_hs],
            [3, "Cooling Source (S. Dingin)", fluid_cs,  m_cs],
        ]

        headers = ["Nomor", "Deskripsi", "Jenis Fluida", "Nilai (kg/s)"]
        
        print("\n--- Analisis Mass Flow Rate ---")
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=".4f"))
    def print_energy_transfer(self):
            """
            Mencetak tabel laju transfer energi untuk setiap komponen
            berdasarkan mass flow fluida kerja (wf_mass_flow).
            Satuan: kW
            """
            # Cek apakah simulasi sudah dijalankan
            if not self.real_states:
                print("Error: Jalankan .run_simulation() terlebih dahulu.")
                return

            # Ambil list H_r (J/kg) dan mass flow (kg/s)
            H = self.real_states["H"]
            m_dot = self.wf_mass_flow

            # Mapping variabel supaya rumus mudah dibaca (satuan masih J/kg)
            h0_r      = H[0]
            h1_r      = H[1]
            h1sup_r   = H[2]
            h2_r      = H[3]
            h23rec_r  = H[4]
            h3_r      = H[6]
            h4_r      = H[7]
            h41rec_r  = H[8]

            # 1. Hitung spesifik delta h (kJ/kg)
            dh_lh      = (h0_r - h41rec_r) / 1000
            dh_eva     = (h1_r - h0_r) / 1000
            dh_sup     = (h1sup_r - h1_r) / 1000
            dh_exp     = (h1sup_r - h2_r) / 1000
            dh_cds     = (-h23rec_r + h3_r) / 1000 # (h3_r - h23rec_r)
            dh_pmp     = (h3_r - h4_r) / 1000
            
            # Energi recuperator (untuk catatan)
            dh_rec     = (h41rec_r - h4_r) / 1000 

            # 2. Hitung Laju Energi (kW) = (kJ/kg) * (kg/s)
            E_lh   = dh_lh * m_dot
            E_eva  = dh_eva * m_dot
            E_sup  = dh_sup * m_dot
            E_exp  = dh_exp * m_dot
            E_cds  = dh_cds * m_dot
            E_pmp  = dh_pmp * m_dot
            
            # Energi recuperator (untuk catatan)
            E_rec  = dh_rec * m_dot 

            # Siapkan data untuk tabulate (TANPA RECUPERATOR)
            table_data = [
                [1, "LH (Liquid Heater)", E_lh],
                [2, "EVA (Evaporator)",   E_eva],
                [3, "SUP (Superheater)",  E_sup],
                [4, "EXP (Expander)",     E_exp],
                [5, "CDS (Condenser)",    E_cds],
                [6, "PMP (Pump)",         E_pmp],
            ]

            headers = ["Nomor", "Komponen", "Energi Transfer (kW)"]
            
            print("\n--- Analisis Laju Transfer Energi (Siklus) ---")
            print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=".4f"))
            
            # --- Catatan dimodifikasi di sini ---

            print(f"Catatan: (+) = Energi yang dikerjakan oleh sistem (Panas/Kerja OUT)\n"
                f"         (-) = Energi yang dikerjakan pada sistem (Panas/Kerja IN)\n"
                f"         * Energi internal REC (dihemat): {E_rec:.4f} kW")
    def print_hs_prop(self):
        """
        Mencetak tabel properti untuk Heat Source (Fluida Panas).
        Satuan: degC, kJ/kg
        """
        # Cek apakah simulasi sudah dijalankan
        if not self.hs_temps or not self.external_h or not self.sim_results:
            print("Error: Jalankan .run_simulation() terlebih dahulu.")
            return

        # Ambil data dari atribut 'self'
        try:
            # Ambil Temperatur (dalam K)
            T_in = self.hs_temps["T_hs_in"]
            T_mid2 = self.hs_temps["T_hs_mid2"]
            T_mid1 = self.hs_temps["T_hs_mid1"]
            T_out = self.hs_temps["T_hs_out"]
            
            # Ambil Entalpi (dalam J/kg)
            H_list = self.external_h["H_hs"] # [h_in, h_mid2, h_mid1, h_out]
            h_in = H_list[0]
            h_mid2 = H_list[1]
            h_mid1 = H_list[2]
            h_out = H_list[3]
            
            # Ambil mass flow (kg/s)
            m_dot_hs = self.sim_results["hs_mass_flow"]
            
        except (KeyError, IndexError) as e:
            print(f"Error: Data simulasi HS tidak lengkap ({e}).")
            return

        # 1. Konversi Unit
        # T (K -> degC)
        T_in_C = T_in - 273.15
        T_mid2_C = T_mid2 - 273.15
        T_mid1_C = T_mid1 - 273.15
        T_out_C = T_out - 273.15
        
        # H (J/kg -> kJ/kg)
        h_in_kJ = h_in / 1000
        h_mid2_kJ = h_mid2 / 1000
        h_mid1_kJ = h_mid1 / 1000
        h_out_kJ = h_out / 1000
        
        # 2. Siapkan data tabel
        table_data = [
            [1, "HS In",      T_in_C,   h_in_kJ],
            [2, "HS Mid 2",   T_mid2_C, h_mid2_kJ],
            [3, "HS Mid 1",   T_mid1_C, h_mid1_kJ],
            [4, "HS Out",     T_out_C,  h_out_kJ],
        ]
        
        headers = ["Nomor", "Index Heat Source", "T (°C)", "H (kJ/kg)"]

        # 3. Hitung Q_in verifikasi
        # Q (kW) = m_dot (kg/s) * delta_h (kJ/kg)
        Q_in_hs = m_dot_hs * (h_in_kJ - h_out_kJ)
        
        # 4. Print tabel dan catatan
        print("\n--- Properti Heat Source (Fluida Panas) ---")
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=".2f"))
        
        print("Catatan:")
        print(f"         1. Mass Flow Heat Source (m_dot_hs): {m_dot_hs:.4f} kg/s")
        print(f"         2. Verifikasi Q_in (sisi HS): {Q_in_hs:.4f} kW")
        print(f"         3. Tekanan Heat Source diasumsikan konstan pada {self.p_hs_in/100000:.2f} bar")
    def print_cs_prop(self):
        """
        Mencetak tabel properti untuk Cooling Source (Fluida Dingin).
        Satuan: degC, kJ/kg
        """
        # Cek apakah simulasi sudah dijalankan
        if not self.cs_temps or not self.external_h or not self.sim_results:
            print("Error: Jalankan .run_simulation() terlebih dahulu.")
            return

        # Ambil data dari atribut 'self'
        try:
            # Ambil Temperatur (dalam K)
            T_in = self.cs_temps["T_cs_in"]
            T_mid1 = self.cs_temps["T_cs_mid1"]
            T_out = self.cs_temps["T_cs_out"]
            
            # Ambil Entalpi (dalam J/kg)
            # Urutan di 'run_simulation': [h_cs_in, h_cs_mid1, h_cs_out]
            H_list = self.external_h["H_cs"] 
            h_in = H_list[0]
            h_mid1 = H_list[1]
            h_out = H_list[2]
            
            # Ambil mass flow (kg/s)
            m_dot_cs = self.sim_results["cs_mass_flow"]
            
        except (KeyError, IndexError) as e:
            print(f"Error: Data simulasi CS tidak lengkap ({e}).")
            return

        # 1. Konversi Unit
        # T (K -> degC)
        T_in_C = T_in - 273.15
        T_mid1_C = T_mid1 - 273.15
        T_out_C = T_out - 273.15
        
        # H (J/kg -> kJ/kg)
        h_in_kJ = h_in / 1000
        h_mid1_kJ = h_mid1 / 1000
        h_out_kJ = h_out / 1000
        
        # 2. Siapkan data tabel
        table_data = [
            [1, "CS In",      T_in_C,   h_in_kJ],
            [2, "CS Mid 1",   T_mid1_C, h_mid1_kJ],
            [3, "CS Out",     T_out_C,  h_out_kJ],
        ]
        
        headers = ["Nomor", "Index Cooling Source", "T (°C)", "H (kJ/kg)"]

        # 3. Hitung Q_out verifikasi
        # Q (kW) = m_dot (kg/s) * delta_h (kJ/kg)
        # (Energi yang diserap oleh fluida pendingin)
        Q_out_cs = m_dot_cs * (h_out_kJ - h_in_kJ)
        
        # 4. Print tabel dan catatan
        print("\n--- Properti Cooling Source (Fluida Dingin) ---")
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=".2f"))
        
        print("Catatan:")
        print(f"         1. Mass Flow Cooling Source (m_dot_cs): {m_dot_cs:.4f} kg/s")
        print(f"         2. Verifikasi Q_out (sisi CS): {Q_out_cs:.4f} kW")
        print(f"         3. Tekanan Cooling Source diasumsikan konstan pada {self.p_cs_in/100000:.2f} bar")
    def print_state_information(self):
        """
        Mencetak tabel informasi state point (real cycle)
        dengan unit yang sudah dikonversi (degC, bar, kJ/kg).
        """
        # Cek apakah simulasi sudah dijalankan
        if not self.real_states:
            print("Error: Jalankan .run_simulation() terlebih dahulu.")
            return

        # Ambil data list dari self.real_states
        # Pastikan run_simulation sudah mengisi "X"
        try:
            T_list = self.real_states["T"]
            P_list = self.real_states["P"]
            S_list = self.real_states["S"]
            H_list = self.real_states["H"]
            X_list = self.real_states["X"]
        except KeyError as e:
            print(f"Error: Data '{e.args[0]}' tidak ditemukan di self.real_states.")
            print("Pastikan run_simulation sudah menyimpan 'X' di self.real_states.")
            return

        # Label state point sesuai urutan di list
        state_labels = [
            "0 (Outlet LH)", 
            "1 (Outlet EVA)", 
            "1sup (Outlet SUP)", 
            "2 (Outlet EXP)", 
            "23rec (REC to CDS)", 
            "23rec3 (Desuperheater)", 
            "3 (Outlet CDS)", 
            "4 (Outlet PMP)", 
            "41rec (REC to LH)"
        ]
        
        table_data = []
        headers = ["State Index", "T (°C)", "P (bar)", "S (kJ/kg.K)", "H (kJ/kg)", "X (Quality)"]

        # Loop untuk setiap state, konversi unit, dan format data
        for i in range(len(state_labels)):
            label = state_labels[i]
            
            # Cek jika state (seperti 23rec3) tidak dihitung (None)
            if T_list[i] is None:
                row = [label, "---", "---", "---", "---", "---"]
            else:
                # Lakukan konversi unit
                T_C = T_list[i] - 273.15
                P_bar = P_list[i] / 100000  # Pa ke bar
                S_kJ = S_list[i] / 1000     # J/kg.K ke kJ/kg.K
                H_kJ = H_list[i] / 1000     # J/kg ke kJ/kg
                
                # Format X (Quality)
                X_raw = X_list[i]
                if isinstance(X_raw, (int, float)):
                    # Jika X adalah angka (0, 1, atau nilai quality 0-1)
                    X_val = f"{X_raw:.4f}"
                elif X_raw is None:
                    # Jika X adalah None
                    X_val = "---"
                else:
                    # Jika X adalah string (misal 'gas', 'liquid', 'supercritical')
                    X_val = str(X_raw) 
                
                row = [label, T_C, P_bar, S_kJ, H_kJ, X_val]
            
            table_data.append(row)

        print("\n--- Informasi State Point (Real Cycle) ---")
        
        # Tentukan format angka untuk setiap kolom
        # [Index, T, P, S, H, X]
        col_formats = [None, ".2f", ".3f", ".4f", ".2f", None]
        
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid", floatfmt=col_formats))
    def calculate_performance(self, use_ideal_states=False):
        """
        Menghitung performa siklus (efisiensi, W_net)
        berdasarkan hasil simulasi.
        
        Args:
            use_ideal_states (bool): Jika True, hitung performa ideal.
                                     Defaultnya False (hitung real).
        """
        if not self.real_states:
            print("Error: Jalankan .run_simulation() terlebih dahulu.")
            return None

        if use_ideal_states:
            H_list = self.ideal_states["H"]
        else:
            H_list = self.real_states["H"]
            
        # Indeks berdasarkan list H_r/H_is:
        # 2: H1_sup (SUP out)
        # 3: H2 (EXP out)
        # 6: H3 (CDS out)
        # 7: H4 (PMP out)
        # 8: H41rec (REC out to LH)

        W_dot_exp_spec = (H_list[2] - H_list[3]) / 1000  # kJ/kg
        W_dot_pmp_spec = (H_list[7] - H_list[6]) / 1000  # kJ/kg
        W_dot_net_spec = W_dot_exp_spec - W_dot_pmp_spec

        Q_dot_in_spec = (H_list[2] - H_list[8]) / 1000 # Q_in = H_sup_out - H_rec_out
        # Hindari pembagian dengan nol jika Q_dot_in_spec adalah 0
        if Q_dot_in_spec == 0:
            eta_thermal = 0
        else:
            eta_thermal = W_dot_net_spec / Q_dot_in_spec

        # Simpan hasil performa ke 'self'
        self.performance = {
            "eta_thermal": eta_thermal,
            "W_dot_net_kW": W_dot_net_spec * self.wf_mass_flow,
            "Q_dot_in_kW": Q_dot_in_spec * self.wf_mass_flow,
            "W_dot_exp_kW": W_dot_exp_spec * self.wf_mass_flow,
            "W_dot_pmp_kW": W_dot_pmp_spec * self.wf_mass_flow,
        }
        
        print(f"Performa (Real) berhasil dikalkulasi. Efisiensi Termal: {eta_thermal:.2%}")
        return self.performance


