"""
Script per aggiungere i campi scenario_normativo e supera_limite_50
alla tabella extra_costi_sicurezza e aggiornare le funzioni correlate
"""

# =============================================
# 1. MIGRATION DATABASE
# =============================================

def migrazione_aggiungi_campi_scenario():
    """
    Aggiunge i campi scenario_normativo e supera_limite_50 
    alla tabella extra_costi_sicurezza
    
    DA ESEGUIRE UNA SOLA VOLTA
    """
    import sqlite3
    
    DB_PATH = 'duvri.db'  # Modifica se necessario
    
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        print("🔧 Inizio migrazione database...")
        
        # Aggiungi colonna scenario_normativo
        try:
            c.execute("""
                ALTER TABLE extra_costi_sicurezza 
                ADD COLUMN scenario_normativo TEXT
            """)
            conn.commit()
            print("✅ Colonna 'scenario_normativo' aggiunta con successo")
        except sqlite3.OperationalError as e:
            if 'duplicate column' in str(e).lower():
                print("ℹ️ Colonna 'scenario_normativo' già esistente")
            else:
                raise
        
        # Aggiungi colonna supera_limite_50
        try:
            c.execute("""
                ALTER TABLE extra_costi_sicurezza 
                ADD COLUMN supera_limite_50 INTEGER DEFAULT 0
            """)
            conn.commit()
            print("✅ Colonna 'supera_limite_50' aggiunta con successo")
        except sqlite3.OperationalError as e:
            if 'duplicate column' in str(e).lower():
                print("ℹ️ Colonna 'supera_limite_50' già esistente")
            else:
                raise
        
        # Aggiungi colonna importo_totale se non esiste
        try:
            c.execute("""
                ALTER TABLE extra_costi_sicurezza 
                ADD COLUMN importo_totale REAL
            """)
            conn.commit()
            print("✅ Colonna 'importo_totale' aggiunta con successo")
        except sqlite3.OperationalError as e:
            if 'duplicate column' in str(e).lower():
                print("ℹ️ Colonna 'importo_totale' già esistente")
            else:
                raise
        
        conn.close()
        print("✅ Migrazione completata con successo!")
        return True
        
    except Exception as e:
        print(f"❌ Errore durante la migrazione: {e}")
        import traceback
        traceback.print_exc()
        return False


# =============================================
# 2. AGGIORNAMENTO FUNZIONE gestione_extra_costi
# =============================================

"""
SOSTITUISCI la funzione gestione_extra_costi in app.py con questa versione aggiornata:
"""

def gestione_extra_costi_AGGIORNATA(duvri_id):
    """
    Pagina gestione extra-costi e integrazione contrattuale.
    VERSIONE AGGIORNATA con scenario_normativo
    """
    
    if session.get('current_duvri_id') != duvri_id:
        flash('Accesso negato', 'danger')
        return redirect(url_for('admin_dashboard'))
    
    # Calcola confronto costi (già include scenario_normativo)
    confronto = calcola_e_confronta_costi(duvri_id)
    
    if not confronto.get('richiede_azione'):
        flash('Nessun extra-costo rilevato', 'info')
        return redirect(url_for('summary'))
    
    # Recupera o crea extra-costo
    extra_costo = get_extra_costo(duvri_id)
    
    if not extra_costo:
        # Crea automaticamente se non esiste
        descrizione = f"Extra-costi da interferenze: incremento {confronto['percentuale_delta']:.1f}%"
        extra_id = crea_extra_costo(duvri_id, confronto['delta'], descrizione)
        
        if extra_id:
            extra_costo = get_extra_costo(duvri_id)
            print(f"✅ Extra-costo creato automaticamente: {extra_id}")
    
    # 🆕 AGGIORNA scenario_normativo e supera_limite_50
    if extra_costo and confronto.get('scenario_normativo'):
        aggiorna_extra_costo(
            duvri_id,
            scenario_normativo=confronto['scenario_normativo'],
            supera_limite_50=1 if confronto.get('supera_limite_50', False) else 0,
            importo_totale=confronto.get('totale_operativo', 0)
        )
        # Ricarica extra_costo con i nuovi dati
        extra_costo = get_extra_costo(duvri_id)
    
    return render_template('gestione_extra_costi.html',
                         duvri_id=duvri_id,
                         confronto=confronto,
                         extra_costo=extra_costo)


# =============================================
# 3. AGGIORNAMENTO FUNZIONE generate_pdf
# =============================================

"""
NELLA FUNZIONE generate_pdf, SOSTITUISCI il blocco di codice
dalle righe 2610-2630 con questo:
"""

