# ✅ Checklist Go-Live Produzione
## Sistema DUVRI Dinamico - USL Toscana Nord Ovest

**Data prevista go-live:** _____________

---

## 📋 Pre-Produzione

### Configurazione Sistema

- [ ] **SECRET_KEY sicura configurata** nel file WSGI
  - [ ] Generata con `python -c "import secrets; print(secrets.token_hex(32))"`
  - [ ] NON committata nel repository
  - [ ] Diversa da quella di sviluppo

- [ ] **Database SQLite** correttamente inizializzato
  - [ ] File `duvri_database.db` creato
  - [ ] Permessi corretti (rw per app)
  - [ ] Backup automatico configurato

- [ ] **Credenziali Admin** configurate
  - [ ] Username sicuro (NON "admin")
  - [ ] Password forte (min 12 caratteri, lettere+numeri+simboli)
  - [ ] Documentate in luogo sicuro

- [ ] **File WSGI** configurato correttamente
  - [ ] Path corretti per il progetto
  - [ ] Variabili ambiente impostate
  - [ ] SECRET_KEY configurata

### Test Funzionali

- [ ] **Login admin funzionante**
  - [ ] Accesso con credenziali
  - [ ] Logout corretto
  - [ ] Session persistente

- [ ] **Flusso Committente completo**
  - [ ] Creazione nuovo DUVRI
  - [ ] Compilazione form committente
  - [ ] Salvataggio corretto dati
  - [ ] Generazione link appaltatore

- [ ] **Flusso Appaltatore completo**
  - [ ] Accesso tramite link univoco
  - [ ] Compilazione form appaltatore
  - [ ] Salvataggio corretto
  - [ ] Redirect a summary
  - [ ] Pulsante "Completato - Esci" visibile
  - [ ] NO pulsante "Torna alla Dashboard"

- [ ] **Calcolo Costi**
  - [ ] Calcolo automatico funzionante
  - [ ] Confronto costi gara vs operativi
  - [ ] Segnalazione extra-costi corretta
  - [ ] Calcolo percentuali preciso

- [ ] **Generazione PDF**
  - [ ] PDF genera correttamente
  - [ ] Layout conforme normativa
  - [ ] Tutti i dati presenti
  - [ ] Logo USL visibile

- [ ] **Gestione Firme Digitali**
  - [ ] Upload PDF firmato funzionante
  - [ ] Download per firma disponibile
  - [ ] Workflow sequenziale corretto

### Test di Sicurezza

- [ ] **HTTPS attivo e funzionante**
  - [ ] Certificato SSL valido
  - [ ] Redirect HTTP → HTTPS

- [ ] **Link appaltatori sicuri**
  - [ ] UUID univoci generati
  - [ ] Impossibile indovinare link
  - [ ] Nessun accesso non autorizzato

- [ ] **Session sicure**
  - [ ] Cookie con flag secure
  - [ ] Session timeout appropriato
  - [ ] from_appaltatore_link gestito correttamente

- [ ] **Input Validation**
  - [ ] Campi obbligatori validati
  - [ ] SQL injection prevenuta (ORM/parametrizzazione)
  - [ ] XSS prevenuto (Jinja2 auto-escape)
  - [ ] File upload sicuri (tipo, dimensione)

### Performance

- [ ] **Caricamento pagine < 2 secondi**
  - [ ] Dashboard
  - [ ] Form committente
  - [ ] Form appaltatore
  - [ ] Summary

- [ ] **Database ottimizzato**
  - [ ] Indici su campi chiave
  - [ ] Query efficienti

### Backup e Disaster Recovery

- [ ] **Backup automatici configurati**
  - [ ] Frequenza: giornaliera
  - [ ] Retention: 30 giorni
  - [ ] Test di restore effettuato

- [ ] **Procedura di ripristino documentata**
  - [ ] Step-by-step scritti
  - [ ] Testati almeno una volta

---

## 📚 Documentazione

- [ ] **Guida RUP** (GUIDA_RUP.html)
  - [ ] Credenziali personalizzate
  - [ ] Contatti supporto aggiornati
  - [ ] Email ICT/SPP corrette
  - [ ] Distribuita a tutti i RUP

- [ ] **Documentazione Tecnica**
  - [ ] README.md aggiornato
  - [ ] Architettura sistema documentata
  - [ ] Procedura deploy documentata

- [ ] **Modelli Email**
  - [ ] Template per invio link appaltatore
  - [ ] Template notifiche RSPP
  - [ ] Template comunicazioni standard

---

## 👥 Formazione Utenti

- [ ] **Sessione formazione RUP**
  - [ ] Data: _____________
  - [ ] Partecipanti: ___ / ___ RUP
  - [ ] Registrazione effettuata
  - [ ] Domande documentate

