import sys
sys.path.insert(0, '.')
from app import load_data
from engine.sas_calculator_fast import FastSASCalculator
df = load_data('2026-08-27')
calc = FastSASCalculator(df)
filtered = calc.filter_offers(commodity='E', fasce='A Fasce', tipo_offerta='Fisso', regione='Lombardia', provincia='015', comune='F205', consumo_annuo=2700, falsa_multioraria='escludi')
sas, _ = calc.calculate_sas(filtered, consumo_annuo=2700, fasce='A Fasce', perc_f1=0.33, perc_f2=0.31, perc_f3=0.36)
filtered['SAS'] = sas
filtered = filtered.sort_values('SAS').head(30)
for i, (_, row) in enumerate(filtered.iterrows()):
    print(f"{i+1}. {row['NOME_VENDITORE']} - {row['NOME_OFFERTA']} - {row['SAS']:.2f}")
