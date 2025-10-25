# =============================================
# IMPORTS
# =============================================
from flask import Flask, render_template, request, redirect, url_for, send_file, session, flash, current_app, make_response
from datetime import datetime, timedelta
import sqlite3
import uuid
import copy
import os
import json
import secrets
import io
import PyPDF2
import base64
from werkzeug.utils import secure_filename
from pathlib import Path

# =============================================
# CONFIGURAZIONE PERCORSI PER PYTHONANYWHERE
# =============================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# =============================================
# CONFIGURAZIONE PDF
# =============================================
try:
    from xhtml2pdf import pisa
    XHTML2PDF_AVAILABLE = True
except ImportError:
    XHTML2PDF_AVAILABLE = False

try:
    from weasyprint import HTML
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False

# =============================================
# INIZIALIZZAZIONE APP
# =============================================
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-development-key')

# Aggiungi dopo la secret key
app.config.update(
    SESSION_COOKIE_SECURE=os.environ.get('FLASK_ENV') == 'production',
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=24),
    MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB max upload
)

# =============================================
# PERCORSI ASSOLUTI (PythonAnywhere compatibili)
# =============================================
# DATA_FILE = os.path.join(BASE_DIR, "data", "duvri_data.json")# per far sì che vada solo su duvri.db
# TOKENS_FILE = os.path.join(BASE_DIR, "data", "access_tokens.json")#
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads", "ditte")
ALLEGATI_FOLDER = os.path.join(BASE_DIR, "uploads", "allegati")
# Database "in memoria" per i DUVRI
duvri_list = {}

# Configurazione directory
app.template_folder = os.path.join(BASE_DIR, 'templates')
app.static_folder = os.path.join(BASE_DIR, 'static')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ALLEGATI_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Crea le directory necessarie
for directory in [
    os.path.join(BASE_DIR, 'data'),
    os.path.join(BASE_DIR, 'output'),
    os.path.join(BASE_DIR, 'templates'),
    os.path.join(BASE_DIR, 'static/css'),
    UPLOAD_FOLDER,
    ALLEGATI_FOLDER,  # ✅ Aggiungi allegati
    os.path.join(BASE_DIR, 'documents')
]:
    os.makedirs(directory, exist_ok=True)



# =============================================
# COSTANTI E LISTE RISCHI
# =============================================

RISCHI_PARAGRAFI = {
    "3.3.1": "Uso cannello ossiacetilenico e fiamma libera",
    "3.3.2": "Uso e stoccaggio di prodotti chimici",
    "3.3.3": "Verniciatura",
    "3.3.4": "Idropulizia",
    "3.3.5": "Lavori in quota",
    "3.3.6": "Uso di attrezzature elettriche portatili o fisse",
    "3.3.7": "Lavoro su scala",
    "3.3.8": "Uso utensili (trapanatura, avvitatori, seghetti alternativi, ecc.)",
    "3.3.9": "Molatura/smerigliatura",
    "3.3.10": "Pulizia ordinaria",
    "3.3.11": "Pulizia mediante macchina su ruota",
    "3.3.12": "Saldatura",
    "3.3.13": "Movimentazione carichi con Transpallet o su ruote",
    "3.3.14": "Movimentazione manuale dei carichi",
    "3.3.15": "Lavori su impianti fissi (elettrici, gas medicali ecc.)",
    "3.3.16": "Lavori su impianti idrici",
    "3.3.17": "Utilizzo di attrezzature da giardinaggio",
    "3.3.18": "Utilizzo motosega",
    "3.3.19": "Refilling Azoto e fluidi criogenici",
    "3.3.20": "Movimentazione e stoccaggio rifiuti speciali",
    "3.3.21": "Movimentazione carichi con gru su autocarro",
    "3.3.22": "Attacco bombola gas alle linee",
    "3.3.23": "Sostituzione filtri (condizionatori, cappe, UTA ecc.)",
    "3.3.24": "Utilizzo di mezzi mobili per attività sanitaria",
    "3.3.25": "Attività assistenziali varie"
}

RISCHI_HTA = [
    "Installazione su quadri elettrici in tensione",
    "Collegamento a sistemi di alimentazione critica (UPS)",
    "Test di continuità e isolamento elettrico",
    "Installazione cablaggi dati e alimentazione",
    "Lavori in sale CED/server room climatizzate",
    "Installazione sistemi di raffreddamento dedicati",
    "Radiazioni ionizzanti (TAC)",
    "Radiazioni non ionizzanti (RMN, laser)",
    "Interferenze con attività sanitarie/mediche"
]

RISCHI_COMMITTENTE = [
    "Presenza di gas medicinali (ossigeno, azoto, ecc.)",
    "Apparecchiature elettromedicali in funzione",
    "Ambienti sterili/sale operatorie nelle vicinanze",
    "Sistemi antincendio automatici attivi",
    "Impianti di condizionamento e ventilazione controllata, UTA",
    "Aree con radiazioni ionizzanti (Tac, Radiologia, Medicina nucleare)",
    "Aree con presenza di campi elettromagnetici (Rmn, Laser ecc..)",
    "Presenza di sostanze chimiche (laboratori)",
    "Passaggio frequente di barelle/carrelli",
    "Accesso limitato per emergenze",
    "Impianti elettrici in tensione non sezionabili",
    "Aree soggette a controllo accessi",
    "Presenza di pazienti infettivi, aree ad alto rischio biologico",
    "Presenza di pazienti immunodepressi"
]

