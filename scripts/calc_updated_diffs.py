import pandas as pd
import io

# Let's write the rows to updated_products.tsv
from scripts.write_updated_tsv import raw_data

# The user provided header + 2 rows:
row1 = r'''"[Product2]"	"01tbI00000BJKcbQAH"	"Benvenuto in ENGIE"	"VARD"	"Benvenuto in ENGIE"	"true"	"2024-12-02T19:04:05.000+0000"	"0056M000009a5nOQAQ"	"2026-10-08T14:56:22.000+0000"	"005bI000006dcDFQAY"	"2026-10-08T14:56:22.000+0000"	"CPQ"	"false"	"01220000000TwwVAAS"	""	""	""	""	"false"	"false"	"2026-10-15T08:55:46.000+0000"	"2026-10-15T08:55:46.000+0000"	""	""	""	""	""	"00013"	"2024-12-11"	"2025-02-11"	""	""	""	""	"24"	"VARD#00013"	""	""	"true"	""	""	""	""	""	""	"true"	"true"	""	""	""	""	""	"Attivazione_SE;Rialimentazione_DF;Rialimentazione_SE;Voltura_DF;Voltura_SE;Rialimentazione_SG;Voltura_SG;Attivazione_GAS;Cambio_Prodotto_SG;Cambio_Prodotto_SE;Cambio_Prodotto_DF"	"Residenziale DF"	"Residenziale SE"	"Residenziale SG"	"2204"	"2204"	"2204"	""	""	""	""	""	""	"1112"	"1112"	"L"	"false"	"Web;Inbound 2 Sales;Door 2 Door;Stellar;Ranger;Agenzie Non Categorizzate;Teleselling"	"true"	"true"	"1106"	"1104"	"false"	"false"	"false"	"true"	"251"	"250"	"2204"	""	"false"	"false"	""	"false"	"false"	"false"	"MM"	""	"90"	""	"false"	""	"Benvenuto in ENGIE"	"Benvenuto in ENGIE"	""	"false"	"false"	""	"false"	"false"	""	"false"	""	""	""	""	""	"false"	"R93"	""	""	""	"false"	""	"false"	"false"	"false"	"false"	""	"false"	"false"	"false"	""	""	""	"false"	""	""	"Indicizzato"	"PSVDA"	"PUNA"	"Mensile"	"Mensile"	"0.065"	"0.02727"	"5.61"	"5.823"	"0.00795"	"0"	""	"false"	"false"	"false"	""	""	""	""	""	""	""	""	""	"NX"	""	""	""	"false"	"true"	"Residential"	"24768.905"	"1268.1989015655"	"582.636452"	"15818.92868754"	"2447.987803131"	"1001.766488"	"11208.8156"	"35482.077046965"	"4021.039671885"	"1790.717144"	"172.50208989432"	"1179.1363081278"	"1651.051868754"	"456.00835957728"	"4010.629671885"	"628.5681540639"	"1064.590253"	"300.840731925"	"448.663219875"	"621.12278915"	"744.308195775"	"867.4936024"	"941.404846375"	"1557.3318795"	""	""	""	""	""	""	"P"	"A fasce"	"X"	"X"	""	""	"001714EPVFL13XXVARD0001300000000"	""	""	"001714GPVML13XXVARD0001300000000"	"001714DPVFL13XXVARD0001300000000"	""	""	""	""	""	""	"67.32"	"69.88"	""	""	""	"NO"	"No, tutto su Pfor"	"NO"	"NO"	"SI"	""	"false"	"Monoraria;Multioraria"	""	""	""	""	""	""	"Creato su Billing"	"Forfettario"	"OK"	"NO"	"RC010"	"true"	"false"	"NO"	""	""	""	""	""	"113.09"	"88.41"	"113.09"	"78"	"78"	"0"	"0"	"0"	"0.00795"	"0.00795"	"0.002"	""	""	""	""	""	"NO"	"0.02727"	"0.02727"	"0.02727"	""	""	""	"Prodotto_a_scaffale_CPQ"	""	""	""	""	"0.03"	"0.03"	"0.03"	""	"0.03"	"false"	""	""	"true"	""	"false"	"false"	"Voltura;Attivazione;Rialimentazione;Cambio Prodotto"	"true"	"false"	"https://www.arera.it/consumatori"'''

