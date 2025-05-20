from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    MessageHandler,
    CallbackQueryHandler,
    CommandHandler,
    filters,
    ConversationHandler
)
from datetime import datetime
from src.database.models import get_user, crear_recordatorio
from src.reminders.mensaje_recordatorios import programar_recordatorio
from src.utils.logger import setup_logger
import logging

logger = logging.getLogger(__name__)

# Estados de la conversación
MENU_RECORDATORIOS = 0
PEDIR_TITULO = 1
CONFIRMAR_DESCRIPCION = 2
PEDIR_DESCRIPCION = 3
PEDIR_FECHA_INICIO = 4
PEDIR_FRECUENCIA = 5
PEDIR_VALOR_CADA_X = 6
PEDIR_FECHA_FIN = 7
PEDIR_ZONA_HORARIA = 8

'''
-----------------------------------------------------------------------------------
 Menú principal de recordatorios
-----------------------------------------------------------------------------------
'''


async def menu_recordatorios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Punto de entrada si el usuario escribe /recordatorios directamente.
    Verificamos el registro.
    """
    user_id = update.effective_user.id
    if not get_user(user_id):
        await update.message.reply_text("Primero debes registrarte con /register.")
        return ConversationHandler.END

    teclado = [
        [InlineKeyboardButton("Crear un recordatorio",
                              callback_data="menu_crear")],
        [InlineKeyboardButton("Ver mis recordatorios",
                              callback_data="menu_ver")],
        [InlineKeyboardButton("Eliminar un recordatorio",
                              callback_data="menu_eliminar")]
    ]
    respuesta = InlineKeyboardMarkup(teclado)

    # Puede venir de un mensaje normal o de un callback
    if update.message:
        await update.message.reply_text("¿Qué quieres hacer?", reply_markup=respuesta)
    elif update.callback_query:
        await update.callback_query.edit_message_text("¿Qué quieres hacer?", reply_markup=respuesta)
    return MENU_RECORDATORIOS


'''
-----------------------------------------------------------------------------------
 Comando para iniciar la creación de recordatorios
-----------------------------------------------------------------------------------
'''


async def comando_recordatorios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Queda como un alias si alguien escribe /recordatorios.
    Se llama a menu_recordatorios, que ya comprueba el registro.
    """
    return await menu_recordatorios(update, context)


'''
-----------------------------------------------------------------------------------
 Callback del menu principal (Tras elegir un botón)
-----------------------------------------------------------------------------------
'''


async def recordatorios_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Verificar registro de nuevo aquí por seguridad
    user_id = query.from_user.id
    if not get_user(user_id):
        await query.edit_message_text("Primero debes registrarte con /register.")
        return ConversationHandler.END

    opcion = query.data
    if opcion == "menu_crear":
        await query.edit_message_text("Has seleccionado: Crear un recordatorio.\nDime el título:")
        return PEDIR_TITULO
    elif opcion == "menu_ver":
        await query.edit_message_text("Has seleccionado: Ver mis recordatorios.")
        from src.reminders.gestion_recordatorios import mostrar_recordatorios
        await mostrar_recordatorios(update, context)
        return ConversationHandler.END
    elif opcion == "menu_eliminar":
        await query.edit_message_text("Has seleccionado: Eliminar un recordatorio.")
        from src.reminders.gestion_recordatorios import eliminar_recordatorios
        await eliminar_recordatorios(update, context)
        return ConversationHandler.END
    else:
        await query.edit_message_text("Opción no reconocida.")
        return ConversationHandler.END


'''
-----------------------------------------------------------------------------------
 Paso 1: Recoger título por texto
-----------------------------------------------------------------------------------
'''


