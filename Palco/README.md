# Palco 🎤 — seu apresentador de slides

Transforma **"preciso apresentar isso"** numa apresentação de slides pronta, bonita e
persuasiva — em português, com a sua marca e com um **roteiro de fala em cada slide**
para você não travar na hora. Tudo conversando, sem PowerPoint, sem instalar programa.

O Palco serve para **pitch comercial, proposta, apresentação para a diretoria/board,
leitura de resultados (RMA), defesa de projeto e palestra**. Ele organiza sua ideia como
uma história (com um pedido claro no fim), escreve os slides no seu tom de voz e gera um
arquivo que abre no navegador e **vira PDF** na hora.

> **Regra de ouro:** o Palco **nunca inventa** número, valor, depoimento ou cliente. Quando
> falta um dado real, ele marca **[PREENCHER]** para você completar. Você apresenta e decide —
> o Palco prepara.

---

## O que ele faz (6 modos)

| Modo | O que você diz | O que recebe |
|------|----------------|--------------|
| **Roteirizar** | "Preciso apresentar uma proposta pra um cliente" | A estrutura da história, slide a slide, para aprovar |
| **Montar** | "Pode montar" | A apresentação pronta (arquivo que abre no navegador) |
| **Ensaiar** | "Me ajuda a ensaiar" | Roteiro de fala, abertura/fechamento, perguntas difíceis prováveis |
| **Tema & Marca** | "Usa a minha cor / meu logo" | A apresentação com a sua identidade visual |
| **Ajustar** | "Esse slide tá cheio, encurta" | O slide refinado, sem encher de texto |
| **Exportar** | "Como salvo em PDF?" | O passo a passo para gerar o PDF |

## Como instalar (1 minuto)

1. Baixe e **descompacte** o arquivo `Palco.zip`.
2. Copie a pasta `Palco` para dentro de `.claude/skills/` no seu projeto
   (ou em `~/.claude/skills/` para usar em qualquer lugar).
3. Abra o Claude Code nessa pasta. Pronto.

## Como usar

Na primeira vez, diga **"configurar Palco"** — ele faz algumas perguntas rápidas (seu nome,
empresa, cor da marca, tom de voz) e guarda tudo localmente. Depois, é só pedir em linguagem
natural, por exemplo:

- *"Tenho uma reunião quinta com um cliente, preciso de uma apresentação da minha proposta."*
- *"Monta uns slides executivos pra eu levar pra diretoria sobre o resultado do trimestre."*
- *"Preciso defender meu projeto pro síndico, me ajuda com a apresentação?"*
- *"Faz os slides da minha palestra sobre IA pra contadores."*

Quando a apresentação ficar pronta, abra o arquivo `apresentacao.html` no navegador:
- **Setas ← →** passam os slides
- **N** mostra/esconde as **notas do apresentador** (o que falar em cada slide)
- **P** (ou Ctrl/Cmd + P) → **Salvar como PDF**
- **F11** → tela cheia para projetar

## O que esperar

- **Nunca inventa dados.** Falta um número real? Ele marca `[PREENCHER]`.
- **Um slide, uma ideia.** O detalhe vai para a sua nota de fala, não para a tela.
- **Termina sempre com um pedido claro** — a plateia sabe o próximo passo.
- **A voz é a sua** — formal ou próxima, do jeito que você configurou.
- **Seus dados ficam no seu computador**, na pasta `.palco/`.

## Privacidade
Tudo é local. O Palco não envia nada para lugar nenhum. As respostas da configuração ficam
em `.palco/config.md`, no seu projeto.

---

Feito para a comunidade **Maestria Academy**. Licença MIT — use, adapte, compartilhe.
