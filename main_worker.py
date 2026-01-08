from common.common_imports import *
from common.models import *
from common.simulation_utils import *
from common.redis_utils import *
from common.rabbit_utils import *
from common.logger import *
from common.job_status import *

redis_client = RedisClient(REDIS_URL)
logger = get_logger('SimulationWorker')

def callback(ch, method, properties, body):
    try:
        data = json.loads(body.decode())
        payload = SimulationPayload(**data["data"])
        job_id = payload.job_id
        logger.info(f"[→] Recibida simulación Job: {job_id}")
        redis_client.update_job(job_id, {"status": JobStatus.RUNNING.value, "progress": 0})
        
        def on_progress(percent: float):
            scaled_progress = round(percent * 0.70, 2)
            redis_client.publish_progress(
                job_id=job_id,
                channel=REDIS_SIMULATION_CHANNEL,
                status=JobStatus.RUNNING.value,
                progress=scaled_progress
            )

        df, paths = simulate_tank_data(
            days=payload.days,
            config_dict=payload.preset.model_dump(),
            seed=payload.seed,
            start_time=payload.start_time,
            out_dir=SIMULATIONS_OUT_DIR,
            tank_id=payload.tank_id,
            job_id=job_id,
            progress_callback=on_progress,
        )  

        # Enviando a MINIO-
        redis_client.publish_progress(job_id, REDIS_SIMULATION_CHANNEL, JobStatus.GENERATING_FILES.value, 70)

        cache_path = generate_chunks(df, job_id, payload.tank_id, out_dir=SIMULATIONS_OUT_DIR)

        redis_client.publish_progress(job_id, REDIS_SIMULATION_CHANNEL, JobStatus.GENERATING_FILES.value, 85)

        print(CACHE_SERVER_URL)
        if check_cache_server_alive(CACHE_SERVER_URL):
            cache_url = f"{CACHE_SERVER_URL}/cache/{job_id}/metadata"
        else:
            logger.warning("[!] Cache server no disponible, cache_url = null")
            cache_url = None

        redis_client.publish_progress(job_id, REDIS_SIMULATION_CHANNEL, JobStatus.PREPARING_UPLOAD.value, 90)

        upload_message = {
            "job_id": job_id,
            "tank_id": payload.tank_id,
            "csv_path": paths.get("csv"),
            "parquet_path": paths.get("parquet"),
            "cache_url": cache_url,
            "cache_path": cache_path,
        }


        logger.info(f"Paths para MinIO {upload_message}")

        channel.basic_publish(
            exchange="",
            routing_key=UPLOAD_QUEUE,
            body=json.dumps(upload_message)
        )

        redis_client.publish_progress(job_id, REDIS_SIMULATION_CHANNEL, JobStatus.QUEUED_FOR_UPLOAD.value, 92)

        redis_client.publish_progress(job_id, REDIS_SIMULATION_CHANNEL, JobStatus.PREPARING_UPLOAD.value, 95, cache_url)

        logger.info(f"[✔] Simulación completada para {job_id}. Archivos: {paths}")

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        logger.error(f"[!] Error ejecutando simulación (Encolando en DLX QUEUE) {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

if __name__ == "__main__":
    logger.info(f"[*] Esperando mensajes en {COLA_NOMBRE}...")
    conn, channel = create_rabbit_connection(URL_RABBIT, COLA_NOMBRE, callback)
    channel.start_consuming()