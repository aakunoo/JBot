import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime
from src.database.models import (
    crear_suscripcion_clima,
    obtener_recordatorios_clima,
    eliminar_recordatorio_clima
)
from src.clima.gestion_clima import programar_recordatorio_diario_clima
from src.utils.logger import setup_logger

logger = logging.getLogger(__name__)

# Estados reutilizados en conversation
STATE_DIARIO_PROVINCIA = 11
STATE_DIARIO_HORA = 12
STATE_DIARIO_ZONA = 13


async def seleccionar_provincia_diario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Ya sabemos la comunidad. El callback_data = "diario_provincia_X".
    Preguntamos la hora.
    """
    query = update.callback_query
    await query.answer()
    provincia = query.data[len("diario_provincia_"):]
    context.user_data["provincia_diario"] = provincia
    await query.edit_message_text(
        "Introduce la hora a la que deseas recibir el recordatorio (HH:MM, 24h):"
    )
    return STATE_DIARIO_HORA


async def recibir_hora_diario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Recibe la hora en texto, validamos. Luego mostramos las zonas horarias.
    """
    texto = update.message.text.strip()
    try:
        hora = datetime.strptime(texto, "%H:%M").time()
    except ValueError:
        await update.message.reply_text("Formato incorrecto. Usa HH:MM (24h).")
        return STATE_DIARIO_HORA

    context.user_data["hora_diario"] = hora
    teclado = generar_teclado_zonas()
    await update.message.reply_text("Selecciona tu zona horaria:", reply_markup=teclado)
    return STATE_DIARIO_ZONA


def generar_teclado_zonas():
    """
    Mismo listado de zonas, 3 columnas.
    """
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    zonas = [
        {"offset": "-7", "pais": "México", "bandera": "🇲🇽"},
        {"offset": "-6", "pais": "El Salvador", "bandera": "🇸🇻"},
        {"offset": "-5", "pais": "Colombia", "bandera": "🇨🇴"},
        {"offset": "-4", "pais": "Bermudas", "bandera": "🇧🇲"},
        {"offset": "-3", "pais": "Argentina", "bandera": "🇦🇷"},
        {"offset": "-2", "pais": "Groenlandia", "bandera": "🇬🇱"},
        {"offset": "-1", "pais": "Cabo Verde", "bandera": "🇨🇻"},
        {"offset": "+0", "pais": "Irlanda", "bandera": "🇮🇪"},
        {"offset": "+1", "pais": "España", "bandera": "🇪🇸"},
        {"offset": "+2", "pais": "Egipto", "bandera": "🇪🇬"},
        {"offset": "+3", "pais": "Arabia Saudí", "bandera": "🇸🇦"},
        {"offset": "+4", "pais": "Abu Dabi", "bandera": "🇦🇪"},
        {"offset": "+5", "pais": "Kazajistán", "bandera": "🇰🇿"},
        {"offset": "+6", "pais": "Uzbekistán", "bandera": "🇺🇿"},
        {"offset": "+7", "pais": "Indonesia", "bandera": "🇮🇩"},
        {"offset": "+8", "pais": "Hong Kong", "bandera": "🇭🇰"},
        {"offset": "+9", "pais": "Corea del Sur", "bandera": "🇰🇷"},
        {"offset": "+10", "pais": "Papúa Nueva Guinea", "bandera": "🇵🇬"},
        {"offset": "+11", "pais": "Australia", "bandera": "🇦🇺"}
    ]
    botones = []
    fila = []
    for i, z in enumerate(zonas):
        utc_str = f"UTC{z['offset']}"
        texto_boton = f"{z['bandera']} ({utc_str})"
        fila.append(InlineKeyboardButton(texto_boton, callback_data=utc_str))
        if (i + 1) % 3 == 0:
            botones.append(fila)
            fila = []
    if fila:
        botones.append(fila)
    return InlineKeyboardMarkup(botones)


async def seleccionar_zona_diario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Se crea la suscripción (crear_suscripcion_clima) y se programa el job (programar_recordatorio_diario_clima).
    """
    query = update.callback_query
    await query.answer()
    zona = query.data
    chat_id = query.message.chat_id

    provincia = context.user_data.get("provincia_diario")
    hora = context.user_data.get("hora_diario")

    from src.database.models import get_user
    usuario = get_user(chat_id)
    if usuario and usuario.get("apodo"):
        nombre = usuario["apodo"]
    else:
        nombre = query.from_user.username

    hora_obj = {"hora": hora.hour, "minuto": hora.minute, "zona": zona}
    nuevo_id = crear_suscripcion_clima(
        chat_id, nombre, provincia, hora_obj)  # <-- devuelve el _id
    record_id = str(nuevo_id)
    crear_suscripcion_clima(chat_id, nombre, provincia, hora_obj)

    programar_recordatorio_diario_clima(
        context, chat_id, provincia, hora, zona, nombre, record_id)

    await query.edit_message_text(
        f"Se ha creado un recordatorio diario para el clima de {provincia} a las {hora.strftime('%H:%M')} {zona}."
    )
    return ConversationHandler.END
