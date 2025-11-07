"""
Enhanced Anomaly Detection Module
Advanced algorithms for correlation analysis, seasonality detection, and predictive analytics
"""
import logging
import os
from typing import Dict, List, Tuple, Optional
import numpy as np
import statistics
from datetime import datetime, timedelta
from dataclasses import dataclass
from scipy import stats
from scipy.signal import find_peaks

logger = logging.getLogger(__name__)

@dataclass
class AnomalyPrediction:
    """Prediction results for future anomalies"""
    metric_name: str
    predicted_value: float
    confidence: float
    timeframe_minutes: int
    severity: str
    reasoning: str

@dataclass
class CorrelationInsight:
    """Correlation analysis results"""
    metric1: str
    metric2: str
    correlation: float
    p_value: float
    insight: str
    causality_direction: Optional[str] = None

class EnhancedAnomalyDetector:
    """Advanced anomaly detection with ML capabilities"""
    
    def __init__(self):
        self.correlation_threshold = float(os.getenv("CORRELATION_THRESHOLD", "0.7"))
        self.significance_level = float(os.getenv("SIGNIFICANCE_LEVEL", "0.05"))
        
    def detect_correlated_anomalies(self, metric_values: Dict[str, List[float]]) -> List[Tuple[str, str, float, str]]:
        """
        Detect correlated anomalies across multiple metrics
        
        Args:
            metric_values: Dictionary of metric_name -> list of values
            
        Returns:
            List of (metric1, metric2, correlation, insight) tuples
        """
        correlations = []
        metric_names = list(metric_values.keys())
        
        # Only proceed if we have enough metrics and data points
        if len(metric_names) < 2:
            return correlations
            
        for i in range(len(metric_names)):
            for j in range(i + 1, len(metric_names)):
                metric1, metric2 = metric_names[i], metric_names[j]
                values1 = metric_values.get(metric1, [])
                values2 = metric_values.get(metric2, [])
                
                # Need at least 5 data points for meaningful correlation
                if len(values1) < 5 or len(values2) < 5:
                    continue
                
                # Align lengths
                min_len = min(len(values1), len(values2))
                values1 = values1[-min_len:]
                values2 = values2[-min_len:]
                
                try:
                    # Calculate Pearson correlation with p-value
                    correlation, p_value = stats.pearsonr(values1, values2)
                    
                    # Only report significant correlations
                    if abs(correlation) > self.correlation_threshold and p_value < self.significance_level:
                        insight = self._generate_correlation_insight(metric1, metric2, correlation, values1, values2)
                        correlations.append((metric1, metric2, correlation, insight))
                        
                except Exception as e:
                    logger.debug(f"Correlation calculation failed for {metric1} vs {metric2}: {e}")
                    continue
        
        return correlations
    
    def _generate_correlation_insight(self, metric1: str, metric2: str, correlation: float, 
                                    values1: List[float], values2: List[float]) -> str:
        """Generate human-readable insight for correlation"""
        
        # Determine correlation strength
        strength = "strong" if abs(correlation) > 0.8 else "moderate"
        direction = "positive" if correlation > 0 else "negative"
        
        # Analyze recent trends
        recent1 = np.mean(values1[-3:]) if len(values1) >= 3 else values1[-1]
        recent2 = np.mean(values2[-3:]) if len(values2) >= 3 else values2[-1]
        
        baseline1 = np.mean(values1[:-3]) if len(values1) > 6 else np.mean(values1)
        baseline2 = np.mean(values2[:-3]) if len(values2) > 6 else np.mean(values2)
        
        trend1 = "increasing" if recent1 > baseline1 * 1.1 else "decreasing" if recent1 < baseline1 * 0.9 else "stable"
        trend2 = "increasing" if recent2 > baseline2 * 1.1 else "decreasing" if recent2 < baseline2 * 0.9 else "stable"
        
        return f"{strength} {direction} correlation: as {metric1} is {trend1}, {metric2} is {trend2}"
    
    def advanced_anomaly_score(self, metric_name: str, values: List[float], 
                             historical_baseline: Optional[float] = None,
                             current_time: Optional[datetime] = None) -> Dict:
        """
        Calculate advanced anomaly score using multiple techniques
        
        Args:
            metric_name: Name of the metric
            values: Recent metric values
            historical_baseline: Optional baseline from historical data
            current_time: Current timestamp
            
        Returns:
            Dictionary with score, confidence, anomalies, and analysis
        """
        if not values or len(values) < 3:
            return {
                "score": 0.0,
                "confidence": 0.0,
                "anomalies": [],
                "trend": "insufficient_data",
                "seasonality": None,
                "predictions": []
            }
        
        try:
            # 1. Statistical anomaly detection (Z-score + IQR)
            z_scores = self._calculate_z_scores(values)
            iqr_outliers = self._detect_iqr_outliers(values)
            
            # 2. Trend analysis
            trend_info = self._analyze_trend(values)
            
            # 3. Seasonality detection (if enough data)
            seasonality_info = None
            if len(values) >= 12:  # Need at least 12 points for seasonality
                seasonality_info = self._detect_seasonality(values)
            
            # 4. Spike detection
            spikes = self._detect_spikes(values)
            
            # 5. Generate predictions
            predictions = self._generate_predictions(values, trend_info, seasonality_info)
            
            # 6. Calculate overall anomaly score
            anomaly_indices = set()
            
            # Add Z-score anomalies (threshold: 2.0)
            for i, z in enumerate(z_scores):
                if abs(z) > 2.0:
                    anomaly_indices.add(i)
            
            # Add IQR outliers
            anomaly_indices.update(iqr_outliers)
            
            # Add spikes
            anomaly_indices.update(spikes)
            
            # Calculate confidence based on multiple factors
            confidence = self._calculate_confidence(values, anomaly_indices, trend_info)
            
            # Overall anomaly score (0-1)
            score = len(anomaly_indices) / len(values) if values else 0.0
            
            # Adjust score based on trend severity
            if trend_info.get("change_rate", 0) > 50:  # >50% change
                score = min(1.0, score * 1.5)
            
            # Boost score if recent values are anomalous
            recent_anomalies = sum(1 for i in anomaly_indices if i >= len(values) - 3)
            if recent_anomalies >= 2:
                score = min(1.0, score * 1.3)
            
            return {
                "score": round(score, 3),
                "confidence": round(confidence, 3),
                "anomalies": list(anomaly_indices),
                "trend": trend_info.get("direction", "stable"),
                "trend_strength": trend_info.get("strength", 0.0),
                "change_rate": trend_info.get("change_rate", 0.0),
                "seasonality": seasonality_info,
                "spikes_detected": len(spikes),
                "predictions": predictions,
                "baseline_deviation": self._calculate_baseline_deviation(values, historical_baseline) if historical_baseline else None
            }
            
        except Exception as e:
            logger.error(f"Error in advanced anomaly scoring for {metric_name}: {e}")
            return {
                "score": 0.0,
                "confidence": 0.0,
                "anomalies": [],
                "trend": "error",
                "seasonality": None,
                "predictions": []
            }
    
    def _calculate_z_scores(self, values: List[float]) -> List[float]:
        """Calculate Z-scores for all values"""
        if len(values) < 2:
            return [0.0] * len(values)
        
        mean = np.mean(values)
        std = np.std(values)
        
        if std == 0:
            return [0.0] * len(values)
        
        return [(v - mean) / std for v in values]
    
    def _detect_iqr_outliers(self, values: List[float]) -> List[int]:
        """Detect outliers using Interquartile Range method"""
        if len(values) < 4:
            return []
        
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        return [i for i, v in enumerate(values) if v < lower_bound or v > upper_bound]
    
    def _analyze_trend(self, values: List[float]) -> Dict:
        """Analyze trend using linear regression"""
        if len(values) < 3:
            return {"direction": "insufficient_data", "strength": 0.0, "change_rate": 0.0}
        
        try:
            x = np.arange(len(values))
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, values)
            
            # Determine direction
            if abs(slope) < 0.01:
                direction = "stable"
            elif slope > 0:
                direction = "increasing"
            else:
                direction = "decreasing"
            
            # Calculate change rate (percentage change from first to last)
            first_val = values[0] if values[0] != 0 else 0.01  # Avoid division by zero
            change_rate = abs((values[-1] - values[0]) / first_val * 100)
            
            return {
                "direction": direction,
                "strength": abs(r_value),
                "slope": slope,
                "p_value": p_value,
                "change_rate": change_rate
            }
            
        except Exception as e:
            logger.debug(f"Trend analysis failed: {e}")
            return {"direction": "error", "strength": 0.0, "change_rate": 0.0}
    
    def _detect_seasonality(self, values: List[float]) -> Optional[Dict]:
        """Detect seasonality patterns (simplified)"""
        if len(values) < 12:
            return None
        
        try:
            # Look for patterns in different periods (5min intervals)
            periods_to_check = [12, 24, 48]  # 1hr, 2hr, 4hr patterns
            best_period = None
            best_score = 0
            
            for period in periods_to_check:
                if len(values) >= period * 2:
                    # Calculate autocorrelation for this period
                    autocorr = self._calculate_autocorrelation(values, period)
                    if autocorr > best_score:
                        best_score = autocorr
                        best_period = period
            
            if best_score > 0.3:  # Threshold for seasonality
                return {
                    "detected": True,
                    "period": best_period,
                    "strength": best_score,
                    "pattern": f"Repeats every {best_period * 5} minutes"
                }
            
            return {"detected": False, "period": None, "strength": 0.0}
            
        except Exception as e:
            logger.debug(f"Seasonality detection failed: {e}")
            return None
    
    def _calculate_autocorrelation(self, values: List[float], lag: int) -> float:
        """Calculate autocorrelation at given lag"""
        if len(values) <= lag:
            return 0.0
        
        try:
            # Split into segments
            segment1 = values[:-lag]
            segment2 = values[lag:]
            
            correlation, _ = stats.pearsonr(segment1, segment2)
            return abs(correlation) if not np.isnan(correlation) else 0.0
            
        except:
            return 0.0
    
    def _detect_spikes(self, values: List[float]) -> List[int]:
        """Detect spikes using peak detection"""
        if len(values) < 5:
            return []
        
        try:
            # Use scipy's find_peaks with adaptive threshold
            mean_val = np.mean(values)
            std_val = np.std(values)
            
            if std_val == 0:
                return []
            
            # Normalize values
            normalized = [(v - mean_val) / std_val for v in values]
            
            # Find positive spikes (height > 2 standard deviations)
            pos_peaks, _ = find_peaks(normalized, height=2.0, distance=2)
            
            # Find negative spikes (dips)
            neg_peaks, _ = find_peaks([-v for v in normalized], height=2.0, distance=2)
            
            return list(pos_peaks) + list(neg_peaks)
            
        except Exception as e:
            logger.debug(f"Spike detection failed: {e}")
            return []
    
    def _generate_predictions(self, values: List[float], trend_info: Dict, 
                           seasonality_info: Optional[Dict]) -> List[AnomalyPrediction]:
        """Generate predictions for future values"""
        predictions = []
        
        if len(values) < 3:
            return predictions
        
        try:
            current_value = values[-1]
            
            # Simple linear trend prediction
            if trend_info.get("direction") != "stable":
                slope = trend_info.get("slope", 0)
                
                # Predict next 3 time periods (15 minutes ahead)
                for i in range(1, 4):
                    predicted_value = current_value + (slope * i)
                    
                    # Determine if prediction indicates anomaly
                    deviation = abs(predicted_value - np.mean(values)) / np.std(values) if np.std(values) > 0 else 0
                    
                    if deviation > 2.0:
                        severity = "high" if deviation > 3.0 else "medium"
                        confidence = min(0.9, trend_info.get("strength", 0) + 0.3)
                        
                        reasoning = f"Trend analysis predicts {trend_info['direction']} pattern will continue"
                        
                        predictions.append(AnomalyPrediction(
                            metric_name="",  # Will be filled by caller
                            predicted_value=predicted_value,
                            confidence=confidence,
                            timeframe_minutes=i * 5,
                            severity=severity,
                            reasoning=reasoning
                        ))
                        break  # Only predict first anomaly
            
            return predictions
            
        except Exception as e:
            logger.debug(f"Prediction generation failed: {e}")
            return []
    
    def _calculate_confidence(self, values: List[float], anomaly_indices: set, trend_info: Dict) -> float:
        """Calculate confidence score for anomaly detection"""
        if not values:
            return 0.0
        
        factors = []
        
        # Factor 1: Data quantity (more data = higher confidence)
        data_factor = min(1.0, len(values) / 20.0)  # Max confidence at 20+ points
        factors.append(data_factor)
        
        # Factor 2: Trend consistency
        trend_factor = trend_info.get("strength", 0.0)
        factors.append(trend_factor)
        
        # Factor 3: Statistical significance
        if anomaly_indices:
            anomaly_ratio = len(anomaly_indices) / len(values)
            # Sweet spot: 10-30% anomalies gives highest confidence
            stat_factor = 1.0 - abs(anomaly_ratio - 0.2) * 2
            stat_factor = max(0.0, stat_factor)
            factors.append(stat_factor)
        else:
            factors.append(0.8)  # High confidence for "no anomalies"
        
        # Factor 4: Recent data weight (recent anomalies are more confident)
        recent_anomalies = sum(1 for i in anomaly_indices if i >= len(values) - 5)
        recent_factor = min(1.0, recent_anomalies * 0.3 + 0.4)
        factors.append(recent_factor)
        
        return np.mean(factors)
    
    def _calculate_baseline_deviation(self, values: List[float], baseline: float) -> Dict:
        """Calculate deviation from historical baseline"""
        if not values or baseline == 0:
            return {"deviation_percent": 0.0, "severity": "none"}
        
        current_avg = np.mean(values[-3:])  # Last 3 values
        deviation_percent = abs(current_avg - baseline) / baseline * 100
        
        if deviation_percent > 100:
            severity = "critical"
        elif deviation_percent > 50:
            severity = "high"
        elif deviation_percent > 25:
            severity = "medium"
        else:
            severity = "low"
        
        return {
            "deviation_percent": deviation_percent,
            "severity": severity,
            "baseline": baseline,
            "current_avg": current_avg
        }

def create_enhanced_detector() -> EnhancedAnomalyDetector:
    """Factory function to create enhanced anomaly detector"""
    return EnhancedAnomalyDetector()
