"""
Pipeline de Ingestão e Atualização Automatizada de Dados do InfoSiga SP
Município: Matão/SP (Código IBGE: 3529302)

Este script realiza o ciclo completo de ETL:
1. Extração (Extract): Consulta a API CKAN do portal Dados Abertos SP (dataset 'eventos-de-sinistro')
   e identifica novos arquivos mensais disponibilizados pelo Detran/Infosiga.
2. Transformação (Transform): Faz streaming dos dados brutos, filtra imediatamente por Matão,
   aplica o mapeamento de colunas, tratamento de nulos, tipagem e feature engineering.
3. Carga (Load): Realiza upsert (inserção sem duplicatas) no arquivo 'data/matao_limpo.csv'
   e recalcula 'output/relatorios/resumo_anual_matao.csv'.
"""

import os
import sys
import json
import logging
import re
import argparse
from datetime import datetime
import urllib.request
import urllib.error
import pandas as pd
import numpy as np

# -----------------------------------------------------------------------------
# Configuração de Logging
# -----------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ETL_INFOSIGA")

# -----------------------------------------------------------------------------
# Constantes do Projeto
# -----------------------------------------------------------------------------
CODIGO_IBGE_MATAO = 3529302
CKAN_PACKAGE_URL = "https://dadosabertos.sp.gov.br/api/3/action/package_show?id=eventos-de-sinistro"
CAMINHO_DATASET_LIMPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "matao_limpo.csv"))
CAMINHO_RESUMO_ANUAL = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "output", "relatorios", "resumo_anual_matao.csv"))
PASTA_TEMP = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "temp_downloads"))

MAPA_COLUNAS = {
    'id_sinistro': 'id_sinistro',
    'tipo_registro': 'tipo_registro',
    'data_sinistro': 'data',
    'ano_sinistro': 'ano',
    'mes_sinistro': 'mes',
    'dia_sinistro': 'dia',
    'hora_sinistro': 'hora',
    'dia_da_semana': 'dia_semana',
    'turno': 'turno',
    'tipo_via': 'tipo_via',
    'tipo_local': 'tipo_local',
    'logradouro': 'logradouro',
    'latitude': 'latitude',
    'longitude': 'longitude',
    'tp_sinistro_primario': 'tipo_sinistro',
    'qtd_bicicleta': 'qtd_bicicleta',
    'qtd_motocicleta': 'qtd_motocicleta',
    'qtd_automovel': 'qtd_automovel',
    'qtd_onibus': 'qtd_onibus',
    'qtd_caminhao': 'qtd_caminhao',
    'qtd_pedestre': 'qtd_pedestre',
    'qtd_veic_outros': 'qtd_outros_veiculos',
    'qtd_gravidade_fatal': 'mortos',
    'qtd_gravidade_grave': 'feridos_graves',
    'qtd_gravidade_leve': 'feridos_leves',
    'qtd_gravidade_ileso': 'ilesos'
}

COLUNAS_CONTAGENS = [
    'qtd_bicicleta', 'qtd_motocicleta', 'qtd_automovel', 
    'qtd_onibus', 'qtd_caminhao', 'qtd_pedestre', 'qtd_outros_veiculos',
    'mortos', 'feridos_graves', 'feridos_leves', 'ilesos'
]


def extrair_mes_ano_do_nome(nome_ou_url: str):
    """
    Extrai (ano, mes) de padrões como 'sinistros_08-2026.csv' ou 'Agosto de 2026'.
    Retorna tupla (ano, mes) ou (None, None).
    """
    # Procura formato sinistros_MM-AAAA.csv
    match_csv = re.search(r"sinistros_(\d{2})-(\d{4})\.csv", nome_ou_url, re.IGNORECASE)
    if match_csv:
        mes = int(match_csv.group(1))
        ano = int(match_csv.group(2))
        return ano, mes

    # Procura formato por extenso
    meses_pt = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'marco': 3, 'abril': 4,
        'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8, 'setembro': 9,
        'outubro': 10, 'novembro': 11, 'dezembro': 12
    }
    for nome_mes, num_mes in meses_pt.items():
        if nome_mes in nome_ou_url.lower():
            match_ano = re.search(r"20\d{2}", nome_ou_url)
            if match_ano:
                return int(match_ano.group(0)), num_mes

    return None, None


