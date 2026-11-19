"""Public-safe projection of proposed SEO work.

Private Search Console query/page pairs are NEVER written to GitHub Actions
artifacts or public issues. Raw metrics remain in memory, not in JSON outputs.
"""
from __future__ import annotations

from copy import deepcopy


def redact_report(report: dict) -> dict:
    clean = deepcopy(report)
    for brief in clean.get("briefs", []):
        if brief.get("gsc_query") is not None:
            brief["gsc_query"] = None
            brief["why"] = (
                "Pesquisa observada em dados Search Console privados; "
                "consulta e metricas omitidas deste relatorio publico."
            )
    gsc = clean.get("gsc") or {}
    diagnostics = gsc.get("diagnostics")
    if isinstance(diagnostics, dict):
        gsc["diagnostics"] = {
            "rows_accepted": diagnostics.get("rows_accepted"),
            "rows_rejected": diagnostics.get("rows_rejected"),
            "warning": "Exportacoes da Search Console podem omitir pesquisas anonimizadas."
        }
    gsc["privacy"] = "Redacted: never disclose search terms or per-row metrics in public outputs."
    return clean
