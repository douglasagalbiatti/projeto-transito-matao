#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Palco — renderizador de apresentacao de slides (somente biblioteca padrao).

Recebe um arquivo JSON com a especificacao do deck (tema, marca e slides) e
gera UM arquivo HTML autossuficiente: navegavel pelo teclado (setas / espaco),
com barra de progresso, contador de slides, modo apresentador (tecla "N" mostra
as notas de fala) e PRONTO PARA IMPRIMIR EM PDF (cada slide vira uma pagina A4
paisagem). Nao precisa de internet, node, npm nem nenhuma API.

Uso:
    python3 palco.py deck.json apresentacao.html

Formato do deck.json (todos os campos opcionais tem padrao sensato):
{
  "titulo": "Proposta — Clinica X",
  "tema": "executivo",                 # executivo | consultoria | criativo | tecnico | claro
  "marca": {
    "nome": "Sua Empresa",
    "cor": "#1F6FEB",                  # cor de destaque (hex)
    "logo": "logo.png",               # caminho/URL opcional (embutido se for arquivo local)
    "rodape": "contato@empresa.com.br"
  },
  "slides": [
    {"tipo": "capa", "titulo": "...", "subtitulo": "...", "nota": "fala do apresentador"},
    {"tipo": "agenda", "titulo": "Roteiro", "itens": ["...", "..."]},
    {"tipo": "secao", "titulo": "1. Diagnostico", "numero": "01"},
    {"tipo": "conteudo", "titulo": "...", "itens": ["...", "..."], "nota": "..."},
    {"tipo": "colunas", "titulo": "...", "colunas": [{"titulo":"Hoje","itens":[...]},{"titulo":"Com a solucao","itens":[...]}]},
    {"tipo": "numero", "titulo": "...", "numero": "37%", "legenda": "...", "nota":"..."},
    {"tipo": "citacao", "texto": "...", "autor": "..."},
    {"tipo": "comparativo", "titulo":"...", "antes":{"titulo":"Antes","itens":[...]}, "depois":{"titulo":"Depois","itens":[...]}},
    {"tipo": "tabela", "titulo":"...", "colunas":["A","B"], "linhas":[["1","2"],["3","4"]]},
    {"tipo": "passos", "titulo":"Proximos passos", "itens":["...","..."]},
    {"tipo": "encerramento", "titulo":"Obrigado", "subtitulo":"Vamos comecar?", "contato":"..."}
  ]
}

