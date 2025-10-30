from .common_imports import *

class PresetSchema(BaseModel):
    """
    Esta es nuestra "Interface". Valida que un diccionario de preset
    tenga TODAS las claves requeridas y que sean del tipo correcto.
    """
    # --- Temperatura ---
    T_base: float
    A_T: float
    sigma_T: float
    drift_T_per_day: float

    # --- Salinidad ---
    S_base: float
    drift_S_per_min: float
    sigma_S: float
    waterchange_reduction: float
    k_evap_per_deg: float
    waterchange_frequency_days: float

    # --- Oxígeno disuelto ---
    O2_base: float
    A_O2: float
    sigma_O2: float
    k_T_O2: float
    O2_event_prob_per_day: float
    hypoxia_min: float
    hypoxia_max: float
    O2_floor: float

    # --- pH ---
    pH_base: float
    A_pH: float
    sigma_pH: float
    k_feed_acid: float
    k_O2_pH: float
    pH_recovery_on_waterchange: float
    O2_pH_threshold: float
    pH_smoothing_alpha: float
    pH_min_limit: float
    pH_max_limit: float
    pH_phase: float = 0.0  

    # --- Feed ---
    Feed_base: float
    feed_spike_multiplier: float
    feed_spike_prob_per_day: float
    feed_spike_duration_min: Tuple[int, int]
    feed_noise_min_factor: float
    feed_noise_max_factor: float
    feed_min_kg_min: float

    # --- Stock ---
    V: float
    initial_N: int
    stocking_prob_per_day: float
    stocking_min: int
    stocking_max: int

    # --- Mortalidad (Pesos) ---
    alpha: float
    beta: float
    gamma: float
    weight_salinity: float

    # --- Mortalidad (Parámetros) ---
    kappa: float
    shock_factor: float
    O2_crit_for_shock: float
    density_crit_for_shock: float
    max_mortality_rate: float

    # --- Mortalidad (Estrés Base) ---
    T_opt: float
    O2_crit: float
    rho_opt: float
    salinity_optimal_min: float
    salinity_optimal_max: float
    salinity_lethal_low: float
    salinity_lethal_high: float

    # --- PARÁMETROS DE SANIDAD ---
    sanity_temp_crit_for_ph: float
    sanity_ph_min_at_crit_temp: float
    sanity_ph_fix_noise_min: float
    sanity_ph_fix_noise_max: float
    sanity_o2_crit_for_ph: float
    sanity_ph_max_at_crit_o2: float
    sanity_density_crit_for_o2: float
    sanity_o2_max_at_crit_density: float
    sanity_o2_fix_noise_min: float
    sanity_o2_fix_noise_max: float
    sanity_salinity_max_with_wc: float
    sanity_sal_fix_noise_min: float
    sanity_sal_fix_noise_max: float
    sanity_max_mortality_ratio: float

    # --- Parámetros de Crecimiento ---
    initial_weight_g: float
    target_weight_g: float
    fcr: float
    feed_table: List[Tuple[float, float]]
    temp_min_growth: float
    temp_optimal_growth: float
    temp_max_growth: float