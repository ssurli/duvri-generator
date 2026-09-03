# 🚀 Guida Deploy su PythonAnywhere (Free Tier)

## ✅ Verifica Compatibilità

**Dimensioni progetto**: ~172MB ✅ (limite free: 500MB)

**Motore PDF**: xhtml2pdf (compatibile con PythonAnywhere free)
- ⚠️ WeasyPrint NON funzionerà su free tier (richiede librerie di sistema)
- ✅ L'app usa già xhtml2pdf come motore principale

---

## 📋 Prerequisiti

1. Account PythonAnywhere (free tier è sufficiente)
2. Git installato sul tuo computer locale
3. Repository Git del progetto

---

## 🔧 Passi per il Deploy

### 1. Prepara il Repository Locale

```bash
# Assicurati che .local/ e .ipython/ non siano nel repository
git status

# Se vedi .local/ o .ipython/, rimuovili:
git rm -r --cached .local .ipython
git commit -m "Remove local Python packages from repo"
git push
```

### 2. Crea Web App su PythonAnywhere

1. Vai su PythonAnywhere Dashboard
2. Clicca su "Web" tab
3. Clicca "Add a new web app"
4. Scegli:
   - **Domain**: `tuousername.pythonanywhere.com`
   - **Python version**: Python 3.10 (o la più recente disponibile)
   - **Framework**: Manual configuration

### 3. Clona il Repository

Apri un **Bash console** su PythonAnywhere:

```bash
cd ~
git clone https://github.com/TUO_USERNAME/duvri-generator.git
cd duvri-generator
```

### 4. Crea Virtual Environment

```bash
# Crea virtual environment
mkvirtualenv --python=/usr/bin/python3.10 duvri-env

# Attiva l'ambiente (se non già attivo)
workon duvri-env

# Installa dipendenze (USA requirements_pythonanywhere.txt!)
pip install -r requirements_pythonanywhere.txt
```

⚠️ **IMPORTANTE**: Usa `requirements_pythonanywhere.txt` e NON `requirements.txt` perché esclude WeasyPrint.

### 5. Configura WSGI File

1. Vai su **Web** tab
2. Clicca su **"WSGI configuration file"** (es. `/var/www/tuousername_pythonanywhere_com_wsgi.py`)
3. Sostituisci tutto il contenuto con:

```python
"""
WSGI Configuration per PythonAnywhere
"""

import os
import sys

# ============================================
# CONFIGURAZIONE PATH - MODIFICA QUI
# ============================================
USERNAME = 'TUO_USERNAME'  # ⚠️ SOSTITUISCI CON IL TUO USERNAME
APP_NAME = 'duvri-generator'

path = f'/home/{USERNAME}/{APP_NAME}'
if path not in sys.path:
    sys.path.append(path)

# ============================================
# VIRTUAL ENVIRONMENT
# ============================================
# Percorso al virtual environment
venv_path = f'/home/{USERNAME}/.virtualenvs/duvri-env'
activate_this = os.path.join(venv_path, 'bin/activate_this.py')

# Attiva il virtual environment
with open(activate_this) as f:
    exec(f.read(), {'__file__': activate_this})

# ============================================
# VARIABILI D'AMBIENTE - MODIFICA QUI
# ============================================
# Genera una chiave segreta sicura con:
# python -c "import secrets; print(secrets.token_hex(32))"
os.environ['SECRET_KEY'] = 'TUA_SECRET_KEY_QUI'  # ⚠️ GENERA E SOSTITUISCI
os.environ['FLASK_ENV'] = 'production'
os.environ['PYTHONANYWHERE_DOMAIN'] = 'pythonanywhere'

# ============================================
# IMPORTA L'APP FLASK
# ============================================
from app import app as application
```

### 6. Genera SECRET_KEY

Nel Bash console di PythonAnywhere:

```bash
workon duvri-env
python -c "import secrets; print(secrets.token_hex(32))"
```

Copia l'output e sostituiscilo nel file WSGI al posto di `TUA_SECRET_KEY_QUI`.

### 6.1 Configura notifica email (opzionale)

Per ricevere una **notifica email al tuo indirizzo aziendale** ogni volta che
un appaltatore preme **"Salva Dati Appaltatore"**, aggiungi queste variabili
nel file WSGI (subito sotto `SECRET_KEY`):

```python
os.environ['NOTIFICA_EMAIL'] = 'tua-email-aziendale@esempio.it'
os.environ['SMTP_HOST'] = 'smtp.gmail.com'
os.environ['SMTP_PORT'] = '587'
os.environ['SMTP_USER'] = 'iltuoaccount@gmail.com'
os.environ['SMTP_PASSWORD'] = 'la_tua_app_password'
os.environ['SMTP_FROM'] = 'iltuoaccount@gmail.com'   # opzionale
```

Note importanti:

