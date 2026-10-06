# Logiche e Ostacoli Superati nella Fase 1 (Scraping Documenti)

Questo documento traccia l'architettura mentale e tecnica del crawler sviluppato per superare le pesanti difese anti-scraping dei vari fornitori energetici italiani. Molti di essi, infatti, non espongono semplicemente file `<a href="file.pdf">` nell'HTML per scoraggiare i bot, ma utilizzano DAM, portali CMS dinamici (AEM, Liferay) e link offuscati.

Ecco come è stato risolto il problema fornitore per fornitore.

## 1. I Provider Standard (Enel, Plenitude, Octopus, ecc.)
Per la maggioranza del mercato, il crawler base in `requests` + `BeautifulSoup` (`crawler_ctes.py`) è sufficiente. Il sistema analizza la pagina index, ricava i link delle singole offerte, ci naviga dentro, e tramite Regex cerca link che terminano in `.pdf` estrapolando dal testo o dall'URL se il file è una *Scheda Sintetica* (SS) o *Condizione Tecnico Economica* (CTE).

## 2. A2A (L'ecosistema Salesforce)
**Problema:** A2A ospita i suoi documenti su un'istanza Salesforce (Salesforce Content Delivery). I link sono formattati come `https://a2aenergia.my.salesforce.com/sfc/p/...` e **non esistono nell'HTML visibile**.
**Soluzione:** A2A inserisce questi link sotto forma di una stringa JSON nascosta dentro un tag `<script>` o un data-attribute. La Regex è stata potenziata in `crawler_ctes.py` per scansionare il raw HTML a caccia di chiavi come `"url_scheda_sintetica":"..."`. I link vengono ricostruiti e scaricati. 

## 3. ACEA (Adobe Experience Manager)
**Problema:** Acea usa AEM. I link ai documenti non finiscono per `.pdf`, ma si presentano come `https://my.acea.it/visualizzaDocumento/?if=...`.
**Soluzione:** È stata aggiunta una whitelist in `is_valid_cte_pdf()` affinché riconosca `visualizzadocumento` come un PDF valido anche in assenza di un'estensione esplicita nel file, assegnandolo a CTE o SS in base al testo cliccato.

## 4. E.ON (Web Components)
**Problema:** E.ON usa un tag custom HTML (`<eon-ui-link href="...">`) al posto del classico tag `<a>`. Uno scraper BeautifulSoup tradizionale basato su `find_all('a')` restituiva 0 risultati.
**Soluzione:** Abbiamo istruito BeautifulSoup a cercare *qualsiasi* tag che possieda l'attributo `href` (`soup.find_all(href=True)`), superando l'astrazione dei Web Components.

## 5. EDISON (Il DAM Inaccessibile)
**Problema:** Edison non espone PDF standard. Carica le risorse (immagini e PDF) interrogando un'API DAM interna. Se interroghi i link visibili (`/renditions/...?binary=true`) ricevi solo immagini di anteprima. I veri PDF sono nascosti in un blocco dati con pattern `/getbusinessdoc.ashx?id=...`.
**Soluzione:** Abbiamo esteso il parse dei JSON embedded in pagina per tracciare la chiave `DocumentLink` anziché il semplice `url`. Intercettando l'URL con l'estensione `.ashx` e passandolo a `requests`, il server restituisce il vero PDF. Questo ha sbloccato oltre 150 file in un solo colpo in `crawler_ctes.py`.

## 6. HERA COMM (Portali Liferay Dinamici)
**Problema:** Hera Comm utilizza Liferay Portal. Il blocco "Documenti" non esiste nell'HTML statico iniziale. Viene renderizzato solo dopo il caricamento della pagina da un framework JS che esegue chiamate a `/api/jsonws/invoke`. In aggiunta, i nomi dei file non contengono le parole "sintetica" o "cte", ma si chiamano `Allegato Nuovi clienti_Casa_ELE_V1.pdf` oppure sono dentro file `.zip`.
**Soluzione:** `requests` è inutile qui. È stato creato uno scraper ad hoc in Playwright (`scripts/hera_scraper.py`). Il bot apre Chromium, naviga alla pagina, attende l'evento `networkidle` (o timeout di render), estrae il DOM interamente reidratato dal JS e cerca i link a `/documents/`. Provvede poi al download sia dei `.pdf` che dei file compressi `.zip`.

## 7. IREN (Obfuscazione Semantica)
**Problema:** Iren mette i PDF in pagina, ma rimuove completamente le parole chiave ("Condizioni", "CTE", "Scheda Sintetica") dai link. Esempio reale: `iren_web_self_luce_prezzo_fisso_240826.pdf`. Inoltre il pulsante per scaricare riporta unicamente la scritta neutra "Visualizza". Questo mandava in tilt i nostri filtri di qualifica dei PDF.
**Soluzione:** Modificata la funzione `is_valid_cte_pdf()` nel crawler principale. Se il link contiene il dominio "iren" e il testo associato è "visualizza", bypassiamo il filtro stringente e scarichiamo forzatamente il documento. Questo ha sbloccato l'estrazione di oltre 400 PDF.

## 8. POSTE ITALIANE (Hosting Multi-dominio)
**Problema:** Il link principale `poste.it/prodotti/energia.html` è un reindirizzamento. La pagina vera dell'offerta risiede su `postepay.poste.it`. Anche qui i PDF sono caricati dinamicamente, e soprattutto ospitati su un terzo server (`media.poste.it`) senza estensione `.pdf`.
**Soluzione:** Creato lo scraper in Playwright `scripts/poste_scraper.py`. Il bot attende l'evento `domcontentloaded`, preleva tutti i link in pagina puntati al dominio `media.poste.it` e filtra il testo del pulsante per intercettare esplicitamente "Condizioni Tecnico Economiche" e "Scheda Sintetica".
