from flask import Flask, render_template, request, send_file
import folium
import os
import pandas as pd
import shutil
import io
from PIL import Image
import time
from selenium import webdriver
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
            tipo_sep = request.form['opcSep']
            
            nomeCamada = request.form['nomeCamada']
            main_column = request.form['mainColumn']
            latitude_column = request.form['latitudeColumn']
            longitude_column = request.form['longitudeColumn']

            filename = uploaded_file.filename
            destination = os.path.join('Dados', filename)
            uploaded_file.save(destination)

            minha_camada = Camada(tipo=tipo_column, 
                                  nome=nomeCamada, 
                                  dfx=pd.read_csv("Dados/" + filename, sep=tipo_sep), 
                                  xNome=main_column, 
                                  yLat=latitude_column, 
                                  zLong=longitude_column)

            vetCamadas.append(minha_camada)

            # Processamento necessário com as informações do arquivo e das colunas
            message = "Arquivo enviado e colunas processadas com sucesso."
            print(tipo_sep)
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


def create_map(filename, zoom_inicial):
    
    cordenadasIniciais = (latitude_inicial, longitude_inicial)
    m = folium.Map(location=cordenadasIniciais, zoom_start=zoom_inicial, tiles=estilo_inicial)

    for camada in vetCamadas:
        if camada.tipo == 'Texto': #TEXTO
            marker_group = folium.FeatureGroup(name=camada.nome, show=False)   
            for index, row in (camada.dfx).iterrows():
                nome = row[camada.xNome]
                lat = float(row[camada.yLat])
                lon = float(row[camada.zLong])
                icon_html = f"""<div style="font-family: courier new; color: black; font-weight: bold; font-size: 10px;">{nome}</div>"""
                icon = folium.DivIcon(html=icon_html)
                folium.Marker(location=((lat+.001), (lon-.002)), icon=icon).add_to(marker_group)


            marker_group.add_to(m)

        if camada.tipo == 'Marcador': #MARCADOR
            marker_group = folium.FeatureGroup(name=camada.nome, show=False)
            for index, row in (camada.dfx).iterrows():
                nome = row[camada.xNome]
                lat = float(row[camada.yLat])
                lon = float(row[camada.zLong])
                popup_text = f"{nome}"
                folium.Marker(location=((lat+.001), (lon-.002)), popup=popup_text).add_to(marker_group)

            marker_group.add_to(m)

    folium.LayerControl().add_to(m)

    return m


@app.route('/save_map_or_image', methods=['POST'])
def save_map_or_image():
    zoom_inicial = request.form.get('zoomInicial', type=int)
    filename = request.form.get('filename', 'map.html')
   
    if not filename.endswith('.html'):
        filename += '.html'
    download_type = request.form.get('download_type')

    if download_type == 'Baixar HTML':
        m = create_map(filename, zoom_inicial)
        arquivo_temporario = f'{filename}'
        
        # Salvar o mapa no arquivo temporário
        m.save(arquivo_temporario)
        
        # Enviar o arquivo temporário como um anexo
        return send_file(arquivo_temporario, as_attachment=True)
    
    if download_type == 'Baixar Imagem':

        delay=5
        fn='Teste.html'
        tmpurl='Teste.html'.format(path=os.getcwd(),mapfile=fn)
        m.save(fn)

        browser = webdriver.Firefox()
        browser.get(tmpurl)
        #Give the map tiles some time to load
        time.sleep(delay)
        browser.save_screenshot('map.png')
        browser.quit()
        

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

    return render_template('camada.html', vetCamadas=vetCamadas)



if __name__ == '__main__':
    app.run(debug=True)





##################### CODIGO

