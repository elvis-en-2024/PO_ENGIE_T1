import pandas as pd
import xlsxwriter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]

def create_dashboard(input_csv="TEST_CRM_multi_risultati_con_codici.csv", output_xlsx="Dashboard_CRM.xlsx"):
    csv_path = BASE_DIR / "data" / "processed" / input_csv
    df = pd.read_csv(csv_path, sep=';', decimal=',')
    
    # Rimuoviamo i campi senza codice univoco per il menu a tendina
    df = df[df['Codice Univoco'].notna() & (df['Codice Univoco'] != '')]
    
    out_path = BASE_DIR / "data" / "processed" / output_xlsx
    
    # Crea l'Excel
    workbook = xlsxwriter.Workbook(out_path)
    
    # 1. Foglio Database
    ws_db = workbook.add_worksheet('Database')
    
    # Scrivi intestazioni
    headers = list(df.columns)
    for col_num, header in enumerate(headers):
        ws_db.write(0, col_num, header)
        
    # Scrivi dati
    for row_num, row_data in enumerate(df.values):
        for col_num, cell_data in enumerate(row_data):
            # se  nan, scrivi vuoto
            if pd.isna(cell_data):
                ws_db.write(row_num + 1, col_num, "")
            else:
                ws_db.write(row_num + 1, col_num, cell_data)
                
    # 2. Foglio Dashboard
    ws = workbook.add_worksheet('Dashboard')
    
    # Formati
    fmt_title = workbook.add_format({'bold': True, 'font_size': 16, 'bg_color': '#112244', 'font_color': 'white'})
    fmt_subtitle = workbook.add_format({'bold': True, 'font_size': 12, 'bg_color': '#E0E0E0'})
    fmt_header = workbook.add_format({'bold': True, 'bottom': 1, 'bg_color': '#F2F2F2'})
    fmt_currency = workbook.add_format({'num_format': '#,##0.00 €'})
    fmt_bold = workbook.add_format({'bold': True})
    
    ws.set_column('A:A', 25)
    ws.set_column('B:B', 20)
    ws.set_column('C:C', 20)
    ws.set_column('D:D', 20)
    ws.set_column('E:E', 20)
    ws.set_column('F:F', 20)
    ws.set_column('G:G', 20)
    
    # Selettore Prodotto
    ws.write('A1', 'DASHBOARD PRODOTTI CRM', fmt_title)
    ws.write('A3', 'Seleziona Codice Univoco:', fmt_bold)
    
    # Aggiungi Data Validation per A4
    num_rows = len(df)
    ws.data_validation('B3', {'validate': 'list',
                              'source': f'=Database!$A$2:$A${num_rows+1}',
                              'input_message': 'Scegli il codice prodotto'})
    
    # Imposta un valore di default per il dropdown
    default_code = str(df.iloc[0]['Codice Univoco'])
    ws.write('B3', default_code)
    
    ws.write('A4', 'Nome Prodotto:', fmt_bold)
    ws.write_formula('B4', f'=VLOOKUP(B3, Database!A:AW, 2, FALSE)')
    
    ws.write('A5', 'Tipo Prezzo:', fmt_bold)
    ws.write_formula('B5', f'=VLOOKUP(B3, Database!A:AW, 3, FALSE)')
    
    row = 7
    # --- TABELLA ENERGIA ELETTRICA ---
    ws.merge_range(f'A{row}:D{row}', 'ENERGIA ELETTRICA', fmt_title)
    row += 1
    ws.write(f'A{row}', 'Tipo abitazione', fmt_header)
    ws.write(f'B{row}', 'Potenza impegnata', fmt_header)
    ws.write(f'C{row}', 'Consumo annuo', fmt_header)
    ws.write(f'D{row}', 'Spesa annua stimata', fmt_header)
    row += 1
    
    profili_ee = [
        ('Residente', '3 kW', '1.500 kWh', 4),
        ('Residente', '3 kW', '2.200 kWh', 5),
        ('Residente', '3 kW', '2.700 kWh', 6),
        ('Residente', '3 kW', '3.200 kWh', 7),
        ('Residente', '4.5 kW', '3.500 kWh', 8),
        ('Residente', '6 kW', '6.000 kWh', 9),
        ('Non residente', '3 kW', '900 kWh', 10),
        ('Non residente', '3 kW', '4.000 kWh', 11)
    ]
    
    for res, pot, cons, col_idx in profili_ee:
        ws.write(f'A{row}', res)
        ws.write(f'B{row}', pot)
        ws.write(f'C{row}', cons)
        ws.write_formula(f'D{row}', f'=VLOOKUP($B$3, Database!$A:$AW, {col_idx}, FALSE)', fmt_currency)
        row += 1
        
    row += 2
    # --- TABELLE GAS (Formato a griglia) ---
    ws.merge_range(f'A{row}:F{row}', 'GAS', fmt_title)
    row += 2
    
    ambiti_left = [
        ("AMBITO NORD OCCIDENTALE VALLE D'AOSTA, PIEMONTE, LIGURIA", 12),
        ("AMBITO CENTRALE TOSCANA, UMBRIA, MARCHE", 24),
        ("AMBITO CENTRO-SUD OCCIDENTALE LAZIO, CAMPANIA", 36)
    ]
    ambiti_right = [
        ("AMBITO NORD ORIENTALE LOMBARDIA, TRENTINO, VENETO, FRIULI, EMR", 18),
        ("AMBITO CENTRO-SUD ORIENTALE ABRUZZO, MOLISE, PUGLIA, BASILICATA", 30),
        ("AMBITO MERIDIONALE CALABRIA, SICILIA, SARDEGNA", 42)
    ]
    
    start_row_gas = row
    
    for i in range(3):
        # LEFT TABLE
        r = start_row_gas + i * 9
        titolo_L, col_idx_L = ambiti_left[i]
        ws.merge_range(f'A{r}:C{r}', titolo_L, fmt_subtitle)
        ws.write(f'A{r+1}', 'Consumo annuo', fmt_header)
        ws.write(f'C{r+1}', 'Spesa annua stimata', fmt_header)
        for j, c in enumerate([120, 480, 700, 1400, 2000, 5000]):
            ws.write(f'A{r+2+j}', f'{c} smc')
            ws.write_formula(f'C{r+2+j}', f'=VLOOKUP($B$3, Database!$A:$AW, {col_idx_L+j}, FALSE)', fmt_currency)
            
        # RIGHT TABLE
        titolo_R, col_idx_R = ambiti_right[i]
        ws.merge_range(f'D{r}:F{r}', titolo_R, fmt_subtitle)
        ws.write(f'D{r+1}', 'Consumo annuo', fmt_header)
        ws.write(f'F{r+1}', 'Spesa annua stimata', fmt_header)
        for j, c in enumerate([120, 480, 700, 1400, 2000, 5000]):
            ws.write(f'D{r+2+j}', f'{c} smc')
            ws.write_formula(f'F{r+2+j}', f'=VLOOKUP($B$3, Database!$A:$AW, {col_idx_R+j}, FALSE)', fmt_currency)

    workbook.close()
    print(f"Dashboard creata con successo: {out_path}")

if __name__ == "__main__":
    create_dashboard()
