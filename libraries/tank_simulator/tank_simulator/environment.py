from .common_imports import *
# Importar nuestros módulos locales
# from presets import SEASON_PRESETS
from .config_models import (
    TemperatureConfig, SalinityConfig, OxygenConfig, pHConfig, FeedConfig,
    MortalityConfig, SanityConfig, GrowthConfig, SimulationState,
    MINUTES_PER_DAY
)
from .preset_schema import PresetSchema

# Importar las funciones de cálculo que necesita para generar schedules
from .core_functions import (
    calculate_density,
    apply_sanity_temp_ph_check, apply_sanity_o2_ph_check,
    apply_sanity_density_o2_check, apply_sanity_waterchange_salinity_check,
    apply_sanity_mortality_check
)

class SimulationEnvironment:
    """
    Contenedor de Inyección de Dependencias (DIP).
    Construye y contiene toda la configuración, los generadores de
    aleatoriedad y los horarios de eventos.
    """
    def __init__(self, days: int, config_dict: dict, seed: int, start_time: datetime, 
                 tank_id: int):

        self.days = days
        self.minutes = int(days * MINUTES_PER_DAY)
        self.seed = seed
        self.start_time = start_time
        self.tank_id = tank_id

        # 1. VALIDACIÓN ESTRICTA (Estilo "Interface" TS)
        #    Aquí usamos Pydantic para validar todo el diccionario.
        try:
            # Intenta crear el modelo Pydantic a partir del diccionario
            params_model = PresetSchema(**config_dict)
        except ValidationError as e:
            # Si falla, Pydantic da un error MUY detallado
            print("="*50)
            print("¡ERROR! El preset de configuración es inválido.")
            print("Revisa que TODAS las claves estén presentes y tengan el tipo correcto.")
            print("="*50)
            raise ValueError(f"Error de validación en el preset:\n{e}")
        
        # 2. Inyección de Dependencia de Aleatoriedad (DIP)
        self.rng = np.random.default_rng(seed)

        # 3. Crear todas las Configs (ISP)
        #    Ahora leemos desde 'params_model.clave' en lugar de 'params["clave"]'.
        #    Esto es 100% seguro porque Pydantic ya lo validó.
        try:
            self.volume_L = params_model.V
            self.initial_N = params_model.initial_N 

            self.temp_config = TemperatureConfig(
                base=params_model.T_base,
                amplitude=params_model.A_T,
                sigma=params_model.sigma_T,
                drift_per_day=params_model.drift_T_per_day
            )
            self.sal_config = SalinityConfig(
                base=params_model.S_base,
                drift_per_min=params_model.drift_S_per_min,
                sigma=params_model.sigma_S,
                k_evap_per_deg=params_model.k_evap_per_deg,
                waterchange_reduction=params_model.waterchange_reduction
            )
            self.o2_config = OxygenConfig(
                base=params_model.O2_base, amplitude=params_model.A_O2, sigma=params_model.sigma_O2,
                k_temp=params_model.k_T_O2, hypoxia_min=params_model.hypoxia_min,
                hypoxia_max=params_model.hypoxia_max, floor=params_model.O2_floor
            )
            self.ph_config = pHConfig(
                 base=params_model.pH_base, amplitude=params_model.A_pH,
                 sigma=params_model.sigma_pH, phase=params_model.pH_phase,
                 k_feed_acid=params_model.k_feed_acid, k_o2_acid=params_model.k_O2_pH,
                 o2_acid_threshold=params_model.O2_pH_threshold,
                 waterchange_recovery_factor=params_model.pH_recovery_on_waterchange,
                 smoothing_alpha=params_model.pH_smoothing_alpha,
                 min_limit=params_model.pH_min_limit,
                 max_limit=params_model.pH_max_limit
            )
            self.feed_config = FeedConfig(
                base_kg_per_day=params_model.Feed_base,
                spike_multiplier=params_model.feed_spike_multiplier,
                noise_min_factor=params_model.feed_noise_min_factor,
                noise_max_factor=params_model.feed_noise_max_factor,
                min_feed_kg_min=params_model.feed_min_kg_min
            )
            self.mort_config = MortalityConfig(
                weight_o2=params_model.alpha, weight_temp=params_model.beta,
                weight_density=params_model.gamma,
                o2_critical_threshold=params_model.O2_crit,
                temp_optimal_threshold=params_model.T_opt,
                density_optimal_threshold=params_model.rho_opt,
                shock_factor=params_model.shock_factor,
                o2_shock_threshold=params_model.O2_crit_for_shock,
                density_shock_threshold=params_model.density_crit_for_shock,
                kappa_scaler=params_model.kappa,
                max_mortality_rate=params_model.max_mortality_rate,
                weight_salinity=params_model.weight_salinity,
                salinity_optimal_min=params_model.salinity_optimal_min,
                salinity_optimal_max=params_model.salinity_optimal_max,
                salinity_lethal_low=params_model.salinity_lethal_low,
                salinity_lethal_high=params_model.salinity_lethal_high
            )
            self.growth_config = GrowthConfig(
                initial_weight_g=params_model.initial_weight_g,
                target_weight_g=params_model.target_weight_g,
                fcr=params_model.fcr,
                feed_table=params_model.feed_table,
                temp_min_growth=params_model.temp_min_growth,
                temp_optimal_growth=params_model.temp_optimal_growth,
                temp_max_growth=params_model.temp_max_growth
            )
            self.sanity_config = SanityConfig(
                temp_crit_for_ph=params_model.sanity_temp_crit_for_ph,
                ph_min_at_crit_temp=params_model.sanity_ph_min_at_crit_temp,
                ph_fix_noise_min=params_model.sanity_ph_fix_noise_min,
                ph_fix_noise_max=params_model.sanity_ph_fix_noise_max,
                o2_crit_for_ph=params_model.sanity_o2_crit_for_ph,
                ph_max_at_crit_o2=params_model.sanity_ph_max_at_crit_o2,
                density_crit_for_o2=params_model.sanity_density_crit_for_o2,
                o2_max_at_crit_density=params_model.sanity_o2_max_at_crit_density,
                o2_fix_noise_min=params_model.sanity_o2_fix_noise_min,
                o2_fix_noise_max=params_model.sanity_o2_fix_noise_max,
                salinity_max_with_wc=params_model.sanity_salinity_max_with_wc,
                sal_fix_noise_min=params_model.sanity_sal_fix_noise_min,
                sal_fix_noise_max=params_model.sanity_sal_fix_noise_max,
                max_mortality_ratio=params_model.sanity_max_mortality_ratio
            )
        except AttributeError as e:
             # Esto solo pasaría si PresetSchema y los Dataclasses no coinciden
             raise Exception(f"Error interno al asignar parámetros validados: {e}")

        # 4. Generar Horarios de Eventos (SRP/OCP)
        #    Ahora pasamos el modelo Pydantic a los generadores
        try:
            self.waterchange_schedule = self._generate_waterchange_schedule(params_model)
            self.o2_event_minutes = self._generate_o2_events(params_model)
            self.feed_spike_schedule = self._generate_feed_spikes(params_model)
            self.stocking_schedule = self._generate_stocking_events(params_model)
        except AttributeError as e:
             raise ValueError(f"Parámetro para generar eventos {e} falta en el config_dict.")

        # 5. Generar Pipeline de Sanidad (OCP)
        self.sanity_pipeline = self._build_sanity_pipeline()

    # --- Funciones de "Ruido" (DIP) ---
    def get_normal_noise(self, mean: float, std: float) -> float:
        return self.rng.normal(mean, std)
    
    def get_uniform_noise(self, min_val: float, max_val: float) -> float:
        return self.rng.uniform(min_val, max_val)

    def get_binomial_noise(self, n: int, p: float) -> int:
        return self.rng.binomial(n, p)

    # --- CAMBIO: Aceptar PresetSchema en lugar de dict ---
    def _generate_waterchange_schedule(self, params_model: PresetSchema) -> Set[int]:
        """Genera el set de minutos de recambio basado en la frecuencia en días."""
        wc_freq_days = params_model.waterchange_frequency_days
        if not wc_freq_days or wc_freq_days <= 0:
            print("INFO: No se programaron recambios de agua.")
            return set()
            
        intervalo_minutos = int(wc_freq_days * MINUTES_PER_DAY)
        schedule = {
            t for t in range(intervalo_minutos - 1, self.minutes, intervalo_minutos)
        }
        print(f"INFO: Recambios programados cada {wc_freq_days} días. Total {len(schedule)} recambios.")
        return schedule

    # --- Generadores de Eventos (SRP) ---
    def _generate_o2_events(self, params_model: PresetSchema) -> Set[int]:
        # (Lógica corregida: prob_per_day * days = num_eventos)
        prob_per_day = params_model.O2_event_prob_per_day
        num_events = int(self.days * prob_per_day)
        if num_events == 0:
            return set()
        event_minutes = self.rng.choice(range(self.minutes), size=num_events, replace=False)
        return set(event_minutes)

    def _generate_feed_spikes(self, params_model: PresetSchema) -> Dict[int, int]:
        prob_per_min = params_model.feed_spike_prob_per_day / MINUTES_PER_DAY
        min_dur, max_dur = params_model.feed_spike_duration_min
        schedule = {}
        for t in range(self.minutes):
            if self.rng.random() < prob_per_min:
                duration = self.rng.integers(min_dur, max_dur + 1)
                schedule[t] = duration 
        return schedule

    def _generate_stocking_events(self, params_model: PresetSchema) -> Dict[int, int]:
        prob_per_min = params_model.stocking_prob_per_day / MINUTES_PER_DAY
        min_stock = params_model.stocking_min
        max_stock = params_model.stocking_max
        schedule = {}
        for t in range(self.minutes):
            if self.rng.random() < prob_per_min:
                amount = self.rng.integers(min_stock, max_stock + 1)
                schedule[t] = amount
        return schedule
    
    def _build_sanity_pipeline(self) -> List[Callable]:
        # (OCP en acción: añade/quita reglas aquí sin tocar el bucle)
        return [
            partial(apply_sanity_temp_ph_check, config=self.sanity_config, noise=self.get_uniform_noise),
            partial(apply_sanity_o2_ph_check, config=self.sanity_config),
            partial(apply_sanity_density_o2_check, config=self.sanity_config, noise=self.get_uniform_noise),
            partial(apply_sanity_waterchange_salinity_check, config=self.sanity_config, noise=self.get_uniform_noise),
            partial(apply_sanity_mortality_check, config=self.sanity_config)
        ]

    # --- Estado Inicial (SRP) ---
    def get_initial_state(self) -> SimulationState:
        """Crea el estado inicial (t=0) de la simulación."""
        try:
            initial_N = self.initial_N
            initial_weight = self.growth_config.initial_weight_g
            initial_biomass = (initial_N * initial_weight) / 1000.0

            return SimulationState(
                timestamp=self.start_time,
                temperature=self.temp_config.base,
                salinity=self.sal_config.base,
                oxygen=self.o2_config.base,
                ph=self.ph_config.base,
                feed_spike_remaining=0,
                survivors=initial_N,
                density=calculate_density(initial_N, self.volume_L),
                current_weight_g=initial_weight,
                biomass_kg=initial_biomass
            )
        except KeyError as e:
            raise Exception(f"Error al crear estado inicial, faltó un parámetro: {e}")