from flask import Flask, render_template, request, send_file
import folium
import os
import pandas as pd
import shutil


############# VARIAVIES 

latitude_inicial = -24.99
longitude_inicial = -53.4595
estilo_inicial = 'CartoDB positron'

class Camada:
    def __init__(self, tipo, nome, dfx, xNome, yLat, zLong):
        self.nome = nome
        self.tipo = tipo
        self.dfx = dfx
        self.xNome = xNome
        self.yLat = yLat
        self.zLong = zLong



vetCamadas = []

############# FUNCOES


############## ROTAS

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():

    ##GAMBIARRA PARA LIDAR COM OS LIXO
    for filename in os.listdir():
        if filename.endswith('.html'):
            os.remove(filename)

    return render_template('homepage.html')

@app.route('/configuracoes', methods=['GET', 'POST'])


def configuracoes_gerais():
    global latitude_inicial
    global longitude_inicial
    global estilo_inicial

    if request.method == 'POST':
        latitude = request.form['latitude']
        longitude = request.form['longitude']
        estiloInicial = request.form['estilo']
        
        # Atualizar as variáveis globais
        latitude_inicial = float(latitude)
        longitude_inicial = float(longitude)
        estilo_inicial = estiloInicial

        print("Latitude:", latitude)
        print("Longitude:", longitude)
        print("Estilo Inicial:", estiloInicial)

    return render_template('configuracoes.html', 
                           latitudeInicial=latitude_inicial,
                           longitudeInicial=longitude_inicial,
                           estiloInicial = estilo_inicial
                           )


@app.route('/camadaGerencia')
def camadas():
    return render_template('camada.html', vetCamadas=vetCamadas)

@app.route('/importarCSV')
def importarCsv():
        return render_template('importar.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if request.method == 'POST':
        uploaded_file = request.files['fileToUpload']

        if uploaded_file:
            tipo_column = request.form['opcSelect']
            main_column = request.form['mainColumn']
            latitude_column = request.form['latitudeColumn']
            longitude_column = request.form['longitudeColumn']

            filename = uploaded_file.filename
            destination = os.path.join('Dados', filename)
            uploaded_file.save(destination)

            minha_camada = Camada(tipo=tipo_column, 
                                  nome=filename, 
                                  dfx=pd.read_csv("Dados/" + filename, sep=';', encoding='latin-1'), 
                                  xNome=main_column, 
                                  yLat=latitude_column, 
                                  zLong=longitude_column)

            vetCamadas.append(minha_camada)

            # Processamento necessário com as informações do arquivo e das colunas
            message = "Arquivo enviado e colunas processadas com sucesso."
            return render_template('camada.html', vetCamadas=vetCamadas, message=message)

    return render_template('camada.html', vetCamadas=vetCamadas)


@app.route('/camada/<camada_nome>')
def mostrar_camada(camada_nome):
    # Encontre o objeto Camada correspondente ao nome clicado
    camada = next((c for c in vetCamadas if c.nome == camada_nome), None)
    if camada:
        return render_template('opcoes_camada.html', camada=camada)
    else:
        return "Camada não encontrada."


@app.route('/SalvarMapa')
def saveMapa():
    return render_template('saveMap.html')

@app.route('/save_map', methods=['POST'])
def save_map():

    filename = request.form['filename']
    if not filename.endswith('.html'):
        filename += '.html'
    
    cordenadasIniciais = (latitude_inicial, longitude_inicial)
    m = folium.Map(location=cordenadasIniciais, zoom_start=12, tiles=estilo_inicial)

    for camada in vetCamadas:
        if camada.tipo == 1: #TEXTO
            print(camada.tipo)



        if camada.tipo == 2: #MARCADOR
            marker_group = folium.FeatureGroup(name=camada.nome, show=False)
            for index, row in (camada.dfx).iterrows():
                nome = row[camada.xNome]
                lat = row[camada.ylat]
                lon = row[camada.zlon]
                popup_text = f"{nome}"
                folium.Marker(location=((lat+.001), (lon-.002)), popup=popup_text).add_to(marker_group)

            marker_group.add_to(m)




    
    # Definir o nome do arquivo temporário
    arquivo_temporario = f'{filename}'
    
    # Salvar o mapa no arquivo temporário
    m.save(arquivo_temporario)
    
    # Enviar o arquivo temporário como um anexo
    return send_file(arquivo_temporario, as_attachment=True)

@app.route('/limpar_dados', methods=['GET'])
def limpar_dados():
    # Limpar o diretório "Dados/"
    folder_path = 'Dados/'
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f'Erro ao excluir {file_path}: {e}')

    # Limpar o vetor de camadas
    vetCamadas.clear()

    return render_template('homepage.html')



if __name__ == '__main__':
    app.run()





##################### CODIGO