- [ ] **Materiale formativo distribuito**
  - [ ] Guida RUP HTML
  - [ ] Video tutorial (se disponibile)
  - [ ] FAQ

- [ ] **Utenti di test designati**
  - [ ] 2-3 RUP pilot
  - [ ] Test DUVRI reali completati
  - [ ] Feedback raccolto e indirizzato

---

## 🔧 Supporto Post Go-Live

- [ ] **Team supporto identificato**
  - [ ] Supporto tecnico ICT: __________
  - [ ] Supporto normativo SPP: __________
  - [ ] Escalation manager: __________

- [ ] **Canali supporto attivi**
  - [ ] Email supporto monitorata
  - [ ] Telefono disponibile
  - [ ] Orari di supporto comunicati

- [ ] **Sistema di tracking issue**
  - [ ] Email dedicata o ticketing
  - [ ] SLA definiti
  - [ ] Procedure di escalation

---

## 📊 Monitoraggio

- [ ] **Metriche da monitorare**
  - [ ] Numero DUVRI creati/settimana
  - [ ] Tempo medio compilazione
  - [ ] Errori segnalati
  - [ ] Tempo risposta supporto

- [ ] **Dashboard monitoraggio**
  - [ ] Log errori monitorati
  - [ ] Spazio disco controllato
  - [ ] Performance monitorate

---

## 📢 Comunicazioni

- [ ] **Email annuncio go-live**
  - [ ] Inviata a tutti i RUP
  - [ ] Data go-live comunicata
  - [ ] Contatti supporto inclusi

- [ ] **Comunicazione appalti in corso**
  - [ ] Identificati appalti attivi
  - [ ] Piano migrazione definito
  - [ ] RUP informati del cambio processo

---

## ⚖️ Conformità Normativa

- [ ] **D.Lgs 81/2008 Art. 26**
  - [ ] Tutti i campi obbligatori presenti
  - [ ] Calcolo costi conforme
  - [ ] DUVRI include tutte le sezioni richieste

- [ ] **D.Lgs 50/2016 (Codice Appalti)**
  - [ ] Gestione costi sicurezza corretta
  - [ ] Extra-costi gestiti secondo normativa

- [ ] **GDPR**
  - [ ] Privacy Policy presente e aggiornata
  - [ ] Cookie banner funzionante
  - [ ] Dati personali protetti
  - [ ] Retention policy definita

---

## 🚀 Go-Live Day

### Mattina (ore 8:00)

- [ ] **Backup completo pre-go-live**
  - [ ] Database
  - [ ] File system
  - [ ] Configurazioni

- [ ] **Controllo finale sistema**
  - [ ] Tutti i servizi running
  - [ ] Log puliti
  - [ ] Spazio disco OK

- [ ] **Email annuncio go-live** inviata
  - [ ] RUP
  - [ ] Management
  - [ ] Supporto tecnico

### Durante il giorno

- [ ] **Monitoraggio attivo**
  - [ ] Log errori controllati ogni ora
  - [ ] Supporto disponibile full-time
  - [ ] Issue tracker monitorato

- [ ] **Primo DUVRI di produzione**
  - [ ] Creato con successo
  - [ ] Workflow completo testato
  - [ ] PDF generato e firmato

### Sera (ore 18:00)

- [ ] **Riepilogo giornata**
  - [ ] Issue riscontrati: ___
  - [ ] Issue risolti: ___
  - [ ] DUVRI creati: ___
  - [ ] Utenti attivi: ___

- [ ] **Backup post go-live**

---

## 📅 Settimana 1 Post Go-Live

- [ ] **Monitoraggio intensivo**
  - [ ] Log controllati 2x/giorno
  - [ ] Call settimanale con RUP pilot
  - [ ] Feedback raccolto

- [ ] **Ottimizzazioni rapide**
  - [ ] Bug critici risolti entro 24h
  - [ ] Miglioramenti UX implementati

- [ ] **Report settimanale**
  - [ ] Metriche utilizzo
  - [ ] Issue riscontrati e risolti
  - [ ] Feedback utenti
  - [ ] Piano azioni successive

---

## ✍️ Firme Approvazione

**Responsabile Progetto ICT:**

Nome: ___________________________
Firma: ___________________________
Data: ____________________________

**Responsabile SPP:**

Nome: ___________________________
Firma: ___________________________
Data: ____________________________

**Direttore Generale / Delegato:**

Nome: ___________________________
Firma: ___________________________
Data: ____________________________

---

## 📝 Note Aggiuntive

_Spazio per annotazioni, issue particolari, o elementi da ricordare:_

_______________________________________________________________________________

_______________________________________________________________________________

_______________________________________________________________________________

_______________________________________________________________________________

_______________________________________________________________________________

---

**Documento preparato da:** Claude AI Assistant
**Versione:** 1.0
**Data documento:** Dicembre 2025
