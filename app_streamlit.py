import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats
from sklearn.ensemble import RandomForestClassifier

# -----------------------------------------------------------------------------
# 1. Configuração da Página
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Sinistros de Trânsito — Matão/SP (2015–2026)",
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

# -----------------------------------------------------------------------------
# 2. Carregamento de Dados com Cache
# -----------------------------------------------------------------------------
@st.cache_data
def carregar_dados_principais():
    caminho = "data/matao_limpo.csv"
    if not os.path.exists(caminho):
        st.error(f"Arquivo de dados não encontrado: {caminho}")
        return pd.DataFrame()
    df = pd.read_csv(caminho, parse_dates=["data"])
    return df

@st.cache_data
def carregar_resumo_anual():
    caminho = "output/relatorios/resumo_anual_matao.csv"
    if os.path.exists(caminho):
        return pd.read_csv(caminho)
    return pd.DataFrame()

@st.cache_data
def carregar_texto_relatorio():
    caminho = "output/relatorios/relatorio_final_matao.md"
    if os.path.exists(caminho):
        with open(caminho, "r", encoding="utf-8") as f:
            return f.read()
    return ""

@st.cache_resource
def treinar_modelo_rf(df):
    """Treina modelo Random Forest para predição e importância das features."""
    features_cat = ['tipo_sinistro', 'tipo_via', 'dia_semana', 'turno']
    features_num = ['hora_int', 'mes', 'qtd_motocicleta', 'qtd_automovel', 'qtd_caminhao', 'qtd_pedestre', 'qtd_bicicleta']
    
    df_ml = df[features_cat + features_num + ['gravidade']].dropna().copy()
    if df_ml.empty:
        return None, None, []
        
    X = pd.get_dummies(df_ml[features_cat + features_num], columns=features_cat, drop_first=True)
    y = df_ml['gravidade']
    
    clf = RandomForestClassifier(n_estimators=100, max_depth=8, class_weight='balanced', random_state=42)
    clf.fit(X, y)
    
    importancias = pd.Series(clf.feature_importances_, index=X.columns).sort_values(ascending=True)
    return clf, importancias, X.columns.tolist()

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
    'Sem vítimas': '#2b5c8f'          # Azul
}
ORDEM_GRAVIDADE = ['Com óbito', 'Com feridos graves', 'Com feridos leves', 'Sem vítimas']
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

if anos_selecionados:
    df_filtrado = df_filtrado[df_filtrado["ano"].isin(anos_selecionados)]
if gravidades_selecionadas:
    df_filtrado = df_filtrado[df_filtrado["gravidade"].isin(gravidades_selecionadas)]
if vias_selecionadas:
    df_filtrado = df_filtrado[df_filtrado["tipo_via"].isin(vias_selecionadas)]
if sinistros_selecionados:
    df_filtrado = df_filtrado[df_filtrado["tipo_sinistro"].isin(sinistros_selecionados)]

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

# Informações da base na barra lateral
st.sidebar.divider()
st.sidebar.markdown(f"**Registros Filtrados:** {len(df_filtrado):,} de {len(df_completo):,} ({len(df_filtrado)/len(df_completo)*100:.1f}%)")
st.sidebar.info("""
**Dados Oficiais:**
- **Fonte:** Infosiga SP
- **Município:** Matão / SP
- **Código IBGE:** 3529302
- **Período:** 2015 a 2026 (ago)
""")

# -----------------------------------------------------------------------------
# 4. Cabeçalho Principal e Contexto Executivo
# -----------------------------------------------------------------------------
st.title("🚗 Diagnóstico e Análise de Sinistros de Trânsito — Matão/SP (2015–2026)")
st.markdown("**Observatório de Segurança Viária baseado nos microdados públicos do Infosiga SP**")

