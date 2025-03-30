from datetime import datetime, time
from bson import ObjectId
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
    ConversationHandler,
    MessageHandler
)

from src.database.models import (
    get_user,
    obtener_recordatorios_clima,
    eliminar_recordatorio_clima,
    actualizar_recordatorio_clima,
    coleccion_clima
)
from src.clima.gestion_clima import obtener_clima_actual, programar_recordatorio_diario_clima
from src.clima.recordatorio_clima import (
    STATE_DIARIO_PROVINCIA,
    STATE_DIARIO_HORA,
    STATE_DIARIO_ZONA,
    seleccionar_provincia_diario,
    recibir_hora_diario,
    seleccionar_zona_diario
)
from src.utils.logger import setup_logger
import logging

logger = logging.getLogger(__name__)

'''
--------------------------------------------------------------------------------
 ESTADOS DE LA CONVERSACIÓN
-------------------------------------------------------------------------------- '''

# Clima actual
STATE_MENU_PRINCIPAL = 0
STATE_ACTUAL_COMUNIDAD = 1
STATE_ACTUAL_PROVINCIA = 2

# Recordatorio diario
STATE_DIARIO_COMUNIDAD = 10
# (STATE_DIARIO_PROVINCIA = 11 en recordatorio_clima.py)
# (STATE_DIARIO_HORA = 12 en recordatorio_clima.py)
# (STATE_DIARIO_ZONA = 13 en recordatorio_clima.py)

# Estados de gestión de recordatorios
STATE_GESTIONAR_MENU = 20
STATE_GESTIONAR_VER = 21
STATE_GESTIONAR_ELIMINAR = 22
STATE_GESTIONAR_EDITAR = 23
STATE_GESTIONAR_EDITAR_HORA = 24
STATE_GESTIONAR_EDITAR_ZONA = 25

''' DICCIONARIO COMUNIDADES '''

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
    '''
    Función de entrada para el comando /clima. Si el usuario escribe
    "/clima <provincia>", mostramos el clima actual de esa provincia.
    Si no, desplegamos el menú principal (Clima actual,
    Recordatorio diario, Gestionar recordatorios).
    '''
    chat_id = update.effective_chat.id
    if not get_user(chat_id):
        await update.message.reply_text("Primero debes registrarte con /register.")
        return ConversationHandler.END

    if context.args:
        provincia = " ".join(context.args)
        texto = obtener_clima_actual(provincia)
        await update.message.reply_text(texto)
        return ConversationHandler.END
    else:
        botones = [
            [InlineKeyboardButton(
                "Clima actual", callback_data="opcion_actual")],
            [InlineKeyboardButton(
                "Recordatorio diario de clima", callback_data="opcion_diario")],
            [InlineKeyboardButton(
                "Gestionar recordatorios de clima", callback_data="opcion_gestionar")]
        ]
        teclado = InlineKeyboardMarkup(botones)
        await update.message.reply_text("Elige una opción:", reply_markup=teclado)
        return STATE_MENU_PRINCIPAL


