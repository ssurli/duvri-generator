"""
Configurazione soglie per calcolo scenario normativo
ASL Toscana Nord Ovest - Sistema DUVRI

Ultimo aggiornamento: 10 novembre 2025
Modificabile dal responsabile del progetto
"""


class ConfigScenarioNormativo:
    """
    Configurazione soglie per determinare lo scenario normativo
    degli extra-costi di sicurezza da interferenze
    
    Logica applicata (OR):
    - COMPENSAZIONE se: extra-costo < soglia_euro OR extra-costo < soglia_%
    - ATTO AGGIUNTIVO se: extra-costo >= soglia_euro AND extra-costo >= soglia_%
    """
    
    # =========================================
    # SOGLIA ASSOLUTA (in Euro)
    # =========================================
    # Se extra-costo < questa cifra → può essere COMPENSAZIONE (con OR)
    SOGLIA_COMPENSAZIONE_EURO = 1000.00
    
    # =========================================
    # SOGLIA PERCENTUALE (sul contratto)
    # =========================================
    # Se extra-costo < questa % del contratto → può essere COMPENSAZIONE (con OR)
    SOGLIA_COMPENSAZIONE_PERCENTUALE = 3.0  # 3% (ridotto da 5%)
    
    # =========================================
    # LIMITE ART. 120 D.LGS. 36/2023
    # =========================================
    # Limite massimo per atto aggiuntivo senza nuova gara
    LIMITE_MASSIMO_PERCENTUALE = 50.0  # 50%
    
    @classmethod
    def get_descrizione_soglie(cls):
        """Restituisce descrizione testuale delle soglie configurate"""
        return {
            'soglia_euro': f"€{cls.SOGLIA_COMPENSAZIONE_EURO:,.2f}",
            'soglia_percentuale': f"{cls.SOGLIA_COMPENSAZIONE_PERCENTUALE}%",
            'limite_massimo': f"{cls.LIMITE_MASSIMO_PERCENTUALE}%",
            'logica': "OR (compensazione se sotto ALMENO UNA soglia)"
        }
    
    @classmethod
    def verifica_scenario(cls, extra_costo, importo_contratto):
        """
        Verifica quale scenario si applicherebbe con i valori forniti
        
        Args:
            extra_costo (float): Importo extra-costo in euro
            importo_contratto (float): Valore contratto in euro
            
        Returns:
            dict: Dizionario con scenario e dettagli
        """
        perc_su_contratto = (extra_costo / importo_contratto * 100) if importo_contratto > 0 else 0
        
        sotto_soglia_euro = extra_costo < cls.SOGLIA_COMPENSAZIONE_EURO
        sotto_soglia_perc = perc_su_contratto < cls.SOGLIA_COMPENSAZIONE_PERCENTUALE
        
        # Operatore OR
        is_compensazione = sotto_soglia_euro or sotto_soglia_perc
        
        supera_50 = perc_su_contratto > cls.LIMITE_MASSIMO_PERCENTUALE
        
        return {
            'extra_costo': extra_costo,
            'importo_contratto': importo_contratto,
            'percentuale': round(perc_su_contratto, 2),
            'sotto_soglia_euro': sotto_soglia_euro,
            'sotto_soglia_percentuale': sotto_soglia_perc,
            'scenario': 'COMPENSAZIONE' if is_compensazione else 'ATTO_AGGIUNTIVO_ART120',
            'supera_limite_50': supera_50,
            'motivazione': cls._get_motivazione(sotto_soglia_euro, sotto_soglia_perc, is_compensazione, supera_50)
        }
    
    @classmethod
    def _get_motivazione(cls, sotto_euro, sotto_perc, is_compensazione, supera_50):
        """Genera motivazione testuale dello scenario"""
        if is_compensazione:
            if sotto_euro and sotto_perc:
                return f"Sotto entrambe le soglie (€{int(cls.SOGLIA_COMPENSAZIONE_EURO)} e {cls.SOGLIA_COMPENSAZIONE_PERCENTUALE}%)"
            elif sotto_euro:
                return f"Sotto soglia assoluta (€{int(cls.SOGLIA_COMPENSAZIONE_EURO)})"
            else:
                return f"Sotto soglia percentuale ({cls.SOGLIA_COMPENSAZIONE_PERCENTUALE}%)"
        else:
            msg = f"Sopra entrambe le soglie (€{int(cls.SOGLIA_COMPENSAZIONE_EURO)} e {cls.SOGLIA_COMPENSAZIONE_PERCENTUALE}%)"
            if supera_50:
                msg += f" - ⚠️ ATTENZIONE: Supera limite {cls.LIMITE_MASSIMO_PERCENTUALE}%!"
            return msg
    
    @classmethod
    def modifica_soglia_euro(cls, nuovo_valore):
        """
        Modifica la soglia in euro
        
        Esempio:
            ConfigScenarioNormativo.modifica_soglia_euro(1500)
        """
        if nuovo_valore <= 0:
            raise ValueError("La soglia deve essere maggiore di 0")
        
        vecchio_valore = cls.SOGLIA_COMPENSAZIONE_EURO
        cls.SOGLIA_COMPENSAZIONE_EURO = float(nuovo_valore)
        print(f"✅ Soglia Euro aggiornata:")
        print(f"   Da: €{vecchio_valore:,.2f}")
        print(f"   A:  €{cls.SOGLIA_COMPENSAZIONE_EURO:,.2f}")
    
    @classmethod
    def modifica_soglia_percentuale(cls, nuovo_valore):
        """
        Modifica la soglia percentuale
        
        Esempio:
            ConfigScenarioNormativo.modifica_soglia_percentuale(2.5)
        """
        if nuovo_valore <= 0 or nuovo_valore > 100:
            raise ValueError("La soglia deve essere tra 0 e 100")
        
        vecchio_valore = cls.SOGLIA_COMPENSAZIONE_PERCENTUALE
        cls.SOGLIA_COMPENSAZIONE_PERCENTUALE = float(nuovo_valore)
        print(f"✅ Soglia % aggiornata:")
        print(f"   Da: {vecchio_valore}%")
        print(f"   A:  {cls.SOGLIA_COMPENSAZIONE_PERCENTUALE}%")
    
    @classmethod
    def stampa_configurazione(cls):
        """Stampa configurazione corrente in modo leggibile"""
        print("=" * 60)
        print("CONFIGURAZIONE SOGLIE SCENARIO NORMATIVO")
        print("=" * 60)
        config = cls.get_descrizione_soglie()
        print(f"💰 Soglia assoluta:      {config['soglia_euro']}")
        print(f"📊 Soglia percentuale:   {config['soglia_percentuale']}")
        print(f"⚠️  Limite massimo:       {config['limite_massimo']}")
        print(f"🔧 Logica:               {config['logica']}")
        print("=" * 60)


