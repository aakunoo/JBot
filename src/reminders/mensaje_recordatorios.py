from datetime import datetime, timezone, timedelta
from telegram.ext import ContextTypes
from src.database import obtener_todos_los_recordatorios

def ahora_utc():
    """Devuelve la hora actual en UTC con offset-aware. (Indica explicitamente que es UTC)"""
    return datetime.now(timezone.utc)

'''
-----------------------------------------------------------------------------------
Funciones que se usan como callbacks para el JobQueue de recordatorios
-----------------------------------------------------------------------------------
'''
async def enviar_recordatorio_inicio(context: ContextTypes.DEFAULT_TYPE):
    """
    Callback que se ejecuta en la hora de inicio del recordatorio.
    Manda un mensaje indicando que el recordatorio ha comenzado.
    """
    job = context.job
    chat_id = job.chat_id
    datos = job.data
    titulo = datos.get("titulo", "")
    descripcion = datos.get("descripcion", "")
    mensaje = f"¡Empieza tu recordatorio!\n\nTítulo: {titulo}\n{descripcion}"
    await context.bot.send_message(chat_id=chat_id, text=mensaje)

async def enviar_recordatorio_repeticion(context: ContextTypes.DEFAULT_TYPE):
    """
    Callback que se repite con cierta frecuencia (diaria, semanal, etc.)
    avisándole al usuario que debe cumplir con su recordatorio.
    """
    job = context.job
    chat_id = job.chat_id
    datos = job.data
    titulo = datos.get("titulo", "")
    descripcion = datos.get("descripcion", "")
    mensaje = f"¡Recuerda cumplir con tu recordatorio!\n\nTítulo: {titulo}\n{descripcion}"
    await context.bot.send_message(chat_id=chat_id, text=mensaje)


async def enviar_recordatorio_fin(context: ContextTypes.DEFAULT_TYPE):
    """
    Callback que se ejecuta en la hora de finalización del recordatorio.
    Envía un mensaje notificando que el recordatorio ha terminado y cancela
    todos los jobs asociados a ese recordatorio.
    """
    job = context.job
    chat_id = job.chat_id
    datos = job.data
    titulo = datos.get("titulo", "")
    record_id = datos.get("record_id")

    mensaje = f"¡Finaliza el recordatorio!\nTítulo: {titulo}"
    await context.bot.send_message(chat_id=chat_id, text=mensaje)

    # Cancelamos todos los jobs asociados a este recordatorio
    cancelar_job_por_record_id(context, record_id)


def timezone_from_string(zona_str: str):
    """
    Recibe un string tipo 'UTC+1', 'UTC-3' y devuelve un objeto timezone
    con ese offset. Si no puede parsear, vuelve timezone.utc por defecto.
    """
    if not zona_str.startswith("UTC"):
        return timezone.utc

    signo = zona_str[3]
    try:
        offset_horas = int(zona_str[4:])
    except ValueError:
        offset_horas = 0

    delta = timedelta(hours=offset_horas if signo == '+' else -offset_horas)
    return timezone(delta)

def si_naive_pasar_utc(fecha, zona_str):
    """
    Si 'fecha' es naive (sin tzinfo), la interpretamos en la zona local
    dada por 'zona_str' y la convertimos a UTC. Si ya es offset-aware,
    se devuelve tal cual. Si fecha es None, retorna None.
    """
    if fecha is None:
        return None

    if fecha.tzinfo is not None:
        # Ya es offset-aware
        return fecha

    # Interpreto la fecha naive con la zona local
    tz_local = timezone_from_string(zona_str)
    fecha_local = fecha.replace(tzinfo=tz_local)
    # Convertimos a UTC
    return fecha_local.astimezone(timezone.utc)

