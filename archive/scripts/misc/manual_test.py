import sys
import pandas as pd
import numpy as np

sys.path.append('.')
from engine.sas_calculator_fast import FastSASCalculator

data = [
    {
        'commodity': 'G',
        'PIVA_VENDITORE': '01806250625',
        'COD_OFFERTA': '038693GSFML01XX00000000000032463',
        'NOME_OFFERTA': 'GAS GALATTICA',
        'TIPO_OFFERTA': '01',
        'TIPO_CLIENTE': '01',
        'REGIONE': '03',
        'PROVINCIA': '015',
        'COMUNE': 'F205',
        'prezzo_vol': 0.489,
        'prezzo_fix': 48.0,
        'sconto_fisso': 0.0,
        'sconto_vol': 0.0,
        'TIPOLOGIA_FASCE': '01'
    }
]
df = pd.DataFrame(data)
calc = FastSASCalculator(df)
res_gas = calc.calculate_sas(df[df['commodity'] == 'G'], {'F1': 1400}, 3.0, is_dual_fuel=False, is_domiciliazione=False, regione='Lombardia', residente=True)
print(res_gas[['NOME_OFFERTA', 'SAS']])
