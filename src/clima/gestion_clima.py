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
        temp_float = datos["main"]["temp"]
        temp = int(round(temp_float))

        desc = datos["weather"][0]["description"]

        viento_m_s = datos["wind"]["speed"]
        viento_kmh = int(round(viento_m_s * 3.6))

        texto = (
            f"Clima actual en {provincia}:\n"
            f"---------------------------\n"
            f"Temperatura: {temp} °C\n"
            f"Estado: {desc.capitalize()}\n"
            f"Viento: {viento_kmh} km/h\n"
            f"---------------------------\n"
        )
        return texto
    else:
        return "No se pudo obtener el clima en este momento."

def obtener_pronostico_clima(provincia, zona="UTC+0"):
    """
    Obtiene la temperatura actual, mínima y máxima en las próximas 24 horas,
    así como la descripción del clima, el viento (convertido a km/h) y el
    porcentaje de nubes. Las temperaturas y el viento se devuelven sin decimales.

    Retorna:
      (temp_actual, temp_min, temp_max, descripcion, viento_kmh, nubes)

    donde cada uno puede ser None si no se pudo obtener.
    El viento se expresa en km/h (en lugar de m/s).
    """

    clave_api = os.getenv("OPENWEATHER_KEY")
    ciudad = f"{provincia},ES"

    # 1. Clima actual (temp_actual, descripción, viento, nubes)
    url_cur = f"https://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={clave_api}&units=metric&lang=es"
    rc = requests.get(url_cur)
    if rc.status_code == 200:
        data_c = rc.json()
        # Tomamos la temperatura y la descripción
        temp_actual = data_c["main"]["temp"]
        descripcion = data_c["weather"][0]["description"]
        viento_m_s = data_c["wind"]["speed"]
        nubes = data_c["clouds"]["all"]

        temp_actual = int(round(temp_actual)) if temp_actual is not None else None
        viento_kmh = int(round(viento_m_s * 3.6)) if viento_m_s is not None else None
    else:
        temp_actual = None
        descripcion = None
        viento_kmh = None
        nubes = None

    # 2. Calculamos la hora local según la zona y definimos un rango de 24h a futuro
    try:
        offset_horas = int(zona[4:]) if zona[3] == '+' else -int(zona[4:])
    except ValueError:
        offset_horas = 0

    now_utc = datetime.now(timezone.utc)
    now_local = now_utc + timedelta(hours=offset_horas)
    limit_local = now_local + timedelta(hours=24)

    # 3. Llamamos al endpoint de 'forecast' para las próximas horas
    url_f = f"https://api.openweathermap.org/data/2.5/forecast?q={ciudad}&appid={clave_api}&units=metric&lang=es"
    rf = requests.get(url_f)
    if rf.status_code == 200:
        data_f = rf.json()
        forecast_list = data_f.get("list", [])

        # 4. Filtramos los Timestamps entre now_local y now_local + 24h
        forecast_prox_24 = []
        for item in forecast_list:
            dt_utc = datetime.fromtimestamp(item["dt"], tz=timezone.utc)
            dt_local = dt_utc + timedelta(hours=offset_horas)
            if now_local <= dt_local <= limit_local:
                forecast_prox_24.append(item)

        # 5. Obtenemos temp_min y temp_max del intervalo
        if forecast_prox_24:
            temps = [f["main"]["temp"] for f in forecast_prox_24]
            temp_min = int(round(min(temps)))
            temp_max = int(round(max(temps)))
        else:
            temp_min = None
            temp_max = None
    else:
        temp_min = None
        temp_max = None

    return temp_actual, temp_min, temp_max, descripcion, viento_kmh, nubes


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

    (temp_actual, temp_min, temp_max, desc, viento_kmh, nubes) = obtener_pronostico_clima(provincia, zona)

    # Calcular la hora local para decidir el saludo.
    try:
        offset_horas = int(zona[4:]) if zona[3] == '+' else -int(zona[4:])
    except ValueError:
        offset_horas = 0
    hora_local = datetime.now(timezone.utc) + timedelta(hours=offset_horas)

    saludo = f"¡Buenos días <b>{nombre}</b>!\n" if hora_local.hour < 12 else f"¡Hola, {nombre}!\n"
    mensaje = saludo + f"Este es el clima para las <b>PRÓXIMAS 24 HORAS</b> en {provincia}:\n\n"

    if None not in (temp_actual, temp_min, temp_max, desc, viento_kmh, nubes):
        mensaje += f"<b>Temperatura mínima</b>: {round(temp_min)}°C\n"
        mensaje += f"<b>Temperatura actual</b>: {round(temp_actual)}°C\n"
        mensaje += f"<b>Temperatura máxima</b>: {round(temp_max)}°C\n"
        mensaje += f"<b>Condición</b>: {desc.capitalize()}\n"
        mensaje += f"<b>Viento</b>: {viento_kmh} km/h\n"
        mensaje += f"<b>Nubes</b>: {nubes}%\n\n"

        if temp_min < 10:
            mensaje += "Hoy hará un frrrrio que pela, abrigate!\n"
        if temp_max > 25:
            mensaje += "Hoy hará bastante calor, date un chapuzón!\n"
        if viento_kmh and viento_kmh > 8:
            mensaje += "Ve con cuidado no salgas volando hoy!\n"
        if nubes and nubes > 80:
            mensaje += "Podría llover, no te olvides del paraguas!\n"
    else:
        mensaje += (
            "No se pudo obtener todos los datos.\n"
            "Posiblemente no haya pronósticos próximos o la API no devolvió información."
        )

    await context.bot.send_message(chat_id=chat_id, text=mensaje, parse_mode="HTML")

def convertir_a_utc(fecha_naive, zona_str):
    """
    Convierte 'fecha_naive' (que es naive) interpretado en zona_str (ej: "UTC+1") a fecha en UTC.
    """
    if fecha_naive is None:
        return None
    signo = zona_str[3]
    try:
        offset_horas = int(zona_str[4:])
    except ValueError:
        offset_horas = 0
    from datetime import timezone, timedelta
    delta = timedelta(hours=offset_horas if signo == '+' else -offset_horas)
    tz_local = timezone(delta)
    fecha_local = fecha_naive.replace(tzinfo=tz_local)
    return fecha_local.astimezone(timezone.utc)

def programar_recordatorio_diario_clima(context, chat_id, provincia, hora_programada, zona_horaria, nombre, record_id):
    """
    Programa un job repetitivo diario que, a la hora local especificada (convertida a UTC),
    envíe el recordatorio de clima. Se incluye record_id en job.data para poder
    cancelarlo/reprogramarlo si el usuario lo edita.
    """
    from datetime import datetime, timezone, timedelta

    now_utc = datetime.now(timezone.utc)
    fecha_naive = datetime.combine(now_utc.date(), hora_programada)
    fecha_programada = convertir_a_utc(fecha_naive, zona_horaria)

    # Si ya pasó la hora de hoy, lo programamos para mañana
    if fecha_programada < now_utc:
        fecha_programada += timedelta(days=1)

    interval = 24 * 3600  # 24 horas
    context.job_queue.run_repeating(
        enviar_recordatorio_diario_clima,
        interval=interval,
        first=fecha_programada,
        chat_id=chat_id,
        name=f"clima_{record_id}",
        data={
            "provincia": provincia,
            "zona": zona_horaria,
            "nombre": nombre,
            "record_id": record_id  # ¡Importante para poder cancelar luego!
        }
    )
