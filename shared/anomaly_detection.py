"""
Anomaly Detection Logic
Pre-filtering using statistical methods before AI analysis with configurable thresholds
"""
import logging
import os
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
        thresholds: Dict[str, float],
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
            # High CPU/Memory is bad
            if current_value > threshold * 1.2:
                return True, "critical"
            elif current_value > threshold:
                return True, "high"
        
        elif "failed" in metric_name.lower() or "error" in metric_name.lower():
            # Dynamic failure thresholds based on baseline
            if mean_value > 0 and std_dev > 0:
                # Use statistical approach: baseline + standard deviations (from environment)
                critical_sigma = float(os.getenv("THRESHOLD_FAILURES_SIGMA_CRITICAL", "3.0"))
                high_sigma = float(os.getenv("THRESHOLD_FAILURES_SIGMA_HIGH", "2.5"))
                medium_sigma = float(os.getenv("THRESHOLD_FAILURES_SIGMA_MEDIUM", "2.0"))
                
                critical_threshold = mean_value + (critical_sigma * std_dev)
                high_threshold = mean_value + (high_sigma * std_dev)
                medium_threshold = mean_value + (medium_sigma * std_dev)
                
                # Ensure minimum practical thresholds
                critical_multiplier = float(os.getenv("THRESHOLD_FAILURES_MULTIPLIER_CRITICAL", "2.0"))
                high_multiplier = float(os.getenv("THRESHOLD_FAILURES_MULTIPLIER_HIGH", "1.5"))
                medium_multiplier = float(os.getenv("THRESHOLD_FAILURES_MULTIPLIER_MEDIUM", "1.2"))
                
                critical_threshold = max(critical_threshold, mean_value * critical_multiplier)
                high_threshold = max(high_threshold, mean_value * high_multiplier)
                medium_threshold = max(medium_threshold, mean_value * medium_multiplier)
                
                if current_value > critical_threshold:
                    return True, "critical"
                elif current_value > high_threshold:
                    return True, "high" 
                elif current_value > medium_threshold:
                    return True, "medium"
            else:
                # Fallback to legacy static thresholds when no historical data
                if current_value > 50:  # Increased from 10
                    return True, "critical"
                elif current_value > 25:  # Increased from 5
                    return True, "high"
                elif current_value > 10:  # Changed from 0
                    return True, "medium"
        
        elif "duration" in metric_name.lower() or "latency" in metric_name.lower():
            # High latency is bad
            if current_value > threshold * 2:
                return True, "critical"
            elif current_value > threshold * 1.5:
                return True, "high"
        
        return False, "none"
    
    def should_trigger_ai_analysis(
        self,
        metric_name: str,
        stats: Dict,
        historical_values: List[float] = None
    ) -> Tuple[bool, str]:
        """
        Determine if metric warrants AI analysis
        
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
        
        # Enhanced thresholds for all metrics (from environment variables)
        thresholds = {
            # Performance Counters
            "performance_counters_processor_time": float(os.getenv("THRESHOLD_CPU_CRITICAL", "80.0")),
            "performance_counters_process_cpu": float(os.getenv("THRESHOLD_CPU_CRITICAL", "80.0")),
            "performance_counters_memory": float(os.getenv("THRESHOLD_MEMORY_CRITICAL", str(1024 * 1024 * 100))),  # 100MB available (low is bad)
            "performance_counters_private_bytes": float(os.getenv("THRESHOLD_MEMORY_CRITICAL", str(1024 * 1024 * 1024 * 2))),  # 2GB private bytes
            "performance_counters_requests_in_queue": float(os.getenv("THRESHOLD_REQUESTS_QUEUE_CRITICAL", "10.0")),
            "performance_counters_requests_per_sec": float(os.getenv("THRESHOLD_REQUESTS_PER_SEC_CRITICAL", "1000.0")),
            
            # Requests
            "requests_duration": float(os.getenv("THRESHOLD_RESPONSE_TIME_CRITICAL", "1000.0")),  # 1 second average latency
            "requests_failed": float(os.getenv("THRESHOLD_FAILURES_STATIC_CRITICAL", "0.0")),  # Any failures
            
            # Exceptions
            "exceptions_count": float(os.getenv("THRESHOLD_FAILURES_STATIC_CRITICAL", "1.0")),  # Any exception
            "exceptions_server": float(os.getenv("THRESHOLD_FAILURES_STATIC_CRITICAL", "1.0")),  # Any server exception
            "exceptions_browser": float(os.getenv("THRESHOLD_FAILURES_STATIC_MEDIUM", "5.0")),  # 5 browser exceptions
            
            # Dependencies
            "dependencies_duration": float(os.getenv("THRESHOLD_DEPENDENCY_DURATION_CRITICAL", "500.0")),  # 500ms dependency latency
            "dependencies_failed": float(os.getenv("THRESHOLD_FAILURES_STATIC_CRITICAL", "1.0")),  # Any dependency failure
            
            # Availability
            "availability_results_available": float(os.getenv("THRESHOLD_AVAILABILITY_CRITICAL", "95.0")),  # 95% availability (below is bad)
            "availability_results_duration": float(os.getenv("THRESHOLD_BROWSER_TIMING_CRITICAL", "5000.0")),  # 5 second availability test
            
            # Browser Timing
            "browser_timing_total": float(os.getenv("THRESHOLD_BROWSER_TIMING_CRITICAL", "3000.0")),  # 3 second total page load
            "browser_timing_network": float(os.getenv("THRESHOLD_RESPONSE_TIME_CRITICAL", "1000.0"))  # 1 second network time
        }
        
        # Check 1: Threshold breach with historical context
        is_breach, severity = self.check_threshold_breach(
            metric_name, 
            latest, 
            thresholds, 
            historical_stats
        )
        if is_breach:
            return True, f"Threshold breach: {severity}"
        
        # Check 2: Significant deviation from average
        deviation_threshold = float(os.getenv("THRESHOLD_DEVIATION_PERCENTAGE", "30.0")) / 100.0  # Convert percentage to decimal
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
                return True, "Increasing request queue"
        
        if trend == "decreasing":
            if "available" in metric_name.lower() and "memory" in metric_name.lower():
                return True, "Decreasing available memory"
            if "availability" in metric_name.lower():
                return True, "Decreasing availability"
        
        # Check 4: Z-score analysis if historical data available
        if historical_values and len(historical_values) > 3:
            zscore = self.calculate_zscore(historical_values)
            if zscore > self.zscore_threshold:
                return True, f"Statistical anomaly detected (z-score: {zscore:.2f})"
        
        # Check 5: Spike detection (CRITICAL for catching missed spikes)
        # ALWAYS check for spikes in failure/exception metrics
        # For other metrics, only check when data is sparse (< 15 points due to ingestion lag)
        should_check_spike = False
        if "failed" in metric_name.lower() or "exception" in metric_name.lower() or "error" in metric_name.lower():
            # ALWAYS check failure/exception metrics for spikes
            should_check_spike = True
        elif "data_points" in stats and len(stats["data_points"]) < 15:
            # Check other metrics only when sparse
            should_check_spike = True
        
        if should_check_spike and "data_points" in stats:
            is_spike, spike_reason = self.detect_spike_in_sparse_data(
                stats["data_points"], 
                metric_name
            )
            if is_spike:
                return True, f"Spike detected: {spike_reason}"
        
        return False, "No anomaly indicators"
    
    def detect_spike_in_sparse_data(
        self, 
        values: List[float],
        metric_name: str
    ) -> Tuple[bool, str]:
        """
        Detect sudden spikes even when data is sparse
        Critical for catching failures missed due to Application Insights ingestion lag
        
        For individual failure records (where each value = 1), we count TOTAL failures
        For aggregated metrics, we check MAX value
        
        Args:
            values: List of metric values (may be individual records or aggregated)
            metric_name: Name of the metric
            
        Returns:
            (is_spike, reason)
        """
        if len(values) < 2:
            return False, "Insufficient data"
        
        # Remove zeros and calculate statistics
        non_zero_values = [v for v in values if v > 0]
        max_value = max(values)
        total_count = len(values)
        sum_values = sum(values)
        
        # For failure/exception metrics: check BOTH individual records AND aggregated values
        if "failed" in metric_name.lower() or "exception" in metric_name.lower():
            # Check if these are individual failure records (all values are 1)
            if all(v == 1 for v in non_zero_values) and len(non_zero_values) > 0:
                # Individual failure records: count total failures
                total_failures = len(non_zero_values)
                if total_failures >= 50:
                    return True, f"{total_failures} individual failures detected (critical threshold: 50)"
                elif total_failures >= 20:
                    return True, f"{total_failures} individual failures detected (elevated threshold: 20)"
                elif total_failures >= 10:
                    # Check if this is significantly higher than baseline
                    # For 25-minute window, expect < 5 failures normally
                    return True, f"{total_failures} individual failures detected (warning threshold: 10)"
            else:
                # Aggregated values: check max value
                if max_value >= 50:  # 50+ failures in one aggregation
                    return True, f"{max_value} failures detected (critical threshold: 50)"
                elif max_value >= 10:  # 10+ failures
                    avg_without_max = np.mean([v for v in values if v != max_value]) if len(values) > 1 else 0
                    if avg_without_max < 2:  # Normally low failures
                        return True, f"{max_value} failures detected (baseline: ~{avg_without_max:.1f})"
        
        # For all metrics: detect if max is significantly higher than baseline
        if len(non_zero_values) > 0:
            avg_non_zero = np.mean(non_zero_values)
            if max_value > avg_non_zero * 5:  # 5x spike
                return True, f"Value spike: {max_value} ({max_value/avg_non_zero:.1f}x average)"
        else:
            # All values are zero except max
            if max_value > 10:
                return True, f"Sudden spike from 0 to {max_value}"
        
        return False, "No spike detected"
    
    def prioritize_metrics(
        self,
        metrics_analysis: Dict[str, Tuple[bool, str]]
    ) -> List[str]:
        """
        Prioritize which metrics to analyze with AI first (ENHANCED)
        
        Args:
            metrics_analysis: Dict of metric_name -> (should_analyze, reason)
            
        Returns:
            Sorted list of metric names by priority
        """
        priority_order = [
            # Priority 1: Critical failures
            "requests_failed",
            "exceptions_server",
            "dependencies_failed",
            "availability_results_available",
            
            # Priority 2: Performance degradation
            "performance_counters_processor_time",
            "performance_counters_process_cpu",
            "requests_duration",
            "dependencies_duration",
            
            # Priority 3: Resource constraints
            "performance_counters_memory",
            "performance_counters_private_bytes",
            "performance_counters_requests_in_queue",
            
            # Priority 4: Other exceptions and errors
            "exceptions_count",
            "exceptions_browser",
            
            # Priority 5: Traffic and volume
            "requests_count",
            "page_views_count",
            "performance_counters_requests_per_sec",
            
            # Priority 6: User experience
            "browser_timing_total",
            "browser_timing_network",
            "page_views_duration"
        ]
        
        # Filter metrics that need analysis
        to_analyze = [name for name, (should, _) in metrics_analysis.items() if should]
        
        # Sort by priority order
        sorted_metrics = []
        for priority_metric in priority_order:
            if priority_metric in to_analyze:
                sorted_metrics.append(priority_metric)
        
        # Add any remaining metrics
        for metric in to_analyze:
            if metric not in sorted_metrics:
                sorted_metrics.append(metric)
        
        return sorted_metrics


def create_prefilter() -> AnomalyPreFilter:
    """
    Factory function to create AnomalyPreFilter
    
    Returns:
        AnomalyPreFilter instance
    """
    import os
    threshold = float(os.getenv("PREFILTER_ZSCORE_THRESHOLD", "2.5"))
    return AnomalyPreFilter(zscore_threshold=threshold)