'''
-----------------------------------------------------------------------------------
Programar un recordatorio concreto en el JobQueue
-----------------------------------------------------------------------------------
'''
def programar_recordatorio(context, recordatorio, record_id=None):
    """
    Programa en el JobQueue el inicio, la repetición y el fin del recordatorio,
    usando los datos del dict 'recordatorio'.

    - recordatorio: dict con claves como "chat_id", "titulo", "descripcion",
      "fecha_hora_inicio", "frecuencia", "fecha_hora_fin", "zona_horaria".
    - record_id: id del recordatorio en la base de datos (string u ObjectId),
      para poder cancelarlo luego buscando job.data["record_id"] == record_id.
    """
    chat_id = recordatorio["chat_id"]
    titulo = recordatorio.get("titulo", "")
    descripcion = recordatorio.get("descripcion", "")
    fecha_inicio = recordatorio.get("fecha_hora_inicio")
    freq = recordatorio.get("frecuencia", {"tipo": "ninguna", "valor": None})
    fecha_fin = recordatorio.get("fecha_hora_fin")
    zona_str = recordatorio.get("zona_horaria", "UTC+0")

    # Convertir a UTC si es naive
    fecha_inicio_utc = si_naive_pasar_utc(fecha_inicio, zona_str)
    fecha_fin_utc = si_naive_pasar_utc(fecha_fin, zona_str)
    now_utc = ahora_utc()

    # 1) INICIO: run_once
    if fecha_inicio_utc and fecha_inicio_utc > now_utc:
        context.job_queue.run_once(
            enviar_recordatorio_inicio,
            when=fecha_inicio_utc,
            chat_id=chat_id,
            name=f"record_inicio_{record_id}",
            data={
                "record_id": record_id,
                "titulo": titulo,
                "descripcion": descripcion,
                "freq": freq
            }
        )

    # 2) REPETICIÓN: dependiendo de freq
    tipo_frec = freq["tipo"]
    valor_frec = freq["valor"]

    def _repetir(interval, first_moment):
        context.job_queue.run_repeating(
            enviar_recordatorio_repeticion,
            interval=interval,
            first=first_moment,
            chat_id=chat_id,
            name=f"record_rep_{record_id}",
            data={
                "record_id": record_id,
                "titulo": titulo,
                "descripcion": descripcion
            }
        )

    if tipo_frec == "diaria" and fecha_inicio_utc:
        primera_rep = fecha_inicio_utc + timedelta(days=1)
        if primera_rep > now_utc:
            _repetir(24 * 3600, primera_rep)

    elif tipo_frec == "semanal" and fecha_inicio_utc:
        primera_rep = fecha_inicio_utc + timedelta(days=7)
        if primera_rep > now_utc:
            _repetir(7 * 24 * 3600, primera_rep)

    elif tipo_frec == "cada_x_dias" and valor_frec and fecha_inicio_utc:
        primera_rep = fecha_inicio_utc + timedelta(days=valor_frec)
        if primera_rep > now_utc:
            _repetir(valor_frec * 24 * 3600, primera_rep)

    elif tipo_frec == "cada_x_horas" and valor_frec and fecha_inicio_utc:
        primera_rep = fecha_inicio_utc + timedelta(hours=valor_frec)
        if primera_rep > now_utc:
            _repetir(valor_frec * 3600, primera_rep)

    # 3) FIN: run_once
    if fecha_fin_utc and fecha_fin_utc > now_utc:
        context.job_queue.run_once(
            enviar_recordatorio_fin,
            when=fecha_fin_utc,
            chat_id=chat_id,
            name=f"record_fin_{record_id}",
            data={
                "record_id": record_id,
                "titulo": titulo
            }
        )

'''
-----------------------------------------------------------------------------------
Cancelar un recordatorio del job_queue buscando su record_id
-----------------------------------------------------------------------------------
'''
def cancelar_job_por_record_id(context, record_id):
    """
    Busca todos los jobs en job_queue y elimina aquel que
    tenga job.data["record_id"] == record_id.
    """
    if not record_id:
        return

    for job in context.job_queue.jobs():
        if job.data and job.data.get("record_id") == record_id:
            job.schedule_removal()

'''
-----------------------------------------------------------------------------------
Reprogramar todos los recordatorios al iniciar el bot
-----------------------------------------------------------------------------------
'''
async def reprogramar_todos_los_recordatorios(context):
    """
    Se llama al arrancar el bot para reprogramar cada recordatorio
    existente en la BD. Esto es útil por si el bot se reinicia y
    queremos restaurar los jobs.
    """
    lista = obtener_todos_los_recordatorios()  # Función en database.py, sin filtrar por chat_id
    now_utc = ahora_utc()

    for r in lista:
        # Uso str para convertir ObjectId a string y almacenarlo
        record_id = str(r["_id"])

        # Ajustamos fecha_inicio y fecha_fin a UTC si están naive
        fecha_inicio = r.get("fecha_hora_inicio")
        fecha_fin = r.get("fecha_hora_fin")
        zona_str = r.get("zona_horaria", "UTC+0")

        if fecha_inicio:
            r["fecha_hora_inicio"] = si_naive_pasar_utc(fecha_inicio, zona_str)
        if fecha_fin:
            r["fecha_hora_fin"] = si_naive_pasar_utc(fecha_fin, zona_str)

        programar_recordatorio(context, r, record_id=record_id)
