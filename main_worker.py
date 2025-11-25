from common.common_imports import *
from common.models import *
from common.simulation_utils import simulate_tank_data
from common.redis_utils import *
from common.rabbit_utils import *
from common.logger import *

redis_client = RedisClient(REDIS_URL)
logger = get_logger('SimulationWorker')

def callback(ch, method, properties, body):
    try:
        data = json.loads(body.decode())
        payload = SimulationPayload(**data["data"])
        job_id = payload.job_id

        logger.info(f"Recibida simulación Job: {job_id}")

        if not job_id:
            logger.error("[!] job_id missing in message")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            return
    
        redis_client.update_job(job_id, {"status": "running", "progress": 0})

        def on_progress(percent: float):
            progress_data = {
                "progress": round(percent, 2),
                "status": "running",
            }
            redis_client.update_job(job_id, progress_data)
            redis_client.publish(REDIS_SIMULATION_CHANNEL,         
            json.dumps({
                "id": job_id,
                **progress_data
            }))

        df, paths = simulate_tank_data(
            days=payload.days,
            config_dict=payload.preset.model_dump(),
            seed=payload.seed,
            start_time=payload.start_time,
            out_dir="simulation_output",
            tank_id=payload.tank_id,
            progress_callback=on_progress,
        )

        redis_client.complete_job(job_id)
        redis_client.publish(REDIS_SIMULATION_CHANNEL, json.dumps({
            "id": job_id,
            "status": "completed",
            "progress": 100
        }))
        logger.info(f"[✔] Simulación completada para {job_id}. Archivos: {paths}")
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"[!] Error ejecutando simulación: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

if __name__ == "__main__":
    logger.info(f"[*] Esperando mensajes en {COLA_NOMBRE}...")
    conn, channel = create_rabbit_connection(URL_RABBIT, COLA_NOMBRE, callback)
    channel.start_consuming()