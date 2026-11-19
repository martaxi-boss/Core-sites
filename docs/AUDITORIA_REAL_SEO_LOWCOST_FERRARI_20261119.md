# TESTE REAL SEO — LOW COST EUROPA — 19/11/2026

## Conclusão e âmbito

**Resultado público técnico: PASS** nos testes executados. **Google Search Console indexação total: NÃO CERTIFICADA** nesta ronda por ausência de sessão/credencial autenticada. O código não foi alterado na aplicação Django nem nos links manuais.

- Site: `https://www.lowcost-europa.eu/`
- Repositório de teste: `martaxi-boss/Core-sites` (somente `lowcost-europa` em `sites.json`)
- CI de rede real: [Core-sites Actions #44593001731](https://github.com/martaxi-boss/Core-sites/actions/runs/44593001731)
- Alteração do auditor, não do site: [Core-sites PR #8](https://github.com/martaxi-boss/Core-sites/pull/8), integrada no main
- Ferrari navegador real: [Home PT #44592716735](https://github.com/martaxi-boss/VPS/actions/runs/44592716735) e [HIFU PT+ES mobile #44593191486](https://github.com/martaxi-boss/VPS/actions/runs/44593191486).
- A verificação é datada. Não representa 100% de todas as URLs históricas ou da situação futura.

## Resultados medidos

| Sinal | Resultado |
| --- | --- |
| Testes automáticos do Core-sites | 48/48 PASS |
| Páginas do sitemap público lidas | 23/23 |
| XML x TXT | 23 URLs idênticas, HTTP 200 |
| robots.txt | HTTP 200; anuncia XML e TXT |
| HTML público / canonical / hreflang / viewport / noindex / JSON-LD sintático | 0 erros nas 23 páginas testadas |
| Amostras por HTTP User-Agent `Googlebot` | `/pt/`, `/pt/products/hifu/` e `/es/products/hifu/`: 3/3 HTTP 200 e 0 erros de metadata |
| Prefixos privados declarados em robots.txt | 9/9 bloqueios verificados por regra mais específica, sem ir buscar as páginas privadas |
| Avisos não bloqueantes | 16: 11 páginas sem prefixo servidas em inglês ao runner estrangeiro; 5 páginas institucionais sem JSON-LD, que não é obrigatório |
| Search Console autenticada | Não consultada nesta execução |

**IMPORTANTE:** a biblioteca Python `urllib.robotparser` interpreta o primeiro match em vez de usar sempre a regra mais específica, podendo tratar `Allow: /` como permissão global mesmo com `Disallow: /go/`. O novo teste próprio usa **precedência por comprimento da regra**, com desempate a favor de Allow para as regras simples efetivamente presentes no nosso site. Não é uma descoberta de erro do ficheiro robots do site. Ver [documentação oficial Google](https://developers.google.com/crawling/docs/robots-txt/robots-txt-spec).

## Comportamento por idioma e relevância portuguesa

Nas 23 páginas públicas servidas ao runner de testes:

- 6 URLs `/pt/`: `<html lang="pt-pt">`, canonicals próprios, hreflang PT/ES/x-default;
- 6 URLs `/es/`: `<html lang="es">`, canonicals próprios, hreflang PT/ES/x-default;
- 11 URLs sem prefixo: `<html lang="en">` do ponto de vista deste runner fora de Portugal.

Isto é **compatível com** o middleware de geolocalização configurado em `apps/storefront/geo_locale.py`, que escolhe por IP e usa inglês para país não reconhecido. Não é prova de que o Google não indexe o PT; as versões fixas `/pt/` permanecem as URLs estáveis recomendadas para Portugal. É um sinal SEO que justifica acompanhar qual o URL que a Google realmente apresenta para pesquisas em PT; não fazer cloaking nem alterar geolocalização cegamente.

## Ferrari com navegador verdadeiro — prova independente do código

`kind=rea-mcp`, ferramenta `capture_browser_scenario` de `rea-agents` privado Ferrari, acionada via ponte GitHub Actions→VPS original. Executou **Chromium 156.0.8078.4** da pasta privada do Ferrari com perfis temporários (limpeza pelo próprio provider). Abriu:

1. `https://www.lowcost-europa.eu/pt/` em desktop: DOM capturado (html pt-pt; title pt-PT; robots index, follow; canonical /pt/; hreflang; JSON-LD).
2. `https://www.lowcost-europa.eu/pt/products/hifu/` em viewport mobile 390×844: DOM capturado, screenshot PNG validado por SHA-256, title HIFU PT, lang pt-pt, robots index, follow, canonical PT.
3. `https://www.lowcost-europa.eu/es/products/hifu/` em viewport mobile 390×844: DOM, screenshot PNG, title espanhol, lang es, robots index, follow, canonical ES.

O resultado REA indica passos de navegação **completed** e capturas reais não vazias. `quality_gate=not_certified` pois não foi configurado um gate automático completo de JS/consola/teclado/rede. O Ferrrari **não** usou login na conta Google nem consultou métricas da Search Console. Nenhuma compra/saída de afiliado foi acionada.

## Google — indexação oficial e alertas

- Evidência histórica verificável [8/11/2026](https://github.com/martaxi-boss/lowcost-europa/blob/main/docs/operations/google-search-console-20261108-1856.json): API oficial `urlInspection.index.inspect` devolveu `PASS / Enviada e indexada` para **6 URLs canónicas**: homepage e cinco categorias **sem prefixo**. Não é cobertura de hoje nem prova de 6 novas indexações.
- E-mail Search Console de 10/11 confirma que a Google começou a registar **impressões desde 8/11**: o site apareceu em resultados de pesquisa.
- E-mails da Search Console recebidos em 19/11 referem exclusões por `robots.txt` para propriedades domínio e WWW; outro de 12/11 refere exclusão por `noindex`. **Não identificam quais as URLs.**
- O código atual bloqueia intencionalmente `/admin/`, `/painel/`, `/ops/`, `/health/`, `/i18n/`, `/go/`, `/contactar/`, `/aliexpress/` e `/pesquisar/`. Logo, os alertas **podem** ser esperados, mas **não é possível prová-lo** sem a lista de URLs do relatório GSC.
- 23 URLs descobertas pelo sitemap não significam 23 URLs indexadas. `site:` nas pesquisas públicas não é um inventário completo e não substitui URL Inspection.

## O que está e não está validado

**Validado:** resposta HTTP dos 23 URLs, metadados canonicals, alternates, indexability declarada, presença de viewport, JSON-LD sem erros sintáticos, robots privado, 3 User-Agent HTTP simulados, 3 páginas reais em Chromium privado Ferrari, integridade e prova de execução.

**Ainda por validar oficialmente:** totais de páginas indexadas em 19/11, lista exata de bloqueios vista pela Search Console, consultas que originaram impressões/cliques em Portugal, CTR, posição média, Core Web Vitals de campo e encomendas atribuídas a URLs manuais. Os últimos testes não incluem compras nem utilizadores reais.

## Próximo passo indispensável (não substituir por novos sitemaps)

Consultar com autorização na **Search Console da propriedade exata** `sc-domain:lowcost-europa.eu` o relatório de páginas excluídas (URLs concretas), fazer a inspeção das 23 URLs do sitemap e extrair `searchAnalytics.query` por país Portugal, página/consulta e datas válidas. Existe fallback oficial gratuito documentado [aqui](https://github.com/martaxi-boss/lowcost-europa/blob/main/docs/operations/official-gsc-free-fallback-20261109.md), que requer OAuth `webmasters.readonly` autorizado pelo titular; não existe autorização reutilizável no Ferrari nem no Core-sites nesta ronda. Não extrair tokens de Windsor nem inventar credenciais.

Se as exclusões corresponderem apenas às rotas privadas, **não corrigir robots.txt**. Se houver páginas `/pt/` públicas bloqueadas/noindex na lista da Search Console, abrir uma alteração pontual no repositório Low Cost, com revisão, testes e deploy via GitHub Actions já existente.

Não publicar conteúdo genérico, não gerar visitas falsas e não alterar links AliExpress manuais em resposta a avisos do Google.
