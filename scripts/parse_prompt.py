import csv
import io
import pandas as pd

with open(r'C:\PO_ENGIE\PO_ENGIE_T1\data\processed\user_last_prompt_full.txt', 'r', encoding='utf-8') as f:
    text = f.read()

# Split by the header
marker = '"_"\t"Id"\t"Name"'
idx1 = text.find(marker)
idx2 = text.find(marker, idx1 + len(marker))

print(f"Header 1 at {idx1}, Header 2 at {idx2}")

# Parse block 1
block1 = text[idx1:idx2]
reader1 = csv.reader(io.StringIO(block1.strip()), delimiter='\t')
rows1 = list(reader1)
print(f"rows1 count: {len(rows1)}")
for i, r in enumerate(rows1):
    print(f"rows1[{i}] length: {len(r)}")
header1 = rows1[0]
val1 = [r for r in rows1[1:] if len(r) == len(header1)][0]

# Parse block 2
block2 = text[idx2:]
reader2 = csv.reader(io.StringIO(block2.strip()), delimiter='\t')
rows2 = list(reader2)
header2 = rows2[0]
val2 = [r for r in rows2[1:] if len(r) == len(header2)][0]

print("Header 1 len:", len(header1), "Val 1 len:", len(val1))
print("Header 2 len:", len(header2), "Val 2 len:", len(val2))

# Create dictionaries
d1 = dict(zip(header1, val1))
d2 = dict(zip(header2, val2))

print("\nProduct 1:", d1.get("Codice_univoco__c"), d1.get("Name"))
print("Product 2:", d2.get("Codice_univoco__c"), d2.get("Name"))

# Let's inspect CodCond columns
codcond_cols = [c for c in header1 if 'CodCond' in c]
print(f"Total CodCond columns: {len(codcond_cols)}")

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

print("\n--- DIFFERENZE CALCOLATE ---")
for grp, items in groups.items():
    print(f"\n=== {grp} ===")
    for field, desc in items:
        v1 = float(d1[field])
        v2 = float(d2[field])
        diff = v2 - v1
        diff_pct = (diff / v1) * 100
        sign = '+' if diff > 0 else ''
        print(f"{desc:48} | VARD: {v1:10.2f} € | VOMB: {v2:10.2f} € | Delta: {sign}{diff:8.2f} € ({sign}{diff_pct:+.2f}%)")

print("\n--- PARAMETRI CHIAVE ---")
for k in [
    'Quota_Comm_fissa_dom_ENGIE_Luce__c', 'Quota_Comm_fissa_domestico_ENGIE_Gas__c',
    'Quota_Comm_fissa_altri_usi_BT_ENGIE_Luce__c', 'Quota_Comm_fissa_altri_usi_ENGIE_Gas__c',
    'Spread_luce__c', 'Spread_luce_lordo_perdite__c', 'Spread_F1__c', 'Spread_F2__c', 'Spread_F3__c',
    'Spread_gas__c', 'Quota_Comm_variabile_dom_ENGIE_Gas__c', 'Quota_Comm_variabile_altri_usi_ENGIE_Gas__c',
    'Dispacciamento__c', 'Quota_Dispacciamento_Forfettario_kWh__c'
]:
    print(f"{k:45}: VARD={d1.get(k)} | VOMB={d2.get(k)}")
