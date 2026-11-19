# Auditoria Ferrari do piloto Low Cost Europa - 19/11/2026

## Escopo e fontes

- Repositório de auditoria: `martaxi-boss/Core-sites`; execução isolada pelo GitHub Actions
- Site observado: `https://www.lowcost-europa.eu`; repositório da aplicação separado (`martaxi-boss/lowcost-europa`)
- Sevelora fora de `sites.json`; o piloto não modifica conteúdos, links de afiliação ou serviços da VPS
- Fonte das métricas: relatórios de rastreio públicos, **não** Search Console nem encomendas

## Evidência de execução existente

[Core-sites - run #44580786718](https://github.com/martaxi-boss/Core-sites/actions/runs/44580786718) passou com as 23 URLs do sitemap e 0 problemas detetados **nos critérios limitados daquele auditor**. GSC `not_connected`: nenhum dado de cliques, país, impressões, posições ou indexação real. Houve 2 briefings editoriais que eram heurísticos, não fundamentados em pesquisas.

O artefacto desse run mostrou que as 15 versões das páginas de categorias `/products/`, `/pt/products/` e `/es/products/` têm aproximadamente **734 a 1830 palavras visíveis**, dados estruturados e 5–7 links de entrada a partir de páginas lidas. Isto não prova qualidade editorial, mas torna inadequada a sugestão automática genérica de "acrescentar mais um guia" sem evidência de lacuna.

## Ferrari realmente executado pela ponte original

1. [Início de equipa Ruflo](https://github.com/martaxi-boss/VPS/actions/runs/44581711043): sessão temporária com auditor e revisor, sem LLM residente
2. [Ferramenta privada real](https://github.com/martaxi-boss/VPS/actions/runs/44581937744): `jq-format-json` validou e formatou o `sites.json` público (256 B), gerando artefacto com SHA-256 `a505c8433b64470a1c2b7adc4b7e1561f4ae1359d67f8c161fead1bf388ead75`
3. [Revisão distinta](https://github.com/martaxi-boss/VPS/actions/runs/44582261230): o revisor aprovou o hash e o conteúdo (exclusivamente `lowcost-europa`, HTTPS www e sitemap certo)
4. [Fecho](https://github.com/martaxi-boss/VPS/actions/runs/44582867554): `ruflo-team` `completed`, uma ferramenta verificada e uma revisão aprovada

**Distinção obrigatória:** esta execução Ferrari comprova a integridade da **configuração pública**, não uma auditoria independente do ranking/Google, uma instalação nova ou uma certificação universal das ferramentas Ferrari. `quality_gate=not_certified` porque não foi solicitado gate externo de aceitação semântica.

[Inventário REA via Ferrari](https://github.com/martaxi-boss/VPS/actions/runs/44582957991) confirmou capacidade de listar ferramentas, mas `inspect_web_page` requer uma sessão CDP ativa e não substitui um teste do website sem preparação explícita dessa sessão. Não alegar que o REA inspecionou a página.

## Lacunas identificadas no código antes desta PR

1. **Privacidade grave:** com uma importação privada de Search Console, o JSON `*.growth.json` podia incluir termos de pesquisa e métricas por linha, apesar de o Markdown público ocultar parte dos detalhes.
2. **Propostas editoriais falsas:** toda categoria listada em `focus_path_contains` gerava oportunidade mesmo com 700+ palavras e várias ligações internas, sem GSC. O core recomendava "trabalhar" onde não havia lacuna demonstrada.
3. **Indexabilidade incompleta:** auditor original só procurava `<meta name="robots">`, ignorando `X-Robots-Tag` HTTP e diretivas `robots.txt` específicas para Googlebot.
4. **Falsa cobertura completa:** páginas excluídas por robots podiam produzir `partial_scan=false`; sitemaps mais extensos que o limite de oito ficheiros podiam ficar truncados silenciosamente.
5. **País GSC não garantido:** um CSV sem dimensão País ou linhas com país em branco ainda podia ser aceite com filtro português.

## Correções propostas e testáveis

- Relatórios JSON públicos sempre sanitizados antes de serializar qualquer pesquisa privada
- Importações GSC com filtro PT só aceites quando a coluna País está presente e preenchida
- O core deixa de forçar briefings: sem lacuna visível ou procura Google observada, devolve zero propostas, declarando a limitação
- Procura real (quando fornecida legalmente) pode revelar oportunidade numa página já extensa, mas só produz briefing sujeito a aprovação
- Auditor verifica robots Googlebot e X-Robots-Tag; assinala rastreio parcial e recusa cobertura silenciosamente truncada
- Novos testes de regressão para cada correção; sem alterações a nenhum domínio de produção

## O que permanece por resolver

- **Medição real:** integrar GSC de forma autorizada e sem Windsor/serviço pago; atualmente não há credenciais nem dados GSC ligados ao `Core-sites`
- **Impacto comercial:** medir cliques orgânicos, cliques reais para AliExpress e conversões em fontes permitidas; não usar contadores de requests/proxies como prova de clientes
- **SEO avançado:** validar hreflang, experiência mobile de campo, links externos de qualidade e valor original por categoria com amostra editorial, não apenas contagens de texto
- **Evitar duplicados:** Low Cost já tem auditoria Lighthouse mobile **semanal** na sua própria CI; o workflow manual do Core-sites não deve ser agendado nem alegado como um teste independente já executado
- **Correções nos sites:** nenhuma. Para aplicar conteúdo ou mudanças de código, preparar uma PR específica no repositório Low Cost após evidência real e revisão humana

O objetivo do Core-sites é crescimento **comprovável**, não crescimento fictício. `PASS` de testes significa somente que a funcionalidade verificada nesse teste cumpriu o respetivo contrato.