with st.container(border=True):
    col_c1, col_c2, col_c3 = st.columns([2, 1, 1])
    with col_c1:
        st.markdown("""
        **Contexto Regional:**  
        Matão é um polo industrial e agrícola estratégico no centro-norte paulista (~85 mil hab.), sediando grandes indústrias 
        (Marchesan, Baldan, Citrosuco) e cortado por duas rodovias estaduais de intenso tráfego: **SP-310 (Washington Luís)** e **SP-326 (Brigadeiro Faria Lima)**.
        """)
    with col_c2:
        st.markdown("""
        **Desafio Viário:**  
        Forte convivência entre carretas de carga pesada, intensa frota de motocicletas para trabalhadores fabris e travessias urbanas.
        """)
    with col_c3:
        st.markdown("""
        **Objetivo:**  
        Mapear pontos críticos, sazonalidade, letalidade por modal e subsidiar políticas públicas de engenharia e fiscalização.
        """)

# Alerta sobre ressalva metodológica de 2019
st.info("""
ℹ️ **Ressalva Metodológica Fundamental:**  
Entre **2015 e 2018**, o Infosiga registrava exclusivamente sinistros com **óbito**. A partir de **2019**, com a integração de dados da Polícia Militar, SAMU e Bombeiros, foram incorporados os sinistros não fatais (feridos graves, leves e sem vítimas).  
Portanto, a série histórica de **óbitos é contínua e comparável de 2015 a 2026**, enquanto o volume total de sinistros reflete a base consolidada a partir de 2019.
""")

# -----------------------------------------------------------------------------
# 5. Painel de Indicadores Chave (KPIs)
# -----------------------------------------------------------------------------
total_reg = len(df_filtrado)
obitos = int(df_filtrado["mortos"].sum())
f_graves = int(df_filtrado["feridos_graves"].sum())
f_leves = int(df_filtrado["feridos_leves"].sum())
sem_vit = int((df_filtrado["gravidade"] == "Sem vítimas").sum())
taxa_letalidade = (obitos / total_reg * 100) if total_reg > 0 else 0.0
sinistros_motos = int((df_filtrado["qtd_motocicleta"] > 0).sum())
pct_motos = (sinistros_motos / total_reg * 100) if total_reg > 0 else 0.0

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("Total de Sinistros", f"{total_reg:,}")
col2.metric("Vítimas Fatais (Óbitos)", f"{obitos}", delta=f"{taxa_letalidade:.1f}% letalidade", delta_color="inverse")
col3.metric("Feridos Graves", f"{f_graves}")
col4.metric("Feridos Leves", f"{f_leves}")
col5.metric("Sem Vítimas (Danos)", f"{sem_vit}")
col6.metric("Envolve Moto", f"{sinistros_motos}", delta=f"{pct_motos:.1f}% dos sinistros", delta_color="off")

st.markdown("---")

