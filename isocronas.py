import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
import matplotlib.colors as mcolors
from shapely.geometry import Polygon
from shapely.ops import transform
import pyproj

st.set_page_config(page_title="Visualizador de Isocronas", layout="wide")

# Mapeo de íconos según el perfil de viaje
icon_map = {
    "driving-car": "🚗",
    "cycling-regular": "🚴",
    "foot-walking": "🚶"
}

# Función para obtener las isócronas
def obtener_isocronas(lat, lon, time_limits, api_key, interval, range_type, profile):
    base_url = f'https://api.openrouteservice.org/v2/isochrones/{profile}'

    request_body = {
        'locations': [[lon, lat]],
        'range': time_limits,
        'range_type': range_type,
        "interval": interval
    }

    headers = {
        'Authorization': api_key,
        'Content-Type': 'application/json'
    }

    response = requests.post(base_url, json=request_body, headers=headers)

    if response.status_code == 200:
        return response.json()['features']
    else:
        st.error(f'Error: {response.status_code}')
        st.write(response.text)
        return None

# Configuración de la aplicación
st.title("Visualizador de Isocronas")

# Sidebar para ingresar parámetros
st.sidebar.header("Parámetros de Isócronas")

coords_input = st.sidebar.text_area(
    "Ingrese coordenadas (latitud, longitud) separadas por comas:",
    value="-34.54512962753, -58.44982207697944"  # Valor por defecto
)

# Procesar las coordenadas ingresadas
try:
    lat, lon = map(float, coords_input.strip().split(','))
except ValueError:
    st.sidebar.error("Por favor ingrese coordenadas válidas en el formato: latitud, longitud")
    lat, lon = None, None

# Tipo de rango
range_type = st.sidebar.selectbox("Elige tipo de rango", ["distance", "time"], index=1)

# Parámetros adicionales
valor_maximo_isocrona = int(st.sidebar.text_input("Límite Isócrona (minutos o metros):", value=50)) * 60
cantidad_isocronas = st.sidebar.slider('Cantidad de Isócronas', 1, 5, value=3)
profile = st.sidebar.selectbox("Elige el perfil de viaje", ["driving-car", "cycling-regular", "foot-walking"], index=0)
icono = icon_map.get(profile, "")

# Crear subtítulo
st.subheader(f"{icono} {profile.replace('-', ' ').title()}")

# Mostrar mapa
if lat is not None and lon is not None:
    mapa = folium.Map(location=[lat, lon], zoom_start=12, tiles='CartoDB positron')

    # Mostrar marcador inicial
    folium.Marker([lat, lon], tooltip="Ubicación inicial").add_to(mapa)

    # Generar y mostrar isócronas
    time_limits = [valor_maximo_isocrona]
    interval = valor_maximo_isocrona / cantidad_isocronas

    isocronas = obtener_isocronas(lat, lon, time_limits, '5b3ce3597851110001cf62480aac3512263444579874635b60aa3a8b', interval, range_type, profile)

    if isocronas:
        colores = plt.cm.viridis(np.linspace(0, 1, len(isocronas)))
        colormap = ListedColormap(colores)
        colores = [mcolors.to_hex(colormap(i)) for i in range(colormap.N)]
        color_dict = {}
        isocrone_value = (interval / 60)

        first_isocrona = isocronas[-1]['geometry']['coordinates'][0]
        first_isocrona = [(coord[1], coord[0]) for coord in first_isocrona]

        # Crear el polígono y calcular el área
        polygon = Polygon(first_isocrona)
        project = pyproj.Transformer.from_crs('epsg:4326', 'epsg:32721', always_xy=True).transform
        polygon_metric = transform(project, polygon)
        area_km2 = polygon_metric.area / 1e6

        for idx, isocrona in enumerate(isocronas):
            coordinates_p = isocrona['geometry']['coordinates'][0]
            coordinates = [(coord[1], coord[0]) for coord in coordinates_p]
            folium.Polygon(locations=coordinates, color=colores[idx % len(colores)], fill=True, fill_opacity=0.4).add_to(mapa)
            color_dict[f"{round(isocrone_value)} min"] = colores[idx % len(colores)]
            isocrone_value += (interval / 60)

        # Leyenda
        legend_html = '''
            <div style="position: fixed; 
                        bottom: 50px; left: 50px; width: 250px; height: auto; 
                        z-index:9999; font-size:14px;
                        padding: 10px; background-color: white; border: 2px solid black;">
        '''
        for key, color in color_dict.items():
            legend_html += f'<i style="background:{color};width:20px;height:20px;float:left;margin-right:8px;"></i>{key}<br>'
        legend_html += '</div>'

        folium.Marker(
            location=[lat, lon],
            icon=folium.DivIcon(html=legend_html)
        ).add_to(mapa)

        st.metric(label="Área de la Isocrona", value=f"{area_km2:.2f} km²")

    # Mostrar el mapa
    st_folium(mapa, width=1200, height=600)
