import pandas as pd

F1 = 891
F2 = 837
F3 = 972
F23 = F2 + F3
TOT_CONS = 2700
POTENZA = 3

dist_fix = 23.04
trasp_pot = 23.52
qual_pot = 0.1988
misura_vol = 0.0119
pereq_vol = 0.00276
qual_vol = 0.00007

asos_vol = 0.031515
arim_vol = 0.001638

df = pd.read_csv('data/storage/verifica_piatta_20260820.csv', dtype=str)
offer = df[df['NOME_OFFERTA'] == 'E.ON LuceClick biorariaVerde'].iloc[0]

quota_fissa = float(offer['COMP_IMP_2_INT_1_PREZZO'])
prezzo_f1 = float(offer['COMP_IMP_1_INT_1_PREZZO'])
prezzo_f23 = float(offer['COMP_IMP_1_INT_2_PREZZO'])
cdispd = 0.024

vendita_fissa = quota_fissa
vendita_energia = (prezzo_f1 * F1) + (prezzo_f23 * F23) + (cdispd * TOT_CONS)
tot_vendita = vendita_fissa + vendita_energia

reti_fissa = dist_fix
reti_pot = (trasp_pot + qual_pot) * POTENZA
reti_energia = (misura_vol + pereq_vol + qual_vol) * TOT_CONS
tot_reti = reti_fissa + reti_pot + reti_energia

tot_oneri = (asos_vol + arim_vol) * TOT_CONS

accise = 21.79 

tot_netto = tot_vendita + tot_reti + tot_oneri + accise
iva = tot_netto * 0.10
tot_sas = tot_netto + iva

print("--- SIMULAZIONE E.ON ---")
print(f"Vendita: {tot_vendita:.2f} (HTML: 467.01)")
print(f"Reti: {tot_reti:.2f} (HTML: 133.97)")
print(f"Oneri: {tot_oneri:.2f} (HTML: 89.51)")
print(f"Imposte: {accise:.2f} (HTML: 21.79)")
print(f"Netto: {tot_netto:.2f} (HTML: 690.49)")
print(f"IVA: {iva:.2f} (HTML: 71.23)")
print(f"SAS: {tot_sas:.2f} (HTML: 783.51)")
