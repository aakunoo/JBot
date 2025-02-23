from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    ConversationHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from datetime import datetime
from src.clima.gestion_clima import obtener_clima_actual, programar_recordatorio_diario_clima
from src.database import get_user, crear_suscripcion_clima
import logging

# Estados para Clima actual
STATE_MENU_PRINCIPAL = 0
STATE_ACTUAL_COMUNIDAD = 1
STATE_ACTUAL_PROVINCIA = 2

# Estados para Recordatorio diario
STATE_DIARIO_COMUNIDAD = 10
STATE_DIARIO_PROVINCIA = 11
STATE_DIARIO_HORA = 12
STATE_DIARIO_ZONA = 13

# Diccionario de Comunidades Autónomas
COMUNIDADES = {
    "Andalucía": {"flag": "☀️", "provincias": ["Almería", "Cádiz", "Córdoba", "Granada", "Huelva", "Jaén", "Málaga", "Sevilla"]},
    "Aragón": {"flag": "🌄", "provincias": ["Huesca", "Teruel", "Zaragoza"]},
    "Asturias": {"flag": "🌊", "provincias": ["Asturias"]},
    "Canarias": {"flag": "🏝️", "provincias": ["Las Palmas", "Santa Cruz de Tenerife"]},
    "Cantabria": {"flag": "🌊", "provincias": ["Cantabria"]},
    "Castilla y León": {"flag": "🏰", "provincias": ["Ávila", "Burgos", "León", "Palencia", "Salamanca", "Segovia", "Soria", "Valladolid", "Zamora"]},
    "Castilla-La Mancha": {"flag": "🌻", "provincias": ["Albacete", "Ciudad Real", "Cuenca", "Guadalajara", "Toledo"]},
    "Cataluña": {"flag": "🏙️", "provincias": ["Barcelona", "Girona", "Lleida", "Tarragona"]},
    "Comunidad Valenciana": {"flag": "🍊", "provincias": ["Alicante", "Castellón", "Valencia"]},
    "Extremadura": {"flag": "🐂", "provincias": ["Badajoz", "Cáceres"]},
    "Galicia": {"flag": "🌊", "provincias": ["La Coruña", "Lugo", "Ourense", "Pontevedra"]},
    "Madrid": {"flag": "🏙️", "provincias": ["Madrid"]},
    "Murcia": {"flag": "🌵", "provincias": ["Murcia"]},
    "Navarra": {"flag": "🛡️", "provincias": ["Navarra"]},
    "País Vasco": {"flag": "⚓", "provincias": ["Álava", "Guipúzcoa", "Vizcaya"]},
    "La Rioja": {"flag": "🍷", "provincias": ["La Rioja"]},
    "Baleares": {"flag": "🏝️", "provincias": ["Baleares"]},
    "Ceuta": {"flag": "🏰", "provincias": ["Ceuta"]},
    "Melilla": {"flag": "🏰", "provincias": ["Melilla"]}
}