async def menu_principal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''
    Función que maneja la respuesta del menú principal (Clima actual,
    Recordatorio diario, Gestionar recordatorios). Dependiendo de la opción,
    redirecciona a otros estados.
    '''
    query = update.callback_query
    await query.answer()
    opcion = query.data

    if opcion == "opcion_actual":
        return await mostrar_menu_comunidades(query, STATE_ACTUAL_COMUNIDAD, prefix="comunidad_")

    elif opcion == "opcion_diario":
        return await mostrar_menu_comunidades(query, STATE_DIARIO_COMUNIDAD, prefix="diario_comunidad_")

    elif opcion == "opcion_gestionar":
        # Submenú con: Ver, Eliminar, Editar
        botones = [
            [InlineKeyboardButton("Ver mis recordatorios",
                                  callback_data="gestionar_ver")],
            [InlineKeyboardButton("Eliminar un recordatorio",
                                  callback_data="gestionar_eliminar")],
            [InlineKeyboardButton("Editar un recordatorio",
                                  callback_data="gestionar_editar")]
        ]
        teclado = InlineKeyboardMarkup(botones)
        await query.edit_message_text("¿Qué deseas hacer?", reply_markup=teclado)
        return STATE_GESTIONAR_MENU

    else:
        await query.edit_message_text("Esta opción está en desarrollo.")
        return ConversationHandler.END


async def mostrar_menu_comunidades(query, next_state, prefix):
    '''
    Función que muestra en un teclado las Comunidades Autónomas
    para elegir, en 3 columnas, con un prefijo distinto según
    sea "comunidad_" o "diario_comunidad_".
    '''
    comunidades_ordenadas = sorted(COMUNIDADES.keys())
    botones = []
    fila = []
    for i, comunidad in enumerate(comunidades_ordenadas):
        emoji = COMUNIDADES[comunidad]["flag"]
        texto_boton = f"{emoji} {comunidad}"
        fila.append(InlineKeyboardButton(
            texto_boton, callback_data=f"{prefix}{comunidad}"))
        if (i + 1) % 3 == 0:
            botones.append(fila)
            fila = []
    if fila:
        botones.append(fila)
    teclado = InlineKeyboardMarkup(botones)
    await query.edit_message_text("Selecciona una Comunidad Autónoma:", reply_markup=teclado)
    return next_state


async def seleccionar_comunidad(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''
    Función que maneja la selección de comunidad para Clima actual (comunidad_...)
    o para un Recordatorio diario (diario_comunidad_...). Luego pasa a
    provincia o provincia_diario según corresponda.
    '''
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("diario_comunidad_"):
        comunidad = data[len("diario_comunidad_"):]
        prefix = "diario_provincia_"
        next_state = STATE_DIARIO_PROVINCIA
    else:
        comunidad = data[len("comunidad_"):]
        prefix = "provincia_"
        next_state = STATE_ACTUAL_PROVINCIA

    provincias = COMUNIDADES.get(comunidad, {}).get("provincias", [])
    if not provincias:
        await query.edit_message_text("No se encontraron provincias para esa comunidad.")
        return ConversationHandler.END

    botones = []
    fila = []
    for i, prov in enumerate(provincias):
        fila.append(InlineKeyboardButton(
            prov, callback_data=f"{prefix}{prov}"))
        if (i + 1) % 2 == 0:
            botones.append(fila)
            fila = []
    if fila:
        botones.append(fila)

    msg = ("Selecciona una provincia:" if prefix ==
           "provincia_" else "Selecciona la provincia para el recordatorio diario:")
    teclado = InlineKeyboardMarkup(botones)
    await query.edit_message_text(msg, reply_markup=teclado)
    return next_state


