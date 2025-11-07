"""
Anomaly Detection Logic
Pre-filtering using statistical methods before AI analysis with configurable thresholds
"""
import logging
from typing import Dict, List, Tuple
import statistics
import numpy as np

try:
    from .config_manager import get_config
except ImportError:
    # Fallback for standalone usage
    import sys
    import os
    sys.path.append(os.path.dirname(__file__))
    from config_manager import get_config

logger = logging.getLogger(__name__)


class AnomalyPreFilter:
    """Pre-filter anomalies using statistical methods with configurable thresholds"""
    
    def __init__(self, zscore_threshold: float = None):
        """
        Initialize pre-filter with configuration-based thresholds
        
        Args:
            zscore_threshold: Standard deviations for anomaly detection (overrides config if provided)
        """
        self.config = get_config()
        self.zscore_threshold = zscore_threshold or self.config.get('prefilter_zscore_threshold', 2.5)
        self.threshold_cache = {}  # Cache computed thresholds
        logger.info(f"AnomalyPreFilter initialized with zscore_threshold={self.zscore_threshold}")
        
        # Validate configuration
        validation = self.config.validate_configuration()
        if not validation['valid']:
            logger.error(f"Configuration validation errors: {validation['errors']}")
        if validation['warnings']:
            logger.warning(f"Configuration warnings: {validation['warnings']}")
    
    def get_dynamic_thresholds(self, metric_name: str, historical_stats: Dict = None) -> Dict[str, float]:
        """Get dynamic thresholds for a metric based on configuration"""
        cache_key = f"{metric_name}_{hash(str(historical_stats))}"
        
        if cache_key in self.threshold_cache:
            return self.threshold_cache[cache_key]
        
        if "failed" in metric_name.lower() or "error" in metric_name.lower():
            # Use dynamic failure thresholds from config
            mean = historical_stats.get("central_tendency", {}).get("mean", 0) if historical_stats else 0
            std = historical_stats.get("dispersion", {}).get("std_dev", 0) if historical_stats else 0
            
            thresholds = self.config.get_dynamic_failure_thresholds(mean, std)
            self.threshold_cache[cache_key] = thresholds
            return thresholds
        
        return {}

    def calculate_zscore(self, values: List[float]) -> float:
        """
        Calculate z-score for the latest value
        
        Args:
            values: List of metric values (latest is last)
            
        Returns:
            Z-score of the latest value
        """
        if len(values) < 3:
            return 0.0
        
        try:
            mean = statistics.mean(values)
            stdev = statistics.stdev(values)
            
            if stdev == 0:
                return 0.0
            
            latest = values[-1]
            zscore = abs((latest - mean) / stdev)
            
            return zscore
            
        except statistics.StatisticsError:
            return 0.0
    
    def check_threshold_breach(
        self,
        metric_name: str,
        current_value: float,
        thresholds: Dict[str, float] = None,
        historical_stats: Dict = None
    ) -> Tuple[bool, str]:
        """
        Check if metric breaches dynamic thresholds based on historical baseline
        
        Args:
            metric_name: Name of the metric
            current_value: Current metric value
            thresholds: Dictionary of metric -> threshold (legacy fallback)
            historical_stats: Historical statistics including mean, std_dev
            
        Returns:
            (is_breach, severity)
        """
        # Use configurable thresholds if no legacy thresholds provided
        if thresholds is None:
            thresholds = self.config.get_metric_thresholds()
        
        if metric_name not in thresholds:
            return False, "none"
        
        # Get historical context for dynamic thresholds
        if historical_stats and "central_tendency" in historical_stats:
            mean_value = historical_stats["central_tendency"].get("mean", 0)
            std_dev = historical_stats.get("dispersion", {}).get("std_dev", 0)
        else:
            mean_value = 0
            std_dev = 0
        
        threshold = thresholds[metric_name]
        
        # Different metrics have different breach conditions
        if "cpu" in metric_name.lower() or "memory" in metric_name.lower():
            # High CPU/Memory is bad - use configurable thresholds
            cpu_thresholds = self.config.get('cpu_thresholds')
            memory_thresholds = self.config.get('memory_thresholds')
            
            if "cpu" in metric_name.lower():
                if current_value > cpu_thresholds['critical']:
                    return True, "critical"
                elif current_value > cpu_thresholds['high']:
                    return True, "high"
            else:  # memory
                if current_value < memory_thresholds['critical']:  # Low available memory is bad
                    return True, "critical"
                elif current_value < memory_thresholds['high']:
                    return True, "high"
        
        elif "failed" in metric_name.lower() or "error" in metric_name.lower():
            # Dynamic failure thresholds based on configuration
            dynamic_thresholds = self.get_dynamic_thresholds(metric_name, historical_stats)
            
            if dynamic_thresholds:
                if current_value > dynamic_thresholds['critical']:
                    return True, "critical"
                elif current_value > dynamic_thresholds['high']:
                    return True, "high" 
                elif current_value > dynamic_thresholds['medium']:
                    return True, "medium"
            else:
                # Use static fallback from config
                static_thresholds = self.config.get('failure_thresholds')['static']
                if current_value > static_thresholds['critical']:
                    return True, "critical"
                elif current_value > static_thresholds['high']:
                    return True, "high"
                elif current_value > static_thresholds['medium']:
                    return True, "medium"
        
        elif "duration" in metric_name.lower() or "latency" in metric_name.lower():
            # High latency is bad - use configurable thresholds
            response_thresholds = self.config.get('response_time_thresholds')
            if current_value > response_thresholds['critical']:
                return True, "critical"
            elif current_value > response_thresholds['high']:
                return True, "high"
        
        elif "queue" in metric_name.lower():
            # High queue depth is bad
            queue_thresholds = self.config.get('requests_queue_thresholds')
            if current_value > queue_thresholds['critical']:
                return True, "critical"
            elif current_value > queue_thresholds['high']:
                return True, "high"
        
        return False, "none"
    
    def should_trigger_ai_analysis(
        self,
        metric_name: str,
        stats: Dict,
        historical_values: List[float] = None
    ) -> Tuple[bool, str]:
        """
        Determine if metric warrants AI analysis using configurable thresholds
        
        Args:
            metric_name: Name of the metric
            stats: Statistics dictionary with avg, latest, etc.
            historical_values: Optional list of historical values
            
        Returns:
            (should_analyze, reason)
        """
        latest = stats.get("latest", 0)
        avg = stats.get("avg", 0)
        trend = stats.get("trend", "stable")
        
        # Extract historical stats from the stats dictionary for dynamic thresholds
        historical_stats = stats  # The stats dict already contains the central_tendency and dispersion info
        
        # Get configurable thresholds
        thresholds = self.config.get_metric_thresholds()
        
        # Check 1: Threshold breach with historical context
        is_breach, severity = self.check_threshold_breach(
            metric_name, 
            latest, 
            thresholds, 
            historical_stats
        )
        if is_breach:
            return True, f"Threshold breach: {severity}"
        
        # Check 2: Significant deviation from average (configurable)
        deviation_threshold = self.config.get('threshold_deviation_percentage', 30.0) / 100.0
        if avg > 0 and abs(latest - avg) / avg > deviation_threshold:
            return True, f"Significant deviation: {((latest - avg) / avg * 100):.1f}%"
        
        # Check 3: Concerning trends
        if trend == "increasing":
            if "cpu" in metric_name.lower():
                return True, "Increasing CPU trend detected"
            if "failed" in metric_name.lower() or "exception" in metric_name.lower():
                return True, "Increasing failure/exception rate"
            if "duration" in metric_name.lower() or "latency" in metric_name.lower():
                return True, "Increasing latency trend"
            if "queue" in metric_name.lower():
                return True, "Increasing queue depth trend"
        
        # Check 4: Z-score based anomaly detection (configurable threshold)
        if historical_values and len(historical_values) >= 3:
            zscore = self.calculate_zscore(historical_values)
            if zscore > self.zscore_threshold:
                return True, f"Statistical anomaly detected: z-score {zscore:.2f}"
        
        return False, "No anomaly indicators"
    
    def get_configuration_summary(self) -> Dict:
        """Get a summary of current configuration for debugging"""
        return {
            'prefilter_enabled': self.config.get('enable_prefilter'),
            'dynamic_thresholds_enabled': self.config.get('dynamic_thresholds_enabled'),
            'zscore_threshold': self.zscore_threshold,
            'deviation_threshold': self.config.get('threshold_deviation_percentage'),
            'failure_thresholds': self.config.get('failure_thresholds'),
            'cpu_thresholds': self.config.get('cpu_thresholds'),
            'memory_thresholds': self.config.get('memory_thresholds'),
            'cache_size': len(self.threshold_cache)
        }
