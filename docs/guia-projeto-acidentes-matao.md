# Guia de Projeto: Análise de Acidentes de Trânsito em Matão/SP

## 1. Compreensão do Negócio e Definição de Objetivos

Antes de tocar nos dados, defina claramente o que deseja responder. Exemplos de perguntas para este projeto:

- Quais são os tipos mais comuns de acidentes em Matão?
- Existem horários ou dias da semana com maior incidência?
- Quais são as vias ou regiões mais críticas?
- Qual a gravidade dos acidentes (com/sem vítimas, óbitos)?
- Houve alguma tendência ao longo dos anos?
- É possível prever a gravidade de um acidente com base nas condições?

> **Dica:** Escolha 3 a 5 perguntas principais. Isso manterá seu projeto focado e evitará que você se perca no volume de dados.

## 2. Configuração do Ambiente Python

Recomendo utilizar **Jupyter Notebook** ou **VS Code com extensão Jupyter** para acompanhar este guia. As bibliotecas essenciais são:

```bash
pip install pandas numpy matplotlib seaborn plotly scikit-learn geopandas
```

Ou, se preferir usar o **Anaconda**, a maioria já vem instalada.

### Estrutura de pastas sugerida para o projeto:

```
projeto-acidentes-matao/
├── data/
│   └── sinistros_sp.csv          # Seu arquivo original
├── notebooks/
│   ├── 01-exploracao.ipynb
│   ├── 02-limpeza.ipynb
│   ├── 03-analise-matao.ipynb
│   └── 04-visualizacoes.ipynb
├── output/
│   ├── graficos/
│   └── relatorios/
└── README.md
```

---

## 3. Carregamento e Primeira Exploração dos Dados

### Passo 3.1: Leitura do arquivo CSV

```python
import pandas as pd
import numpy as np

# Ajuste o caminho conforme a localização do seu arquivo
df = pd.read_csv('data/sinistros_sp.csv')

# Verifique as primeiras linhas
print(df.head())
```

> **O que observar:** Nomes das colunas, separador decimal (vírgula ou ponto), codificação do arquivo (se der erro de caracteres estranhos, use `encoding='latin1'` ou `encoding='utf-8'`).

### Passo 3.2: Conhecendo a estrutura

```python
# Informações gerais: tipos de dados, valores nulos, memória usada
print(df.info())

# Estatísticas descritivas das colunas numéricas
print(df.describe())

# Dimensões do dataset
print(f"Total de registros: {df.shape[0]}")
print(f"Total de colunas: {df.shape[1]}")
```

### Passo 3.3: Identifique a coluna da cidade

Você precisa descobrir como a cidade é representada no dataset. Geralmente pode se chamar `municipio`, `cidade`, `localidade` ou similar.

```python
# Liste todas as colunas
print(df.columns.tolist())

# Veja valores únicos que possam indicar a coluna de município
for col in df.columns:
    if df[col].dtype == 'object':
        amostra = df[col].dropna().unique()[:5]
        print(f"{col}: {amostra}")
```

---

## 4. Limpeza e Preparação dos Dados (Data Cleaning)

### Passo 4.1: Filtrar apenas os registros de Matão

Supondo que a coluna se chame `municipio`:

```python
# Verifique se existe Matão nos dados (atenção a acentuação e caixa alta/baixa)
print(df['municipio'].unique())

# Filtrar
matao_variants = ['MATÃO', 'MATAO', 'Matão', 'Matao']
df_matao = df[df['municipio'].isin(matao_variants)].copy()

print(f"Registros de Matão: {len(df_matao)}")
```

> **Dica:** Se Matão não aparecer, pode estar escrito de outra forma ou o dataset pode ter apenas código de município (IBGE). Nesse caso, use o código IBGE de Matão: **3529302**.

### Passo 4.2: Padronização de colunas principais

Trabalhe com cópias para não perder os dados originais:

```python
# Renomeie colunas para facilitar (exemplo)
df_matao.rename(columns={
    'data_inversa': 'data',
    'horario': 'hora',
    'dia_semana': 'dia_semana',
    'tipo_acidente': 'tipo',
    'classificacao_acidente': 'classificacao',
    'feridos_leves': 'feridos_leves',
    'feridos_graves': 'feridos_graves',
    'mortos': 'mortos',
    'ilesos': 'ilesos',
    'latitude': 'latitude',
    'longitude': 'longitude',
    'br': 'rodovia',
    'km': 'quilometragem'
}, inplace=True)
```

### Passo 4.3: Tratamento de dados faltantes

```python
# Quantidade de nulos por coluna
print(df_matao.isnull().sum())

# Estratégias comuns:
# - Colunas com muitos nulos e pouca relevância: remover
# - Coordenadas (latitude/longitude): se forem essenciais para mapa, remova registros sem elas
# - Horário: pode ser preenchido com um valor padrão ou deixado como desconhecido
# - Número de vítimas: preencher com 0, assumindo que nulo = nenhuma

df_matao['feridos_leves'] = df_matao['feridos_leves'].fillna(0)
df_matao['feridos_graves'] = df_matao['feridos_graves'].fillna(0)
df_matao['mortos'] = df_matao['mortos'].fillna(0)
df_matao['ilesos'] = df_matao['ilesos'].fillna(0)
```

