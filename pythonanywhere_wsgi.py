import os
import sys

# Aggiungi il percorso della tua app
path = '/home/tuo_username/duvri-app'
if path not in sys.path:
    sys.path.append(path)

# Imposta le variabili d'ambiente per PRODUZIONE
os.environ['SECRET_KEY'] = 'inserisci-qui-una-secret-key-molto-lunga-e-sicura'
os.environ['FLASK_ENV'] = 'production'
os.environ['PYTHONANYWHERE_DOMAIN'] = 'pythonanywhere'

# Importa l'app Flask
from app import app as application