import os, json, pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Tuple
from tank_simulator.environment import SimulationEnvironment
from tank_simulator.orchestration import run_simulation

def export_results(
    rows: List[Dict[str, Any]], 
    env: SimulationEnvironment, 
    out_dir: str
) -> Dict[str, str]:
    df = pd.DataFrame(rows)
    os.makedirs(out_dir, exist_ok=True)    
    base_filename = f"tank_{env.tank_id}_{env.days}d_seed{env.seed}"
    csv_path = os.path.join(out_dir, f"{base_filename}.csv")
    pq_path = os.path.join(out_dir, f"{base_filename}.parquet")
    meta_path = os.path.join(out_dir, f"{base_filename}_meta.json")
    df.to_csv(csv_path, index=False)
    try:
        df.to_parquet(pq_path, index=False)
    except Exception as e:
        print(f"Warning: Could not save parquet file. {e}")
        pq_path = None
    meta = {
        "generated_at": datetime.utcnow().isoformat(),
        "seed": env.seed,
        "days": env.days,
        "minutes": env.minutes,
        "tank_id": env.tank_id,
        "start_time": env.start_time.isoformat(),
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)    
    return {"csv": csv_path, "parquet": pq_path, "meta": meta_path}


def simulate_tank_data(
    days: int,
    config_dict: dict,
    seed: int,
    start_time: datetime,
    out_dir: str,
    tank_id: int,
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
    paths = export_results(rows, env, out_dir)
    return pd.DataFrame(rows), paths