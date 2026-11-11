from playwright.sync_api import sync_playwright
import re
import json

def run():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page(ignore_https_errors=True)
        print("Apertura Portale Offerte Luce...")
        pg.goto("https://www.ilportaleofferte.it/portaleOfferte/it/confronto-tariffe-prezzi-luce-gas.page", wait_until="domcontentloaded")
        pg.click("#energiaElettrica", force=True)
        pg.locator("#capComune").fill("")
        pg.locator("#capComune").type("20121", delay=100) # Milano
        pg.locator(".ui-menu-item").first.wait_for(timeout=15000)
        pg.locator(".ui-menu-item").first.click()
        pg.locator("#casa").wait_for(state="visible", timeout=45000)
        pg.click("#casa", force=True)
        pg.click("#prezzoVariabile", force=True)
        pg.click("#residenteSI", force=True)
        pg.locator("a:visible").filter(has_text="Avanti").first.click()
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
        
        # Invece di usare il click di playwright, usa evaluate come in rileva_componenti
        print("Ricerca completata, apro il dettaglio della prima offerta tramite JS...")
        successo = pg.evaluate("""() => {
            const btn = document.querySelector('a.linkDettaglio');
            if (btn) { btn.click(); return true; }
            return false;
        }""")
        
        if successo:
            pg.wait_for_url("**/dettaglio_offerta_ml.page*", timeout=120000)
            pg.wait_for_load_state("domcontentloaded")
            text = pg.evaluate("document.body.innerText")
            m = re.search(r'PUN.{0,100}?(0,\d{4,6})', text, re.IGNORECASE | re.DOTALL)
            pun_val = float(m.group(1).replace(",", ".")) if m else None
            print("PUN TROVATO:", pun_val)
        else:
            print("Nessuna offerta trovata")
            
        b.close()
        
if __name__ == '__main__':
    run()
