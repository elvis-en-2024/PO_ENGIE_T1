from playwright.sync_api import sync_playwright
import re
import json
import logging

def estrai_indici():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page(ignore_https_errors=True)
        
        # 1. Recupero PUN Stima da offerta luce Variabile
        print("[1/2] Estrazione PUN (Luce)...")
        pg.goto("https://www.ilportaleofferte.it/portaleOfferte/it/confronto-tariffe-prezzi-luce-gas.page", wait_until="domcontentloaded", timeout=90000)
        
        pg.click("#energiaElettrica", force=True)
        print("energiaElettrica clicked")
        pg.locator("#capComune").fill("")
        pg.locator("#capComune").type("20121", delay=100) # Milano
        print("cap filled")
        pg.locator(".ui-menu-item").first.wait_for(timeout=15000)
        pg.locator(".ui-menu-item").first.click()
        print("cap selected")
        pg.locator("#casa").wait_for(state="visible", timeout=45000)
        pg.click("#casa", force=True)
        pg.click("#prezzoVariabile", force=True)
        pg.click("#residenteSI", force=True)
        pg.locator("a:visible").filter(has_text="Avanti").first.click()
        print("Avanti clicked")
        pg.wait_for_timeout(1500)
        
        pg.select_option("#scegliPotenza", "3")
        pg.select_option("#tipoTariffa", "monoraria")
        pg.click("#ferNO", force=True)
        pg.click("#consumoSI", force=True)
        pg.wait_for_timeout(800)
        pg.fill("#ConsumoAnnuo", "2700")
        pg.locator("#ConsumoAnnuo").dispatch_event("keyup")
        
        pg.locator("input[name=confronta]:visible").click()
        pg.wait_for_url("**/confronta_offerte.page*", timeout=120000)
        pg.wait_for_load_state("domcontentloaded")
        
        # Filtriamo per offerte PLACET così siamo sicuri del calcolo pulito
        pg.locator(".linkDettaglio").first.click()
        print("      > Dettaglio cliccato...")
        pg.locator("text=Spesa").first.wait_for(state="visible", timeout=90000)
        print("      > Dettaglio aperto, analisi testo...")
        
        text = pg.locator("body").inner_text()
        
        # Cerca la riga della tabella o testo limitato
        m_pun = re.search(r'PUN.{0,100}?(0,\d{4,6})\b', text, re.IGNORECASE | re.DOTALL)
        pun_val = None
        if m_pun:
            pun_val = float(m_pun.group(1).replace(",", "."))
            print(f"      > Trovato PUN ufficiale dichiarato: {pun_val}")
        else:
            print("      ! PUN testuale non trovato.")
            
        b.close()
        
    # Ripetiamo per il GAS
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page(ignore_https_errors=True)
        
        print("\n[2/2] Estrazione PSV (Gas)...")
        pg.goto("https://www.ilportaleofferte.it/portaleOfferte/it/confronto-tariffe-prezzi-luce-gas.page", wait_until="domcontentloaded", timeout=90000)
        
        pg.click("#gas", force=True)
        pg.locator("#capComune").fill("")
        pg.locator("#capComune").type("20121", delay=100) # Milano
        pg.locator(".ui-menu-item").first.wait_for(timeout=15000)
        pg.locator(".ui-menu-item").first.click()
        pg.locator("#casa").wait_for(state="visible", timeout=45000)
        pg.click("#casa", force=True)
        pg.click("#prezzoVariabile", force=True)
        pg.locator("a:visible").filter(has_text="Avanti").first.click()
        pg.wait_for_timeout(1500)
        
        pg.locator("#scegliClasse").wait_for(state="visible", timeout=20000)
        pg.select_option("#scegliClasse", "1")
        pg.click("label[for=riscaldamento]", force=True)
        pg.click("label[for=cottura]", force=True)
        pg.click("label[for=acquaCalda]", force=True)
        
        pg.click("#consumoGasSI", force=True)
        pg.locator("#ConsumoAnnuoGas").wait_for(state="visible", timeout=10000)
        pg.fill("#ConsumoAnnuoGas", "1400")
        pg.locator("#ConsumoAnnuoGas").dispatch_event("keyup")
        
        pg.locator("input[name=confronta]:visible").click()
        pg.wait_for_url("**/confronta_offerte.page*", timeout=120000)
        pg.wait_for_load_state("domcontentloaded")
        
        pg.locator(".linkDettaglio").first.click()
        print("      > Dettaglio cliccato...")
        pg.locator("text=Spesa").first.wait_for(state="visible", timeout=90000)
        print("      > Dettaglio aperto, analisi testo...")
        
        text_gas = pg.locator("body").inner_text()
        
        # Cerca PSV
        m_psv = re.search(r'PSV.{0,100}?(0,\d{4,6})\b', text_gas, re.IGNORECASE | re.DOTALL)
        psv_val = None
        if m_psv:
            psv_val = float(m_psv.group(1).replace(",", "."))
            print(f"      > Trovato PSV ufficiale dichiarato: {psv_val}")
        else:
            print("      ! PSV testuale non trovato.")
            
        b.close()
        
    print("\n--- RISULTATO ESTRAZIONE UFFICIALE PORTALE OFFERTE ---")
    print(f"PUN (Stima): {pun_val}")
    print(f"PSV (Stima): {psv_val}")
    
    with open("data/raw/indici_ufficiali_po.json", "w") as f:
        json.dump({"PUN": pun_val, "PSV": psv_val}, f, indent=4)
        
if __name__ == '__main__':
    estrai_indici()