row2 = r'''"[Product2]"	"01tbI00000TRAc5QAH"	"PRODOTTO OMBRELLO INDICIZZATO"	"VOMB"	""	"true"	"2026-09-24T16:52:41.000+0000"	"005bI000006OSm6QAG"	"2026-10-07T10:02:29.000+0000"	"005bI000006dcDFQAY"	"2026-10-07T10:02:29.000+0000"	"CPQ"	"false"	"01220000000TwwVAAS"	""	""	""	""	"false"	"false"	"2026-10-15T08:56:45.000+0000"	"2026-10-15T08:56:45.000+0000"	""	""	""	""	""	"00007"	"2026-10-08"	"2026-10-21"	""	""	""	""	"12"	"VOMB#00007"	""	""	"true"	""	""	""	""	""	""	"true"	"true"	""	""	""	""	""	"SwitchIn_SE;SwitchIn_SG;SwitchIn_DF"	"Residenziale DF"	"Residenziale SE"	"Residenziale SG"	"2204"	"2204"	"2204"	""	""	""	""	""	""	"1112"	"1112"	"L"	"false"	""	"true"	"true"	"1106"	"1104"	"false"	"false"	"false"	"false"	"250"	"251"	"2204"	""	"true"	"false"	""	"false"	"false"	"false"	"MM"	""	"90"	""	"false"	""	""	""	""	"false"	"false"	""	"false"	""	""	""	""	""	"false"	"R111"	""	""	""	"false"	""	"false"	"false"	"false"	"false"	""	"false"	"false"	"false"	""	""	""	"false"	""	""	"Indicizzato"	"PSVDA"	"PUNA"	"Mensile"	"Mensile"	"0.15"	"0.03091"	""	""	""	""	""	"false"	"true"	"false"	""	""	""	""	""	""	""	""	""	"NX"	""	""	""	"false"	"true"	"Residential"	"24808.198"	"1383.7739015655"	"582.297052"	"17359.92868754"	"2679.137803131"	"1002.113888"	"11225.8886"	"38949.327046965"	"4406.289671885"	"1792.357344"	"247.74808989432"	"1353.0063081278"	"1871.151868754"	"558.99235957728"	"4461.879671885"	"748.5031540639"	"1131.099253"	"366.097331925"	"514.162219875"	"686.90458915"	"810.291995775"	"933.6794024"	"1007.711846375"	"1624.6488795"	""	""	""	""	""	""	"P"	"A fasce"	"X"	"X"	""	""	"001714EPVFL07XXVOMB0000700000000"	""	""	"001714GPVML07XXVOMB0000700000000"	"001714DPVFL07XXVOMB0000700000000"	""	""	""	""	""	""	""	""	""	""	""	"NO"	"No, tutto su Pfor"	"NO"	"NO"	"SI"	""	"false"	"Monoraria;Multioraria"	""	""	""	""	""	""	"Creato su Billing"	"CDISPD"	"OK"	"NO"	"RC010"	"true"	"false"	"NO"	""	""	""	""	""	"113.09"	"88.41"	"113.09"	"144"	"144"	"0"	"0"	"0"	"0"	"0"	""	""	""	""	""	""	"SI"	"0.03091"	"0.03091"	"0.03091"	""	""	""	"Prodotto_a_scaffale_CPQ"	""	""	""	""	"0.034"	"0.034"	"0.034"	""	"0.034"	"false"	""	""	"false"	""	"false"	"false"	"Rinnovo"	"true"	"false"	"https://www.arera.it/consumatori"'''

import csv
header = list(csv.reader(io.StringIO(raw_data.strip()), delimiter='\t'))[0]
r1_vals = list(csv.reader(io.StringIO(row1.strip()), delimiter='\t'))[0]
r2_vals = list(csv.reader(io.StringIO(row2.strip()), delimiter='\t'))[0]

print("Header length:", len(header))
print("Row 1 length:", len(r1_vals))
print("Row 2 length:", len(r2_vals))

vard = dict(zip(header, r1_vals))
vomb = dict(zip(header, r2_vals))

