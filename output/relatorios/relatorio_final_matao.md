# Relatório Executivo: Análise e Diagnóstico de Sinistros de Trânsito em Matão/SP (2015–2026)

**Autor:** Análise de Ciência de Dados  
**Data:** Setembro de 2026  
**Fonte de Dados:** Infosiga SP (Movimento Paulista de Segurança no Trânsito)  
**Abrangência:** Município de Matão / SP (Código IBGE: 3529302)  

---

## 1. Contexto e Objetivos

Matão é um polo industrial e agrícola estratégico localizado no centro-norte do Estado de São Paulo, contando com cerca de 85 mil habitantes. O município abriga grandes indústrias dos setores metalmecânico, agrícola e citrícola (como Marchesan, Baldan e Citrosuco), além de ser cortado por dois eixos rodoviários de relevância estadual: a **SP-310 (Rodovia Washington Luís)** e a **SP-326 (Rodovia Brigadeiro Faria Lima)**.

A combinação entre fluxo de veículos de carga de grande porte, expressiva frota de motocicletas utilizada para deslocamento de trabalhadores e travessias urbanas/rodoviárias torna a segurança viária um tema crítico de saúde pública e gestão urbana.

O objetivo deste estudo foi conduzir um diagnóstico aprofundado dos sinistros de trânsito em Matão ao longo de mais de 11 anos, identificando:
- Padrões de evolução temporal e sazonalidade;
- Os tipos de acidentes e modais de transporte mais vulneráveis;
- A geografia do risco e as vias mais letais;
- A viabilidade de predição da gravidade dos sinistros via Machine Learning.

---

## 2. Metodologia e Processamento de Dados

### 2.1 Coleta e Engenharia de Dados
Os dados brutos foram obtidos do repositório público do **Infosiga SP**, divididos em três períodos:
1. `sinistros_2015-2021.csv`
2. `sinistros_2022-2024.csv`
3. `sinistros_2025-2026.csv`

Dado que os arquivos originais compreendem todo o Estado de São Paulo (totalizando cerca de 400 MB de dados brutos), implementou-se um pipeline de ingestão em **lotes (*chunks*) de 20.000 linhas**. O processo filtrou exclusivamente os registros com `cod_ibge == 3529302` ou `municipio == 'MATAO'`, consolidando um dataset tratado de **4.074 sinistros** ocupando menos de 800 KB de memória e disco.

### 2.2 Tratamento e Limpeza
- **Tratamento de Nulos:** Em variáveis de contagem de veículos (`qtd_motocicleta`, `qtd_automovel`, etc.) e vítimas (`qtd_gravidade_*`), valores ausentes (`NaN`) foram imputados como `0` e convertidos para inteiros.
- **Normalização de Coordenadas:** Valores de latitude e longitude com separador decimal em vírgula foram higienizados e convertidos para ponto flutuante, alcançando **3.648 sinistros georreferenciados válidos** (quase 90% da base).
- **Classificação de Gravidade:** Criação da variável categórica hierárquica `gravidade` (`Com óbito`, `Com feridos graves`, `Com feridos leves`, `Sem vítimas`).

### 2.3 Ressalva Metodológica Fundamental
Entre **2015 e 2018**, o Infosiga registrava exclusivamente sinistros que resultavam em óbito. A partir de **2019**, com a integração de dados da Polícia Militar, SAMU e Corpo de Bombeiros, o sistema passou a registrar também sinistros não fatais e notificações. Portanto:
- A análise do volume total de sinistros é comparável de **2019 em diante**;
- A série histórica de **sinistros fatais e óbitos é contínua e comparável de 2015 a 2026**.

---

## 3. Principais Descobertas

### 3.1 Distribuição da Gravidade das Ocorrências
No acumulado histórico de 4.074 sinistros em Matão:
- **Sem vítimas (apenas danos materiais/notificações):** 1.920 ocorrências (47,13%)
- **Com feridos leves:** 1.726 ocorrências (42,37%)
- **Com feridos graves:** 286 ocorrências (7,02%)
- **Com óbito:** 142 ocorrências (3,49%) — totalizando **147 vítimas fatais** registradas.

### 3.2 O Perigo Crítico do "Choque" contra Obstáculos Fixos
Ao analisar o cruzamento entre o tipo de evento e o desfecho:
| Tipo de Sinistro | Total de Ocorrências | Óbitos | Feridos Graves | Taxa de Letalidade (%) |
| :--- | :---: | :---: | :---: | :---: |
| **CHOQUE** | 290 | 41 | 34 | **14,14%** |
| **ATROPELAMENTO** | 207 | 16 | 26 | **7,73%** |
| **COLISÃO** | 1.506 | 58 | 176 | **3,85%** |
| **OUTROS** | 1.367 | 24 | 45 | **1,76%** |
| **NÃO DISPONÍVEL** | 704 | 3 | 5 | **0,43%** |

