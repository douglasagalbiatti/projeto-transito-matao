"""Regras estatísticas compartilhadas por ETL, notebooks e dashboard."""

import os

import numpy as np
import pandas as pd

ANO_INICIO_COMPARAVEL = 2019
URL_ARTEFATOS = "https://raw.githubusercontent.com/douglasagalbiatti/projeto-transito-matao/artefatos"
SEM_FERIDOS = "Sem feridos (ilesos registrados)"
SEM_INFORMACAO = "Sem informação de vítimas"
ORDEM_GRAVIDADE = [
    "Com óbito",
    "Com feridos graves",
    "Com feridos leves",
    SEM_FERIDOS,
    SEM_INFORMACAO,
]


def caminho_grafico(nome: str) -> str:
    """Usa o gráfico gerado localmente ou, se não houver, o publicado na branch 'artefatos'."""
    caminho = f"output/graficos/{nome}"
    return caminho if os.path.exists(caminho) else f"{URL_ARTEFATOS}/{caminho}"


def br(valor, casas: int = 0) -> str:
    """Formata um número com vírgula decimal e ponto de milhar."""
    return f"{valor:,.{casas}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def formatar_tabela(df: pd.DataFrame, casas: dict = None, sem_milhar: list = ()):
    """Aplica o padrão brasileiro à exibição, mantendo os valores numéricos para ordenação."""
    casas = casas or {}
    formatos = {}
    for coluna in df.select_dtypes("number").columns:
        decimais = casas.get(coluna, 2 if pd.api.types.is_float_dtype(df[coluna]) else 0)
        if coluna in sem_milhar:
            formatos[coluna] = lambda v, d=decimais: "" if pd.isna(v) else br(v, d).replace(".", "")
        else:
            formatos[coluna] = lambda v, d=decimais: "" if pd.isna(v) else br(v, d)
    for coluna in df.select_dtypes("datetime").columns:
        formatos[coluna] = lambda v: "" if pd.isna(v) else v.strftime("%d/%m/%Y")
    return df.style.format(formatos)


def classificar_gravidade(df: pd.DataFrame) -> pd.Series:
    """Classifica o desfecho sem tratar ausência de informação como ausência de vítimas."""
    condicoes = [
        df["mortos"] > 0,
        df["feridos_graves"] > 0,
        df["feridos_leves"] > 0,
        df["ilesos"] > 0,
    ]
    return pd.Series(
        np.select(condicoes, ORDEM_GRAVIDADE[:4], default=SEM_INFORMACAO),
        index=df.index,
        name="gravidade",
    )


def base_comparavel(df: pd.DataFrame) -> pd.DataFrame:
    """Sinistros de 2019 em diante, sem notificações, cuja cobertura varia por ano."""
    return df[(df["ano"] >= ANO_INICIO_COMPARAVEL) & (df["tipo_registro"] != "NOTIFICACAO")]


def serie_diaria(df: pd.DataFrame) -> pd.Series:
    """Registros por dia corrido, incluindo os dias sem nenhum registro."""
    datas = pd.to_datetime(df["data"])
    calendario = pd.date_range(datas.min(), datas.max())
    return datas.value_counts().reindex(calendario, fill_value=0).sort_index()


def comparar_dias(df: pd.DataFrame) -> dict:
    """Compara dias úteis e fins de semana por teste de Welch, com intervalo de 95%."""
    from scipy import stats

    serie = serie_diaria(df)
    dia_semana = serie.index.day_of_week
    uteis, fds = serie[dia_semana < 5], serie[dia_semana >= 5]
    diferenca = fds.mean() - uteis.mean()
    erro = np.sqrt(uteis.var() / len(uteis) + fds.var() / len(fds))
    return {
        "media_uteis": uteis.mean(),
        "media_fds": fds.mean(),
        "diferenca": diferenca,
        "ic95": (diferenca - 1.96 * erro, diferenca + 1.96 * erro),
        "p_welch": stats.ttest_ind(uteis, fds, equal_var=False).pvalue,
        "dias_sem_registro_pct": (serie == 0).mean() * 100,
        "media_por_dia": serie.groupby(dia_semana).mean(),
    }


def tabela_letalidade(df: pd.DataFrame, por: str = "tipo_sinistro") -> pd.DataFrame:
    """Letalidade = sinistros com óbito ÷ sinistros, com contagens de pessoas à parte."""
    tabela = df.groupby(por).agg(
        sinistros=("id_sinistro", "count"),
        sinistros_fatais=("mortos", lambda s: int((s > 0).sum())),
        mortos=("mortos", "sum"),
        feridos_graves=("feridos_graves", "sum"),
    )
    tabela["letalidade_pct"] = (tabela["sinistros_fatais"] / tabela["sinistros"] * 100).round(2)
    return tabela.sort_values("letalidade_pct", ascending=False).reset_index()


def razao_letalidade(df: pd.DataFrame, tipo_a: str, tipo_b: str) -> tuple:
    """Razão de letalidade de tipo_a sobre tipo_b e seu intervalo de 95% (log-normal)."""
    fatais = df["mortos"] > 0
    a, b = df["tipo_sinistro"] == tipo_a, df["tipo_sinistro"] == tipo_b
    fa, na, fb, nb = (fatais & a).sum(), a.sum(), (fatais & b).sum(), b.sum()
    razao = (fa / na) / (fb / nb)
    erro = np.sqrt(1 / fa - 1 / na + 1 / fb - 1 / nb)
    return razao, razao * np.exp(-1.96 * erro), razao * np.exp(1.96 * erro)
