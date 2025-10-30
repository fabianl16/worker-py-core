from .common_imports import *

# --- ABSTRACCIONES DE TIPO ---
NoiseSource = Callable[[float, float], float]
UniformNoiseSource = Callable[[float, float], float]
BinomialSource = Callable[[int, float], int]
SimStateRow = Dict[str, Any]

# --- CONSTANTES GLOBALES ---
MINUTES_PER_DAY = 1440.0

# --- DEFINICIONES DE CONFIGURACIÓN ---
@dataclass(frozen=True)
class TemperatureConfig:
    """Contiene solo los parámetros necesarios para el cálculo de temperatura."""
    base: float
    amplitude: float
    sigma: float
    drift_per_day: float

@dataclass(frozen=True)
class SalinityConfig:
    """Contiene solo los parámetros necesarios para el cálculo de salinidad."""
    base: float
    drift_per_min: float
    sigma: float
    k_evap_per_deg: float
    waterchange_reduction: float

@dataclass(frozen=True)
class OxygenConfig:
    """Contiene solo los parámetros para el dominio de Oxígeno."""
    base: float
    amplitude: float
    sigma: float
    k_temp: float  
    hypoxia_min: float
    hypoxia_max: float
    floor: float

@dataclass(frozen=True)
class pHConfig:
    """Parámetros específicos para el dominio de pH."""
    base: float
    amplitude: float
    sigma: float
    phase: float
    k_feed_acid: float
    k_o2_acid: float
    o2_acid_threshold: float
    waterchange_recovery_factor: float
    smoothing_alpha: float
    min_limit: float
    max_limit: float

@dataclass(frozen=True)
class FeedConfig:
    """Parámetros específicos para el dominio de Alimentación."""
    base_kg_per_day: float
    spike_multiplier: float
    noise_min_factor: float = -0.05
    noise_max_factor: float = 0.05
    min_feed_kg_min: float = 0.0

@dataclass(frozen=True)
class MortalityConfig:
    """Parámetros específicos para el modelo de mortalidad."""
    weight_o2: float
    weight_temp: float
    weight_density: float
    o2_critical_threshold: float
    temp_optimal_threshold: float
    density_optimal_threshold: float
    shock_factor: float
    o2_shock_threshold: float
    density_shock_threshold: float
    kappa_scaler: float
    max_mortality_rate: float
    weight_salinity: float          
    salinity_optimal_min: float     
    salinity_optimal_max: float     
    salinity_lethal_low: float      
    salinity_lethal_high: float     

@dataclass(frozen=True)
class SanityConfig:
    """Parámetros para TODAS las reglas de 'sanity check'."""
    temp_crit_for_ph: float 
    ph_min_at_crit_temp: float 
    ph_fix_noise_min: float 
    ph_fix_noise_max: float 
    o2_crit_for_ph: float 
    ph_max_at_crit_o2: float
    density_crit_for_o2: float 
    o2_max_at_crit_density: float 
    o2_fix_noise_min: float 
    o2_fix_noise_max: float 
    salinity_max_with_wc: float
    sal_fix_noise_min: float 
    sal_fix_noise_max: float
    max_mortality_ratio: float 

@dataclass
class SimulationState:
    """Contiene el estado mutable de la simulación que cambia cada minuto."""
    timestamp: datetime
    temperature: float
    salinity: float
    oxygen: float
    ph: float
    feed_spike_remaining: int
    survivors: int
    density: float
    current_weight_g: float
    biomass_kg: float

@dataclass(frozen=True)
class GrowthConfig:
    """Parámetros para el modelo de crecimiento diario."""
    initial_weight_g: float
    target_weight_g: float
    fcr: float  
    temp_min_growth: float    
    feed_table: List[tuple[float, float]]
    temp_optimal_growth: float 
    temp_max_growth: float    