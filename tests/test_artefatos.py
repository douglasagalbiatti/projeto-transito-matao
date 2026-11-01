"""Testes dos indicadores e dos documentos gerados a partir deles."""

import os
import tempfile
import unittest

import pandas as pd

from scripts import gerar_artefatos
from src.indicadores import calcular_indicadores
from src.metricas import br

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _base():
    return pd.read_csv(os.path.join(RAIZ, "data", "matao_limpo.csv"))


def _com_novo_mes(df):
    novos = df[df["ano"] == df["ano"].max()].tail(30).copy()
    novos["id_sinistro"] = [f"novo-{n}" for n in range(len(novos))]
    novos["data"] = "2031-01-15"
    novos["ano"] = 2031
    novos["mes"] = 1
    return pd.concat([df, novos], ignore_index=True)


class TestArtefatos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.df = _base()
        cls.indicadores = calcular_indicadores(cls.df)

    def _renderizar(self, indicadores):
        with tempfile.TemporaryDirectory() as pasta:
            os.makedirs(os.path.join(pasta, "output", "relatorios"))
            return gerar_artefatos.renderizar_documentos(indicadores, raiz=pasta)

    def test_totais_conferem_com_a_base(self):
        i = self.indicadores
        self.assertEqual(i["total"], len(self.df))
        self.assertEqual(i["mortos"], self.df["mortos"].sum())
        self.assertEqual(sum(d["n"] for d in i["desfechos"].values()), len(self.df))

    def test_novo_mes_muda_todos_os_documentos(self):
        novo = calcular_indicadores(_com_novo_mes(self.df))
        self.assertEqual(novo["total"], self.indicadores["total"] + 30)
        self.assertEqual(novo["data_fim"], "15/01/2031")
        documentos = self._renderizar(novo)
        for destino, conteudo in documentos.items():
            self.assertIn(br(novo["total"]), conteudo, destino)
            self.assertNotIn(f">{br(self.indicadores['total'])}<", conteudo, destino)

    def test_documentos_nao_deixam_marcadores_do_modelo(self):
        for destino, conteudo in self._renderizar(self.indicadores).items():
            self.assertNotIn("{{", conteudo, destino)
            self.assertNotIn("{%", conteudo, destino)

    def test_conclusao_acompanha_o_teste_estatistico(self):
        for significativo, trecho in [(True, "O intervalo exclui zero."), (False, "não demonstra diferença")]:
            i = {**self.indicadores, "teste": {**self.indicadores["teste"], "significativo": significativo}}
            relatorio = self._renderizar(i)[os.path.join("output", "relatorios", "relatorio_final_matao.md")]
            self.assertIn(trecho, relatorio)

    def test_conclusao_acompanha_o_modelo(self):
        modelo = {**self.indicadores["modelo"], "supera_referencia": True}
        relatorio = self._renderizar({**self.indicadores, "modelo": modelo})[
            os.path.join("output", "relatorios", "relatorio_final_matao.md")
        ]
        self.assertIn("O modelo supera essa referência", relatorio)
        self.assertNotIn("não supera a referência", relatorio)


if __name__ == "__main__":
    unittest.main()
