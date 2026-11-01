"""Testes das regras estatísticas e da limpeza do ETL."""

import unittest
from unittest.mock import patch

import pandas as pd

from scripts import atualizar_dados_infosiga as etl
from src import metricas


def _registros(**colunas):
    base = {"mortos": [0], "feridos_graves": [0], "feridos_leves": [0], "ilesos": [0]}
    return pd.DataFrame({**base, **colunas})


class TestMetricas(unittest.TestCase):
    def test_sem_dados_de_vitima_nao_vira_sem_vitimas(self):
        self.assertEqual(metricas.classificar_gravidade(_registros())[0], metricas.SEM_INFORMACAO)
        self.assertEqual(metricas.classificar_gravidade(_registros(ilesos=[2]))[0], metricas.SEM_FERIDOS)
        self.assertEqual(metricas.classificar_gravidade(_registros(mortos=[1], ilesos=[2]))[0], "Com óbito")

    def test_base_comparavel_exclui_anos_antigos_e_notificacoes(self):
        df = pd.DataFrame({
            "ano": [2018, 2019, 2019],
            "tipo_registro": ["SINISTRO FATAL", "NOTIFICACAO", "SINISTRO NAO FATAL"],
        })
        self.assertEqual(metricas.base_comparavel(df).index.tolist(), [2])

    def test_serie_diaria_inclui_dias_sem_registro(self):
        df = pd.DataFrame({"data": ["2024-01-01", "2024-01-01", "2024-01-03"]})
        self.assertEqual(metricas.serie_diaria(df).tolist(), [2, 0, 1])

    def test_comparar_dias_usa_o_calendario_completo(self):
        # Segunda 01/01/2024 com 7 registros e domingo 07/01 com 1; demais dias vazios.
        df = pd.DataFrame({"data": ["2024-01-01"] * 7 + ["2024-01-07"]})
        resultado = metricas.comparar_dias(df)
        self.assertAlmostEqual(resultado["media_uteis"], 7 / 5)
        self.assertAlmostEqual(resultado["media_fds"], 1 / 2)
        self.assertAlmostEqual(resultado["dias_sem_registro_pct"], 5 / 7 * 100)

    def test_formato_brasileiro(self):
        self.assertEqual(metricas.br(1234.5, 2), "1.234,50")
        self.assertEqual(metricas.br(1360), "1.360")

    def test_formatar_tabela_preserva_numeros_e_codigos(self):
        df = pd.DataFrame({"ano": [2026], "total": [1360], "taxa": [15.22], "hora": [float("nan")], "data": pd.to_datetime(["2026-09-29"])})
        estilo = metricas.formatar_tabela(df, sem_milhar=["ano"])
        html = estilo.to_html()
        for esperado in [">2026<", ">1.360<", ">15,22<", ">29/09/2026<"]:
            self.assertIn(esperado, html)
        self.assertEqual(estilo.data["total"].iloc[0], 1360)

    def test_letalidade_separa_sinistros_e_pessoas(self):
        df = pd.DataFrame({
            "id_sinistro": [1, 2, 3, 4],
            "tipo_sinistro": ["CHOQUE"] * 4,
            "mortos": [2, 0, 0, 0],
            "feridos_graves": [0, 1, 1, 0],
        })
        linha = metricas.tabela_letalidade(df).iloc[0]
        self.assertEqual((linha.sinistros_fatais, linha.mortos, linha.letalidade_pct), (1, 2, 25.0))


def _bruto(**extras):
    linha = {coluna: [1] for coluna in etl.MAPA_COLUNAS}
    linha.update({
        "cod_ibge": [etl.CODIGO_IBGE_MATAO], "data_sinistro": ["05/01/2026"], "hora_sinistro": ["17:30"],
        "dia_da_semana": ["Segunda-feira"], "latitude": ["-21,6"], "longitude": ["-48,3"],
    })
    linha.update(extras)
    return pd.DataFrame(linha)


class TestEtl(unittest.TestCase):
    def test_coluna_ausente_interrompe_em_vez_de_zerar(self):
        with self.assertRaises(ValueError):
            etl.processar_e_limpar_chunk_matao(_bruto().drop(columns="qtd_gravidade_fatal"))

    def test_cod_ibge_texto_e_aceito(self):
        self.assertEqual(len(etl.processar_e_limpar_chunk_matao(_bruto(cod_ibge=["3529302"]))), 1)

    def test_fallback_de_municipio_aceita_grafia_sem_acento(self):
        bruto = _bruto(municipio=["MATAO"]).drop(columns="cod_ibge")
        self.assertEqual(len(etl.processar_e_limpar_chunk_matao(bruto)), 1)

    def test_periodo_usa_nome_quando_url_nao_tem_data(self):
        recurso = {"url": "https://exemplo/arquivo.csv", "name": "Agosto de 2026"}
        self.assertEqual(etl.periodo_do_recurso(recurso), (2026, 8))

    def test_janela_de_revisao_reprocessa_meses_recentes(self):
        self.assertTrue(etl.mes_na_janela(2026, 7, 2026, 9))
        self.assertTrue(etl.mes_na_janela(2025, 12, 2026, 2))
        self.assertFalse(etl.mes_na_janela(2026, 6, 2026, 9))

    def test_falha_de_download_nao_altera_a_base(self):
        recursos = [{"format": "CSV", "url": "https://x/sinistros_09-2026.csv", "name": ""}]
        with patch.object(etl, "obter_recursos_ckan", return_value=recursos), \
                patch.object(etl, "obter_periodo_atual_matao", return_value=(2026, 9)), \
                patch.object(etl, "baixar_arquivo", return_value=False), \
                patch.object(etl.os.path, "exists", return_value=False), \
                patch.object(etl.pd.DataFrame, "to_csv") as salvar:
            self.assertFalse(etl.executar_pipeline())
        salvar.assert_not_called()


if __name__ == "__main__":
    unittest.main()
