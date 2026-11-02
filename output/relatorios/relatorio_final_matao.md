<!-- Gerado por scripts/gerar_artefatos.py. Para mudar o texto, edite templates/relatorio_final_matao.md.j2. -->
# Relatório Executivo: Análise e Diagnóstico de Sinistros de Trânsito em Matão/SP (2015–2026)

**Autor:** Análise de Ciência de Dados  
**Fonte de Dados:** Infosiga SP (Movimento Paulista de Segurança no Trânsito)  
**Abrangência:** Município de Matão / SP (Código IBGE: 3529302)  
**Recorte:** 18/03/2015 a 29/09/2026  

> **Atualização automática:** números e conclusões condicionais são recalculados a cada novo mês de dados. A interpretação continua exigindo revisão humana. As correções feitas sobre o estudo de setembro de 2026 estão em `output/relatorios/ERRATA.md`.

---

## 1. Contexto e Objetivos

Matão é um polo industrial e agrícola localizado no centro-norte do Estado de São Paulo. O município abriga indústrias como Marchesan, Baldan e Citrosuco e é cortado pela **SP-310 (Rodovia Washington Luís)** e pela **SP-326 (Rodovia Brigadeiro Faria Lima)**.

O estudo buscou descrever:
- A evolução temporal e a distribuição por dia e hora;
- Os tipos de sinistro e os modais envolvidos;
- A distribuição dos óbitos entre vias urbanas e rodovias;
- O que um modelo de Machine Learning consegue extrair das variáveis disponíveis.

---

## 2. Metodologia e Processamento de Dados

### 2.1 Coleta
Os dados vêm do **Infosiga SP**. Os arquivos estaduais são lidos em lotes de 20.000 linhas e filtrados por `cod_ibge == 3529302`, resultando em **4.126 registros** nesta atualização. Os meses recentes são baixados novamente a cada ciclo para incorporar revisões da fonte.

### 2.2 Tratamento
- **Contagens vazias:** viram `0`. Isso pode subestimar envolvidos: 99 de 211 atropelamentos têm `qtd_pedestre = 0`.
- **Coordenadas:** 3.698 registros têm coordenadas, e 3.692 estão na região de Matão. Coordenadas exatas se repetem muito: 1.066 registros estão em 40 pontos, e parte deles pode indicar uma referência, e não o local do impacto.
- **Gravidade:** `Com óbito`, `Com feridos graves`, `Com feridos leves`, `Sem feridos (ilesos registrados)` e `Sem informação de vítimas`.

### 2.3 Ressalvas Metodológicas
- **2015 a 2018:** só há sinistros fatais. Calcular letalidade com esses anos a infla.
- **Notificações:** são 1.916 registros, quase sempre sem dados de vítimas e veículos. Sua participação anual varia de 21% a 84% desde 2019, e parte pode repetir sinistros já registrados: há ao menos 20 grupos com mesma data, hora e via. A definição oficial do tipo de registro deve ser conferida no dicionário do Infosiga.
- **Base comparável:** letalidade, gravidade por modal e modelo usam **sinistros de 2019 em diante, sem notificações**. Mesmo assim, os totais anuais não medem tendência, porque 2019 tem só 73 sinistros fora das notificações.
- **Exposição:** não há fluxo de veículos nem frota, então volume não equivale a risco.

---

## 3. Principais Descobertas

### 3.1 Desfecho dos Registros
| Desfecho | Registros | % |
| :--- | :---: | :---: |
| Sem informação de vítimas | 1.892 | 45,9% |
| Com feridos leves | 1.737 | 42,1% |
| Com feridos graves | 288 | 7,0% |
| Com óbito | 143 | 3,5% |
| Sem feridos (ilesos registrados) | 66 | 1,6% |

Os 143 registros com óbito somam **150 vítimas fatais**. Os 1.892 registros sem informação não permitem afirmar que ninguém se feriu.

### 3.2 Letalidade por Tipo de Sinistro (base comparável)
Letalidade = sinistros com óbito ÷ sinistros do tipo.

| Tipo de Sinistro | Sinistros | Com óbito | Óbitos (pessoas) | Feridos graves (pessoas) | Letalidade |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Atropelamento** | 92 | 14 | 14 | 24 | **15,22%** |
| **Choque** | 267 | 32 | 33 | 36 | **11,99%** |
| **Outros** | 371 | 17 | 18 | 47 | **4,58%** |
| **Colisão** | 1.360 | 38 | 40 | 182 | **2,79%** |
| **Não disponível** | 78 | 0 | 0 | 5 | **0,00%** |

No conjunto, a letalidade do choque é **4,29 vezes** a da colisão (IC95% 2,73 a 6,74). Por tipo de via:

| Via | Choque | Colisão |
| :--- | :---: | :---: |
| Vias urbanas | 11,11% (23/207) | 1,68% (21/1.247) |
| Estradas e rodovias | 13,56% (8/59) | 14,29% (16/112) |

A diferença aparece nas vias urbanas; nas rodovias, as taxas são próximas.
Atropelamento e choque não podem ser ordenados com segurança (teste exato de Fisher, p = 0,470).
A base não informa a velocidade nem qual objeto foi atingido.