# =============================================
# FUNZIONI DATABASE SQLite
# =============================================
def get_db_connection():
    """Crea connessione al database SQLite"""
    db_path = os.path.join(BASE_DIR, 'duvri.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Inizializza il database per multipli DUVRI"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS duvri (
            id TEXT PRIMARY KEY,
            nome_progetto TEXT,
            link_appaltatore TEXT,
            committente_data TEXT,
            appaltatore_data TEXT,
            signatures TEXT,
            stato TEXT DEFAULT 'bozza',
            created_at TIMESTAMP,
            updated_at TIMESTAMP
        )
    ''')
    conn.commit()
    
    # 🆕 Aggiungi colonna se non esiste (per database esistenti)
    try:
        c.execute("ALTER TABLE duvri ADD COLUMN link_appaltatore TEXT")
        conn.commit()
        print("✅ Colonna link_appaltatore aggiunta")
    except:
        pass  # Colonna già esiste
    
    conn.close()

def get_current_duvri_data():
    """Ottiene i dati del DUVRI corrente"""
    duvri_id = session.get('current_duvri_id')

    if not duvri_id:
        return {"committente": {}, "appaltatore": {}, "signatures": {}}

    try:
        conn = get_db_connection()
        duvri = conn.execute('SELECT * FROM duvri WHERE id = ?', (duvri_id,)).fetchone()
        conn.close()

        if not duvri:
            return {"committente": {}, "appaltatore": {}, "signatures": {}}

        result = {
            'committente': json.loads(duvri['committente_data']) if duvri['committente_data'] else {},
            'appaltatore': json.loads(duvri['appaltatore_data']) if duvri['appaltatore_data'] else {},
            'signatures': json.loads(duvri['signatures']) if duvri['signatures'] else {},
        }
        return result

    except Exception as e:
        print(f"❌ ERRORE get_current_duvri_data: {e}")
        return {"committente": {}, "appaltatore": {}, "signatures": {}}

def save_current_duvri_data(data):
    """Salva i dati del DUVRI corrente"""
    duvri_id = session.get('current_duvri_id')

    if not duvri_id:
        return False

    try:
        conn = get_db_connection()
        
        # 🆕 Salva anche link_appaltatore se presente in memoria
        link_appaltatore = None
        if duvri_id in duvri_list:
            link_appaltatore = duvri_list[duvri_id].get('link_appaltatore')
        
        conn.execute(
            '''UPDATE duvri SET
               committente_data = ?, appaltatore_data = ?, signatures = ?, 
               link_appaltatore = ?, updated_at = ?
               WHERE id = ?''',
            (
                json.dumps(data.get('committente', {})),
                json.dumps(data.get('appaltatore', {})),
                json.dumps(data.get('signatures', {})),
                link_appaltatore,
                datetime.now(),
                duvri_id
            )
        )
        conn.commit()
        conn.close()

        sync_db_to_memory(duvri_id)
        return True

    except Exception as e:
        print(f"❌ ERRORE save_current_duvri_data: {e}")
        return False

def sync_db_to_memory(duvri_id):
    """Sincronizza i dati dal database alla memoria"""
    try:
        conn = get_db_connection()
        duvri_db = conn.execute('SELECT * FROM duvri WHERE id = ?', (duvri_id,)).fetchone()
        conn.close()

        if duvri_db and duvri_id in duvri_list:
            duvri_list[duvri_id]['dati_committente'] = json.loads(duvri_db['committente_data']) if duvri_db['committente_data'] else {}
            duvri_list[duvri_id]['dati_appaltatore'] = json.loads(duvri_db['appaltatore_data']) if duvri_db['appaltatore_data'] else {}
            duvri_list[duvri_id]['signatures'] = json.loads(duvri_db['signatures']) if duvri_db['signatures'] else {}
    except Exception as e:
        print(f"❌ ERRORE sync_db_to_memory: {e}")

def sync_all_duvri_from_db():
    """Sincronizza TUTTI i DUVRI dal database alla memoria"""
    try:
        conn = get_db_connection()
        duvri_from_db = conn.execute('SELECT * FROM duvri').fetchall()
        conn.close()

        print(f"📊 Trovati {len(duvri_from_db)} DUVRI nel database")

        for duvri_db in duvri_from_db:
            duvri_id = duvri_db['id']
            if duvri_id not in duvri_list:
                duvri_list[duvri_id] = {
                    'id': duvri_id,
                    'nome_progetto': duvri_db['nome_progetto'] or 'DUVRI Senza Nome',
                    'link_appaltatore': duvri_db['link_appaltatore'] or str(uuid.uuid4()),  # ✅ CARICA DA DB
                    'stato': duvri_db['stato'] or 'bozza',
                    'created_at': duvri_db['created_at'] or datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'dati_committente': json.loads(duvri_db['committente_data']) if duvri_db['committente_data'] else {},
                    'dati_appaltatore': json.loads(duvri_db['appaltatore_data']) if duvri_db['appaltatore_data'] else {},
                    'signatures': json.loads(duvri_db['signatures']) if duvri_db['signatures'] else {}
                }
                print(f"✅ Sincronizzato DUVRI {duvri_id} da DB a memoria")

        print(f"📊 Memoria: {len(duvri_list)} DUVRI")

    except Exception as e:
        print(f"❌ Errore sync_all_duvri_from_db: {e}")

def load_all_duvri_from_db():
    """Carica tutti i DUVRI dal database alla memoria all'avvio"""
    try:
        conn = get_db_connection()
        duvri_from_db = conn.execute('SELECT * FROM duvri').fetchall()
        conn.close()

        print(f"📊 Caricamento DUVRI dal database: {len(duvri_from_db)} trovati")

        for duvri_db in duvri_from_db:
            duvri_id = duvri_db['id']
            # Ricrea la struttura completa in memoria
            duvri_list[duvri_id] = {
                'id': duvri_id,
                'nome_progetto': duvri_db['nome_progetto'] or 'DUVRI Senza Nome',
                'link_appaltatore': str(uuid.uuid4()),  # Nuovo link per sicurezza
                'stato': duvri_db['stato'] or 'bozza',
                'created_at': duvri_db['created_at'] or datetime.now().strftime('%Y-%m-%d %H:%M'),
                'dati_committente': json.loads(duvri_db['committente_data']) if duvri_db['committente_data'] else {},
                'dati_appaltatore': json.loads(duvri_db['appaltatore_data']) if duvri_db['appaltatore_data'] else {},
                'signatures': json.loads(duvri_db['signatures']) if duvri_db['signatures'] else {}
            }
            print(f"✅ Caricato DUVRI: {duvri_db['nome_progetto']}")

    except Exception as e:
        print(f"❌ Errore nel caricamento DUVRI: {e}")

# Chiama questa funzione DOPO init_db() nel main

# =============================================
# NOTIFICA EMAIL DUVRI CARICATO APPALTATORE
# =============================================

def invia_notifica_semplice(duvri_id, dati_committente, dati_appaltatore):
    """Notifica solo quando l'appaltatore carica il DUVRI firmato"""
    print("=" * 50)
    print("📋 DUVRI PRONTO PER COMMITTENTE")
    print("=" * 50)
    print(f"DA: {dati_appaltatore.get('ragione_sociale', 'Appaltatore')}")
    print(f"PER: {dati_committente.get('nome', 'Committente')}")
    print(f"EMAIL: {dati_committente.get('email', 'N/D')}")
    print(f"OGGETTO: {dati_appaltatore.get('oggetto', 'N/D')}")
    print(f"DATA: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 50)
    return True

# =============================================
# FUNZIONI AUSILIARIE UNIFICATE
# =============================================

def processa_form_(request):
    """Elabora i dati del form dell'appaltatore"""
    return {
        'ragione_sociale': request.form.get('ragione_sociale'),
        'cf': request.form.get('cf'),
        'piva': request.form.get('piva'),
        'cciaa': request.form.get('cciaa'),
        'sede': request.form.get('sede'),
        'telefono': request.form.get('telefono'),
        'fax': request.form.get('fax'),
        'email': request.form.get('email'),
        'pec': request.form.get('pec'),
        'datore_lavoro_nome': request.form.get('datore_lavoro_nome'),
        'datore_lavoro_rif': request.form.get('datore_lavoro_rif'),
        'rspp_nome': request.form.get('rspp_nome'),
        'rspp_rif': request.form.get('rspp_rif'),
        'resp_appalto_nome': request.form.get('resp_appalto_nome'),
        'resp_appalto_rif': request.form.get('resp_appalto_rif'),
        'max_addetti': request.form.get('max_addetti'),
        'orario_lavoro': request.form.get('orario_lavoro'),
        'orario_altro': request.form.get('orario_altro'),
        'oggetto': request.form.get('oggetto'),
        'rischi': request.form.getlist('rischi'),
        'marca_modello': request.form.get('marca_modello'),
        'potenza_kw': request.form.get('potenza_kw'),
        'peso_kg': request.form.get('peso_kg'),
        'durata_giorni': request.form.get('durata_giorni'),
        'numero_tecnici': request.form.get('numero_tecnici'),
        'note_rischi_struttura': request.form.get('note_rischi_struttura'),
        'compilato_il': datetime.now().strftime('%Y-%m-%d %H:%M')
    }

def trova_duvri_per_link(link_univoco):
    """Trova un DUVRI tramite il link appaltatore"""
    
    # 1. Cerca in memoria (veloce)
    for duvri_id, duvri in duvri_list.items():
        if duvri.get('link_appaltatore') == link_univoco:
            print(f"✅ DUVRI trovato in memoria: {duvri_id}")
            return duvri, duvri_id
    
    # 2. Cerca nel database
    print(f"🔍 Cerco nel database link: {link_univoco}")
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 🆕 Cerca nella colonna link_appaltatore
        cursor.execute("""
            SELECT * FROM duvri 
            WHERE link_appaltatore = ?
        """, (link_univoco,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            duvri_id = row['id']
            print(f"✅ DUVRI trovato nel DB: {duvri_id}")
            
            # Carica in memoria
            if duvri_id not in duvri_list:
                duvri_list[duvri_id] = {
                    'id': duvri_id,
                    'nome_progetto': row['nome_progetto'] or 'DUVRI',
                    'link_appaltatore': row['link_appaltatore'],
                    'stato': row['stato'] or 'bozza',
                    'created_at': row['created_at'],
                    'dati_committente': json.loads(row['committente_data']) if row['committente_data'] else {},
                    'dati_appaltatore': json.loads(row['appaltatore_data']) if row['appaltatore_data'] else {},
                    'signatures': json.loads(row['signatures']) if row['signatures'] else {}
                }
                print(f"💾 DUVRI caricato in memoria")
            
            return duvri_list[duvri_id], duvri_id
        else:
            print(f"❌ Link non trovato nel database")
            return None, None
            
    except Exception as e:
        print(f"❌ Errore: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def salva_dati_appaltatore_unificato(duvri_id, dati_appaltatore):
    """Salva i dati dell'appaltatore in modo unificato"""
    # Salva in memoria
    if duvri_id in duvri_list:
        duvri_list[duvri_id]['dati_appaltatore'] = dati_appaltatore

    # Salva nel database
    current_data = get_current_duvri_data()
    current_data['appaltatore'] = dati_appaltatore
    
    # 🆕 CALCOLO AUTOMATICO COSTI SICUREZZA
    # Verifica che ci siano tutti i parametri necessari
    ha_importo = current_data.get('committente', {}).get('importo')
    ha_lavoratori = dati_appaltatore.get('max_addetti')
    ha_durata = dati_appaltatore.get('durata_giorni')
    
    if ha_importo and ha_lavoratori and ha_durata:
        print("\n🔢 Calcolo costi sicurezza parametrico...")
        try:
            costi_calcolati = calcola_costi_sicurezza(current_data)
            current_data['appaltatore'].update(costi_calcolati)
            dati_appaltatore.update(costi_calcolati)
            print(f"✅ Costi calcolati e salvati")
        except Exception as e:
            print(f"❌ Errore calcolo costi: {e}")
    else:
        print(f"⚠️ Parametri mancanti per calcolo costi:")
        print(f"   - Importo committente: {'✅' if ha_importo else '❌'}")
        print(f"   - Max addetti: {'✅' if ha_lavoratori else '❌'}")
        print(f"   - Durata giorni: {'✅' if ha_durata else '❌'}")
    
    # Aggiorna anche in memoria
    if duvri_id in duvri_list:
        duvri_list[duvri_id]['dati_appaltatore'] = dati_appaltatore
    
    save_current_duvri_data(current_data)

    # Aggiorna stato
    if duvri_id in duvri_list:
        duvri = duvri_list[duvri_id]
        if duvri.get('dati_committente'):
            duvri['stato'] = 'completato'
        else:
            duvri['stato'] = 'in compilazione'

def valida_duvri_access(duvri_id):
    """Valida l'accesso a un DUVRI"""
    if not duvri_id or duvri_id not in duvri_list:
        flash('❌ Seleziona prima un DUVRI', 'error')
        return False, redirect(url_for('admin_dashboard'))
    return True, None

def get_allegati_list(duvri_id):
    """Restituisce la lista degli allegati per un DUVRI"""
    allegati_dir = os.path.join(ALLEGATI_FOLDER, f"duvri_{duvri_id}")
    allegati = []

    if os.path.exists(allegati_dir):
        for filename in os.listdir(allegati_dir):
            filepath = os.path.join(allegati_dir, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                allegati.append({
                    'nome_originale': filename,
                    'data_upload': datetime.fromtimestamp(stat.st_mtime).strftime('%d/%m/%Y %H:%M'),
                    'dimensione': stat.st_size
                })

    return allegati

# =============================================
# FUNZIONE COSTI
# =============================================

def calcola_costi_sicurezza(data):
    """
    Calcola i costi di sicurezza in modo parametrico usando CAMPI ESISTENTI.
    
    Parametri utilizzati:
    - committente.importo → Importo appalto
    - appaltatore.max_addetti → Numero lavoratori
    - appaltatore.durata_giorni → Durata lavori (NUOVO campo)
    - committente.rischi_struttura → Rischi committente
    - appaltatore.rischi → Rischi appaltatore
    """
    
    # ========================================
    # PARAMETRI DA DATI ESISTENTI
    # ========================================
    
    appaltatore = data.get('appaltatore', {})
    committente = data.get('committente', {})
    
    # 🆕 Usa campi esistenti
    importo_appalto = float(committente.get('importo', 0))
    numero_lavoratori = int(appaltatore.get('max_addetti', 1))
    durata_giorni = int(appaltatore.get('durata_giorni', 1))
    
    rischi_committente = committente.get('rischi_struttura', [])
    rischi_appaltatore = appaltatore.get('rischi', [])
    
    print(f"\n💰 CALCOLO COSTI PARAMETRICO")
    print(f"📊 Importo appalto (committente): €{importo_appalto:,.2f}")
    print(f"👷 Lavoratori (appaltatore.max_addetti): {numero_lavoratori}")
    print(f"📅 Durata (appaltatore.durata_giorni): {durata_giorni} giorni")
    print(f"⚠️ Rischi committente: {len(rischi_committente)}")
    print(f"⚠️ Rischi appaltatore: {len(rischi_appaltatore)}")
    
    # Validazione
    if importo_appalto <= 0:
        print("⚠️ ATTENZIONE: Importo appalto non valido, uso minimo €5.000")
        importo_appalto = 5000
    
    if numero_lavoratori <= 0:
        print("⚠️ ATTENZIONE: Numero lavoratori non valido, uso 1")
        numero_lavoratori = 1
    
    if durata_giorni <= 0:
        print("⚠️ ATTENZIONE: Durata non valida, uso 5 giorni")
        durata_giorni = 5
    
    # ========================================
    # 1. COSTO BASE (% su importo)
    # ========================================
    
    percentuale_base = 0.02
    costo_base = max(importo_appalto * percentuale_base, 500)
    
    print(f"\n1️⃣ COSTO BASE:")
    print(f"   {percentuale_base*100}% di €{importo_appalto:,.2f} = €{costo_base:,.2f}")
    
    # ========================================
    # 2. COSTI PER LAVORATORE
    # ========================================
    
    costo_dpi_base = 150
    costo_dpi_rischi = 0
    
    DPI_RISCHI = {
        'biologico': 100,
        'chimico': 120,
        'radiologico': 150,
        'elettric': 80,  # Cattura "elettrico", "elettrici"
        'caduta': 120,
        'quota': 120,    # Cattura "lavori in quota"
        'rumore': 40,
        'vibrazioni': 30,
    }
    
    tutti_rischi = rischi_committente + rischi_appaltatore
    
    for rischio_str in tutti_rischi:
        rischio_lower = rischio_str.lower()
        for chiave, costo in DPI_RISCHI.items():
            if chiave in rischio_lower:
                costo_dpi_rischi += costo
                break
    
    costo_formazione = 200
    
    ha_rischi_sanitari = any(
        keyword in rischio_str.lower()
        for rischio_str in tutti_rischi
        for keyword in ['biologico', 'chimico', 'radiologico', 'rumore', 'vibrazioni']
    )
    costo_sorveglianza = 150 if ha_rischi_sanitari else 0
    
    costo_per_lavoratore = (costo_dpi_base + costo_dpi_rischi + 
                            costo_formazione + costo_sorveglianza)
    costo_totale_lavoratori = costo_per_lavoratore * numero_lavoratori
    
    print(f"\n2️⃣ COSTI PER LAVORATORE:")
    print(f"   DPI base: €{costo_dpi_base}")
    print(f"   DPI rischi specifici: €{costo_dpi_rischi}")
    print(f"   Formazione: €{costo_formazione}")
    print(f"   Sorveglianza sanitaria: €{costo_sorveglianza}")
    print(f"   → Per lavoratore: €{costo_per_lavoratore}")
    print(f"   → Totale ({numero_lavoratori} lavoratori): €{costo_totale_lavoratori:,.2f}")
    
    # ========================================
    # 3. COSTI SPECIFICI PER RISCHI
    # ========================================
    
    COSTI_RISCHIO = {
        'biologico': {'impiantistica': 500, 'controlli': 300},
        'chimico': {'impiantistica': 600, 'controlli': 400},
        'radiologico': {'impiantistica': 800, 'controlli': 500},
        'elettric': {'impiantistica': 400, 'controlli': 200},
        'caduta': {'impiantistica': 600, 'segnaletica': 300},
        'quota': {'impiantistica': 600, 'segnaletica': 300},
        'incendio': {'impiantistica': 500, 'presidi': 400},
        'rumore': {'controlli': 300},
        'pazient': {'segnaletica': 400, 'altre_misure': 300},
    }
    
    costo_impiantistica = 0
    costo_controlli = 0
    costo_segnaletica = 0
    costo_presidi = 0
    costo_altre_misure = 0
    
    for rischio_str in tutti_rischi:
        rischio_lower = rischio_str.lower()
        for chiave, valori in COSTI_RISCHIO.items():
            if chiave in rischio_lower:
                costo_impiantistica += valori.get('impiantistica', 0)
                costo_controlli += valori.get('controlli', 0)
                costo_segnaletica += valori.get('segnaletica', 0)
                costo_presidi += valori.get('presidi', 0)
                costo_altre_misure += valori.get('altre_misure', 0)
                break
    
    print(f"\n3️⃣ COSTI SPECIFICI RISCHI:")
    print(f"   Impiantistica: €{costo_impiantistica:,.2f}")
    print(f"   Controlli: €{costo_controlli:,.2f}")
    print(f"   Segnaletica: €{costo_segnaletica:,.2f}")
    print(f"   Presidi: €{costo_presidi:,.2f}")
    print(f"   Altre misure: €{costo_altre_misure:,.2f}")
    
    # ========================================
    # 4. COSTI LEGATI ALLA DURATA
    # ========================================
    
    numero_incontri = max(1, durata_giorni // 5)
    costo_per_incontro = 250
    costo_incontri = numero_incontri * costo_per_incontro
    
    numero_controlli_periodici = max(1, durata_giorni // 10)
    costo_per_controllo = 200
    costo_controlli_periodici = numero_controlli_periodici * costo_per_controllo
    
    costo_controlli += costo_controlli_periodici
    
    print(f"\n4️⃣ COSTI DURATA ({durata_giorni} giorni):")
    print(f"   Incontri coordinamento: {numero_incontri} × €{costo_per_incontro} = €{costo_incontri:,.2f}")
    print(f"   Controlli periodici: {numero_controlli_periodici} × €{costo_per_controllo} = €{costo_controlli_periodici:,.2f}")
    
    # ========================================
    # 5. TOTALE
    # ========================================
    
    costo_dpi_totale = costo_dpi_base * numero_lavoratori + costo_dpi_rischi * numero_lavoratori
    
    totale_generale = (costo_base + 
                      costo_totale_lavoratori + 
                      costo_impiantistica + 
                      costo_controlli + 
                      costo_segnaletica + 
                      costo_presidi + 
                      costo_altre_misure + 
                      costo_incontri)
    
    percentuale_su_appalto = (totale_generale / importo_appalto * 100) if importo_appalto > 0 else 0
    
    print(f"\n💰 TOTALE COSTI SICUREZZA:")
    print(f"   €{totale_generale:,.2f} ({percentuale_su_appalto:.1f}% dell'appalto)")
    
    if percentuale_su_appalto < 3:
        print(f"   ⚠️ Percentuale bassa (<3%)")
    elif percentuale_su_appalto > 20:
        print(f"   ⚠️ Percentuale alta (>20%)")
    else:
        print(f"   ✅ Percentuale nel range normale (3-20%)")
    
    # ========================================
    # RETURN
    # ========================================
    
    return {
        'costo_incontri': round(costo_incontri, 2),
        'costo_dpi': round(costo_dpi_totale, 2),
        'costo_impiantistica': round(costo_impiantistica, 2),
        'costo_segnaletica': round(costo_segnaletica, 2),
        'costo_presidi': round(costo_presidi, 2),
        'costo_controlli': round(costo_controlli, 2),
        'costo_altre_misure': round(costo_altre_misure + costo_base, 2),
        'costi_presenti': True,
        'costi_calcolati_auto': True,
        'note_costi_sicurezza': f'Calcolati parametricamente: importo €{importo_appalto:,.2f}, {numero_lavoratori} lavoratori, {durata_giorni} giorni, {len(tutti_rischi)} rischi. Totale: €{totale_generale:,.2f} ({percentuale_su_appalto:.1f}% appalto).'
    }

# =============================================
# CONFIGURAZIONE UPLOAD FILE
# =============================================
ALLOWED_EXTENSIONS = {"pdf"}

def allowed_file(filename):
    """Verifica se il file ha un'estensione permessa"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_logo_path():
    """Restituisce il percorso del logo"""
    logo_paths = [
        "static/logo.png",
        "static/logo.jpg",
        "static/images/logo.png",
        "documents/logo.png"
    ]
    for path in logo_paths:
        if os.path.exists(path):
            return path
    return None

# =============================================
# CONFIGURAZIONE UPLOAD ALLEGATI
# =============================================
ALLOWED_EXTENSIONS = {"pdf", "doc", "docx", "xls", "xlsx", "jpg", "jpeg", "png"}
ALLEGATI_FOLDER = os.path.join(BASE_DIR, "uploads", "allegati")

os.makedirs(ALLEGATI_FOLDER, exist_ok=True)

# =============================================
# ROUTES PRINCIPALI
# =============================================

@app.route('/')
def index():
    """Reindirizza alla dashboard admin"""
    return redirect(url_for('admin_dashboard'))

@app.route('/admin')
def admin_dashboard():
    """Dashboard solo per l'amministratore - vede tutti i DUVRI"""
    # 🔥 FORZA SINCRONIZZAZIONE
    sync_all_duvri_from_db()

    return render_template('admin_dashboard.html',
                         duvri_list=duvri_list,
                         current_duvri_id=session.get('current_duvri_id'))

@app.route('/nuovo_duvri')
def nuovo_duvri():
    """Crea un nuovo DUVRI con link univoco per l'appaltatore"""
    nome_progetto = request.args.get('nome', 'Nuovo Progetto')

    # Genera ID e link univoci
    duvri_id = str(uuid.uuid4())[:8]
    link_appaltatore = str(uuid.uuid4())

    nuovo_duvri = {
        'id': duvri_id,
        'nome_progetto': nome_progetto,
        'link_appaltatore': link_appaltatore,
        'stato': 'bozza',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'dati_committente': {},
        'dati_appaltatore': {}
    }

    # Salva in memoria
    duvri_list[duvri_id] = nuovo_duvri

    # Salva nel database
    try:
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO duvri (id, nome_progetto, created_at, updated_at) VALUES (?, ?, ?, ?)',
            (duvri_id, nome_progetto, datetime.now(), datetime.now())
        )
        conn.commit()
        conn.close()
        print(f"✅ DUVRI {duvri_id} salvato nel database")
    except Exception as e:
        print(f"❌ Errore salvataggio DB: {e}")

    # Imposta come attivo
    session['current_duvri_id'] = duvri_id
    flash(f'✅ DUVRI "{nome_progetto}" creato con successo!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/compila_committente', methods=['GET', 'POST'])
def compila_committente():
    """Route per compilare i dati del committente"""
    duvri_id = request.args.get('duvri_id') or session.get('current_duvri_id')

    # Validazione
    is_valid, redirect_response = valida_duvri_access(duvri_id)
    if not is_valid:
        return redirect_response

    # Imposta come DUVRI attivo
    session['current_duvri_id'] = duvri_id
    duvri = duvri_list[duvri_id]

    if request.method == 'POST':
        # Processa il form
        dati_committente = {
            'nome': request.form.get('nome'),
            'codice_fiscale': request.form.get('codice_fiscale'),
            'indirizzo': request.form.get('indirizzo'),
            'referente': request.form.get('referente'),
            'email': request.form.get('email'),
            'tipologia_struttura': request.form.get('tipologia_struttura'),
            'area_installazione': request.form.get('area_installazione'),
            'presenza_pazienti': request.form.get('presenza_pazienti'),
            'alimentazione_disponibile': request.form.get('alimentazione_disponibile'),
            'tipo_pavimento': request.form.get('tipo_pavimento'),
            'altezza_soffitto': request.form.get('altezza_soffitto'),
            'larghezza_accesso': request.form.get('larghezza_accesso'),
            'orari_lavori': request.form.get('orari_lavori'),
            'referente_tecnico': request.form.get('referente_tecnico'),
            'rischi_struttura': request.form.getlist('rischi_struttura'),
            'note_rischi_struttura': request.form.get('note_rischi_struttura'),
            'costo_correzione': request.form.get('costo_correzione', '0'),
            'importo': request.form.get('importo', ''),
            'oggetto': request.form.get('oggetto', ''),
            'compilato_il': datetime.now().strftime('%Y-%m-%d %H:%M')
        }

        # Salva i dati
        duvri['dati_committente'] = dati_committente
        current_data = get_current_duvri_data()
        current_data['committente'] = dati_committente
        save_current_duvri_data(current_data)

        # Aggiorna stato
        if duvri['dati_appaltatore']:
            duvri['stato'] = 'completato'
        else:
            duvri['stato'] = 'in compilazione'

        flash('✅ Dati committente salvati con successo!', 'success')
        return redirect(url_for('summary'))

    # GET: mostra form con dati esistenti + oggetto sincronizzato
    data = duvri.get('dati_committente', {})

    # 🔄 SINCRONIZZAZIONE OGGETTO: se non esiste nel committente ma esiste nell'appaltatore
    if not data.get('oggetto') and duvri.get('dati_appaltatore', {}).get('oggetto'):
        data['oggetto'] = duvri['dati_appaltatore']['oggetto']

    return render_template('committente_form.html',
                         data=data,
                         rischi_committente=RISCHI_COMMITTENTE,
                         duvri_id=duvri_id,
                         duvri_list=duvri_list,
                         current_duvri_id=duvri_id)

@app.route('/compila_appaltatore', methods=['GET', 'POST'])
def compila_appaltatore():
    """Route per admin - compila dati appaltatore"""
    duvri_id = request.args.get('duvri_id') or session.get('current_duvri_id')

    # Validazione
    is_valid, redirect_response = valida_duvri_access(duvri_id)
    if not is_valid:
        return redirect_response

    duvri = duvri_list[duvri_id]

    if request.method == 'POST':
        # Processa e salva dati usando funzione unificata
        dati_appaltatore = processa_form_(request)
        salva_dati_appaltatore_unificato(duvri_id, dati_appaltatore)

        flash('✅ Dati appaltatore salvati con successo!', 'success')
        return redirect(url_for('summary'))

    # GET: mostra form con dati esistenti
    data = duvri.get('dati_appaltatore', {})
    dati_committente = duvri.get('dati_committente', {})  # 🆕 Aggiungi dati committente
    
    return render_template('appaltatore_form.html',
                         data=data,
                         dati_committente=dati_committente,  # 🆕 Passa al template
                         rischi_paragrafi=RISCHI_PARAGRAFI,
                         rischi_hta=RISCHI_HTA,
                         duvri_id=duvri_id)

@app.route('/appaltatore_form/<link_univoco>', methods=['GET', 'POST'])
def appaltatore_form(link_univoco):
    """Route per appaltatore esterno tramite link"""
    # Trova DUVRI usando funzione unificata
    duvri_trovato, duvri_id = trova_duvri_per_link(link_univoco)

    if not duvri_trovato:
        return render_template('errore_appaltatore.html',
                             messaggio="Link DUVRI non valido. Contatta il committente.")

    # 🔥 Sincronizza i dati dal database
    sync_db_to_memory(duvri_id)

    # Imposta come DUVRI attivo
    session['current_duvri_id'] = duvri_id
    session['from_appaltatore_link'] = True

    if request.method == 'POST':
        # ✅ 1. VALIDA i dati prima di salvare
        errori = valida_dati_appaltatore(request.form)

        if errori:
            # ✅ 2. In caso di errori, RIMANI sul form
            for errore in errori:
                flash(errore, 'danger')
            dati_committente = duvri_trovato.get('dati_committente', {})  # 🆕
            
            return render_template('appaltatore_form.html',
                                 data=request.form,
                                 dati_committente=dati_committente,  # 🆕 Nuovo parametro
                                 rischi_paragrafi=RISCHI_PARAGRAFI,
                                 rischi_hta=RISCHI_HTA,
                                 duvri_id=duvri_id)

        # ✅ 3. Solo se validazione OK, salva e redirect
        dati_appaltatore = processa_form_(request)
        salva_dati_appaltatore_unificato(duvri_id, dati_appaltatore)

        flash('✅ Dati salvati correttamente!', 'success')
        return redirect(url_for('summary'))

    # GET: mostra form con dati esistenti
    data = duvri_trovato.get('dati_appaltatore', {})
    dati_committente = duvri_trovato.get('dati_committente', {})  # 🆕 Passa dati committente
    
    return render_template('appaltatore_form.html',
                         data=data,
                         dati_committente=dati_committente,  # 🆕 Nuovo parametro
                         rischi_paragrafi=RISCHI_PARAGRAFI,
                         rischi_hta=RISCHI_HTA,
                         duvri_id=duvri_id)

def valida_dati_appaltatore(form_data):
    """Valida i dati obbligatori del form appaltatore"""
    errori = []

    # Campi obbligatori (come definito nel template con required)
    if not form_data.get('ragione_sociale', '').strip():
        errori.append('La ragione sociale è obbligatoria')

    if not form_data.get('cf', '').strip():
        errori.append('Il codice fiscale è obbligatorio')

    if not form_data.get('piva', '').strip():
        errori.append('La partita IVA è obbligatoria')

    if not form_data.get('sede', '').strip():
        errori.append('La sede legale è obbligatoria')

    if not form_data.get('telefono', '').strip():
        errori.append('Il telefono è obbligatorio')

    if not form_data.get('email', '').strip():
        errori.append('L\'email è obbligatoria')

    if not form_data.get('pec', '').strip():
        errori.append('La PEC è obbligatoria')

    if not form_data.get('datore_lavoro_nome', '').strip():
        errori.append('Il nominativo del datore di lavoro è obbligatorio')

    if not form_data.get('rspp_nome', '').strip():
        errori.append('Il nominativo RSPP è obbligatorio')

    if not form_data.get('resp_appalto_nome', '').strip():
        errori.append('Il nominativo del responsabile appalto è obbligatorio')

    if not form_data.get('max_addetti') or int(form_data.get('max_addetti', 0)) < 1:
        errori.append('Il numero massimo di addetti deve essere almeno 1')

    return errori

@app.route('/select_duvri/<duvri_id>')
def select_duvri(duvri_id):
    """Seleziona un DUVRI come attivo"""
    if duvri_id in duvri_list:
        session['current_duvri_id'] = duvri_id
        return redirect(url_for('summary'))
    else:
        flash('❌ DUVRI non trovato', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/appaltatore/<link_univoco>', methods=['GET', 'POST'])
def appaltatore_duvri(link_univoco):
    """Vista per l'appaltatore - vede solo il suo DUVRI"""
    # 🔥 FORZA SINCRONIZZAZIONE PRIMA DI CERCARE
    sync_all_duvri_from_db()

    duvri_trovato, duvri_id = trova_duvri_per_link(link_univoco)
    if not duvri_trovato:
        # 🔥 MODIFICA CRITICA: NON reindirizzare alla dashboard admin!
        return render_template('errore_appaltatore.html',
                             messaggio="DUVRI non trovato. Contatta il committente.")

    # Imposta flag per identificare accesso appaltatore
    session['from_appaltatore_link'] = True
    session['current_duvri_id'] = duvri_id

    # 🔥 IMPORTANTE: Sincronizza i dati dal database
    sync_db_to_memory(duvri_id)

    # Mostra direttamente il form appaltatore
    data = duvri_trovato.get('dati_appaltatore', {})
    return render_template('appaltatore_form.html',
                         data=data,
                         rischi_paragrafi=RISCHI_PARAGRAFI,
                         rischi_hta=RISCHI_HTA,
                         duvri_id=duvri_id)

@app.route('/emergency_recover')
def emergency_recover():
    """Recupera tutti i DUVRI dal database - SOLO EMERGENZA"""
    try:
        conn = get_db_connection()
        duvri_from_db = conn.execute('SELECT * FROM duvri').fetchall()
        conn.close()

        recovered_count = 0
        for duvri_db in duvri_from_db:
            duvri_id = duvri_db['id']
            if duvri_id not in duvri_list:
                duvri_list[duvri_id] = {
                    'id': duvri_id,
                    'nome_progetto': duvri_db['nome_progetto'] or 'DUVRI Recuperato',
                    'link_appaltatore': str(uuid.uuid4()),  # Nuovo link per sicurezza
                    'stato': duvri_db['stato'] or 'bozza',
                    'created_at': duvri_db['created_at'] or datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'dati_committente': json.loads(duvri_db['committente_data']) if duvri_db['committente_data'] else {},
                    'dati_appaltatore': json.loads(duvri_db['appaltatore_data']) if duvri_db['appaltatore_data'] else {},
                    'signatures': json.loads(duvri_db['signatures']) if duvri_db['signatures'] else {}
                }
                recovered_count += 1
                print(f"✅ Recuperato DUVRI: {duvri_db['nome_progetto']}")

        flash(f"✅ Recuperati {recovered_count} DUVRI dal database!", "success")
        return redirect(url_for('admin_dashboard'))

    except Exception as e:
        flash(f"❌ Errore nel recupero: {str(e)}", "danger")
        return redirect(url_for('admin_dashboard'))

@app.route('/ricalcola_costi', methods=['POST'])
def ricalcola_costi():
    """Ricalcola i costi di sicurezza"""
    print("\n🔄 RICALCOLA COSTI")
    
    duvri_id = session.get('current_duvri_id')
    print(f"📊 DUVRI ID: {duvri_id}")

    if not duvri_id:
        flash("Nessun DUVRI selezionato", "warning")
        return redirect(url_for('summary'))

    data = get_current_duvri_data()
    print(f"📊 Appaltatore presente: {bool(data.get('appaltatore'))}")

    if data.get('appaltatore'):
        # Rimuove flag modifiche manuali
        if 'costi_modificati_manualmente' in data['appaltatore']:
            del data['appaltatore']['costi_modificati_manualmente']
            print("✅ Flag modifiche manuali rimosso")
        
        # Calcola nuovi costi
        costi_calcolati = calcola_costi_sicurezza(data)
        print(f"💰 TOTALE calcolato: {sum([v for k,v in costi_calcolati.items() if k.startswith('costo_') and isinstance(v, (int, float))])}")

        # Mantiene le note
        note_esistenti = data['appaltatore'].get('note_costi_sicurezza', '')
        costi_calcolati['note_costi_sicurezza'] = note_esistenti
        costi_calcolati['costi_calcolati_auto'] = True

        # 🆕 AGGIORNA anche in memoria (duvri_list)
        if duvri_id in duvri_list:
            if 'dati_appaltatore' not in duvri_list[duvri_id]:
                duvri_list[duvri_id]['dati_appaltatore'] = {}
            duvri_list[duvri_id]['dati_appaltatore'].update(costi_calcolati)
            print("✅ Aggiornato in memoria (duvri_list)")

        # Aggiorna i dati e salva
        data['appaltatore'].update(costi_calcolati)
        save_current_duvri_data(data)
        print("✅ Salvato nel database")

        flash("✅ Costi ricalcolati con successo!", "success")
    else:
        print("❌ Nessun appaltatore")
        flash("⚠️ Nessun dato appaltatore trovato", "warning")

    return redirect(url_for('summary'))


@app.route('/summary')
def summary():
    """Pagina di riepilogo"""
    duvri_id = session.get('current_duvri_id')

    if not duvri_id:
        flash('Prima crea o seleziona un DUVRI', 'warning')
        return redirect(url_for('admin_dashboard'))

    # Carica dati dal database
    data = get_current_duvri_data()

    # Aggiungi lista allegati ai dati
    if 'appaltatore' not in data:
        data['appaltatore'] = {}

    data['appaltatore']['allegati'] = get_allegati_list(duvri_id)

    # CALCOLO COSTI AUTOMATICO - logica semplificata
    if data.get('appaltatore'):
        # Verifica se i costi NON sono presenti OPPURE sono automatici ma devono essere ricalcolati
        costi_mancanti = not any(
            data['appaltatore'].get(campo)
            for campo in ['costo_incontri', 'costo_dpi', 'costo_impiantistica']
        )

        # Se i costi mancano o sono automatici, ricalcola
        if costi_mancanti or data['appaltatore'].get('costi_calcolati_auto'):
            costi_calcolati = calcola_costi_sicurezza(data)

            # Preserva le note esistenti
            if 'note_costi_sicurezza' in data['appaltatore']:
                costi_calcolati['note_costi_sicurezza'] = data['appaltatore']['note_costi_sicurezza']

            # Aggiorna SOLO se sono costi automatici o mancanti
            data['appaltatore'].update(costi_calcolati)
            save_current_duvri_data(data)

    return render_template('summary.html',
                         data=data,
                         duvri_list=duvri_list,
                         current_duvri_id=duvri_id,
                         WEASYPRINT_AVAILABLE=WEASYPRINT_AVAILABLE,
                         XHTML2PDF_AVAILABLE=XHTML2PDF_AVAILABLE)

# =============================================
# ROUTES SECONDARIE E LEGACY
# =============================================

@app.route('/gestisci_duvri/<duvri_id>')
def gestisci_duvri(duvri_id):
    """Gestione DUVRI"""
    session['current_duvri_id'] = duvri_id
    return render_template('gestisci_duvri.html', duvri_id=duvri_id)

@app.route('/imposta_duvri_attivo', methods=['POST'])
def imposta_duvri_attivo():
    """Imposta DUVRI attivo"""
    duvri_id = request.form.get('duvri_id')
    ruolo = request.form.get('ruolo')

    session['current_duvri_id'] = duvri_id

    if ruolo == 'committente':
        return redirect(url_for('compila_committente'))
    elif ruolo == 'appaltatore':
        return redirect(url_for('compila_appaltatore'))
    else:
        return redirect(url_for('select_role'))

@app.route("/select_role", methods=["POST"])
def select_role():
    """Selezione ruolo (legacy)"""
    role = request.form.get("role")
    if role in ["committente", "appaltatore"]:
        session["role"] = role
        return redirect(url_for("form_page", role=role))
    return redirect(url_for("admin_dashboard"))

@app.route('/elimina_duvri/<duvri_id>', methods=['POST'])
def elimina_duvri(duvri_id):
    """
    Elimina un DUVRI e tutti i dati associati
    """
    try:
        # Verifica che il DUVRI esista nella memoria
        if duvri_id not in duvri_list:
            flash('DUVRI non trovato.', 'danger')
            return redirect(url_for('admin_dashboard'))

        # Recupera il nome del progetto per il messaggio di conferma
        nome_progetto = duvri_list[duvri_id].get('nome_progetto', 'Senza nome')

        # 1. Elimina il DUVRI dalla memoria
        del duvri_list[duvri_id]

        # 2. Elimina il DUVRI dal database SQLite
        conn = get_db_connection()
        conn.execute('DELETE FROM duvri WHERE id = ?', (duvri_id,))
        conn.commit()
        conn.close()

        # 3. Se era il DUVRI corrente, resetta la selezione nella sessione
        if session.get('current_duvri_id') == duvri_id:
            session.pop('current_duvri_id', None)

        flash(f'DUVRI "{nome_progetto}" eliminato con successo.', 'success')

    except Exception as e:
        flash(f'Errore durante l\'eliminazione del DUVRI: {str(e)}', 'danger')

    return redirect(url_for('admin_dashboard'))

@app.route('/duplica_duvri/<duvri_id>')
def duplica_duvri(duvri_id):
    """
    Duplica un DUVRI esistente con un nuovo ID e link univoco
    """
    try:
        # Verifica che il DUVRI esista nella memoria
        if duvri_id not in duvri_list:
            flash('DUVRI non trovato.', 'danger')
            return redirect(url_for('admin_dashboard'))

        # Recupera il DUVRI originale
        duvri_originale = duvri_list[duvri_id]

        # Genera un nuovo ID univoco
        nuovo_id = str(uuid.uuid4())

        # Crea una copia profonda del DUVRI originale
        nuovo_duvri = copy.deepcopy(duvri_originale)

        # Aggiorna i campi univoci
        nuovo_duvri['id'] = nuovo_id
        nuovo_duvri['link_appaltatore'] = str(uuid.uuid4())
        nuovo_duvri['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M")

        # Modifica il nome per indicare che è una copia
        nome_originale = nuovo_duvri.get('nome_progetto', 'DUVRI senza nome')
        nuovo_duvri['nome_progetto'] = f"{nome_originale} (Copia)"

        # Resetta lo stato a "bozza" se non è già in bozza
        if nuovo_duvri.get('stato') != 'bozza':
            nuovo_duvri['stato'] = 'bozza'

        # Resetta le firme se presenti
        if 'signatures' in nuovo_duvri:
            nuovo_duvri['signatures'] = {}

        # Resetta i timestamp di firma
        if 'firmato_il' in nuovo_duvri:
            del nuovo_duvri['firmato_il']

        # IMPORTANTE: Mantieni tutti i dati dei form ma resetta alcuni campi temporanei
        # Mantieni dati committente
        if 'dati_committente' in nuovo_duvri:
            # Resetta solo la data di compilazione
            nuovo_duvri['dati_committente']['compilato_il'] = datetime.now().strftime('%Y-%m-%d %H:%M')

        # Mantieni dati appaltatore
        if 'dati_appaltatore' in nuovo_duvri:
            # Resetta solo la data di compilazione
            nuovo_duvri['dati_appaltatore']['compilato_il'] = datetime.now().strftime("%Y-%m-%d %H:%M")

        # 1. Aggiungi il nuovo DUVRI alla memoria
        duvri_list[nuovo_id] = nuovo_duvri

        # 2. Salva il nuovo DUVRI nel database SQLite
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO duvri (id, nome_progetto, committente_data, appaltatore_data, signatures, stato, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
            (
                nuovo_id,
                nuovo_duvri['nome_progetto'],
                json.dumps(nuovo_duvri.get('dati_committente', {})),
                json.dumps(nuovo_duvri.get('dati_appaltatore', {})),
                json.dumps(nuovo_duvri.get('signatures', {})),
                nuovo_duvri['stato'],
                datetime.now(),
                datetime.now()
            )
        )
        conn.commit()
        conn.close()

        # 3. Imposta come DUVRI corrente
        session['current_duvri_id'] = nuovo_id

        flash(f'DUVRI "{nome_originale}" duplicato con successo con tutti i dati!', 'success')

    except Exception as e:
        flash(f'Errore durante la duplicazione del DUVRI: {str(e)}', 'danger')

    return redirect(url_for('admin_dashboard'))


@app.route("/form/<role>", methods=["GET", "POST"])
def form_page(role):
    """Pagina form per compilazione (legacy)"""
    if role not in ["committente", "appaltatore"]:
        return redirect(url_for("admin_dashboard"))

    data = get_current_duvri_data()
    current_data = data.get(role, {})

    if request.method == "POST":
        form_data = {}

        for key, value in request.form.items():
            if key not in ['rischi', 'rischi_struttura']:
                form_data[key] = value

        if role == "appaltatore":
            rischi_selezionati = request.form.getlist('rischi')
            form_data['rischi'] = rischi_selezionati
        elif role == "committente":
            rischi_selezionati = request.form.getlist('rischi_struttura')
            form_data['rischi_struttura'] = rischi_selezionati

        form_data['mezzi_non_applicabile'] = 'mezzi_non_applicabile' in request.form

        data[role] = form_data
        save_current_duvri_data(data)

        flash(f"Dati {role} salvati con successo!")
        return redirect(url_for("summary"))

    return render_template('form.html',
                         role=role,
                         data=current_data,
                         rischi_paragrafi=RISCHI_PARAGRAFI,
                         rischi_hta=RISCHI_HTA,
                         rischi_committente=RISCHI_COMMITTENTE)

@app.route("/sign/<role>")
def sign(role):
    """Firma del DUVRI"""
    if role not in ["committente", "appaltatore"]:
        return redirect(url_for("summary"))

    data = get_current_duvri_data()
    if "signatures" not in data:
        data["signatures"] = {}

    data["signatures"][role] = datetime.now().strftime("%d/%m/%Y alle %H:%M:%S")
    save_current_duvri_data(data)

    flash(f"Firma registrata per {role}")
    return redirect(url_for("summary"))

@app.route("/pdf")
def generate_pdf():
    """Genera PDF del DUVRI - VERSIONE CON DEBUG COMPLETO"""
    print("\n" + "="*80)
    print("🚀 INIZIO GENERAZIONE PDF")
    print("="*80)

    try:
        # STEP 1: Recupero dati
        print("\n📊 STEP 1: Recupero dati DUVRI")
        data = get_current_duvri_data()
        duvri_id = session.get('current_duvri_id', 'unknown')
        print(f"✅ duvri_id: {duvri_id}")
        print(f"✅ Dati recuperati: {bool(data)}")

        # STEP 2: Controllo firme
        print("\n✍️ STEP 2: Controllo firme")
        firme = data.get("signatures", {})
        print(f"📊 Firme presenti: {firme}")

        if not (firme.get("committente") and firme.get("appaltatore")):
            print("❌ BLOCCO: Firme mancanti")
            flash("❌ Entrambe le parti devono firmare prima di generare il PDF")
            return redirect(url_for("summary"))
        print("✅ Firme OK")

        # STEP 3: Preparazione nomi file
        print("\n📝 STEP 3: Preparazione nomi file")
        nome_ditta = "Ditta"
        if data.get('appaltatore', {}).get('ragione_sociale'):
            nome_ditta = data['appaltatore']['ragione_sociale']
            nome_ditta = "".join(c for c in nome_ditta if c.isalnum() or c in (' ', '-', '_')).rstrip()
            nome_ditta = nome_ditta.replace(' ', '_')[:30]
        print(f"✅ Nome ditta sanitizzato: {nome_ditta}")

        data_oggi = datetime.now().strftime('%Y-%m-%d')
        filename_base = f"DUVRI_{nome_ditta}_{data_oggi}.pdf"
        filename_completo = f"DUVRI_{nome_ditta}_{data_oggi}_completo.pdf"
        print(f"✅ Filename base: {filename_base}")
        print(f"✅ Filename completo: {filename_completo}")

        # STEP 4: Preparazione directory
        print("\n📁 STEP 4: Preparazione directory output")
        output_folder = os.path.join(current_app.root_path, "output")
        print(f"📂 Output folder: {output_folder}")
        os.makedirs(output_folder, exist_ok=True)

        output_path_base = os.path.join(output_folder, filename_base)
        output_path_completo = os.path.join(output_folder, filename_completo)
        print(f"✅ Path PDF base: {output_path_base}")
        print(f"✅ Path PDF completo: {output_path_completo}")

        # STEP 5: Render HTML
        print("\n🎨 STEP 5: Rendering template HTML")
        try:
            html_content = render_template("pdf_template.html", data=data, datetime=datetime)
            print(f"✅ HTML generato: {len(html_content)} caratteri")
            # Salva HTML per debug
            html_debug_path = os.path.join(output_folder, f"DEBUG_{filename_base}.html")
            with open(html_debug_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"💾 HTML salvato per debug in: {html_debug_path}")
        except Exception as e:
            print(f"❌ ERRORE rendering HTML: {str(e)}")
            raise

        pdf_base_path = None

        # STEP 6: Tentativo con xhtml2pdf
        print("\n🔧 STEP 6: Tentativo generazione con xhtml2pdf")
        print(f"📊 xhtml2pdf disponibile: {XHTML2PDF_AVAILABLE}")

        if XHTML2PDF_AVAILABLE:
            try:
                print("⚙️ Avvio xhtml2pdf...")
                pdf_bytes = io.BytesIO()
                pisa_status = pisa.CreatePDF(html_content, dest=pdf_bytes)

                print(f"📊 Pisa status err: {pisa_status.err}")
                print(f"📊 Pisa status log: {pisa_status.log}")

                if not pisa_status.err:
                    with open(output_path_base, 'wb') as f:
                        f.write(pdf_bytes.getvalue())
                    pdf_base_path = output_path_base
                    print(f"✅ PDF generato con xhtml2pdf: {output_path_base}")
                    print(f"📊 Dimensione file: {os.path.getsize(output_path_base)} bytes")
                else:
                    print(f"⚠️ xhtml2pdf ha restituito errori: {pisa_status.err}")
            except Exception as e:
                print(f"❌ Errore xhtml2pdf: {str(e)}")
                import traceback
                print(traceback.format_exc())

                        # STEP 7: Tentativo con WeasyPrint
        print("\n🔧 STEP 7: Tentativo generazione con WeasyPrint")
        print(f"📊 WeasyPrint disponibile: {WEASYPRINT_AVAILABLE}")
        print(f"📊 PDF già generato: {bool(pdf_base_path)}")

        if not pdf_base_path and WEASYPRINT_AVAILABLE:
            try:
                print("⚙️ Avvio WeasyPrint...")
                from weasyprint import HTML
                HTML(string=html_content).write_pdf(target=output_path_base)
                pdf_base_path = output_path_base
                print(f"✅ PDF generato con WeasyPrint: {output_path_base}")
                print(f"📊 Dimensione file: {os.path.getsize(output_path_base)} bytes")
            except Exception as e:
                print(f"❌ Errore WeasyPrint: {str(e)}")
                import traceback
                print(traceback.format_exc())

        # STEP 8: Verifica PDF generato
        print("\n🔍 STEP 8: Verifica PDF base")
        if not pdf_base_path:
            print("❌ BLOCCO: Nessun motore PDF ha funzionato")
            flash("❌ Nessun motore PDF funzionante. Installa xhtml2pdf o WeasyPrint.")
            return redirect(url_for("summary"))

        if not os.path.exists(pdf_base_path):
            print(f"❌ BLOCCO: File PDF non trovato: {pdf_base_path}")
            flash("❌ Errore: PDF generato ma file non trovato")
            return redirect(url_for("summary"))

        print(f"✅ PDF base verificato: {pdf_base_path}")

        # STEP 9: Unione con allegati
        print("\n📎 STEP 9: Unione con allegati PDF")
        try:
            pdf_finale_path = unisci_pdf_duvri(duvri_id, pdf_base_path, output_path_completo)
            print(f"✅ PDF finale: {pdf_finale_path}")
            print(f"📊 Dimensione finale: {os.path.getsize(pdf_finale_path)} bytes")

            flash(f"✅ PDF generato con allegati - salvato in: output/{os.path.basename(pdf_finale_path)}")

            print("\n🎉 GENERAZIONE PDF COMPLETATA CON SUCCESSO")
            print("="*80 + "\n")

            return send_file(
                pdf_finale_path,
                as_attachment=True,
                download_name=os.path.basename(pdf_finale_path)
            )
        except Exception as e:
            print(f"⚠️ Errore unione PDF allegati: {str(e)}")
            import traceback
            print(traceback.format_exc())

            flash(f"✅ PDF base generato (senza allegati) - salvato in: output/{filename_base}")

            print("\n⚠️ GENERAZIONE PDF COMPLETATA (solo base, senza allegati)")
            print("="*80 + "\n")

            return send_file(
                output_path_base,
                as_attachment=True,
                download_name=filename_base
            )

    except Exception as e:
        print(f"\n❌❌❌ ERRORE CRITICO GENERAZIONE PDF ❌❌❌")
        print(f"Errore: {str(e)}")
        import traceback
        print(traceback.format_exc())
        print("="*80 + "\n")

        flash(f"❌ Errore nella generazione del PDF: {str(e)}")
        return redirect(url_for("summary"))


def unisci_pdf_duvri(duvri_id, pdf_base_path, output_path_completo):
    """Unisce il PDF base con tutti i PDF allegati - VERSIONE CON DEBUG"""
    print("\n" + "-"*60)
    print("📎 FUNZIONE: unisci_pdf_duvri")
    print("-"*60)

    try:
        merger = PyPDF2.PdfMerger()
        print("✅ PyPDF2.PdfMerger inizializzato")

        # 1. Aggiungi il PDF base
        print(f"\n📄 Aggiunta PDF base: {pdf_base_path}")
        if os.path.exists(pdf_base_path):
            merger.append(pdf_base_path)
            print(f"✅ PDF base aggiunto ({os.path.getsize(pdf_base_path)} bytes)")
        else:
            raise FileNotFoundError(f"PDF base non trovato: {pdf_base_path}")

        # 2. Cerca PDF allegati
        print(f"\n🔍 Ricerca allegati per duvri_id: {duvri_id}")
        cartella_allegati = os.path.join(current_app.config['UPLOAD_FOLDER'], str(duvri_id))
        print(f"📂 Percorso cartella allegati: {cartella_allegati}")
        print(f"📊 Cartella esiste: {os.path.exists(cartella_allegati)}")

        if os.path.exists(cartella_allegati):
            # Lista tutti i file
            tutti_i_file = os.listdir(cartella_allegati)
            print(f"📊 File totali nella cartella: {len(tutti_i_file)}")
            print(f"📂 Lista completa file: {tutti_i_file}")

            # Filtra solo i PDF
            pdf_allegati = []
            for filename in tutti_i_file:
                if filename.lower().endswith('.pdf'):
                    full_path = os.path.join(cartella_allegati, filename)
                    pdf_allegati.append(full_path)
                    print(f"   ✅ PDF trovato: {filename}")

            print(f"\n📊 Totale PDF allegati trovati: {len(pdf_allegati)}")

            if pdf_allegati:
                # Ordina i PDF
                pdf_allegati.sort()
                print("📊 Ordine di unione:")
                for i, pdf_path in enumerate(pdf_allegati, 1):
                    print(f"   {i}. {os.path.basename(pdf_path)}")

                # Aggiungi tutti i PDF
                for pdf_path in pdf_allegati:
                    try:
                        merger.append(pdf_path)
                        print(f"✅ Aggiunto: {os.path.basename(pdf_path)} ({os.path.getsize(pdf_path)} bytes)")
                    except Exception as e:
                        print(f"❌ Errore aggiunta {os.path.basename(pdf_path)}: {str(e)}")
                        continue
            else:
                print("⚠️ Nessun PDF trovato nella cartella allegati")
        else:
            print("⚠️ Cartella allegati non esiste - PDF senza allegati")

        # 3. Salva il PDF unito
        print(f"\n💾 Salvataggio PDF finale: {output_path_completo}")
        merger.write(output_path_completo)
        merger.close()

        if os.path.exists(output_path_completo):
            print(f"✅ PDF unito salvato con successo")
            print(f"📊 Dimensione: {os.path.getsize(output_path_completo)} bytes")
        else:
            print(f"❌ File non trovato dopo salvataggio!")

        print("-"*60 + "\n")
        return output_path_completo

    except Exception as e:
        print(f"\n❌ ERRORE nell'unione PDF: {str(e)}")
        import traceback
        print(traceback.format_exc())
        print("-"*60 + "\n")
        # In caso di errore, restituisci il PDF base
        return pdf_base_path


# =============================================
# ROUTE DEBUG AGGIUNTIVA
# =============================================

@app.route('/test_pdf_generation')
def test_pdf_generation():
    """Test completo generazione PDF con diagnostica"""
    duvri_id = session.get('current_duvri_id')

    diagnostica = {
        'duvri_id': duvri_id,
        'duvri_exists_in_memory': duvri_id in duvri_list if duvri_id else False,
        'xhtml2pdf_available': XHTML2PDF_AVAILABLE,
        'weasyprint_available': WEASYPRINT_AVAILABLE,
        'output_dir_exists': os.path.exists(os.path.join(BASE_DIR, "output")),
        'output_dir_writable': os.access(os.path.join(BASE_DIR, "output"), os.W_OK),
        'cwd': os.getcwd(),
    }

    if duvri_id:
        data = get_current_duvri_data()
        diagnostica.update({
            'committente_presente': bool(data.get('committente')),
            'appaltatore_presente': bool(data.get('appaltatore')),
            'firme_committente': bool(data.get('signatures', {}).get('committente')),
            'firme_appaltatore': bool(data.get('signatures', {}).get('appaltatore')),
            'committente_nome': data.get('committente', {}).get('nome', 'N/A'),
            'appaltatore_nome': data.get('appaltatore', {}).get('ragione_sociale', 'N/A'),
        })

        cartella_allegati = os.path.join(app.config['UPLOAD_FOLDER'], f"duvri_{duvri_id}")
        if os.path.exists(cartella_allegati):
            pdf_files = [f for f in os.listdir(cartella_allegati) if f.lower().endswith('.pdf')]
            diagnostica['num_allegati_pdf'] = len(pdf_files)
            diagnostica['allegati_list'] = pdf_files
        else:
            diagnostica['num_allegati_pdf'] = 0
            diagnostica['allegati_list'] = []

    # Formatta output HTML
    output = "<h1>🔍 Diagnostica Generazione PDF</h1><pre>"
    for key, value in diagnostica.items():
        status = "✅" if isinstance(value, bool) and value else "❌" if isinstance(value, bool) else "📊"
        output += f"{status} {key}: {value}\n"
    output += "</pre>"

    return output


@app.route("/reset")
def reset_data():
    """Reset dei dati per nuova compilazione"""
    duvri_id = session.get('current_duvri_id')
    if duvri_id:
        conn = get_db_connection()
        conn.execute(
            'UPDATE duvri SET committente_data = NULL, appaltatore_data = NULL, signatures = NULL WHERE id = ?',
            (duvri_id,)
        )
        conn.commit()
        conn.close()

    session.clear()
    flash("Dati resettati con successo. Puoi iniziare una nuova compilazione.")
    return redirect(url_for("admin_dashboard"))

@app.route("/download/<filename>")
def download_pdf(filename):
    """Serve i PDF dalla cartella documents/"""
    try:
        allowed_files = {
            "duvri_dinamico": "DUVRI_Dinamico_Rev_1_0_1U.pdf",
            "duvri_statico": "DUVRI_STATICO_rev_1_0.pdf"
        }

        if filename not in allowed_files:
            flash("File non autorizzato")
            return redirect(url_for('admin_dashboard'))  # ← CAMBIA QUI

        real_filename = allowed_files[filename]
        pdf_path = os.path.join(BASE_DIR, "documents", real_filename)

        if not os.path.exists(pdf_path):
            flash("File non trovato")
            return redirect(url_for('admin_dashboard'))  # ← CAMBIA QUI

        return send_file(
            pdf_path,
            as_attachment=False,
            download_name=real_filename
        )
    except Exception as e:
        flash(f"Errore: {str(e)}")
        return redirect(url_for('admin_dashboard'))

@app.route('/debug_pdf')
def debug_pdf():
    """Pagina di debug per la generazione PDF"""
    data = get_current_duvri_data()
    duvri_id = session.get('current_duvri_id', 'unknown')

    # Verifica motori PDF
    pdf_info = {
        'xhtml2pdf_available': XHTML2PDF_AVAILABLE,
        'weasyprint_available': WEASYPRINT_AVAILABLE,
        'duvri_id': duvri_id,
        'firme_committente': data.get("signatures", {}).get("committente"),
        'firme_appaltatore': data.get("signatures", {}).get("appaltatore"),
        'output_dir_exists': os.path.exists(os.path.join(BASE_DIR, "output")),
        'allegati_dir_exists': os.path.exists(os.path.join(ALLEGATI_FOLDER, f"duvri_{duvri_id}"))
    }

    # Conta allegati PDF
    allegati_dir = os.path.join(ALLEGATI_FOLDER, f"duvri_{duvri_id}")
    if os.path.exists(allegati_dir):
        pdf_files = [f for f in os.listdir(allegati_dir) if f.lower().endswith('.pdf')]
        pdf_info['num_allegati_pdf'] = len(pdf_files)
        pdf_info['allegati_list'] = pdf_files
    else:
        pdf_info['num_allegati_pdf'] = 0
        pdf_info['allegati_list'] = []

    return render_template('debug_pdf.html', pdf_info=pdf_info)

@app.route("/download_duvri_pdf/<duvri_id>")
def download_duvri_pdf(duvri_id):
    """Scarica il PDF del DUVRI specifico"""
    try:
        # Verifica che il DUVRI esista e sia completato
        if duvri_id not in duvri_list:
            flash("DUVRI non trovato", "danger")
            return redirect(url_for('admin_dashboard'))

        duvri = duvri_list[duvri_id]

        if duvri.get('stato') != 'completato':
            flash("PDF non disponibile. Il DUVRI non è stato completato.", "warning")
            return redirect(url_for('admin_dashboard'))

        # Cerca il PDF nella cartella output
        output_dir = "output"
        if os.path.exists(output_dir):
            for file in os.listdir(output_dir):
                if file.startswith(f"DUVRI_{duvri_id}_"):
                    pdf_path = os.path.join(output_dir, file)
                    return send_file(
                        pdf_path,
                        as_attachment=True,
                        download_name=f"DUVRI_{duvri['nome_progetto']}.pdf"
                    )

        # Se non trova il PDF, reindirizza alla generazione
        session['current_duvri_id'] = duvri_id
        return redirect(url_for('generate_pdf'))

    except Exception as e:
        flash(f"Errore nel recupero del PDF: {str(e)}", "danger")
        return redirect(url_for('admin_dashboard'))

@app.route("/upload_signed/<tipo_firma>", methods=["GET", "POST"])
def upload_signed(tipo_firma):
    """Upload del DUVRI firmato digitalmente - supporta committente e appaltatore"""
    duvri_id = session.get('current_duvri_id')

    if not duvri_id:
        flash("Nessun DUVRI selezionato", "danger")
        return redirect(url_for('admin_dashboard'))

    if tipo_firma not in ['committente', 'appaltatore']:
        flash("Tipo di firma non valido", "danger")
        return redirect(url_for('summary'))

    if request.method == "POST":
        firmatario = request.form.get("firmatario", "").strip()
        if not firmatario:
            flash("Inserire il nome del firmatario")
            return redirect(request.url)

        data_firma = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if "file" not in request.files:
            flash("Nessun file selezionato")
            return redirect(request.url)

        file = request.files["file"]
        if file.filename == "":
            flash("Nessun file scelto")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            # 1. Salva il file PDF nella cartella del DUVRI
            duvri_folder = os.path.join(app.config["UPLOAD_FOLDER"], f"duvri_{duvri_id}")
            os.makedirs(duvri_folder, exist_ok=True)

            filename = secure_filename(f"{tipo_firma}_{firmatario}_{data_firma.replace(':','-')}.pdf")
            filepath = os.path.join(duvri_folder, filename)
            file.save(filepath)

            # 2. Salva i metadati
            meta_path = filepath.replace(".pdf", ".txt")
            with open(meta_path, "w", encoding="utf-8") as meta:
                meta.write(f"Tipo firma: {tipo_firma}\n")
                meta.write(f"Firmatario: {firmatario}\n")
                meta.write(f"Data firma upload: {data_firma}\n")
                meta.write(f"DUVRI ID: {duvri_id}\n")

            # 3. AGGIORNA STATO DELLE FIRME NEL DUVRI
            if duvri_id in duvri_list:
                # Inizializza la struttura per le firme digitali
                if 'firme_digitali' not in duvri_list[duvri_id]:
                    duvri_list[duvri_id]['firme_digitali'] = {}

                # Salva i dati della firma
                duvri_list[duvri_id]['firme_digitali'][tipo_firma] = {
                    'firmatario': firmatario,
                    'data_firma': data_firma,
                    'file_path': filepath
                }

                # ✅ INVIA NOTIFICA quando l'appaltatore completa il DUVRI
                if tipo_firma == 'appaltatore' and duvri_list[duvri_id].get('dati_appaltatore'):
                    dati_appaltatore = duvri_list[duvri_id]['dati_appaltatore']
                    dati_committente = duvri_list[duvri_id].get('dati_committente', {})

                    # Invia notifica al committente
                    if dati_committente.get('email'):
                        invia_notifica_semplice(duvri_id, dati_committente, dati_appaltatore)
                        print(f"📧 Notifica inviata a: {dati_committente['email']}")
                    else:
                        print("⚠️ Nessuna email committente trovata")

                # Verifica se entrambe le parti hanno firmato
                firme_completate = all(
                    ruolo in duvri_list[duvri_id]['firme_digitali']
                    for ruolo in ['committente', 'appaltatore']
                )

                if firme_completate:
                    duvri_list[duvri_id]['stato'] = 'completato_firme_digitali'
                    flash("✅ Documento completamente firmato da entrambe le parti!", "success")
                else:
                    # Aggiorna lo stato parziale
                    if tipo_firma == 'appaltatore':
                        duvri_list[duvri_id]['stato'] = 'firmato_appaltatore'
                    else:
                        duvri_list[duvri_id]['stato'] = 'firmato_committente'

                    flash(f"✅ Firma {tipo_firma} caricata con successo!", "success")

                # Aggiorna anche nel database
                conn = get_db_connection()
                conn.execute(
                    'UPDATE duvri SET stato = ?, updated_at = ? WHERE id = ?',
                    (duvri_list[duvri_id]['stato'], datetime.now(), duvri_id)
                )
                conn.commit()
                conn.close()

            return redirect(url_for("summary"))
        else:
            flash("Formato file non valido. Carica solo PDF.")
            return redirect(request.url)

    return render_template("upload_signed.html", tipo_firma=tipo_firma)

@app.route("/download_per_firma/<tipo_firma>")
def download_per_firma(tipo_firma):
    """Scarica il PDF pronto per la firma digitale"""
    duvri_id = session.get('current_duvri_id')

    if not duvri_id or duvri_id not in duvri_list:
        flash("DUVRI non trovato", "danger")
        return redirect(url_for('summary'))

    duvri = duvri_list[duvri_id]
    data = get_current_duvri_data()

    if tipo_firma == 'appaltatore':
        # Genera il PDF COMPLETO con allegati per la firma
        try:
            # Prepara nome file
            nome_ditta = "Ditta"
            if data.get('appaltatore', {}).get('ragione_sociale'):
                nome_ditta = data['appaltatore']['ragione_sociale']
                nome_ditta = "".join(c for c in nome_ditta if c.isalnum() or c in (' ', '-', '_')).rstrip()
                nome_ditta = nome_ditta.replace(' ', '_')[:30]

            data_oggi = datetime.now().strftime('%Y-%m-%d')
            filename_base = f"DUVRI_{nome_ditta}_{data_oggi}.pdf"
            filename_completo = f"DUVRI_{nome_ditta}_{data_oggi}_PER_FIRMA_APPALTATORE.pdf"
            output_path_base = os.path.join("output", filename_base)
            output_path_completo = os.path.join("output", filename_completo)

            os.makedirs("output", exist_ok=True)

            # Genera il PDF base
            html_content = render_template("pdf_template.html", data=data, datetime=datetime)

            pdf_base_path = None
            if XHTML2PDF_AVAILABLE:
                try:
                    pdf_bytes = io.BytesIO()
                    pisa_status = pisa.CreatePDF(html_content, dest=pdf_bytes)
                    if not pisa_status.err:
                        with open(output_path_base, 'wb') as f:
                            f.write(pdf_bytes.getvalue())
                        pdf_base_path = output_path_base
                except Exception as e:
                    print(f"xhtml2pdf fallito: {e}")

            if not pdf_base_path and WEASYPRINT_AVAILABLE:
                try:
                    HTML(string=html_content).write_pdf(output_path_base)
                    pdf_base_path = output_path_base
                except Exception as e:
                    print(f"WeasyPrint fallito: {e}")

            if not pdf_base_path:
                flash("Errore nella generazione del PDF", "danger")
                return redirect(url_for('summary'))

            # UNISCI CON ALLEGATI per creare il PDF COMPLETO per la firma
            pdf_finale_path = unisci_pdf_duvri(duvri_id, pdf_base_path, output_path_completo)

            flash("✅ PDF per firma generato con tutti gli allegati", "success")
            return send_file(
                pdf_finale_path,
                as_attachment=True,
                download_name=filename_completo
            )

        except Exception as e:
            print(f"Errore generazione PDF per firma: {e}")
            flash(f"Errore nella generazione del PDF per firma: {str(e)}", "danger")
            return redirect(url_for('summary'))

    elif tipo_firma == 'committente':
        # Secondo firmatario - verifica che l'appaltatore abbia già firmato
        firme = duvri.get('firme_digitali', {})
        if 'appaltatore' not in firme:
            flash("L'appaltatore deve prima firmare il documento", "warning")
            return redirect(url_for('summary'))

        # Prepara nome file descrittivo per il download
        nome_ditta = "Ditta"
        if data.get('appaltatore', {}).get('ragione_sociale'):
            nome_ditta = data['appaltatore']['ragione_sociale']
            nome_ditta = "".join(c for c in nome_ditta if c.isalnum() or c in (' ', '-', '_')).rstrip()
            nome_ditta = nome_ditta.replace(' ', '_')[:30]

        data_oggi = datetime.now().strftime('%Y-%m-%d')

        # Restituisci il PDF già firmato dall'appaltatore
        return send_file(
            firme['appaltatore']['file_path'],
            as_attachment=True,
            download_name=f"DUVRI_{nome_ditta}_{data_oggi}_firmato_appaltatore.pdf"
        )

    else:
        flash("Tipo di firma non valido", "danger")
        return redirect(url_for('summary'))

@app.route("/download_duvri_completo")
def download_duvri_completo():
    """Scarica il DUVRI con entrambe le firme digitali (nuovo flusso)"""
    duvri_id = session.get('current_duvri_id')

    if not duvri_id or duvri_id not in duvri_list:
        flash("DUVRI non trovato", "danger")
        return redirect(url_for('summary'))

    duvri = duvri_list[duvri_id]

    # Verifica che entrambe le parti abbiano firmato
    if not duvri.get('firme_digitali') or not all(
        ruolo in duvri['firme_digitali']
        for ruolo in ['committente', 'appaltatore']
    ):
        flash("Il documento non è ancora completamente firmato", "warning")
        return redirect(url_for('summary'))

    # Restituisci l'ultimo documento caricato (quello con entrambe le firme)
    ultimo_file = duvri['firme_digitali']['committente']['file_path']

    return send_file(
        ultimo_file,
        as_attachment=True,
        download_name=f"DUVRI_Completo_Firmato_{duvri['nome_progetto']}.pdf"
    )

def _genera_pdf_base(duvri_id, destinazione):
    """Genera il PDF base del DUVRI"""
    data = get_current_duvri_data()

    # Aggiungi indicazione per la firma
    data['destinazione_firma'] = destinazione

    html_content = render_template("pdf_template.html", data=data, datetime=datetime)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"DUVRI_{duvri_id}_{destinazione}_{timestamp}.pdf"
    output_path = os.path.join("output", filename)

    # Assicurati che la cartella output esista
    os.makedirs("output", exist_ok=True)

    if WEASYPRINT_AVAILABLE:
        HTML(string=html_content).write_pdf(output_path)
    elif XHTML2PDF_AVAILABLE:
        with open(output_path, 'wb') as f:
            pisa.CreatePDF(html_content, dest=f)
    else:
        flash("Nessun motore PDF disponibile", "danger")
        return redirect(url_for('summary'))

    return send_file(
        output_path,
        as_attachment=True,
        download_name=f"DUVRI_da_firmare.pdf"
    )

@app.route("/logout")
def logout():
    """Logout - gestisce uscita appaltatore e admin"""
    if session.get('from_appaltatore_link'):
        # APPALTATORE: pagina di conferma finale
        session.clear()
        return render_template("appaltatore_completato.html")
    else:
        # ADMIN: torna alla dashboard
        session.clear()
        flash("Logout effettuato con successo", "info")
        return redirect(url_for("admin_dashboard"))

@app.route('/upload_allegato', methods=['GET', 'POST'])
def upload_allegato():
    """Upload allegati - versione semplificata"""
    duvri_id = session.get('current_duvri_id')

    if not duvri_id:
        flash("Nessun DUVRI selezionato", "danger")
        return redirect(url_for('summary'))

    if request.method == 'POST':
        if 'allegato' not in request.files:
            flash("Nessun file selezionato", "danger")
            return redirect(request.url)

        file = request.files['allegato']
        if file.filename == '':
            flash("Nessun file scelto", "danger")
            return redirect(request.url)

        if file and allowed_file(file.filename):
            try:
                # Crea cartella per il DUVRI
                duvri_folder = os.path.join(ALLEGATI_FOLDER, f"duvri_{duvri_id}")
                os.makedirs(duvri_folder, exist_ok=True)

                # Salva il file
                filename = secure_filename(file.filename)
                filepath = os.path.join(duvri_folder, filename)
                file.save(filepath)

                flash(f"✅ Allegato '{filename}' caricato con successo!", "success")
                return redirect(url_for('summary'))

            except Exception as e:
                flash(f"❌ Errore durante il caricamento: {str(e)}", "danger")
                return redirect(request.url)
        else:
            flash("❌ Tipo file non consentito", "danger")
            return redirect(request.url)

    return render_template('upload_allegato.html')

@app.route('/elimina_allegato/<int:allegato_index>', methods=['POST'])
def elimina_allegato(allegato_index):
    """Elimina un allegato specifico tramite indice"""
    duvri_id = session.get('current_duvri_id')

    if not duvri_id:
        flash("Nessun DUVRI selezionato", "danger")
        return redirect(url_for('summary'))

    try:
        # Ottieni la lista degli allegati
        allegati_dir = os.path.join(ALLEGATI_FOLDER, f"duvri_{duvri_id}")
        if not os.path.exists(allegati_dir):
            flash("❌ Nessun allegato trovato", "danger")
            return redirect(url_for('summary'))

        # Lista tutti i file nella directory
        files = [f for f in os.listdir(allegati_dir) if os.path.isfile(os.path.join(allegati_dir, f))]
        files.sort()  # Ordina per nome

        if allegato_index < 0 or allegato_index >= len(files):
            flash("❌ Allegato non trovato", "danger")
            return redirect(url_for('summary'))

        filename = files[allegato_index]
        filepath = os.path.join(allegati_dir, filename)

        if os.path.exists(filepath):
            os.remove(filepath)
            flash(f"✅ Allegato '{filename}' eliminato con successo!", "success")
        else:
            flash("❌ Allegato non trovato", "danger")

    except Exception as e:
        flash(f"❌ Errore durante l'eliminazione: {str(e)}", "danger")

    return redirect(url_for('summary'))

@app.route('/download_allegato/<int:allegato_index>')
def download_allegato(allegato_index):
    """Scarica un allegato specifico tramite indice"""
    duvri_id = session.get('current_duvri_id')

    if not duvri_id:
        flash("Nessun DUVRI selezionato", "danger")
        return redirect(url_for('summary'))

    try:
        # Ottieni la lista degli allegati
        allegati_dir = os.path.join(ALLEGATI_FOLDER, f"duvri_{duvri_id}")
        if not os.path.exists(allegati_dir):
            flash("❌ Nessun allegato trovato", "danger")
            return redirect(url_for('summary'))

        # Lista tutti i file nella directory
        files = [f for f in os.listdir(allegati_dir) if os.path.isfile(os.path.join(allegati_dir, f))]
        files.sort()  # Ordina per nome

        if allegato_index < 0 or allegato_index >= len(files):
            flash("❌ Allegato non trovato", "danger")
            return redirect(url_for('summary'))

        filename = files[allegato_index]
        filepath = os.path.join(allegati_dir, filename)

        return send_file(
            filepath,
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        flash(f"❌ Errore durante il download: {str(e)}", "danger")
        return redirect(url_for('summary'))

# =============================================
# ROUTES DI DEBUG
# =============================================

@app.route('/debug_save')
def debug_save():
    """Debug salvataggio dati"""
    duvri_id = session.get('current_duvri_id')

    return {
        'duvri_id': duvri_id,
        'in_memory': duvri_list.get(duvri_id, {}).get('dati_committente', 'NOT_FOUND'),
        'in_database': get_current_duvri_data().get('committente', 'NOT_FOUND'),
        'all_duvri_ids': list(duvri_list.keys())
    }

@app.route('/test_save')
def test_save():
    """Test salvataggio"""
    test_data = {'nome': 'TEST', 'timestamp': datetime.now().isoformat()}
    current_data = get_current_duvri_data()
    current_data['committente'] = test_data
    result = save_current_duvri_data(current_data)
    return f"Salvataggio test: {'SUCCESSO' if result else 'FALLITO'}"

@app.route('/test_summary')
def test_summary():
    """Test della route summary"""
    duvri_id = session.get('current_duvri_id')
    data = get_current_duvri_data()

    return {
        'duvri_id': duvri_id,
        'data_loaded': bool(data),
        'committente_presente': bool(data.get('committente')),
        'appaltatore_presente': bool(data.get('appaltatore')),
        'duvri_list_keys': list(duvri_list.keys())
    }

@app.route('/recover_duvri')
def recover_duvri():
    """Recupera il DUVRI corrente dalla sessione"""
    duvri_id = session.get('current_duvri_id')

    if not duvri_id:
        return "Nessun DUVRI in sessione"

    conn = get_db_connection()
    duvri_db = conn.execute('SELECT * FROM duvri WHERE id = ?', (duvri_id,)).fetchone()
    conn.close()

    if duvri_db:
        if duvri_id not in duvri_list:
            duvri_list[duvri_id] = {
                'id': duvri_id,
                'nome_progetto': duvri_db['nome_progetto'] or 'DUVRI Recuperato',
                'link_appaltatore': str(uuid.uuid4()),
                'stato': duvri_db['stato'] or 'bozza',
                'created_at': duvri_db['created_at'] or datetime.now().strftime('%Y-%m-%d %H:%M'),
                'dati_committente': json.loads(duvri_db['committente_data']) if duvri_db['committente_data'] else {},
                'dati_appaltatore': json.loads(duvri_db['appaltatore_data']) if duvri_db['appaltatore_data'] else {},
                'signatures': json.loads(duvri_db['signatures']) if duvri_db['signatures'] else {}
            }
            return f"✅ DUVRI {duvri_id} recuperato e aggiunto alla memoria!"
        else:
            return f"✅ DUVRI {duvri_id} già in memoria"
    else:
        return f"❌ DUVRI {duvri_id} non trovato nel database"

def load_environment():
    """Carica le variabili d'ambiente in modo robusto"""
    env_files = [
        '.env',           # Nome standard
        'sec.env',        # Il tuo file originale
        'config.env',     # Altri nomi comuni
    ]

    for env_file in env_files:
        env_path = Path('.').absolute() / env_file
        if env_path.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(dotenv_path=env_path)
                print(f"✅ {env_file} caricato da: {env_path}")
                return True
            except Exception as e:
                print(f"❌ Errore caricamento {env_path}: {e}")

    print("⚠️ Nessun file .env trovato, usando variabili di sistema")
    return False

@app.template_filter('b64encode')
def b64encode_filter(filepath):
    """Legge un file e lo converte in base64"""
    try:
        full_path = os.path.join(app.root_path, filepath)
        if os.path.exists(full_path):
            with open(full_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
    except Exception as e:
        print(f"Errore caricamento file {filepath}: {e}")
    return None

# =============================================
# ROUTE privacy
# =============================================
@app.route('/privacy-policy')
def privacy_policy():
    """Pagina Privacy Policy per i cookie"""
    return render_template('privacy_policy.html')

@app.before_request
def load_duvri_on_every_request():
    """Ricarica i DUVRI dal database ad ogni richiesta - previene perdita dati"""
    try:
        # Controlla se la memoria è vuota ma il database ha dati
        conn = get_db_connection()
        db_count = conn.execute('SELECT COUNT(*) as count FROM duvri').fetchone()['count']
        conn.close()

        if db_count > 0 and len(duvri_list) == 0:
            print(f"🔄 Ricaricamento automatico: {db_count} DUVRI dal database")
            sync_all_duvri_from_db()

    except Exception as e:
        print(f"⚠️ Errore nel ricaricamento automatico: {e}")



if __name__ == "__main__":
    # =============================================
    # CARICAMENTO VARIABILI AMBIENTE
    # =============================================
    load_environment()

    # Debug variabili
    print("=== VARIABILI AMBIENTE ===")
    print(f"SECRET_KEY: {'✅ Configurata' if os.environ.get('SECRET_KEY') else '❌ Non trovata'}")
    print(f"FLASK_ENV: {os.environ.get('FLASK_ENV', 'development')}")
    print("==========================")

    # =============================================
    # INIZIALIZZAZIONE APPLICAZIONE
    # =============================================
    # Inizializza il database
    init_db()

    # Sincronizza tutti i DUVRI dal database alla memoria
    sync_all_duvri_from_db()

    print(f"🚀 Avviato con {len(duvri_list)} DUVRI in memoria")

    # =============================================
    # AVVIO SERVER
    # =============================================
    if os.environ.get('PYTHONANYWHERE_DOMAIN'):
        # Produzione su PythonAnywhere
        print("📍 Modalità: PythonAnywhere (Produzione)")
        app.run(debug=False, host='0.0.0.0')
    else:
        # Sviluppo locale
        print("📍 Modalità: Sviluppo Locale")
        debug_mode = os.environ.get('FLASK_ENV') == 'development'
        app.run(debug=debug_mode, host='0.0.0.0', port=5000)
