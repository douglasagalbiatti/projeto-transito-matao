"""Indicadores calculados da base, usados nos documentos gerados automaticamente."""

import pandas as pd
from scipy import stats

from src.metricas import (
    ANO_INICIO_COMPARAVEL,
    SEM_FERIDOS,
    SEM_INFORMACAO,
    base_comparavel,
    comparar_dias,
    razao_letalidade,
    tabela_letalidade,
)
from src.modelo import treinar_modelo

DIAS_SEMANA = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
ROTULOS_TIPO = {
    "ATROPELAMENTO": "Atropelamento",
    "CHOQUE": "Choque",
    "COLISAO": "Colisão",
    "OUTROS": "Outros",
    "NAO DISPONIVEL": "Não disponível",
}
URBANA, RODOVIA = "VIAS URBANAS", "ESTRADAS E RODOVIAS"
# Diferença, em pontos percentuais, abaixo da qual duas letalidades são descritas como próximas
LIMITE_TAXAS_PROXIMAS = 5
ROTULOS_VARIAVEIS = {
    "qtd_motocicleta": "motocicletas",
    "qtd_automovel": "automóveis",
    "qtd_caminhao": "caminhões",
    "qtd_pedestre": "pedestres",
    "qtd_bicicleta": "bicicletas",
    "hora_int": "hora",
    "mes": "mês",
}


def _taxa(df: pd.DataFrame) -> dict:
    fatais = int((df["mortos"] > 0).sum())
    return {"fatais": fatais, "n": len(df), "pct": fatais / len(df) * 100 if len(df) else 0.0}


def _grave_ou_fatal_pct(df: pd.DataFrame) -> float:
    return ((df["mortos"] > 0) | (df["feridos_graves"] > 0)).mean() * 100 if len(df) else 0.0


