# Notas do apresentador (o roteiro de fala)

O maior medo de quem não apresenta muito é **"e se eu travar?"**. Por isso todo
deck do Palco carrega, em cada slide, uma **nota do apresentador** — o que falar
quando aquele slide estiver na tela. No deck aberto, a tecla **N** mostra/esconde
as notas (ficam invisíveis na projeção e na impressão; são só para quem apresenta).

## Como escrever uma boa nota (campo `"nota"` de cada slide)
- Escreva como **fala**, não como texto: a frase que a pessoa diria em voz alta.
- 1 a 3 frases por slide. A nota é um trilho, não um roteiro decorado.
- Inclua, quando ajudar:
  - **a transição** ("depois de mostrar o problema, eu emendo…")
  - **o exemplo a citar** ("conte o caso do cliente X aqui")
  - **a pergunta a fazer** ("pergunte: quanto isso custa por mês pra vocês?")
  - **o tempo** ("não passe de 1 min aqui")
- Marque com **[PREENCHER]** tudo que depende de um dado real que o dono tem e a
  IA não — número do cliente, nome do caso, valor. Nunca invente para preencher.

## Exemplo
```json
{ "tipo":"numero", "numero":"23%", "titulo":"das consultas viram falta",
  "legenda":"Média do setor sem confirmação ativa",
  "nota":"Mostre o 23% e faça uma pausa. Pergunte: 'quantas faltas vocês tiveram mês passado?'. Se ele disser o número, troque o 23% pelo dele — fica muito mais forte. [PREENCHER número real se houver]" }
```

## Modo "Ensaiar" (o que entregar quando o dono pede para ensaiar)
Além das notas por slide, ajude o dono a se preparar:
1. **Tempo total** estimado (≈1-2 min/slide) e onde ele costuma estourar.
2. **Abertura forte** (as 2 primeiras frases, decoradas) e **fechamento** (o pedido, decorado).
3. **3 perguntas difíceis prováveis** que a plateia pode fazer + uma resposta curta e honesta
   para cada (sem prometer o que não pode cumprir).
4. **Plano B**: o que cortar se o tempo encurtar (quais slides pular sem perder a história).

Lembre o dono: **ele apresenta, o Palco prepara.** A skill nunca "apresenta no lugar dele"
nem promete resultado — ela organiza a história e o roteiro de fala.
