import streamlit as st
from skyfield.api import load, Topos
from datetime import datetime
import pandas as pd
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
import pytz

# Inicializando as ferramentas que vamos usar
ts = load.timescale()
planetas = load ('de421.bsp') # Este arquivo tem as posições dos planetas da NASA

def descobrir_signo(graus):
    signos = [
        "Áries", "Touro", "Gêmeos", "Câncer", "Leão", "Virgem", 
        "Libra", "Escorpião", "Sagitário", "Capricórnio", "Aquário", "Peixes"
        
    ]
    #O sinal % 360 garante que o número esteja sempre no círculo
    #Dividir por 30 dá o índice do signo (0 a 11)
    indice = int((graus %360) / 30)
    return signos[indice]
    
def descobrir_elemento(signo):
    elementos = {
        "Fogo": ["Áries", "Leão", "Sagitário"],
        "Terra": ["Touro", "Virgem", "Capricórnio"],
        "Ar": ["Gêmeos", "Libra", "Aquário"],
        "Água": ["Câncer", "Escorpião", "Peixes"]
    }
    for elemento, lista in elementos.items():
        if signo in lista:
            return elemento
    return "N/A"
    
def buscar_dados_cidade(nome_cidade):
    geolocator = Nominatim(user_agent="bah60x_mapa")
    try:
        # Busca a cidade na internet
        localizacao = geolocator.geocode(nome_cidade, timeout=10)
        
        if localizacao:
            lat = localizacao.latitude
            lon = localizacao.longitude
            
            #Descobre o fudo horário automaticamente
            tf = TimezoneFinder()
            fuso_str = tf.timezone_at(lng=lon, lat=lat)
            
            return lat, lon, fuso_str
        else:
            #Se o código chegar aqui, é porque o Goolge/Nominatim não achou o nome da cidade
            return None, None, None
    except Exception as e:
        #Se der erro ele mostra aqui
        st.error(f"Erro técnico: {e}")
        return None, None, None

def calcular_astros(data_nasc, hora_nasc, fuso_str, lat, lon):
    #1. Ajustando o Fuso Horário
    tz = pytz.timezone(fuso_str)
    dt = datetime.combine(data_nasc, hora_nasc)
    dt_local = tz.localize(dt)
    dt_utc = dt_local.astimezone(pytz.utc)
    
    #2. Criando o momento no tempo da NASA
    tempo = ts.from_datetime(dt_utc)
    
    #3. Definindo o local na Terra (Onde você estava)
    onde_estou = planetas['earth'] + Topos(latitude_degrees=lat, longitude_degrees=lon)
    
    #4. Lista completa de astros
    astros_nomes = {
        'sun': 'Sol',
        'moon': 'Lua',
        'mercury': 'Mercúrio',
        'venus': 'Vênus',
        'mars': 'Marte',
        'jupiter barycenter': 'júpiter',
        'saturn barycenter': 'Saturno',
        'uranus barycenter': 'Urano',
        'neptune barycenter': 'Netuno',
        'pluto barycenter': 'Plutão'
        }
    resultados = []
    for chave, nome in astros_nomes.items():
        #1. Localiza o astro no céu
        posicao = onde_estou.at(tempo).observe(planetas[chave]).apparent()
            
        #2. Pega a Longitude (Signo)
        lat_ecl, lon_ecl, dist = posicao.ecliptic_latlon()
        
        #3. Pega a altitude (para saber se está acima do horizonte)
        alt, az, d = posicao.altaz()
        
        #4. Adiciona na nossa lista com o signo e elemento!
        signo_nome = descobrir_signo(lon_ecl.degrees)
        elemento = descobrir_elemento(signo_nome)
        
        resultados.append({
            "Ponto": nome,
            "Signo": signo_nome,
            "Elemento": elemento,
            "Graus": round(lon_ecl.degrees %30, 2), # Graus dentro do signo (0 a 30)
            "Altitude": round(alt.degrees, 2)
        })
         
    return resultados 
        
# 1. Criando o Título Principal
st.title("Ferramentas holísticas")

# 2. Criando as duas opções no topo (botões de navegação)
aba_astral, aba_numerologia = st.tabs (["🔭 Mapa Astral", "🔢 Mapa Numerológico"])

# 3. O que aparece na aba Mapa Astral
with aba_astral:
    st.header("Seu Mapa Astral")
    st.write("Descubra a posição dos astros no seu nascimento.")
    
    # Aqui colocamos os campos do mapa astral
    cidade = st.text_input("Em qual cidade você naceu?")
    data_nasc = st.date_input(
    "Data de nascimento",
    value=datetime.now(), #Define o dia de hoje como padrão
    format="DD/MM/YYYY",
    min_value=datetime(1900, 1, 1), # Permite datas desde 1900
    max_value=datetime(2100, 12, 31), #Define um limite no futuro
    key="data_astral"
)
    st.write("Hora de nascimento:")
    col_hora, col_min = st.columns(2)
    with col_hora:
        h_val = st.number_input("Hora", min_value=0, max_value=23, value=12, step=1)
    with col_min:
        m_val = st.number_input("Minuto", min_value=0, max_value=59, value=0, step=1)
    
    #Criamos a hora final direto desses números
    from datetime import time
    hora_final = time(h_val, m_val)

    if st.button("Gerar meu Mapa Astral"):
        if cidade.strip():
            with st.spinner ('Consultando os astros e o GPS...'):
                lat, lon, fuso = buscar_dados_cidade(cidade)
                if lat:
                    st.success(f"Cidade Encontrada!")
                    mapa = calcular_astros(data_nasc, hora_final, fuso, lat, lon)
                    
                    st.subheader("Posições encontradas:")
                    df = pd.DataFrame(mapa)
                    st.table(df)
                else:
                    st.error("Não encontrei a cidade.")
        else:
            st.warning("Por favor, digite o nome de uma cidade.")

        #Esse spinner é o loading visual
            with st.spinner('Consultando os astros e o GPS...'):
                lat, lon, fuso = buscar_dados_cidade(cidade)
                if lat:
                    st.success(f"Cidade encontrada!")
                    st.write (f"**Latitude:** {lat:.2f} | **Longitude:** {lon:.2f}")
                    st.info(f"**Fuso Horário:** {fuso}")
                    
                    mapa = calcular_astros(data_nasc, hora_nasc, fuso, lat, lon)
                    
                    st.subheader("Posição encontradas:")
                    df = pd.DataFrame(mapa)
                    st.table(df)
                else:
                    #Adicione isso para o usuario nao ficar no vácuo
                    st.error("Não consegui encontrar sua cidade. Tente: Cidade,Estado")
                    
           
# 4. O que aparece na Numerologia
with aba_numerologia:
    st.header("Sua Numerologia")
    st.write("Transforme seu nome e data de nasc em números de destino")
    
    nome_completo = st.text_input("Digite seu nome completo sem acentos)")
    data_nasc_num = st.date_input (
        "Data de nascimento",
        value=datetime.now(),
        format="DD/MM/YYYY",
        min_value=datetime(1900, 1, 1),
        max_value=datetime(2100, 12,31),
        key="data_num"
)
    
    if st.button("Calcular minha Numerologia"):
        st.success ("Calculando seus números mestres...")        