### Passo 4.4: Conversão de tipos de dados

```python
# Converter data para datetime
df_matao['data'] = pd.to_datetime(df_matao['data'], errors='coerce')

# Extrair componentes úteis
df_matao['ano'] = df_matao['data'].dt.year
df_matao['mes'] = df_matao['data'].dt.month
df_matao['dia'] = df_matao['data'].dt.day

# Converter hora para número de horas (inteiro), se aplicável
df_matao['hora_int'] = pd.to_datetime(df_matao['hora'], format='%H:%M', errors='coerce').dt.hour
```

### Passo 4.5: Criar colunas derivadas

```python
# Total de vítimas
df_matao['total_vitimas'] = (
    df_matao['feridos_leves'] + df_matao['feridos_graves'] + df_matao['mortos']
)

# Classificação simplificada de gravidade
def classificar_gravidade(row):
    if row['mortos'] > 0:
        return 'Com óbito'
    elif row['feridos_graves'] > 0:
        return 'Com feridos graves'
    elif row['feridos_leves'] > 0:
        return 'Com feridos leves'
    else:
        return 'Sem vítimas'

df_matao['gravidade'] = df_matao.apply(classificar_gravidade, axis=1)
```

---

## 5. Análise Exploratória de Dados (EDA)

A EDA é o coração do projeto. Explore visualmente e estatisticamente os dados de Matão.

### 5.1 Distribuição temporal dos acidentes

```python
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")

# Acidentes por ano
plt.figure(figsize=(10, 5))
df_matao['ano'].value_counts().sort_index().plot(kind='bar')
plt.title('Acidentes por Ano em Matão')
plt.xlabel('Ano')
plt.ylabel('Quantidade')
plt.tight_layout()
plt.savefig('output/graficos/acidentes_por_ano.png')
plt.show()

# Acidentes por dia da semana
ordem_dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
plt.figure(figsize=(10, 5))
df_matao['dia_semana'].value_counts().reindex(ordem_dias).plot(kind='bar')
plt.title('Acidentes por Dia da Semana em Matão')
plt.tight_layout()
plt.savefig('output/graficos/acidentes_por_dia.png')
plt.show()

# Acidentes por hora do dia
plt.figure(figsize=(12, 5))
df_matao['hora_int'].value_counts().sort_index().plot(kind='bar')
plt.title('Acidentes por Hora do Dia em Matão')
plt.xlabel('Hora')
plt.tight_layout()
plt.savefig('output/graficos/acidentes_por_hora.png')
plt.show()
```

### 5.2 Tipos de acidentes e gravidade

```python
# Tipos mais comuns
plt.figure(figsize=(12, 6))
df_matao['tipo'].value_counts().plot(kind='barh')
plt.title('Tipos de Acidentes em Matão')
plt.tight_layout()
plt.savefig('output/graficos/tipos_acidentes.png')
plt.show()

# Gravidade
plt.figure(figsize=(8, 6))
df_matao['gravidade'].value_counts().plot(kind='pie', autopct='%1.1f%%')
plt.title('Distribuição da Gravidade dos Acidentes')
plt.ylabel('')
plt.tight_layout()
plt.savefig('output/graficos/gravidade_acidentes.png')
plt.show()
```

### 5.3 Cruzamento de variáveis

```python
# Tipo de acidente x Gravidade
crosstab = pd.crosstab(df_matao['tipo'], df_matao['gravidade'])

plt.figure(figsize=(12, 8))
sns.heatmap(crosstab, annot=True, fmt='d', cmap='YlOrRd')
plt.title('Tipo de Acidente vs Gravidade')
plt.tight_layout()
plt.savefig('output/graficos/heatmap_tipo_gravidade.png')
plt.show()

# Dia da semana x Hora (mapa de calor)
heatmap_data = df_matao.pivot_table(index='dia_semana', columns='hora_int', values='data', aggfunc='count')
heatmap_data = heatmap_data.reindex(ordem_dias)

plt.figure(figsize=(16, 6))
sns.heatmap(heatmap_data, cmap='Reds', linewidths=0.5)
plt.title('Distribuição de Acidentes: Dia da Semana vs Hora')
plt.tight_layout()
plt.savefig('output/graficos/heatmap_dia_hora.png')
plt.show()
```

---

## 6. Análise Geoespacial (Mapa de Calor)

Se seus dados contêm latitude e longitude, você pode criar visualizações geográficas.

