from .common_imports import *

# Importar nuestros módulos locales
from .environment import SimulationEnvironment
from .config_models import SimulationState, MINUTES_PER_DAY
from .core_functions import (
    calculate_sinusoidal_temperature,
    calculate_salinity_delta,
    update_salinity_state,
    calculate_sinusoidal_oxygen,
    calculate_hypoxia_event_value,
    apply_oxygen_floor,
    calculate_ph_diurnal_delta,
    calculate_ph_feed_delta,
    calculate_ph_o2_delta,
    calculate_ph_noise_delta,
    apply_ph_waterchange_recovery,
    apply_ph_smoothing,
    apply_ph_limits,
    update_feed_spike_state,
    calculate_o2_stress_penalty,
    calculate_temp_stress_penalty,
    calculate_density_stress_penalty,
    calculate_salinity_stress_penalty,
    apply_mortality_shock,
    convert_risk_to_mortality_rate,
    apply_mortality_limit,
    calculate_deaths_stochastic,
    apply_deaths_to_population,
    calculate_density,
    calculate_daily_feed_demand_kg,
    calculate_daily_growth
)


def simulation_step(t: int, env: SimulationEnvironment, prev_state: SimulationState, feed_kg_per_min_today: float) -> (SimulationState, Dict[str, Any]): # type: ignore
    """
    R.U.: Orquesta todas las funciones puras para UN solo minuto (t).
    Devuelve el nuevo estado y la fila de datos para guardar.
    """
    
    # --- Banderas de Eventos ---
    is_waterchange = (t in env.waterchange_schedule)
    is_o2_event = (t in env.o2_event_minutes)
    
    # --- 1. Temperatura ---
    temp = calculate_sinusoidal_temperature(
        t_min=t,
        config=env.temp_config,
        noise_source=env.get_normal_noise
    )
    temp_above_base = temp - env.temp_config.base 
    # --- 2. Salinidad ---
    sal_delta = calculate_salinity_delta(
        config=env.sal_config,
        noise_source=env.get_normal_noise,
        temp_above_base=temp_above_base,
        waterchange_active=is_waterchange
    )
    sal = update_salinity_state(prev_state.salinity, sal_delta)
    # --- 3. Alimentación (Feed) ---
    spike_remaining = update_feed_spike_state(prev_state.feed_spike_remaining)
    if t in env.feed_spike_schedule:
        spike_remaining = env.feed_spike_schedule[t]
        
    is_spike_active = (spike_remaining > 0)

    base_rate_per_min = feed_kg_per_min_today 
    noise_factor = env.get_uniform_noise(
        env.feed_config.noise_min_factor, 
        env.feed_config.noise_max_factor
    )
    spike_add = 0.0
    if is_spike_active:
        spike_add = env.feed_config.spike_multiplier * base_rate_per_min
    feed_rate = max(
            env.feed_config.min_feed_kg_min, 
            base_rate_per_min * (1.0 + noise_factor) + spike_add
        )
    # --- 4. Oxígeno (O2) ---
    if is_o2_event:
        o2_raw = calculate_hypoxia_event_value(env.o2_config, env.get_uniform_noise)
    else:
        o2_raw = calculate_sinusoidal_oxygen(
            t_min=t,
            config=env.o2_config,
            noise_source=env.get_normal_noise,
            temp_above_base=temp_above_base
        )
    o2 = apply_oxygen_floor(o2_raw, env.o2_config)
    # --- 5. pH ---
    ph_calc = env.ph_config.base
    ph_calc += calculate_ph_diurnal_delta(t, env.ph_config)
    ph_calc += calculate_ph_feed_delta(feed_rate, env.ph_config) 
    ph_calc += calculate_ph_o2_delta(o2, env.ph_config)
    ph_calc += calculate_ph_noise_delta(env.ph_config, env.get_normal_noise)
    if is_waterchange:
        ph_calc = apply_ph_waterchange_recovery(ph_calc, env.ph_config)
    ph_smoothed = apply_ph_smoothing(ph_calc, prev_state.ph, env.ph_config)
    ph = apply_ph_limits(ph_smoothed, env.ph_config)
    # --- 6. Población y Densidad ---
    stock_add = env.stocking_schedule.get(t, 0)
    survivors_before_deaths = prev_state.survivors + stock_add
    density = calculate_density(survivors_before_deaths, env.volume_L)
    # --- 7. Mortalidad ---
    p_o2 = env.mort_config.weight_o2 * calculate_o2_stress_penalty(o2, env.mort_config)
    p_temp = env.mort_config.weight_temp * calculate_temp_stress_penalty(temp, env.mort_config)
    p_rho = env.mort_config.weight_density * calculate_density_stress_penalty(density, env.mort_config)
    p_sal = env.mort_config.weight_salinity * calculate_salinity_stress_penalty(sal, env.mort_config)
    risk_base = p_o2 + p_temp + p_rho + p_sal
    risk_shocked = apply_mortality_shock(risk_base, o2, density, env.mort_config)
    m_rate = convert_risk_to_mortality_rate(risk_shocked, env.mort_config)
    m_rate = apply_mortality_limit(m_rate, env.mort_config)
    # --- 8. Supervivientes (Survivors) ---
    deaths = calculate_deaths_stochastic(
        n_previous=survivors_before_deaths,
        mortality_rate=m_rate,
        binomial_source=env.get_binomial_noise
    )
    survivors = apply_deaths_to_population(survivors_before_deaths, deaths)
    # --- 9. Crear Nuevo Estado y Fila de Salida ---
    new_timestamp = prev_state.timestamp + timedelta(minutes=1)
    new_state = SimulationState(
            timestamp=new_timestamp,
            temperature=temp,
            salinity=sal,
            oxygen=o2,
            ph=ph,
            feed_spike_remaining=spike_remaining,
            survivors=survivors,
            density=density, 
            current_weight_g=prev_state.current_weight_g, 
            biomass_kg=prev_state.biomass_kg             
    )
    row_data = {
        "timestamp_utc": new_timestamp.isoformat(),
        "tank_id": env.tank_id,
        "minute_index": t,
        "temperature_C": temp,
        "salinity_ppt": sal,
        "oxygen_mgL": o2,
        "pH": ph,
        "feed_kg_min": feed_rate,
        "density_shrimp_L": density,
        "survivors": survivors,
        "deaths": deaths,
        "current_weight_g": new_state.current_weight_g,
        "biomass_kg": new_state.biomass_kg,
        "waterchange": is_waterchange,
        "feed_spike": is_spike_active,
        "stock_add": stock_add,
        "mortality_rate_min": m_rate
    }    
    # --- 10. Sanity Checks ---
    for rule_function in env.sanity_pipeline:
        row_data = rule_function(row_data)
    final_row = {
        "timestamp_utc": row_data["timestamp_utc"],
        "tank_id": int(row_data["tank_id"]),
        "minute_index": int(row_data["minute_index"]),
        "temperature_C": round(row_data["temperature_C"], 4),
        "salinity_ppt": round(row_data["salinity_ppt"], 4),
        "oxygen_mgL": round(row_data["oxygen_mgL"], 3),
        "pH": round(row_data["pH"], 3),
        "feed_kg_min": round(row_data["feed_kg_min"], 6),
        "density_shrimp_L": round(row_data["density_shrimp_L"], 4),
        "survivors": int(row_data["survivors"]),
        "deaths": int(row_data["deaths"]),
        "current_weight_g": round(row_data["current_weight_g"], 4), 
        "biomass_kg": round(row_data["biomass_kg"], 4),           
        "waterchange": bool(row_data["waterchange"]),
        "feed_spike": bool(row_data["feed_spike"]),
        "stock_add": int(row_data["stock_add"])
    }
    return new_state, final_row