def obter_recursos_ckan():
    """Consulta a API CKAN do Estado de SP e retorna a lista de recursos disponíveis."""
    logger.info("Consultando catálogo de dados abertos do Governo de SP (CKAN)...")
    req = urllib.request.Request(
        CKAN_PACKAGE_URL,
        headers={"User-Agent": "ProjetoTransitoMatao/1.0 (Python urllib)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("success"):
                recursos = data.get("result", {}).get("resources", [])
                logger.info(f"API respondeu com sucesso: {len(recursos)} recursos encontrados.")
                return recursos
            else:
                logger.error("API retornou status não-sucedido.")
                return []
    except Exception as e:
        logger.error(f"Falha ao conectar à API CKAN: {e}")
        return []


def obter_periodo_atual_matao(caminho_csv: str):
    """Retorna o ano e mês mais recente já presente em matao_limpo.csv."""
    if not os.path.exists(caminho_csv):
        return None, None
    try:
        df = pd.read_csv(caminho_csv, usecols=["data"])
        datas = pd.to_datetime(df["data"], errors="coerce").dropna()
        if datas.empty:
            return None, None
        data_max = datas.max()
        return data_max.year, data_max.month
    except Exception as e:
        logger.warning(f"Não foi possível ler data máxima do CSV existente: {e}")
        return None, None


def baixar_arquivo(url: str, destino: str) -> bool:
    """Faz o download de um arquivo com tratamento de timeout e streaming de blocos."""
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    try:
        logger.info(f"Baixando: {os.path.basename(destino)} ...")
        with urllib.request.urlopen(req, timeout=60) as resp, open(destino, "wb") as f_out:
            bloco_tamanho = 1024 * 1024  # 1 MB
            while True:
                bloco = resp.read(bloco_tamanho)
                if not bloco:
                    break
                f_out.write(bloco)
        logger.info(f"Download concluído ({os.path.getsize(destino) / (1024*1024):.2f} MB).")
        return True
    except Exception as e:
        logger.error(f"Erro no download da URL {url}: {e}")
        if os.path.exists(destino):
            os.remove(destino)
        return False


def processar_e_limpar_chunk_matao(df_bruto: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica as etapas exatas de limpeza e feature engineering desenvolvidas
    no notebook 02-limpeza.ipynb para os registros de Matão.
    """
    # 1. Filtrar código IBGE de Matão
    if "cod_ibge" in df_bruto.columns:
        df_matao = df_bruto[df_bruto["cod_ibge"] == CODIGO_IBGE_MATAO].copy()
    else:
        # Fallback se cod_ibge estiver formatado como string ou ausente
        df_matao = df_bruto[df_bruto["municipio"].astype(str).str.upper() == "MATÃO"].copy()

    if df_matao.empty:
        return pd.DataFrame()

    # 2. Selecionar e renomear colunas
    colunas_presentes = {k: v for k, v in MAPA_COLUNAS.items() if k in df_matao.columns}
    df_matao = df_matao[list(colunas_presentes.keys())].rename(columns=colunas_presentes).copy()

    # Garantir que todas as colunas mapeadas existam
    for col_padrao in MAPA_COLUNAS.values():
        if col_padrao not in df_matao.columns:
            df_matao[col_padrao] = 0 if col_padrao in COLUNAS_CONTAGENS else None

    # 3. Tratar contagens numéricas (NaN -> 0 -> int)
    for col in COLUNAS_CONTAGENS:
        df_matao[col] = pd.to_numeric(df_matao[col], errors="coerce").fillna(0).astype(int)

    # 4. Formatação de Datas e Horas
    # Tenta padrão %d/%m/%Y ou ISO %Y-%m-%d
    df_matao["data"] = pd.to_datetime(df_matao["data"], dayfirst=True, errors="coerce")
    
    # Extrair hora inteira
    horas_parsed = pd.to_datetime(df_matao["hora"].astype(str), format="%H:%M", errors="coerce")
    df_matao["hora_int"] = horas_parsed.dt.hour

    # 5. Latitude e Longitude
    df_matao["latitude"] = pd.to_numeric(df_matao["latitude"].astype(str).str.replace(",", "."), errors="coerce")
    df_matao["longitude"] = pd.to_numeric(df_matao["longitude"].astype(str).str.replace(",", "."), errors="coerce")

    # 6. Feature Engineering
    df_matao["total_vitimas"] = df_matao["feridos_leves"] + df_matao["feridos_graves"] + df_matao["mortos"]
    df_matao["total_veiculos"] = (
        df_matao["qtd_bicicleta"] + df_matao["qtd_motocicleta"] +
        df_matao["qtd_automovel"] + df_matao["qtd_onibus"] +
        df_matao["qtd_caminhao"] + df_matao["qtd_outros_veiculos"]
    )

    condicoes = [
        df_matao["mortos"] > 0,
        df_matao["feridos_graves"] > 0,
        df_matao["feridos_leves"] > 0
    ]
    rotulos = ["Com óbito", "Com feridos graves", "Com feridos leves"]
    df_matao["gravidade"] = np.select(condicoes, rotulos, default="Sem vítimas")

    df_matao["fim_de_semana"] = df_matao["dia_semana"].astype(str).str.upper().str.contains("SÁBADO|SABADO|DOMINGO")

    # Formatar campo 'data' como string YYYY-MM-DD para salvar no CSV
    df_matao["data"] = df_matao["data"].dt.strftime("%Y-%m-%d")

    return df_matao


def processar_arquivo_bruto(caminho_csv: str) -> pd.DataFrame:
    """Lê arquivo bruto em chunks de 20.000 linhas e extrai registros de Matão."""
    registros = []
    chunk_size = 20000
    
    # Testa encodings comuns no portal do Infosiga
    encodings = ["latin1", "utf-8", "iso-8859-1"]
    encoding_usado = "latin1"

    for enc in encodings:
        try:
            for chunk in pd.read_csv(caminho_csv, sep=";", encoding=enc, chunksize=chunk_size, low_memory=False):
                df_tratado = processar_e_limpar_chunk_matao(chunk)
                if not df_tratado.empty:
                    registros.append(df_tratado)
            encoding_usado = enc
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            logger.error(f"Erro ao processar chunk de {caminho_csv} com {enc}: {e}")
            break

    if registros:
        return pd.concat(registros, ignore_index=True)
    return pd.DataFrame()


def atualizar_resumo_anual(df_completo: pd.DataFrame, caminho_resumo: str):
    """Gera o arquivo de resumo anual agregado atualizado para o dashboard."""
    os.makedirs(os.path.dirname(caminho_resumo), exist_ok=True)
    resumo_anual = df_completo.groupby("ano").agg(
        total_sinistros=("id_sinistro", "count"),
        obitos=("mortos", "sum"),
        feridos_graves=("feridos_graves", "sum"),
        feridos_leves=("feridos_leves", "sum"),
        ilesos=("ilesos", "sum")
    ).reset_index()

    resumo_anual.to_csv(caminho_resumo, index=False)
    logger.info(f"Resumo anual atualizado salvo em: {caminho_resumo}")


def executar_pipeline(forcar_todos: bool = False) -> bool:
    """Função principal que orquestra a obtenção, limpeza e inserção dos dados."""
    logger.info("=== INICIANDO PIPELINE DE ATUALIZAÇÃO DO INFOSIGA (MATÃO/SP) ===")
    
    # 1. Carregar base existente
    if os.path.exists(CAMINHO_DATASET_LIMPO):
        df_atual = pd.read_csv(CAMINHO_DATASET_LIMPO)
        logger.info(f"Dataset atual carregado com {len(df_atual)} sinistros.")
    else:
        df_atual = pd.DataFrame()
        logger.warning(f"Arquivo {CAMINHO_DATASET_LIMPO} não encontrado. Será criada uma nova base.")

    ultimo_ano, ultimo_mes = obter_periodo_atual_matao(CAMINHO_DATASET_LIMPO)
    logger.info(f"Último período registrado na base de Matão: {ultimo_mes:02d}/{ultimo_ano}" if ultimo_ano else "Nenhum período registrado previamente.")

    # 2. Consultar API CKAN
    recursos = obter_recursos_ckan()
    if not recursos:
        logger.warning("Nenhum recurso obtido da API. Encerrando pipeline.")
        return False

    # 3. Filtrar recursos que precisam ser baixados
    recursos_pendentes = []
    for res in recursos:
        formato = res.get("format", "").upper()
        if formato != "CSV":
            continue
        url = res.get("url", "")
        nome = res.get("name", "")
        ano, mes = extrair_mes_ano_do_nome(url or nome)
        
        if not ano or not mes:
            continue

        # Se forcar_todos for False, só pega meses iguais ou posteriores ao último existente
        # (é bom pegar também o mês atual pois pode ter sido atualizado com dados consolidados)
        if not forcar_todos and ultimo_ano and ultimo_mes:
            if (ano < ultimo_ano) or (ano == ultimo_ano and mes < ultimo_mes):
                continue

        recursos_pendentes.append({
            "nome": nome,
            "url": url,
            "ano": ano,
            "mes": mes
        })

    # Ordenar por ano e mês cronologicamente
    recursos_pendentes.sort(key=lambda x: (x["ano"], x["mes"]))
    logger.info(f"Total de arquivos mensais a serem verificados/processados: {len(recursos_pendentes)}")

    novos_dfs = []
    os.makedirs(PASTA_TEMP, exist_ok=True)

    try:
        for item in recursos_pendentes:
            nome_arq = f"sinistros_{item['mes']:02d}-{item['ano']}.csv"
            caminho_local = os.path.join(PASTA_TEMP, nome_arq)

            sucesso = baixar_arquivo(item["url"], caminho_local)
            if not sucesso:
                logger.warning(f"Pulando {nome_arq} devido a erro no download.")
                continue

            logger.info(f"Processando e filtrando Matão em {nome_arq}...")
            df_mes_matao = processar_arquivo_bruto(caminho_local)
            
            qtd_encontrada = len(df_mes_matao)
            logger.info(f" -> Encontrados {qtd_encontrada} sinistros para Matão em {item['mes']:02d}/{item['ano']}.")
            if qtd_encontrada > 0:
                novos_dfs.append(df_mes_matao)

            # Limpar arquivo temporário para economizar espaço
            if os.path.exists(caminho_local):
                os.remove(caminho_local)

    finally:
        # Remover pasta temporária se estiver vazia
        if os.path.exists(PASTA_TEMP) and not os.listdir(PASTA_TEMP):
            os.rmdir(PASTA_TEMP)

    if not novos_dfs:
        logger.info("Nenhum novo sinistro foi adicionado. A base já está atualizada com os dados do InfoSiga.")
        return True

    # 4. Inserção / Upsert no Dataset Consolidado
    df_novos_concatenados = pd.concat(novos_dfs, ignore_index=True)
    logger.info(f"Total de registros obtidos nos novos arquivos: {len(df_novos_concatenados)}")

    if df_atual.empty:
        df_final = df_novos_concatenados
    else:
        # Concatena a base existente com os novos registros
        df_combinado = pd.concat([df_atual, df_novos_concatenados], ignore_index=True)
        # Deduplica pelo 'id_sinistro' mantendo a versão mais recente dos dados
        df_final = df_combinado.drop_duplicates(subset=["id_sinistro"], keep="last").copy()

    # Ordenar por data e id
    df_final["data_temp"] = pd.to_datetime(df_final["data"], errors="coerce")
    df_final = df_final.sort_values(by=["data_temp", "id_sinistro"]).drop(columns=["data_temp"])

    # Salvar dataset consolidado
    df_final.to_csv(CAMINHO_DATASET_LIMPO, index=False)
    novos_inseridos = len(df_final) - len(df_atual)
    logger.info(f"=== ATUALIZAÇÃO CONCLUÍDA COM SUCESSO ===")
    logger.info(f"Base de dados salva: {CAMINHO_DATASET_LIMPO}")
    logger.info(f"Total anterior: {len(df_atual)} | Total agora: {len(df_final)} | Novos registros líquidos: {novos_inseridos}")

    # 5. Atualizar resumo anual
    atualizar_resumo_anual(df_final, CAMINHO_RESUMO_ANUAL)

    return True


def verificar_novos_dados() -> bool:
    """
    Modo apenas verificação (--verificar):
    Consulta a API do InfoSiga/CKAN e compara com a base local matao_limpo.csv.
    Não baixa arquivos nem modifica a base de dados.
    Retorna True se existirem novos dados disponíveis, False caso contrário.
    """
    logger.info("=== VERIFICAÇÃO DE NOVOS DADOS NO INFOSIGA ===")
    ultimo_ano, ultimo_mes = obter_periodo_atual_matao(CAMINHO_DATASET_LIMPO)
    if ultimo_ano and ultimo_mes:
        logger.info(f"Último período registrado na base local (Matão): {ultimo_mes:02d}/{ultimo_ano}")
    else:
        logger.warning("Base local ainda não possui registros.")

    recursos = obter_recursos_ckan()
    if not recursos:
        logger.error("Não foi possível obter a lista de arquivos da API do Estado de SP.")
        return False

    meses_disponiveis = []
    meses_novos = []

    for res in recursos:
        if res.get("format", "").upper() != "CSV":
            continue
        url = res.get("url", "")
        nome = res.get("name", "")
        ano, mes = extrair_mes_ano_do_nome(url or nome)
        if not ano or not mes:
            continue
        meses_disponiveis.append((ano, mes, nome))
        
        if ultimo_ano and ultimo_mes:
            if (ano > ultimo_ano) or (ano == ultimo_ano and mes > ultimo_mes):
                meses_novos.append((ano, mes, nome))

    meses_disponiveis.sort(key=lambda x: (x[0], x[1]))
    if meses_disponiveis:
        primeiro = meses_disponiveis[0]
        ultimo = meses_disponiveis[-1]
        logger.info(f"Período disponível no portal InfoSiga: {primeiro[1]:02d}/{primeiro[0]} até {ultimo[1]:02d}/{ultimo[0]}")

    if meses_novos:
        logger.info(f"🔔 ATENÇÃO: {len(meses_novos)} novo(s) mês(es) disponível(is) para download no InfoSiga:")
        for ano, mes, nome in meses_novos:
            logger.info(f"   -> Mês {mes:02d}/{ano} ({nome})")
        logger.info("Execute com a flag '--automatico' para baixar e incorporar os dados.")
        return True
    else:
        logger.info("✅ SITUAÇÃO: A base de dados local já está sincronizada com o InfoSiga. Nenhum mês pendente.")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline ETL de Atualização de Dados do InfoSiga SP para Matão/SP"
    )
    parser.add_argument(
        "--verificar",
        action="store_true",
        help="Apenas verifica se existem novos meses disponíveis no InfoSiga, sem baixar ou alterar a base."
    )
    parser.add_argument(
        "--automatico",
        action="store_true",
        help="Executa o pipeline completo de extração, limpeza, deduplicação e inserção dos novos dados."
    )
    parser.add_argument(
        "--forcar",
        action="store_true",
        help="Força o reprocessamento de todos os arquivos mensais disponíveis."
    )

    args = parser.parse_args()

    if args.verificar:
        tem_novos = verificar_novos_dados()
        sys.exit(0)
    elif args.automatico:
        sucesso = executar_pipeline(forcar_todos=args.forcar)
        sys.exit(0 if sucesso else 1)
    else:
        # Se chamado sem argumentos, exibe o menu de ajuda
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()

