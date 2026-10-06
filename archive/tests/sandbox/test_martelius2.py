import pandas as pd
df = pd.read_parquet('data/processed/storico_2026.parquet')
m = df[df['NOME_OFFERTA'] == 'GAS GALATTICA']
if len(m) > 0:
    for _, row in m.iterrows():
        print('Venditore:', row['PIVA_VENDITORE'])
        print('CCV (Quota fissa):', row.get('COMP_IMP_0_INT_0_PREZZO', 'N/A'))
        print('Prezzo Vol (smc):', row.get('COMP_IMP_0_INT_1_PREZZO', 'N/A'))
        print('Sconto 1:', row.get('SCONTO_1_PREZZO_1_VAL', 'N/A'))
else:
    print('Offerta non trovata in questo file')

