from .common_imports import *

from .config_models import (
    TemperatureConfig, SalinityConfig, OxygenConfig, pHConfig, FeedConfig,
    MortalityConfig, SanityConfig, GrowthConfig,
    NoiseSource, UniformNoiseSource, BinomialSource, SimStateRow,
    MINUTES_PER_DAY
)

# --- FUNCIONES DE CÁLCULO ---

def calculate_density(survivors: int, volume_L: float) -> float:
    """Calcula la densidad (ej. organismos/L)."""
    return max(0.0, survivors / volume_L)

def calculate_sinusoidal_temperature(
    t_min: int, 
    config: TemperatureConfig, 
    noise_source: NoiseSource, 
    phase: float = 0.0
) -> float:
    """Calcula la temperatura (°C) en t_min usando un modelo sinusoidal."""
    minute_of_day = t_min % 1440
    daily = config.amplitude * np.sin(2 * np.pi * minute_of_day / 1440.0 + phase)
    drift = config.drift_per_day * (t_min / 1440.0)    
    noise = noise_source(0, config.sigma) 
    
    return config.base + daily + drift + noise

def calculate_salinity_delta(
    config: SalinityConfig,
    noise_source: NoiseSource,
    temp_above_base: float,
    waterchange_active: bool,
) -> float:
    """Calcula el *cambio* (delta) en salinidad para un minuto."""
    delta_evap = config.k_evap_per_deg * max(0.0, temp_above_base)
    delta_drift = config.drift_per_min
    delta_repl = config.waterchange_reduction if waterchange_active else 0.0
    noise = noise_source(0, config.sigma)
        
    return delta_evap + delta_drift - delta_repl + noise

def update_salinity_state(prev_sal: float, delta: float) -> float:
    """Aplica el delta al estado anterior."""
    return max(0.0, prev_sal + delta)

def calculate_sinusoidal_oxygen(
    t_min: int,
    config: OxygenConfig,
    noise_source: NoiseSource,
    temp_above_base: float
) -> float:
    """Calcula el O2 'normal' (sinusoidal, afectado por T)."""
    diurnal = config.amplitude * np.sin(2 * np.pi * (t_min % 1440) / 1440)
    noise = noise_source(0, config.sigma)
    temp_effect = config.k_temp * temp_above_base
    
    return config.base + diurnal - temp_effect + noise

def calculate_hypoxia_event_value(
    config: OxygenConfig,
    uniform_noise_source: UniformNoiseSource
) -> float:
    """Calcula el valor de O2 durante un evento de hipoxia."""
    return uniform_noise_source(config.hypoxia_min, config.hypoxia_max)

def apply_oxygen_floor(o2_value: float, config: OxygenConfig) -> float:
    """Asegura que el valor de O2 no caiga bajo el suelo."""
    return max(o2_value, config.floor)

def calculate_ph_diurnal_delta(t_min: int, config: pHConfig) -> float:
    """Calcula el delta de pH basado en el ciclo diurno (sinusoidal)."""
    minute_of_day = t_min % 1440
    return config.amplitude * np.sin(2 * np.pi * minute_of_day / 1440.0 + config.phase)

def calculate_ph_feed_delta(feed_t_kg_min: float, config: pHConfig) -> float:
    """Calcula el delta de pH basado en la alimentación."""
    return -config.k_feed_acid * feed_t_kg_min

def calculate_ph_feed_delta(feed_t_kg_min: float, config: pHConfig) -> float:
    """Calcula el delta de pH basado en la alimentación."""
    return -config.k_feed_acid * feed_t_kg_min

def calculate_ph_o2_delta(O2_t: Optional[float], config: pHConfig) -> float:
    """Calcula el delta de pH basado en el déficit de oxígeno."""
    if O2_t is None:
        return 0.0
    o2_deficit = max(0.0, (config.o2_acid_threshold - O2_t))
    return -config.k_o2_acid * o2_deficit

def calculate_ph_noise_delta(config: pHConfig, noise_source: NoiseSource) -> float:
    """Calcula el delta de ruido aleatorio para el pH."""
    return noise_source(0, config.sigma)

def apply_ph_waterchange_recovery(
    ph_value: float, 
    config: pHConfig
) -> float:
    """Aplica una recuperación parcial hacia el pH base."""
    # (1 - factor) * actual + factor * objetivo
    factor = config.waterchange_recovery_factor
    return (1 - factor) * ph_value + (factor * config.base)

def apply_ph_smoothing(
    current_ph_calculated: float, 
    prev_ph_state: float, 
    config: pHConfig
) -> float:
    """Suaviza el nuevo valor calculado con el estado anterior."""
    alpha = config.smoothing_alpha
    return (alpha * current_ph_calculated) + ((1 - alpha) * prev_ph_state)