async def pedir_titulo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not get_user(user_id):
        await update.message.reply_text("Primero debes registrarte con /register.")
        return ConversationHandler.END

    context.user_data["nuevo_recordatorio"] = {}
    context.user_data["nuevo_recordatorio"]["titulo"] = update.message.text.strip()

    keyboard = [
        [InlineKeyboardButton("Sí", callback_data="desc_si"),
         InlineKeyboardButton("No", callback_data="desc_no")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("¿Quieres añadir una descripción al recordatorio?", reply_markup=reply_markup)
    return CONFIRMAR_DESCRIPCION


'''
-----------------------------------------------------------------------------------
 Paso 1.1: Confirmar si desea descripción
-----------------------------------------------------------------------------------
'''


async def confirmar_descripcion(update, context):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if not get_user(user_id):
        await query.edit_message_text("Primero debes registrarte con /register.")
        return ConversationHandler.END

    if query.data == "desc_si":
        await query.edit_message_text("Introduce una descripción para el recordatorio:")
        return PEDIR_DESCRIPCION
    else:  # "desc_no"
        context.user_data["nuevo_recordatorio"]["descripcion"] = "Sin descripción"
        await query.edit_message_text(
            "No has indicado una descripción.\n"
            "¿Cuándo debe iniciar el recordatorio? (Ejemplo: 2025-02-20 08:00)"
        )
        return PEDIR_FECHA_INICIO


'''
-----------------------------------------------------------------------------------
 Paso 2: Recoger descripción por texto
-----------------------------------------------------------------------------------
'''


async def pedir_descripcion(update, context):
    user_id = update.effective_user.id
    if not get_user(user_id):
        await update.message.reply_text("Primero debes registrarte con /register.")
        return ConversationHandler.END

    context.user_data["nuevo_recordatorio"]["descripcion"] = update.message.text.strip()
    await update.message.reply_text("¿Cuándo debe iniciar el recordatorio? (Ejemplo: 2025-02-20 08:00)")
    return PEDIR_FECHA_INICIO


'''
-----------------------------------------------------------------------------------
 Paso 3: Recoger fecha/hora de inicio por texto
-----------------------------------------------------------------------------------
'''


async def pedir_fecha_inicio(update, context):
    user_id = update.effective_user.id
    if not get_user(user_id):
        await update.message.reply_text("Primero debes registrarte con /register.")
        return ConversationHandler.END

    texto = update.message.text.strip()
    try:
        fecha_obj = datetime.strptime(texto, "%Y-%m-%d %H:%M")
        context.user_data["nuevo_recordatorio"]["fecha_inicio"] = fecha_obj
    except ValueError:
        await update.message.reply_text(
            "Formato de fecha/hora inválido. Usa YYYY-MM-DD HH:MM. Inténtalo de nuevo."
        )
        return PEDIR_FECHA_INICIO

    # Menú para la frecuencia
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    teclado_frecuencia = [
        [InlineKeyboardButton("Ninguna", callback_data="ninguna")],
        [InlineKeyboardButton("Diaria", callback_data="diaria")],
        [InlineKeyboardButton("Semanal", callback_data="semanal")],
        [InlineKeyboardButton("Cada X días", callback_data="cada_x_dias")],
        [InlineKeyboardButton("Cada X horas", callback_data="cada_x_horas")]
    ]
    respuesta = InlineKeyboardMarkup(teclado_frecuencia)
    await update.message.reply_text(
        "¿Con qué frecuencia se repetirá el recordatorio?\n(Elige una opción)",
        reply_markup=respuesta
    )
    return PEDIR_FRECUENCIA


'''
-----------------------------------------------------------------------------------
 Paso 4: Seleccionar frecuencia (InlineKeyboard)
-----------------------------------------------------------------------------------
'''


async def seleccionar_frecuencia(update, context):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if not get_user(user_id):
        await query.edit_message_text("Primero debes registrarte con /register.")
        return ConversationHandler.END

    datos_freq = query.data
    frecuencia = {"tipo": "ninguna", "valor": None}

    if datos_freq in ["diaria", "semanal", "ninguna"]:
        frecuencia["tipo"] = datos_freq
        context.user_data["nuevo_recordatorio"]["frecuencia"] = frecuencia
        await query.edit_message_text(
            f"Has seleccionado: {datos_freq}.\n"
            "¿Fecha/hora de finalización? (YYYY-MM-DD HH:MM)\nSi no hay fin, escribe 'ninguna'."
        )
        return PEDIR_FECHA_FIN

    elif datos_freq == "cada_x_dias":
        frecuencia["tipo"] = "cada_x_dias"
        context.user_data["nuevo_recordatorio"]["frecuencia"] = frecuencia
        await query.edit_message_text(
            "Has seleccionado: 'Cada X días'.\n¿Cada cuántos días deseas que se repita? (ej. 3)"
        )
        return PEDIR_VALOR_CADA_X

    elif datos_freq == "cada_x_horas":
        frecuencia["tipo"] = "cada_x_horas"
        context.user_data["nuevo_recordatorio"]["frecuencia"] = frecuencia
        await query.edit_message_text(
            "Has seleccionado: 'Cada X horas'.\n¿Cada cuántas horas deseas que se repita? (ej. 6)"
        )
        return PEDIR_VALOR_CADA_X


'''
-----------------------------------------------------------------------------------
 Paso 4.1: si elegimos cada_x_dias o cada_x_horas, pedimos el valor por texto
-----------------------------------------------------------------------------------
'''


async def pedir_valor_cada_x(update, context):
    user_id = update.effective_user.id
    if not get_user(user_id):
        await update.message.reply_text("Primero debes registrarte con /register.")
        return ConversationHandler.END

    texto = update.message.text.strip()
    if not texto.isdigit():
        await update.message.reply_text("Por favor, escribe un número entero.")
        return PEDIR_VALOR_CADA_X

    x = int(texto)
    frecuencia = context.user_data["nuevo_recordatorio"]["frecuencia"]
    frecuencia["valor"] = x
    context.user_data["nuevo_recordatorio"]["frecuencia"] = frecuencia

    await update.message.reply_text(
        "¿Fecha/hora de finalización? (YYYY-MM-DD HH:MM)\n"
        "Si no hay fin, escribe 'ninguna'."
    )
    return PEDIR_FECHA_FIN


'''
-----------------------------------------------------------------------------------
 Paso 5: Recoger fecha/hora fin por texto
-----------------------------------------------------------------------------------
'''


async def pedir_fecha_fin(update, context):
    user_id = update.effective_user.id
    if not get_user(user_id):
        await update.message.reply_text("Primero debes registrarte con /register.")
        return ConversationHandler.END

    texto = update.message.text.strip().lower()
    fecha_fin = None
    if texto != "ninguna":
        try:
            fecha_obj = datetime.strptime(texto, "%Y-%m-%d %H:%M")
            fecha_fin = fecha_obj
        except ValueError:
            await update.message.reply_text("Formato inválido. Usaré 'ninguna' como fecha fin.")
            fecha_fin = None

    context.user_data["nuevo_recordatorio"]["fecha_fin"] = fecha_fin

    # Teclado con zonas horarias
    teclado_zonas = generar_teclado_zonas()
    from telegram import InlineKeyboardMarkup
    reply_markup = InlineKeyboardMarkup(teclado_zonas)
    await update.message.reply_text(
        "Selecciona tu zona horaria pulsando la bandera correspondiente:",
        reply_markup=reply_markup
    )
    return PEDIR_ZONA_HORARIA


def generar_teclado_zonas():
    from telegram import InlineKeyboardButton
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
        {"offset": "+5", "pais": "Kazajistan", "bandera": "🇰🇿"},
        {"offset": "+6", "pais": "Uzbekistan", "bandera": "🇺🇿"},
        {"offset": "+7", "pais": "Indonesia", "bandera": "🇮🇩"},
        {"offset": "+8", "pais": "Hong Kong", "bandera": "🇭🇰"},
        {"offset": "+9", "pais": "Corea del Sur", "bandera": "🇰🇷"},
        {"offset": "+10", "pais": "Papúa Nueva Guinea", "bandera": "🇵🇬"},
        {"offset": "+11", "pais": "Australia", "bandera": "🇦🇺"},
    ]

    from telegram import InlineKeyboardMarkup
    botones = []
    for zona in zonas:
        utc_str = f"UTC{zona['offset']}"
        texto_boton = f"{zona['bandera']}  ({utc_str})"
        botones.append(InlineKeyboardButton(
            texto_boton, callback_data=utc_str))

    filas = []
    fila_temp = []
    for i, boton in enumerate(botones, start=1):
        fila_temp.append(boton)
        if i % 3 == 0:
            filas.append(fila_temp)
            fila_temp = []
    if fila_temp:
        filas.append(fila_temp)

    return filas


async def seleccionar_zona_horaria(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Callback que se ejecuta cuando el usuario selecciona una zona horaria.
    Crea el recordatorio en la BD y programa los jobs.
    """
    query = update.callback_query
    await query.answer()
    zona = query.data
    user_id = query.from_user.id

    # Recuperamos los datos guardados
    datos = context.user_data["nuevo_recordatorio"]
    datos["zona_horaria"] = zona

    # Creamos el recordatorio en la BD
    id_insertado = crear_recordatorio(
        user_id=user_id,
        titulo=datos["titulo"],
        descripcion=datos["descripcion"],
        fecha_hora_inicio=datos["fecha_inicio"],
        frecuencia=datos["frecuencia"],
        fecha_hora_fin=datos["fecha_fin"],
        zona_horaria=datos["zona_horaria"]
    )

    # Preparamos el diccionario para programar_recordatorio
    r = {
        "user_id": user_id,
        "titulo": datos["titulo"],
        "descripcion": datos["descripcion"],
        "fecha_hora_inicio": datos["fecha_inicio"],
        "frecuencia": datos["frecuencia"],
        "fecha_hora_fin": datos["fecha_fin"],
        "zona_horaria": datos["zona_horaria"]
    }

    # Programamos los jobs
    programar_recordatorio(context, r, record_id=str(id_insertado))

    await query.edit_message_text(
        f"¡Recordatorio creado!\n\n"
        f"Título: {datos['titulo']}\n"
        f"Descripción: {datos['descripcion']}\n"
        f"Fecha de inicio: {datos['fecha_inicio'].strftime('%Y-%m-%d %H:%M')}\n"
        f"Frecuencia: {datos['frecuencia']['tipo']}\n"
        f"Zona horaria: {zona}"
    )
    return ConversationHandler.END


'''
-----------------------------------------------------------------------------------
 Cancelar (A falta de completarse.)
-----------------------------------------------------------------------------------
'''


async def cancelar_recordatorio(update, context):
    await update.message.reply_text("Has cancelado el proceso.")
    return ConversationHandler.END


'''
-----------------------------------------------------------------------------------
 Definición del ConversationHandler
-----------------------------------------------------------------------------------
'''

conv_handler_recordatorios = ConversationHandler(
    entry_points=[CommandHandler("recordatorios", comando_recordatorios)],
    states={
        MENU_RECORDATORIOS: [CallbackQueryHandler(recordatorios_menu_callback, pattern="^menu_")],
        PEDIR_TITULO: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_titulo)],
        CONFIRMAR_DESCRIPCION: [CallbackQueryHandler(confirmar_descripcion, pattern="^desc_")],
        PEDIR_DESCRIPCION: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_descripcion)],
        PEDIR_FECHA_INICIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_fecha_inicio)],
        PEDIR_FRECUENCIA: [CallbackQueryHandler(seleccionar_frecuencia)],
        PEDIR_VALOR_CADA_X: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_valor_cada_x)],
        PEDIR_FECHA_FIN: [MessageHandler(filters.TEXT & ~filters.COMMAND, pedir_fecha_fin)],
        PEDIR_ZONA_HORARIA: [CallbackQueryHandler(seleccionar_zona_horaria)]
    },
    fallbacks=[CommandHandler("cancel", cancelar_recordatorio)],
    per_user=True,
    per_chat=False
)
