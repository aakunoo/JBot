from datetime import datetime, timezone, timedelta
from telegram.ext import ContextTypes
from src.database import obtener_todos_los_recordatorios

def ahora_utc():
    """Devuelve la hora actual en UTC con offset-aware. (Indica explicitamente que es UTC)"""
    return datetime.now(timezone.utc)

'''
------------------------------------------------------------------------------
 Callbacks para el JobQueue
------------------------------------------------------------------------------ '''

async def enviar_recordatorio_inicio(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    datos = context.job.data
    titulo = datos.get("titulo", "")
    descripcion = datos.get("descripcion", "")
    mensaje = f"¡Empieza tu recordatorio!\n\nTítulo: {titulo}\n{descripcion}"
    await context.bot.send_message(chat_id=chat_id, text=mensaje)


async def enviar_recordatorio_repeticion(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    datos = context.job.data
    titulo = datos.get("titulo", "")
    descripcion = datos.get("descripcion", "")
    mensaje = f"¡Recuerda cumplir con tu recordatorio!\n\nTítulo: {titulo}\n{descripcion}"
    await context.bot.send_message(chat_id=chat_id, text=mensaje)


async def enviar_recordatorio_fin(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.chat_id
    datos = context.job.data
    titulo = datos.get("titulo", "")
    mensaje = f"¡Finaliza el recordatorio!\nTítulo: {titulo}"
    await context.bot.send_message(chat_id=chat_id, text=mensaje)


def timezone_from_string(zona_str: str):
    """
    Recibe un string tipo "UTC+1", "UTC-3" y devuelve un objeto timezone
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


'''
----------------------------------
Programar un recordatorio concreto
---------------------------------- s '''

def programar_recordatorio(context, recordatorio):
    chat_id = recordatorio["chat_id"]
    titulo = recordatorio.get("titulo", "")
    descripcion = recordatorio.get("descripcion", "")
    fecha_inicio = recordatorio.get("fecha_hora_inicio")
    freq = recordatorio.get("frecuencia", {"tipo": "ninguna", "valor": None})
    fecha_fin = recordatorio.get("fecha_hora_fin")
    zona_str = recordatorio.get("zona_horaria", "UTC+0")

    # Convertir a UTC si es naive
    fecha_inicio = si_naive_pasar_utc(fecha_inicio, zona_str)
    fecha_fin = si_naive_pasar_utc(fecha_fin, zona_str)

    now_utc = ahora_utc()

    # 1) INICIO
    if fecha_inicio and fecha_inicio > now_utc:
        context.job_queue.run_once(
            enviar_recordatorio_inicio,
            when=fecha_inicio,
            chat_id=chat_id,
            data={"titulo": titulo, "descripcion": descripcion, "freq": freq}
        )

    # 2) REPETICIÓN
    tipo_frec = freq["tipo"]
    valor_frec = freq["valor"]

    if tipo_frec == "diaria":
        # La primera repetición es 24h después de 'fecha_inicio'
        context.job_queue.run_repeating(
            enviar_recordatorio_repeticion,
            interval=24 * 3600,
            first=fecha_inicio + timedelta(days=1),
            chat_id=chat_id,
            data={"titulo": titulo, "descripcion": descripcion}
        )
    elif tipo_frec == "semanal":
        context.job_queue.run_repeating(
            enviar_recordatorio_repeticion,
            interval=7 * 24 * 3600,
            first=fecha_inicio + timedelta(days=7),
            chat_id=chat_id,
            data={"titulo": titulo, "descripcion": descripcion}
        )
    elif tipo_frec == "cada_x_dias":
        if valor_frec:
            context.job_queue.run_repeating(
                enviar_recordatorio_repeticion,
                interval=valor_frec * 24 * 3600,
                first=fecha_inicio + timedelta(days=valor_frec),
                chat_id=chat_id,
                data={"titulo": titulo, "descripcion": descripcion}
            )
    elif tipo_frec == "cada_x_horas":
        if valor_frec:
            context.job_queue.run_repeating(
                enviar_recordatorio_repeticion,
                interval=valor_frec * 3600,
                first=fecha_inicio + timedelta(hours=valor_frec),
                chat_id=chat_id,
                data={"titulo": titulo, "descripcion": descripcion}
            )

    # 3) FIN
    if fecha_fin and fecha_fin > now_utc:
        context.job_queue.run_once(
            enviar_recordatorio_fin,
            when=fecha_fin,
            chat_id=chat_id,
            data={"titulo": titulo}
        )


def si_naive_pasar_utc(fecha, zona_str):
    """
    Si 'fecha' es naive (sin tzinfo), la interpretamos en la zona local dada por 'zona_str'
    (por ej. "UTC+1") y convertimos a UTC. Si ya es offset-aware, se devuelve tal cual.
    Si fecha es None, retorna None.
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
    fecha_utc = fecha_local.astimezone(timezone.utc)
    return fecha_utc

'''
------------------------------------------------------------------------------
 Reprogramar todos los recordatorios al iniciar el bot
------------------------------------------------------------------------------ '''

async def reprogramar_todos_los_recordatorios(context):
    """
    Se llama al arrancar el bot para reprogramar cada recordatorio
    existente en la BD.
    """
    lista = obtener_todos_los_recordatorios()  # Función en database.py, sin chat_id
    now_utc = ahora_utc()

    for r in lista:
        # si fecha_inicio y fecha_fin vienen naive y existe su zona_horaria, ajustar a UTC
        fecha_inicio = r.get("fecha_hora_inicio")
        fecha_fin = r.get("fecha_hora_fin")
        zona_str = r.get("zona_horaria", "UTC+0")

        if fecha_inicio:
            # offset-aware
            r["fecha_hora_inicio"] =  si_naive_pasar_utc(fecha_inicio, zona_str)

        if fecha_fin:
            r["fecha_hora_fin"] =  si_naive_pasar_utc(fecha_fin, zona_str)

        programar_recordatorio(context, r)
