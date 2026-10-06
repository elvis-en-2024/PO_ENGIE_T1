import pyarrow.parquet as pq
import pyarrow.compute as pc
import pandas as pd

table = pq.read_table('data/storage/storico_completo.parquet')

# Filter for EE, Fixed Price
# TIPO_MERCATO? We want Mercato Libero maybe? Or just ELE?
# commodity is usually 'EE' or 'Elettricita' or 'Luce'
# Let's check unique commodities
com = pc.unique(table['commodity']).to_pylist()
print("Commodities:", com)

# Print unique TIPO_MERCATO
tm = pc.unique(table['TIPO_MERCATO']).to_pylist()
print("TIPO_MERCATO:", tm)
