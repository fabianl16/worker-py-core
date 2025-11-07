
from datetime import datetime
import pandas as pd


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