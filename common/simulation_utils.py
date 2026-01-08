import os, json, pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Tuple
from tank_simulator.environment import SimulationEnvironment
from tank_simulator.orchestration import run_simulation
import requests

def export_results(
    rows: List[Dict[str, Any]], 
    env: SimulationEnvironment, 
    out_dir: str,
    job_id: str
) -> Dict[str, str]:
    df = pd.DataFrame(rows)
    tank_folder = os.path.join(out_dir, f"tank_{env.tank_id}")
    os.makedirs(tank_folder, exist_ok=True)
    base_filename = f"{job_id}_tank_{env.tank_id}_seed{env.seed}"
    csv_path = os.path.join(tank_folder, f"{base_filename}.csv")
    pq_path = os.path.join(tank_folder, f"{base_filename}.parquet")

    df.to_csv(csv_path, index=False)
    try:
        df.to_parquet(pq_path, index=False)
    except Exception as e:
        print(f"Warning: Could not save parquet file. {e}")
        pq_path = None

    return {"csv": csv_path, "parquet": pq_path}


def simulate_tank_data(
    days: int,
    config_dict: dict,
    seed: int,
    start_time: datetime,
    out_dir: str,
    tank_id: int,
    job_id: str,
    progress_callback=None
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    env = SimulationEnvironment(
        days=days,
        config_dict=config_dict,
        seed=seed,
        start_time=start_time,
        tank_id=tank_id,
    )

    rows = run_simulation(env, progress_callback=progress_callback)
    paths = export_results(rows, env, out_dir, job_id)
    return pd.DataFrame(rows), paths


def generate_chunks(df: pd.DataFrame, job_id: str, tank_id: int, out_dir: str, chunk_size=50000):
    tank_folder = os.path.join(out_dir, f"tank_{tank_id}")
    cache_folder = os.path.join(tank_folder, f"{job_id}_cache")
    os.makedirs(cache_folder, exist_ok=True)

    chunks = []
    total_rows = len(df)

    for i, start in enumerate(range(0, total_rows, chunk_size)):
        end = start + chunk_size
        chunk_df = df.iloc[start:end]
        chunk_path = os.path.join(cache_folder, f"chunk_{i+1}.json")
        chunk_df.to_json(chunk_path, orient="records")
        chunks.append(chunk_path)

    # Metadata
    metadata = {
        "job_id": job_id,
        "rows": total_rows,
        "chunks": len(chunks),
        "chunk_size": chunk_size
    }

    with open(os.path.join(cache_folder, "index.json"), "w") as f:
        json.dump(metadata, f, indent=2)

    return cache_folder

def check_cache_server_alive(cache_server_url: str) -> bool:
    print(f"{cache_server_url}/health")
    try:
        health_url = f"{cache_server_url}/health"
        response = requests.get(health_url, timeout=2)
        return response.status_code == 200
    except Exception:
        return False