# Función de entrada para /clima.
async def comando_clima(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        provincia = " ".join(context.args)
        texto = obtener_clima_actual(provincia)
        await update.message.reply_text(texto)
        return ConversationHandler.END
    else:
        botones = [
            [InlineKeyboardButton("Clima actual", callback_data="opcion_actual")],
            [InlineKeyboardButton("Recordatorio diario", callback_data="opcion_diario")],
            [InlineKeyboardButton("Gestionar recordatorios", callback_data="opcion_gestionar")]
        ]
        teclado = InlineKeyboardMarkup(botones)
        await update.message.reply_text("Elige una opción:", reply_markup=teclado)
        return STATE_MENU_PRINCIPAL

# Menú principal: según la opción seleccionada.
async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    opcion = query.data
    if opcion == "opcion_actual":
        return await mostrar_menu_comunidades(query, STATE_ACTUAL_COMUNIDAD, prefix="comunidad_")
    elif opcion == "opcion_diario":
        return await mostrar_menu_comunidades(query, STATE_DIARIO_COMUNIDAD, prefix="diario_comunidad_")
    else:
        await query.edit_message_text("Esta opción está en desarrollo.")
        return ConversationHandler.END

# Muestra el menú de Comunidades en 3 columnas.
async def mostrar_menu_comunidades(query, next_state, prefix):
    comunidades_ordenadas = sorted(COMUNIDADES.keys())
    botones = []
    fila = []
    for i, comunidad in enumerate(comunidades_ordenadas):
        emoji = COMUNIDADES[comunidad]["flag"]
        texto_boton = f"{emoji} {comunidad}"
        fila.append(InlineKeyboardButton(texto_boton, callback_data=f"{prefix}{comunidad}"))
        if (i + 1) % 3 == 0:
            botones.append(fila)
            fila = []
    if fila:
        botones.append(fila)
    teclado = InlineKeyboardMarkup(botones)
    await query.edit_message_text("Selecciona una Comunidad Autónoma:", reply_markup=teclado)
    return next_state

# Tras seleccionar la comunidad, se muestra el menú de provincias.
async def seleccionar_comunidad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("diario_comunidad_"):
        comunidad = data[len("diario_comunidad_"):]
        prefix = "diario_provincia_"
    elif data.startswith("comunidad_"):
        comunidad = data[len("comunidad_"):]
        prefix = "provincia_"
    else:
        comunidad = data
        prefix = "provincia_"
    provincias = COMUNIDADES.get(comunidad, {}).get("provincias", [])
    if not provincias:
        await query.edit_message_text("No se encontraron provincias para esa comunidad.")
        return ConversationHandler.END
    botones = []
    fila = []
    for i, prov in enumerate(provincias):
        fila.append(InlineKeyboardButton(prov, callback_data=f"{prefix}{prov}"))
        if (i + 1) % 2 == 0:
            botones.append(fila)
            fila = []
    if fila:
        botones.append(fila)
    teclado = InlineKeyboardMarkup(botones)
    msg = "Selecciona una provincia:" if prefix == "provincia_" else "Selecciona la provincia para el recordatorio diario:"
    await query.edit_message_text(msg, reply_markup=teclado)
    return STATE_ACTUAL_PROVINCIA if prefix == "provincia_" else STATE_DIARIO_PROVINCIA

# Flujo Clima Actual: muestra el clima actual.
async def mostrar_clima_actual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    provincia = query.data[len("provincia_"):]
    texto = obtener_clima_actual(provincia)
    await query.edit_message_text(texto)
    return ConversationHandler.END

# Flujo Recordatorio diario: tras seleccionar la provincia.
async def seleccionar_provincia_diario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    provincia = query.data[len("diario_provincia_"):]
    context.user_data["provincia_diario"] = provincia
    await query.edit_message_text("Introduce la hora a la que deseas recibir el recordatorio (HH:MM, 24h):")
    return STATE_DIARIO_HORA

# Recibe la hora para el recordatorio diario.
async def recibir_hora_diario(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

# Genera el teclado de zonas horarias en 3 columnas.
def generar_teclado_zonas():
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

# Tras seleccionar la zona horaria, almacena el recordatorio y programa el job.
async def seleccionar_zona_diario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    zona = query.data  # Ejemplo: "UTC+1"
    context.user_data["zona_diario"] = zona
    chat_id = query.message.chat_id
    provincia = context.user_data.get("provincia_diario")
    hora = context.user_data.get("hora_diario")
    usuario = get_user(chat_id)
    if usuario and usuario.get("apodo"):
        nombre = usuario["apodo"]
    else:
        nombre = query.from_user.username
    # Se almacena el recordatorio en la BBDD (colección de clima)
    hora_obj = {"hora": hora.hour, "minuto": hora.minute, "zona": zona}
    crear_suscripcion_clima(chat_id, nombre, provincia, hora_obj)
    # Se programa el job; se incluye "nombre" en job.data para personalizar el saludo.
    programar_recordatorio_diario_clima(context, chat_id, provincia, hora, zona, nombre)
    await query.edit_message_text(f"Se ha creado un recordatorio diario para el clima de {provincia} a las {hora.strftime('%H:%M')} {zona}.")
    return ConversationHandler.END

conv_handler_clima = ConversationHandler(
    entry_points=[CommandHandler("clima", comando_clima)],
    states={
        STATE_MENU_PRINCIPAL: [CallbackQueryHandler(menu_principal, pattern="^(opcion_actual|opcion_diario|opcion_gestionar)$")],
        STATE_ACTUAL_COMUNIDAD: [CallbackQueryHandler(seleccionar_comunidad, pattern="^comunidad_")],
        STATE_ACTUAL_PROVINCIA: [CallbackQueryHandler(mostrar_clima_actual, pattern="^provincia_")],
        STATE_DIARIO_COMUNIDAD: [CallbackQueryHandler(seleccionar_comunidad, pattern="^diario_comunidad_")],
        STATE_DIARIO_PROVINCIA: [CallbackQueryHandler(seleccionar_provincia_diario, pattern="^diario_provincia_")],
        STATE_DIARIO_HORA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_hora_diario)],
        STATE_DIARIO_ZONA: [CallbackQueryHandler(seleccionar_zona_diario)]
    },
    fallbacks=[CommandHandler("cancel", lambda update, context: update.message.reply_text("Operación cancelada."))],
    per_user=True,
    per_chat=True
)