# =========================================
# ESEMPI DI USO
# =========================================

def test_esempi_scenari():
    """Testa vari scenari con le soglie configurate"""
    
    print("\n" + "=" * 70)
    print("TEST SCENARI CON SOGLIE CONFIGURATE")
    print("=" * 70)
    
    ConfigScenarioNormativo.stampa_configurazione()
    
    # Esempi di test
    test_cases = [
        (800, 50000, "Sotto entrambe le soglie"),
        (1200, 50000, "Sopra €1000 ma sotto 3%"),
        (900, 20000, "Sotto €1000 ma sopra 3%"),
        (1500, 40000, "Sopra entrambe le soglie"),
        (500, 10000, "Caso limite basso"),
        (25000, 50000, "Supera limite 50%")
    ]
    
    print("\n📋 RISULTATI TEST:\n")
    
    for extra, contratto, descrizione in test_cases:
        risultato = ConfigScenarioNormativo.verifica_scenario(extra, contratto)
        
        icona = "🟢" if risultato['scenario'] == 'COMPENSAZIONE' else "🔴"
        warning = " ⚠️" if risultato['supera_limite_50'] else ""
        
        print(f"{icona} {descrizione}")
        print(f"   Extra-costo: €{risultato['extra_costo']:,.2f} | Contratto: €{risultato['importo_contratto']:,.2f}")
        print(f"   Percentuale: {risultato['percentuale']}%")
        print(f"   Scenario: {risultato['scenario']}{warning}")
        print(f"   Motivazione: {risultato['motivazione']}")
        print()


if __name__ == '__main__':
    # Se esegui questo file direttamente, mostra test
    test_esempi_scenari()
    
    print("\n💡 SUGGERIMENTI:")
    print("   - Per modificare soglia €: ConfigScenarioNormativo.modifica_soglia_euro(1500)")
    print("   - Per modificare soglia %: ConfigScenarioNormativo.modifica_soglia_percentuale(2.5)")
    print("   - Per verificare scenario: ConfigScenarioNormativo.verifica_scenario(1200, 50000)")