CODICE_DA_SOSTITUIRE_IN_generate_pdf = '''
        # 🆕 Calcola confronto e extra-costo per sezione 2.6
        confronto_costi = None
        extra_costo = None
        
        # Solo se DUVRI completato con appaltatore
        if data.get('appaltatore') and data.get('appaltatore').get('max_addetti'):
            try:
                confronto_costi = calcola_e_confronta_costi(duvri_id)
                print(f"✅ Confronto costi calcolato: {confronto_costi.get('stato') if confronto_costi else 'None'}")
                
                if confronto_costi and confronto_costi.get('richiede_azione'):
                    extra_costo = get_extra_costo(duvri_id)
                    
                    # 🆕 Se extra_costo esiste, aggiorna con scenario_normativo
                    if extra_costo and confronto_costi.get('scenario_normativo'):
                        aggiorna_extra_costo(
                            duvri_id,
                            scenario_normativo=confronto_costi['scenario_normativo'],
                            supera_limite_50=1 if confronto_costi.get('supera_limite_50', False) else 0,
                            importo_totale=confronto_costi.get('totale_operativo', 0)
                        )
                        # Ricarica extra_costo con i nuovi dati
                        extra_costo = get_extra_costo(duvri_id)
                    
                    print(f"✅ Extra-costo recuperato: {bool(extra_costo)}")
                    if extra_costo:
                        print(f"   Scenario: {extra_costo.get('scenario_normativo')}")
                        print(f"   Supera limite: {extra_costo.get('supera_limite_50')}")
            except Exception as e:
                print(f"⚠️ Errore calcolo confronto costi per PDF: {e}")
        
        html_content = render_template("pdf_template.html", 
                                     data=data, 
                                     datetime=datetime,
                                     confronto_costi=confronto_costi,
                                     extra_costo=extra_costo)
'''


# =============================================
# 4. ISTRUZIONI PER L'IMPLEMENTAZIONE
# =============================================

ISTRUZIONI = """
PROCEDURA DI AGGIORNAMENTO:

1. BACKUP del database
   ----------------------
   Copia il file duvri.db prima di procedere:
   
   cp duvri.db duvri.db.backup_$(date +%Y%m%d_%H%M%S)


2. ESEGUI LA MIGRAZIONE
   ---------------------
   Apri Python nella directory del progetto e esegui:
   
   python
   >>> from migration_scenario_normativo import migrazione_aggiungi_campi_scenario
   >>> migrazione_aggiungi_campi_scenario()
   
   Oppure esegui questo script direttamente:
   
   python migration_scenario_normativo.py


3. AGGIORNA app.py
   ----------------
   Sostituisci la funzione gestione_extra_costi (riga ~2102) con la versione
   gestione_extra_costi_AGGIORNATA presente in questo file.
   
   Sostituisci il blocco di codice in generate_pdf (righe ~2610-2630) con il
   blocco presente nella variabile CODICE_DA_SOSTITUIRE_IN_generate_pdf.


4. SOSTITUISCI IL TEMPLATE
   ------------------------
   Sostituisci templates/pdf_template.html con il file pdf_template_updated.html


5. TESTA
   -----
   a) Accedi a un DUVRI esistente con extra-costi
   b) Vai su /gestione_extra_costi/<duvri_id>
   c) Verifica che venga mostrato lo scenario normativo corretto
   d) Genera il PDF
   e) Verifica che nel PDF appaia la nuova sezione 2.6.3


6. VERIFICA DATABASE
   ------------------
   Puoi verificare che i campi siano stati aggiunti con:
   
   sqlite3 duvri.db
   .schema extra_costi_sicurezza
   
   Dovresti vedere:
   - scenario_normativo TEXT
   - supera_limite_50 INTEGER DEFAULT 0
   - importo_totale REAL


RISOLUZIONE PROBLEMI:
---------------------

Problema: "Column already exists"
Soluzione: I campi sono già stati aggiunti, puoi continuare.

Problema: "Table extra_costi_sicurezza not found"
Soluzione: Esegui prima init_db() dall'app.

Problema: La sezione non appare nel PDF
Soluzione: Verifica che extra_costo.scenario_normativo sia valorizzato:
  - Vai su /gestione_extra_costi/<duvri_id> per far calcolare lo scenario
  - Controlla nel database: SELECT scenario_normativo FROM extra_costi_sicurezza WHERE duvri_id = 'xxx'

Problema: Nel PDF compare solo il box giallo ma non quello colorato
Soluzione: Lo scenario viene applicato solo quando ci sono extra-costi.
  Verifica che confronto_costi.richiede_azione sia True.
"""


# =============================================
# 5. ESECUZIONE SCRIPT
# =============================================

if __name__ == '__main__':
    print("=" * 70)
    print("MIGRATION: Aggiungi campi scenario_normativo")
    print("=" * 70)
    print()
    
    risposta = input("Vuoi procedere con la migrazione? (si/no): ")
    
    if risposta.lower() in ['si', 's', 'yes', 'y']:
        print()
        migrazione_aggiungi_campi_scenario()
        print()
        print("=" * 70)
        print("MIGRAZIONE COMPLETATA")
        print("=" * 70)
        print()
        print("PROSSIMI PASSI:")
        print(ISTRUZIONI)
    else:
        print("Migrazione annullata.")
