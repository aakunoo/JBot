from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (CommandHandler,ConversationHandler,CallbackQueryHandler,ContextTypes)
from src.clima.gestion_clima import obtener_clima_actual_imagen

# Estados para la conversación
ESTADO_MENU_PRINCIPAL = 0
ESTADO_COMUNIDAD = 1
ESTADO_PROVINCIA = 2

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

async def comando_clima(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Función de entrada para el comando /clima.
    Si se proporcionan argumentos (por ejemplo, "/clima Salamanca"), se muestra directamente el clima actual.
    Si no, se muestra el menú principal con 3 opciones.
    """
    if context.args:
        provincia = " ".join(context.args)
        texto, _ = obtener_clima_actual_imagen(provincia)
        await update.message.reply_text(texto)
        return ConversationHandler.END
    else:
        # Menú principal con tres opciones.
        botones = [
            [InlineKeyboardButton("Clima actual", callback_data="opcion_actual")],
            [InlineKeyboardButton("Recordatorio diario", callback_data="opcion_diario")],
            [InlineKeyboardButton("Gestionar recordatorios", callback_data="opcion_gestionar")]
        ]
        teclado = InlineKeyboardMarkup(botones)
        await update.message.reply_text("Elige una opción:", reply_markup=teclado)
        return ESTADO_MENU_PRINCIPAL

async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Maneja la selección del menú principal.
    Solo la opción "Clima actual" está operativa; las otras muestran “En desarrollo”.
    """
    query = update.callback_query
    await query.answer()
    opcion = query.data
    if opcion == "opcion_actual":
        # 3 columnas
        comunidades_ordenadas = sorted(COMUNIDADES.keys())
        botones = []
        fila = []
        for i, comunidad in enumerate(comunidades_ordenadas):
            emoji = COMUNIDADES[comunidad]["flag"]
            texto_boton = f"{emoji} {comunidad}"
            fila.append(InlineKeyboardButton(texto_boton, callback_data=f"comunidad_{comunidad}"))
            if (i + 1) % 3 == 0:
                botones.append(fila)
                fila = []
        if fila:
            botones.append(fila)
        teclado = InlineKeyboardMarkup(botones)
        await query.edit_message_text("Selecciona una Comunidad Autónoma:", reply_markup=teclado)
        return ESTADO_COMUNIDAD
    else:
        await query.edit_message_text("Esta opción está en desarrollo.")
        return ConversationHandler.END

async def seleccionar_comunidad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Tras seleccionar una Comunidad, se muestra un menú con las provincias correspondientes.
    """
    query = update.callback_query
    await query.answer()
    comunidad = query.data.split("_", 1)[1]
    provincias = COMUNIDADES.get(comunidad, {}).get("provincias", [])
    if not provincias:
        await query.edit_message_text("No se encontraron provincias para esa comunidad.")
        return ConversationHandler.END
    botones = []
    fila = []
    for i, provincia in enumerate(provincias):
        fila.append(InlineKeyboardButton(provincia, callback_data=f"provincia_{provincia}"))
        if (i + 1) % 2 == 0:
            botones.append(fila)
            fila = []
    if fila:
        botones.append(fila)
    teclado = InlineKeyboardMarkup(botones)
    await query.edit_message_text(f"Selecciona una provincia de {comunidad}:", reply_markup=teclado)
    return ESTADO_PROVINCIA

async def mostrar_clima(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Muestra el clima actual de la provincia seleccionada.
    """
    query = update.callback_query
    await query.answer()
    provincia = query.data.split("_", 1)[1]
    texto, _ = obtener_clima_actual_imagen(provincia)
    await query.edit_message_text(texto)
    return ConversationHandler.END

conv_handler_clima_actual = ConversationHandler(
    entry_points=[CommandHandler("clima", comando_clima)],
    states={
        ESTADO_MENU_PRINCIPAL: [CallbackQueryHandler(menu_principal, pattern="^(opcion_actual|opcion_diario|opcion_gestionar)$")],
        ESTADO_COMUNIDAD: [CallbackQueryHandler(seleccionar_comunidad, pattern="^comunidad_")],
        ESTADO_PROVINCIA: [CallbackQueryHandler(mostrar_clima, pattern="^provincia_")]
    },
    fallbacks=[],
    per_user=True,
    per_chat=True
)
