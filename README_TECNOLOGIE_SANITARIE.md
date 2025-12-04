# Analisi Tecnologie Sanitarie PNRR
## USL Toscana Nord Ovest - Case di Comunità e Ospedali di Comunità

## 📁 File del progetto

### File CSV (dati sorgente)
- **`tecnologie_cdc_dettaglio.csv`** - Dettaglio tecnologie per Case di Comunità (26 righe)
- **`tecnologie_odc_dettaglio.csv`** - Dettaglio tecnologie per Ospedali di Comunità (22 righe)
- **`riepilogo_strutture.csv`** - Totali per ogni struttura (22 righe)

### File Excel originale
- **`Stima arredi PNRR (1).xlsx`** - File Excel originale con tutti i dati

### Script di analisi
- **`analisi_tecnologie_sanitarie.py`** - Script Python interattivo per visualizzazione e analisi

## 🚀 Come usare lo script Python

### Prerequisiti
```bash
# Installa le dipendenze necessarie
pip3 install pandas openpyxl
```

### Esecuzione
```bash
# Esegui lo script
python3 analisi_tecnologie_sanitarie.py
```

### Funzionalità disponibili

Lo script presenta un menu interattivo con le seguenti opzioni:

1. **Riepilogo Generale** - Vista d'insieme con totali CdC e OdC
2. **Riepilogo per Tecnologia** - Aggregazione per tipo di tecnologia
3. **Top 10 Strutture** - Classifica delle strutture per investimento
4. **Dettaglio CdC** - Lista completa per ogni Casa di Comunità
5. **Dettaglio OdC** - Lista completa per ogni Ospedale di Comunità
6. **Visualizza tutto** - Tutti i report in sequenza
7. **Esporta Excel** - Genera file `report_tecnologie_sanitarie.xlsx`

## 📊 Dati principali

### Totali
- **Case di Comunità**: 155 unità → €142.259,66
- **Ospedali di Comunità**: 108 unità → €221.292,63
- **TOTALE GENERALE**: 263 unità → €363.552,29

### Tecnologie principali
- Letto elettrico degenza (LINET): 89 unità → €153.358,39
- LETTINO VISITA ELETTRICO: 145 unità → €122.960,00
- Lavapadelle (ARJO): 5 unità → €25.241,69
- Sollevatore (ARJO): 4 unità → €18.720,00
- FRIGORIFERO: 5 unità → €15.000,00

### Top 5 strutture per investimento
1. OdC Viareggio → €92.725,55
2. OdC Barga → €49.059,03
3. OdC Massa → €46.059,03
4. CdC Massa → €33.920,00
5. OdC Cecina → €24.833,36

## 🔄 Aggiornamento dati

### Modificare i file CSV
I file CSV sono modificabili con Excel, Google Sheets o qualsiasi editor:

```csv
Tipologia,Tecnologia,Locale,Struttura,Quantita,Costo_Unitario_EUR,Importo_Totale_EUR
CdC,LETTINO VISITA ELETTRICO,AMBULATORIO MEDICO,CdC Carrara,1,848.00,848.00
```

**Per aggiungere nuove tecnologie:**
1. Apri il file CSV appropriato (cdc o odc)
2. Aggiungi una nuova riga con i dati
3. Salva il file
4. Riesegui lo script Python

**Per modificare quantità:**
1. Modifica il campo `Quantita`
2. Ricalcola `Importo_Totale_EUR` = Quantita × Costo_Unitario_EUR
3. Salva

### Formato colonne CSV

#### File dettaglio (cdc/odc)
- `Tipologia`: "CdC" o "OdC"
- `Tecnologia`: Nome completo della tecnologia
- `Locale`: Locale di destinazione (es. "AMBULATORIO MEDICO")
- `Struttura`: Nome della struttura (es. "CdC Carrara")
- `Quantita`: Numero intero di unità
- `Costo_Unitario_EUR`: Costo per unità (formato: 1234.56)
- `Importo_Totale_EUR`: Quantita × Costo_Unitario_EUR

#### File riepilogo strutture
- `Tipologia`: "CdC" o "OdC"
- `Struttura`: Nome della struttura
- `Importo_Totale_EUR`: Totale per la struttura

## 📈 Esempi di utilizzo

### Esempio 1: Vista rapida
```bash
python3 analisi_tecnologie_sanitarie.py
# Seleziona opzione 1 per riepilogo generale
```

### Esempio 2: Esportazione Excel
```bash
python3 analisi_tecnologie_sanitarie.py
# Seleziona opzione 7 per creare report_tecnologie_sanitarie.xlsx
```

### Esempio 3: Analisi per tecnologia
```bash
python3 analisi_tecnologie_sanitarie.py
# Seleziona opzione 2 per vedere aggregazione per tecnologia
```

## 🔧 Troubleshooting

### Errore "No module named 'pandas'"
```bash
pip3 install pandas openpyxl
```

### Errore "File not found"
Assicurati di essere nella directory corretta:
```bash
cd /path/to/duvri-generator
ls *.csv  # Verifica presenza file CSV
```

### I dati non corrispondono
Verifica che i file CSV non siano stati modificati accidentalmente:
```bash
git status
git diff  # Mostra modifiche
```

## 📝 Note

- I costi sono espressi in Euro (IVA esclusa per CdC, IVA inclusa per OdC)
- Le quantità sono numeri interi
- I file CSV usano encoding UTF-8
- Il separatore CSV è la virgola (,)

## 📞 Contatti

Per domande o supporto, contattare il RUP della struttura di riferimento.

---

**Ultimo aggiornamento**: Dicembre 2025
**Progetto**: PNRR - Missione 6 Salute