def apply_ph_limits(ph_value: float, config: pHConfig) -> float:
    """Aplica los límites (suelo/techo) realistas al valor de pH."""
    return max(config.min_limit, min(config.max_limit, ph_value))

def calculate_feed_rate_kg_min(
    config: FeedConfig,
    noise_source: UniformNoiseSource,
    is_spike_active: bool
) -> float:
    """Calcula la tasa de feed (kg/min) para el minuto actual."""

    base_rate_per_min = config.base_kg_per_day / MINUTES_PER_DAY    
    noise_factor = noise_source(
        config.noise_min_factor, 
        config.noise_max_factor
    )
    spike_add = 0.0
    if is_spike_active:
        spike_add = config.spike_multiplier * base_rate_per_min
        
    total_feed = base_rate_per_min * (1.0 + noise_factor) + spike_add
    
    return max(config.min_feed_kg_min, total_feed)

def update_feed_spike_state(
    current_spike_remaining_min: int
) -> int:
    """Actualiza el estado (contador) del spike."""
    return max(0, current_spike_remaining_min - 1)

def calculate_o2_stress_penalty(
    o2_t: float, 
    config: MortalityConfig
) -> float:
    """Calcula la penalización por bajo O2."""
    return max(0.0, config.o2_critical_threshold - o2_t)

def calculate_temp_stress_penalty(
    temp_t: float, 
    config: MortalityConfig
) -> float:
    """Calcula la penalización por alta Temperatura."""
    return max(0.0, temp_t - config.temp_optimal_threshold)

def calculate_density_stress_penalty(
    rho_t: float, 
    config: MortalityConfig
) -> float:
    """Calcula la penalización por alta Densidad."""
    return max(0.0, rho_t - config.density_optimal_threshold)

def apply_mortality_shock(
    risk_score: float, 
    o2_t: float, 
    rho_t: float, 
    config: MortalityConfig
) -> float:
    """RESPONSABILIDAD: Aplica un multiplicador de shock si se cumplen las condiciones."""
    is_shock_condition = (
        (o2_t < config.o2_shock_threshold) and 
        (rho_t > config.density_shock_threshold)
    )
    
    if is_shock_condition:
        return risk_score * config.shock_factor
    return risk_score

def convert_risk_to_mortality_rate(
    risk_score: float, 
    config: MortalityConfig
) -> float:
    """Convierte el 'risk_score' (r) a tasa (m) vía sigmoide, risk_score = 0 DEBE producir m_rate = 0."""
    if risk_score <= 0:
        return 0.0
    sigmoid_risk = 1.0 / (1.0 + np.exp(-risk_score))
    scaled_risk = (sigmoid_risk - 0.5) * 2.0
    
    return config.kappa_scaler * scaled_risk

def apply_mortality_limit(
    rate: float, 
    config: MortalityConfig
) -> float:
    """RESPONSABILIDAD: Aplica un límite superior (techo) a la tasa."""
    return min(rate, config.max_mortality_rate)

def calculate_deaths_deterministic(
    n_previous: int, 
    mortality_rate: float
) -> int:
    """Calcula muertes como una fracción determinista de la población."""
    rate = max(0.0, min(1.0, mortality_rate))
    n_pop = max(0, n_previous)
    return int(n_pop * rate)

def calculate_deaths_stochastic(
    n_previous: int, 
    mortality_rate: float,
    binomial_source: BinomialSource
) -> int:
    """Calcula muertes usando una fuente de distribución binomial inyectada."""
    rate = max(0.0, min(1.0, mortality_rate))
    n_pop = max(0, n_previous)
    
    if n_pop == 0 or rate == 0.0:
        return 0
    return binomial_source(n_pop, rate)

def apply_deaths_to_population(
    n_previous: int, 
    n_deaths: int
) -> int:
    """Aplica las muertes a la población, asegurando que no sea negativa."""
    return max(0, n_previous - n_deaths)

def apply_sanity_temp_ph_check(
    row: SimStateRow, 
    config: SanityConfig, 
    noise: UniformNoiseSource
) -> SimStateRow:
    """Corrige pH si T es alta y pH es bajo."""
    if (row["temperature_C"] > config.temp_crit_for_ph and 
        row["pH"] < config.ph_min_at_crit_temp):
        
        new_row = row.copy() 
        fix = noise(config.ph_fix_noise_min, config.ph_fix_noise_max)
        new_row["pH"] = config.ph_min_at_crit_temp + fix
        return new_row
    return row 

def apply_sanity_o2_ph_check(
    row: SimStateRow, 
    config: SanityConfig
) -> SimStateRow:
    """Corrige pH si O2 es crítico y pH es alto."""
    if (row["oxygen_mgL"] < config.o2_crit_for_ph and 
        row["pH"] > config.ph_max_at_crit_o2):
        new_row = row.copy()
        new_row["pH"] = config.ph_max_at_crit_o2
        return new_row
    return row

