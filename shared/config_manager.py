"""
Configuration Manager for Anomaly Detection System
Handles environment-based threshold configuration
"""
import os
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """Manages configuration from environment variables with sensible defaults"""
    
    def __init__(self):
        self.config = self._load_configuration()
        logger.info(f"Configuration loaded with {len(self.config)} settings")
    
    def _load_configuration(self) -> Dict[str, Any]:
        """Load configuration from environment variables with defaults"""
        return {
            # Core Settings
            'anomaly_confidence_threshold': float(os.getenv('ANOMALY_CONFIDENCE_THRESHOLD', '0.85')),
            'metrics_lookback_minutes': int(os.getenv('METRICS_LOOKBACK_MINUTES', '25')),
            'timer_interval_minutes': int(os.getenv('TIMER_INTERVAL_MINUTES', '5')),
            'enable_prefilter': os.getenv('ENABLE_PREFILTER', 'true').lower() == 'true',
            'prefilter_zscore_threshold': float(os.getenv('PREFILTER_ZSCORE_THRESHOLD', '2.5')),
            'moving_avg_window': int(os.getenv('MOVING_AVG_WINDOW', '5')),
            'rate_change_threshold': float(os.getenv('RATE_CHANGE_THRESHOLD', '0.5')),
            'threshold_deviation_percentage': float(os.getenv('THRESHOLD_DEVIATION_PERCENTAGE', '30.0')),
            'dynamic_thresholds_enabled': os.getenv('DYNAMIC_THRESHOLDS_ENABLED', 'true').lower() == 'true',
            
            # Performance Counter Thresholds
            'cpu_thresholds': {
                'critical': float(os.getenv('THRESHOLD_CPU_CRITICAL', '90.0')),
                'high': float(os.getenv('THRESHOLD_CPU_HIGH', '80.0'))
            },
            'memory_thresholds': {
                'critical': float(os.getenv('THRESHOLD_MEMORY_CRITICAL', '104857600')),  # 100MB
                'high': float(os.getenv('THRESHOLD_MEMORY_HIGH', '52428800'))  # 50MB
            },
            'requests_queue_thresholds': {
                'critical': float(os.getenv('THRESHOLD_REQUESTS_QUEUE_CRITICAL', '20.0')),
                'high': float(os.getenv('THRESHOLD_REQUESTS_QUEUE_HIGH', '10.0'))
            },
            'requests_per_sec_thresholds': {
                'critical': float(os.getenv('THRESHOLD_REQUESTS_PER_SEC_CRITICAL', '2000.0')),
                'high': float(os.getenv('THRESHOLD_REQUESTS_PER_SEC_HIGH', '1000.0'))
            },
            'response_time_thresholds': {
                'critical': float(os.getenv('THRESHOLD_RESPONSE_TIME_CRITICAL', '5000.0')),
                'high': float(os.getenv('THRESHOLD_RESPONSE_TIME_HIGH', '3000.0'))
            },
            'dependency_duration_thresholds': {
                'critical': float(os.getenv('THRESHOLD_DEPENDENCY_DURATION_CRITICAL', '1000.0')),
                'high': float(os.getenv('THRESHOLD_DEPENDENCY_DURATION_HIGH', '500.0'))
            },
            'availability_thresholds': {
                'critical': float(os.getenv('THRESHOLD_AVAILABILITY_CRITICAL', '90.0')),
                'high': float(os.getenv('THRESHOLD_AVAILABILITY_HIGH', '95.0'))
            },
            'browser_timing_thresholds': {
                'critical': float(os.getenv('THRESHOLD_BROWSER_TIMING_CRITICAL', '5000.0')),
                'high': float(os.getenv('THRESHOLD_BROWSER_TIMING_HIGH', '3000.0'))
            },
            
            # Dynamic Failure Thresholds
            'failure_thresholds': {
                'static': {
                    'critical': int(os.getenv('THRESHOLD_FAILURES_STATIC_CRITICAL', '50')),
                    'high': int(os.getenv('THRESHOLD_FAILURES_STATIC_HIGH', '25')),
                    'medium': int(os.getenv('THRESHOLD_FAILURES_STATIC_MEDIUM', '10'))
                },
                'sigma': {
                    'critical': float(os.getenv('THRESHOLD_FAILURES_SIGMA_CRITICAL', '3.0')),
                    'high': float(os.getenv('THRESHOLD_FAILURES_SIGMA_HIGH', '2.5')),
                    'medium': float(os.getenv('THRESHOLD_FAILURES_SIGMA_MEDIUM', '2.0'))
                },
                'multiplier': {
                    'critical': float(os.getenv('THRESHOLD_FAILURES_MULTIPLIER_CRITICAL', '2.0')),
                    'high': float(os.getenv('THRESHOLD_FAILURES_MULTIPLIER_HIGH', '1.5')),
                    'medium': float(os.getenv('THRESHOLD_FAILURES_MULTIPLIER_MEDIUM', '1.2'))
                }
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key"""
        return self.config.get(key, default)
    
    def get_metric_thresholds(self) -> Dict[str, float]:
        """Get legacy threshold dictionary for backward compatibility"""
        config = self.config
        return {
            # Performance Counters
            "performance_counters_processor_time": config['cpu_thresholds']['high'],
            "performance_counters_process_cpu": config['cpu_thresholds']['high'],
            "performance_counters_memory": config['memory_thresholds']['high'],
            "performance_counters_private_bytes": config['memory_thresholds']['critical'] * 20,  # 2GB
            "performance_counters_requests_in_queue": config['requests_queue_thresholds']['high'],
            "performance_counters_requests_per_sec": config['requests_per_sec_thresholds']['high'],
            
            # Requests
            "requests_duration": config['response_time_thresholds']['high'],
            "requests_count": config['requests_per_sec_thresholds']['high'],
            "requests_failed": 0,  # Will use dynamic logic
            
            # Dependencies
            "dependencies_duration": config['dependency_duration_thresholds']['high'],
            "dependencies_failed": 1.0,  # Any dependency failure
            
            # Availability
            "availability_results_available": config['availability_thresholds']['high'],
            "availability_results_duration": config['response_time_thresholds']['critical'],
            
            # Browser Timing
            "browser_timing_total": config['browser_timing_thresholds']['high'],
            "browser_timing_network": config['browser_timing_thresholds']['high'] / 3
        }
    
    def get_dynamic_failure_thresholds(self, historical_mean: float = 0, historical_std: float = 0) -> Dict[str, float]:
        """Calculate dynamic failure thresholds based on historical data"""
        failure_config = self.config['failure_thresholds']
        
        if not self.config['dynamic_thresholds_enabled'] or historical_std <= 0:
            # Use static fallback thresholds
            return {
                'critical': float(failure_config['static']['critical']),
                'high': float(failure_config['static']['high']),
                'medium': float(failure_config['static']['medium'])
            }
        
        # Calculate statistical thresholds
        sigma_config = failure_config['sigma']
        multiplier_config = failure_config['multiplier']
        
        statistical_thresholds = {
            'critical': historical_mean + (sigma_config['critical'] * historical_std),
            'high': historical_mean + (sigma_config['high'] * historical_std),
            'medium': historical_mean + (sigma_config['medium'] * historical_std)
        }
        
        # Calculate minimum practical thresholds
        practical_thresholds = {
            'critical': historical_mean * multiplier_config['critical'],
            'high': historical_mean * multiplier_config['high'],
            'medium': historical_mean * multiplier_config['medium']
        }
        
        # Use the higher of statistical or practical thresholds
        return {
            'critical': max(statistical_thresholds['critical'], practical_thresholds['critical']),
            'high': max(statistical_thresholds['high'], practical_thresholds['high']),
            'medium': max(statistical_thresholds['medium'], practical_thresholds['medium'])
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """Validate configuration and return validation results"""
        validation = {
            'valid': True,
            'warnings': [],
            'errors': []
        }
        
        # Check critical values
        if self.config['anomaly_confidence_threshold'] < 0.5 or self.config['anomaly_confidence_threshold'] > 1.0:
            validation['warnings'].append("Anomaly confidence threshold should be between 0.5 and 1.0")
        
        if self.config['metrics_lookback_minutes'] < 5:
            validation['warnings'].append("Metrics lookback period less than 5 minutes may not provide enough data")
        
        if not self.config['enable_prefilter']:
            validation['warnings'].append("Pre-filter is disabled - this may increase costs significantly")
        
        # Check threshold sanity
        for metric_type, thresholds in [
            ('cpu_thresholds', self.config['cpu_thresholds']),
            ('memory_thresholds', self.config['memory_thresholds'])
        ]:
            if thresholds['critical'] <= thresholds['high']:
                validation['errors'].append(f"{metric_type}: Critical threshold must be higher than high threshold")
                validation['valid'] = False
        
        return validation

# Global configuration instance
config_manager = ConfigManager()

def get_config() -> ConfigManager:
    """Get the global configuration manager instance"""
    return config_manager
