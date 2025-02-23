import os
from dotenv import load_dotenv
load_dotenv()
import requests
from datetime import datetime, timedelta, timezone
from telegram.ext import ContextTypes

def obtener_clima_actual(provincia):
    """
    Consulta el endpoint 'weather' de OpenWeather para obtener el clima actual.
    Retorna un texto descriptivo.
    """
    ciudad = f"{provincia},ES"
    clave_api = os.getenv("OPENWEATHER_KEY") # Para la KEY de registro de OpenWeather
    url_api = f"https://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={clave_api}&units=metric&lang=es"
    respuesta = requests.get(url_api)
    if respuesta.status_code == 200:
        datos = respuesta.json()
        temp = datos["main"]["temp"]
        descripcion = datos["weather"][0]["description"]
        return f"Clima en {provincia}: {temp}°C, {descripcion}"
    else:
        return "No se pudo obtener el clima en este momento."

def obtener_pronostico_clima(provincia, zona="UTC+0"):
    """
    Consulta el endpoint 'forecast' de OpenWeather para obtener el pronóstico del día.
    Devuelve una tupla:
      (temp_actual, temp_min, temp_max, descripción, viento, nubes)
    usando la fecha local del usuario, calculada a partir del offset indicado en 'zona'.
    """
    clave_api = os.getenv("OPENWEATHER_KEY")
    ciudad = f"{provincia},ES"

    # Clima actual
    url_current = f"https://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={clave_api}&units=metric&lang=es"
    r_current = requests.get(url_current)
    if r_current.status_code == 200:
        data_current = r_current.json()
        temp_actual = data_current["main"]["temp"]
        descripcion = data_current["weather"][0]["description"]
        viento = data_current["wind"]["speed"]
        nubes = data_current["clouds"]["all"]
    else:
        temp_actual = descripcion = viento = nubes = None

    # Calcular el offset a partir de 'zona'
    try:
        offset = int(zona[4:]) if zona[3] == '+' else -int(zona[4:])
    except ValueError:
        offset = 0
    # Fecha local del usuario
    usuario_ahora = datetime.now(timezone.utc) + timedelta(hours=offset)
    hoy_local = usuario_ahora.date()

    # Pronóstico del día
    url_forecast = f"https://api.openweathermap.org/data/2.5/forecast?q={ciudad}&appid={clave_api}&units=metric&lang=es"
    r_forecast = requests.get(url_forecast)
    if r_forecast.status_code == 200:
        data_forecast = r_forecast.json()
        forecast_hoy = [item for item in data_forecast.get("list", [])
                        if (datetime.fromtimestamp(item["dt"], tz=timezone.utc) + timedelta(hours=offset)).date() == hoy_local]
        if forecast_hoy:
            temps = [item["main"]["temp"] for item in forecast_hoy]
            temp_min = min(temps)
            temp_max = max(temps)
        else:
            temp_min = temp_max = None
    else:
        temp_min = temp_max = None

    return temp_actual, temp_min, temp_max, descripcion, viento, nubes

async def enviar_recordatorio_diario_clima(context: ContextTypes.DEFAULT_TYPE):
    """
    Callback del job que envía el recordatorio diario del clima.
    Si la hora local (calculada según la zona) es anterior a las 12, se saluda con "Buenos días".
    Se incluye un resumen del clima: temperaturas mínima, actual, máxima, descripción, viento y nubes.
    Además, se añaden recomendaciones según las condiciones (por ejemplo, "¡Abrigate bien!" o "¡Hoy toca piscina!").
    """
    job = context.job
    chat_id = job.chat_id
    provincia = job.data["provincia"]
    zona = job.data.get("zona", "UTC+0")
    nombre = job.data.get("nombre", "")
    temp_actual, temp_min, temp_max, descripcion, viento, nubes = obtener_pronostico_clima(provincia, zona)
    # Calcular la hora local actual según la zona
    try:
        offset = int(zona[4:]) if zona[3] == '+' else -int(zona[4:])
    except ValueError:
        offset = 0
    local_now = (datetime.now(timezone.utc) + timedelta(hours=offset))
    if local_now.hour < 12:
        saludo = f"¡Buenos días, {nombre}!\n"
    else:
        saludo = f"¡Hola, {nombre}!\n"
    mensaje = saludo + f"Este es el clima que va a hacer hoy en {provincia}:\n"
    if None not in (temp_actual, temp_min, temp_max, descripcion, viento, nubes):
        mensaje += f"Temperatura mínima: {temp_min}°C\n"
        mensaje += f"Temperatura actual: {temp_actual}°C\n"
        mensaje += f"Temperatura máxima: {temp_max}°C\n"
        mensaje += f"Condición: {descripcion.capitalize()}\n"
        mensaje += f"Viento: {viento} m/s\n"
        mensaje += f"Nubes: {nubes}%\n"
        # Recomendaciones según condiciones:
        if temp_min < 10:
            mensaje += "Hoy hará algo de frio, ¡abrígate bien!\n"
        if temp_max > 25:
            mensaje += "Hoy va a hacer bastante calor, ¡aprovecha y ve a la piscina!\n"
        if viento > 8:
            mensaje += "Va a hacer bastante viento, ¡ten cuidado no salgas volando!\n"
        if nubes > 80:
            mensaje += "No sería raro si lloviese, ¡ve preparado!\n"
    else:
        mensaje += "No se pudo obtener toda la información."
    await context.bot.send_message(chat_id=chat_id, text=mensaje)

def convertir_a_utc(fecha, zona_str):
    """
    Convierte una hora naive (fecha) interpretada en la zona dada (ej: "UTC+1")
    a una hora en UTC.
    """
    if fecha is None:
        return None
    if fecha.tzinfo is not None:
        return fecha
    signo = zona_str[3]
    try:
        offset = int(zona_str[4:])
    except ValueError:
        offset = 0
    delta = timedelta(hours=offset if signo == '+' else -offset)
    tz = timezone(delta)
    fecha_local = fecha.replace(tzinfo=tz)
    return fecha_local.astimezone(timezone.utc)

def programar_recordatorio_diario_clima(context, chat_id, provincia, hora_programada, zona_horaria, nombre):
    """
    Programa un job repetitivo que envía el recordatorio diario del clima a la hora indicada.
    La hora naive se convierte a UTC usando la zona seleccionada.
    Se incluye la zona y el nombre en job.data para personalizar el mensaje.
    """
    ahora = datetime.now(timezone.utc)
    fecha_naive = datetime.combine(ahora.date(), hora_programada)
    fecha_programada = convertir_a_utc(fecha_naive, zona_horaria)
    if fecha_programada < datetime.now(timezone.utc):
        fecha_programada += timedelta(days=1)
    intervalo = 24 * 3600  # 24 horas en segundos
    context.job_queue.run_repeating(
        enviar_recordatorio_diario_clima,
        interval=intervalo,
        first=fecha_programada,
        chat_id=chat_id,
        data={"provincia": provincia, "zona": zona_horaria, "nombre": nombre}
    )