async def mostrar_clima_actual(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''
    Función que finalmente muestra el clima actual de la provincia elegida,
    utilizando obtener_clima_actual, y edita el mensaje para mostrar el resultado.
    '''
    query = update.callback_query
    await query.answer()
    provincia = query.data[len("provincia_"):]
    texto = obtener_clima_actual(provincia)
    await query.edit_message_text(texto)
    return ConversationHandler.END

# --------------------------------------------------------------------------------
# GESTIONAR RECORDATORIOS (ver, eliminar, editar)
# --------------------------------------------------------------------------------


async def submenu_gestionar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''
    Submenú principal al pulsar "Gestionar recordatorios",
    donde el usuario elige si quiere ver, eliminar o editar
    sus recordatorios de clima.
    '''
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "gestionar_ver":
        # Para ver
        return await mostrar_recordatorios_clima_list(query, context)
    elif data == "gestionar_eliminar":
        return await mostrar_recordatorios_clima_eliminar(query, context)
    elif data == "gestionar_editar":
        return await mostrar_recordatorios_clima_editar(query, context)
    else:
        await query.edit_message_text("Opción no reconocida.")
        return ConversationHandler.END


async def mostrar_recordatorios_clima_list(query, context):
    '''
    Muestra en un mensaje la lista de recordatorios de clima existentes,
    sin permitir ninguna acción (sólo lectura).
    '''
    chat_id = query.message.chat_id
    lista = obtener_recordatorios_clima(chat_id)
    if not lista:
        await query.edit_message_text("No tienes recordatorios de clima.")
        return ConversationHandler.END

    texto = "Tus recordatorios de clima:\n\n"
    for rec in lista:
        prov = rec.get("provincia", "")
        hora_cfg = rec.get("hora_config", {})
        hora_str = f"{hora_cfg.get('hora', '--')}:{hora_cfg.get('minuto', '--')} {hora_cfg.get('zona', '')}"
        texto += f"- {prov} @ {hora_str}\n"
    await query.edit_message_text(texto)
    return ConversationHandler.END


async def mostrar_recordatorios_clima_eliminar(query, context):
    '''
    Muestra un listado de botones con cada recordatorio de clima,
    para que el usuario seleccione cuál desea eliminar.
    '''
    chat_id = query.message.chat_id
    lista = obtener_recordatorios_clima(chat_id)
    if not lista:
        await query.edit_message_text("No tienes recordatorios de clima.")
        return ConversationHandler.END

    botones = []
    for rec in lista:
        _id = str(rec["_id"])
        prov = rec.get("provincia", "")
        hora_cfg = rec.get("hora_config", {})
        hora_str = f"{hora_cfg.get('hora', '--')}:{hora_cfg.get('minuto', '--')} {hora_cfg.get('zona', '')}"
        texto = f"{prov} @ {hora_str}"
        botones.append([InlineKeyboardButton(
            texto, callback_data=f"clima_eliminar_{_id}")])

    teclado = InlineKeyboardMarkup(botones)
    await query.edit_message_text("Selecciona el recordatorio que deseas eliminar:", reply_markup=teclado)
    return STATE_GESTIONAR_ELIMINAR


async def eliminar_recordatorio_clima_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("clima_eliminar_"):
        rec_id = data[len("clima_eliminar_"):]
        resultado = eliminar_recordatorio_clima(rec_id)
        if resultado.deleted_count > 0:
            await query.edit_message_text("Recordatorio eliminado.")
        else:
            await query.edit_message_text("No se pudo eliminar el recordatorio.")
    else:
        await query.edit_message_text("Opción no reconocida.")
    return ConversationHandler.END


async def mostrar_recordatorios_clima_editar(query, context):
    '''
    Muestra un listado de recordatorios de clima para que el usuario
    seleccione cuál quiere editar (cambiando hora y zona).
    '''
    chat_id = query.message.chat_id
    lista = obtener_recordatorios_clima(chat_id)
    if not lista:
        await query.edit_message_text("No tienes recordatorios de clima.")
        return ConversationHandler.END

    botones = []
    for rec in lista:
        _id = str(rec["_id"])
        prov = rec.get("provincia", "")
        hora_cfg = rec.get("hora_config", {})
        hora_str = f"{hora_cfg.get('hora', '--')}:{hora_cfg.get('minuto', '--')} {hora_cfg.get('zona', '')}"
        texto = f"{prov} @ {hora_str}"
        botones.append([InlineKeyboardButton(
            texto, callback_data=f"clima_editar_{_id}")])

    teclado = InlineKeyboardMarkup(botones)
    await query.edit_message_text("Selecciona el recordatorio que deseas editar:", reply_markup=teclado)
    return STATE_GESTIONAR_EDITAR


async def editar_recordatorio_clima_seleccionado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''
    Callback que guarda en user_data el id del recordatorio a editar,
    y pide al usuario la nueva hora en formato HH:MM.
    '''
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("clima_editar_"):
        rec_id = data[len("clima_editar_"):]
        context.user_data["id_recordatorio_clima"] = rec_id
        await query.edit_message_text("Indica la nueva hora (HH:MM) para este recordatorio:")
        return STATE_GESTIONAR_EDITAR_HORA
    else:
        await query.edit_message_text("Opción no reconocida.")
        return ConversationHandler.END


async def editar_recordatorio_clima_hora(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''
    Tras recibir la nueva hora por mensaje, guardamos ese valor y
    pedimos la nueva zona horaria mediante un teclado de opciones.
    '''
    text = update.message.text.strip()
    try:
        hora = datetime.strptime(text, "%H:%M").time()
    except ValueError:
        await update.message.reply_text("Formato incorrecto, usa HH:MM (24h).")
        return STATE_GESTIONAR_EDITAR_HORA

    context.user_data["nueva_hora_clima"] = hora

    teclado = generar_teclado_zonas()
    await update.message.reply_text("Selecciona la nueva zona horaria:", reply_markup=teclado)
    return STATE_GESTIONAR_EDITAR_ZONA


def generar_teclado_zonas():
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


async def editar_recordatorio_clima_zona(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''
    Tras seleccionar la nueva zona, se realiza la actualización
    del registro en la base de datos y se finaliza la conversación.
    Tras seleccionar la nueva zona, actualizamos la BBDD y reprogramamos el job
    para que el recordatorio llegue a la nueva hora/ zona.
    '''
    query = update.callback_query
    await query.answer()
    zona = query.data
    rec_id = context.user_data.get("id_recordatorio_clima")
    hora = context.user_data.get("nueva_hora_clima")

    if not rec_id or not hora:
        await query.edit_message_text("Faltan datos para editar.")
        return ConversationHandler.END

    # 1) Actualizar en BD
    cambios = {
        "hora_config": {
            "hora": hora.hour,
            "minuto": hora.minute,
            "zona": zona
        }
    }
    actualizar_recordatorio_clima(rec_id, cambios)

    # 2) Cancelar el job anterior
    cancelar_job_clima(context, rec_id)

    # 3) Leer doc recién editado, reprogramar
    doc = coleccion_clima.find_one({"_id": ObjectId(rec_id)})
    if doc:
        chat_id = doc["chat_id"]
        provincia = doc["provincia"]
        hora_cfg = doc["hora_config"]
        nombre = doc["nombre_usuario"]

        hora_obj = time(hora.hour, hora.minute)

        # Reprogramar con record_id
        programar_recordatorio_diario_clima(
            context,
            chat_id,
            provincia,
            hora_obj,
            zona,
            nombre,
            rec_id
        )

    await query.edit_message_text("¡Recordatorio actualizado con la nueva hora!")
    return ConversationHandler.END


def cancelar_job_clima(context, record_id):
    """
    Recorre los jobs en context.job_queue y elimina
    el que coincida con el record_id en job.data.
    """
    for job in context.job_queue.jobs():
        if job.data and job.data.get("record_id") == record_id:
            job.schedule_removal()


''' CONVERSATION HANDLER '''

conv_handler_clima = ConversationHandler(
    entry_points=[CommandHandler("clima", comando_clima)],
    states={
        # Menú principal
        STATE_MENU_PRINCIPAL: [
            CallbackQueryHandler(
                menu_principal, pattern="^(opcion_actual|opcion_diario|opcion_gestionar)$")
        ],
        # Clima actual
        STATE_ACTUAL_COMUNIDAD: [CallbackQueryHandler(seleccionar_comunidad, pattern="^comunidad_")],
        STATE_ACTUAL_PROVINCIA: [CallbackQueryHandler(mostrar_clima_actual, pattern="^provincia_")],

        # Recordatorio diario
        STATE_DIARIO_COMUNIDAD: [CallbackQueryHandler(seleccionar_comunidad, pattern="^diario_comunidad_")],
        STATE_DIARIO_PROVINCIA: [CallbackQueryHandler(seleccionar_provincia_diario, pattern="^diario_provincia_")],
        STATE_DIARIO_HORA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_hora_diario)],
        STATE_DIARIO_ZONA: [CallbackQueryHandler(seleccionar_zona_diario)],

        # Gestionar recordatorios
        STATE_GESTIONAR_MENU: [
            CallbackQueryHandler(
                submenu_gestionar, pattern="^(gestionar_ver|gestionar_eliminar|gestionar_editar)$")
        ],
        STATE_GESTIONAR_ELIMINAR: [
            CallbackQueryHandler(
                eliminar_recordatorio_clima_callback, pattern="^clima_eliminar_")
        ],
        STATE_GESTIONAR_EDITAR: [
            CallbackQueryHandler(
                editar_recordatorio_clima_seleccionado, pattern="^clima_editar_")
        ],
        STATE_GESTIONAR_EDITAR_HORA: [
            MessageHandler(filters.TEXT & ~filters.COMMAND,
                           editar_recordatorio_clima_hora)
        ],
        STATE_GESTIONAR_EDITAR_ZONA: [
            CallbackQueryHandler(editar_recordatorio_clima_zona)
        ]
    },
    fallbacks=[
        CommandHandler("cancel", lambda update,
                       context: update.message.reply_text("Operación cancelada."))
    ],
    per_user=True,
    per_chat=True
)