### 3.3 Modais
Entre os 2.223 registros com veículo ou pedestre informado, automóveis aparecem em 67,1%, motocicletas em 62,2%, caminhões em 9,4%, pedestres em 5,0%, bicicletas em 4,0% e ônibus em 1,5%.

A proporção de sinistros graves ou fatais com e sem moto, na base comparável, é:

| Via | Com moto | Sem moto |
| :--- | :---: | :---: |
| Vias urbanas | 16,9% | 12,3% |
| Estradas e rodovias | 29,8% | 29,6% |

A base não liga cada vítima ao seu veículo. Ela não permite concluir que o motociclista é a figura mais vulnerável nem que a moto é o principal fator de gravidade.

### 3.4 Padrões Temporais
- **Horas:** os maiores volumes ocorrem às 17h (350), 18h (305) e 19h (268), seguidos das 13h (258). Essas três primeiras horas concentram 22,4% dos registros e 21,7% dos sinistros fatais.
- **Dias úteis e fins de semana:** contando todos os dias do calendário desde 2019, inclusive os 29,1% sem registro, as médias são **1,42** e **1,51 registros/dia**. A diferença é de 0,09 (IC95% -0,02 a 0,21; teste de Welch, p = 0,107). O resultado não demonstra diferença nem prova igualdade.
- **Dias da semana:** Sexta (1,66) e Sábado (1,68) têm as maiores médias; os demais dias variam de 1,32 a 1,39. Esse contraste é descritivo e deve ser confirmado em novos períodos.
- **Madrugada:** 20,8% dos registros de fim de semana ocorrem entre 22h e 5h, contra 11,0% nos dias úteis.

As relações com saída de fábricas, retorno do almoço e álcool são hipóteses, pois não são medidas aqui.

### 3.5 Geografia
- **Vias urbanas:** têm **82 dos 150 óbitos (55%)**, com letalidade de 2,2% na base completa.
- **Estradas e rodovias:** têm **61 óbitos (41%)**, com letalidade de 14,7%. SP-310 e SP-326 somam 59 óbitos. Outros 7 óbitos estão sem tipo de via informado.
- **Vias com mais sinistros, sem notificações:** SP 310 (202), AVENIDA BALDAN (123), RUA SINHARINHA FROTA (107), RUA RUI BARBOSA (107).

Com notificações, RUA SINHARINHA FROTA lideraria (473), mas 77% dos registros são notificações. O endereço do hospital fica nessa rua, o que indica possível registro do local de atendimento, ainda sem confirmação. Por isso, ela não deve ser tratada como a via mais crítica. Este estudo não analisa trevos específicos.

### 3.6 Modelo de Machine Learning
Um Random Forest treinado na base comparável obteve **78,8% de acurácia**, contra 78,8% de sempre prever a classe mais comum, e 20,0% de acurácia balanceada.

**O modelo não supera a referência, portanto as variáveis disponíveis não sustentam previsão de gravidade.**
As maiores importâncias de permutação são motocicletas (0,019), via: VIAS URBANAS (0,015), automóveis (0,013). Elas não indicam sentido nem causa, e o modelo usa dados conhecidos só depois do sinistro.

---

## 4. Recomendações

As ações abaixo são hipóteses a validar com contagem de tráfego, inspeção em campo e dados de velocidade e alcoolemia.

### A. Engenharia de Tráfego
- **Choques urbanos:** inspecionar os locais de choque em vias urbanas e identificar os objetos atingidos antes de instalar defensas.
- **Rodovias:** avaliar com a concessionária ou o órgão responsável os pontos de óbito na SP-310 e na SP-326.
- **Motocicletas:** avaliar bolsões de parada nos cruzamentos de maior fluxo.

### B. Fiscalização e Monitoramento
- **Velocidade:** medir a velocidade nas vias com mais óbitos antes de definir locais e horários de radares.
- **Dias com mais registros:** testar operações noturnas em Sexta e Sábado, medindo o resultado.
- **Qualidade do dado:** conferir com o Infosiga as notificações e as coordenadas repetidas.

### C. Educação e Conscientização
- **Empresas e trabalhadores:** promover campanhas de direção defensiva e uso correto de equipamentos de proteção.

---

## 5. Limitações do Estudo
- **Subnotificação:** sinistros leves resolvidos sem acionar os órgãos públicos não constam na base.
- **Notificações:** faltam dados de vítimas e veículos, e pode haver duplicidade.
- **Vítima sem veículo:** a base não indica em qual veículo cada vítima estava.
- **Falta de exposição:** não há fluxo de veículos nem frota.
- **Falta de variáveis comportamentais:** não há velocidade, consumo de álcool ou manutenção veicular.
- **Localização:** coordenadas e nomes de vias têm repetições e grafias diferentes.
- **Dados recentes:** o último ano é parcial e está sujeito a revisões.

---

## 6. Anexos e Arquivos Gerados
- **Base Limpa Consolidada:** `data/matao_limpo.csv`
- **Resumo Anual Estatístico:** `output/relatorios/resumo_anual_matao.csv`
- **Mapa Interativo, Gráficos e Resumo em PDF:** branch `artefatos`, que guarda apenas a versão mais recente