> **Destaque:** Embora colisões sejam o evento mais volumoso, **o choque contra obstáculo fixo (postes, árvores, muretas) é quase 4 vezes mais letal que uma colisão veicular**. Quase 1 a cada 7 choques resulta em morte em Matão, apontando para excesso de velocidade e perda de controle.

### 3.3 Modais: A Vulnerabilidade Extrema da Motocicleta
- **Automóveis** estiveram envolvidos em 1.480 acidentes (36,3%).
- **Motocicletas** estiveram envolvidas em 1.375 acidentes (33,8%).
- **Caminhões** estiveram em 208 acidentes (5,1%), pedestres em 112 (2,7%) e bicicletas em 88 (2,2%).

Na modelagem preditiva supervisionada (Random Forest Classifier, acurácia de 79%), a variável **`qtd_motocicleta` despontou isolada como a característica mais importante (Gini Importance ~ 0,17)** para determinar a gravidade do acidente, superando variáveis como horário, tipo de via e volume de automóveis.

### 3.4 Padrões Temporais
- **Horário de Pico Absoluto:** O período entre **17h e 19h** concentra o maior volume de acidentes da cidade (pico às 17h com 347 sinistros), correspondendo ao término da jornada de trabalho nas indústrias e comércio. Há um pico secundário às **13h** (retorno do almoço).
- **Dias Úteis vs Finais de Semana:** A aplicação do **teste t de Student** revelou que a média diária de acidentes é estatisticamente indiferente entre dias úteis (**2,03 acidentes/dia**) e finais de semana (**2,04 acidentes/dia**), com $p\text{-valor} = 0,76$. A diferença reside no horário: dias úteis concentram-se no horário comercial/rush, enquanto fins de semana dispersam-se pela noite e madrugada.

### 3.5 Geografia da Severidade Viária
A visualização geoespacial interativa evidenciou dois comportamentos espaciais distintos:
1. **Malha Urbana Central e Bairros:** Apresenta densa concentração de acidentes, porém com predomínio de danos materiais e feridos leves (menor velocidade operacional).
2. **Eixos Rodoviários (SP-310 e SP-326) e Trevos:** Concentram a esmagadora maioria dos sinistros com óbito. Destacam-se como zonas de alto risco os entroncamentos de acesso à cidade (trevos da Av. Baldan e Av. Trolesi) e o trecho próximo ao Distrito Industrial Adolfo Baldan.

---

## 4. Recomendações para Segurança no Trânsito

Com base nas evidências empíricas levantadas, propõem-se ações estruturadas nos três pilares da segurança viária:

### A. Engenharia de Tráfego
- **Atenuação de Impacto em Obstáculos Fixos:** Mapeamento de postes e árvores sem recuo no leito carroçável das principais avenidas arteriais de Matão, instalando defensas metálicas ou barreiras absorvedoras de impacto.
- **Readequação Geométrica dos Trevos Rodoviários:** Melhoria na sinalização horizontal refletiva e reforço de iluminação nos acessos da SP-310 e SP-326 ao perímetro urbano.
- **Espaço para Motociclistas:** Implantação de bolsões de parada exclusivos para motos à frente dos semáforos (*bike/moto boxes*) nos cruzamentos de maior fluxo.

### B. Fiscalização e Monitoramento
- **Radares nos Corredores Arteriais:** Monitoramento eletrônico de velocidade nas vias de escoamento industrial durante as janelas de pico (17h–19h e 12h–13h).
- **Operações de Fim de Semana:** Fiscalização noturna e de madrugada com foco em alcoolemia e direção perigosa nas sextas, sábados e domingos.

### C. Educação e Conscientização
- **Campanhas Focadas em Empresas e Trabalhadores:** Parcerias com as grandes indústrias de Matão para palestras e conscientização sobre direção defensiva e uso correto de equipamentos de proteção (capacete afivelado, jaqueta e calçados adequados).

---

## 5. Limitações do Estudo
- **Subnotificação de Danos Materiais:** Acidentes leves resolvidos por acordo verbal entre motoristas, sem intervenção das forças públicas, não constam na base.
- **Falta de Variáveis Comportamentais:** O banco do Infosiga não audita telemetria (velocidade no instante exato do impacto), consumo de substâncias psicoativas ou condição de manutenção preventiva do veículo.

---

## 6. Anexos e Arquivos Gerados
- **Base Limpa Consolidada:** `data/matao_limpo.csv`
- **Resumo Anual Estatístico:** `output/relatorios/resumo_anual_matao.csv`
- **Mapa Geoespacial Interativo:** `output/graficos/mapa_acidentes.html`
- **Gráficos em Alta Resolução:** `output/graficos/*.png`
