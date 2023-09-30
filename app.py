from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

##############################################################
# carrega os dados
dados = pd.read_csv('./dados/pacientes_INTO.csv',parse_dates=[1,2,3,4,12,20],dtype={'Unnamed: 23': str})

# # preparação dos dados para o treemap
# dados_tree = pd.DataFrame(dados[['SERVIÇO','CID']].value_counts()).sort_index().reset_index()
# dados_tree.columns=['SERVIÇO','CID','ATENDIMENTOS']
# # adiciona dados extras
# lista_n_pacientes = []
# lista_reinternacoes = []
# lista_obitos = []
# lista_mortalidades = []
# lista_estada = []
# lista_estada_prolongada = []
# lista_taxa_eventos_adversos = []
# # loopa
# for i in dados_tree.index:
#     # recupera o dataframe com os dados correpsondes a linha
#     mask = (dados['SERVIÇO'] == dados_tree.loc[i,'SERVIÇO']) & (dados['CID'] == dados_tree.loc[i,'CID'])
#     data_line = dados[mask]
#     # extrai as medidas
#     n_pacientes = len(data_line.index.unique()) # descobre numero de pacientes
#     reinternacoes = (data_line.index.value_counts()>1).sum() # numero de reinternacoes
#     obitos = (data_line['MOTIVO DA ALTA'] == 'OBITO').sum()
#     estada_media = data_line['ESTADA'].quantile(.5)
#     estada_prolongada = (data_line['ESTADA']>data_line['ESTADA'].quantile(.75)).sum()
#     # adiciona as listas
#     lista_n_pacientes.append(n_pacientes)
#     lista_reinternacoes.append(reinternacoes)
#     lista_obitos.append(obitos)
#     lista_mortalidades.append(obitos/n_pacientes)
#     lista_estada.append(estada_media)
#     lista_estada_prolongada.append(estada_prolongada)
#     lista_taxa_eventos_adversos.append( (estada_prolongada+obitos+reinternacoes)/n_pacientes )
# # adiciona nas colunas
# dados_tree['n pacientes'] = lista_n_pacientes
# dados_tree['reinternacoes'] = lista_reinternacoes
# dados_tree['obitos'] = lista_obitos
# dados_tree['mortalidade'] = lista_mortalidades
# dados_tree['estada'] = lista_estada
# dados_tree['estadas prolongadas'] = lista_estada_prolongada
# dados_tree['taxa de eventos adversos'] = lista_taxa_eventos_adversos
dados_tree = pd.read_csv("./dados/treemap_data.csv")

# Cria dados temporarios organizado por ano, esses dados serão atualizados de acordo com o click no treemap 
dados_temp = dados.copy()
dados_temp['DATA INTERNAÇÃO'] = dados_temp['DATA INTERNAÇÃO'].dt.year
dados_temp_por_ano = dados_temp.groupby('DATA INTERNAÇÃO')

##############################################################
# cria as figuras
x_range = (dados_temp['DATA INTERNAÇÃO'].min()-1,dados_temp['DATA INTERNAÇÃO'].max()+1)

# treeplot
fig_tree = px.treemap(dados_tree,values='ATENDIMENTOS',
                path=[px.Constant("INTO"),'SERVIÇO','CID'],
                # hover_data=['reinternacoes','mortalidade','estada','estadas prolongadas','taxa de eventos adversos'],
                hover_data=['mortalidade'],
                # custom_data=['mortalidade'],
                width=800,
                height=400)
fig_tree.update_traces(root_color="lightgrey")
fig_tree.update_traces(hovertemplate='')
# ajuste estético
fig_tree.update_layout(margin = {'t':25, 'l':5, 'r':5, "b":5})

# cria figura de numero de internações - usando dados de idade por conveniencia 
def get_fig_n_internacoes(dados_temp_por_ano):
    fig_n_internacoes = px.line(
        x=dados_temp_por_ano['IDADE'].count().index,
        y=dados_temp_por_ano['IDADE'].count(),
        labels={
            "x": "Ano",
            "y": "Internações"},
        width=800, height=200)
    # controla a estettica da linha
    fig_n_internacoes.update_traces(line={'color':'black'})
    # ajuste estetico
    fig_n_internacoes.update_layout(margin = {'t':25, 'l':25, 'r':5, "b":5},xaxis_range=x_range)

    return fig_n_internacoes

# instancia a figura
fig_n_internacoes = get_fig_n_internacoes(dados_temp_por_ano)

