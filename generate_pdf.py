import weasyprint
import os

base_path = os.path.dirname(os.path.abspath(__file__))

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
    font-size: 9pt;
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

<h1>Entendendo o Trânsito de Matão: Um Olhar Sobre os Registros (2015–2026)</h1>

<h2>Introdução</h2>
<p>Como está a segurança no trânsito da nossa cidade? Analisamos os registros oficiais do Infosiga SP para Matão, de março de 2015 a setembro de 2026, para entender onde estão os sinais de alerta e o que ainda precisa ser verificado.</p>

<h2>Os Dados</h2>
<p>São 4.126 registros. Destes, 1.916 são notificações, que quase sempre vêm sem dados de vítimas e veículos. Por isso, 1.892 registros (45,9%) estão como "sem informação de vítimas", o que não significa que ninguém se feriu. Há 1.737 registros com feridos leves, 288 com feridos graves e 143 com óbito, que somam 150 vítimas fatais. Os sinistros com óbito variam de 6 a 17 por ano. Até 2018, a base só traz sinistros fatais.</p>

<img src="file://{base_path}/output/graficos/acidentes_por_ano.png" alt="Evolução dos registros por ano">

<h2>Letalidade: Atropelamentos, Choques e Colisões</h2>
<p>Para comparar de forma justa, usamos os sinistros de 2019 em diante, sem notificações. Atropelamentos e choques têm as maiores letalidades, mas as amostras são pequenas para ordená-los. Em vias urbanas, os choques são bem mais letais que as colisões (11,11% contra 1,68%). Nas rodovias, as taxas são próximas (13,56% contra 14,29%).</p>

<table>
  <tr>
    <th>Tipo</th>
    <th>Sinistros</th>
    <th>Com óbito</th>
    <th>Letalidade</th>
  </tr>
  <tr>
    <td>Atropelamento</td>
    <td>92</td>
    <td>14</td>
    <td>15,22%</td>
  </tr>
  <tr>
    <td>Choque</td>
    <td>267</td>
    <td>32</td>
    <td>11,99%</td>
  </tr>
  <tr>
    <td>Outros</td>
    <td>371</td>
    <td>17</td>
    <td>4,58%</td>
  </tr>
  <tr>
    <td>Colisão</td>
    <td>1.360</td>
    <td>38</td>
    <td>2,79%</td>
  </tr>
</table>

<h2>Motocicletas</h2>
<p>As motos aparecem em 62,2% dos registros com veículo ou pedestre informado. Em vias urbanas, 16,9% dos sinistros com moto são graves ou fatais, contra 12,3% dos sem moto. Nas rodovias, as taxas são iguais (29,8% e 29,6%). A base não mostra em qual veículo cada vítima estava, então não permite medir o risco individual do motociclista.</p>

<img src="file://{base_path}/output/graficos/tipos_e_veiculos.png" alt="Registros por tipo e veículo">

<h2>Horários e Dias</h2>
<p>Os maiores volumes ocorrem às 17h, 18h e 19h, mas não há dado de fluxo de veículos para dizer se esse é o horário de maior risco. Essas horas têm 22,4% dos registros e 21,7% dos sinistros fatais.</p>
<p>Contando todos os dias do calendário desde 2019, a média é de 1,42 registro por dia útil e 1,51 por dia de fim de semana (p = 0,107), resultado que não demonstra diferença nem prova igualdade. Sexta (1,66) e sábado (1,68) ficam acima dos demais dias. No fim de semana, 20,8% dos registros ocorrem entre 22h e 5h, contra 11,0% nos dias úteis.</p>

<img src="file://{base_path}/output/graficos/acidentes_dia_e_hora.png" alt="Registros por dia e hora">
<img src="file://{base_path}/output/graficos/heatmap_dia_hora.png" alt="Mapa de calor de registros">

<h2>Onde Acontecem?</h2>
<p>As vias urbanas têm 82 dos 150 óbitos (55%), e as estradas e rodovias, 61 (41%). As rodovias têm menos registros, porém maior letalidade por registro: 14,7% contra 2,2%. Este estudo não analisa trevos específicos.</p>

<h2>O Que Verificar e Fazer</h2>
<p>As ações abaixo são hipóteses a validar, pois a base não mede velocidade, álcool nem fluxo de veículos:</p>
<ul>
  <li><strong>Ruas e Rodovias:</strong> inspecionar os locais de choque urbano e os pontos de óbito na SP-310 e na SP-326 antes de definir obras.</li>
  <li><strong>Fiscalização:</strong> medir a velocidade nas vias com mais óbitos e testar operações nas noites de sexta e sábado, avaliando o resultado.</li>
  <li><strong>Conscientização:</strong> promover campanhas de direção defensiva e uso correto de capacetes e equipamentos de proteção.</li>
</ul>

<h2>Conclusão</h2>
<p>Os dados indicam onde olhar primeiro: óbitos nas vias urbanas e nas rodovias, choques urbanos e noites de sexta e sábado. Melhorar a qualidade dos registros é parte do trabalho, porque quase metade da base não informa o desfecho.</p>

</body>
</html>
"""

pdf = weasyprint.HTML(string=html_content).write_pdf(f"{base_path}/output/relatorios/relatorio_ciencia_de_dados_matao.pdf")
print("PDF gerado com sucesso com gráficos e tabelas incluídos!")
