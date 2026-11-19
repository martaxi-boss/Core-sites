# Core-sites v2 - integração de ideias open source

**Estado:** implementação experimental em branch de teste. Não é um CMS e não publica alterações nos websites.

A versão v2 utiliza ideias e métodos de projetos públicos, mas o código escrito no Core-sites é original. Não copiámos ficheiros de terceiros, portanto não estamos a instalar os projetos originais. Antes de qualquer reutilização direta de código, é necessário rever a licença e obrigações da versão concreta.

## Referências aproveitadas

| Repositório | Licença indicada no GitHub | Ideia aproveitada e resultado |
| --- | --- | --- |
| https://github.com/tentacl-ai/seo-autopilot | MIT | Diagnosticar e priorizar problemas, preparar melhorias e aceitar dados reais do Search Console |
| https://github.com/NeoZi12/dispatchseo | AGPL-3.0 | Fila editorial e briefings orientados à intenção de compra, sem publicação automática nem copiar código AGPL |
| https://github.com/StJudeWasHere/seonaut | MIT | Prioridades P0/P1/P2 e agrupamento de problemas por URL |
| https://github.com/harlan-zw/unlighthouse | MIT | Verificações de qualidade mobile em páginas escolhidas, usando Lighthouse direto e um runner temporário |
| https://github.com/lycheeverse/lychee | Apache-2.0 | Verificação de links internos que apontem para URLs do sitemap com falha na mesma auditoria |

## O que a v2 já consegue fazer

1. Ler um sitemap XML público, respeitar robots.txt e analisar páginas sem alterar servidores de produção.
2. Identificar erros de indexação técnicos visíveis, títulos e descrições duplicados, e links internos para páginas que falharam.
3. Criar por site uma fila de prioridades com evidência e recomendação clara.
4. Gerar no máximo dois briefings editoriais por site e ronda, adaptados ao conteúdo comercial, sem publicar.
5. Produzir relatórios de auditoria e relatórios de crescimento na mesma execução do GitHub Actions.
6. Permitir um teste Lighthouse mobile manual e limitado, sem instalar nada permanentemente na VPS.
7. Aceitar, apenas no ambiente local e privado, dados conjuntos de página + consulta da Search Console em CSV, validando domínio, contagens e posições.

## O que ainda não faz

- Não possui ligação autenticada automática à Google Search Console; sem dados oficiais de procura, as oportunidades são heurísticas.
- Não cria páginas, publica conteúdos nem abre pull requests nos repositórios dos sites.
- Não gera visitantes, CTR artificial, cliques falsos nem utiliza proxies.
- Não mede encomendas ou vendas na Awin e não promete melhorias de ranking.

## Formatos e testes

O programa seo_growth_core.py cria, para cada site, um relatório JSON e Markdown com as observações públicas.

O programa growth_engine.cli transforma esses resultados em ficheiros .growth.json e .growth.md, contendo prioridades e briefings.

Para executar testes offline:

    python3 -m unittest discover -s tests -p 'test_*.py' -v

Para testar o motor em modo reduzido:

    python3 seo_growth_core.py --config sites.json --out reports --max-pages 3
    python3 -m growth_engine.cli --config sites.json --audit-dir reports --out reports

Para usar dados privados da Search Console (apenas em ambiente controlado e nunca no Actions do repositório público):

    python3 -m growth_engine.cli --config sites.json --audit-dir reports --out reports --gsc-dir gsc-private

Ficheiros aceites: gsc-private/lowcost-europa.csv e gsc-private/sevelora.csv. O CSV precisa das colunas conjuntas página, consulta, cliques, impressões e posição, exportadas pelo Google. O importador não inventa dados ausentes. Estes ficheiros e relatórios privados não devem ser publicados em repositórios ou artefactos.

## Política moderada e específicas dos sites

- **Low Cost Europa**: não alterar produtos, ligações manuais, preços, categorias e regras de gestão da montra. Priorizar aconselhamento e comparações factuais.
- **Sevelora**: não alterar o feed Awin/Diversual ou os segredos. Priorizar textos originais, informação útil e navegação.
- **Ritmo**: análise diária, propostas de conteúdo apenas para revisão, com limite inicial de duas por ronda e por site.
- **Segurança**: sem instalações globais, serviços residentes, escrita no VPS, acesso ao cofre ou alteração automática de conteúdos públicos.
- **Medição**: comparar apenas dados oficiais de períodos equivalentes, sem confundir impressões, visitas reais, pedidos HTTP e vendas.

O motor de crescimento deve produzir tarefas concretas que possam virar melhorias aprovadas nos repositórios dos sites. As métricas posteriores à publicação serão medidas em fontes próprias; não é possível comprovar crescimento apenas com este teste técnico.
