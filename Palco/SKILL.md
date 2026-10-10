---
name: palco
description: >
  Monta apresentações de slides profissionais e persuasivas em português a partir
  de uma conversa — pitch comercial, proposta, apresentação executiva/board, leitura
  de resultados (RMA), defesa de projeto ou palestra. Gera um deck HTML autossuficiente
  (navega pelo teclado, vira PDF imprimindo) com a marca do dono e um roteiro de fala
  (notas do apresentador) em cada slide. Use quando alguém disser "preciso apresentar",
  "montar uma apresentação/slides/deck", "fazer um pitch", "apresentar pra diretoria/cliente",
  "slides da proposta", "apresentação executiva" ou "tenho uma reunião e preciso de slides".
  Nunca inventa números, depoimentos ou dados — marca [PREENCHER] quando falta dado real.
---

# Palco — seu apresentador de slides

Transforma "preciso apresentar X" em uma **apresentação de slides pronta**: estruturada
como história (com um pedido no fim), bonita, com a marca do dono e com um **roteiro de
fala** em cada slide para quem não tem segurança de apresentar. A saída é um arquivo HTML
que abre no navegador, navega pelo teclado e **vira PDF imprimindo** — sem internet, sem
PowerPoint, sem instalar nada.

Não confunda com outras skills da casa:
- **Vitrine** monta um *painel/dashboard de métricas* de resultado — Palco monta a *apresentação narrativa de slides* para falar ao vivo.
- **Forja "Apresentar"** faz um *one-pager de uma oferta* — Palco faz a *apresentação multi-slide* completa.
- **Holofote** produz *conteúdo público para redes* — Palco prepara uma *apresentação para uma reunião/plateia*.

## Quando usar
"Preciso apresentar", "montar slides/apresentação/deck", "fazer um pitch", "apresentar
pra diretoria/board/cliente", "slides da proposta", "apresentação executiva", "RMA em
slides", "defender meu projeto", "tenho uma palestra".

## Princípios invioláveis (valem em todos os modos)
1. **Nunca inventa** número, valor, data, depoimento, caso ou cliente. Falta dado real → `[PREENCHER]`. (`references/anti_slop.md`)
2. **Um slide = uma ideia.** Detalhe vai para a nota do apresentador, não para o slide.
3. **Termina sempre com um pedido claro** (próximos passos).
4. **A voz é a do dono** (tom de `config.md`); o Palco prepara, **o dono apresenta e decide**.
5. **Dados 100% locais** em `.palco/`.

## Primeira vez (setup)
Se existir `setup/SETUP.md` e não existir `.palco/config.md`, rode a primeira conversa de
`setup/SETUP.md` (nome, empresa, público típico, tom, cor da marca, logo, tema, contato),
grave `.palco/config.md`, garanta `.palco/` no `.gitignore` e **apague a pasta `setup/`**.
Depois, sempre leia `.palco/config.md` no começo para aplicar marca, tema e tom.

## Os 6 modos

### 1. Roteirizar — desenhar a história antes de escrever
Quando o dono diz o que precisa apresentar, primeiro **entenda**: objetivo (o que ele quer
que aconteça no fim?), público, tempo disponível, e o que ele já tem de dado/material.
Escolha a **estrutura narrativa** em `references/frameworks.md` (pitch, executiva/board, RMA,
defesa de projeto, palestra). Devolva o **esqueleto**: a lista de slides, um por linha, com
o tipo e uma frase do que vai em cada. Confirme antes de escrever tudo.

### 2. Montar — escrever os slides e gerar o deck
Escreva o conteúdo de cada slide seguindo `references/tipos_de_slide.md` e `anti_slop.md`,
e a **nota do apresentador** de cada um (`references/notas_apresentador.md`). Monte o objeto
do deck (tema + marca de `config.md` + slides) num JSON e gere o HTML:
```bash
python3 scripts/palco.py deck.json apresentacao.html
```
Salve `apresentacao.html` na pasta do dono. Diga a ele: abra no navegador, **setas** navegam,
**N** mostra as notas de fala, **P** (ou Ctrl/Cmd+P) salva em **PDF**, **F11** tela cheia.

### 3. Ensaiar — preparar a fala
Entregue o roteiro de fala consolidado: tempo total estimado, abertura e fechamento para
decorar, **3 perguntas difíceis prováveis com respostas honestas**, e um plano B de cortes
se o tempo encurtar. Detalhe em `references/notas_apresentador.md` (seção Ensaiar).

### 4. Tema & Marca — vestir com a cara do dono
Aplique/ajuste o tema visual (`references/temas.md`) e a marca: cor de destaque = cor da
marca, logo na capa, nome/contato no rodapé. Sugira o tema certo pelo contexto (board →
`executivo`/`consultoria`; agência → `criativo`; engenharia/laudo → `tecnico`; vão imprimir
→ `claro`). Regere o HTML.

### 5. Ajustar — refinar slide a slide
Edite um slide específico, reordene, **encurte** (regra anti-clutter: máx. ~5 bullets de
uma linha), quebre um slide cheio em dois, corte jargão genérico, troque um bullet fraco por
um específico. Regere o HTML. Nunca adicione dado novo sem origem real.

### 6. Exportar — virar PDF / PPTX
PDF é nativo: abrir o HTML e imprimir (P) em "Salvar como PDF", layout paisagem — cada slide
vira uma página A4. Se o dono **precisa mesmo de .pptx editável**, explique que o HTML é a
entrega principal (projeta e imprime igual a um PowerPoint) e que dá para recriar no
PowerPoint/Google Slides usando o conteúdo já escrito, slide a slide. Não prometa conversão
automática que a skill não faz.

## O motor (`scripts/palco.py`)
Só biblioteca padrão do Python. Recebe um JSON com `titulo`, `tema`, `marca` e `slides[]`,
e gera **um** HTML autossuficiente (navegação por teclado, barra de progresso, contador,
modo notas com a tecla N, impressão em PDF com 1 slide/página). Tipos de slide: `capa`,
`agenda`, `secao`, `conteudo`, `colunas`, `comparativo`, `numero`, `citacao`, `tabela`,
`passos`, `encerramento`. Todo slide aceita `nota` e `eyebrow`. O motor **só renderiza** o
que está no JSON — nunca cria conteúdo. Ver o cabeçalho do arquivo para o formato completo.

## Referências
- `references/frameworks.md` — estruturas narrativas por objetivo
- `references/tipos_de_slide.md` — catálogo de slides e campos
- `references/temas.md` — temas visuais e como casar com a marca
- `references/notas_apresentador.md` — como escrever o roteiro de fala + modo Ensaiar
- `references/anti_slop.md` — nunca-inventa + anti-cara-de-IA + checklist
