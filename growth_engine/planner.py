"""Prioritize observed technical issues and propose small editorial briefs.

Inspired by the workflow patterns of SEO Autopilot / SEOnaut / DispatchSEO,
but implemented from scratch; no third-party source code is embedded.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from urllib.parse import urlsplit

from .gsc import GscRow, page_opportunities

LEVELS = {"critical": "P0", "important": "P1", "opportunity": "P2"}
SORT = {"P0": 0, "P1": 1, "P2": 2}


def _safe_title(value: str) -> str:
    return " ".join(str(value).split())[:120]


def _tokenize(title: str) -> set[str]:
    ignored = {"para", "sobre", "como", "a", "o", "de", "da", "do", "em", "com",
               "e", "por", "uma", "um", "site", "lowcost", "europa", "sevelora", "produtos"}
    return {token.casefold().strip(",.;:?!") for token in title.split()
            if len(token) >= 4 and token.casefold().strip(",.;:?!") not in ignored}


def suggest_internal_source(target: dict, pages: list[dict]) -> dict | None:
    """Pick an already-scanned, related page lacking a link to target.

    Only suggestions. We never mutate content or add links automatically.
    """
    target_url = target["url"]
    target_title = _tokenize(target.get("title", ""))
    target_path = urlsplit(target_url).path
    def editorial_path(value: str) -> tuple[str, ...]:
        segments = [x for x in urlsplit(value).path.split("/") if x]
        if segments and segments[0] in ("pt", "es"):
            segments = segments[1:]
        return tuple(segments)
    normalized_target = editorial_path(target_url)
    locale = "/es/" if target_path.startswith("/es/") else "/pt/" if target_path.startswith("/pt/") else None
    possibilities = []
    for p in pages:
        if (p["url"] == target_url or target_url in p.get("outbound_internal", [])
                or (normalized_target and editorial_path(p["url"]) == normalized_target)):
            # Never recommend linking alternate-locale or legacy paths of the same page.
            continue
        source_path = urlsplit(p["url"]).path
        if locale and source_path.startswith(("/pt/", "/es/")) and not source_path.startswith(locale):
            continue
        shared = len(target_title.intersection(_tokenize(p.get("title", ""))))
        if source_path in ("/", "/pt/", "/es/"):
            shared += 1
        if shared >= 1:
            possibilities.append((shared, p["url"], p))
    if not possibilities:
        return None
    _, _, best = max(possibilities, key=lambda x: (x[0], -len(x[1])))
    return {
        "source": best["url"], "source_title": _safe_title(best.get("title", "")),
        "target": target_url,
        "why": "Sugestão contextual baseada nas páginas já lidas; confirmar relevância editorial e intenção de pesquisa.",
    }


def technical_queue(report: dict, limit: int = 8) -> list[dict]:
    """Use severity from observed checks, deduplicate overlapping alerts per URL."""
    findings = report.get("findings", [])
    pages = report.get("page_signals", [])
    urls = {p.get("url"): p for p in pages}
    chosen = []
    per_url = Counter()
    for f in sorted(findings, key=lambda x: (SORT.get(LEVELS.get(x.get("level")), 9), x.get("url", ""))):
        url = f.get("url", "")
        if not url or per_url[url] >= 2:
            continue
        level = LEVELS.get(f.get("level"), "P2")
        evidence = "reproduced on-page audit" if url in urls else "public crawl observation"
        chosen.append({
            "priority": level, "kind": "technical", "url": url,
            "problem": _safe_title(f.get("problem", "")),
            "recommended_action": _safe_title(f.get("recommendation", "")),
            "evidence": evidence,
            "automatic_fix": False,
        })
        per_url[url] += 1
        if len(chosen) >= limit:
            break
    return chosen


def commercial_briefs(report: dict, site: dict, gsc_rows: list[GscRow] | None = None,
                      limit: int = 2) -> list[dict]:
    """Two bounded editorial brief suggestions per site, not invented articles."""
    pages = report.get("page_signals", [])
    by_url = {p["url"]: p for p in pages}
    ideas = list(report.get("growth_opportunities", []))
    gsc = page_opportunities(gsc_rows or [], set(by_url)) if gsc_rows is not None else []
    opportunity_by_page = {}
    for item in gsc:
        opportunity_by_page.setdefault(item["page"], item)
        # Search-demand evidence can reveal an opportunity on an otherwise rich page.
        # Without that data, the scanner must not invent missing buyer guides.
        url = item["page"]
        focus = site.get("focus_path_contains", ["/products/", "/categoria/"])
        if (url in by_url and any(p in urlsplit(url).path for p in focus)
                and not any(old.get("url") == url for old in ideas)):
            ideas.append({"url": url, "title": by_url[url].get("title", ""),
                          "incoming_links": by_url[url].get("incoming_links", 0)})
    def order(item):
        g = opportunity_by_page.get(item["url"])
        path = urlsplit(item["url"]).path
        # Avoid generating thin product text; prefer category pages and PT market.
        category_first = 0 if site.get("id") == "sevelora" and path.startswith("/categoria/") else 1
        locale = 0 if path.startswith("/pt/") else (2 if path.startswith("/es/") else 1)
        return (0 if g else 1, -(g["impressions"] if g else 0),
                category_first, locale, item.get("incoming_links", 0), item["url"])
    chosen = []
    for idea in sorted(ideas, key=order):
        page = by_url.get(idea.get("url"))
        if not page:
            continue
        g = opportunity_by_page.get(page["url"])
        title = _safe_title(page.get("title", "")) or "Página a melhorar"
        link = suggest_internal_source(page, pages)
        target = site.get("id", "")
        if target == "lowcost-europa":
            sections = [
                "Diferenças entre tecnologias e critérios objetivos de seleção",
                "Quem pode beneficiar de cada tipo de equipamento e respetivas limitações",
                "O que confirmar na ficha técnica, garantia e assistência do vendedor",
                "Perguntas frequentes factuais e links internos relevantes",
            ]
        elif target == "sevelora":
            sections = [
                "Critérios de escolha: materiais, dimensões, compatibilidade e manutenção",
                "Privacidade, higiene e cuidados adequados à categoria",
                "Diferenças práticas entre tipos de produtos disponíveis",
                "Perguntas frequentes e ligações para categorias relacionadas",
            ]
        else:
            sections = [
                "Dúvidas reais do comprador sobre esta categoria",
                "Comparação factual das opções e respetivas limitações",
                "Perguntas frequentes e navegação interna relevante",
            ]
        chosen.append({
            "url": page["url"], "working_title": title,
            "intent": "Ajudar um comprador português a escolher, sem repetir informação genérica do fornecedor.",
            "why": (f"Pesquisa observada: {g['impressions']} impressões, "
                    f"{g['clicks']} cliques, posição média {g['position']} (linha GSC)."
                    if g else "Oportunidade editorial heurística observada na página pública; procura ainda não confirmada."),
            "gsc_query": g["query"] if g else None,
            "suggested_sections": sections, "internal_link_suggestion": link,
            "review_checks": [
                "Confirmar fontes, termos e detalhes atuais antes de escrever",
                "Não inventar eficácia, preços, stock, avaliações ou entregas",
                "Distinguir informação original de descrição do fornecedor",
                "Rever manualmente o texto e publicar apenas por PR aprovado",
            ],
            "state": "proposal_only",
        })
        if len(chosen) >= limit:
            break
    return chosen


def plan(report: dict, site: dict, gsc_rows: list[GscRow] | None = None,
         gsc_diagnostics: dict | None = None) -> dict:
    queue = technical_queue(report, limit=8)
    briefs = commercial_briefs(report, site, gsc_rows=gsc_rows, limit=2)
    for item in briefs:
        queue.append({
            "priority": "P2", "kind": "editorial", "url": item["url"],
            "problem": "Oportunidade de reforçar informação útil para quem quer comprar",
            "recommended_action": "Preparar guia original a partir do briefing e validar antes de publicar",
            "evidence": "GSC export row + sampled HTML" if item["gsc_query"] else "sampled HTML only, unverified demand",
            "automatic_fix": False,
        })
    return {
        "version": "0.2.0", "site": site["id"],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_audit": {
            "checked_at_utc": report.get("checked_at_utc"),
            "pages_scanned": report.get("pages_scanned", 0),
            "sitemap_urls": report.get("sitemap_urls", 0),
            "partial_scan": report.get("partial_scan", True),
        },
        "gsc": {
            "status": "provided_export" if gsc_rows is not None else "not_connected",
            "diagnostics": gsc_diagnostics,
            "caution": "No GSC access means no claim of keyword rankings, search clicks or sales."
                       if gsc_rows is None else
                       "CSV rows may be truncated or anonymized; cannot infer total traffic, rank uplift or causality.",
        },
        "priority_queue": queue,
        "briefs": briefs,
        "guardrails": {
            "max_briefs_per_site": 2,
            "change_policy": "manual_review_and_site_specific_pull_request",
            "traffic_policy": "no_synthetic_clicks_or_visitors",
            "privacy": "Search Console queries must not be published into public GitHub issues or artifacts.",
        },
    }


def markdown(result: dict, public: bool = True) -> str:
    """Public mode deliberately hides raw query text and exact GSC metrics."""
    s = result["source_audit"]
    lines = [
        f"# Plano de crescimento - {result['site']}",
        "", f"Data UTC: {result['generated_at_utc']}",
        f"Auditoria: {s['pages_scanned']} páginas analisadas de {s['sitemap_urls']} no sitemap.",
        f"Search Console: {'dados de exportação fornecidos (privados)' if result['gsc']['status'] == 'provided_export' else 'não ligado neste job'}.",
        "", "## Prioridades propostas (não publicadas)", "",
    ]
    for task in result["priority_queue"][:10]:
        lines.append(
            f"- **{task['priority']} / {task['kind']}** [{task['url']}]({task['url']}): "
            f"{task['problem']}. Próxima ação: {task['recommended_action']}."
        )
    if not result["priority_queue"]:
        lines.append("Sem ações propostas nesta amostra.")
    lines.extend(["", "## Briefings editoriais - máximo 2 por site", ""])
    for b in result["briefs"]:
        lines.extend([f"### [{b['working_title']}]({b['url']})",
            "",
            ("Motivo: observações de Search Console (detalhes confidenciais)." if public and b["gsc_query"]
             else f"Motivo: {b['why']}"),
            "", f"Objetivo: {b['intent']}", "", "Estrutura a estudar:"])
        for section in b["suggested_sections"]:
            lines.append(f"- {section}")
        if b["internal_link_suggestion"]:
            l = b["internal_link_suggestion"]
            lines.append(f"- Ligação contextual possível: [{l['source']}]({l['source']}) → [{l['target']}]({l['target']}); confirmar pertinência")
        lines.extend(["", "Verificações antes da aprovação:"])
        for check in b["review_checks"]:
            lines.append(f"- {check}")
        if not public and b["gsc_query"]:
            lines.append(f"- Consulta de pesquisa (uso privado): {b['gsc_query']}")
        lines.append("")
    if not result["briefs"]:
        lines.append("Sem briefings elegíveis nesta amostra; não inventar oportunidades.")
    lines.extend(["", "**Limites:** Não mede vendas nem indexação; não gera visitas fictícias e não altera sites em produção.",
                  "Prioridades heurísticas precisam de revisão humana; não são um score oficial do Google.", ""])
    return "\n".join(lines)
