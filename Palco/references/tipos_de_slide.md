# Tipos de slide (catálogo do palco.py)

Monte o deck como uma lista de objetos `slides`. Cada slide tem um `tipo`.
Todo slide aceita `"nota"` (roteiro de fala — ver notas_apresentador.md) e
`"eyebrow"` (rótulo pequeno acima do título). Campos não usados podem ser omitidos.

| tipo | Para quê | Campos |
|------|----------|--------|
| `capa` | Abertura | `titulo`, `subtitulo`, `eyebrow`, `rodape` |
| `agenda` | Roteiro da fala | `titulo`, `itens[]` |
| `secao` | Divisória entre blocos | `numero`, `titulo`, `subtitulo` |
| `conteudo` | Slide padrão (texto + bullets) | `titulo`, `texto`, `itens[]` |
| `colunas` | 2-4 blocos lado a lado | `titulo`, `colunas[{titulo, itens[]}]` |
| `comparativo` | Antes × Depois (o salto) | `titulo`, `antes{titulo,itens[]}`, `depois{titulo,itens[]}` |
| `numero` | Um número que prende | `numero`, `titulo`, `legenda` |
| `citacao` | Frase / depoimento (só real) | `texto`, `autor` |
| `tabela` | Dados estruturados | `titulo`, `colunas[]`, `linhas[[...]]` |
| `passos` | Próximos passos numerados | `titulo`, `itens[]` |
| `encerramento` | Fechamento + pedido | `titulo`, `subtitulo`, `contato` |

## Boas práticas por tipo
- **capa**: a promessa, não o assunto. "Recepção que não perde paciente" > "Apresentação".
- **conteudo**: no máximo **5 bullets**, cada um **uma linha**. Se passar disso, vire `colunas`
  ou quebre em dois slides. Bullet não é frase inteira — é a ideia.
- **numero**: um número por slide. O número é a estrela; o resto é legenda.
- **comparativo**: serve para mostrar transformação — é o slide mais persuasivo de um pitch.
- **tabela**: 2-4 colunas, poucas linhas. Tabela densa não se lê de longe.
- **citacao**: só depoimento/frase REAL. Nunca invente depoimento (ver anti_slop.md).
- **passos**: sempre termine a apresentação com um destes ou com `encerramento` — a plateia
  precisa saber **o que acontece agora**.

## Regra de densidade (do mundo real)
- Um slide com **uma linha só** é desperdício, a menos que seja `secao`, `numero`,
  `citacao` ou `encerramento` (que são intencionalmente enxutos).
- Um slide com **texto demais** ninguém lê. O equilíbrio: título forte + 3 a 5 ideias curtas.
- O que é detalhe **vai para a nota do apresentador**, não para o slide. O slide é o pôster;
  a fala é o filme.
