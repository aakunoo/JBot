import os
import requests

def obtener_clima_actual_imagen(provincia):
    """
    Consulta el endpoint 'weather' de OpenWeather para obtener el clima actual.
    Retorna una tupla (texto, None) ya que en esta versión no se usan imágenes.
    """
    ciudad = f"{provincia},ES"
    clave_api = os.getenv("OPENWEATHER_KEY")
    url_api = f"https://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={clave_api}&units=metric&lang=es"
    respuesta = requests.get(url_api)
    if respuesta.status_code == 200:
        datos = respuesta.json()
        temperatura = datos["main"]["temp"]
        descripcion = datos["weather"][0]["description"]
        texto = f"Clima en {provincia}: {temperatura}°C, {descripcion}"
        return texto, None
    else:
        return "No se pudo obtener el clima en este momento.", None
