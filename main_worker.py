from common.common_imports import *
from common.models import *
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
    start_time: datetime ,
    out_dir: str, 
    tank_id: int 
) -> (pd.DataFrame, Dict[str, str]): # type: ignore

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



print(f"[*] Esperando mensajes en {URL_RABBIT}...")

connection = pika.BlockingConnection(pika.URLParameters(URL_RABBIT))
channel = connection.channel()
channel.queue_declare(queue=COLA_NOMBRE, durable=True)
print(f"[*] Esperando mensajes en {COLA_NOMBRE}...")

def callback(ch, method, properties, body):
    try:
        body_dict = json.loads(body.decode())
        payload = SimulationPayload(**body_dict["data"]) 
        #Ejecutar simulación
        df, paths = simulate_tank_data(
            days=payload.days,
            config_dict=payload.preset.model_dump(),
            seed=payload.seed,
            start_time=payload.start_time,
            out_dir="simulation_output",
            tank_id=payload.tank_id
        )
        print(f"[✔] Simulación completada. Archivos: {paths}")
        
        ch.basic_ack(delivery_tag=method.delivery_tag)

    except ValidationError as e:
        print(f"[!] Error de validación del mensaje: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    except Exception as e:
        print(f"[!] Error ejecutando simulación: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

channel.basic_consume(queue=COLA_NOMBRE, on_message_callback=callback)
channel.start_consuming()