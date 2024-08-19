import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
import matplotlib.colors as mcolors
import folium.plugins
from shapely.geometry import shape
from shapely.geometry import Polygon
from shapely.ops import transform
import pyproj

st.set_page_config(page_title="Visualizador de Isocronas", layout="wide")

url_river = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Escudo_del_C_A_River_Plate.svg/194px-Escudo_del_C_A_River_Plate.svg.png"
url_boca = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/CABJ70.png/207px-CABJ70.png"


icon_map = {
    "driving-car": "🚗",
    "cycling-regular": "🚴",
    "foot-walking": "🚶"
}

# Función para obtener las isócronas
def obtener_isocronas(lat, lon, time_limits, api_key, interval, range_type, profile):
    base_url = f'https://api.openrouteservice.org/v2/isochrones/{profile}'

    # Cuerpo de la solicitud
    request_body = {
        'locations': [[lon, lat]],
        'range': time_limits,  # Lista de límites de tiempo en segundos
        'range_type': range_type,
        "interval": interval  # Definido en segundos
    }

    # Encabezados de la solicitud
    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json'
    }

    # Realizar la solicitud POST a la API
    response = requests.post(base_url, json=request_body, headers=headers)

    if response.status_code == 200:
        data = response.json()
        return data['features']
    else:
        st.error(f'Error: {response.status_code}')
        st.write(response.text)
        return None

url_river = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Escudo_del_C_A_River_Plate.svg/194px-Escudo_del_C_A_River_Plate.svg.png"
url_boca = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/CABJ70.png/207px-CABJ70.png"

# Title with smaller River and Boca icons using HTML
# st.markdown(f"""
#     <h1 style='text-align: left;'>
#         Visualizador de Isocronas  (
#         <img src="{url_river}" alt="River Plate" width="40"/>
#         <span style='font-size:18px;'>vs</span> 
#         <img src="{url_boca}" alt="Boca Juniors" width="45"/> )
#     </h1>
#     """, unsafe_allow_html=True)

st.title("Visualizador de Isocronas")

# Entrada de datos en el sidebar
st.sidebar.header("Parámetros de Isócronas")

# Entrada de coordenadas en el sidebar con un valor por defecto
coords_input = st.sidebar.text_area(
    "Ingrese coordenadas (latitud, longitud) separadas por comas:",
    value="-34.54512962753, -58.44982207697944"  # Valor por defecto
)

coords_input_2 = st.sidebar.text_area(
    "Ingrese coordenadas (latitud, longitud) separadas por comas 2:",
    value="-34.630875557459476, -58.36434323027729"  # Valor por defecto
)

# Procesar las coordenadas ingresadas
try:
    lat, lon = map(float, coords_input.strip().split(','))
    coords_list = [(lat, lon)]
except ValueError:
    st.sidebar.error("Por favor ingrese coordenadas válidas en el formato: latitud, longitud")
    coords_list = []

try:
    lat2, lon2 = map(float, coords_input_2.strip().split(','))
    coords_list2 = [(lat2, lon2)]
except ValueError:
    st.sidebar.error("Por favor ingrese coordenadas válidas en el formato: latitud, longitud")
    coords_list = []
# # Entrada de coordenadas en el sidebar
# lat = st.sidebar.number_input("Latitud", value=-34.48351217814145, format="%.6f")
# lon = st.sidebar.number_input("Longitud", value=-58.693829674868425, format="%.6f")

# # Entrada de coordenadas en el sidebar
# lat2 = st.sidebar.number_input("Latitud2", value=-34.48351217814145, format="%.6f")
# lon2 = st.sidebar.number_input("Longitud2", value=-58.693829674868425, format="%.6f")

# Tipo de rango
range_type = st.sidebar.selectbox("Elige tipo de rango", ["distance", "time"], index=1)

# Límite de la isócrona
valor_maximo_isocrona = int(st.sidebar.text_input("Límite Isócrona (minutos para 'time' o metros para 'distance'):", value=50)) * 60

# Cantidad de isócronas
cantidad_isocronas = st.sidebar.slider('Cantidad de Isócronas', 1, 5, value=3)

# Selección del perfil de viaje
profile = st.sidebar.selectbox("Elige el perfil de viaje", ["driving-car", "cycling-regular", "foot-walking"], index=0)

icono = icon_map.get(profile, "")

# Crear el subtítulo dinámico con el icono y el texto del perfil
st.subheader(f"{icono} {profile.replace('-', ' ').title()}")

# Mostrar isócronas
mostrar_isocronas = st.sidebar.checkbox('Mostrar Isócronas')

mostrar_leyenda = st.sidebar.checkbox('Mostrar Leyenda')

col1,spacer,col2 = st.columns([3,0.1, 1])

