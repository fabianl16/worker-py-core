# Imagen base oficial de Python (puedes ajustar la versión si tu proyecto usa otra)
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos del proyecto al contenedor
COPY . /app

# Copiar tu librería local (si no está dentro del proyecto principal)
COPY libraries/tank_simulator /tmp/tank_simulator

# Instalar dependencias del sistema necesarias (opcional, por si usas numpy/pandas)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc && \
    rm -rf /var/lib/apt/lists/*

# Instalar dependencias de Python desde requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Instalar tu paquete local
RUN pip install /tmp/tank_simulator

# Comando por defecto al arrancar el contenedor
CMD ["sleep", "infinity"]