- Con **Gmail** serve una *App Password* (Google Account → Sicurezza →
  Verifica in due passaggi → Password per le app), non la password normale.
- Su PythonAnywhere **Free Tier** l'invio SMTP è consentito solo verso i
  server nella whitelist (Gmail è incluso). Per altri provider serve un
  account a pagamento.
- Se queste variabili **non** sono impostate, l'app funziona comunque: la
  notifica viene solo scritta nel log, senza inviare email.

### 7. Configura Directory Statiche

Nella sezione **Web** > **Static files**:

| URL           | Directory                                      |
|---------------|------------------------------------------------|
| `/static/`    | `/home/TUO_USERNAME/duvri-generator/static`    |

⚠️ Sostituisci `TUO_USERNAME` con il tuo username PythonAnywhere.

### 8. Crea Directory Necessarie

Nel Bash console:

```bash
cd ~/duvri-generator
mkdir -p uploads/ditte uploads/allegati uploads_duvri_estar output documents/templates
chmod 755 uploads uploads_duvri_estar output
```

### 9. Inizializza Database

```bash
workon duvri-env
cd ~/duvri-generator
python database.py
```

Dovresti vedere: `✅ Database inizializzato: /home/TUO_USERNAME/duvri-generator/duvri.db`

### 10. Reload Web App

1. Torna su **Web** tab
2. Clicca sul pulsante verde **"Reload tuousername.pythonanywhere.com"**
3. Attendi qualche secondo

### 11. Testa l'App

Vai su: `https://tuousername.pythonanywhere.com`

---

## 🐛 Troubleshooting

### Errore: ModuleNotFoundError

**Causa**: Virtual environment non configurato correttamente

**Soluzione**:
```bash
workon duvri-env
pip install -r requirements_pythonanywhere.txt
```

Verifica che il file WSGI contenga il codice per attivare il virtual environment.

### Errore: 500 Internal Server Error

**Causa**: Errore nell'app

**Soluzione**:
1. Vai su **Web** tab
2. Clicca su **"Error log"**
3. Cerca l'errore più recente
4. Correggi l'errore nel codice
5. Fai `git pull` per aggiornare
6. Reload dell'app

### Errore: Static files non caricano

**Causa**: Path statici non configurati

**Soluzione**:
- Verifica la sezione **Static files** nella Web tab
- Assicurati che il path sia assoluto: `/home/TUO_USERNAME/duvri-generator/static`

### Errore: Database locked

**Causa**: Permessi del file database

**Soluzione**:
```bash
chmod 666 ~/duvri-generator/duvri.db
chmod 777 ~/duvri-generator
```

### PDF non si generano

**Causa**: Probabile problema con le librerie PDF

**Verifica**:
```bash
workon duvri-env
python -c "from xhtml2pdf import pisa; print('xhtml2pdf OK')"
```

Se fallisce:
```bash
pip install --upgrade xhtml2pdf reportlab
```

---

## 📊 Limiti Free Tier

- **Spazio disco**: 500MB ✅ (progetto: ~172MB)
- **CPU time**: 100 secondi/giorno (rigenerato ogni 24h)
- **Web requests**: illimitate
- **Database**: SQLite incluso ✅

**Consigli per risparmiare spazio**:
- Pulisci periodicamente la cartella `output/`
- Pulisci periodicamente la cartella `uploads/`

---

## 🔄 Aggiornamenti Futuri

Quando fai modifiche al codice:

```bash
# Su PythonAnywhere Bash console
cd ~/duvri-generator
git pull
workon duvri-env
pip install -r requirements_pythonanywhere.txt  # se hai aggiornato dipendenze
```

Poi vai su **Web** tab e clicca **"Reload"**.

---

## 🔐 Sicurezza

1. ✅ Usa sempre HTTPS (PythonAnywhere lo fornisce automaticamente)
2. ✅ Non committare mai la SECRET_KEY nel repository
3. ✅ SECRET_KEY deve essere lunga e casuale (almeno 32 caratteri)
4. ✅ Session cookies configurati come secure e httponly

---

## 📞 Supporto

- **PythonAnywhere Forums**: https://www.pythonanywhere.com/forums/
- **PythonAnywhere Help**: https://help.pythonanywhere.com/
- **Documentazione Flask**: https://flask.palletsprojects.com/

---

## ✨ Checklist Finale

- [ ] Repository clonato su PythonAnywhere
- [ ] Virtual environment creato e attivato
- [ ] Dipendenze installate da `requirements_pythonanywhere.txt`
- [ ] File WSGI configurato con USERNAME e SECRET_KEY
- [ ] Static files configurati
- [ ] Directory uploads create
- [ ] Database inizializzato
- [ ] Web app reloaded
- [ ] App funzionante su `https://tuousername.pythonanywhere.com`

Buon deploy! 🚀
