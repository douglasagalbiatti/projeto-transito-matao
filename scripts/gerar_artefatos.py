"""
Gera novamente gráficos e documentos a partir de 'data/matao_limpo.csv'.

Notebooks 03 e 04: gráficos estáticos e mapas.
Modelos em 'templates/': README, relatório, apresentação e resumo em PDF.

Gráficos, mapas, PDF e notebooks executados não são versionados na main:
'scripts/publicar_artefatos.sh' os publica na branch 'artefatos'.
"""

import argparse
import logging
import os
import sys
import time

import pandas as pd
from jinja2 import Environment, FileSystemLoader, StrictUndefined

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, RAIZ)
from src.indicadores import calcular_indicadores
from src.metricas import URL_ARTEFATOS, br

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ARTEFATOS")

NOTEBOOKS = ["03-analise-matao.ipynb", "04-visualizacoes.ipynb"]
DOCUMENTOS = {
    "README.md.j2": "README.md",
    "relatorio_final_matao.md.j2": os.path.join("output", "relatorios", "relatorio_final_matao.md"),
    "apresentacao_matao.html.j2": "apresentacao_matao.html",
}
PASTAS_GERADAS = [os.path.join("output", "graficos"), os.path.join("output", "notebooks")]
CAMINHO_PDF = os.path.join("output", "relatorios", "relatorio_ciencia_de_dados_matao.pdf")


def executar_notebooks():
    """Reexecuta os notebooks que produzem gráficos e mapas."""
    import nbformat
    from nbconvert.preprocessors import ExecutePreprocessor

    pasta = os.path.join(RAIZ, "notebooks")
    destino = os.path.join(RAIZ, "output", "notebooks")
    os.makedirs(destino, exist_ok=True)
    for nome in NOTEBOOKS:
        logger.info(f"Executando {nome}...")
        caminho = os.path.join(pasta, nome)
        notebook = nbformat.read(caminho, as_version=4)
        ExecutePreprocessor(timeout=600, kernel_name="python3").preprocess(notebook, {"metadata": {"path": pasta}})
        nbformat.write(notebook, os.path.join(destino, nome))


def remover_antigos(inicio: float):
    """Apaga os arquivos gerados que esta execução não produziu de novo."""
    for pasta in PASTAS_GERADAS:
        for nome in os.listdir(os.path.join(RAIZ, pasta)):
            caminho = os.path.join(RAIZ, pasta, nome)
            if os.path.getmtime(caminho) < inicio:
                os.remove(caminho)
                logger.info(f"Removido por estar desatualizado: {nome}")


def renderizar_documentos(indicadores: dict, raiz: str = RAIZ) -> dict:
    """Preenche os modelos com os indicadores e grava os documentos."""
    ambiente = Environment(
        loader=FileSystemLoader(os.path.join(RAIZ, "templates")),
        undefined=StrictUndefined,
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    ambiente.filters["br"] = br
    gerados = {}
    for modelo, destino in DOCUMENTOS.items():
        conteudo = ambiente.get_template(modelo).render(i=indicadores, url=URL_ARTEFATOS)
        caminho = os.path.join(raiz, destino)
        with open(caminho, "w", encoding="utf-8") as arquivo:
            arquivo.write(conteudo)
        gerados[destino] = conteudo
    gerados["resumo_html"] = ambiente.get_template("resumo_pdf.html.j2").render(i=indicadores, base_path=RAIZ)
    return gerados


def gerar_pdf(html: str):
    """Converte o resumo em PDF, com os gráficos gerados pelos notebooks."""
    import weasyprint

    weasyprint.HTML(string=html).write_pdf(os.path.join(RAIZ, CAMINHO_PDF))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sem-notebooks", action="store_true", help="Não reexecuta os notebooks.")
    args = parser.parse_args()

    inicio = time.time()
    if not args.sem_notebooks:
        executar_notebooks()

    df = pd.read_csv(os.path.join(RAIZ, "data", "matao_limpo.csv"))
    indicadores = calcular_indicadores(df)
    documentos = renderizar_documentos(indicadores)
    gerar_pdf(documentos["resumo_html"])
    if not args.sem_notebooks:
        remover_antigos(inicio)
    logger.info(f"Artefatos atualizados com dados até {indicadores['data_fim']}.")


if __name__ == "__main__":
    main()
