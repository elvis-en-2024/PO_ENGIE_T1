from playwright.sync_api import sync_playwright
import re

def run():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page(ignore_https_errors=True)
        
        # 1. Recupero PUN Stima da offerta luce Variabile
        print("Apertura Portale Offerte per Estrazione Indici...")
        pg.goto("https://www.ilportaleofferte.it/portaleOfferte/it/confronto-tariffe-prezzi-luce-gas.page", wait_until="domcontentloaded")
        
        # Compila form luce variabile
        pg.click("#energiaElettrica", force=True)
        pg.fill("#capComune", "00185") # Roma
        pg.locator(".ui-menu-item").first.wait_for()
        pg.locator(".ui-menu-item").first.click()
        pg.click("#casa", force=True)
        pg.click("#prezzoVariabile", force=True)
        pg.click("#residenteSI", force=True)
        pg.locator("a:visible").filter(has_text="Avanti").first.click()
        pg.wait_for_timeout(1000)
        pg.select_option("#scegliPotenza", "3")
        pg.select_option("#tipoTariffa", "monoraria")
        pg.click("#ferNO", force=True)
        pg.click("#consumoNO", force=True)
        pg.click("#submitSimulaLuce", force=True)
        print("Ricerca luce inviata...")
        pg.wait_for_url("**/confronto_ml.page", timeout=60000)
        pg.wait_for_load_state("load")
        
        # Clicca il primo dettaglio
        pg.locator("a.linkDettaglio").first.click()
        print("Dettaglio aperto...")
        pg.wait_for_url("**/dettaglio_offerta_ml.page", timeout=60000)
        pg.wait_for_load_state("load")
        
        # Estrai tutto il testo della pagina
        text = pg.locator("body").inner_text()
        
        # Cerca i valori dichiarati nel testo per PUN
        m = re.search(r'valore del PUN.*?((?:0|1),\d{3,6})', text, re.IGNORECASE | re.DOTALL)
        if m:
            print("PUN TROVATO NEL TESTO:", m.group(1))
        else:
            print("PUN non trovato testualmente. Cerco nella tabella...")
            righe = pg.eval_on_selector_all(
                "tr", """rs => rs.map(r => [...r.children].map(c => c.textContent.trim())
                    .filter(Boolean)).filter(c => c.length >= 2).map(c => [c[0], c[c.length-1]])""")
            for k, v in righe:
                if 'PUN' in k or 'pun' in k.lower():
                    print(k, v)
                    
        b.close()
        
if __name__ == '__main__':
    run()