Nunca inventa dados: o conteudo vem inteiro do JSON. Lacunas devem vir marcadas
como [PREENCHER] pela camada que monta o deck.
"""

import sys, json, os, base64, html, mimetypes

# ----------------------------------------------------------------------------
# Temas: cada tema define a familia de fontes (Google Fonts), o fundo, a tinta
# do texto, superficies e uma cor de destaque padrao (sobreposta pela marca).
# ----------------------------------------------------------------------------
TEMAS = {
    "executivo": {
        "display": "Fraunces", "body": "Inter",
        "fonts_url": "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600&display=swap",
        "fundo": "#0E1726", "tinta": "#EAF0F8", "suave": "#9FB0C9",
        "superficie": "#16223A", "borda": "rgba(255,255,255,.10)", "destaque": "#5B8DEF",
        "claro": False,
    },
    "consultoria": {
        "display": "Spectral", "body": "Inter",
        "fonts_url": "https://fonts.googleapis.com/css2?family=Spectral:wght@500;600;700&family=Inter:wght@400;500;600&display=swap",
        "fundo": "#0B0D12", "tinta": "#F2F4F7", "suave": "#A9B0BC",
        "superficie": "#151821", "borda": "rgba(255,255,255,.09)", "destaque": "#C9A227",
        "claro": False,
    },
    "criativo": {
        "display": "Sora", "body": "Inter",
        "fonts_url": "https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;500;600&display=swap",
        "fundo": "#121018", "tinta": "#F4F1FA", "suave": "#B6AEC9",
        "superficie": "#1C1828", "borda": "rgba(255,255,255,.10)", "destaque": "#8B5CF6",
        "claro": False,
    },
    "tecnico": {
        "display": "IBM Plex Sans", "body": "IBM Plex Sans",
        "fonts_url": "https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500&display=swap",
        "fundo": "#0C1116", "tinta": "#E6EDF3", "suave": "#9DA9B4",
        "superficie": "#141B22", "borda": "rgba(255,255,255,.10)", "destaque": "#2F9E8F",
        "claro": False,
    },
    "claro": {
        "display": "Fraunces", "body": "Inter",
        "fonts_url": "https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Inter:wght@400;500;600&display=swap",
        "fundo": "#FBF8F1", "tinta": "#1B2330", "suave": "#5B6675",
        "superficie": "#FFFFFF", "borda": "rgba(20,30,45,.10)", "destaque": "#1F6FEB",
        "claro": True,
    },
}


def esc(t):
    return html.escape(str(t if t is not None else ""))


def embed_logo(caminho):
    """Embute um logo local como data URI; se for URL, devolve a propria URL."""
    if not caminho:
        return ""
    if str(caminho).startswith(("http://", "https://", "data:")):
        return caminho
    if os.path.isfile(caminho):
        mime = mimetypes.guess_type(caminho)[0] or "image/png"
        with open(caminho, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        return f"data:{mime};base64,{b64}"
    return ""  # caminho invalido -> sem logo (nunca inventa)


# ----------------------------------------------------------------------------
# Renderizacao de cada tipo de slide -> HTML interno
# ----------------------------------------------------------------------------
def _lista(itens):
    if not itens:
        return ""
    lis = "".join(f"<li>{esc(i)}</li>" for i in itens)
    return f"<ul class='lista'>{lis}</ul>"


def render_slide(s, idx, total):
    tipo = s.get("tipo", "conteudo")
    nota = s.get("nota", "")
    nota_html = f"<aside class='notas' aria-hidden='true'>{esc(nota)}</aside>" if nota else ""
    eyebrow = f"<div class='eyebrow'>{esc(s['eyebrow'])}</div>" if s.get("eyebrow") else ""

    if tipo == "capa":
        logo = "<img class='capa-logo' src='__LOGO__' alt=''>" if "__HASLOGO__" else ""
        corpo = f"""
        <div class='slide capa'>
          <div class='capa-top'>{logo}<span class='capa-marca'>__MARCA__</span></div>
          <div class='capa-mid'>
            {eyebrow}
            <h1 class='capa-titulo'>{esc(s.get('titulo','[PREENCHER titulo]'))}</h1>
            <p class='capa-sub'>{esc(s.get('subtitulo',''))}</p>
          </div>
          <div class='capa-base'>{esc(s.get('rodape',''))}</div>
        </div>"""

    elif tipo == "agenda":
        itens = s.get("itens", [])
        lis = "".join(
            f"<li><span class='ag-num'>{i+1:02d}</span><span>{esc(t)}</span></li>"
            for i, t in enumerate(itens)
        )
        corpo = f"""
        <div class='slide pad'>
          {eyebrow}<h2 class='titulo'>{esc(s.get('titulo','Roteiro'))}</h2>
          <ol class='agenda'>{lis}</ol>
        </div>"""

    elif tipo == "secao":
        corpo = f"""
        <div class='slide secao'>
          <div class='secao-num'>{esc(s.get('numero',''))}</div>
          <h2 class='secao-titulo'>{esc(s.get('titulo','[PREENCHER]'))}</h2>
          <p class='secao-sub'>{esc(s.get('subtitulo',''))}</p>
        </div>"""

    elif tipo == "colunas":
        cols = s.get("colunas", [])
        cards = "".join(
            f"<div class='card'><h3>{esc(c.get('titulo',''))}</h3>{_lista(c.get('itens',[]))}</div>"
            for c in cols
        )
        corpo = f"""
        <div class='slide pad'>
          {eyebrow}<h2 class='titulo'>{esc(s.get('titulo',''))}</h2>
          <div class='grid cols-{max(1,len(cols))}'>{cards}</div>
        </div>"""

    elif tipo == "comparativo":
        a = s.get("antes", {}); d = s.get("depois", {})
        corpo = f"""
        <div class='slide pad'>
          {eyebrow}<h2 class='titulo'>{esc(s.get('titulo',''))}</h2>
          <div class='grid cols-2'>
            <div class='card card-antes'><h3>{esc(a.get('titulo','Antes'))}</h3>{_lista(a.get('itens',[]))}</div>
            <div class='card card-depois'><h3>{esc(d.get('titulo','Depois'))}</h3>{_lista(d.get('itens',[]))}</div>
          </div>
        </div>"""

    elif tipo == "numero":
        corpo = f"""
        <div class='slide numero'>
          {eyebrow}<div class='big-num'>{esc(s.get('numero','[N]'))}</div>
          <h2 class='num-titulo'>{esc(s.get('titulo',''))}</h2>
          <p class='num-legenda'>{esc(s.get('legenda',''))}</p>
        </div>"""

    elif tipo == "citacao":
        corpo = f"""
        <div class='slide citacao'>
          <blockquote>{esc(s.get('texto','[PREENCHER]'))}</blockquote>
          <div class='cit-autor'>{esc(s.get('autor',''))}</div>
        </div>"""

    elif tipo == "tabela":
        cols = s.get("colunas", [])
        th = "".join(f"<th>{esc(c)}</th>" for c in cols)
        rows = ""
        for ln in s.get("linhas", []):
            tds = "".join(f"<td>{esc(v)}</td>" for v in ln)
            rows += f"<tr>{tds}</tr>"
        corpo = f"""
        <div class='slide pad'>
          {eyebrow}<h2 class='titulo'>{esc(s.get('titulo',''))}</h2>
          <table class='tabela'><thead><tr>{th}</tr></thead><tbody>{rows}</tbody></table>
        </div>"""

    elif tipo == "passos":
        itens = s.get("itens", [])
        lis = "".join(
            f"<li><span class='passo-num'>{i+1}</span><span>{esc(t)}</span></li>"
            for i, t in enumerate(itens)
        )
        corpo = f"""
        <div class='slide pad'>
          {eyebrow}<h2 class='titulo'>{esc(s.get('titulo','Proximos passos'))}</h2>
          <ol class='passos'>{lis}</ol>
        </div>"""

    elif tipo == "encerramento":
        corpo = f"""
        <div class='slide encerramento'>
          <h1 class='enc-titulo'>{esc(s.get('titulo','Obrigado'))}</h1>
          <p class='enc-sub'>{esc(s.get('subtitulo',''))}</p>
          <div class='enc-contato'>{esc(s.get('contato',''))}</div>
        </div>"""

    else:  # conteudo (padrao)
        extra = f"<p class='lead'>{esc(s['texto'])}</p>" if s.get("texto") else ""
        corpo = f"""
        <div class='slide pad'>
          {eyebrow}<h2 class='titulo'>{esc(s.get('titulo','[PREENCHER]'))}</h2>
          {extra}{_lista(s.get('itens',[]))}
        </div>"""

    return f"""<section class='deck-slide' data-idx='{idx}'>
      <div class='canvas'>{corpo}
        <div class='chrome'><span class='cnt'>{idx+1} / {total}</span><span class='brand-foot'>__MARCA__</span></div>
      </div>
      {nota_html}
    </section>"""


def construir(deck):
    tema_nome = (deck.get("tema") or "executivo").lower()
    tema = TEMAS.get(tema_nome, TEMAS["executivo"])
    marca = deck.get("marca", {}) or {}
    nome_marca = marca.get("nome", "")
    cor = marca.get("cor") or tema["destaque"]
    logo_uri = embed_logo(marca.get("logo", ""))
    haslogo = bool(logo_uri)
    rodape = marca.get("rodape", "")

    slides = deck.get("slides", [])
    if not slides:
        slides = [{"tipo": "capa", "titulo": deck.get("titulo", "[PREENCHER]")}]

    secoes = []
    for i, s in enumerate(slides):
        if "rodape" not in s and s.get("tipo") == "capa" and rodape:
            s["rodape"] = rodape
        secoes.append(render_slide(s, i, len(slides)))
    body = "\n".join(secoes)

    # substituicoes de marca/logo nos placeholders
    body = body.replace("__MARCA__", esc(nome_marca))
    if haslogo:
        body = body.replace("__LOGO__", logo_uri)
        body = body.replace("class='capa-top'>", "class='capa-top has-logo'>")
    else:
        # remove img de logo da capa se nao houver logo
        body = body.replace("<img class='capa-logo' src='__LOGO__' alt=''>", "")
    # remove o marcador textual usado para decidir o logo na capa
    body = body.replace("__HASLOGO__", "")

    titulo_doc = esc(deck.get("titulo", "Apresentacao"))
    page_bg = tema["fundo"] if not tema["claro"] else "#EFE9DD"

    return TEMPLATE.format(
        titulo=titulo_doc, fonts_url=tema["fonts_url"],
        display=tema["display"], body_font=tema["body"],
        fundo=tema["fundo"], tinta=tema["tinta"], suave=tema["suave"],
        superficie=tema["superficie"], borda=tema["borda"], destaque=cor,
        page_bg=page_bg, slides=body,
        cartao_texto="#1B2330" if tema["claro"] else tema["tinta"],
    )


# ----------------------------------------------------------------------------
# Template HTML/CSS/JS (chaves de CSS escapadas como {{ }})
# ----------------------------------------------------------------------------
TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titulo}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{fonts_url}" rel="stylesheet">
<style>
  :root{{
    --fundo:{fundo}; --tinta:{tinta}; --suave:{suave}; --sup:{superficie};
    --borda:{borda}; --cor:{destaque}; --cartao-txt:{cartao_texto};
  }}
  *{{box-sizing:border-box;margin:0;padding:0}}
  html,body{{background:{page_bg};color:var(--tinta);
    font-family:"{body_font}",system-ui,sans-serif;-webkit-font-smoothing:antialiased}}
  .deck-slide{{display:none}}
  .deck-slide.ativo{{display:block}}
  .stage{{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:28px}}
  .canvas{{position:relative;width:min(96vw,1180px);aspect-ratio:16/9;background:var(--fundo);
    border:1px solid var(--borda);border-radius:18px;overflow:hidden;
    box-shadow:0 1px 0 rgba(255,255,255,.04),0 30px 70px -30px rgba(0,0,0,.55)}}
  .slide{{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center}}
  .slide.pad{{padding:7% 8%}}
  /* tipografia */
  .titulo{{font-family:"{display}",serif;font-weight:600;font-size:clamp(26px,3.6vw,44px);
    line-height:1.05;letter-spacing:-.02em;text-wrap:balance;margin-bottom:.7em;color:var(--tinta)}}
  .eyebrow{{font-size:12px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;
    color:var(--cor);margin-bottom:14px}}
  .lead{{font-size:clamp(15px,1.5vw,19px);line-height:1.6;color:var(--suave);max-width:62ch;margin-bottom:18px}}
  .lista{{list-style:none;display:flex;flex-direction:column;gap:14px;max-width:64ch}}
  .lista li{{position:relative;padding-left:30px;font-size:clamp(14px,1.45vw,18px);
    line-height:1.5;color:var(--tinta)}}
  .lista li::before{{content:"";position:absolute;left:4px;top:.62em;width:9px;height:9px;
    border-radius:3px;background:var(--cor)}}
  /* capa */
  .capa{{padding:8% 8%}}
  .capa-top{{display:flex;align-items:center;gap:14px;position:absolute;top:7%;left:8%}}
  .capa-logo{{height:38px;width:auto;object-fit:contain}}
  .capa-marca{{font-weight:600;letter-spacing:.02em;color:var(--suave);font-size:15px}}
  .capa-mid{{margin-top:6%}}
  .capa-titulo{{font-family:"{display}",serif;font-weight:700;font-size:clamp(34px,5.4vw,68px);
    line-height:1.02;letter-spacing:-.025em;text-wrap:balance;color:var(--tinta)}}
  .capa-sub{{margin-top:20px;font-size:clamp(16px,1.8vw,22px);color:var(--suave);max-width:60ch}}
  .capa-base{{position:absolute;bottom:7%;left:8%;color:var(--suave);font-size:13px;letter-spacing:.02em}}
  /* secao */
  .secao{{padding:0 9%}}
  .secao-num{{font-family:"{display}",serif;font-weight:700;font-size:clamp(60px,11vw,150px);
    line-height:1;color:var(--cor);opacity:.9}}
  .secao-titulo{{font-family:"{display}",serif;font-weight:600;font-size:clamp(28px,4.4vw,56px);
    letter-spacing:-.02em;margin-top:.1em;color:var(--tinta);text-wrap:balance}}
  .secao-sub{{margin-top:14px;color:var(--suave);font-size:clamp(15px,1.6vw,20px);max-width:58ch}}
  /* grid / cards */
  .grid{{display:grid;gap:20px;margin-top:6px}}
  .grid.cols-1{{grid-template-columns:1fr}}
  .grid.cols-2{{grid-template-columns:1fr 1fr}}
  .grid.cols-3{{grid-template-columns:repeat(3,1fr)}}
  .grid.cols-4{{grid-template-columns:repeat(4,1fr)}}
  .card{{background:var(--sup);border:1px solid var(--borda);border-radius:14px;padding:26px 24px;
    box-shadow:0 18px 40px -28px rgba(0,0,0,.6)}}
  .card h3{{font-family:"{display}",serif;font-weight:600;font-size:clamp(17px,1.8vw,22px);
    margin-bottom:14px;color:var(--tinta)}}
  .card .lista li{{font-size:clamp(13px,1.3vw,16px)}}
  .card-depois{{border-color:color-mix(in srgb,var(--cor) 55%,var(--borda))}}
  .card-depois h3{{color:var(--cor)}}
  .card-antes{{opacity:.92}}
  /* numero */
  .numero{{align-items:center;text-align:center;padding:0 8%}}
  .big-num{{font-family:"{display}",serif;font-weight:700;font-size:clamp(80px,15vw,200px);
    line-height:.9;letter-spacing:-.03em;color:var(--cor)}}
  .num-titulo{{font-family:"{display}",serif;font-weight:600;font-size:clamp(22px,3vw,38px);
    margin-top:.2em;color:var(--tinta);text-wrap:balance}}
  .num-legenda{{margin-top:12px;color:var(--suave);font-size:clamp(14px,1.5vw,19px);max-width:54ch}}
  /* citacao */
  .citacao{{align-items:flex-start;padding:0 10%}}
  .citacao blockquote{{font-family:"{display}",serif;font-weight:500;font-size:clamp(24px,3.6vw,46px);
    line-height:1.25;letter-spacing:-.01em;color:var(--tinta);text-wrap:balance}}
  .citacao blockquote::before{{content:"\201C";color:var(--cor)}}
  .citacao blockquote::after{{content:"\201D";color:var(--cor)}}
  .cit-autor{{margin-top:22px;color:var(--cor);font-weight:600;font-size:15px;letter-spacing:.02em}}
  /* tabela */
  .tabela{{width:100%;border-collapse:collapse;margin-top:8px;font-size:clamp(13px,1.35vw,17px)}}
  .tabela th{{text-align:left;color:var(--cor);font-weight:600;padding:12px 14px;
    border-bottom:2px solid color-mix(in srgb,var(--cor) 40%,var(--borda))}}
  .tabela td{{padding:12px 14px;border-bottom:1px solid var(--borda);color:var(--tinta)}}
  /* agenda / passos */
  .agenda,.passos{{list-style:none;display:flex;flex-direction:column;gap:16px;margin-top:8px;max-width:70ch}}
  .agenda li,.passos li{{display:flex;align-items:baseline;gap:18px;font-size:clamp(15px,1.6vw,21px);
    color:var(--tinta);padding-bottom:14px;border-bottom:1px solid var(--borda)}}
  .ag-num{{font-family:"{display}",serif;font-weight:700;color:var(--cor);font-size:.9em;min-width:38px}}
  .passo-num{{display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;
    flex:0 0 34px;border-radius:50%;background:var(--cor);color:#fff;font-weight:700;font-size:15px}}
  /* encerramento */
  .encerramento{{align-items:center;text-align:center;padding:0 8%}}
  .enc-titulo{{font-family:"{display}",serif;font-weight:700;font-size:clamp(40px,7vw,84px);
    letter-spacing:-.025em;color:var(--tinta)}}
  .enc-sub{{margin-top:16px;color:var(--suave);font-size:clamp(16px,1.9vw,24px)}}
  .enc-contato{{margin-top:26px;color:var(--cor);font-weight:600;font-size:clamp(14px,1.5vw,18px)}}
  /* chrome (rodape do slide) */
  .chrome{{position:absolute;left:0;right:0;bottom:0;display:flex;justify-content:space-between;
    align-items:center;padding:14px 26px;font-size:11px;color:var(--suave);letter-spacing:.04em}}
  .brand-foot{{opacity:.8}}
  /* barra de progresso + ajuda */
  .progress{{position:fixed;top:0;left:0;height:3px;background:var(--cor);width:0;z-index:50;transition:width .25s}}
  .ajuda{{position:fixed;bottom:14px;left:50%;transform:translateX(-50%);z-index:50;
    font-size:11px;color:var(--suave);background:rgba(0,0,0,.32);border:1px solid var(--borda);
    padding:6px 14px;border-radius:999px;backdrop-filter:blur(6px)}}
  .notas{{display:none}}
  body.modo-notas .ajuda{{background:var(--cor);color:#fff}}
  body.modo-notas .deck-slide.ativo .notas{{display:block;position:fixed;left:50%;bottom:54px;
    transform:translateX(-50%);max-width:min(92vw,1180px);width:100%;background:#0b0b0bEE;color:#fff;
    border:1px solid var(--borda);border-radius:12px;padding:16px 20px;font-size:14px;line-height:1.5;z-index:60}}
  .notas::before{{content:"🎤 Notas do apresentador";display:block;font-size:11px;letter-spacing:.1em;
    text-transform:uppercase;color:var(--cor);margin-bottom:6px}}

  /* ---------- IMPRESSAO / PDF: 1 slide por pagina A4 paisagem ---------- */
  @media print{{
    @page{{size:A4 landscape;margin:0}}
    html,body{{background:#fff}}
    .progress,.ajuda{{display:none!important}}
    .stage{{display:block!important;min-height:auto;padding:0}}
    .deck-slide{{display:block!important;page-break-after:always;break-after:page;break-inside:avoid}}
    .deck-slide:last-child{{page-break-after:auto}}
    .canvas{{width:100%;height:100vh;aspect-ratio:auto;border:0;border-radius:0;box-shadow:none;page-break-inside:avoid}}
    .notas{{display:none!important}}
  }}
</style>
</head>
<body>
<div class="progress" id="progress"></div>
<main class="stage" id="stage">
{slides}
</main>
<div class="ajuda" id="ajuda">← →  navegar  ·  <b>N</b> notas do apresentador  ·  <b>P</b> imprimir/PDF  ·  F11 tela cheia</div>
<script>
  var slides=[].slice.call(document.querySelectorAll('.deck-slide'));
  var i=0;
  function mostra(n){{
    i=Math.max(0,Math.min(slides.length-1,n));
    slides.forEach(function(s,k){{s.classList.toggle('ativo',k===i);}});
    document.getElementById('progress').style.width=((i+1)/slides.length*100)+'%';
    location.hash=(i+1);
  }}
  function prox(){{mostra(i+1);}}
  function ant(){{mostra(i-1);}}
  document.addEventListener('keydown',function(e){{
    if(['ArrowRight','ArrowDown','PageDown',' '].indexOf(e.key)>=0){{e.preventDefault();prox();}}
    else if(['ArrowLeft','ArrowUp','PageUp'].indexOf(e.key)>=0){{e.preventDefault();ant();}}
    else if(e.key==='Home'){{mostra(0);}}
    else if(e.key==='End'){{mostra(slides.length-1);}}
    else if(e.key==='n'||e.key==='N'){{document.body.classList.toggle('modo-notas');}}
    else if(e.key==='p'||e.key==='P'){{window.print();}}
  }});
  document.getElementById('stage').addEventListener('click',function(e){{
    if(e.clientX > window.innerWidth/2){{prox();}} else {{ant();}}
  }});
  var h=parseInt((location.hash||'').replace('#',''));
  mostra(isNaN(h)?0:h-1);
</script>
</body>
</html>"""


def main():
    if len(sys.argv) < 3:
        print("uso: python3 palco.py deck.json apresentacao.html", file=sys.stderr)
        sys.exit(1)
    entrada, saida = sys.argv[1], sys.argv[2]
    with open(entrada, "r", encoding="utf-8") as f:
        deck = json.load(f)
    html_out = construir(deck)
    with open(saida, "w", encoding="utf-8") as f:
        f.write(html_out)
    n = len(deck.get("slides", []) or [1])
    print(f"OK: {saida} gerado com {n} slide(s). Abra no navegador; tecla P (ou Ctrl/Cmd+P) salva em PDF.")


if __name__ == "__main__":
    main()
