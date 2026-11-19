"""Read-only import of a *joint page + query* Search Console CSV export.

Not an API client. Actual GSC data must be exported with both dimensions.
Never save CSVs, credentials or search-query reports to a public GitHub repository.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from urllib.parse import urlsplit


@dataclass(frozen=True)
class GscRow:
    page: str
    query: str
    clicks: int
    impressions: int
    position: float
    country: str | None = None


def number(value: str) -> float:
    raw = str(value).strip().replace("\u00a0", "").replace(" ", "").replace("%", "")
    if not raw:
        raise ValueError("Empty Search Console metric")
    if "," in raw and "." in raw:
        raw = raw.replace(".", "").replace(",", ".") if raw.rfind(",") > raw.rfind(".") else raw.replace(",", "")
    elif "," in raw:
        raw = raw.replace(",", ".")
    return float(raw)


def column_name(key: str) -> str:
    key = (key or "").lstrip("\ufeff").strip().casefold()
    return {
        "pages": "page", "page": "page", "top pages": "page", "página": "page", "páginas": "page",
        "query": "query", "queries": "query", "top queries": "query", "consulta": "query",
        "consultas": "query", "pesquisa": "query",
        "clicks": "clicks", "cliques": "clicks",
        "impressions": "impressions", "impressões": "impressions",
        "position": "position", "posição": "position",
        "country": "country", "país": "country",
    }.get(key, key)


def load_csv(path: Path, hostname: str, country_filter: str | None = None) -> tuple[list[GscRow], dict]:
    """Return validated rows and import diagnostics; never claim complete GSC coverage."""
    data = path.read_text(encoding="utf-8-sig")
    if not data.strip():
        raise ValueError("Search Console CSV is empty")
    try:
        dialect = csv.Sniffer().sniff(data[:2048], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(StringIO(data), dialect=dialect)
    header = [column_name(col) for col in (reader.fieldnames or [])]
    required = {"page", "query", "clicks", "impressions", "position"}
    missing = required.difference(header)
    if missing:
        raise ValueError("Joint page+query CSV required; missing: " + ", ".join(sorted(missing)))
    result: list[GscRow] = []
    dropped = 0
    for raw in reader:
        fields = {column_name(k): (v or "").strip() for k, v in raw.items() if k is not None}
        try:
            page = fields["page"].strip()
            p = urlsplit(page)
            if p.scheme != "https" or (p.hostname or "").casefold() != hostname.casefold():
                dropped += 1
                continue
            if p.username or p.password or p.port not in (None, 443):
                dropped += 1
                continue
            query = fields["query"].strip()
            if not query:
                dropped += 1
                continue
            country = fields.get("country") or None
            if country_filter and country and country.casefold() not in {country_filter.casefold(), "portugal", "prt", "pt"}:
                dropped += 1
                continue
            clicks_f, impressions_f = number(fields["clicks"]), number(fields["impressions"])
            position = number(fields["position"])
            clicks, impressions = int(clicks_f), int(impressions_f)
            if (clicks_f != clicks or impressions_f != impressions or
                    impressions <= 0 or clicks < 0 or clicks > impressions or not 1 <= position <= 1000):
                dropped += 1
                continue
            clean_page = "https://" + p.netloc.lower() + (p.path or "/")
            result.append(GscRow(clean_page, query[:180], clicks, impressions, position, country))
        except (ValueError, KeyError, TypeError):
            dropped += 1
    return result, {
        "source": "user-supplied Search Console joint page+query CSV",
        "rows_accepted": len(result), "rows_rejected": dropped,
        "warning": "Export may omit low-volume/anonymized queries and does not establish full index coverage.",
    }


def page_opportunities(rows: list[GscRow], sample_pages: set[str], limit: int = 5) -> list[dict]:
    """Pick pages with observed search demand and opportunities for measured improvement.

    Group by page; aggregating by unique query+page is safe only if export uses one
    row per pair (GSC exports with additional dimensions can represent subsets).
    We therefore use the maximum observed impressions for a page as a conservative
    opportunity signal and never claim a site's total clicks or impressions.
    """
    suggestions = []
    by_page: dict[str, list[GscRow]] = {}
    for row in rows:
        if row.page in sample_pages:
            by_page.setdefault(row.page, []).append(row)
    for page, items in by_page.items():
        candidates = sorted(items, key=lambda x: (-x.impressions, x.query))
        for item in candidates[:2]:
            if item.impressions < 20 or not 2.0 <= item.position <= 35.0:
                continue
            ctr = item.clicks / item.impressions
            if ctr >= 0.03:
                continue
            suggestions.append({
                "page": page, "query": item.query, "impressions": item.impressions,
                "clicks": item.clicks, "position": round(item.position, 1),
                "ctr": round(ctr, 4),
                "reason": "Pesquisa observada com impressões e CTR baixo; avaliar intenção, título e conteúdo da página",
                "evidence": "observed GSC export row; not a measured ranking uplift",
            })
    return sorted(suggestions, key=lambda x: (-x["impressions"], x["page"]))[:limit]