# -----------------------------------------------------------------------------
# 6. Abas Temáticas com Todos os Resultados do Relatório
# -----------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📊 Evolução & Gravidade",
    "⚡ Tipos & Choque Crítico",
    "🏍️ Modais & Vulnerabilidade",
    "⏱️ Padrões Temporais & Teste t",
    "🗺️ Geografia do Risco (Mapa)",
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
        dados_ano = df_completo.groupby('ano').agg(
            total_sinistros=('id_sinistro', 'count'),
            obitos=('mortos', 'sum')
        ).reset_index()
        
        fig_ano = go.Figure()
        # Barras
        fig_ano.add_trace(go.Bar(
            x=dados_ano['ano'],
            y=dados_ano['total_sinistros'],
            name='Total de Sinistros Registrados',
            marker_color='#2b5c8f',
            opacity=0.85,
            text=dados_ano['total_sinistros'],
            textposition='auto',
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
            title="<b>Evolução dos Sinistros e Fatalidades em Matão/SP (2015–2026)</b>",
            xaxis=dict(title="Ano", tickmode='linear', tick0=2015, dtick=1),
            yaxis=dict(title="Total de Sinistros", showgrid=True),
            yaxis2=dict(
                title="Vítimas Fatais",
                overlaying='y',
                side='right',
                showgrid=False,
                range=[0, dados_ano['obitos'].max() * 1.5]
            ),
            legend=dict(x=0.01, y=0.99, bgcolor='rgba(255,255,255,0.8)'),
            margin=dict(l=40, r=40, t=50, b=40),
            height=420
        )
        st.plotly_chart(fig_ano, width="stretch")
        st.caption("* 2015–2018: Apenas sinistros fatais constavam no sistema Infosiga. A partir de 2019 houve incorporação ampla de ocorrências.")

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
        fig_donut.update_traces(textinfo='percent+label', pull=[0.05, 0, 0, 0])
        fig_donut.update_layout(
            margin=dict(l=20, r=20, t=50, b=20),
            showlegend=False,
            height=420
        )
        st.plotly_chart(fig_donut, width="stretch")

    st.markdown("#### Resumo Estatístico Anual Consolidado (Oficial)")
    if not df_resumo_anual.empty:
        colunas_format = {
            "ano": "Ano",
            "total_sinistros": "Total Sinistros",
            "obitos": "Óbitos",
            "feridos_graves": "Feridos Graves",
            "feridos_leves": "Feridos Leves",
            "ilesos": "Ilesos"
        }
        df_show_anual = df_resumo_anual.rename(columns=colunas_format)
        st.dataframe(df_show_anual, width="stretch", hide_index=True)
    
    with st.expander("🖼️ Ver Gráfico Estático Publicado no Relatório (acidentes_por_ano.png)"):
        if os.path.exists("output/graficos/acidentes_por_ano.png"):
            st.image("output/graficos/acidentes_por_ano.png", caption="Figura 1: Evolução anual dos sinistros e fatalidades (Matplotlib)", width="stretch", alt="Evolução anual dos sinistros")

# =============================================================================
# ABA 2: Tipos de Sinistro & Choque Crítico
# =============================================================================
with tab2:
    st.subheader("2. Tipos de Sinistro e a Gravidade Extrema do Choque contra Obstáculos Fixos")
    
    st.markdown("""
    > ⚠️ **Destaque do Relatório:** Embora colisões sejam o evento mais volumoso em Matão, **o choque contra obstáculo fixo (postes, árvores, muretas) é quase 4 vezes mais letal que uma colisão veicular**. Quase **1 a cada 7 choques resulta em morte (14,14%)**, apontando para excesso de velocidade, perda de controle e falta de defensas metálicas protetoras.
    """)
    
    # Construção da tabela de letalidade oficial
    tipos_rel = df_completo['tipo_sinistro'].value_counts().index
    tab_letal = df_completo.groupby('tipo_sinistro').agg(
        total_ocorrencias=('id_sinistro', 'count'),
        obitos=('mortos', 'sum'),
        feridos_graves=('feridos_graves', 'sum')
    ).reindex(tipos_rel).reset_index()
    
    tab_letal['taxa_letalidade_pct'] = ((tab_letal['obitos'] / tab_letal['total_ocorrencias']) * 100).round(2)
    tab_letal = tab_letal.sort_values(by='taxa_letalidade_pct', ascending=False)
    
    col_t2a, col_t2b = st.columns([3, 2])
    
    with col_t2a:
        fig_letal = px.bar(
            tab_letal,
            x='tipo_sinistro',
            y='taxa_letalidade_pct',
            color='taxa_letalidade_pct',
            color_continuous_scale='Reds',
            text='taxa_letalidade_pct',
            title="<b>Taxa de Letalidade (%) por Tipo de Sinistro</b>",
            labels={'taxa_letalidade_pct': 'Letalidade (% óbitos)', 'tipo_sinistro': 'Tipo de Sinistro'}
        )
        fig_letal.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
        fig_letal.update_layout(
            margin=dict(l=20, r=20, t=50, b=40),
            coloraxis_showscale=False,
            height=380
        )
        st.plotly_chart(fig_letal, width="stretch")
        
    with col_t2b:
        fig_vol = px.bar(
            tab_letal.sort_values(by='total_ocorrencias', ascending=True),
            x='total_ocorrencias',
            y='tipo_sinistro',
            orientation='h',
            text='total_ocorrencias',
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
        st.plotly_chart(fig_vol, width="stretch")

    st.markdown("#### Tabela Comparativa de Severidade por Tipo de Sinistro")
    st.dataframe(
        tab_letal.rename(columns={
            'tipo_sinistro': 'Tipo de Sinistro',
            'total_ocorrencias': 'Total de Ocorrências',
            'obitos': 'Óbitos',
            'feridos_graves': 'Feridos Graves',
            'taxa_letalidade_pct': 'Taxa de Letalidade (%)'
        }),
        width="stretch",
        hide_index=True
    )

# =============================================================================
# ABA 3: Modais & Vulnerabilidade
# =============================================================================
with tab3:
    st.subheader("3. Modais de Transporte: A Vulnerabilidade Extrema da Motocicleta")
    
    st.markdown("""
    Na análise de modais em Matão:
    - **Automóveis** estiveram presentes em 1.480 acidentes (36,3%).
    - **Motocicletas** estiveram presentes em 1.375 acidentes (33,8%).
    - **Caminhões** estiveram em 208 acidentes (5,1%), pedestres em 112 (2,7%) e bicicletas em 88 (2,2%).
    
    O protagonismo da motocicleta reflete o deslocamento diário de trabalhadores das indústrias locais, sendo o fator que mais eleva a severidade clínica dos acidentes.
    """)
    
    col_t3a, col_t3b = st.columns([1, 1])
    
    with col_t3a:
        # Presença de modais
        total_sin = len(df_filtrado)
        modais_dict = {
            'Automóvel': int((df_filtrado['qtd_automovel'] > 0).sum()),
            'Motocicleta': int((df_filtrado['qtd_motocicleta'] > 0).sum()),
            'Caminhão': int((df_filtrado['qtd_caminhao'] > 0).sum()),
            'Pedestre': int((df_filtrado['qtd_pedestre'] > 0).sum()),
            'Bicicleta': int((df_filtrado['qtd_bicicleta'] > 0).sum()),
            'Ônibus': int((df_filtrado['qtd_onibus'] > 0).sum())
        }
        df_modais = pd.DataFrame(list(modais_dict.items()), columns=['Modal', 'Qtd_Sinistros']).sort_values(by='Qtd_Sinistros', ascending=True)
        df_modais['Percentual'] = (df_modais['Qtd_Sinistros'] / total_sin * 100).round(1) if total_sin > 0 else 0
        
        fig_mod = px.bar(
            df_modais,
            x='Qtd_Sinistros',
            y='Modal',
            orientation='h',
            text=df_modais.apply(lambda r: f"{r['Qtd_Sinistros']} ({r['Percentual']}%)", axis=1),
            color='Modal',
            color_discrete_sequence=['#fa8431'],
            title="<b>Presença dos Modais nos Sinistros</b>"
        )
        fig_mod.update_traces(textposition='outside')
        fig_mod.update_layout(showlegend=False, height=380, margin=dict(l=20, r=40, t=50, b=20))
        st.plotly_chart(fig_mod, width="stretch")
        
    with col_t3b:
        # Comparativo: Com Moto vs Sem Moto em relação à gravidade
        df_filtrado_comp = df_filtrado.copy()
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
            text=df_motos_melt['Percentual'].apply(lambda v: f"{v:.1f}%" if v > 4 else ""),
            title="<b>Perfil de Gravidade: Com Moto vs Sem Moto</b>"
        )
        fig_comp.update_layout(height=380, margin=dict(l=20, r=20, t=50, b=20), yaxis=dict(title="% do Total do Grupo"))
        st.plotly_chart(fig_comp, width="stretch")

    with st.expander("🖼️ Ver Gráfico Estático Publicado (tipos_e_veiculos.png)"):
        if os.path.exists("output/graficos/tipos_e_veiculos.png"):
            st.image("output/graficos/tipos_e_veiculos.png", caption="Figura 2: Tipos de sinistro e veículos envolvidos (Matplotlib)", width="stretch", alt="Tipos de sinistro e veículos")

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
        
        # Destacar os 3 horários de pico (17h, 18h, 13h)
        top_horas = contagem_h.nlargest(3, 'Qtd_Sinistros')['Hora'].tolist()
        contagem_h['Cor'] = contagem_h['Hora'].apply(lambda h: '#de2d26' if h in top_horas else '#3182bd')
        
        fig_hora = px.bar(
            contagem_h,
            x='Hora',
            y='Qtd_Sinistros',
            title="<b>Distribuição por Hora do Dia (Destaque nos Picos)</b>",
            text='Qtd_Sinistros'
        )
        fig_hora.update_traces(marker_color=contagem_h['Cor'], textposition='outside')
        fig_hora.update_layout(
            xaxis=dict(tickmode='linear', dtick=2, title="Hora do Dia (0h–23h)"),
            yaxis=dict(title="Quantidade de Sinistros"),
            height=380,
            margin=dict(l=20, r=20, t=50, b=30)
        )
        st.plotly_chart(fig_hora, width="stretch")
        st.caption("Pico absoluto às **17h** (saída fabril e comercial), seguido pelas **18h** e pelo pico secundário do almoço às **13h**.")
        
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
            title="<b>Sinistros por Dia da Semana e Gravidade</b>",
            xaxis=dict(title="Dia da Semana"),
            yaxis=dict(title="Total de Sinistros"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=380,
            margin=dict(l=20, r=20, t=60, b=30)
        )
        st.plotly_chart(fig_dia, width="stretch")

    # Heatmap Interativo Dia da Semana vs Hora do Dia
    st.markdown("#### Mapa de Calor Interativo: Dia da Semana vs Hora do Dia")
    if not df_hora.empty:
        heatmap_data = df_hora.pivot_table(
            index='dia_semana',
            columns='hora_int',
            values='id_sinistro',
            aggfunc='count',
            fill_value=0
        ).reindex(DIAS_ORDENADOS)
        
        fig_heat = px.imshow(
            heatmap_data,
            labels=dict(x="Hora do Dia", y="Dia da Semana", color="Sinistros"),
            x=list(range(24)),
            y=[d.replace('-feira', '') for d in DIAS_ORDENADOS],
            color_continuous_scale="YlOrRd",
            aspect="auto",
            text_auto=True
        )
        fig_heat.update_layout(height=320, margin=dict(l=40, r=20, t=30, b=30))
        st.plotly_chart(fig_heat, width="stretch")

    # Painel do Teste Estatístico
    with st.container(border=True):
        st.markdown("#### 🔬 Teste de Hipótese Estatística (t de Student - Welch)")
        st.markdown("**Pergunta de Pesquisa:** Há diferença estatisticamente significativa no volume diário de acidentes entre dias úteis e finais de semana?")
        
        df_rec = df_completo[df_completo['ano'] >= 2019].copy()
        sinistros_diarios = df_rec.groupby(['data', 'fim_de_semana']).size().reset_index(name='qtd')
        uteis = sinistros_diarios[sinistros_diarios['fim_de_semana'] == False]['qtd']
        fds = sinistros_diarios[sinistros_diarios['fim_de_semana'] == True]['qtd']
        
        t_stat, p_val = stats.ttest_ind(uteis, fds, equal_var=False)
        
        c_stat1, c_stat2, c_stat3, c_stat4 = st.columns(4)
        c_stat1.metric("Média em Dias Úteis", f"{uteis.mean():.2f} acid/dia", f"DP: {uteis.std():.2f}")
        c_stat2.metric("Média em Fins de Semana", f"{fds.mean():.2f} acid/dia", f"DP: {fds.std():.2f}")
        c_stat3.metric("Estatística t", f"{t_stat:.4f}")
        c_stat4.metric("p-valor", f"{p_val:.4f}", delta="p > 0.05 (H0 mantida)", delta_color="off")
        
        st.markdown(f"""
        **Interpretação Científica:**  
        Com **p-valor = {p_val:.2f} (> 0.05)**, conclui-se que **não há diferença estatisticamente significativa** na média diária total de acidentes entre dias de semana e fins de semana.  
        A distinção crucial é **comportamental e temporal**: nos dias úteis, os sinistros concentram-se no horário comercial e de término de expediente fabril (17h–19h); nos finais de semana, dispersam-se pela noite e madrugada (associados a entretenimento e alcoolemia).
        """)

    with st.expander("🖼️ Ver Gráficos Estáticos Publicados (heatmap_dia_hora.png e acidentes_dia_e_hora.png)"):
        col_img1, col_img2 = st.columns(2)
        with col_img1:
            if os.path.exists("output/graficos/heatmap_dia_hora.png"):
                st.image("output/graficos/heatmap_dia_hora.png", caption="Mapa de calor original", width="stretch", alt="Mapa de calor")
        with col_img2:
            if os.path.exists("output/graficos/acidentes_dia_e_hora.png"):
                st.image("output/graficos/acidentes_dia_e_hora.png", caption="Distribuição de dia e hora original", width="stretch", alt="Acidentes dia e hora")

# =============================================================================
# ABA 5: Geografia do Risco (Mapa Interativo & Vias Críticas)
# =============================================================================
with tab5:
    st.subheader("5. Geografia do Risco Viário em Matão/SP")
    
    st.markdown("""
    O mapeamento geoespacial evidencia **dois comportamentos espaciais distintos**:
    1. **Malha Urbana Central e Bairros:** Densa concentração de acidentes, porém com predomínio de danos materiais e ferimentos leves (menor velocidade operacional).
    2. **Eixos Rodoviários (SP-310 Washington Luís e SP-326 Faria Lima) e Trevos:** Concentram a quase totalidade dos sinistros fatais. Zonas de risco extremo: trevos da Av. Baldan, Av. Trolesi e entroncamento do Distrito Industrial Adolfo Baldan.
    """)
    
    # Mapa Interativo Plotly com Carto Positron
    df_geo = df_filtrado.dropna(subset=['latitude', 'longitude']).copy()
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
            title=f"<b>Mapeamento dos Sinistros de Trânsito ({len(df_geo):,} pontos georreferenciados)</b>"
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
        st.plotly_chart(fig_map, width="stretch")
    else:
        st.warning("Nenhum registro com coordenadas válidas para os filtros selecionados.")

    st.markdown("#### Ranking das 10 Vias com Mais Sinistros em Matão")
    ranking_vias = df_completo.groupby('logradouro').agg(
        total_sinistros=('id_sinistro', 'count'),
        obitos=('mortos', 'sum'),
        feridos_graves=('feridos_graves', 'sum'),
        feridos_leves=('feridos_leves', 'sum')
    ).sort_values(by='total_sinistros', ascending=False).head(10).reset_index()
    
    col_v1, col_v2 = st.columns([3, 2])
    with col_v1:
        st.dataframe(
            ranking_vias.rename(columns={
                'logradouro': 'Via / Logradouro',
                'total_sinistros': 'Total de Sinistros',
                'obitos': 'Óbitos',
                'feridos_graves': 'Feridos Graves',
                'feridos_leves': 'Feridos Leves'
            }),
            width="stretch",
            hide_index=True
        )
    with col_v2:
        fig_rank = px.bar(
            ranking_vias.sort_values(by='total_sinistros', ascending=True),
            x='total_sinistros',
            y='logradouro',
            orientation='h',
            title="<b>Top Vias Mais Críticas</b>",
            color_discrete_sequence=['#2b5c8f']
        )
        fig_rank.update_layout(height=360, margin=dict(l=20, r=20, t=40, b=20), yaxis=dict(title=""))
        st.plotly_chart(fig_rank, width="stretch")

    with st.expander("🖼️ Ver Mapa Estático Publicado (mapa_estatico_matao.png)"):
        if os.path.exists("output/graficos/mapa_estatico_matao.png"):
            st.image("output/graficos/mapa_estatico_matao.png", caption="Mapa estático de calor e pontos em Matão/SP", width="stretch", alt="Mapa estático de Matão")

# =============================================================================
# ABA 6: Machine Learning & Simulador
# =============================================================================
with tab6:
    st.subheader("6. Modelagem Preditiva Supervisionada (Random Forest Classifier)")
    
    st.markdown("""
    Treinou-se um classificador supervisionado (**Random Forest**) para prever a gravidade clínica do sinistro com base nas características ambientais, temporais e veiculares.
    O modelo atingiu **acurácia de 79%** no conjunto de teste com balanceamento de pesos de classe.
    """)
    
    clf, importancias, features_list = treinar_modelo_rf(df_completo)
    
    col_ml1, col_ml2 = st.columns([1, 1])
    
    with col_ml1:
        st.markdown("#### Top 10 Variáveis Mais Importantes (Gini Importance)")
        if importancias is not None:
            top_10_imp = importancias.tail(10).reset_index()
            top_10_imp.columns = ['Feature', 'Importancia']
            
            fig_imp = px.bar(
                top_10_imp,
                x='Importancia',
                y='Feature',
                orientation='h',
                color='Importancia',
                color_continuous_scale='Blues',
                title="<b>Gini Importance no Random Forest</b>"
            )
            fig_imp.update_layout(
                coloraxis_showscale=False,
                height=380,
                margin=dict(l=20, r=20, t=40, b=20),
                xaxis=dict(title="Importância Relativa"),
                yaxis=dict(title="")
            )
            st.plotly_chart(fig_imp, width="stretch")
            st.caption("A variável **`qtd_motocicleta`** desponta isolada como o fator mais determinante para o desfecho de gravidade, superando horário e tipo de via.")
    
    with col_ml2:
        st.markdown("#### 🧪 Simulador Interativo de Risco de Sinistro")
        st.caption("Altere os parâmetros para consultar a predição da gravidade pelo modelo treinado:")
        
        with st.form("simulador_ml"):
            sim_tipo_sinistro = st.selectbox("Tipo de Sinistro:", options=['COLISAO', 'CHOQUE', 'ATROPELAMENTO', 'OUTROS'])
            sim_tipo_via = st.selectbox("Tipo de Via:", options=['VIAS URBANAS', 'ESTRADAS E RODOVIAS'])
            sim_dia = st.selectbox("Dia da Semana:", options=DIAS_ORDENADOS)
            sim_hora = st.slider("Hora do Dia:", 0, 23, 17)
            sim_motos = st.number_input("Qtd de Motocicletas Envolvidas:", min_value=0, max_value=5, value=1)
            sim_autos = st.number_input("Qtd de Automóveis Envolvidos:", min_value=0, max_value=5, value=1)
            sim_caminhao = st.number_input("Qtd de Caminhões Envolvidos:", min_value=0, max_value=3, value=0)
            
            submit_sim = st.form_submit_button("Calcular Risco do Cenário")
            
        if submit_sim and clf is not None:
            # Montar vetor de predição
            sim_turno = "NOITE" if sim_hora >= 18 or sim_hora < 6 else "TARDE" if sim_hora >= 12 else "MANHA"
            
            # Criar DataFrame com uma linha
            input_dict = {f: 0 for f in features_list}
            input_dict['hora_int'] = sim_hora
            input_dict['mes'] = 6
            input_dict['qtd_motocicleta'] = sim_motos
            input_dict['qtd_automovel'] = sim_autos
            input_dict['qtd_caminhao'] = sim_caminhao
            input_dict['qtd_pedestre'] = 0
            input_dict['qtd_bicicleta'] = 0
            
            if f"tipo_sinistro_{sim_tipo_sinistro}" in input_dict:
                input_dict[f"tipo_sinistro_{sim_tipo_sinistro}"] = 1
            if f"tipo_via_{sim_tipo_via}" in input_dict:
                input_dict[f"tipo_via_{sim_tipo_via}"] = 1
            if f"dia_semana_{sim_dia}" in input_dict:
                input_dict[f"dia_semana_{sim_dia}"] = 1
            if f"turno_{sim_turno}" in input_dict:
                input_dict[f"turno_{sim_turno}"] = 1
                
            input_df = pd.DataFrame([input_dict])
            pred_classe = clf.predict(input_df)[0]
            probas = clf.predict_proba(input_df)[0]
            classes = clf.classes_
            
            st.markdown(f"**Resultado da Simulação:**")
            if pred_classe == "Com óbito":
                st.error(f"🚨 Gravidade Prevista: **{pred_classe}** (Alto Risco de Fatalidade)")
            elif pred_classe == "Com feridos graves":
                st.warning(f"⚠️ Gravidade Prevista: **{pred_classe}**")
            else:
                st.success(f"ℹ️ Gravidade Prevista: **{pred_classe}**")
                
            df_prob = pd.DataFrame({'Gravidade': classes, 'Probabilidade (%)': (probas * 100).round(1)})
            st.dataframe(df_prob, width="stretch", hide_index=True)

    with st.expander("🖼️ Ver Gráfico Estático Publicado (importancia_features_ml.png)"):
        if os.path.exists("output/graficos/importancia_features_ml.png"):
            st.image("output/graficos/importancia_features_ml.png", caption="Figura 5: Importância das variáveis no Random Forest", width="stretch", alt="Importância das features")

# =============================================================================
# ABA 7: Recomendações & Conclusões
# =============================================================================
with tab7:
    st.subheader("7. Recomendações Estruturadas para Segurança Viária")
    
    st.markdown("""
    Com base nas evidências empíricas levantadas ao longo de mais de uma década de dados, propõem-se ações alinhadas aos três pilares da segurança no trânsito:
    """)
    
    col_r1, col_r2, col_r3 = st.columns(3)
    
    with col_r1:
        with st.container(border=True):
            st.markdown("### 🛠️ A. Engenharia de Tráfego")
            st.markdown("""
            - **Atenuação de Impacto em Obstáculos Fixos:** Mapeamento de postes e árvores sem recuo no leito carroçável das avenidas arteriais de Matão, instalando defensas metálicas ou barreiras absorvedoras de impacto.
            - **Readequação Geométrica dos Trevos:** Melhoria na sinalização horizontal refletiva e reforço de iluminação nos acessos da SP-310 e SP-326 ao perímetro urbano.
            - **Bolsões para Motociclistas (*Moto Boxes*):** Implantação de áreas de parada exclusivas à frente dos semáforos nos cruzamentos de maior fluxo para reduzir colisões com automóveis.
            """)
            
    with col_r2:
        with st.container(border=True):
            st.markdown("### 🚔 B. Fiscalização e Monitoramento")
            st.markdown("""
            - **Radares nos Corredores Arteriais:** Monitoramento eletrônico de velocidade nas vias de escoamento industrial durante as janelas críticas de pico (17h–19h e 12h–13h).
            - **Operações Noturnas de Fim de Semana:** Blitze com etilômetro direcionadas às noites de sexta, sábado e domingo, combatendo alcoolemia e manobras arriscadas.
            - **Fiscalização Integrada com Rodovias:** Trabalho conjunto entre Polícia Militar Urbana e Polícia Militar Rodoviária nos trevos de acesso.
            """)
            
    with col_r3:
        with st.container(border=True):
            st.markdown("### 🎓 C. Educação e Conscientização")
            st.markdown("""
            - **Campanhas com Indústrias Locais:** Parcerias com Marchesan, Baldan, Citrosuco e outras grandes empregadoras para palestras regulares de direção defensiva voltadas a trabalhadores motociclistas.
            - **Equipamentos de Proteção:** Campanhas sobre fixação correta do capacete, calçados adequados e roupas de alta visibilidade.
            - **Sensibilização sobre Obstáculos Fixos:** Campanhas educativas alertando sobre o risco desproporcional de morte no choque contra postes e árvores.
            """)

    st.divider()
    st.markdown("### ⚠️ Limitações do Estudo")
    st.markdown("""
    - **Subnotificação de Danos Materiais:** Acidentes de pequena monta acordados amigavelmente sem chamado aos órgãos policiais ou de resgate não entram no sistema Infosiga.
    - **Falta de Variáveis Comportamentais:** A base não audita telemetria (velocidade exata no momento da colisão), dosagem alcoólica ou estado de manutenção veicular.
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
    st.dataframe(df_filtrado, width="stretch", height=350)
    
    with st.expander("📖 Ler Relatório Executivo Completo na Íntegra (Markdown)", expanded=False):
        if texto_relatorio:
            st.markdown(texto_relatorio)
        else:
            st.write("Arquivo de relatório não encontrado.")

# -----------------------------------------------------------------------------
# Rodapé Institucional
# -----------------------------------------------------------------------------
st.markdown("---")
st.caption("Desenvolvido para o Observatório de Trânsito de Matão/SP • Dados Oficiais do Infosiga SP (2015–2026) • Tecnologia: Streamlit, Plotly e Scikit-Learn")
