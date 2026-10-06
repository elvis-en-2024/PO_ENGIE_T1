import re

with open('engine/sas_calculator_fast.py', 'r', encoding='utf-8') as f:
    content = f.read()

new_filter = """
    def filter_offers(self, commodity='E', tipo_offerta='Fisso', tipo_cliente='Domestico', fasce='Biorario', regione='Lombardia', provincia='015', comune='F205'):
        filtered = self.df
        
        # Commodity & Cliente
        filtered = filtered[
            (filtered['commodity'] == commodity) & 
            (filtered['TIPO_OFFERTA'].astype(str).str.contains(tipo_offerta, case=False, na=False)) &
            (filtered['TIPO_CLIENTE'].astype(str).str.contains(tipo_cliente, case=False, na=False))
        ]
        
        if regione and regione != 'Tutte' and 'REGIONE' in filtered.columns:
            istat_regioni = {
                'Piemonte': '01', 'Valle d\\'Aosta': '02', 'Lombardia': '03', 'Trentino-Alto Adige': '04', 
                'Veneto': '05', 'Friuli-Venezia Giulia': '06', 'Liguria': '07', 'Emilia-Romagna': '08', 
                'Toscana': '09', 'Umbria': '10', 'Marche': '11', 'Lazio': '12', 'Abruzzo': '13', 
                'Molise': '14', 'Campania': '15', 'Puglia': '16', 'Basilicata': '17', 'Calabria': '18', 
                'Sicilia': '19', 'Sardegna': '20'
            }
            regione_code = istat_regioni.get(regione, '03')
            is_national = filtered['REGIONE'].isna() | (filtered['REGIONE'] == '')
            is_regional = filtered['REGIONE'].astype(str) == regione_code
            filtered = filtered[is_national | is_regional]
            
        if provincia and 'PROVINCIA' in filtered.columns:
            is_national_prov = filtered['PROVINCIA'].isna() | (filtered['PROVINCIA'] == '') | (filtered['PROVINCIA'] == 'None')
            is_prov = filtered['PROVINCIA'].astype(str) == provincia
            filtered = filtered[is_national_prov | is_prov]
            
        if comune and 'COMUNE' in filtered.columns:
            is_national_com = filtered['COMUNE'].isna() | (filtered['COMUNE'] == '') | (filtered['COMUNE'] == 'None')
            is_com = filtered['COMUNE'].astype(str) == comune
            filtered = filtered[is_national_com | is_com]
            
        # Fasce (Solo per Elettricita')
        if commodity == 'E' and 'TIPOLOGIA_FASCE' in filtered.columns:
            if fasce == 'Biorario':
                filtered = filtered[filtered['TIPOLOGIA_FASCE'].astype(str).str.contains('F2|F3|biorario|Peak/OffPeak', na=False, regex=True, case=False)]
            elif fasce == 'Monorario':
                filtered = filtered[filtered['TIPOLOGIA_FASCE'].astype(str).str.contains('monorario', na=False, regex=True, case=False)]
        
        # Hardcode exclusion
        filtered = filtered[~filtered['NOME_OFFERTA'].astype(str).str.contains('Sottocosto', case=False, na=False)]
        return filtered
"""

pattern = r"def filter_offers\(self, commodity='E'.*?return filtered"
content = re.sub(pattern, new_filter.strip(), content, flags=re.DOTALL)

with open('engine/sas_calculator_fast.py', 'w', encoding='utf-8') as f:
    f.write(content)
