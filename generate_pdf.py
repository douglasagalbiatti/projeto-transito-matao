import markdown
import weasyprint
import os

base_path = "/home/alien/Documentos/data_science/projeto_transito_matao"

html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
  @page {{
    size: A4;
    margin: 2cm;
  }}
  body {{
    font-family: Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.5;
    column-count: 2;
    column-gap: 1cm;
    text-align: justify;
  }}
  h1 {{
    font-size: 16pt;
    column-span: all;
    text-align: center;
    margin-bottom: 20px;
    color: #2c3e50;
  }}
  h2 {{
    font-size: 14pt;
    color: #2980b9;
    margin-top: 15px;
    margin-bottom: 10px;
  }}
  p {{
    margin-bottom: 10px;
  }}
  ul {{
    margin-top: 0;
    margin-bottom: 10px;
    padding-left: 20px;
  }}
  img {{
    max-width: 100%;
    height: auto;
    display: block;
    margin: 10px auto;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 15px;
    font-size: 10pt;
  }}
  th, td {{
    border: 1px solid #ddd;
    padding: 6px;
    text-align: center;
  }}
  th {{
    background-color: #f2f2f2;
    font-weight: bold;
  }}
</style>
</head>
<body>

<h1>Entendendo o Trânsito de Matão: Um Olhar Sobre os Acidentes (2015–2026)</h1>

<h2>Introdução</h2>
<p>Você já se perguntou como está a segurança no trânsito da nossa cidade? Entre 2015 e 2026, coletamos e analisamos informações detalhadas sobre os acidentes de trânsito em Matão. Com cerca de 85 mil habitantes e um forte setor industrial, o tráfego da nossa cidade mistura muitos carros, motocicletas, caminhões de carga e rodovias importantes (SP-310 e SP-326). O objetivo deste estudo foi descobrir onde mora o perigo e o que podemos fazer para tornar nossas ruas mais seguras.</p>

<h2>Os Dados</h2>
<p>Analisamos mais de 4 mil registros oficiais do estado. Descobrimos que quase metade desses casos (47%) resultou apenas em danos materiais, ou seja, ninguém se machucou. Porém, tivemos mais de 1.700 acidentes com ferimentos leves, 286 com ferimentos graves e, infelizmente, 147 vítimas fatais nesse período (uma média de 6 a 17 mortes por ano).</p>

<img src="file://{base_path}/output/graficos/acidentes_por_ano.png" alt="Evolução de acidentes por ano">

<h2>O Maior Perigo: Choques e Motocicletas</h2>
<p>Quando pensamos em acidentes graves, logo imaginamos batidas entre dois carros. No entanto, os dados nos mostram que bater em obstáculos fixos (como postes e árvores) é quase 4 vezes mais letal do que bater em outro veículo. De cada sete "choques" desse tipo, um resulta em morte.</p>

<table>
  <tr>
    <th>Tipo de Sinistro</th>
    <th>Total de Casos</th>
    <th>Óbitos</th>
    <th>Feridos Graves</th>
    <th>Taxa de Letalidade (%)</th>
  </tr>
  <tr>
    <td>CHOQUE</td>
    <td>290</td>
    <td>41</td>
    <td>34</td>
    <td>14,14%</td>
  </tr>
  <tr>
    <td>ATROPELAMENTO</td>
    <td>207</td>
    <td>16</td>
    <td>26</td>
    <td>7,73%</td>
  </tr>
  <tr>
    <td>COLISÃO</td>
    <td>1.506</td>
    <td>58</td>
    <td>176</td>
    <td>3,85%</td>
  </tr>
  <tr>
    <td>OUTROS</td>
    <td>1.367</td>
    <td>24</td>
    <td>45</td>
    <td>1,76%</td>
  </tr>
</table>

<p>Outro alerta importante vai para os motociclistas. As motos estão envolvidas em um terço de todos os acidentes (33,8%), mas a presença delas é o fator número um que determina se um acidente será grave ou não.</p>

<img src="file://{base_path}/output/graficos/tipos_e_veiculos.png" alt="Acidentes por tipos e veículos">
<img src="file://{base_path}/output/graficos/importancia_features_ml.png" alt="Fatores mais importantes na severidade">

<h2>Horários de Maior Atenção</h2>
<p>A correria do dia a dia dita o ritmo dos acidentes. O horário de maior perigo em Matão é o fim da tarde, entre as 17h e as 19h, exatamente quando as pessoas estão saindo do trabalho, das indústrias e do comércio. Também há um aumento notável por volta das 13h.</p>
<p>Ao contrário do que se possa imaginar, a média diária de acidentes é quase a mesma nos finais de semana em comparação aos dias úteis (cerca de 2 acidentes por dia). A diferença é que, de segunda a sexta, eles se concentram no horário de pico, enquanto no fim de semana acontecem de forma mais espalhada, invadindo a noite e a madrugada.</p>

<img src="file://{base_path}/output/graficos/acidentes_dia_e_hora.png" alt="Acidentes por dia e hora">
<img src="file://{base_path}/output/graficos/heatmap_dia_hora.png" alt="Mapa de calor de acidentes">

<h2>Onde Acontecem?</h2>
<p>Mapeamos todos esses acidentes. Dentro da cidade e nos bairros, vemos muitos acidentes, mas na maioria das vezes com danos menores, pois as velocidades são mais baixas. O verdadeiro risco à vida está nas rodovias e nos trevos de acesso à cidade, como os da Avenida Baldan e Avenida Trolesi, além da região do Distrito Industrial. É lá que ocorrem quase todas as fatalidades.</p>

<h2>O Que Podemos Fazer? (Recomendações)</h2>
<p>Diante disso, algumas ações podem salvar vidas:</p>
<ul>
  <li><strong>Ruas e Rodovias:</strong> Instalar proteções ao redor de postes e árvores nas avenidas principais, melhorar a iluminação e a sinalização nos trevos, e criar espaços exclusivos de parada para motos nos semáforos.</li>
  <li><strong>Fiscalização:</strong> Redobrar a atenção com radares de velocidade nos horários críticos (17h-19h) e realizar operações durante as madrugadas dos finais de semana.</li>
  <li><strong>Conscientização:</strong> Promover palestras e campanhas nas grandes empresas da cidade, incentivando o uso correto de capacetes e equipamentos de proteção.</li>
</ul>

<h2>Conclusão</h2>
<p>Os números mostram que o trânsito de Matão exige atenção especial, especialmente nos trevos e nos finais de tarde. Com cuidado redobrado, melhorias nas vias e respeito às regras, podemos reduzir os acidentes e garantir que todos voltem para casa em segurança.</p>

</body>
</html>
"""

pdf = weasyprint.HTML(string=html_content).write_pdf(f"{base_path}/relatorio_ciencia_de_dados_matao.pdf")
print("PDF gerado com sucesso com gráficos e tabelas incluídos!")
