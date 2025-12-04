#!/usr/bin/env python3
"""
Script per l'analisi e visualizzazione delle tecnologie sanitarie PNRR
USL Toscana Nord Ovest - Case di Comunità e Ospedali di Comunità

Utilizzo:
    python3 analisi_tecnologie_sanitarie.py
"""

import pandas as pd
import sys
from pathlib import Path

# Configurazione output
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.float_format', lambda x: f'€{x:,.2f}')


def stampa_sezione(titolo, carattere="=", larghezza=100):
    """Stampa una sezione formattata"""
    print("\n" + carattere * larghezza)
    print(titolo.center(larghezza))
    print(carattere * larghezza + "\n")


def carica_dati():
    """Carica i file CSV"""
    try:
        df_cdc = pd.read_csv('tecnologie_cdc_dettaglio.csv')
        df_odc = pd.read_csv('tecnologie_odc_dettaglio.csv')
        df_riepilogo = pd.read_csv('riepilogo_strutture.csv')

        # Converti colonne numeriche
        df_cdc['Importo_Totale_EUR'] = pd.to_numeric(df_cdc['Importo_Totale_EUR'])
        df_odc['Importo_Totale_EUR'] = pd.to_numeric(df_odc['Importo_Totale_EUR'])
        df_riepilogo['Importo_Totale_EUR'] = pd.to_numeric(df_riepilogo['Importo_Totale_EUR'])

        return df_cdc, df_odc, df_riepilogo
    except FileNotFoundError as e:
        print(f"❌ Errore: File non trovato - {e}")
        print("Assicurati di essere nella directory corretta con i file CSV.")
        sys.exit(1)


def visualizza_riepilogo_generale(df_cdc, df_odc, df_riepilogo):
    """Visualizza il riepilogo generale"""
    stampa_sezione("RIEPILOGO GENERALE TECNOLOGIE SANITARIE PNRR")

    totale_cdc = df_cdc['Importo_Totale_EUR'].sum()
    totale_odc = df_odc['Importo_Totale_EUR'].sum()
    totale_generale = totale_cdc + totale_odc

    quantita_cdc = df_cdc['Quantita'].sum()
    quantita_odc = df_odc['Quantita'].sum()
    quantita_totale = quantita_cdc + quantita_odc

    print(f"{'Tipologia':<30} {'Quantità':>12} {'Importo Totale':>20}")
    print("-" * 65)
    print(f"{'Case di Comunità (CdC)':<30} {quantita_cdc:>12,} {f'€{totale_cdc:,.2f}':>20}")
    print(f"{'Ospedali di Comunità (OdC)':<30} {quantita_odc:>12,} {f'€{totale_odc:,.2f}':>20}")
    print("-" * 65)
    print(f"{'TOTALE GENERALE':<30} {quantita_totale:>12,} {f'€{totale_generale:,.2f}':>20}")
    print()


def visualizza_tecnologie_per_categoria(df_cdc, df_odc):
    """Visualizza riepilogo per tecnologia"""
    stampa_sezione("RIEPILOGO PER TECNOLOGIA")

    # Combina CdC e OdC
    df_all = pd.concat([df_cdc, df_odc])

    # Aggrega per tecnologia
    riepilogo_tech = df_all.groupby('Tecnologia').agg({
        'Quantita': 'sum',
        'Costo_Unitario_EUR': 'first',
        'Importo_Totale_EUR': 'sum'
    }).round(2)

    # Ordina per importo decrescente
    riepilogo_tech = riepilogo_tech.sort_values('Importo_Totale_EUR', ascending=False)

    print(f"{'Tecnologia':<55} {'Qty':>6} {'Costo Unit.':>15} {'Totale':>20}")
    print("-" * 100)

    for idx, row in riepilogo_tech.iterrows():
        tecnologia = idx[:50] + "..." if len(idx) > 50 else idx
        costo_unit = f"€{row['Costo_Unitario_EUR']:,.2f}"
        importo_tot = f"€{row['Importo_Totale_EUR']:,.2f}"
        print(f"{tecnologia:<55} {int(row['Quantita']):>6} {costo_unit:>15} {importo_tot:>20}")

    print("-" * 100)
    totale_finale = f"€{riepilogo_tech['Importo_Totale_EUR'].sum():,.2f}"
    print(f"{'TOTALE':<55} {int(riepilogo_tech['Quantita'].sum()):>6} {'':>15} {totale_finale:>20}")
    print()


def visualizza_top_strutture(df_riepilogo, n=10):
    """Visualizza le top N strutture per investimento"""
    stampa_sezione(f"TOP {n} STRUTTURE PER INVESTIMENTO")

    top_strutture = df_riepilogo.nlargest(n, 'Importo_Totale_EUR')

    print(f"{'Pos':>4} {'Tipo':>6} {'Struttura':<50} {'Importo Totale':>20}")
    print("-" * 85)

    for i, (_, row) in enumerate(top_strutture.iterrows(), 1):
        importo = f"€{row['Importo_Totale_EUR']:,.2f}"
        print(f"{i:>4} {row['Tipologia']:>6} {row['Struttura']:<50} {importo:>20}")

    print()