# --- COMPONENTE 5: El Runner del Bucle (SRP) ---
def run_simulation(env: SimulationEnvironment) -> List[Dict[str, Any]]:
    """
    R.U.: Ejecuta el bucle de simulación. MINUTO a MINUTO. 
    """
    print(f"Starting simulation for tank {env.tank_id} ({env.days} days)...")
    
    # Cargar params solo para el estado inicial

    state = env.get_initial_state()
        
    rows = []
    daily_feed_given_kg = 0.0 
    feed_kg_per_min_today = 0.0 
    daily_temps = []
    
    # --- Bucle Principal ---
    for t in range(env.minutes):
        
        # --- Lógica Diaria (se ejecuta al inicio del día, t=0, 1440, etc.) ---
        if t % MINUTES_PER_DAY == 0:
            day_number = t // MINUTES_PER_DAY
            # print(f"  Simulating Day {day_number + 1}...")
            
            # 1. Calcular biomasa actual (inicio del día)
            state.biomass_kg = (state.survivors * state.current_weight_g) / 1000.0
            
            # 2. Calcular demanda de feed para HOY (kg/día)
            daily_feed_demand_kg = calculate_daily_feed_demand_kg(
                state.biomass_kg,
                state.current_weight_g, 
                env.growth_config       
            )
            
            # 3. Calcular tasa de feed para los próximos minutos (kg/min)
            feed_kg_per_min_today = daily_feed_demand_kg / MINUTES_PER_DAY
            
            # 4. Resetear acumulador de comida del día
            daily_feed_given_kg = 0.0

        # --- Lógica Minuto a Minuto ---
        # Pasamos la tasa de feed calculada para el día actual
        new_state, output_row = simulation_step(t, env, state, feed_kg_per_min_today)
        
        # Acumulamos cuánto alimento se dio *realmente* este minuto
        daily_feed_given_kg += output_row["feed_kg_min"] 
        daily_temps.append(output_row["temperature_C"])
        
        rows.append(output_row)
        state = new_state # Actualizamos el estado para el siguiente minuto

        # --- Lógica Fin del Día (se ejecuta en t=1439) ---
        if (t + 1) % MINUTES_PER_DAY == 0:
            # Calcular nuevo peso basado en la comida *realmente* dada
            avg_temp_today = np.mean(daily_temps) if daily_temps else env.temp_config.base
            state.current_weight_g = calculate_daily_growth(
                current_weight_g=state.current_weight_g,
                feed_eaten_today_kg=daily_feed_given_kg,
                fcr=env.growth_config.fcr,
                survivors_at_end_of_day=state.survivors,
                avg_temp_today=avg_temp_today,     
                config=env.growth_config        
            )
            daily_temps = [] 
            # Imprimir progreso diario (opcional)
            # print(f"    End of Day {day_number + 1}: Weight={state.current_weight_g:.2f}g, Survivors={state.survivors}")

        # --- Condición de Parada (Cosecha) ---
        if state.current_weight_g >= env.growth_config.target_weight_g:
            print(f"  Target weight {env.growth_config.target_weight_g}g reached at minute {t}. Stopping simulation.")
            break 

    print(f"Simulation loop complete. {len(rows)} minutes generated.")
    return rows