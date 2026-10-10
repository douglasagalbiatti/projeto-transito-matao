# Temas visuais (escolha pelo contexto e pela marca)

O `palco.py` traz 5 temas prontos. Cada um já tem um par de fontes e uma paleta
afinados — você só escolhe o nome e, opcionalmente, troca a **cor de destaque**
pela cor da marca do dono (`marca.cor`). Não invente CSS: use o tema.

| Tema | Quando usar | Clima | Fonte de título | Fundo |
|------|-------------|-------|------------------|-------|
| `executivo` | Board, diretoria, proposta corporativa, RMA executivo | Sóbrio, confiável | Fraunces (serifa) | Escuro azulado |
| `consultoria` | Consultoria, finanças, jurídico, perícia | Elegante, premium | Spectral (serifa) | Quase preto + dourado |
| `criativo` | Agência, marketing, conteúdo, lançamento | Energia, moderno | Sora | Escuro roxo |
| `tecnico` | Engenharia, arquitetura, laudo, produto, dados | Limpo, preciso | IBM Plex Sans | Escuro neutro |
| `claro` | Quando vão imprimir, sala muito clara, ou marca clara | Leve, arejado | Fraunces sobre creme | Creme/ivory |

## Como casar com a marca
- **Cor de destaque** (`marca.cor`): use a cor principal da marca do dono (hex). Ela
  pinta títulos de destaque, números grandes, marcadores e a barra de progresso.
  Se o dono não tem cor definida, deixe o padrão do tema.
- **Logo** (`marca.logo`): caminho de um PNG/JPG local (vira data URI embutido, funciona
  offline) **ou** uma URL. Aparece na capa. Sem logo, a capa usa só o nome.
- **Nome / rodapé** (`marca.nome`, `marca.rodape`): nome da empresa no rodapé de cada
  slide e contato na capa/encerramento.

## Regras anti-cara-de-IA (resumo — detalhe em anti_slop.md)
- Nunca o roxo→azul degradê genérico nem "ícone dentro de caixinha com gradiente" em todo card.
- Fundo dominante neutro + UMA cor de destaque. Não encha de cores.
- Título grande com tracking negativo; corpo respirando. Hierarquia clara.
- Varie o ritmo: nem todo slide é três cards iguais. Alterne `secao`, `numero`,
  `citacao`, `comparativo`, `conteudo`.
- Cada tema só funciona se o **conteúdo** for específico. Slide bonito com texto
  genérico continua sendo slide ruim.
