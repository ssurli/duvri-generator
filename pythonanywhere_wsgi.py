"""
WSGI Configuration per PythonAnywhere

ISTRUZIONI SETUP:
1. Sostituisci 'TUO_USERNAME' con il tuo username PythonAnywhere
2. Genera una SECRET_KEY sicura (puoi usare: python -c "import secrets; print(secrets.token_hex(32))")
3. Sostituisci 'TUA_SECRET_KEY_QUI' con la chiave generata
4. Configura questo file nella sezione "Web" di PythonAnywhere come WSGI configuration file
"""

import os
import sys

# ============================================
# CONFIGURAZIONE PATH - MODIFICA QUI
# ============================================
# Sostituisci 'TUO_USERNAME' con il tuo username PythonAnywhere
USERNAME = 'TUO_USERNAME'
APP_NAME = 'duvri-generator'

path = f'/home/{USERNAME}/{APP_NAME}'
if path not in sys.path:
    sys.path.append(path)

# ============================================
# VARIABILI D'AMBIENTE - MODIFICA QUI
# ============================================
# Genera una chiave segreta con: python -c "import secrets; print(secrets.token_hex(32))"
os.environ['SECRET_KEY'] = 'TUA_SECRET_KEY_QUI'
os.environ['FLASK_ENV'] = 'production'
os.environ['PYTHONANYWHERE_DOMAIN'] = 'pythonanywhere'

# ============================================
# IMPORTA L'APP FLASK
# ============================================
from app import app as application