
import pyarrow.parquet as pq
table = pq.read_table('data/processed/storico_2026_full.parquet')
df = table.to_pandas()
for nome in ['Extra2a Luce', 'E.ON LuceClick biorariaVerde']:
    row = df[df['NOME_OFFERTA'] == nome]
    if not row.empty:
        r = row.iloc[0]
        di = r.get('DATA_INIZIO')
        dfine = r.get('DATA_FINE')
        vf = r.get('COMP_IMP_1_INT_1_VALIDO_FINO')
        print(nome, 'INIZIO:', di, 'FINE:', dfine, 'VALIDO_FINO:', vf)

