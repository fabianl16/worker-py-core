# ==== Librerías base ====
import os
import json
import numpy as np
import pandas as pd
import pika
import time

# ==== Fechas y tiempo ====
from datetime import datetime, timedelta

# ==== Tipos genéricos ====
from typing import List, Dict, Any, Set, Callable, Optional, Tuple

# ==== Utilidades ====
from functools import partial

# ==== Modelado y validación ====
from dataclasses import dataclass
from pydantic import BaseModel, ValidationError


# ==== Rabbit Config ====
RABBIT_USER = os.environ.get("RABBITMQ_USER", "guest")
RABBIT_PASS = os.environ.get("RABBITMQ_PASS", "guest")
RABBIT_HOST = os.environ.get("RABBITMQ_HOST", "localhost")
RABBIT_PORT = os.environ.get("RABBITMQ_PORT", "5672")
UPLOAD_QUEUE = os.environ.get("RABBITMQ_UPLOAD_QUEUE", "minio_upload_queue")
COLA_NOMBRE = os.environ.get("RABBITMQ_SIMULATIONS_QUEUE", "simulations_queue")
URL_RABBIT = f"amqp://{RABBIT_USER}:{RABBIT_PASS}@{RABBIT_HOST}:{RABBIT_PORT}"

# ==== Redis Config ====
REDIS_HOST  =  os.environ.get("REDIS_HOST", "guest")
REDIS_PORT  =  os.environ.get("REDIS_PORT", "guest")
REDIS_URL   =  f"redis://{REDIS_HOST}:{REDIS_PORT}"
REDIS_SIMULATION_CHANNEL = os.environ.get("REDIS_SIMULATION_CHANNEL", "guest")
REDIS_SIMULATION_NAMESPACE = os.environ.get("REDIS_SIMULATION_NAMESPACE", "guest")
REDIS_SIMULATION_EVENT = os.environ.get("REDIS_SIMULATION_EVENT", "guest")


# ==== Simulations Config ====
SIMULATIONS_OUT_DIR= os.getenv("SIMULATIONS_OUT_DIR", "simulations_storage")
CACHE_SERVER_URL = os.getenv("CACHE_SERVER_URL", "http://localhost:8000")

# ==== Simulations Upload Config ====
MINIO_URL = os.getenv("MINIO_URL", "localhost:9000")
MINIO_ACCESS = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "simulations")

__all__ = [
    # Librerías base
    "os", "json", "np", "pd",

    # Tiempo
    "datetime", "timedelta", "time",

    # Tipado
    "List", "Dict", "Any", "Set", "Callable", "Optional", "Tuple", "BaseModel", "ValidationError",

    # Utilidades
    "partial",

    # Modelado
    "dataclass", "BaseModel", "ValidationError",

    #Conexiones
    "pika",

    # Configuración RABBIT
    "RABBIT_USER", "RABBIT_PASS", "RABBIT_HOST", "RABBIT_PORT", "COLA_NOMBRE", "URL_RABBIT", "UPLOAD_QUEUE",

    #Configuracion REDIS
    "REDIS_HOST", "REDIS_PORT", "REDIS_URL", "REDIS_SIMULATION_CHANNEL", "REDIS_SIMULATION_NAMESPACE", "REDIS_SIMULATION_EVENT",

    #Configuracion simulations data
    "SIMULATIONS_OUT_DIR", "CACHE_SERVER_URL",

    #Simulations Upload
    "MINIO_URL", "MINIO_ACCESS", "MINIO_SECRET", "MINIO_BUCKET"

]