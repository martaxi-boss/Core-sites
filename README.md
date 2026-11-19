# Core-sites — núcleo independente de crescimento SEO

Core reutilizável para acompanhar e melhorar os sites de afiliação, sem processos residentes e sem dependências na VPS.

## Estado e objetivos

**v2 (em validação):** motor de auditoria técnica e de oportunidades comerciais com prioridades P0/P1/P2, até dois briefings editoriais por site, análise de links internos e entrada opcional de dados reais do Search Console (CSV privado). Execução via GitHub Actions; apenas relatórios e propostas, sem alterar sites ou gerar visitas artificiais.

**Piloto ativo: apenas Low Cost Europa** (`https://www.lowcost-europa.eu/`).

O Sevelora está **em espera** e não faz parte da configuração `sites.json` durante o piloto. Só volta a entrar após avaliação explícita dos resultados. O motor continua preparado para vários sites.

O catálogo do Low Cost e os seus links manuais não são modificados.

O catálogo do Sevelora, os links manuais do Low Cost, credenciais privadas, backups, GitHub de cada aplicação e a respetiva VPS permanecem intactos.

## O que faz

1. Descobre páginas através do sitemap XML público, sempre no domínio canónico.
2. Respeita robots.txt e impõe limites rígidos de páginas, respostas e tempo.
3. Deteta problemas em títulos, canonicals, meta descriptions, headings, noindex, alt e ligações internas.
4. Prioriza oportunidades de conteúdo original orientado para compradores, sem inventar dados de pesquisa.
5. Publica relatórios JSON e Markdown como artefactos do GitHub Actions e mantém **uma issue de backlog por site**, sem duplicados.

## Ficheiros

- `seo_growth_core.py`: motor somente leitura em Python, sem bibliotecas externas.
- `growth_engine/`: importação opcional de CSV Search Console, prioridades por evidência e briefings comerciais.
- `sites.json`: registo dos sites e respetivas configurações públicas.
- `tests/`: testes offline do rastreio, oportunidades e segurança dos dados.
- `.github/workflows/seo-growth-core.yml`: testes, execução diária e relatórios.
- `docs/ROADMAP.md`: próximos passos para passar de auditoria a crescimento mensurável.
- `docs/OPEN_SOURCE_INTEGRATION.md`: funcionalidades aproveitadas como ideias, licenças e limites.
- `.github/workflows/seo-performance-sample.yml`: auditoria Lighthouse mobile manual e limitada.

## Executar

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 seo_growth_core.py --config sites.json --out reports --max-pages 20
python3 -m growth_engine.cli --config sites.json --audit-dir reports --out reports
```

O workflow automático do GitHub Actions para este piloto analisa só o Low Cost Europa e não instala nada na VPS e usa o runner temporário do próprio GitHub.
A cadência inicial é diária, 07:21 UTC. É possível iniciar uma auditoria manual em **Actions → SEO Growth Core → Run workflow**.

## Limitações relevantes

- Não gera visitas, simulações humanas, proxies ou CTR artificial.
- Não consulta posições Google nem mede conversões sem dados de origem autorizados.
- Não regista visitas sintéticas nas métricas de negócio.
- Não faz publicação massiva, spam, alteração de afiliação ou reenvio repetitivo de URLs.
- O Google decide indexação e posicionamento; nenhuma ferramenta garante ranking.

Para crescimento de verdade, a fase seguinte liga dados oficiais da Search Console de forma autorizada, prepara melhorias específicas por PR nos sites e mede cliques reais para o afiliado. **Nenhum código de projetos externos foi copiado; foram estudadas as ideias e reimplementadas funcionalidades limitadas e próprias.**