def calcular_indicadores(df: pd.DataFrame) -> dict:
    """Calcula todos os números e condições que sustentam os textos dos documentos."""
    df = df.copy()
    df["data"] = pd.to_datetime(df["data"])
    notificacao = df["tipo_registro"] == "NOTIFICACAO"
    comparavel = base_comparavel(df)
    recente = df[df["ano"] >= ANO_INICIO_COMPARAVEL]
    sem_notificacao = df[~notificacao]
    fim = df["data"].max()
    ultimo_mes_completo = (fim + pd.Timedelta(days=1)).month != fim.month
    ind = {
        "data_inicio": df["data"].min().strftime("%d/%m/%Y"),
        "data_fim": fim.strftime("%d/%m/%Y"),
        "mes_fim": fim.strftime("%m/%Y"),
        "ano_inicio": int(df["ano"].min()),
        "ano_fim": int(df["ano"].max()),
        "anos_de_dados": int((fim - df["data"].min()).days / 365.25),
        "ultimo_mes_completo": ultimo_mes_completo,
        "total": len(df),
        "notificacoes": int(notificacao.sum()),
        "mortos": int(df["mortos"].sum()),
        "feridos_graves": int(df["feridos_graves"].sum()),
    }

    # Desfechos
    contagem = df["gravidade"].value_counts()
    ind["desfechos"] = {
        chave: {"n": int(contagem.get(rotulo, 0)), "pct": contagem.get(rotulo, 0) / len(df) * 100}
        for chave, rotulo in {
            "sem_informacao": SEM_INFORMACAO,
            "leves": "Com feridos leves",
            "graves": "Com feridos graves",
            "obito": "Com óbito",
            "sem_feridos": SEM_FERIDOS,
        }.items()
    }

    # Série anual; o ano em andamento fica fora dos extremos de sinistros fatais
    por_ano = df.groupby("ano").agg(
        registros=("id_sinistro", "count"),
        notificacoes=("tipo_registro", lambda s: int((s == "NOTIFICACAO").sum())),
        fatais=("mortos", lambda s: int((s > 0).sum())),
        mortos=("mortos", "sum"),
    )
    por_ano["pct_notificacoes"] = por_ano["notificacoes"] / por_ano["registros"] * 100
    desde_inicio = por_ano[por_ano.index >= ANO_INICIO_COMPARAVEL]
    ind.update({
        "notificacoes_pct_min": desde_inicio["pct_notificacoes"].min(),
        "notificacoes_pct_max": desde_inicio["pct_notificacoes"].max(),
        "fatais_ano_min": int(por_ano["fatais"].min()),
        "fatais_ano_max": int(por_ano["fatais"].max()),
        "mortos_ano_min": int(por_ano["mortos"].min()),
        "mortos_ano_max": int(por_ano["mortos"].max()),
        "sinistros_primeiro_ano_comparavel": int(
            por_ano.loc[ANO_INICIO_COMPARAVEL, "registros"] - por_ano.loc[ANO_INICIO_COMPARAVEL, "notificacoes"]
        ),
    })

    # Letalidade por tipo, na base comparável
    letalidade = tabela_letalidade(comparavel)
    ind["letalidade"] = [
        {**linha, "rotulo": ROTULOS_TIPO.get(linha["tipo_sinistro"], linha["tipo_sinistro"])}
        for linha in letalidade.to_dict("records")
    ]
    ind["razao_choque_colisao"], ind["razao_ic_inf"], ind["razao_ic_sup"] = razao_letalidade(comparavel, "CHOQUE", "COLISAO")

    tipos = comparavel["tipo_sinistro"]
    ind["choque"] = _taxa(comparavel[tipos == "CHOQUE"])
    ind["colisao"] = _taxa(comparavel[tipos == "COLISAO"])
    ind["atropelamento"] = _taxa(comparavel[tipos == "ATROPELAMENTO"])
    ind["choque_urbano"] = _taxa(comparavel[(tipos == "CHOQUE") & (comparavel["tipo_via"] == URBANA)])
    ind["colisao_urbana"] = _taxa(comparavel[(tipos == "COLISAO") & (comparavel["tipo_via"] == URBANA)])
    ind["choque_rodovia"] = _taxa(comparavel[(tipos == "CHOQUE") & (comparavel["tipo_via"] == RODOVIA)])
    ind["colisao_rodovia"] = _taxa(comparavel[(tipos == "COLISAO") & (comparavel["tipo_via"] == RODOVIA)])
    ind["rodovia_taxas_proximas"] = abs(ind["choque_rodovia"]["pct"] - ind["colisao_rodovia"]["pct"]) < LIMITE_TAXAS_PROXIMAS
    ind["urbano_choque_maior"] = ind["choque_urbano"]["pct"] > ind["colisao_urbana"]["pct"] + LIMITE_TAXAS_PROXIMAS
    a, c = ind["atropelamento"], ind["choque"]
    ind["atropelamento_choque_p"] = stats.fisher_exact(
        [[a["fatais"], a["n"] - a["fatais"]], [c["fatais"], c["n"] - c["fatais"]]]
    )[1]

    # Modais, entre registros com veículo ou pedestre informado
    com_modal = df[(df["total_veiculos"] > 0) | (df["qtd_pedestre"] > 0)]
    ind["registros_com_modal"] = len(com_modal)
    ind["modais"] = {
        nome: (com_modal[coluna] > 0).mean() * 100
        for nome, coluna in {
            "automovel": "qtd_automovel", "moto": "qtd_motocicleta", "caminhao": "qtd_caminhao",
            "pedestre": "qtd_pedestre", "bicicleta": "qtd_bicicleta", "onibus": "qtd_onibus",
        }.items()
    }
    atropelamentos = df[df["tipo_sinistro"] == "ATROPELAMENTO"]
    ind["atropelamentos_total"] = len(atropelamentos)
    ind["atropelamentos_sem_pedestre"] = int((atropelamentos["qtd_pedestre"] == 0).sum())

    moto = comparavel["qtd_motocicleta"] > 0
    urbana, rodovia = comparavel["tipo_via"] == URBANA, comparavel["tipo_via"] == RODOVIA
    ind["moto_urbana_pct"] = _grave_ou_fatal_pct(comparavel[moto & urbana])
    ind["sem_moto_urbana_pct"] = _grave_ou_fatal_pct(comparavel[~moto & urbana])
    ind["moto_rodovia_pct"] = _grave_ou_fatal_pct(comparavel[moto & rodovia])
    ind["sem_moto_rodovia_pct"] = _grave_ou_fatal_pct(comparavel[~moto & rodovia])

    # Horas
    horas = df["hora_int"].dropna().astype(int).value_counts().head(4)
    top3 = [int(h) for h in horas.index[:3]]
    ind["horas"] = [{"hora": int(h), "n": int(n)} for h, n in horas.items()]
    ind["horas_top3_texto"] = ", ".join(f"{h}h" for h in top3[:2]) + f" e {top3[2]}h"
    ind["horas_top3_pct_registros"] = df["hora_int"].isin(top3).mean() * 100
    ind["horas_top3_pct_fatais"] = df[df["mortos"] > 0]["hora_int"].isin(top3).mean() * 100

    # Dias
    teste = comparar_dias(recente)
    media_dia = teste["media_por_dia"]
    maiores = media_dia.nlargest(2).sort_index()
    demais = media_dia.drop(maiores.index)
    ind["teste"] = {k: teste[k] for k in ["media_uteis", "media_fds", "diferenca", "ic95", "p_welch", "dias_sem_registro_pct"]}
    ind["teste"]["significativo"] = teste["p_welch"] < 0.05
    ind["dias_destaque"] = [{"nome": DIAS_SEMANA[d], "media": v} for d, v in maiores.items()]
    ind["dias_demais_min"], ind["dias_demais_max"] = demais.min(), demais.max()
    madrugada = recente["hora_int"].isin([22, 23, 0, 1, 2, 3, 4, 5])
    ind["noite_fds_pct"] = madrugada[recente["fim_de_semana"]].mean() * 100
    ind["noite_uteis_pct"] = madrugada[~recente["fim_de_semana"]].mean() * 100

    # Geografia
    for chave, via in [("urbana", URBANA), ("rodovia", RODOVIA)]:
        trecho = df[df["tipo_via"] == via]
        ind[f"via_{chave}"] = {
            "registros": len(trecho),
            "mortos": int(trecho["mortos"].sum()),
            "mortos_pct": trecho["mortos"].sum() / df["mortos"].sum() * 100,
            "letalidade": (trecho["mortos"] > 0).mean() * 100,
        }
    ind["mortos_sem_via"] = int(df[~df["tipo_via"].isin([URBANA, RODOVIA])]["mortos"].sum())
    ind["mortos_sp310_sp326"] = int(df[df["logradouro"].isin(["SP 310", "SP 326"])]["mortos"].sum())
    ind["urbana_tem_mais_obitos"] = ind["via_urbana"]["mortos"] > ind["via_rodovia"]["mortos"]
    ranking = sem_notificacao["logradouro"].value_counts().head(4)
    ind["ranking_vias"] = [{"via": via, "n": int(n)} for via, n in ranking.items()]
    via_topo = df["logradouro"].value_counts().index[0]
    topo = df[df["logradouro"] == via_topo]
    ind["via_topo_com_notificacoes"] = {
        "via": via_topo,
        "n": len(topo),
        "pct_notificacoes": (topo["tipo_registro"] == "NOTIFICACAO").mean() * 100,
    }
    ind["via_topo_muda"] = via_topo != ranking.index[0]

    # Coordenadas e possíveis duplicidades
    na_regiao = df["latitude"].between(-21.80, -21.40) & df["longitude"].between(-48.60, -48.10)
    repetidas = df.groupby(["latitude", "longitude"]).size()
    repetidas = repetidas[repetidas >= 10]
    ind["com_coordenadas"] = int(df["latitude"].notna().sum())
    ind["coordenadas_na_regiao"] = int(na_regiao.sum())
    ind["pontos_no_mapa"] = int((na_regiao & ~notificacao).sum())
    ind["coordenadas_repetidas_registros"] = int(repetidas.sum())
    ind["coordenadas_repetidas_pontos"] = len(repetidas)
    chave_duplicada = ["data", "hora", "logradouro"]
    com_hora = df[df["hora"].notna()]
    ind["grupos_mesma_data_hora_via"] = int(
        com_hora[com_hora.duplicated(chave_duplicada, keep=False)].groupby(chave_duplicada).ngroups
    )

    # Modelo
    modelo = treinar_modelo(df)
    principais = modelo["importancias"].sort_values(ascending=False).head(3)
    ind["modelo"] = {
        "acuracia": modelo["acuracia"] * 100,
        "referencia": modelo["referencia"] * 100,
        "balanceada": modelo["acuracia_balanceada"] * 100,
        "supera_referencia": modelo["acuracia"] > modelo["referencia"],
        "principais": [
            {"variavel": ROTULOS_VARIAVEIS.get(v, v.replace("tipo_via_", "via: ").replace("tipo_sinistro_", "tipo: ")), "valor": i}
            for v, i in principais.items()
        ],
    }
    return ind
