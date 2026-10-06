from datetime import date
from pathlib import Path
import yaml
import logging

logger = logging.getLogger(__name__)

class PricingEngine:
    """
    Motore di calcolo Fase 2: Spesa Annua Stimata (SAS) e Ranking.
    Implementa le logiche dei documenti ARERA/Acquirente Unico isolando 
    le regole regolatorie dalle logiche di piattaforma.
    """
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._load_config()
        
    def _load_config(self):
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.rules = yaml.safe_load(f)
            
    def _get_active_params(self, target_date: date) -> dict:
        """Estrae i parametri corretti in base al periodo di validità (es. switch 01/04/2026)."""
        for periodo in self.rules.get('periodi', []):
            start = date.fromisoformat(periodo['valid_from'])
            end = date.fromisoformat(periodo['valid_to'])
            if start <= target_date <= end:
                return periodo
        raise ValueError(f"Nessun parametro regolato trovato per la data {target_date}")

    def calcola_sas(self, offerta: dict, data_rif: date, profilo_consumo: dict) -> dict:
        """
        Calcola la SAS e gli Indicatori (ICF, IC, IP) a partire dal modello dati estratto.
        
        Args:
            offerta: Record denormalizzato con le componenti di prezzo.
            data_rif: Data per selezionare il set regolatorio corretto.
            profilo_consumo: Es. {"consumo_annuo": 2700, "potenza": 3.0, "tipo_cliente": "domestico"}
            
        Returns:
            dict con {'SAS': valore, 'ICF': valore, ...} o marcatore non calcolabile.
        """
        parametri = self._get_active_params(data_rif)
        
        # TODO: Implementare l'albero di calcolo in base a "Regole SAS v4.0"
        # ATTENZIONE: Mancando i PDF, si attende il loro inserimento qui.
        
        is_tutele_graduali = parametri.get('parametri_elettrici', {}).get('dispacciamento_tutele_graduali', False)
        
        # Placeholder
        risultato = {
            "is_calcolabile": True,
            "motivo_esclusione": None,
            "spesa_annua_stimata": 0.0,
            "indicatori": {"ICF": 0.0, "IC": 0.0, "IP": 0.0}
        }
        
        return risultato
        
    def simula_ranking(self, mia_offerta_params: dict, data_rif: date, profilo_consumo: dict, df_competitors) -> int:
        """Calcola la SAS della nostra offerta simulata e la ordina contro il database storico."""
        mia_sas = self.calcola_sas(mia_offerta_params, data_rif, profilo_consumo)
        # TODO: Logica di sorting in Polars
        return 1
