from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from src.database import get_user, obtener_recordatorios, eliminar_recordatorio_por_id

''' 
---------------------------------------------------------------------------
 Muestra todos los recordatorios del usuario con el chat_id que corresponde
--------------------------------------------------------------------------- '''
async def mostrar_recordatorios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    mensaje = update.message if update.message else update.callback_query.message
    if not get_user(chat_id):
        await mensaje.reply_text("Primero debes registrarte con /register.")
        return
    lista = obtener_recordatorios(chat_id)
    if not lista:
        await mensaje.reply_text("No tienes recordatorios.")
        return

    texto = "Tus recordatorios:\n\n"
    for indice, recordatorio in enumerate(lista, start=1):
        titulo = recordatorio.get("titulo", "Sin título")
        descripcion = recordatorio.get("descripcion", "Sin descripción")
        fecha_inicio = recordatorio.get("fecha_hora_inicio")
        if fecha_inicio and isinstance(fecha_inicio, datetime):
            fecha_str = fecha_inicio.strftime("%Y-%m-%d %H:%M")
        else:
            fecha_str = "Sin fecha"
        texto += f"{indice}) {titulo} - {descripcion} (Inicio: {fecha_str})\n"
    await mensaje.reply_text(texto)

'''
---------------------------------------------------------------------------
 Función para iniciar la eliminación de recordatorios
--------------------------------------------------------------------------- '''

async def eliminar_recordatorios(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    mensaje = update.message if update.message else update.callback_query.message
    if not get_user(chat_id):
        await mensaje.reply_text("Primero debes registrarte con /register.")
        return
    lista = obtener_recordatorios(chat_id)
    if not lista:
        await mensaje.reply_text("No tienes recordatorios para eliminar.")
        return

    teclado = []
    for indice, recordatorio in enumerate(lista, start=1):
        titulo = recordatorio.get("titulo", "Sin título")
        callback_data = f"eliminar_{str(recordatorio['_id'])}"
        teclado.append([InlineKeyboardButton(f"{indice}) {titulo}", callback_data=callback_data)])
    reply_markup = InlineKeyboardMarkup(teclado)
    await mensaje.reply_text("Selecciona el recordatorio que deseas eliminar:", reply_markup=reply_markup)

'''
---------------------------------------------------------------------------
 Callback para procesar la eliminación de un recordatorio
--------------------------------------------------------------------------- '''

async def procesar_eliminar_recordatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data.startswith("eliminar_"):
        recordatorio_id = data[len("eliminar_"):]
        resultado = eliminar_recordatorio_por_id(recordatorio_id)
        if resultado.deleted_count > 0:
            await query.edit_message_text("Recordatorio eliminado.")
        else:
            await query.edit_message_text("No se pudo eliminar el recordatorio.")
    else:
        await query.edit_message_text("Opción no reconocida.")
