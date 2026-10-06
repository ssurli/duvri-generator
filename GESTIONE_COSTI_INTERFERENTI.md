# Gestione Costi Interferenti (DUVRI)

Nota tecnica che riassume **come il sistema gestisce i costi della sicurezza da
interferenze**: modalità di calcolo, scenari normativi, dove i costi vengono
mostrati, quali campi sono obbligatori e le **limitazioni note** (in particolare
il caso multi‑sede).

> Riferimenti normativi: art. 26 D.Lgs. 81/08 (DUVRI e costi non soggetti a
> ribasso) e art. 120 D.Lgs. 36/2023 (varianti / atto aggiuntivo).

---

## 1. Le tre modalità di calcolo (scelte dal Committente)

Campo `modalita_costi` nel form Committente (`templates/committente_form.html`),
salvato in `committente_data`:

| Modalità | Come si ottiene l'importo | Campi operativi appaltatore |
|---|---|---|
| **Automatico** (default) | Calcolo parametrico da importo appalto + n° addetti + durata + rischi | **Obbligatori** |
| **Manuale per voce** (`usa_costi_manuali=true`) | Il committente inserisce le singole voci | Opzionali |
| **Forfettario da gara** | Usa l'importo `costi_sicurezza_gara` dichiarato nei documenti di gara | Opzionali |

Solo la modalità **Automatico** usa `max_addetti` e `durata_giorni`: le altre
due prendono l'importo da input del committente. Vedi §5.

---

## 2. Calcolo automatico — `calcola_costi_sicurezza(data)` (`app.py`)

Componenti del `totale_operativo` (calcolo parametrico):

- **Costo base**: `max(importo_appalto × %base, 500)`; `%base` = `percentuale_costo_base`
  (default **2%**, limitata tra 0% e 3%).
- **Per lavoratore** × `max_addetti`: DPI base 150 + DPI per rischio (mappa rischi→€)
  + formazione 200 + sorveglianza sanitaria 150 (se rischi sanitari).
- **Per rischio** (committente + appaltatore): impiantistica / controlli / segnaletica
  / presidi / altre misure (mappa `COSTI_RISCHIO`).
- **Per durata**: `n_incontri = max(1, durata_giorni // 5)` → costo incontri;
  `n_controlli = max(1, durata_giorni // 10)` → costo controlli periodici.

**Default di sicurezza** se un parametro manca/non valido: importo → 5.000,
lavoratori → 1, durata → 5 giorni. (Rilevante solo in modalità Automatico; nelle
altre non incide, vedi §5.)

---

## 3. Scenari normativi — `calcola_e_confronta_costi(duvri_id)` (`app.py`)

Input rilevanti dal committente: `tipo_duvri`, `costi_inclusi_gara` (checkbox),
`costi_sicurezza_gara` (importo), `importo_gara_base`, e il `totale_operativo`
calcolato al §2.

Soglie configurabili in `config_scenario.py`:
- `SOGLIA_COMPENSAZIONE_EURO` = **€1.000**
- `SOGLIA_COMPENSAZIONE_PERCENTUALE` = **3%** (sul contratto)
- `LIMITE_MASSIMO_PERCENTUALE` = **50%** (limite art. 120)

### Instradamento

| Condizione | Scenario | `stato` | Esito |
|---|---|---|---|
| `tipo_duvri == 'ricognitivo'` | Ricognitivo | `PRIMO_CALCOLO` | Stima per documenti di gara, nessuna azione |
| `costi_inclusi_gara` **e** `costi_sicurezza_gara == 0` | **2 — Inclusi ma compensati** | vedi sotto | Compensazione o atto aggiuntivo |
| `not costi_inclusi_gara` **o** `costi_sicurezza_gara == 0` | **3 — Non previsti in gara** | `EXTRA_COSTI_TOTALI` / `NESSUN_COSTO` | Tutto extra → atto aggiuntivo |
| `costi_inclusi_gara` **e** `costi_sicurezza_gara > 0` | **4 — Previsti ed evidenziati** | confronto delta | Extra / risparmio / confermato |

### Scenario 2 (inclusi ma compensati) in dettaglio
- `totale_operativo == 0` → `NESSUN_COSTO` (nessuna azione).
- `totale_operativo > 0`:
  - **sotto almeno una soglia** (< €1.000 **oppure** < 3%) → `COSTI_COMPENSATI`
    → compensazione interna con **verbale RUP/Appaltatore** (`richiede_azione`).
  - **sopra entrambe le soglie** → `EXTRA_COSTI` → **atto aggiuntivo art. 120**;
    flag `supera_limite_50` se la % sul contratto supera il 50%.

### Scenario 4 (previsti ed evidenziati) in dettaglio
`delta = totale_operativo − costi_sicurezza_gara`:
- `delta > 0` → `EXTRA_COSTI` (atto aggiuntivo se `delta` sul appalto > 50%).
- `delta < 0` → `RISPARMIO`.
- `delta == 0` → `CONFERMATO`.

---

## 4. Dove e quando compaiono i costi

