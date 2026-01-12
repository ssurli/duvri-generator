#!/usr/bin/env python3
"""
Script di diagnostica per verificare perché la sezione
Gestione Extra Costi non è visibile
"""

import sys
import os

# Aggiungi il path dell'app
sys.path.insert(0, '/home/user/duvri-generator')

from app import app, get_current_duvri_data, calcola_e_confronta_costi
import json

def diagnose():
    with app.app_context():
        # Ottieni i dati del DUVRI corrente
        try:
            data = get_current_duvri_data()

            print("=" * 70)
            print("DIAGNOSTICA GESTIONE COSTI INTERFERENTI")
            print("=" * 70)

            # Verifica sessione
            from flask import session
            duvri_id = session.get('current_duvri_id', 'Non impostato')
            print(f"\n📋 DUVRI ID corrente: {duvri_id}")

            if not duvri_id or duvri_id == 'Non impostato':
                print("\n❌ PROBLEMA: Nessun DUVRI in sessione")
                print("   Soluzione: Aprire un DUVRI esistente dalla dashboard")
                return

            # Verifica dati committente
            committente = data.get('committente', {})
            appaltatore = data.get('appaltatore', {})

            print(f"\n📝 DATI COMMITTENTE:")
            print(f"   - Tipo DUVRI: {committente.get('tipo_duvri', 'NON IMPOSTATO')}")
            print(f"   - Costi inclusi in gara: {committente.get('costi_inclusi_gara', False)}")
            print(f"   - Costi sicurezza gara: €{committente.get('costi_sicurezza_gara', 0):,.2f}")
            print(f"   - Importo gara base: €{committente.get('importo_gara_base', 0):,.2f}")
            print(f"   - Usa costi manuali: {committente.get('usa_costi_manuali', False)}")

            print(f"\n👷 DATI APPALTATORE:")
            print(f"   - Max addetti: {appaltatore.get('max_addetti', 'NON IMPOSTATO')}")
            print(f"   - Durata: {appaltatore.get('durata', 'NON IMPOSTATO')}")
            print(f"   - Costi presenti: {appaltatore.get('costi_presenti', False)}")

            # Verifica se l'appaltatore è compilato
            if not appaltatore.get('max_addetti'):
                print("\n❌ PROBLEMA: Sezione appaltatore non completata")
                print("   La gestione costi è disponibile solo per DUVRI completati")
                print("   Soluzione: Completare il form appaltatore")
                return

            # Calcola confronto costi
            print("\n💰 CALCOLO CONFRONTO COSTI...")
            try:
                confronto = calcola_e_confronta_costi(duvri_id)

                print(f"\n📊 RISULTATO CONFRONTO:")
                print(f"   - Tipo: {confronto.get('tipo')}")
                print(f"   - Stato: {confronto.get('stato')}")
                print(f"   - Costi operativi totali: €{confronto.get('totale_operativo', 0):,.2f}")
                print(f"   - Costi da gara: €{confronto.get('costi_gara', 0):,.2f}")
                print(f"   - Delta: €{confronto.get('delta', 0):,.2f}")
                print(f"   - Scenario normativo: {confronto.get('scenario_normativo', 'NESSUNO')}")
                print(f"   - Richiede azione: {confronto.get('richiede_azione')}")
                print(f"   - Azione richiesta: {confronto.get('azione_richiesta', 'NESSUNA')}")
                print(f"\n💬 Messaggio: {confronto.get('messaggio')}")

                # DIAGNOSTICA SPECIFICA
                print("\n" + "=" * 70)
                if confronto.get('richiede_azione'):
                    print("✅ SEZIONE GESTIONE COSTI DOVREBBE ESSERE VISIBILE")
                    print(f"   Il link dovrebbe apparire nel summary con il testo:")
                    print(f"   '📋 Gestisci Integrazione Contrattuale'")
                else:
                    print("❌ SEZIONE GESTIONE COSTI NON VISIBILE")
                    print("\n🔍 MOTIVO:")

                    if confronto.get('tipo') == 'RICOGNITIVO':
                        print("   - DUVRI di tipo RICOGNITIVO (per documenti di gara)")
                        print("   - Questa tipologia non richiede gestione extra-costi")
                        print("\n💡 SOLUZIONE:")
                        print("   - Cambiare tipo DUVRI in 'OPERATIVO' se i lavori sono iniziati")
                        print("   - Oppure completare prima la gara e poi compilare il DUVRI operativo")

                    elif confronto.get('stato') == 'NESSUN_COSTO':
                        print("   - Nessun costo operativo rilevato (€0)")
                        print("\n💡 SOLUZIONE:")
                        print("   - Verificare che siano stati compilati i dati appaltatore")
                        print("   - Controllare durata lavori e numero addetti")
                        print("   - Se necessario, usare 'costi manuali' dal form committente")

                    elif confronto.get('stato') == 'RISPARMIO':
                        print("   - I costi operativi sono INFERIORI a quelli previsti in gara")
                        print(f"   - Risparmio di €{confronto.get('delta', 0):,.2f}")
                        print("\n💡 SOLUZIONE:")
                        print("   - Questo è positivo! Non serve integrazione contrattuale")
                        print("   - I costi previsti in gara coprono quelli effettivi")

                    elif confronto.get('stato') == 'CONFERMATO':
                        print("   - I costi operativi corrispondono esattamente a quelli di gara")
                        print("\n💡 SOLUZIONE:")
                        print("   - Nessuna azione necessaria")
                        print("   - I costi sono perfettamente in linea con le previsioni")

                    else:
                        print(f"   - Stato: {confronto.get('stato')}")
                        print(f"   - Condizione non gestita, verificare i dati")

                print("=" * 70)

                # Debug dettagliato costi operativi
                print("\n📋 DETTAGLIO COSTI OPERATIVI:")
                costi_dict = confronto.get('costi_operativi_dict', {})
                for voce, importo in costi_dict.items():
                    if voce.startswith('costo_'):
                        print(f"   - {voce}: €{importo:,.2f}")

            except Exception as e:
                print(f"\n❌ ERRORE nel calcolo confronto costi:")
                print(f"   {str(e)}")
                import traceback
                traceback.print_exc()

        except Exception as e:
            print(f"\n❌ ERRORE nell'ottenere i dati DUVRI:")
            print(f"   {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    diagnose()