def apply_sanity_density_o2_check(
    row: SimStateRow, 
    config: SanityConfig, 
    noise: UniformNoiseSource
) -> SimStateRow:
    """Corrige O2 si la densidad es alta y O2 es alto."""
    if (row["density_shrimp_L"] > config.density_crit_for_o2 and 
        row["oxygen_mgL"] > config.o2_max_at_crit_density):
        
        new_row = row.copy()
        fix = noise(config.o2_fix_noise_min, config.o2_fix_noise_max)
        new_row["oxygen_mgL"] = config.o2_max_at_crit_density - fix
        return new_row
    return row

def apply_sanity_waterchange_salinity_check(
    row: SimStateRow, 
    config: SanityConfig, 
    noise: UniformNoiseSource
) -> SimStateRow:
    """Corrige Salinidad si hay recambio y S es alta."""
    if row["waterchange"] and row["salinity_ppt"] > config.salinity_max_with_wc:
        new_row = row.copy()
        fix = noise(config.sal_fix_noise_min, config.sal_fix_noise_max)
        new_row["salinity_ppt"] = config.salinity_max_with_wc + fix
        return new_row
    return row

def apply_sanity_mortality_check(
    row: SimStateRow, 
    config: SanityConfig
) -> SimStateRow:
    """Limita las muertes a un % de la población."""
    survivors = row.get("survivors", 0)
    deaths = row.get("deaths", 0)
    max_deaths = int(survivors * config.max_mortality_ratio)
    if deaths > max_deaths:
        new_row = row.copy()
        new_row["deaths"] = max_deaths
        return new_row
    return row

def calculate_daily_growth(
    current_weight_g: float,
    feed_eaten_today_kg: float,
    fcr: float,
    survivors_at_end_of_day: int,
    avg_temp_today: float, 
    config: GrowthConfig   
) -> float:
    """Calcula el nuevo peso individual promedio al final del día. Modelo simple basado en FCR y ajustado por temperatura."""
    if survivors_at_end_of_day <= 0:
        return current_weight_g
    temp_factor = 0.0
    if config.temp_min_growth < avg_temp_today < config.temp_max_growth:
        if avg_temp_today <= config.temp_optimal_growth:
            temp_factor = (avg_temp_today - config.temp_min_growth) / \
                          (config.temp_optimal_growth - config.temp_min_growth)
        else:
            temp_factor = 1.0 - (avg_temp_today - config.temp_optimal_growth) / \
                            (config.temp_max_growth - config.temp_optimal_growth)
        temp_factor = max(0.0, min(1.0, temp_factor)) 
    potential_biomass_gain_kg = feed_eaten_today_kg / fcr
    potential_individual_gain_g = (potential_biomass_gain_kg / survivors_at_end_of_day) * 1000.0 if survivors_at_end_of_day > 0 else 0
    actual_individual_gain_g = potential_individual_gain_g * temp_factor
    new_weight_g = current_weight_g + actual_individual_gain_g

    return new_weight_g

def get_feed_rate_for_weight(
    current_weight_g: float, 
    feed_table: List[tuple[float, float]]
) -> float:
    """Función auxiliar pura para obtener la tasa de alimentación correcta de la tabla según el peso actual."""
    for (max_weight, feed_rate) in feed_table:
        if current_weight_g <= max_weight:
            return feed_rate            
    return feed_table[-1][1] if feed_table else 0.04 

def calculate_daily_feed_demand_kg(
    biomass_kg: float, 
    current_weight_g: float,
    config: GrowthConfig      
) -> float:
    """Calcula la demanda diaria de alimento (kg) basada en la biomasa y la tabla de alimentación."""
    feed_rate_percent = get_feed_rate_for_weight(
            current_weight_g, 
            config.feed_table
    )
    return biomass_kg * feed_rate_percent

def calculate_salinity_stress_penalty(
    salinity_t: float,
    config: MortalityConfig
) -> float:
    """Calcula la penalización por estrés salino (0=óptimo, 1=letal)."""
    penalty = 0.0
    if salinity_t < config.salinity_optimal_min:
        if salinity_t <= config.salinity_lethal_low:
            penalty = 1.0 
        else:
            penalty = (config.salinity_optimal_min - salinity_t) / \
                      (config.salinity_optimal_min - config.salinity_lethal_low)                  
    elif salinity_t > config.salinity_optimal_max:
        if salinity_t >= config.salinity_lethal_high:
            penalty = 1.0 
        else:
            penalty = (salinity_t - config.salinity_optimal_max) / \
                      (config.salinity_lethal_high - config.salinity_optimal_max)
                      
    return max(0.0, min(1.0, penalty)) 