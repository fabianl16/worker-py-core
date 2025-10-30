from common.common_imports import *
from main import simulate_tank_data

# Conexión a RabbitMQ

rabbit_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672")
params = pika.URLParameters(rabbit_url)
connection = pika.BlockingConnection(params)
channel = connection.channel()

queue_name = "simulations_queue"
channel.queue_declare(queue=queue_name, durable=True)

print("🐍 Worker listo y esperando mensajes...")

def callback(ch, method, properties, body):
    try:
        message = json.loads(body)
        print("📩 Preset recibido:", message.get("preset_name"))

        # Extraer parámetros del mensaje
        days = message.get("days", 120)
        seed = message.get("seed", 101)
        start_time_str = message.get("start_time", "2025-01-01T12:00:00")
        start_time = datetime.fromisoformat(start_time_str)
        out_dir = message.get("out_dir", "simulation_output")
        tank_id = message.get("tank_id", 1)
        preset_dict = message.get("preset") 

        if not preset_dict:
            raise ValueError("No se recibió el preset en el mensaje.")

        # Ejecutar simulación
        df, paths = simulate_tank_data(
            days=days,
            config_dict=preset_dict,
            seed=seed,
            start_time=start_time,
            out_dir=out_dir,
            tank_id=tank_id
        )
        print(json.dumps(paths, indent=2))
    except Exception as e:
        print("❌ Error procesando la simulación:", e)

    finally:
        ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue=queue_name, on_message_callback=callback)
channel.start_consuming()