with col1:

    # Inicializar el mapa-34.58677499359066, -58.39298569145753
    mapa = folium.Map(location=[-34.58677499359066, -58.39298569145753], zoom_start=12, tiles='CartoDB positron')

    api_key = '5b3ce3597851110001cf62480aac3512263444579874635b60aa3a8b'

    # Añadir plugins de Draw y Fullscreen al mapa
    # draw = folium.plugins.Draw(export=False)
    # mapa.add_child(draw)

    folium.plugins.Fullscreen(
        position="topright",
        title="Expand me",
        title_cancel="Exit me",
        force_separate_button=True,
    ).add_to(mapa)

    # Mostrar marcador de la ubicación inicial
    folium.Marker([lat, lon], tooltip="Ubicación inicial").add_to(mapa)

    # Mostrar marcador de la ubicación inicial
    folium.Marker([lat2, lon2], tooltip="Ubicación inicial").add_to(mapa)

    # Generación de isócronas automáticamente si se selecciona la opción
    if mostrar_isocronas:
        time_limits = [valor_maximo_isocrona]
        interval = valor_maximo_isocrona / cantidad_isocronas
        isocronas = obtener_isocronas(lat, lon, time_limits, api_key, interval, range_type, profile)

        if isocronas:
            colores = plt.cm.viridis(np.linspace(0, 1, len(isocronas)))
            colormap = ListedColormap(colores)
            colores = [mcolors.to_hex(colormap(i)) for i in range(colormap.N)]
            color_dict = {}
            isocrone_value = (interval/60)
            
            # Procesar la primera isocrona para calcular su área
            
            first_isocrona = isocronas[-1]

            first_isocrona = first_isocrona['geometry']['coordinates'][0]
            first_isocrona = [(coord[1], coord[0]) for coord in first_isocrona]
            # Crear un objeto Polygon de shapely
            first_isocrona = Polygon(first_isocrona)

            # Definir el proyector para convertir de lat/lon a UTM
            project = pyproj.Transformer.from_crs('epsg:4326', 'epsg:32633', always_xy=True).transform

            # Reproyectar el polígono
            polygon_metric = transform(project, first_isocrona)

            # Calcular el área en metros cuadrados
            area_m2 = polygon_metric.area/ 1e6

            for idx, isocrona in enumerate(isocronas):
                coordinates_p = isocrona['geometry']['coordinates'][0]
                coordinates = [(coord[1], coord[0]) for coord in coordinates_p]
                folium.Polygon(locations=coordinates, color=colores[idx % len(colores)], fill=True, fill_opacity=0.4).add_to(mapa)
                # Añadir un marcador con el tiempo
                color_dict[f"{round(isocrone_value)} min"] = colores[idx % len(colores)]
                isocrone_value = isocrone_value + (interval/60)



        isocronas = obtener_isocronas(lat2, lon2, time_limits, api_key, interval, range_type, profile)

        if isocronas:
            colores = plt.cm.viridis(np.linspace(0, 1, len(isocronas)))
            colormap = ListedColormap(colores)
            colores = [mcolors.to_hex(colormap(i)) for i in range(colormap.N)]
            color_dict = {}
            isocrone_value = (interval/60)

            first_isocrona = isocronas[-1]

            first_isocrona = first_isocrona['geometry']['coordinates'][0]
            first_isocrona = [(coord[1], coord[0]) for coord in first_isocrona]
            # Crear un objeto Polygon de shapely
            first_isocrona = Polygon(first_isocrona)

            # Definir el proyector para convertir de lat/lon a UTM
            project = pyproj.Transformer.from_crs('epsg:4326', 'epsg:32633', always_xy=True).transform

            # Reproyectar el polígono
            polygon_metric = transform(project, first_isocrona)

            # Calcular el área en metros cuadrados
            area_m2_2 = polygon_metric.area/ 1e6

            for idx, isocrona in enumerate(isocronas):
                coordinates_p = isocrona['geometry']['coordinates'][0]
                coordinates = [(coord[1], coord[0]) for coord in coordinates_p]
                folium.Polygon(locations=coordinates, color=colores[idx % len(colores)], fill=True, fill_opacity=0.4).add_to(mapa)
                # Añadir un marcador con el tiempo
                color_dict[f"{round(isocrone_value)} min"] = colores[idx % len(colores)]
                isocrone_value = isocrone_value + (interval/60)
        

                    # Crear la leyenda

            if mostrar_leyenda:       
                legend_html = '''
                <div style="position: fixed; 
                            bottom: 50px; left: 180px; width: 250px; height: auto; 
                            ; z-index:9999; font-size:14px;
                             padding: 10px;">
                    
                '''
                # Añadir cada color y su descripción a la leyenda
                for key, color in color_dict.items():
                    legend_html += f'<i style="background:{color};width:20px;height:20px;float:left;margin-right:8px;"></i>{key}<br>'

                legend_html += '</div>'

                # Añadir la leyenda como un marcador en el mapa
                folium.Marker(
                    location=[lat, lon],  # Ajusta la posición según sea necesario
                    icon=folium.DivIcon(html=legend_html)
                ).add_to(mapa)

        # time_limits = [valor_maximo_isocrona]
        # interval = valor_maximo_isocrona / cantidad_isocronas
        # isocronas = obtener_isocronas(lat2, lon2, time_limits, api_key, interval, range_type, profile)

        # if isocronas:
        #     colores = plt.cm.viridis(np.linspace(0, 1, len(isocronas)))
        #     colormap = ListedColormap(colores)
        #     colores = [mcolors.to_hex(colormap(i)) for i in range(colormap.N)]

        #     for idx, isocrona in enumerate(isocronas):
        #         coordinates_p = isocrona['geometry']['coordinates'][0]
        #         coordinates = [(coord[1], coord[0]) for coord in coordinates_p]
        #         folium.Polygon(locations=coordinates, color=colores[idx % len(colores)], fill=True, fill_opacity=0.4).add_to(mapa)

    # Mostrar el mapa en la aplicación
    st_folium(mapa, width=1200, height=600)


with col2:    



    # Mostrar la primera métrica en la primera columna

    if mostrar_isocronas:


        st.metric(label="Área Isocrona River", value=f"{area_m2:.2f} km²")
        st.metric(label="Área Isocrona Boca", value=f"{area_m2_2:.2f} km²")
