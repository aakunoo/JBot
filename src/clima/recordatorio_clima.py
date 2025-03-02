import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, MessageHandler, filters, CallbackQueryHandler
from datetime import datetime
from src.database import get_user
from src.clima.gestion_clima import programar_recordatorio_diario_clima
from src.database import crear_suscripcion_clima

# Estados que reutilizamos del ConversationHandler principal
STATE_DIARIO_PROVINCIA = 11
STATE_DIARIO_HORA = 12
STATE_DIARIO_ZONA = 13

async def seleccionar_provincia_diario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Tras elegir la comunidad en modo "Recordatorio diario",
    el usuario selecciona la provincia (callback_data = "diario_provincia_XXX").
    Luego se pide la hora.
    """
    query = update.callback_query
    await query.answer()
    provincia = query.data[len("diario_provincia_"):]
    context.user_data["provincia_diario"] = provincia
    await query.edit_message_text("Introduce la hora a la que deseas recibir el recordatorio (HH:MM, 24h):")
    return STATE_DIARIO_HORA

async def recibir_hora_diario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Recibe la hora (HH:MM). Valida el formato.
    Luego muestra el menú de zonas horarias.
    """
    texto = update.message.text.strip()
    try:
        hora = datetime.strptime(texto, "%H:%M").time()
    except ValueError:
        await update.message.reply_text("Formato incorrecto. Usa HH:MM (24h).")
        return STATE_DIARIO_HORA

    context.user_data["hora_diario"] = hora

    # Generamos el teclado de zonas horarias (3 columnas)
    teclado = generar_teclado_zonas()
    await update.message.reply_text("Selecciona tu zona horaria:", reply_markup=teclado)
    return STATE_DIARIO_ZONA

def generar_teclado_zonas():
    """
    Genera un teclado de 3 columnas con las zonas horarias desde UTC-7 hasta UTC+11.
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
    for i, zona in enumerate(zonas):
        utc_str = f"UTC{zona['offset']}"
        texto_boton = f"{zona['bandera']} ({utc_str})"
        fila.append(InlineKeyboardButton(texto_boton, callback_data=utc_str))
        if (i + 1) % 3 == 0:
            botones.append(fila)
            fila = []
    if fila:
        botones.append(fila)
    return InlineKeyboardMarkup(botones)

async def seleccionar_zona_diario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Tras seleccionar la zona horaria, creamos la suscripción en la BBDD
    y programamos el Job diario.
    """
    query = update.callback_query
    await query.answer()
    zona = query.data  # "UTC+1", por ejemplo
    chat_id = query.message.chat_id
    provincia = context.user_data.get("provincia_diario")
    hora = context.user_data.get("hora_diario")

    # Obtener el nombre (apodo si existe, si no username).
    from src.database import get_user
    usuario = get_user(chat_id)
    if usuario and usuario.get("apodo"):
        nombre = usuario["apodo"]
    else:
        nombre = query.from_user.username

    # Almacenamos en BBDD
    hora_obj = {"hora": hora.hour, "minuto": hora.minute, "zona": zona}
    crear_suscripcion_clima(chat_id, nombre, provincia, hora_obj)

    # Programar el envío diario
    programar_recordatorio_diario_clima(context, chat_id, provincia, hora, zona, nombre)

    await query.edit_message_text(
        f"Se ha creado un recordatorio diario para el clima de {provincia} a las {hora.strftime('%H:%M')} {zona}."
    )
    return ConversationHandler.END