print("\n--- PARAMETRI ECONOMICI CHIAVE ---")
for k in ['Codice_univoco__c', 'Name', 'ProductCode', 'Release__c', 'Processo__c',
          'Quota_Comm_fissa_dom_ENGIE_Luce__c', 'Quota_Comm_fissa_domestico_ENGIE_Gas__c',
          'Quota_Comm_fissa_altri_usi_BT_ENGIE_Luce__c', 'Quota_Comm_fissa_altri_usi_ENGIE_Gas__c',
          'Spread_luce__c', 'Spread_luce_lordo_perdite__c', 'Dispacciamento__c',
          'Spread_gas__c', 'Quota_Comm_variabile_dom_ENGIE_Gas__c', 'Quota_Comm_variabile_altri_usi_ENGIE_Gas__c']:
    print(f"{k:45}: VARD={vard.get(k)} | VOMB={vomb.get(k)}")

groups = {
    'Luce - Domestico Residente': [
        ('CodCondSpeStimAnnoR3kW1500kWh__c', 'Residente 3 kW - 1.500 kWh'),
        ('CodCondSpeStimAnnoR3kW2200kWh__c', 'Residente 3 kW - 2.200 kWh'),
        ('CodCondSpeStimAnnoR3kW2700kWh__c', 'Residente 3 kW - 2.700 kWh (ARERA Base)'),
        ('CodCondSpeStimAnnoR3kW3200kWh__c', 'Residente 3 kW - 3.200 kWh'),
        ('CodCondSpeStimAnnoR4_5kW3500kWh__c', 'Residente 4,5 kW - 3.500 kWh'),
        ('CodCondSpeStimAnnoR6kW6000kWh__c', 'Residente 6 kW - 6.000 kWh'),
    ],
    'Luce - Domestico Non Residente': [
        ('CodCondSpeStimAnnoNR3kW900kWh__c', 'Non Residente 3 kW - 900 kWh'),
        ('CodCondSpeStimAnnoNR3kW4000kWh__c', 'Non Residente 3 kW - 4.000 kWh'),
    ],
    'Luce - Altri Usi (AU / Business)': [
        ('CodCondSpeStimAnnoAU1900kWh__c', 'Altri Usi - 1.900 kWh'),
        ('CodCondSpeStimAnnoAU3600kWh__c', 'Altri Usi - 3.600 kWh'),
        ('CodCondSpeStimAnnoAU6800kWh__c', 'Altri Usi - 6.800 kWh'),
        ('CodCondSpeStimAnnoAU45000kWh__c', 'Altri Usi - 45.000 kWh'),
        ('CodCondSpeStimAnnoAU100000kWh__c', 'Altri Usi - 100.000 kWh'),
    ],
    'Gas - Domestico': [
        ('CodCondSpeStimAnnoDOM120smc__c', 'Domestico - 120 Smc (Cottura)'),
        ('CodCondSpeStimAnnoDOM480smc__c', 'Domestico - 480 Smc (Acqua calda/Cottura)'),
        ('CodCondSpeStimAnnoDOM700smc__c', 'Domestico - 700 Smc (Riscaldamento)'),
        ('CodCondSpeStimAnnoDOM1400smc__c', 'Domestico - 1.400 Smc (ARERA Base Riscaldamento)'),
        ('CodCondSpeStimAnnoDOM2000smc__c', 'Domestico - 2.000 Smc'),
        ('CodCondSpeStimAnnoDOM5000smc__c', 'Domestico - 5.000 Smc'),
    ],
    'Gas - Altri Usi (AU / Condomini / P.IVA)': [
        ('CodCondSpeStimAnnoAU1500smc__c', 'Altri Usi - 1.500 Smc'),
        ('CodCondSpeStimAnnoAU3000smc__c', 'Altri Usi - 3.000 Smc'),
        ('CodCondSpeStimAnnoAU5000smc__c', 'Altri Usi - 5.000 Smc'),
        ('CodCondSpeStimAnnoAU20000smc__c', 'Altri Usi - 20.000 Smc'),
        ('CodCondSpeStimAnnoAU45000smc__c', 'Altri Usi - 45.000 Smc'),
    ]
}

print("\n--- CONFRONTO CODICI CONDOTTA ---")
for grp, items in groups.items():
    print(f'\n=== {grp} ===')
    for field, desc in items:
        v = float(vard[field])
        o = float(vomb[field])
        diff = o - v
        diff_pct = (diff / v) * 100
        sign = '+' if diff > 0 else ''
        print(f'{desc:48} | VARD: {v:10.2f} € | VOMB (Rinnovo): {o:10.2f} € | Delta: {sign}{diff:8.2f} € ({sign}{diff_pct:+.2f}%)')
