import redis
import json
from datetime import datetime
from typing import Dict, Any

class RedisClient:
    def __init__(self, url: str):
        self.client = redis.Redis.from_url(url, decode_responses=True)

    def register_job(self, job_id: str, data: Dict[str, Any]):
        self.client.hset(f"{job_id}", mapping=data)

    def update_job(self, job_id: str, updates: Dict[str, Any]):
        updates["updated_at"] = datetime.utcnow().isoformat()
        self.client.hset(f"{job_id}", mapping=updates)

    def complete_job(self, job_id: str):
        self.update_job(job_id, {
            "status": "completed",
            "progress": 100,
        })

    def job_exists(self, job_id: str) -> bool:
        return self.client.exists(f"{job_id}") == 1
    
    def publish(self, channel, message: dict):
        self.client.publish(channel, json.dumps(message))
