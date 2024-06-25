import os
import pandas as pd
import streamlit as st
import plotly.express as px

nomes_eventos = {
    16: "Antena Violada",
    25: "Bateria Violada",
    28: "Engate e desengate violado",
    6: "Desvio de Rota",
    10: "Movimento Indevido",
    47: "Perda de Sinal",
    29: "Porta do Caroneiro Aberta/Violada",
    30: "Porta do Motorista Aberta/Violada",
    15: "Teclado Violado",
    32: "Velocidade Violada",
    26: "Violação do Sensor da Porta do Baú",
    22: "Violação dos Sensores das janelas",
    56: "Parada não autorizada"
}

def calcular_pontuacao(row, porcentagens):
    pontuacao = 0
    for codigo, porcentagem in porcentagens.items():
        coluna = f'esis_espa_codigo_{codigo}'
        if coluna in row.index:
            pontuacao += row[coluna] * porcentagem
    return pontuacao

def plotar_grafico_pizza(df_eventos):
    fig = px.pie(df_eventos, names='evento', values='quantidade', title='Distribuição de Eventos', hole=0.3)
    st.plotly_chart(fig)

def plotar_grafico_barras(df_eventos_diarios):
    df_eventos_diarios['data'] = pd.to_datetime(df_eventos_diarios['esis_data_leitura']).dt.date
    df_eventos_diarios_agrupado = df_eventos_diarios.groupby('data').size().reset_index(name='quantidade')
    fig = px.bar(df_eventos_diarios_agrupado, x='data', y='quantidade', title='Eventos Registrados por Dia')
    fig.update_xaxes(type='category')  
    st.plotly_chart(fig)

script_directory = os.path.dirname(os.path.abspath(__file__))

csv_path = os.path.join(script_directory, 'fonte.csv')
df = pd.read_csv(csv_path, parse_dates=['esis_data_leitura'])

data_minima = df['esis_data_leitura'].min().strftime('%d/%m/%Y')
data_maxima = df['esis_data_leitura'].max().strftime('%d/%m/%Y')

eventos_na_base = df['esis_espa_codigo'].unique()

for codigo in eventos_na_base:
    coluna = f'esis_espa_codigo_{codigo}'
    df[coluna] = (df['esis_espa_codigo'] == codigo).astype(int)

st.set_page_config(
    page_title='Avaliação de Risco de Motoristas',
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.sidebar.header('Configurações:')
with st.sidebar.form("config_form"):
    porcentagens = {}
    for codigo in eventos_na_base:
        if codigo in nomes_eventos:
            nome_evento = nomes_eventos[codigo]
            porcentagens[codigo] = st.number_input(f"Porcentagem {nome_evento}:", min_value=0, max_value=100, step=1, key=f"porcentagem_{codigo}")

    quantidade_motoristas = st.number_input("Quantidade de Motoristas a Serem Exibidos:", key="quantidade_motoristas", value=5, min_value=1, max_value=20, step=1)

    data_inicial = st.date_input("Data Inicial:", key="data_inicial", value=pd.to_datetime(data_minima, format='%d/%m/%Y'))
    data_final = st.date_input("Data Final:", key="data_final", value=pd.to_datetime(data_maxima, format='%d/%m/%Y'))

    executar_button = st.form_submit_button(label='Executar')

st.image(os.path.join(script_directory, 'logo.png'), width=300)
st.title('Motoristas Analisados:')
executado_com_sucesso = False

with st.spinner("Calculando..."):
    if executar_button:
        if all(0 <= valor <= 100 for valor in porcentagens.values()) and sum(porcentagens.values()) == 100:
            porcentagens_normalizadas = {codigo: valor / 100 for codigo, valor in porcentagens.items()}
            df['pontuacao'] = df.apply(calcular_pontuacao, porcentagens=porcentagens_normalizadas, axis=1)

            if df[[f'esis_espa_codigo_{codigo}' for codigo in eventos_na_base]].sum().sum() == 0:
                st.warning('Nenhum evento encontrado na base de dados.')
            else:
                pontuacao_total = df.groupby('motorista')['pontuacao'].sum().reset_index()
                pontuacao_total['pontuacao'] = pontuacao_total['pontuacao'].round(2)
                motoristas_ordenados = pontuacao_total.sort_values(by='pontuacao', ascending=False)
                motoristas_selecionados = motoristas_ordenados['motorista'].head(quantidade_motoristas)

                for motorista in motoristas_selecionados:
                    with st.expander(f'Motorista {motorista}'):
                        st.write(f"Pontuação Total: {pontuacao_total[pontuacao_total['motorista'] == motorista]['pontuacao'].values[0]}")

                        df_eventos_diarios = df[df['motorista'] == motorista].groupby('esis_data_leitura').size().reset_index(name='quantidade')
                        plotar_grafico_barras(df_eventos_diarios)

                        df_eventos_motorista = df[df['motorista'] == motorista][[f'esis_espa_codigo_{codigo}' for codigo in eventos_na_base]]
                        eventos_motorista = []
                        for codigo, nome in nomes_eventos.items():
                            if f'esis_espa_codigo_{codigo}' in df_eventos_motorista.columns and porcentagens_normalizadas.get(codigo, 0) > 0:
                                if df_eventos_motorista[f'esis_espa_codigo_{codigo}'].sum() > 0:
                                    eventos_motorista.append({'evento': nome, 'quantidade': df_eventos_motorista[f'esis_espa_codigo_{codigo}'].sum()})

                        df_eventos_motorista = pd.DataFrame(eventos_motorista)
                        if not df_eventos_motorista.empty:
                            plotar_grafico_pizza(df_eventos_motorista)

            executado_com_sucesso = True
        else:
            st.warning('Por favor, preencha as porcentagens corretamente.')
            executado_com_sucesso = True

if not executado_com_sucesso:
    st.write("Bem-vindo ao sistema de Avaliação de Risco de Motoristas!")
    st.write("Preencha as colunas à esquerda com as porcentagens desejadas para cada evento.")
    st.write("Certifique-se de que a soma de todas as porcentagens seja 100%.")
    st.write("Depois, clique no botão 'Executar' para visualizar os resultados.")