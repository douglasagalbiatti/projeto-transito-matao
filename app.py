import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from src.metricas import (
    caminho_grafico,
    ORDEM_GRAVIDADE,
    SEM_FERIDOS,
    SEM_INFORMACAO,
    base_comparavel,
    br,
    comparar_dias,
    formatar_tabela,
    razao_letalidade,
    tabela_letalidade,
)
from src.modelo import (
    DOBRAS_CV,
    NOMES_REFERENCIA,
    NOMES_VARIAVEIS_MODELO,
    REPETICOES_CV,
    prever_probabilidade,
    treinar_modelo,
)

# -----------------------------------------------------------------------------
# 1. Configuração da Página
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Sinistros de Trânsito — Matão/SP",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS refinada
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        border: 1px solid #e9ecef;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .badge-fatais {
        background-color: #d90429;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-graves {
        background-color: #f77f00;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-leves {
        background-color: #e5b124;
        color: #1a1a1a;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .badge-semvitima {
        background-color: #2b5c8f;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.85rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding-top: 10px;
        padding-bottom: 10px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

def mostrar_grafico(fig):
    """Exibe um gráfico Plotly com vírgula decimal e ponto de milhar."""
    fig.update_layout(separators=",.")
    fig.update_xaxes(separatethousands=True)
    fig.update_yaxes(separatethousands=True)
    st.plotly_chart(fig, width="stretch")

# -----------------------------------------------------------------------------
# 2. Carregamento de Dados com Cache
# -----------------------------------------------------------------------------
@st.cache_data(ttl="1h")
def carregar_dados_principais():
    caminho = "data/matao_limpo.csv"
    if not os.path.exists(caminho):
        st.error(f"Arquivo de dados não encontrado: {caminho}")
        return pd.DataFrame()
    df = pd.read_csv(caminho, parse_dates=["data"])
    return df

@st.cache_data(ttl="1h")
def carregar_resumo_anual():
    caminho = "output/relatorios/resumo_anual_matao.csv"
    if os.path.exists(caminho):
        return pd.read_csv(caminho)
    return pd.DataFrame()

@st.cache_data(ttl="1h")
def carregar_texto_relatorio():
    caminho = "output/relatorios/relatorio_final_matao.md"
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    return ""

@st.cache_resource(ttl="1h")
def treinar_modelo_cache(df):
    return treinar_modelo(df)

df_completo = carregar_dados_principais()
df_resumo_anual = carregar_resumo_anual()
texto_relatorio = carregar_texto_relatorio()

if df_completo.empty:
    st.error("Não foi possível carregar a base de dados `data/matao_limpo.csv`. Verifique se o arquivo está na raiz do projeto.")
    st.stop()

# Cores padronizadas para níveis de gravidade
CORES_GRAVIDADE = {
    'Com óbito': '#d90429',         # Vermelho
    'Com feridos graves': '#f77f00',  # Laranja
    'Com feridos leves': '#e5b124',   # Amarelo/Dourado
    SEM_FERIDOS: '#2b5c8f',           # Azul
    SEM_INFORMACAO: '#adb5bd'         # Cinza
}
DIAS_ORDENADOS = ['Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado', 'Domingo']

# -----------------------------------------------------------------------------
# 3. Barra Lateral de Filtros Interativos
# -----------------------------------------------------------------------------
st.sidebar.title("🚦 Filtros de Análise")
st.sidebar.caption("Personalize os parâmetros para filtrar a base de Matão/SP")

# Filtro de Anos
todos_anos = sorted(df_completo["ano"].dropna().unique().tolist())
anos_selecionados = st.sidebar.multiselect(
    "Ano do Sinistro:",
    options=todos_anos,
    default=todos_anos
)

# Filtro de Gravidade
gravidades_disponiveis = ORDEM_GRAVIDADE
gravidades_selecionadas = st.sidebar.multiselect(
    "Nível de Gravidade:",
    options=gravidades_disponiveis,
    default=gravidades_disponiveis
)

# Filtro de Tipo de Via
tipos_via = sorted(df_completo["tipo_via"].dropna().unique().tolist())
vias_selecionadas = st.sidebar.multiselect(
    "Tipo de Via:",
    options=tipos_via,
    default=tipos_via
)

# Filtro de Tipo de Sinistro
tipos_sinistro = sorted(df_completo["tipo_sinistro"].dropna().unique().tolist())
sinistros_selecionados = st.sidebar.multiselect(
    "Tipo de Sinistro:",
    options=tipos_sinistro,
    default=tipos_sinistro
)

# Filtro de Modal Específico
filtro_modal = st.sidebar.selectbox(
    "Filtro por Modal Envolvido:",
    options=["Todos os Modais", "Com Motocicleta", "Com Automóvel", "Com Caminhão", "Com Pedestre", "Com Bicicleta"]
)

# Aplicação dos Filtros
df_filtrado = df_completo.copy()

df_filtrado = df_filtrado[
    df_filtrado["ano"].isin(anos_selecionados)
    & df_filtrado["gravidade"].isin(gravidades_selecionadas)
    & df_filtrado["tipo_via"].isin(vias_selecionadas)
    & df_filtrado["tipo_sinistro"].isin(sinistros_selecionados)
]

if filtro_modal == "Com Motocicleta":
    df_filtrado = df_filtrado[df_filtrado["qtd_motocicleta"] > 0]
elif filtro_modal == "Com Automóvel":
    df_filtrado = df_filtrado[df_filtrado["qtd_automovel"] > 0]
elif filtro_modal == "Com Caminhão":
    df_filtrado = df_filtrado[df_filtrado["qtd_caminhao"] > 0]
elif filtro_modal == "Com Pedestre":
    df_filtrado = df_filtrado[df_filtrado["qtd_pedestre"] > 0]
elif filtro_modal == "Com Bicicleta":
    df_filtrado = df_filtrado[df_filtrado["qtd_bicicleta"] > 0]

if df_filtrado.empty:
    st.warning("Nenhum registro atende aos filtros selecionados.")
    st.stop()

df_comparavel = base_comparavel(df_filtrado)

# Informações da base na barra lateral
st.sidebar.divider()
st.sidebar.markdown(f"**Registros Filtrados:** {br(len(df_filtrado))} de {br(len(df_completo))} ({br(len(df_filtrado)/len(df_completo)*100, 1)}%)")
st.sidebar.info("""
**Dados Oficiais:**
- **Fonte:** Infosiga SP
- **Município:** Matão / SP
- **Código IBGE:** 3529302
- **Período:** {inicio} a {fim}
""".format(inicio=df_completo["data"].min().strftime("%m/%Y"), fim=df_completo["data"].max().strftime("%m/%Y")))

