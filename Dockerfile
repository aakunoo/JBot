FROM python:3.13-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y procps

# Copiar requirements.txt primero para aprovechar la caché de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código fuente
COPY . .

# Asegurarse de que el directorio src existe y tiene los permisos correctos
RUN mkdir -p /app/src && chmod -R 755 /app/src

# Establecer PYTHONPATH
ENV PYTHONPATH=/app

# Ejecutar la aplicación
CMD ["python", "-m", "src.main"]