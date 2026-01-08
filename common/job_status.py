from enum import Enum



class JobStatus(str, Enum):
    QUEUED = 'queued'
    SENDING_TO_START = 'sending-to-start'
    START_SIMULATION = 'start-simulation'

    VALIDATING = 'validating'
    RUNNING = 'running'
    GENERATING_FILES = 'generating-files'

    # --- NUEVO ETAPAS PARA PROCESO DE SUBIDA A MINIO ---
    PREPARING_UPLOAD = 'preparing-upload'
    QUEUED_FOR_UPLOAD = 'queued-for-upload'
    UPLOADING = 'uploading'
    VALIDATING_UPLOAD = 'validating-upload'
    UPLOAD_RETRYING = 'upload-retrying'
    UPLOAD_FAILED = 'upload-failed'
    UPLOAD_COMPLETED = 'upload-completed'

    # --- EXISTENTES ---
    RETRY_WAITING = 'retry-waiting'
    RETRYING = 'retrying'

    COMPLETED = 'completed'
    ERROR = 'error'
    TIMEOUT = 'timeout'
    CANCELLED = 'cancelled'

    FAILED_PERMANENTLY = 'failed-permanently'