# cria figura para variaveis numericas
def get_fig_numerica(dados_temp,dados_temp_por_ano,variavel,nome_exib,y_range):
    # adiciona um jitter no ano para exibicao do scatter
    dados_temp['DATA INTERNACAO JITTER'] = dados_temp["DATA INTERNAÇÃO"] + np.random.normal(0,0.05,len(dados_temp))
    # apresenta os dados como scatter
    fig_numerica_scatter = px.scatter(
        x=dados_temp['DATA INTERNACAO JITTER'],
        y=dados_temp[variavel],
        )
    # controla opacidade
    fig_numerica_scatter.update_traces(marker={"opacity":.1})
    # adiciona a linha de tendencia central como openGL
    fig_numerica_linha = go.Figure(
        data = [go.Scattergl(  
            x=dados_temp_por_ano[variavel].describe().index,
            y=dados_temp_por_ano[variavel].quantile(.5),
        )])
    # adiciona os erros
    fig_numerica_linha.update_traces(
        error_y={
            'array':dados_temp_por_ano[variavel].quantile(.75)-dados_temp_por_ano[variavel].quantile(.5),
            'arrayminus':dados_temp_por_ano[variavel].quantile(.5)-dados_temp_por_ano[variavel].quantile(.25)
        },
        selector={'type':'scattergl'})
    # controla a estetica da linha
    fig_numerica_linha.update_traces(line={'color':'black'})
    # junta as figuras
    fig_numerica = go.Figure(
        data = fig_numerica_scatter.data + fig_numerica_linha.data,
        layout = {
            'width':800,
            "height":200,
            'xaxis_title':{'text':'Ano'},
            'yaxis_title':{'text':nome_exib},
            'yaxis_range':y_range,
            'xaxis_range':x_range
        }
    )
    # ajusta estetico
    fig_numerica.update_layout(margin = {'t':5, 'l':25, 'r':5, "b":5},showlegend=False)
    
    return fig_numerica

# instancia as figuras de base
fig_idade = get_fig_numerica(dados_temp,dados_temp_por_ano,'IDADE','Idade (anos)',[0,100]) 
fig_estada = get_fig_numerica(dados_temp,dados_temp_por_ano,'ESTADA','Estada (dias)',[0,30]) 

##############################################################
# outros elementos graficso

# instancia len dados para economia processual
len_dados= dados_tree['ATENDIMENTOS'].sum()

# cria o texto basico
def make_texto_base(dados,len_dados):
    # define texto auxiliar
    inicio_periodo = dados['DATA INTERNAÇÃO'].min().strftime("%m/%Y")
    fim_periodo = dados['DATA INTERNAÇÃO'].max().strftime("%m/%Y")
    # cria texto principal
    texto = '''
    No periodo entre {0} e {1}, foram realizadas {2} internações no INTO'''
    # insere as informações
    texto = texto.format(inicio_periodo,fim_periodo,len_dados)

    return texto

# instancia o texto base
texto_base = make_texto_base(dados,len_dados)

# adiciona texto do CAE
def make_texto_cae(servico, len_dados, len_dados_temp):
    texto_cae ='''
    O centro de serviço especializado (CAE) {0} foi responsável por {1} ({2}%) dessas internações'''
    texto_cae = texto_cae.format(servico,len_dados_temp,int(len_dados_temp/len_dados*100))
    
    return texto_cae

def make_texto_cid (cid, len_dados_cae, dados_temp):
    # faz texto base
    texto_cid ='''
    O codigo internacional de doenças (CID) {0}
    foi indicado como causa de {1} ({2}%) das internações desse CAE
    '''
    texto_cid = texto_cid.format(cid, len(dados_temp), int(len(dados_temp)/len_dados_cae*100))
    # tenta adicionar informação de sexo
    try:
        percent_homens = int((dados_temp['SEXO']=='M').sum()/len(dados_temp)*100)
        texto_sexo = '''
    Desses pacientes {0}% eram homens 
    '''
        texto_sexo = texto_sexo.format(percent_homens)
    except Exception as error:
        texto_sexo=''''''
        print("não foi possivel calcular percentual de homens",'\n',error)
    # tenta adicionar informação de idade
    try:
        idade_media = int(dados_temp['IDADE'].mean())
        idade_Q1 = int(dados_temp['IDADE'].quantile(.25))
        idade_Q3 = int(dados_temp['IDADE'].quantile(.75))
        texto_idade = '''
    A idade média dos pacientes foi de {0} anos, com metade tendo entre {1} e {2} anos 
    '''
        texto_idade = texto_idade.format(idade_media,idade_Q1,idade_Q3)
    except Exception as error:
        texto_sexo=''''''
        print("não foi possivel calcular idade media",'\n',error)
    # tenta adicionar informação de estada
    try:
        estada_Q2 = int(dados_temp['ESTADA'].quantile(.5))
        estada_P95 = int(dados_temp['ESTADA'].quantile(.95))
        texto_estada = '''
    Metade desses pacientes receberam alta em até {0} dias, com 95% dos pacientes liberados em ate {1} dias 
    '''
        texto_estada = texto_estada.format(estada_Q2,estada_P95)
    except Exception as error:
        texto_sexo=''''''
        print("não foi possivel calcular estada",'\n',error)
    return [texto_cid,texto_sexo,texto_idade,texto_estada]


##############################################################
# instancia o app
app = Dash(__name__)
server = app.server

##############################################################
# define elementos do layout
borda = '0px black solid'

