import pika
import json
import time

COLA_NOMBRE = 'simulations_queue'
URL_RABBIT = 'amqp://guest:guest@rabbitmq:5672'

try:
    connection = pika.BlockingConnection(pika.URLParameters(URL_RABBIT))
    channel = connection.channel()

    channel.queue_declare(queue=COLA_NOMBRE, durable=True)
    print(f" [*] Conectado a RabbitMQ. Esperando mensajes en la cola '{COLA_NOMBRE}'...")

    def callback(ch, method, properties, body):
        # !! VERIFICACIÓN CLAVE #4 !!
        # ESTO DEBE IMPRIMIRSE SI *ALGO* LLEGA
        print("\n==============================================")
        print(f" [x] ¡MENSAJE RECIBIDO! Crudo: {body.decode()}")
        print("==============================================")

        try:
            mensaje_nest = json.loads(body.decode())
            datos_reales = mensaje_nest.get('data') 
            patron = mensaje_nest.get('pattern')

            print(f" [✔] Patrón detectado: {patron}")
            print(f" [✔] Procesando datos: {datos_reales}")
            
            time.sleep(1) # Simula trabajo
            
            print(" [✔] Tarea completada.")
            
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f" [!] ERROR al procesar el mensaje: {e}")
            # No acusamos recibo (nack) para que se reintente si es necesario
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_consume(
        queue=COLA_NOMBRE,
        on_message_callback=callback
        # auto_ack=False por defecto, lo cual es correcto
    )

    channel.start_consuming()

except pika.exceptions.AMQPConnectionError as e:
    print(f" [!] ERROR: No se pudo conectar a RabbitMQ en {URL_RABBIT}")
    print(f" [!] Asegúrate que el servidor está corriendo y las credenciales son correctas.")
except KeyboardInterrupt:
    print('Consumidor detenido manualmente.')
    if 'connection' in locals() and connection.is_open:
        connection.close()