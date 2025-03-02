import os
from dotenv import load_dotenv
load_dotenv()
import requests
from datetime import datetime, timedelta, timezone
from telegram.ext import ContextTypes

def obtener_clima_actual(provincia):
    """
    Consulta el endpoint 'weather' de OpenWeather para obtener el clima actual.
    Devuelve un texto descriptivo.
    """
    ciudad = f"{provincia},ES"
    clave_api = os.getenv("OPENWEATHER_KEY")
    url_api = f"https://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={clave_api}&units=metric&lang=es"
    resp = requests.get(url_api)
    if resp.status_code == 200:
        datos = resp.json()
        temp = datos["main"]["temp"]
        descripcion = datos["weather"][0]["description"]
        return f"Clima en {provincia}: {temp}°C, {descripcion}"
    else:
        return "No se pudo obtener el clima en este momento."

def obtener_pronostico_clima(provincia, zona="UTC+0"):
    """
    Consulta el endpoint 'forecast' de OpenWeather para obtener el pronóstico del día.
    Devuelve (temp_actual, temp_min, temp_max, descripción, viento, nubes).
    El filtrado se basa en la fecha local del usuario, calculada con la 'zona'.
    """
    clave_api = os.getenv("OPENWEATHER_KEY")
    ciudad = f"{provincia},ES"

    # Clima actual
    url_cur = f"https://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={clave_api}&units=metric&lang=es"
    rc = requests.get(url_cur)
    if rc.status_code == 200:
        data_c = rc.json()
        temp_actual = data_c["main"]["temp"]
        descripcion = data_c["weather"][0]["description"]
        viento = data_c["wind"]["speed"]
        nubes = data_c["clouds"]["all"]
    else:
        temp_actual = descripcion = viento = nubes = None

    # Calcular offset de la zona
    try:
        offset_horas = int(zona[4:]) if zona[3] == '+' else -int(zona[4:])
    except ValueError:
        offset_horas = 0
    ahora_usuario = datetime.now(timezone.utc) + timedelta(hours=offset_horas)
    fecha_local = ahora_usuario.date()

    # Pronóstico del día
    url_f = f"https://api.openweathermap.org/data/2.5/forecast?q={ciudad}&appid={clave_api}&units=metric&lang=es"
    rf = requests.get(url_f)
    if rf.status_code == 200:
        data_f = rf.json()
        forecast_hoy = [item for item in data_f.get("list", []) if
            (datetime.fromtimestamp(item["dt"], tz=timezone.utc) + timedelta(hours=offset_horas)).date() == fecha_local]
        if forecast_hoy:
            temps = [it["main"]["temp"] for it in forecast_hoy]
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
    Usa obtener_pronostico_clima para mostrar datos de temperatura min, max, nubes, etc.
    Y si la hora local es antes de las 12, pone "Buenos días" con el nombre/apodo del usuario.
    """
    job = context.job
    chat_id = job.chat_id
    provincia = job.data["provincia"]
    zona = job.data.get("zona", "UTC+0")
    nombre = job.data.get("nombre", "")

    (temp_actual, temp_min, temp_max, desc, viento, nubes) = obtener_pronostico_clima(provincia, zona)

    # Calcular la hora local para decidir el saludo.
    try:
        offset_horas = int(zona[4:]) if zona[3] == '+' else -int(zona[4:])
    except ValueError:
        offset_horas = 0
    hora_local = datetime.now(timezone.utc) + timedelta(hours=offset_horas)

    saludo = f"¡Buenos días, {nombre}!\n" if hora_local.hour < 12 else f"¡Hola, {nombre}!\n"
    mensaje = saludo + f"Este es el clima que hará hoy en {provincia}:\n"

    if None not in (temp_actual, temp_min, temp_max, desc, viento, nubes):
        mensaje += f"Temperatura mínima: {temp_min}°C\n"
        mensaje += f"Temperatura actual: {temp_actual}°C\n"
        mensaje += f"Temperatura máxima: {temp_max}°C\n"
        mensaje += f"Condición: {desc.capitalize()}\n"
        mensaje += f"Viento: {viento} m/s\n"
        mensaje += f"Nubes: {nubes}%\n"
        # Ejemplos de recomendaciones
        if temp_min < 10:
            mensaje += "Hoy hará algo de frío, ¡abrígate bien!\n"
        if temp_max > 25:
            mensaje += "Hace bastante calor, ¡toca piscina!\n"
        if viento and viento > 8:
            mensaje += "Cuidado con el viento...\n"
        if nubes and nubes > 80:
            mensaje += "Podría llover, no vendría mal un paraguas.\n"
    else:
        mensaje += "No se pudo obtener toda la información."

    await context.bot.send_message(chat_id=chat_id, text=mensaje)

def convertir_a_utc(fecha_naive, zona_str):
    """
    Convierte 'fecha_naive' (que es naive) interpretado en zona_str (ej: "UTC+1") a fecha en UTC.
    """
    if fecha_naive is None:
        return None
    from datetime import timedelta, timezone
    signo = zona_str[3]
    try:
        offset_horas = int(zona_str[4:])
    except ValueError:
        offset_horas = 0
    delta = timedelta(hours=offset_horas if signo == '+' else -offset_horas)
    tz_local = timezone(delta)
    fecha_local = fecha_naive.replace(tzinfo=tz_local)
    return fecha_local.astimezone(timezone.utc)

def programar_recordatorio_diario_clima(context, chat_id, provincia, hora_programada, zona_horaria, nombre):
    """
    Programa un job diario a la hora indicada, convirtiéndola a UTC usando zona_horaria.
    Se pasa 'nombre' en job.data para personalizar el saludo.
    """
    now_utc = datetime.now(timezone.utc)
    fecha_naive = datetime.combine(now_utc.date(), hora_programada)
    fecha_programada = convertir_a_utc(fecha_naive, zona_horaria)

    if fecha_programada < now_utc:
        fecha_programada += timedelta(days=1)

    interval = 24 * 3600  # 24 horas
    context.job_queue.run_repeating(
        enviar_recordatorio_diario_clima,
        interval=interval,
        first=fecha_programada,
        chat_id=chat_id,
        data={"provincia": provincia, "zona": zona_horaria, "nombre": nombre}
    )
