import subprocess
import os
import shutil
import socket
from datetime import datetime

'''
Devuelve una cadena con la salida del comando "ps aux" usando la ruta completa.
'''
def get_active_processes():
    try:
        output = subprocess.check_output(["/bin/ps", "aux"], universal_newlines=True)
        return output
    except Exception as e:
        return f"Error al obtener procesos: {str(e)}"

'''
Devuelve el tiempo de actividad del sistema usando el comando "uptime -p" con la ruta completa.
'''
def get_uptime():
    try:
        output = subprocess.check_output(["/usr/bin/uptime", "-p"], universal_newlines=True)
        return output.strip()
    except Exception as e:
        return f"Error al obtener uptime: {str(e)}"

'''
Devuelve la fecha y hora actual del sistema en formato "YYYY-MM-DD HH:MM:SS".
'''
def get_date_time():
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

'''
Devuelve el nombre del equipo (hostname) del sistema.
'''
def get_hostname():
    try:
        return socket.gethostname()
    except Exception as e:
        return f"Error al obtener el nombre del equipo: {str(e)}"

'''
Devuelve una cadena con el uso del disco en la ruta indicada (por defecto, "/"),
calculado en GB, mostrando el total, usado y libre.
'''
def get_disk_usage(path="/"):
    try:
        usage = shutil.disk_usage(path)
        total_gb = usage.total / (1024**3)
        used_gb = usage.used / (1024**3)
        free_gb = usage.free / (1024**3)
        return f"Total: {total_gb:.2f} GB, Usado: {used_gb:.2f} GB, Libre: {free_gb:.2f} GB"
    except Exception as e:
        return f"Error al obtener uso de disco: {str(e)}"

'''
Reúne la información del sistema (procesos, uptime, fecha y hora, hostname y uso de disco)
en un formato de "tabla" para mostrarlo de forma estética.
Se muestran solo las primeras 15 líneas de los procesos activos para evitar saturar el mensaje.
'''
def get_system_info():
    procesos = get_active_processes().splitlines()
    procesos_str = "\n".join(procesos[:15])
    uptime = get_uptime()
    fecha_hora = get_date_time()
    hostname = get_hostname()
    disco = get_disk_usage()

    info = (
        f"Información del sistema:\n"
        f"---------------------------------\n"
        f"Nombre del equipo: {hostname}\n"
        f"Fecha y hora: {fecha_hora}\n"
        f"Tiempo de actividad: {uptime}\n"
        f"Uso de disco: {disco}\n\n"
        f"Procesos activos (primeras 15 líneas):\n"
        f"{procesos_str}"
    )
    return info