def visualizza_dettaglio_cdc(df_cdc):
    """Visualizza dettaglio completo CdC"""
    stampa_sezione("DETTAGLIO CASE DI COMUNITÀ (CdC)", "-")

    for struttura in sorted(df_cdc['Struttura'].unique()):
        df_strutt = df_cdc[df_cdc['Struttura'] == struttura]
        totale = df_strutt['Importo_Totale_EUR'].sum()

        print(f"\n📍 {struttura} - Totale: €{totale:,.2f}")
        print("-" * 80)

        for _, row in df_strutt.iterrows():
            print(f"  • {row['Tecnologia'][:60]:<60}")
            print(f"    Quantità: {int(row['Quantita']):>3} × €{row['Costo_Unitario_EUR']:>10,.2f} = €{row['Importo_Totale_EUR']:>12,.2f}")
            if row['Locale']:
                print(f"    Locale: {row['Locale']}")


def visualizza_dettaglio_odc(df_odc):
    """Visualizza dettaglio completo OdC"""
    stampa_sezione("DETTAGLIO OSPEDALI DI COMUNITÀ (OdC)", "-")

    for struttura in sorted(df_odc['Struttura'].unique()):
        df_strutt = df_odc[df_odc['Struttura'] == struttura]
        totale = df_strutt['Importo_Totale_EUR'].sum()

        print(f"\n🏥 {struttura} - Totale: €{totale:,.2f}")
        print("-" * 80)

        for _, row in df_strutt.iterrows():
            print(f"  • {row['Tecnologia'][:60]:<60}")
            print(f"    Quantità: {int(row['Quantita']):>3} × €{row['Costo_Unitario_EUR']:>10,.2f} = €{row['Importo_Totale_EUR']:>12,.2f}")
            if row['Locale']:
                print(f"    Locale: {row['Locale']}")


def esporta_report_excel(df_cdc, df_odc, df_riepilogo):
    """Esporta un report completo in Excel"""
    try:
        output_file = 'report_tecnologie_sanitarie.xlsx'

        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            # Combina dati
            df_all = pd.concat([df_cdc, df_odc])

            # Riepilogo per tecnologia
            riepilogo_tech = df_all.groupby('Tecnologia').agg({
                'Quantita': 'sum',
                'Costo_Unitario_EUR': 'first',
                'Importo_Totale_EUR': 'sum'
            }).round(2).sort_values('Importo_Totale_EUR', ascending=False)

            # Scrivi fogli
            df_cdc.to_excel(writer, sheet_name='CdC Dettaglio', index=False)
            df_odc.to_excel(writer, sheet_name='OdC Dettaglio', index=False)
            df_riepilogo.to_excel(writer, sheet_name='Riepilogo Strutture', index=False)
            riepilogo_tech.to_excel(writer, sheet_name='Riepilogo Tecnologie')

        print(f"\n✅ Report Excel esportato: {output_file}")
        return True
    except Exception as e:
        print(f"\n⚠️  Impossibile esportare Excel (openpyxl non installato): {e}")
        return False


def menu_interattivo(df_cdc, df_odc, df_riepilogo):
    """Menu interattivo per scegliere la visualizzazione"""
    while True:
        stampa_sezione("MENU ANALISI TECNOLOGIE SANITARIE", "═")
        print("1. Riepilogo Generale")
        print("2. Riepilogo per Tecnologia")
        print("3. Top 10 Strutture per Investimento")
        print("4. Dettaglio completo Case di Comunità (CdC)")
        print("5. Dettaglio completo Ospedali di Comunità (OdC)")
        print("6. Visualizza tutto")
        print("7. Esporta report Excel")
        print("0. Esci")
        print()

        scelta = input("Seleziona un'opzione (0-7): ").strip()

        if scelta == "0":
            print("\n👋 Arrivederci!")
            break
        elif scelta == "1":
            visualizza_riepilogo_generale(df_cdc, df_odc, df_riepilogo)
        elif scelta == "2":
            visualizza_tecnologie_per_categoria(df_cdc, df_odc)
        elif scelta == "3":
            visualizza_top_strutture(df_riepilogo, 10)
        elif scelta == "4":
            visualizza_dettaglio_cdc(df_cdc)
        elif scelta == "5":
            visualizza_dettaglio_odc(df_odc)
        elif scelta == "6":
            visualizza_riepilogo_generale(df_cdc, df_odc, df_riepilogo)
            visualizza_tecnologie_per_categoria(df_cdc, df_odc)
            visualizza_top_strutture(df_riepilogo, 10)
            visualizza_dettaglio_cdc(df_cdc)
            visualizza_dettaglio_odc(df_odc)
        elif scelta == "7":
            esporta_report_excel(df_cdc, df_odc, df_riepilogo)
        else:
            print("❌ Opzione non valida. Riprova.")

        if scelta in ["1", "2", "3", "4", "5", "6", "7"]:
            input("\n[Premi INVIO per continuare]")


def main():
    """Funzione principale"""
    print("🏥 " + "="*98)
    print("   ANALISI TECNOLOGIE SANITARIE PNRR - USL Toscana Nord Ovest".center(100))
    print("="*100)

    # Carica dati
    print("\n📂 Caricamento dati...")
    df_cdc, df_odc, df_riepilogo = carica_dati()
    print("✅ Dati caricati con successo!")

    # Avvia menu interattivo
    menu_interattivo(df_cdc, df_odc, df_riepilogo)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interruzione da tastiera. Arrivederci!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Errore imprevisto: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
