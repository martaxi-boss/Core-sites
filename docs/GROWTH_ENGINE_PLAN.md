# Growth Engine — arquitetura proposta para o Core-sites

Estado: estratégia de evolução. **Não implementada**. O motor v1 existente analisa SEO técnico e produz backlog; não publica conteúdos, não mede posições nem gera tráfego.

## Objetivo comercial

Aumentar a descoberta orgânica e os cliques qualificados para fornecedores nos websites registados, sem automação de visitas fictícias, manipulação de CTR, spam ou instalação de serviços residentes na VPS. O core é multi-site, com regras e calendários próprios para cada projeto.

## Referências abertas investigadas (19/11/2026)

| Referência | Licença indicada no repositório | Ideia que vale estudar | Cautela |
| --- | --- | --- | --- |
| https://github.com/tentacl-ai/seo-autopilot | MIT | Ciclo crawl → diagnóstico → correção → avaliação antes/depois; integração GSC; filas de aprovação | Não instalar cegamente; auditar dependências, custos externos e arquitetura |
| https://github.com/NeoZi12/dispatchseo | AGPL-3.0 | Investigação de temas, fila editorial, propostas de artigos como pull requests, medição após publicação | Se reutilizarmos código, rever condições da AGPL; não copiar diretamente para o core MIT sem estudar obrigações |
| https://github.com/harlan-zw/unlighthouse | MIT | Auditoria Lighthouse de cobertura mais ampla, evitando depender de uma única página | Usar runner descartável e limites de páginas; Low Cost já tem Lighthouse semanal |
| https://github.com/StJudeWasHere/seonaut | MIT | Priorização dos problemas por gravidade e impacto | Stack Go + MySQL mais pesado; estudar conceitos em vez de instalar serviço |
| https://github.com/lycheeverse/lychee | Apache-2.0 | Verificar links partidos e URLs externas de forma controlada | Limitar rede e frequência de verificações |

As ideias gerais e os algoritmos próprios podem ser implementados nativamente no Core-sites, sem incluir código de terceiros. Qualquer cópia/adaptação substancial de código de terceiros requer verificar a licença da versão concreta e cumprir as atribuições.

## Pipeline proposto: oportunidades reais → alterações pequenas → medição

1. **Sinais reais** (read-only): importar dados de Search Console via integração autorizada, quando disponível; capturar query, página, país, impressões, cliques, CTR e posição média. Não inventar resultados. Sem acesso, usar apenas dados públicos e assinalar lacunas.
2. **Seleção de oportunidades**: detetar páginas com impressões e CTR fraco, URLs sem tráfego mas com potencial de intenção comercial, títulos não diferenciados, ligações internas fracas e categorias com conteúdo duplicado. Não usar números arbitrários como prova de posição.
3. **Fila editorial**: sugestões pontuais de guias e comparações originais orientadas para a escolha de produtos; priorizar relevância PT e claims verificáveis. Nenhuma publicação massiva.
4. **Correções propostas por pull request**: cada site mantém o seu repositório, testes e processo de publicação. O Core-sites só cria propostas isoladas e regista impacto previsto; não altera diretamente produção.
5. **Medição posterior**: comparar períodos equivalentes de 7, 28 e 56 dias com dados reais, assinalar sazonalidade e ausência de amostra; medir cliques orgânicos qualificados e cliques de saída para os parceiros quando existirem.
6. **Distribuição autorizada**: considerar canais próprios com API oficial ou agendamento consentido. Nunca fazer publicações repetitivas em grupos ou obter cliques falsos.

## Ritmo moderado inicial

- Verificação técnica: diária, sem execução residente na VPS (já configurada em v1).
- Oportunidades comerciais: revisão semanal de dados, quando existirem.
- Propostas editoriais: máximo inicial de 1–2 por site por semana, sujeitas a validação e aprovação.
- Métricas: avaliação de tendências após acumulação de dados reais; nenhuma promessa de subir posições num prazo fixo.

## Restrições por site

**Low Cost Europa** (Django): produtos e links inseridos manualmente pelo proprietário. O Core-sites não pode criar produtos, substituir links, reativar descoberta de catálogo nem alterar automações internas; a prioridade é explicar diferenças entre equipamentos e melhorar páginas existentes.

**Sevelora** (Next.js, afiliação Awin): sincronização do feed pertence à aplicação. O Core-sites não escreve no catálogo nem tem acesso às credenciais de afiliação; deve diferenciar páginas e guias em pt-PT, evitar conteúdo genérico do fornecedor e propor melhorias verificadas.

## Próximas implementações no Core-sites

1. **Módulo read-only de dados Google Search Console**, sem novo serviço pago nem autenticação permanente indevida. Requer credenciais/autorização existentes ou a disponibilizar pelo proprietário.
2. **Motor de oportunidades de procura** com regras explícitas e saída JSON testada, respeitando janelas de dados e erros.
3. **Gerador de briefings SEO** (não gerador cego de 100 artigos) e estrutura de pull requests com diffs isolados por site.
4. **Medição de resultados** por domínio, com antes/depois e distinção entre visitantes humanos, pedidos HTTP e cliques oficiais.
5. **Relatório semanal** de melhorias sugeridas, aplicadas e observadas, sempre com fonte verificável.

## Fontes normativas

- https://developers.google.com/search/docs/fundamentals/creating-helpful-content
- https://developers.google.com/search/docs/essentials/spam-policies
- https://developers.google.com/webmaster-tools/v1/searchanalytics/query

Não confundir auditoria automática com crescimento efetivo. O objetivo do core é transformar sinais reais em tarefas e melhorias úteis, depois medir se trouxeram mais procura e vendas.