```python
import plotly.express as px

# Verifique se há coordenadas válidas
df_mapa = df_matao.dropna(subset=['latitude', 'longitude']).copy()

# Garanta que são numéricas
df_mapa['latitude'] = pd.to_numeric(df_mapa['latitude'], errors='coerce')
df_mapa['longitude'] = pd.to_numeric(df_mapa['longitude'], errors='coerce')

# Scatter map com Plotly
fig = px.scatter_mapbox(
    df_mapa,
    lat='latitude',
    lon='longitude',
    color='gravidade',
    hover_data=['tipo', 'data', 'hora'],
    zoom=12,
    height=600,
    title='Acidentes de Trânsito em Matão/SP'
)
fig.update_layout(mapbox_style="open-street-map")
fig.write_html('output/graficos/mapa_acidentes.html')
fig.show()
```

> **Alternativa sem internet:** Use `geopandas` + `matplotlib` para criar mapas estáticos, caso não queira depender de tiles online.

---

## 7. Análise Estatística e Modelagem Preditiva (Opcional)

### 7.1 Teste de hipóteses simples

Exemplo: Será que há diferença significativa no número de acidentes entre dias úteis e finais de semana?

```python
from scipy import stats

df_matao['fim_de_semana'] = df_matao['dia_semana'].isin(['Sábado', 'Domingo'])

uteis = df_matao[df_matao['fim_de_semana'] == False].groupby('data').size()
fds = df_matao[df_matao['fim_de_semana'] == True].groupby('data').size()

t_stat, p_value = stats.ttest_ind(uteis, fds, equal_var=False)
print(f"Estatística t: {t_stat:.4f}, p-valor: {p_value:.4f}")

if p_value < 0.05:
    print("Há diferença estatisticamente significativa entre dias úteis e fins de semana.")
else:
    print("Não há evidência estatística de diferença significativa.")
```

### 7.2 Modelo preditivo simples: prever gravidade do acidente

```python
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

# Prepare os dados para modelagem
features = ['hora_int', 'dia_semana', 'tipo', 'mes']

# Transforme variáveis categóricas em numéricas (One-Hot Encoding)
df_model = df_matao[features + ['gravidade']].dropna().copy()
df_model = pd.get_dummies(df_model, columns=['dia_semana', 'tipo', 'mes'], drop_first=True)

X = df_model.drop('gravidade', axis=1)
y = df_model['gravidade']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)

# Treine um modelo
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

y_pred = clf.predict(X_test)

print(classification_report(y_test, y_pred))

# Importância das variáveis
importancias = pd.Series(clf.feature_importances_, index=X.columns).sort_values(ascending=False)
print(importancias.head(10))
```

> **Atenção:** Modelos preditivos com poucos dados de uma única cidade podem não ser robustos. Use mais como exercício de aprendizado do que como ferramenta definitiva.

---

## 8. Storytelling e Comunicação dos Resultados

A etapa final é transformar números em narrativa.

### Estrutura sugerida para o relatório:

1. **Contexto:** Por que acidentes de trânsito em Matão importam?
2. **Metodologia:** De onde vieram os dados, período analisado, ferramentas usadas.
3. **Principais Descobertas:** Use os gráficos salvos em `output/graficos/`
   - "O tipo mais comum de acidente em Matão é..."
   - "Os horários de pico de acidentes são..."
   - "As vias mais críticas são..."
4. **Recomendações:** Com base nos dados, sugestões para o trânsito local.
5. **Limitações:** O que os dados não mostram? Há subnotificação?

### Exportando um resumo estatístico:

```python
resumo = df_matao.groupby('ano').agg({
    'data': 'count',
    'mortos': 'sum',
    'feridos_graves': 'sum',
    'feridos_leves': 'sum',
    'ilesos': 'sum'
}).rename(columns={'data': 'total_acidentes'})

resumo.to_csv('output/relatorios/resumo_anual_matao.csv')
print(resumo)
```

---

## 9. Checklist de Progresso

Use esta lista para acompanhar seu avanço:

- [ ] Ambiente configurado e bibliotecas instaladas
- [ ] Arquivo CSV carregado corretamente
- [ ] Coluna de município identificada e filtrada para Matão
- [ ] Dados limpos (nulos tratados, tipos corrigidos)
- [ ] Colunas derivadas criadas (ano, mês, gravidade, etc.)
- [ ] Análise temporal concluída (gráficos de ano, mês, dia, hora)
- [ ] Análise de tipos e gravidade concluída
- [ ] Mapa de calor gerado (se houver coordenadas)
- [ ] Cruzamentos de variáveis analisados
- [ ] (Opcional) Modelagem preditiva testada
- [ ] Relatório escrito com storytelling
- [ ] Gráficos e resumos exportados para `output/`

---

## Dicas Finais

- **Persistência:** Use `df_matao.to_csv('data/matao_limpo.csv', index=False)` para salvar o dataset limpo entre sessões.
- **Documentação:** Mantenha um arquivo `README.md` explicando cada notebook.
- **Controle de versão:** Se souber usar Git, versione seus notebooks. Caso contrário, salve cópias com datas (`01-exploracao-2025-01-15.ipynb`).
- **Não tenha medo de errar:** A Ciência de Dados é iterativa. Se uma análise não faz sentido, volte e questione seus dados.

Bom projeto!
