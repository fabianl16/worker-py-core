import json
import os
from minio import Minio
from common.redis_utils import RedisClient
from common.logger import get_logger
from common.rabbit_utils import create_rabbit_connection
from common.common_imports import *
from common.job_status import *


logger = get_logger("MinioUploaderWorker")

redis_client = RedisClient(REDIS_URL)

minio_client = Minio(
    MINIO_URL,
    access_key=MINIO_ACCESS,
    secret_key=MINIO_SECRET,
    secure=False
)

# Crear bucket si no existe
if not minio_client.bucket_exists(MINIO_BUCKET):
    minio_client.make_bucket(MINIO_BUCKET)
    logger.info(f"[+] Bucket '{MINIO_BUCKET}' creado")

def upload_file(local_path: str, remote_path: str):
    minio_client.fput_object(
        bucket_name=MINIO_BUCKET,
        object_name=remote_path,
        file_path=local_path
    )

def callback(ch, method, properties, body):
    try:
        data = json.loads(body.decode())
        job_id = data["job_id"]
        tank_id = data["tank_id"]

        parquet = data["parquet_path"]
        csv = data["csv_path"]
        cache_url = data["cache_url"]

        remote_folder = f"{job_id}/tank_{tank_id}"

        redis_client.publish_progress(job_id, REDIS_SIMULATION_CHANNEL, JobStatus.VALIDATING_UPLOAD.value, 95, cache_url)

        missing_files = []

        if not parquet or not os.path.exists(parquet):
            missing_files.append("parquet")

        if not csv or not os.path.exists(csv):
            missing_files.append("csv")
        
        if missing_files:
            error_msg = f"Archivos faltantes: {', '.join(missing_files)}"
            logger.error(f"[✖] {error_msg} | job={job_id}")

            redis_client.publish_progress(
                job_id,
                REDIS_SIMULATION_CHANNEL,
                JobStatus.UPLOAD_FAILED.value,
                100,
                cache_url
            )

            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        redis_client.publish_progress(job_id, REDIS_SIMULATION_CHANNEL, JobStatus.UPLOADING.value, 96, cache_url)

        upload_file(parquet, f"{remote_folder}/output.parquet")
        redis_client.publish_progress(
            job_id,
            REDIS_SIMULATION_CHANNEL,
            JobStatus.UPLOADING.value,
            98,
            cache_url
        )

        upload_file(csv, f"{remote_folder}/output.csv")
        redis_client.publish_progress(
            job_id,
            REDIS_SIMULATION_CHANNEL,
            JobStatus.UPLOADING.value,
            99,
            cache_url
        )

        final_url = (
            f"http://{MINIO_URL}/"
            f"{MINIO_BUCKET}/"
            f"{job_id}/tank_{tank_id}/output.csv"
        )

        logger.info(f"[✔] Subida correcta en MinIO para job {job_id}")
        redis_client.publish_progress(job_id, REDIS_SIMULATION_CHANNEL, JobStatus.COMPLETED.value, 100, final_url)

        ch.basic_ack(delivery_tag=method.delivery_tag)

    except Exception as e:
        redis_client.publish_progress(job_id, REDIS_SIMULATION_CHANNEL, JobStatus.UPLOAD_FAILED.value, 100, cache_url)
        logger.error(f"[!] Error subiendo a MinIO: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


if __name__ == "__main__":
    logger.info(f"[*] Esperando mensajes en {UPLOAD_QUEUE}...")
    conn, channel = create_rabbit_connection(
        URL_RABBIT,
        UPLOAD_QUEUE,
        callback
    )
    channel.start_consuming()