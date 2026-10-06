import pandas as pd
df = pd.read_parquet('data/processed/storico_2026_full.parquet')
df = df[df['DATA_RIFERIMENTO'] == df['DATA_RIFERIMENTO'].max()]
m = df[df['NOME_OFFERTA'] == 'GAS GALATTICA']
for _, row in m.iterrows():
    print('Venditore:', row['PIVA_VENDITORE'])
    print('CCV (Quota fissa):', row.get('COMP_IMP_0_INT_0_PREZZO', 'N/A'))
    print('Prezzo Vol (smc):', row.get('COMP_IMP_0_INT_1_PREZZO', 'N/A'))
    print('Sconto 1:', row.get('SCONTO_1_PREZZO_1_VAL', 'N/A'))
    print('Sconto tipo:', row.get('SCONTO_1_PREZZO_1_TIPO', 'N/A'))