# -----------------------------------------------------------------------------
# 4. Cabeçalho Principal e Contexto Executivo
# -----------------------------------------------------------------------------
PERIODO = f"{int(df_completo['ano'].min())}–{int(df_completo['ano'].max())}"
st.title(f"🚗 Diagnóstico e Análise de Sinistros de Trânsito — Matão/SP ({PERIODO})")
st.markdown("**Observatório de Segurança Viária baseado nos microdados públicos do Infosiga SP**")

with st.container(border=True):
    col_c1, col_c2, col_c3 = st.columns([2, 1, 1])
    with col_c1:
        st.markdown("""
        **Contexto Regional:**  
        Matão é um polo industrial e agrícola estratégico no centro-norte paulista, sediando grandes indústrias 
        (Marchesan, Baldan, Citrosuco) e cortado por duas rodovias estaduais de intenso tráfego: **SP-310 (Washington Luís)** e **SP-326 (Brigadeiro Faria Lima)**.
        """)
    with col_c2:
        st.markdown("""
        **Contexto Viário:**  
        Convivência de caminhões, automóveis, motocicletas e travessias urbanas. A base não mede fluxo de veículos nem frota.
        """)
    with col_c3:
        st.markdown("""
        **Objetivo:**  
        Descrever padrões por tipo de sinistro, horário e via, e indicar o que deve ser verificado em campo.
        """)

# Alerta sobre ressalva metodológica de 2019
st.info("""
ℹ️ **Ressalva Metodológica Fundamental:**  
Entre **2015 e 2018**, o Infosiga registrava exclusivamente sinistros com **óbito**. A partir de **2019**, com a integração de dados da Polícia Militar, SAMU e Bombeiros, foram incorporados os sinistros não fatais e as notificações.  
A proporção de **notificações**, quase sempre sem dados de vítimas e veículos, varia muito por ano. Por isso, totais anuais não medem tendência, e letalidade e perfis de gravidade usam a **base comparável: sinistros de 2019 em diante, sem notificações**.
""")

# -----------------------------------------------------------------------------
# 5. Painel de Indicadores Chave (KPIs)
# -----------------------------------------------------------------------------
total_reg = len(df_filtrado)
obitos = int(df_filtrado["mortos"].sum())
f_graves = int(df_filtrado["feridos_graves"].sum())
f_leves = int(df_filtrado["feridos_leves"].sum())
sem_info = int((df_filtrado["gravidade"] == SEM_INFORMACAO).sum())
taxa_letalidade = (df_comparavel["mortos"] > 0).mean() * 100 if len(df_comparavel) > 0 else 0.0
sinistros_motos = int((df_filtrado["qtd_motocicleta"] > 0).sum())
total_com_modal = int(((df_filtrado["total_veiculos"] > 0) | (df_filtrado["qtd_pedestre"] > 0)).sum())
pct_motos = (sinistros_motos / total_com_modal * 100) if total_com_modal > 0 else 0.0

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Total de Registros", br(total_reg))
col2.metric("Vítimas Fatais (Óbitos)", br(obitos), delta=f"{br(taxa_letalidade, 1)}% letalidade (base comparável)", delta_color="off")
col3.metric("Feridos Graves", br(f_graves))
col4.metric("Feridos Leves", br(f_leves))
col5.metric("Sem Informação de Vítimas", br(sem_info))
col6.metric("Envolve Moto", br(sinistros_motos), delta=f"{br(pct_motos, 1)}% dos registros com modal informado", delta_color="off")

st.markdown("---")

# -----------------------------------------------------------------------------
# 6. Abas Temáticas com Todos os Resultados do Relatório
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📊 Evolução & Gravidade",
    "⚡ Tipos & Letalidade",
    "🏍️ Modais",
    "⏱️ Padrões Temporais & Teste t",
    "🗺️ Geografia (Mapa)",
    "🤖 Machine Learning",
    "🛡️ Recomendações",
    "📄 Relatório na Íntegra & Dados"
])

# =============================================================================
# ABA 1: Evolução Temporal & Distribuição da Gravidade
# =============================================================================
with tab1:
    st.subheader("1. Evolução Histórica Anual e Distribuição de Gravidade")
    
    col_t1a, col_t1b = st.columns([3, 2])
    
    with col_t1a:
        # Gráfico Anual: Barras de Sinistros + Linha de Óbitos
        dados_ano = df_filtrado.groupby('ano').agg(
            sinistros=('tipo_registro', lambda s: int((s != 'NOTIFICACAO').sum())),
            notificacoes=('tipo_registro', lambda s: int((s == 'NOTIFICACAO').sum())),
            obitos=('mortos', 'sum')
        ).reset_index()
        
        fig_ano = go.Figure()
        # Barras
        fig_ano.add_trace(go.Bar(
            x=dados_ano['ano'],
            y=dados_ano['sinistros'],
            name='Sinistros (fatais e não fatais)',
            marker_color='#2b5c8f',
            yaxis='y'
        ))
        fig_ano.add_trace(go.Bar(
            x=dados_ano['ano'],
            y=dados_ano['notificacoes'],
            name='Notificações',
            marker_color='#adb5bd',
            yaxis='y'
        ))
        # Linha de Óbitos
        fig_ano.add_trace(go.Scatter(
            x=dados_ano['ano'],
            y=dados_ano['obitos'],
            name='Vítimas Fatais (Óbitos)',
            mode='lines+markers+text',
            line=dict(color='#d90429', width=3),
            marker=dict(size=8, color='#d90429'),
            text=dados_ano['obitos'],
            textposition='top center',
            yaxis='y2'
        ))
        
        fig_ano.update_layout(
            barmode='stack',
            title=f"<b>Evolução dos Registros e Óbitos em Matão/SP ({PERIODO})</b>",
            xaxis=dict(title="Ano", tickmode='linear', tick0=2015, dtick=1, tickformat='d'),
            yaxis=dict(title="Total de Registros", showgrid=True),
            yaxis2=dict(
                title="Vítimas Fatais",
                overlaying='y',
                side='right',
                showgrid=False,
                range=[0, max(dados_ano['obitos'].max(), 1) * 1.5],
                dtick=5
            ),
            legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.8)'),
            margin=dict(l=40, r=40, t=50, b=40),
            height=420
        )
        mostrar_grafico(fig_ano)
        st.caption("* 2015–2018: apenas sinistros fatais. A partir de 2019, a variação do total reflete também a cobertura das notificações. O último ano pode estar incompleto.")

    with col_t1b:
        # Gráfico Donut de Gravidade
        contagem_grav = df_filtrado['gravidade'].value_counts().reindex(ORDEM_GRAVIDADE).fillna(0)
        fig_donut = px.pie(
            values=contagem_grav.values,
            names=contagem_grav.index,
            color=contagem_grav.index,
            color_discrete_map=CORES_GRAVIDADE,
            hole=0.45,
            title="<b>Distribuição da Gravidade das Ocorrências</b>"
        )
        fig_donut.update_traces(textinfo='percent+label', pull=[0.05, 0, 0, 0, 0])
        fig_donut.update_layout(
            margin=dict(l=20, r=20, t=50, b=20),
            showlegend=False,
            height=420
        )
        mostrar_grafico(fig_donut)

    st.markdown("#### Resumo Estatístico Anual (base completa, sem filtros)")
    if not df_resumo_anual.empty:
        colunas_format = {
            "ano": "Ano",
            "total_sinistros": "Total de Registros",
            "obitos": "Óbitos",
            "feridos_graves": "Feridos Graves",
            "feridos_leves": "Feridos Leves",
            "ilesos": "Ilesos"
        }
        df_show_anual = df_resumo_anual.rename(columns=colunas_format)
        st.dataframe(formatar_tabela(df_show_anual, sem_milhar=["Ano"]), width="stretch", hide_index=True)
    
    with st.expander("🖼️ Ver Gráfico Estático (acidentes_por_ano.png)"):
        st.image(caminho_grafico("acidentes_por_ano.png"), caption="Figura 1: Sinistros, notificações e óbitos por ano (Matplotlib)", width="stretch", alt="Evolução anual dos sinistros")

