# Core-sites — núcleo independente de crescimento SEO

Core reutilizável para acompanhar e melhorar os sites de afiliação, sem processos residentes e sem dependências na VPS.

## Estado e objetivos

**v1:** motor de auditoria técnica e de oportunidades comerciais, somente leitura; execução automática no GitHub Actions e relatórios por site. Não cria cliques fictícios, não altera os sites automaticamente e não promete posições no Google.

Sites iniciais:
- [Low Cost Europa](https://www.lowcost-europa.eu/) (Django; links de catálogo exclusivamente manuais).
- [Sevelora](https://sevelora.eu/) (Next.js; feed Awin/Diversual independente).

O catálogo do Sevelora, os links manuais do Low Cost, credenciais privadas, backups, GitHub de cada aplicação e a respetiva VPS permanecem intactos.

## O que faz

1. Descobre páginas através do sitemap XML público, sempre no domínio canónico.
2. Respeita robots.txt e impõe limites rígidos de páginas, respostas e tempo.
3. Deteta problemas em títulos, canonicals, meta descriptions, headings, noindex, alt e ligações internas.
4. Prioriza oportunidades de conteúdo original orientado para compradores, sem inventar dados de pesquisa.
5. Publica relatórios JSON e Markdown como artefactos do GitHub Actions e mantém **uma issue de backlog por site**, sem duplicados.

## Ficheiros

- `seo_growth_core.py`: motor somente leitura em Python, sem bibliotecas externas.
- `sites.json`: registo dos sites e respetivas configurações públicas.
- `tests/test_seo_growth_core.py`: testes offline.
- `.github/workflows/seo-growth-core.yml`: testes, execução diária e relatórios.
- `docs/ROADMAP.md`: próximos passos para passar de auditoria a crescimento mensurável.

## Executar

```bash
python3 -m unittest discover -s tests -p 'test_seo_growth_core.py' -v
python3 seo_growth_core.py --config sites.json --out reports --max-pages 20
```

O workflow automático do GitHub Actions não instala nada na VPS e usa o runner temporário do próprio GitHub.
A cadência inicial é diária, 07:21 UTC. É possível iniciar uma auditoria manual em **Actions → SEO Growth Core → Run workflow**.

## Limitações relevantes

- Não gera visitas, simulações humanas, proxies ou CTR artificial.
- Não consulta posições Google nem mede conversões sem dados de origem autorizados.
- Não regista visitas sintéticas nas métricas de negócio.
- Não faz publicação massiva, spam, alteração de afiliação ou reenvio repetitivo de URLs.
- O Google decide indexação e posicionamento; nenhuma ferramenta garante ranking.

Para crescimento de verdade, a fase seguinte cruza dados oficiais de desempenho com propostas de melhorias, mudanças revistas por PR e medição de cliques para o afiliado.
