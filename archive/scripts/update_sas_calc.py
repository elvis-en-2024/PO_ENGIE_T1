import re

with open('engine/sas_calculator.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace the __init__ to include AreraTariffs
new_init = """import pandas as pd
import numpy as np
from engine.arera_tariffs import AreraTariffs

class SASCalculator:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.arera = AreraTariffs()
"""
code = re.sub(r'import pandas as pd\nimport numpy as np\n\nclass SASCalculator:\n    def __init__\(self, df: pd\.DataFrame\):\n        self\.df = df\n\s+# Costanti ARERA.*?\n        }', new_init, code, flags=re.DOTALL)

# Replace calculate_sas definition to take regione and residente
code = code.replace(
    "def calculate_sas(self, \n                      filtered_df: pd.DataFrame, \n                      consumi: dict, \n                      potenza: float, \n                      is_dual_fuel: bool = False,\n                      is_domiciliazione: bool = False):",
    "def calculate_sas(self, \n                      filtered_df: pd.DataFrame, \n                      consumi: dict, \n                      potenza: float, \n                      is_dual_fuel: bool = False,\n                      is_domiciliazione: bool = False,\n                      regione: str = 'Lombardia',\n                      residente: bool = True):"
)

# Replace Oneri e Reti standard in calculate_sas
new_oneri = """        TOT_CONS = F1 + F2 + F3
        
        # Oneri e Reti (Verranno calcolati dinamicamente nel loop o qui)
        ele_conf = self.arera.ELE['residente' if residente else 'non_residente']
        tot_reti_oneri_ele = (
            ele_conf['dist_fix'] + ele_conf['oneri_fix'] + 
            (ele_conf['trasp_pot'] + ele_conf['oneri_pot']) * potenza + 
            (ele_conf['trasp_vol'] + ele_conf['oneri_vol']) * TOT_CONS
        )
        accisa_ele = self.arera.get_ele_accisa_avg(residente, TOT_CONS) * TOT_CONS
        
        gas_fix_arera, gas_vol_arera = self.arera.get_gas_costi_regolati(regione, TOT_CONS)
"""
code = re.sub(r'        TOT_CONS = F1 \+ F2 \+ F3\n.*?\n        accisa = self\.ARERA\[\'accisa\'\]\n', new_oneri + '\n', code, flags=re.DOTALL)

# Replace the CDISPd part and tot_sas calculation inside the loop
new_totali = """            if commodity == 'E':
                # 3. CDISPd (Sbilanciamento)
                cdispd_val = row.get('DISP_CdispD_VALORE')
                if not pd.isna(cdispd_val):
                    try:
                        cdispd = float(str(cdispd_val).replace(',', '.'))
                    except ValueError:
                        cdispd = ele_conf['cdispd']
                else:
                    cdispd = ele_conf['cdispd']
                    
                costo_venditore_vol += cdispd * TOT_CONS
                
                # Totali ELE
                costo_venditore = costo_venditore_fix + costo_venditore_vol
                tot_netto = costo_venditore + tot_reti_oneri_ele + accisa_ele
                iva = tot_netto * 0.10  # 10% IVA su tutto per l'elettricità residenziale
                if not residente:
                    iva = tot_netto * 0.22 # Non residenti 22%
                tot_sas = tot_netto + iva
            else:
                # GAS
                costo_venditore = costo_venditore_fix + costo_venditore_vol
                
                # Oneri regolate + Accise + Addizionali ivati
                tot_arera_ivato = (gas_fix_arera * 1.22) + (gas_vol_arera * TOT_CONS * 1.10)
                
                # IVA 22% su base fissa, 10% su base variabile venditore
                tot_sas = (costo_venditore_fix * 1.22) + (costo_venditore_vol * 1.10) + tot_arera_ivato
"""
code = re.sub(r'            if commodity == \'E\':.*?tot_sas = \(costo_venditore_fix \* 1\.22\) \+ \(costo_venditore_vol \* 1\.10\) \+ 173\.16', new_totali, code, flags=re.DOTALL)

with open('engine/sas_calculator.py', 'w', encoding='utf-8') as f:
    f.write(code)
