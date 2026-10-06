import polars as pl

DIM_OFFERTA_SCHEMA = {
    "offerta_id": pl.Utf8,
    "sk_offerta_versione": pl.Utf8,
    "valid_from": pl.Date,
    "valid_to": pl.Date,
    "is_current": pl.Boolean,
    "content_hash": pl.Utf8,
    "n_giorni_pubblicazione": pl.Int32,
    "commodity": pl.Utf8,
    "codice_offerta": pl.Utf8,
    "piva_venditore": pl.Utf8,
    "nome_offerta": pl.Utf8,
    "tipo_mercato": pl.Utf8,
    "tipo_offerta": pl.Utf8,
    "url_offerta": pl.Utf8,
    "consumo_min": pl.Float64,
    "consumo_max": pl.Float64,
    "tipologia_fasce": pl.Utf8,
    "commercializzazione_data_inizio": pl.Utf8,
    "commercializzazione_data_fine": pl.Utf8,
    "prezzo_monorario": pl.Float64,
    "prezzo_f1": pl.Float64,
    "prezzo_f2": pl.Float64,
    "prezzo_f3": pl.Float64,
    "quota_fissa_annua": pl.Float64,
    "spread": pl.Float64,
    "sconto_nome": pl.Utf8,
    "sconto_valore": pl.Float64,
    "flag_sconti_multipli": pl.Boolean
}

OPEN_END_DATE = "2099-12-31"