# =============================================================================
# ABA 2: Tipos de Sinistro & Choque Crítico
# =============================================================================
with tab2:
    st.subheader("2. Tipos de Sinistro e Letalidade")
    
    tab_letal = tabela_letalidade(df_comparavel)
    base_tipos = base_comparavel(df_completo)
    razao, ic_inf, ic_sup = razao_letalidade(base_tipos, 'CHOQUE', 'COLISAO')
    
    st.markdown(f"""
    > ⚠️ **Base comparável, sem os filtros:** a letalidade do choque é **{br(razao, 1)} vezes** a da colisão (IC95% {br(ic_inf, 1)} a {br(ic_sup, 1)}), mas a diferença é urbana. Em rodovias, as taxas são próximas.
    
    Letalidade = sinistros com óbito ÷ sinistros do tipo. O dado não informa velocidade nem qual objeto foi atingido.
    """)
    
    comparacao_via = base_tipos[base_tipos['tipo_sinistro'].isin(['CHOQUE', 'COLISAO']) & (base_tipos['tipo_via'] != 'NAO DISPONIVEL')]
    st.dataframe(formatar_tabela(tabela_letalidade(comparacao_via, por=['tipo_via', 'tipo_sinistro'])), width="stretch", hide_index=True)
    
    col_t2a, col_t2b = st.columns([3, 2])
    
    with col_t2a:
        fig_letal = px.bar(
            tab_letal,
            x='tipo_sinistro',
            y='letalidade_pct',
            color='letalidade_pct',
            color_continuous_scale='Reds',
            text=tab_letal['letalidade_pct'].apply(lambda v: f"{br(v, 2)}%"),
            title="<b>Taxa de Letalidade (%) por Tipo de Sinistro</b>",
            labels={'letalidade_pct': 'Letalidade (% dos sinistros)', 'tipo_sinistro': 'Tipo de Sinistro'}
        )
        fig_letal.update_traces(textposition='outside')
        fig_letal.update_layout(
            margin=dict(l=20, r=20, t=50, b=40),
            coloraxis_showscale=False,
            height=380
        )
        mostrar_grafico(fig_letal)
        
    with col_t2b:
        fig_vol = px.bar(
            tab_letal.sort_values(by='sinistros', ascending=True),
            x='sinistros',
            y='tipo_sinistro',
            orientation='h',
            text=tab_letal.sort_values(by='sinistros', ascending=True)['sinistros'].apply(br),
            title="<b>Volume Total de Ocorrências por Tipo</b>",
            color_discrete_sequence=['#2b5c8f']
        )
        fig_vol.update_traces(textposition='outside')
        fig_vol.update_layout(
            margin=dict(l=20, r=20, t=50, b=40),
            height=380,
            xaxis=dict(title="Total de Ocorrências"),
            yaxis=dict(title="")
        )
        mostrar_grafico(fig_vol)

    st.markdown("#### Tabela Comparativa de Severidade por Tipo de Sinistro")
    st.dataframe(
        formatar_tabela(tab_letal.rename(columns={
            'tipo_sinistro': 'Tipo de Sinistro',
            'sinistros': 'Sinistros',
            'sinistros_fatais': 'Sinistros com Óbito',
            'mortos': 'Óbitos (pessoas)',
            'feridos_graves': 'Feridos Graves (pessoas)',
            'letalidade_pct': 'Letalidade (%)'
        })),
        width="stretch",
        hide_index=True
    )

# =============================================================================
# ABA 3: Modais
# =============================================================================
with tab3:
    st.subheader("3. Modais de Transporte")
    
    st.markdown("""
    As proporções consideram apenas registros com veículo ou pedestre informado, pois notificações costumam vir sem esses dados.
    
    A base não liga cada vítima ao seu veículo. Ela mostra a gravidade do sinistro com moto, não o risco individual do motociclista, e não há dado de frota ou de quilômetros rodados.
    """)
    
    col_t3a, col_t3b = st.columns([1, 1])
    
    with col_t3a:
        # Presença de modais
        df_com_modal = df_filtrado[(df_filtrado['total_veiculos'] > 0) | (df_filtrado['qtd_pedestre'] > 0)]
        total_sin = len(df_com_modal)
        modais_dict = {
            'Automóvel': int((df_com_modal['qtd_automovel'] > 0).sum()),
            'Motocicleta': int((df_com_modal['qtd_motocicleta'] > 0).sum()),
            'Caminhão': int((df_com_modal['qtd_caminhao'] > 0).sum()),
            'Pedestre': int((df_com_modal['qtd_pedestre'] > 0).sum()),
            'Bicicleta': int((df_com_modal['qtd_bicicleta'] > 0).sum()),
            'Ônibus': int((df_com_modal['qtd_onibus'] > 0).sum())
        }
        df_modais = pd.DataFrame(list(modais_dict.items()), columns=['Modal', 'Qtd_Sinistros']).sort_values(by='Qtd_Sinistros', ascending=True)
        df_modais['Percentual'] = (df_modais['Qtd_Sinistros'] / total_sin * 100).round(1) if total_sin > 0 else 0
        
        fig_mod = px.bar(
            df_modais,
            x='Qtd_Sinistros',
            y='Modal',
            orientation='h',
            text=df_modais.apply(lambda r: f"{br(r['Qtd_Sinistros'])} ({br(r['Percentual'], 1)}%)", axis=1),
            color='Modal',
            color_discrete_sequence=['#fa8431'],
            title="<b>Presença dos Modais nos Sinistros</b>"
        )
        fig_mod.update_traces(textposition='outside')
        fig_mod.update_layout(showlegend=False, height=380, margin=dict(l=20, r=40, t=50, b=20))
        mostrar_grafico(fig_mod)
        
    with col_t3b:
        # Comparativo: Com Moto vs Sem Moto em relação à gravidade
        df_filtrado_comp = df_comparavel.copy()
        df_filtrado_comp['Grupo'] = np.where(df_filtrado_comp['qtd_motocicleta'] > 0, 'Com Motocicleta', 'Sem Motocicleta')
        crosstab_motos = pd.crosstab(df_filtrado_comp['Grupo'], df_filtrado_comp['gravidade'], normalize='index') * 100
        crosstab_motos = crosstab_motos.reindex(columns=ORDEM_GRAVIDADE).reset_index()
        
        df_motos_melt = crosstab_motos.melt(id_vars='Grupo', var_name='Gravidade', value_name='Percentual')
        
        fig_comp = px.bar(
            df_motos_melt,
            x='Grupo',
            y='Percentual',
            color='Gravidade',
            color_discrete_map=CORES_GRAVIDADE,
            barmode='stack',
            text=df_motos_melt['Percentual'].apply(lambda v: f"{br(v, 1)}%" if v > 4 else ""),
            title="<b>Perfil de Gravidade: Com Moto vs Sem Moto (base comparável)</b>"
        )
        fig_comp.update_layout(height=380, margin=dict(l=20, r=20, t=50, b=20), yaxis=dict(title="% do Total do Grupo"))
        mostrar_grafico(fig_comp)

    with st.expander("🖼️ Ver Gráfico Estático (tipos_e_veiculos.png)"):
        st.image(caminho_grafico("tipos_e_veiculos.png"), caption="Figura 2: Tipos de sinistro e veículos envolvidos (Matplotlib)", width="stretch", alt="Tipos de sinistro e veículos")

