from common.common_imports import *

from tank_simulator.environment import SimulationEnvironment
from tank_simulator.orchestration import run_simulation
from datetime import datetime
import pandas as pd

def export_results(
    rows: List[Dict[str, Any]], 
    env: SimulationEnvironment, 
    out_dir: str
) -> Dict[str, str]:
    """R.U.: Guarda los resultados (DataFrame y metadata) en disco."""
    print(f"Exporting results to {out_dir}...")
    
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
        
    print(f"✅ Export complete.")
    
    return {"csv": csv_path, "parquet": pq_path, "meta": meta_path}

def simulate_tank_data(
    days: int, 
    config_dict: dict, 
    seed: int, 
    start_time: datetime ,
    out_dir: str, 
    tank_id: int 
) -> (pd.DataFrame, Dict[str, str]): # type: ignore
    """
    R.U.: Orquesta los componentes de alto nivel:
    1. Setup
    2. Run
    3. Export
    """
    
    # 1. Setup (Configuración y Eventos)
    sim_start_time = start_time or datetime.utcnow()
    
    env = SimulationEnvironment(
        days=days,
        config_dict=config_dict,
        seed=seed,
        start_time=sim_start_time,
        tank_id=tank_id,

    )
    
    # 2. Run (Ejecutar el bucle)
    rows = run_simulation(env)
    
    # 3. Export (Guardar en disco)
    paths = export_results(rows, env, out_dir)
    
    return pd.DataFrame(rows), paths

# if __name__ == "__main__":
#     print("🚀 Iniciando simulación SOLID desde main.py...")
#     # Define la hora de inicio
#     start_time = datetime(2025, 1, 1, 12, 0, 0)

#     mi_configuracion = SEASON_PRESETS["perfect_lab"].copy()
        
#     df, paths = simulate_tank_data(
#         days=120,
#         config_dict=mi_configuracion,
#         seed=101,
#         start_time=start_time,
#         out_dir="simulation_output",
#         tank_id=1
#     )
    
#     # print("\n--- Resumen de la simulación (últimos 5 min) ---")
#     # print(df.tail())
    
#     print(f"\n✅ Simulación completada. Archivos guardados:")
#     print(json.dumps(paths, indent=2))