- **Salvataggio appaltatore** — `salva_dati_appaltatore_unificato()`: il calcolo
  automatico parte **solo se** ci sono importo + `max_addetti` + `durata_giorni`
  **e** non è attiva la modalità manuale del committente né una modifica manuale
  dell'appaltatore. Altrimenti viene saltato (non è un errore).
- **Riepilogo** — route `/summary` + `templates/summary.html`: card indipendente
  "Costi di Sicurezza da Interferenze".
  - In **Forfettario/Manuale** l'importo è definito dal committente → mostrato
    **subito**, anche prima che l'appaltatore compili.
  - In **Automatico** senza dati appaltatore → pannello "in attesa" che elenca
    cosa manca (nessun numero fittizio).
  - Il box di **confronto** (`confronto_costi`) compare solo dopo che l'appaltatore
    ha compilato (serve `max_addetti`).
- **PDF** — `templates/pdf_template.html`: riporta il calcolo, il confronto e lo
  scenario normativo. Reso robusto ai campi operativi vuoti.

---

## 5. Campi operativi obbligatori: `max_addetti` e `durata_giorni`

Questi due campi (form appaltatore, sezione "Parametri Operativi") **alimentano
solo il calcolo automatico** (§2). Regola di obbligatorietà — `valida_dati_appaltatore(richiedi_operativi)`:

| Modalità costi committente | `max_addetti` / `durata_giorni` |
|---|---|
| **Automatico** (o modalità non ancora scelta) | **Obbligatori** |
| **Forfettario / Manuale** | **Opzionali** |

La route esterna `appaltatore_form` deduce la modalità dal committente e la passa
alla validazione e al template (attributo `required`, asterisco, testi d'aiuto
condizionali). Se la modalità è ignota → default `automatico` → comportamento
storico invariato.

Nel PDF, se lasciati vuoti: durata → *"secondo contratto (continuativa / giornate
variabili)"*, addetti → *"Variabile / non applicabile"*.

---

## 6. ⚠️ LIMITAZIONE NOTA — operatività su più sedi (multi‑sede)

**Lo sblocco dell'obbligatorietà di `max_addetti`/`durata_giorni` è legato alla
MODALITÀ COSTI, non al flag multi‑sede.**

Conseguenza pratica:

- Se il committente è in **Forfettario/Manuale** → i campi operativi sono già
  opzionali (indipendentemente dal multi‑sede). ✅
- Se il committente è in **Automatico** e ha spuntato **"operatività su più sedi"**
  (`multi_sede` / `sedi_operative`, province Lucca / Versilia / Massa / Pisa /
  Livorno) → i campi operativi **restano obbligatori**, perché il calcolo
  parametrico ha comunque bisogno di quei numeri. In questo caso:
  - "Numero massimo addetti contemporaneamente presenti" e una "durata in giorni"
    unica **possono perdere di significato** (es. contratto di assistenza
    pluriennale con giornate variabili, o presenza distribuita su più sedi).

### Indicazione operativa
Per contratti **multi‑sede** o **pluriennali/continuativi** usare la modalità
**Forfettario** (importo da gara) o **Manuale**: sono il "vestito" corretto per
questi appalti, perché il costo non deriva dalla formula `addetti × durata`.

### Possibile estensione futura (NON implementata)
Rendere opzionali `max_addetti`/`durata_giorni` **anche** quando `multi_sede` è
attivo, pur restando in Automatico. Compromesso: in quel caso il calcolo userebbe
i default (1 lavoratore / 5 giorni), producendo un costo **indicativo e non
reale** in modo silenzioso. Per questo al momento **non** è stato fatto: la scelta
è di forzare l'uso della modalità corretta (forfettario/manuale) per quei
contratti. Da rivalutare se emergesse l'esigenza operativa.

---

## 7. Riferimenti nel codice

| Cosa | File / funzione |
|---|---|
| Modalità costi (radio) | `templates/committente_form.html` (`modalita_costi`) |
| Calcolo parametrico | `app.py` → `calcola_costi_sicurezza()` |
| Scenari normativi | `app.py` → `calcola_e_confronta_costi()` |
| Soglie / limite art. 120 | `config_scenario.py` (`ConfigScenarioNormativo`) |
| Auto‑calcolo al salvataggio | `app.py` → `salva_dati_appaltatore_unificato()` |
| Obbligatorietà condizionale | `app.py` → `valida_dati_appaltatore(richiedi_operativi)` + route `appaltatore_form` |
| Parametri operativi (form) | `templates/appaltatore_form.html` (sezione "Parametri Operativi") |
| Visualizzazione riepilogo | route `/summary` + `templates/summary.html` |
| Preparazione dati PDF | `app.py` → `prepara_dati_per_pdf()` + `templates/pdf_template.html` |
| Multi‑sede (campi) | `committente_form.html` / `app.py` (`multi_sede`, `sedi_operative`) |

> I nomi di funzione sono il riferimento stabile; i numeri di riga possono
> cambiare nel tempo.