# =============================================================================
# ABA 4: Padrões Temporais & Teste Estatístico
# =============================================================================
with tab4:
    st.subheader("4. Padrões Temporais, Horários de Pico e Teste de Hipótese")
    
    col_t4a, col_t4b = st.columns([1, 1])
    
    with col_t4a:
        # Gráfico por Hora do Dia
        df_hora = df_filtrado.dropna(subset=['hora_int']).copy()
        df_hora['hora_int'] = df_hora['hora_int'].astype(int)
        contagem_h = df_hora['hora_int'].value_counts().reindex(range(24), fill_value=0).reset_index()
        contagem_h.columns = ['Hora', 'Qtd_Sinistros']
        
        # Destacar os 3 horários de maior volume
        top_horas = contagem_h.nlargest(3, 'Qtd_Sinistros')['Hora'].tolist()
        contagem_h['Cor'] = contagem_h['Hora'].apply(lambda h: '#de2d26' if h in top_horas else '#3182bd')
        
        fig_hora = px.bar(
            contagem_h,
            x='Hora',
            y='Qtd_Sinistros',
            title="<b>Distribuição por Hora do Dia (Destaque nos Picos)</b>",
            text=contagem_h['Qtd_Sinistros'].apply(br)
        )
        fig_hora.update_traces(marker_color=contagem_h['Cor'], textposition='outside')
        fig_hora.update_layout(
            xaxis=dict(tickmode='linear', dtick=2, title="Hora do Dia (0h–23h)"),
            yaxis=dict(title="Quantidade de Registros"),
            height=380,
            margin=dict(l=20, r=20, t=50, b=30)
        )
        mostrar_grafico(fig_hora)
        st.caption(f"Maiores volumes: **{', '.join(f'{h}h' for h in top_horas)}**. Volume não equivale a risco: a base não traz o fluxo de veículos por horário.")
        
    with col_t4b:
        # Gráfico Empilhado por Dia da Semana
        df_dia = df_filtrado.copy()
        crosstab_dia = pd.crosstab(df_dia['dia_semana'], df_dia['gravidade']).reindex(index=DIAS_ORDENADOS, columns=ORDEM_GRAVIDADE).fillna(0)
        
        fig_dia = go.Figure()
        for g in ORDEM_GRAVIDADE:
            if g in crosstab_dia.columns:
                fig_dia.add_trace(go.Bar(
                    x=[d.replace('-feira', '') for d in DIAS_ORDENADOS],
                    y=crosstab_dia[g],
                    name=g,
                    marker_color=CORES_GRAVIDADE[g]
                ))
        fig_dia.update_layout(
            barmode='stack',
            title="<b>Registros por Dia da Semana e Gravidade</b>",
            xaxis=dict(title="Dia da Semana"),
            yaxis=dict(title="Total de Registros"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=380,
            margin=dict(l=20, r=20, t=60, b=30)
        )
        mostrar_grafico(fig_dia)

    # Heatmap Interativo Dia da Semana vs Hora do Dia
    st.markdown("#### Mapa de Calor Interativo: Dia da Semana vs Hora do Dia")
    if not df_hora.empty:
        heatmap_data = df_hora.pivot_table(
            index='dia_semana',
            columns='hora_int',
            values='id_sinistro',
            aggfunc='count',
            fill_value=0
        ).reindex(index=DIAS_ORDENADOS, columns=range(24), fill_value=0)
        
        fig_heat = px.imshow(
            heatmap_data,
            labels=dict(x="Hora do Dia", y="Dia da Semana", color="Registros"),
            x=list(range(24)),
            y=[d.replace('-feira', '') for d in DIAS_ORDENADOS],
            color_continuous_scale="YlOrRd",
            aspect="auto",
            text_auto=True
        )
        fig_heat.update_layout(height=320, margin=dict(l=40, r=20, t=30, b=30))
        mostrar_grafico(fig_heat)

    # Painel do Teste Estatístico
    with st.container(border=True):
        st.markdown("#### 🔬 Comparação entre Dias Úteis e Fins de Semana (teste de Welch)")
        st.markdown("Registros de 2019 em diante, sem os filtros da barra lateral. Cada dia do calendário conta, inclusive os dias sem nenhum registro.")
        
        teste = comparar_dias(df_completo[df_completo['ano'] >= 2019])
        media_por_dia = teste['media_por_dia']
        
        c_stat1, c_stat2, c_stat3, c_stat4 = st.columns(4)
        c_stat1.metric("Média em Dias Úteis", f"{br(teste['media_uteis'], 2)} registros/dia")
        c_stat2.metric("Média em Fins de Semana", f"{br(teste['media_fds'], 2)} registros/dia")
        c_stat3.metric("Diferença (IC95%)", br(teste['diferenca'], 2), f"{br(teste['ic95'][0], 2)} a {br(teste['ic95'][1], 2)}", delta_color="off")
        c_stat4.metric("p-valor", br(teste['p_welch'], 3))
        
        conclusao = "O intervalo exclui zero." if teste['p_welch'] < 0.05 else "O intervalo inclui zero, o que não prova que as médias sejam iguais."
        st.markdown(f"""
        **Interpretação:** {conclusao} Agrupar os dias em dois blocos esconde diferenças: a média é {br(media_por_dia[4], 2)} na sexta e {br(media_por_dia[5], 2)} no sábado, contra {br(media_por_dia[[0, 1, 2, 3, 6]].mean(), 2)} nos demais dias. {br(teste['dias_sem_registro_pct'], 1)}% dos dias não têm registro.
        """)

    with st.expander("🖼️ Ver Gráficos Estáticos (heatmap_dia_hora.png e acidentes_dia_e_hora.png)"):
        col_img1, col_img2 = st.columns(2)
        with col_img1:
            st.image(caminho_grafico("heatmap_dia_hora.png"), caption="Mapa de calor original", width="stretch", alt="Mapa de calor")
        with col_img2:
            st.image(caminho_grafico("acidentes_dia_e_hora.png"), caption="Distribuição de dia e hora original", width="stretch", alt="Acidentes dia e hora")

# =============================================================================
# ABA 5: Geografia (Mapa Interativo & Vias)
# =============================================================================
with tab5:
    st.subheader("5. Distribuição Geográfica dos Sinistros em Matão/SP")
    
    via_valida = df_completo[df_completo['tipo_via'].isin(['VIAS URBANAS', 'ESTRADAS E RODOVIAS'])]
    obitos_via = via_valida.groupby('tipo_via')['mortos'].sum()
    letal_via = via_valida.groupby('tipo_via')['mortos'].apply(lambda s: (s > 0).mean() * 100)
    total_obitos = df_completo['mortos'].sum()
    st.markdown(f"""
    Na base completa, as vias urbanas têm **{obitos_via['VIAS URBANAS']} de {total_obitos} óbitos ({obitos_via['VIAS URBANAS'] / total_obitos * 100:.0f}%)**, e as rodovias, **{obitos_via['ESTRADAS E RODOVIAS']} ({obitos_via['ESTRADAS E RODOVIAS'] / total_obitos * 100:.0f}%)**.
    A rodovia tem menos registros, porém maior letalidade por registro: **{br(letal_via['ESTRADAS E RODOVIAS'], 1)}%**, contra **{br(letal_via['VIAS URBANAS'], 1)}%** nas vias urbanas.
    """)
    
    # Mapa Interativo Plotly com Carto Positron
    # Notificações se concentram em poucas coordenadas repetidas e são omitidas do mapa
    df_geo = df_filtrado[df_filtrado['tipo_registro'] != 'NOTIFICACAO'].dropna(subset=['latitude', 'longitude']).copy()
    # Filtrar coordenadas razoáveis de Matão
    df_geo = df_geo[
        (df_geo['latitude'].between(-21.80, -21.40)) & 
        (df_geo['longitude'].between(-48.60, -48.10))
    ].copy()
    df_geo['data_fmt'] = df_geo['data'].dt.strftime('%d/%m/%Y')
    
    if not df_geo.empty:
        fig_map = px.scatter_map(
            df_geo,
            lat='latitude',
            lon='longitude',
            color='gravidade',
            category_orders={'gravidade': ORDEM_GRAVIDADE},
            color_discrete_map=CORES_GRAVIDADE,
            hover_name='tipo_sinistro',
            hover_data={
                'latitude': False,
                'longitude': False,
                'gravidade': True,
                'data_fmt': True,
                'hora': True,
                'tipo_via': True,
                'logradouro': True,
                'total_vitimas': True
            },
            zoom=12.1,
            center={"lat": -21.6035, "lon": -48.3645},
            map_style='carto-positron',
            height=600,
            title=f"<b>Mapeamento dos Sinistros de Trânsito ({br(len(df_geo))} pontos georreferenciados)</b>"
        )
        fig_map.update_layout(
            margin=dict(l=0, r=0, t=40, b=0),
            legend=dict(
                title=dict(text='<b>Gravidade</b>'),
                bgcolor='rgba(255, 255, 255, 0.9)',
                bordercolor='#cccccc',
                borderwidth=1,
                x=0.01,
                y=0.99
            )
        )
        mostrar_grafico(fig_map)
        st.caption("Coordenadas exatas se repetem muitas vezes em alguns pontos, então a localização pode indicar uma referência, e não o local do impacto.")
    else:
        st.warning("Nenhum registro com coordenadas válidas para os filtros selecionados.")

    st.markdown("#### Ranking das 10 Vias com Mais Sinistros (filtros aplicados, sem notificações)")
    ranking_vias = df_filtrado[df_filtrado['tipo_registro'] != 'NOTIFICACAO'].groupby('logradouro').agg(
        total_sinistros=('id_sinistro', 'count'),
        obitos=('mortos', 'sum'),
        feridos_graves=('feridos_graves', 'sum'),
        feridos_leves=('feridos_leves', 'sum')
    ).sort_values(by='total_sinistros', ascending=False).head(10).reset_index()
    
    col_v1, col_v2 = st.columns([3, 2])
    with col_v1:
        st.dataframe(
            formatar_tabela(ranking_vias.rename(columns={
                'logradouro': 'Via / Logradouro',
                'total_sinistros': 'Total de Sinistros',
                'obitos': 'Óbitos',
                'feridos_graves': 'Feridos Graves',
                'feridos_leves': 'Feridos Leves'
            })),
            width="stretch",
            hide_index=True
        )
    with col_v2:
        fig_rank = px.bar(
            ranking_vias.sort_values(by='total_sinistros', ascending=True),
            x='total_sinistros',
            y='logradouro',
            orientation='h',
            title="<b>Vias com Mais Sinistros</b>",
            color_discrete_sequence=['#2b5c8f']
        )
        fig_rank.update_layout(height=360, margin=dict(l=20, r=20, t=40, b=20), yaxis=dict(title=""))
        mostrar_grafico(fig_rank)

    with st.expander("🖼️ Ver Mapa Estático (mapa_estatico_matao.png)"):
        st.image(caminho_grafico("mapa_estatico_matao.png"), caption="Mapa estático dos sinistros em Matão/SP, sem notificações", width="stretch", alt="Mapa estático de Matão")

# =============================================================================
# ABA 6: Machine Learning & Simulador
# =============================================================================
with tab6:
    st.subheader("6. Modelo Exploratório de Gravidade (Regressão Logística)")

    resultado_ml = treinar_modelo_cache(df_completo)

    st.markdown("""
    Modelo exploratório ajustado na base comparável (sem os filtros), para descrever associações com desfecho **grave ou fatal** (ferido grave ou óbito). Ele usa dados conhecidos só depois do sinistro, portanto não prevê acidentes futuros.
    """)

    if resultado_ml is None:
        st.warning("Não há sinistros suficientes na base comparável para ajustar e avaliar o modelo.")
    else:
        teste_ml = resultado_ml['teste']
        prevalencia_pct = resultado_ml['prevalencia'] * 100
        cv_ml = resultado_ml['validacao_cruzada']
        temporal_ml = resultado_ml['temporal']

        c_ml1, c_ml2, c_ml3, c_ml4 = st.columns(4)
        c_ml1.metric(
            "ROC-AUC no teste", br(resultado_ml['auc'], 3),
            f"IC 95%: {br(resultado_ml['auc_ic'][0], 3)} a {br(resultado_ml['auc_ic'][1], 3)}", delta_color="off", delta_arrow="off",
            help="Chance de o modelo dar risco maior a um sinistro grave do que a um não grave. 0,5 equivale ao acaso.",
        )
        c_ml2.metric(
            "PR-AUC no teste", br(resultado_ml['pr_auc'], 3), f"acaso: {br(resultado_ml['prevalencia'], 3)}", delta_color="off", delta_arrow="off",
            help="Precisão média ao longo dos limiares. Sem modelo, ela fica na proporção de casos graves.",
        )
        c_ml3.metric(
            "Sensibilidade", f"{br(teste_ml['sensibilidade'] * 100, 1)}%", "limiar: risco médio", delta_color="off", delta_arrow="off",
            help="Entre os sinistros graves ou fatais do teste, quantos o modelo marcou com risco acima da média do treino.",
        )
        c_ml4.metric(
            "Precisão", f"{br(teste_ml['precisao'] * 100, 1)}%", f"acaso: {br(prevalencia_pct, 1)}%", delta_color="off", delta_arrow="off",
            help="Entre os sinistros marcados com risco acima da média, quantos foram de fato graves ou fatais.",
        )
        st.caption(
            f"Divisão aleatória com {br(resultado_ml['n_teste'])} sinistros de teste. "
            "Sensibilidade e precisão usam como limiar o risco médio do treino, em vez de 50%, que o modelo quase nunca atinge."
        )

        with st.container(border=True):
            st.markdown("#### 🧪 Validação")
            col_val1, col_val2 = st.columns([1, 1.6])
            nomes_metricas = {
                'auc': 'ROC-AUC',
                'pr_auc': 'PR-AUC',
                'brier_skill': 'Ganho no Brier',
                'sensibilidade': 'Sensibilidade',
                'precisao': 'Precisão',
                'acuracia_balanceada': 'Acurácia balanceada',
            }
            with col_val1:
                st.markdown(f"**Validação cruzada** ({DOBRAS_CV} partes × {REPETICOES_CV} repetições)")
                tabela_cv = pd.DataFrame({
                    'Métrica': [nomes_metricas[m] for m in cv_ml.index],
                    'Média ± desvio': [f"{br(l.media, 3)} ± {br(l.desvio, 3)}" for l in cv_ml.itertuples()],
                })
                st.dataframe(tabela_cv, width="stretch", hide_index=True)
                st.caption(
                    f"{br(int(cv_ml['rodadas'].iloc[0]))} treinos com sorteios diferentes. "
                    "Um desvio pequeno indica que as métricas não dependem do sorteio. "
                    "Ganho no Brier: quanto o erro das porcentagens é menor que o de prever sempre a média (0 = nenhum ganho)."
                )
            with col_val2:
                st.markdown("**Validação por ano** (treina com os anos anteriores e testa no ano seguinte)")
                if temporal_ml.empty:
                    st.info("Não há anos suficientes na base para a validação por ano.")
                else:
                    fim_dados = pd.to_datetime(df_completo['data']).max()
                    ano_incompleto = fim_dados.year if (fim_dados.month, fim_dados.day) != (12, 31) else None
                    tabela_temporal = pd.DataFrame({
                        'Ano de teste': [f"{a} (até {fim_dados:%m/%Y})" if a == ano_incompleto else str(a) for a in temporal_ml['ano']],
                        'Treino': temporal_ml['anos_treino'],
                        'Sinistros': temporal_ml['n_teste'],
                        'Graves (%)': temporal_ml['prevalencia'] * 100,
                        'ROC-AUC': temporal_ml['auc'],
                        'PR-AUC': temporal_ml['pr_auc'],
                        'Sensibilidade (%)': temporal_ml['sensibilidade'] * 100,
                        'Precisão (%)': temporal_ml['precisao'] * 100,
                    })
                    st.dataframe(
                        formatar_tabela(tabela_temporal, casas={'Graves (%)': 1, 'ROC-AUC': 3, 'PR-AUC': 3, 'Sensibilidade (%)': 1, 'Precisão (%)': 1}),
                        width="stretch", hide_index=True,
                    )
                    st.caption("Mede se o padrão aprendido no passado vale para os anos seguintes, como aconteceria no uso real.")

    with st.container(border=True):
        st.markdown("#### ⚠️ Limitações do Modelo")
        st.info(
            "**As limitações vêm dos dados, não do modelo.** A regressão logística aproveita as informações "
            "que a base do Infosiga oferece, mas faltam nela fatores decisivos para a gravidade de um sinistro, "
            "como velocidade, alcoolemia, uso de capacete ou cinto e idade dos envolvidos. Sem esses dados, "
            "nenhum modelo consegue estimar a gravidade com mais precisão.",
            icon="ℹ️",
        )
        if resultado_ml is not None:
            leitura_auc = (
                "ordena os sinistros só um pouco melhor que o acaso (0,5)"
                if resultado_ml['auc'] < 0.7
                else "ordena os sinistros melhor que o acaso (0,5), sem bastar para classificar casos individuais"
            )
            desempenho = (
                f"o ROC-AUC de {br(resultado_ml['auc'], 3)} indica que o modelo {leitura_auc}. Com o limiar padrão de 50%, "
                f"a acurácia de {br(resultado_ml['acuracia'] * 100, 1)}% fica perto dos {br(resultado_ml['referencia'] * 100, 1)}% "
                f"de sempre prever \"não grave\". Com o limiar no risco médio, o modelo marca {br(teste_ml['sensibilidade'] * 100, 0)}% "
                f"dos casos graves, mas só {br(teste_ml['precisao'] * 100, 0)}% dos marcados são de fato graves."
            )
            classe_rara = (
                f"desfechos graves ou fatais são {br(prevalencia_pct, 1)}% da base do modelo. O erro das porcentagens do modelo (Brier) "
                f"é só {br(teste_ml['brier_skill'] * 100, 0)}% menor que o de prever sempre a média, e a estimativa do simulador não foi "
                "calibrada, então não deve ser lida como probabilidade real."
            )
            if temporal_ml.empty:
                frase_temporal = "Não há anos suficientes para testar o modelo em anos posteriores ao treino."
            else:
                frase_temporal = (
                    f"Treinado só com anos anteriores, o modelo teve ROC-AUC entre {br(temporal_ml['auc'].min(), 3)} e "
                    f"{br(temporal_ml['auc'].max(), 3)} nos testes de {temporal_ml['ano'].min()} a {temporal_ml['ano'].max()}: "
                    "o padrão se manteve até aqui, o que não garante que continue."
                )
            validacao = (
                f"com {br(resultado_ml['n_total'])} sinistros, as métricas variam entre os sorteios da validação cruzada "
                f"(ROC-AUC {br(cv_ml.loc['auc', 'media'], 3)} ± {br(cv_ml.loc['auc', 'desvio'], 3)}). {frase_temporal}"
            )
        else:
            desempenho = "Não há sinistros suficientes na base comparável para ajustar e avaliar o modelo."
            classe_rara = "Sem modelo ajustado, não há estimativas a interpretar."
            validacao = "Sem conjunto de teste, não há avaliação do modelo."
        st.markdown(f"""
- **Não prevê acidentes:** usa o tipo de sinistro e os veículos envolvidos, informações conhecidas só depois que o sinistro aconteceu. Ele descreve associações com desfecho grave ou fatal, não a chance de um acidente ocorrer.
- **Desempenho:** {desempenho}
- **Classe rara:** {classe_rara}
- **Validação:** {validacao}
- **Variáveis ausentes:** a base não traz velocidade, alcoolemia, uso de capacete ou cinto, idade dos envolvidos nem condição da via. O modelo só sabe se cada tipo de veículo esteve presente, não quantos eram, e a base não liga cada vítima ao seu veículo.
- **Razão de chance não é causa:** cada razão de chance é uma associação ajustada pelas demais variáveis desta base. Fatores ausentes, como velocidade e alcoolemia, podem explicar parte dela. Pedestre envolvido e atropelamento quase sempre aparecem juntos, por isso os intervalos dessas duas variáveis são largos e devem ser lidos em conjunto.
- **Efeitos somados, sem interação:** o modelo supõe que cada fator multiplica a chance da mesma forma em qualquer situação, por exemplo que a moto pesa igual em rodovia e em via urbana. Combinações específicas podem fugir desse padrão.
- **Simulador:** combinações raras ou ausentes na base, como atropelamento com veículo pesado de madrugada, são extrapolação.
- **Uso adequado:** apoio à exploração dos dados. Não serve para decidir sobre casos individuais nem substitui a análise de campo.
""")

    col_ml1, col_ml2 = st.columns([1.1, 1])

    with col_ml1:
        st.markdown("#### 📊 Razões de Chance (IC 95%)")
        if resultado_ml is not None:
            rc = resultado_ml['razoes_chance'].reset_index(names='Variável')
            rc['Nome'] = rc['Variável'].map(lambda x: NOMES_VARIAVEIS_MODELO.get(x, x))
            rc['Leitura'] = [
                'Aumenta a chance' if l.ic_inf > 1 else 'Reduz a chance' if l.ic_sup < 1 else 'Inconclusivo (IC inclui 1)'
                for l in rc.itertuples()
            ]
            rc = rc.sort_values('razao_chance')
            cores_leitura = {'Aumenta a chance': '#d62728', 'Reduz a chance': '#1f77b4', 'Inconclusivo (IC inclui 1)': '#9ca3af'}

            fig_rc = go.Figure()
            for leitura, cor in cores_leitura.items():
                parte = rc[rc['Leitura'] == leitura]
                if parte.empty:
                    continue
                fig_rc.add_trace(go.Scatter(
                    x=parte['razao_chance'],
                    y=parte['Nome'],
                    mode='markers',
                    name=leitura,
                    marker=dict(color=cor, size=10),
                    error_x=dict(
                        type='data', symmetric=False,
                        array=parte['ic_sup'] - parte['razao_chance'],
                        arrayminus=parte['razao_chance'] - parte['ic_inf'],
                        color=cor, thickness=1.5,
                    ),
                    customdata=parte[['ic_inf', 'ic_sup', 'n_casos']],
                    hovertemplate="<b>%{y}</b><br>Razão de chance: %{x:.2f}<br>IC 95%: %{customdata[0]:.2f} a %{customdata[1]:.2f}<br>Casos com a característica: %{customdata[2]:,}<extra></extra>",
                ))
            fig_rc.add_vline(x=1, line_dash='dash', line_color='rgba(0,0,0,0.4)')
            fig_rc.update_layout(
                height=480, margin=dict(l=20, r=20, t=30, b=30),
                xaxis=dict(
                    type='log', title='Razão de chance (escala logarítmica)',
                    tickvals=[0.125, 0.25, 0.5, 1, 2, 4, 8, 16], ticktext=['0,125', '0,25', '0,5', '1', '2', '4', '8', '16'],
                ),
                yaxis=dict(title='', categoryorder='array', categoryarray=rc['Nome'].tolist()),
                legend=dict(orientation='h', yanchor='bottom', y=1.0, x=0),
            )
            mostrar_grafico(fig_rc)
            refs_ml = resultado_ml['referencias']
            st.caption(
                "Cada razão de chance compara sinistros com e sem a característica, mantendo as demais iguais. "
                f"Categorias de referência: {NOMES_REFERENCIA[refs_ml['tipo_via']]}, "
                f"{NOMES_REFERENCIA[refs_ml['tipo_sinistro']]} e {NOMES_REFERENCIA[refs_ml['turno']]}. "
                "Acima de 1, a chance de desfecho grave ou fatal é maior; abaixo de 1, menor. É associação, não causa."
            )
            with st.expander("Tabela das razões de chance"):
                tabela_rc = rc.sort_values('razao_chance', ascending=False)
                st.dataframe(
                    formatar_tabela(
                        pd.DataFrame({
                            'Variável': tabela_rc['Nome'],
                            'Razão de chance': tabela_rc['razao_chance'],
                            'IC 95% inferior': tabela_rc['ic_inf'],
                            'IC 95% superior': tabela_rc['ic_sup'],
                            'Valor-p': tabela_rc['p_valor'],
                            'Sinistros com a característica': tabela_rc['n_casos'],
                        }),
                        casas={'Valor-p': 3},
                    ),
                    width="stretch", hide_index=True,
                )
                st.caption(f"Modelo ajustado nos {br(resultado_ml['n_total'])} sinistros da base comparável com desfecho informado.")

    with col_ml2:
        st.markdown("#### 🧪 Simulador Exploratório de Gravidade")
        st.caption("Estimativa da gravidade supondo que o sinistro ocorreu; não é a chance de ele ocorrer.")

        with st.form("simulador_ml"):
            sim_tipo_sinistro = st.selectbox("Tipo de Sinistro:", options=['COLISAO', 'CHOQUE', 'ATROPELAMENTO', 'OUTROS'])
            sim_tipo_via = st.selectbox("Tipo de Via:", options=['VIAS URBANAS', 'ESTRADAS E RODOVIAS'])
            sim_dia = st.selectbox("Dia da Semana:", options=DIAS_ORDENADOS)
            sim_hora = st.slider("Hora do Dia:", 0, 23, 17, help="O modelo usa o turno correspondente à hora.")
            sim_motos = st.checkbox("🏍️ Envolve Motocicleta", value=True)
            sim_autos = st.checkbox("🚗 Envolve Automóvel", value=True)
            sim_pesado = st.checkbox("🚛 Envolve Caminhão ou Ônibus", value=False)
            sim_pedestres = st.checkbox("🚶 Envolve Pedestre", value=False)
            sim_bike = st.checkbox("🚲 Envolve Bicicleta", value=False)

            submit_sim = st.form_submit_button("Estimar Gravidade do Cenário")

        if submit_sim and resultado_ml is not None:
            sim_turno = "MADRUGADA" if sim_hora < 6 else "MANHA" if sim_hora < 12 else "TARDE" if sim_hora < 18 else "NOITE"
            caso_simulado = pd.DataFrame([{
                'qtd_motocicleta': int(sim_motos),
                'qtd_automovel': int(sim_autos),
                'qtd_caminhao': int(sim_pesado),
                'qtd_onibus': 0,
                'qtd_pedestre': int(sim_pedestres),
                'qtd_bicicleta': int(sim_bike),
                'fim_de_semana': sim_dia in ('Sábado', 'Domingo'),
                'tipo_via': sim_tipo_via,
                'tipo_sinistro': sim_tipo_sinistro,
                'turno': sim_turno,
            }])
            prob_grave = prever_probabilidade(resultado_ml, caso_simulado)[0] * 100
            st.metric(
                "Estimativa do modelo de desfecho grave ou fatal",
                f"{br(prob_grave, 1)}%",
                f"Média da base do modelo: {br(resultado_ml['prevalencia'] * 100, 1)}%",
                delta_color="off", delta_arrow="off",
            )
            st.progress(min(prob_grave / 100.0, 1.0))

    with st.expander("🖼️ Ver Gráfico Estático (razoes_chance_ml.png)"):
        st.image(caminho_grafico("razoes_chance_ml.png"), caption="Figura 5: Razões de chance da regressão logística, com IC 95%", width="stretch", alt="Razões de chance do modelo")

# =============================================================================
# ABA 7: Recomendações & Conclusões
# =============================================================================
with tab7:
    st.subheader("7. Recomendações Estruturadas para Segurança Viária")
    
    st.markdown("""
    As ações abaixo são hipóteses a validar com contagem de tráfego, inspeção em campo e dados de velocidade e alcoolemia, que não constam nesta base:
    """)
    
    col_r1, col_r2, col_r3 = st.columns(3)
    
    with col_r1:
        with st.container(border=True):
            st.markdown("### 🛠️ A. Engenharia de Tráfego")
            st.markdown("""
            - **Choques Urbanos:** Inspeção dos locais de choque em vias urbanas para identificar os objetos atingidos antes de instalar defensas.
            - **Acessos Rodoviários:** Avaliação de sinalização e iluminação nos acessos da SP-310 e SP-326, após inspeção em campo, pois esta base não analisa trevos específicos.
            - **Bolsões para Motociclistas (*Moto Boxes*):** Avaliação de áreas de parada à frente dos semáforos nos cruzamentos de maior fluxo.
            """)
            
    with col_r2:
        with st.container(border=True):
            st.markdown("### 🚔 B. Fiscalização e Monitoramento")
            st.markdown("""
            - **Radares nos Corredores Arteriais:** Monitoramento eletrônico de velocidade nas vias de escoamento industrial nos pontos e horários confirmados por medição de velocidade.
            - **Operações Noturnas de Fim de Semana:** Blitze com etilômetro nas noites de sexta e sábado, quando os registros são mais frequentes. A base não mede alcoolemia.
            - **Fiscalização Integrada com Rodovias:** Trabalho conjunto entre Polícia Militar Urbana e Polícia Militar Rodoviária nos trevos de acesso.
            """)
            
    with col_r3:
        with st.container(border=True):
            st.markdown("### 🎓 C. Educação e Conscientização")
            st.markdown("""
            - **Campanhas com Indústrias Locais:** Parcerias com Marchesan, Baldan, Citrosuco e outras grandes empregadoras para palestras regulares de direção defensiva voltadas a trabalhadores motociclistas.
            - **Equipamentos de Proteção:** Campanhas sobre fixação correta do capacete, calçados adequados e roupas de alta visibilidade.
            - **Sensibilização sobre Obstáculos Fixos:** Campanhas educativas sobre a maior letalidade dos choques em vias urbanas.
            """)

    st.divider()
    st.markdown("### ⚠️ Limitações do Estudo")
    st.markdown("""
    - **Subnotificação de Danos Materiais:** Acidentes de pequena monta acordados amigavelmente sem chamado aos órgãos policiais ou de resgate não entram no sistema Infosiga.
    - **Falta de Variáveis Comportamentais:** A base não audita telemetria (velocidade exata no momento da colisão), dosagem alcoólica ou estado de manutenção veicular.
    - **Notificações:** Quase sempre vêm sem dados de vítimas e veículos, e parte pode repetir sinistros já registrados.
    - **Sem Denominador de Exposição:** Não há fluxo de veículos nem frota, então volumes não medem risco.
    - **Vítima sem Veículo:** A base não indica em qual veículo cada vítima estava.
    - **Campos Vazios:** Contagens vazias viram zero, o que pode subestimar envolvidos.
    """)

# =============================================================================
# ABA 8: Relatório na Íntegra & Dados
# =============================================================================
with tab8:
    st.subheader("8. Documentação Completa e Download dos Dados")
    
    col_d1, col_d2, col_d3 = st.columns(3)
    
    with col_d1:
        csv_limpo = df_completo.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Base Limpa (matao_limpo.csv)",
            data=csv_limpo,
            file_name="matao_limpo.csv",
            mime="text/csv",
            width="stretch"
        )
        
    with col_d2:
        if not df_resumo_anual.empty:
            csv_anual = df_resumo_anual.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Resumo Anual (resumo_anual.csv)",
                data=csv_anual,
                file_name="resumo_anual_matao.csv",
                mime="text/csv",
                width="stretch"
            )
            
    with col_d3:
        if texto_relatorio:
            st.download_button(
                label="📥 Baixar Relatório Executivo (.md)",
                data=texto_relatorio.encode('utf-8'),
                file_name="relatorio_final_matao.md",
                mime="text/markdown",
                width="stretch"
            )

    st.markdown("#### Visualização dos Microdados Filtrados")
    st.dataframe(
        formatar_tabela(
            df_filtrado,
            casas={"latitude": 6, "longitude": 6, "hora_int": 0},
            sem_milhar=["id_sinistro", "ano", "mes", "dia", "hora_int"],
        ),
        width="stretch",
        height=350,
    )
    
    with st.expander("📖 Ler Relatório Executivo Completo na Íntegra (Markdown)", expanded=False):
        if texto_relatorio:
            st.markdown(texto_relatorio)
        else:
            st.write("Arquivo de relatório não encontrado.")

# -----------------------------------------------------------------------------
# Rodapé Institucional
# -----------------------------------------------------------------------------
st.markdown("---")
st.caption(f"Desenvolvido para o Observatório de Trânsito de Matão/SP • Dados Oficiais do Infosiga SP ({PERIODO}) • Tecnologia: Streamlit, Plotly e Scikit-Learn")