coluna_graficos = html.Div([
    html.Div([dcc.Graph(figure=fig_n_internacoes,id='graph_n_internacoes')],style={'border': borda}),
    html.Div([dcc.Graph(figure=fig_idade,id='graph_idade')],style={'border': borda}),
    html.Div([dcc.Graph(figure=fig_estada,id='graph_estada')],style={'border': borda}),
],style={'display': 'inline-block', 'border': borda,'margin-left': '50px'})

coluna_tree = html.Div([
    html.Div([dcc.Graph(figure=fig_tree,id='graph_tree')],style={'display': 'inline-block','border': borda}),
    html.Div([dcc.Markdown(texto_base,id='texto')],style={'whiteSpace': 'pre-wrap','text-align': 'left','border': borda} ),
],style={'display': 'inline-block', 'border': borda,'vertical-align': 'top','margin-right': '50px'})

# deifne o layout
app.layout = html.Div([
    html.H1(children='Legado INTO', style={'textAlign':'center', 'border': borda}),
    html.Div([
        coluna_tree,
        coluna_graficos,
    ],style={'border': borda,'text-align': 'center'}),
    # html.Div([dcc.Markdown('Versão de teste desenvolvida pela equipe da UPNEURO e coordenação da pós graduação INTO', style={'textAlign':'center', 'border': borda,'margin-bottom':'0px'})], style={'display':'inline-block', 'border': borda})
    # html.Div([html.Footer('Versão de teste desenvolvida pela equipe da UPNEURO e coordenação da pós graduação INTO')], style={'textAlign':'center', 'border': borda,'margin-bottom':'0px'})
],style={'border': borda,'height': '98%','width': '99%','position': 'absolute' ,'display':'grid'})
##############################################################
# callbacks

# recupera o serviço/cid clicado no treemap 
@app.callback(
    Output("graph_n_internacoes", "figure"),
    Output("graph_idade", "figure"),
    Output("graph_estada", "figure"),
    Output("texto", "children"),
    Input("graph_tree", "clickData"),
)
def get_dados_treemap(click_data):

    print(click_data)

    # recupera os dados do click no treemap
    try:
        dados_click = np.array((click_data['points'][0]['id']).split('/'))
        dados_click = np.pad(dados_click,[0,3-len(dados_click)],constant_values=0)
    except:
        dados_click = np.array([0,0,0])
    # recupera informações de cada campo
    print(dados_click)
    controle,servico,cid = dados_click

    # faz texto para concatenar ao final
    texto_cae = ''''''
    texto_cid = ''''''

    # evita quebras
    if controle == '0' or servico == '0':
        print("reiniciando figura")    
        # reinicia as figuras    
        nova_fig_n = fig_n_internacoes
        nova_fig_idade = fig_idade
        nova_fig_estada = fig_estada
        novo_texto = texto_base
    # retorna o fluxo de criação de figura
    else:
        print('criando nova figura')
        dados_temp = dados[dados['SERVIÇO']==servico].copy()
        # adiciona texto do cae
        len_dados_cae = len(dados_temp)
        texto_cae = make_texto_cae(servico, len_dados, len_dados_cae)
        # verifica se o CID foi selecionado
        if cid != '0':
            print('CID selecionado')
            dados_temp = dados_temp[dados_temp['CID']==cid].copy()
            # faz o texto do CID
            try:
                texto_cid = make_texto_cid(cid, len_dados_cae, dados_temp)
            except Exception as error:
                print("não foi possivel criar texto CID",'\n',error)
        # organiza a coluna de internação por ano e cria agrupador para criação da figura
        dados_temp['DATA INTERNAÇÃO'] = dados_temp['DATA INTERNAÇÃO'].dt.year
        dados_temp_por_ano = dados_temp.groupby('DATA INTERNAÇÃO')
        # cria a nova figura de numero de internação - usa a idade por conveniencia
        print(dados_temp_por_ano['IDADE'].count().index)
        print(dados_temp_por_ano['IDADE'].count())
        # garante que nao vai quebrar
        try:
            # nova fig n
            nova_fig_n = get_fig_n_internacoes(dados_temp_por_ano) 
            # nova fig idade
            nova_fig_idade = get_fig_numerica(dados_temp,dados_temp_por_ano,'IDADE','Idade (anos)',[0,100]) 
            nova_fig_estada = get_fig_numerica(dados_temp,dados_temp_por_ano,'ESTADA','Estada (dias)',[0,30]) 
            novo_texto = [texto_base,texto_cae, *texto_cid]
            print(novo_texto)
        except Exception as error:
            # reseta as figuras
            nova_fig_n = fig_n_internacoes
            nova_fig_idade = fig_idade
            nova_fig_estada = fig_estada
            novo_texto = texto_base
            print('erro na criação da figura, reiniciando figura','\n',error)
    
    return (nova_fig_n, nova_fig_idade, nova_fig_estada, novo_texto)

##############################################################
# roda o negocio

if __name__ == '__main__':
    app.run(debug=True)