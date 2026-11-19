# Auditoria Low Cost Europa — Ferrari + Core-sites
**Data:** 19/11/2026, verificações públicas até 18:27 UTC  
**Escopo:** apenas `https://www.lowcost-europa.eu/`. Não abrange Sevelora e não altera a montra, os links manuais, a VPS, DNS ou as contas Search Console.

## Resultado executivo

- **PASS — site público:** o monitor VPS de 19/11 13:42 confirmou HTTP 200 em `/`, `/pt/`, `/es/`, duas categorias PT, `/robots.txt`, `/sitemap.xml`, `/sitemap.txt`, `/favicon.ico`; Nginx e serviço da aplicação ativos no início e fim do job. [Prova](https://github.com/martaxi-boss/VPS/actions/runs/44535984357).
- **PASS — sitemap e Googlebot:** a auditoria oficial [Core-sites #44587714395](https://github.com/martaxi-boss/Core-sites/actions/runs/44587714395) verificou às 18:27:04 que XML e TXT respondem HTTP 200, contêm 23 URLs exatamente iguais, sem duplicados, robots anuncia ambos e não bloqueia Googlebot nessas URLs.
- **PASS — conteúdo técnico amostrado:** 23/23 HTML, 0 avisos críticos, importantes ou oportunidades conforme heurísticas implementadas, 0 páginas omitidas. O auditor não certifica SEO perfeito nem indexação Google.
- **PASS — testes:** 35 regressões Core-sites em 19/11. CI da aplicação [#44409781323](https://github.com/martaxi-boss/lowcost-europa/actions/runs/44409781323) em 18/11: 843 testes concluídos, job PASS.
- **PASS — Github/VPS no rollout recente:** [VPS #44411061328](https://github.com/martaxi-boss/VPS/actions/runs/44411061328), 18/11 22:26, confirmou app SHA `61d1197ad050902bee81c378fab34a4d82ffbd1c`, igualdade GitHub/VPS, 23 páginas e canonical/hreflang antes/depois, serviços e timers preservados. Não se conclui daqui que todos os processos, env e bancos continuem invariáveis depois desse momento.
- **Mobile (medição de laboratório)**: [Lighthouse 16/11 #43915160792](https://github.com/martaxi-boss/lowcost-europa/actions/runs/43915160792) teve home desempenho 95/SEO 100/acessibilidade 96; HIFU 99/100/97; Pressoterapia 99/100/97; boas práticas 100 nas três. Não mede Web Vitals de campo nem conversões.

## Estado dos motores de pesquisa — última evidência autenticada, não lida novamente hoje

| Serviço | Última evidência | Situação |
| --- | --- | --- |
| Google Search Console | 09/11: sitemap TXT `/sitemap.txt` **Sucesso / 23 URLs descobertas** (propriedade URL-prefix WWW; domínio também verificado). | Entrada XML antiga apresentava «Não foi possível obter», apesar de XML público válido. Não reabrir nem reenviar automaticamente a mesma lista. As 23 descobertas **não são 23 indexadas**. |
| Bing Webmaster Tools | 18/11 ~00:34: XML **Success/23/0 erros/0 avisos** | Homepage e cinco categorias originais constavam como **Discovered but not crawled**. Relatório de desempenho 11–17/11 sem linhas utilizáveis; não inferir ausência de tráfego total. |
| Yandex | 18/11: interface Sitemap files read-only; Add desativado. | Submissão ainda pendente, sem contornar interface ou repetição automática. |
| Brave | Evidência pública histórica 08/11: seis resultados. | Sem nova contagem autenticada nesta auditoria. |
| Seznam | Página inicial confirmada historicamente. | Categorias não confirmadas. |
| DuckDuckGo/Yahoo | Sem confirmação de inclusão registada. | Uma pesquisa isolada não prova exclusão total. |

O Core-sites **não tem sessão autenticada GSC ou Bing**, não leu contas externas nesta ronda e não apresenta clicks, impressões, CTR, posições médias, número de URLs indexadas ou vendas como se fossem medidos.

## Ferrari efetivamente executado

A [ponte Ferrari #44588019929](https://github.com/martaxi-boss/VPS/actions/runs/44588019929), por GitHub Actions → SSH **existente** → Ferrari privado, executou `jq-format-json` no relatório público `lowcost-europa.readiness.json` (1 451 bytes). No ZIP devolveu `artifacts/formatted.json`, `report.json.status=completed`, executor privado `/srv/projects/skill-universal/tools/ubuntu-cli/bin/jq`, SHA-256 **aecd7d607dd3d9df21e67226dfec80e47b58000ead2710a4555e329aa2896743** igual ao relatório inicial, que contém `status=pass`, `xml_urls=23`, `txt_urls=23`. O `quality_gate` é `not_certified` porque não foi pedido gate de aceitação semântica. Esta ferramenta comprovou a integridade do resultado: a verificação HTTP foi feita por GitHub Actions, não por navegador remoto Ferrari.

Já existia uma [missão Ruflo Ferrari](https://github.com/martaxi-boss/VPS/actions/runs/44582867554) em 19/11 com `jq` real e revisor separado, que certificou somente o manifesto `sites.json` (um site Low Cost) e não posições no Google.

## Implementação efetiva do piloto Core-sites

**Já integrado, em produção do próprio core (não dentro da aplicação Django):**

1. Fonte oficial do motor: `martaxi-boss/Core-sites`. `sites.json` contém **apenas lowcost-europa**.
2. Workflow `.github/workflows/seo-growth-core.yml` roda em runner efémero `ubuntu-24.04` sem instalações ou serviços residentes na VPS. Agenda pretendida: todos os dias **07:21 UTC**; agendamentos GitHub não garantem hora ou execução exata.
3. Executa testes offline e analisa URLs do `sitemap.xml`, robots Googlebot, HTTP/metadata, noindex (meta e `X-Robots-Tag`), canonicals, links internos, títulos, H1, descrições.
4. `growth_engine/seo_readiness.py` verifica independentemente XML/TXT/robots + cobertura (novo em [PR #7](https://github.com/martaxi-boss/Core-sites/pull/7)).
5. A fila de crescimento só propõe algo quando há sinal observável de lacuna; nenhuma produção massiva de guias. Sem dados GSC autorizados, 0 propostas é um resultado legítimo.
6. Guarda artefactos JSON/Markdown por 14 dias e atualiza a [issue de monitorização #4](https://github.com/martaxi-boss/Core-sites/issues/4) sem duplicar. A execução de `main` [#44587714395](https://github.com/martaxi-boss/Core-sites/actions/runs/44587714395) atualizou a issue com XML/TXT/robots, 23/23 e 0 alertas.

**O que não está integrado:** o core ainda NÃO modifica `martaxi-boss/lowcost-europa`, NÃO implementa SEO IA com publicação automática, NÃO tem Search Console autenticada nem controlo de conversões/comissões, e NÃO comprova crescimento de rankings.

## Lacunas e próximos passos por prioridade

1. **P1 — Dados reais Search Console.** Encontrar meio oficialmente autorizado, somente leitura e compatível com a regra do proprietário **sem OAuth permanente, Windsor.ai, serviços pagos ou novos píxeis**. Enquanto não existir, declarar claramente sem dados. [Issue #6](https://github.com/martaxi-boss/Core-sites/issues/6).
2. **P1 — Problema de descoberta vs rastreio.** Bing aceita o sitemap mas ainda indicava páginas não rastreadas. Sem erro HTTP reproduzido, não alterar sitemaps por tentativa. Investigar os dados autenticados futuros e o valor dos conteúdos atuais, evitando submeter URLs inalteradas.
3. **P1 — Cliques e conversões reais.** O monitor Nginx [#44535984357](https://github.com/martaxi-boss/VPS/actions/runs/44535984357) registou `observed_search_requests=1` em 19/11 13:42; isso é uma classificação de pedido HTTP, **não** visitante humano, clique oficial GSC, venda ou comissão. Não usar esse contador para alegar crescimento.
4. **P2 — Frequência do monitor.** O workflow `lowcost-search-referrers-daily.yml` está configurado com cron `31 * * * *`, mas entre os runs recentes de 19/11 só foram observadas execuções a 03:44 e 13:41 UTC. GitHub Actions schedule é best effort; não prometer relatório de hora a hora, nem adicionar outro daemon sem necessidade.
5. **P2 — Auditoria comercial e mobile real.** O teste de site não voltou a executar compras AliExpress, consentimentos, conversões nem navegação num Android físico. O Lighthouse acima é um laboratório e não substitui este teste.
6. **P2 — Alterações nos sites.** Só preparar alterações Django isoladas por pull request no repositório Low Cost quando houver um defeito reproduzido ou uma oportunidade fundamentada em dados. Respeitar curadoria manual e links existentes; fazer testes/rollback e ativação via GitHub Actions→VPS (sem SSH novo).

## Decisão

**Não alterar o site nem os sitemaps agora.** O problema comercial ainda não está comprovado como erro técnico; depende principalmente de indexação, procura real e medição autorizada. Continuar o piloto exclusivamente no Low Cost, com rotinas suaves e revisões baseadas em evidência, sem proxies ou tráfego artificial.

Os relatórios são historicamente datados e não substituem leitura autenticada atual de Search Consoles.
