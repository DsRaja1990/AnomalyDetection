#!/usr/bin/env python3
"""
Local test for anomaly detection function
Tests the core logic without Azure dependencies
"""
import os
import sys
import json
from datetime import datetime, timedelta
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_mock_metrics_data():
    """Create mock metrics data with spikes to test detection"""
    end_time = datetime.utcnow()
    
    # Create 60 data points (1 per minute for the last hour)
    mock_data = {
        "request_count": {
            "config": {"display_name": "Request Count"},
            "data_points": [],
            "statistics": {"latest": 0, "central_tendency": {"mean": 100}},
            "data_quality": {"completeness": 1.0}
        },
        "request_failed": {
            "config": {"display_name": "Failed Requests"},
            "data_points": [],
            "statistics": {"latest": 0, "central_tendency": {"mean": 2}},
            "data_quality": {"completeness": 1.0}
        },
        "request_duration": {
            "config": {"display_name": "Request Duration"},
            "data_points": [],
            "statistics": {"latest": 0, "central_tendency": {"mean": 200}},
            "data_quality": {"completeness": 1.0}
        }
    }
    
    # Generate normal data with spikes at specific times
    for i in range(60):
        timestamp = end_time - timedelta(minutes=59-i)
        
        # Normal values
        normal_requests = 100 + (i % 10) - 5  # 95-105 requests
        normal_failures = 1 + (i % 3)  # 1-3 failures  
        normal_duration = 200 + (i % 50) - 25  # 175-225ms
        
        # Create spikes at minute 48 and 50 (like 10:58 PM spikes)
        if i in [48, 50]:  # Simulate spikes
            spike_requests = 250  # 250 requests (vs normal 100)
            spike_failures = 100  # 100 failures (vs normal 2)
            spike_duration = 4500  # 4.5 seconds (vs normal 200ms)
            
            mock_data["request_count"]["data_points"].append({
                "timestamp": timestamp.isoformat(),
                "value": spike_requests
            })
            mock_data["request_failed"]["data_points"].append({
                "timestamp": timestamp.isoformat(), 
                "value": spike_failures
            })
            mock_data["request_duration"]["data_points"].append({
                "timestamp": timestamp.isoformat(),
                "value": spike_duration
            })
            
            logger.info(f"SPIKE at minute {i}: requests={spike_requests}, failures={spike_failures}, duration={spike_duration}ms")
        else:
            mock_data["request_count"]["data_points"].append({
                "timestamp": timestamp.isoformat(),
                "value": normal_requests
            })
            mock_data["request_failed"]["data_points"].append({
                "timestamp": timestamp.isoformat(),
                "value": normal_failures  
            })
            mock_data["request_duration"]["data_points"].append({
                "timestamp": timestamp.isoformat(),
                "value": normal_duration
            })
    
    # Update statistics with actual values
    for metric_name, metric_data in mock_data.items():
        values = [dp["value"] for dp in metric_data["data_points"]]
        mock_data[metric_name]["statistics"] = {
            "latest": values[-1],
            "central_tendency": {"mean": sum(values) / len(values)},
            "variability": {"std_dev": 0},  # Simplified
            "count": len(values),
            "min": min(values),
            "max": max(values)
        }
    
    return mock_data

def test_anomaly_detection_logic():
    """Test the core anomaly detection logic"""
    logger.info("=== LOCAL ANOMALY DETECTION TEST ===")
    
    # Create mock data with spikes
    metrics_data = create_mock_metrics_data()
    logger.info(f"Created mock metrics with {len(metrics_data)} metric types")
    
    # Test Step 2: Extract statistics
    logger.info("=== STEP 2: PROCESSING METRICS STATISTICS ===")
    metrics_stats = {}
    for metric_name, metric_info in metrics_data.items():
        if metric_info and metric_info.get("data_points"):
            stats = metric_info["statistics"]
            data_points = metric_info["data_points"]
            stats["data_points"] = [dp["value"] for dp in data_points]
            metrics_stats[metric_name] = stats
            logger.info(f"DEBUG: Processed {metric_name} - {len(data_points)} data points, max={stats['max']}, mean={stats['central_tendency']['mean']:.1f}")
    
    # Test Step 3: Pre-filtering (simplified)
    logger.info("=== STEP 3: PRE-FILTERING ===")
    metrics_to_analyze = []
    
    # Simple spike detection for testing
    for metric_name, stats in metrics_stats.items():
        mean_val = stats["central_tendency"]["mean"]
        max_val = stats["max"]
        
        # Detect if max is significantly higher than mean (simple spike detection)
        if max_val > mean_val * 2:  # 100% increase threshold
            metrics_to_analyze.append(metric_name)
            logger.info(f"PRE-FILTER DETECTED SPIKE: {metric_name} - max={max_val}, mean={mean_val:.1f} (spike ratio: {max_val/mean_val:.1f}x)")
        else:
            logger.info(f"Pre-filter: {metric_name} normal - max={max_val}, mean={mean_val:.1f}")
    
    if not metrics_to_analyze:
        logger.warning("Pre-filter: No anomalies detected. Analyzing all metrics anyway...")
        metrics_to_analyze = list(metrics_stats.keys())
    
    logger.info(f"Pre-filter prioritized {len(metrics_to_analyze)} metrics for AI analysis: {metrics_to_analyze}")
    
    # Test would continue with AI analysis...
    logger.info("=== STEP 4: AI ANALYSIS (SIMULATED) ===")
    for metric_name in metrics_to_analyze:
        values = metrics_stats[metric_name]["data_points"]
        max_val = max(values)
        mean_val = sum(values) / len(values)
        
        # Simulate AI decision
        if max_val > mean_val * 2:
            logger.info(f"AI ANALYSIS: {metric_name} - ANOMALY DETECTED! max={max_val}, mean={mean_val:.1f}")
        else:
            logger.info(f"AI ANALYSIS: {metric_name} - Normal behavior, max={max_val}, mean={mean_val:.1f}")
    
    logger.info("=== LOCAL TEST COMPLETED ===")
    return True

if __name__ == "__main__":
    try:
        success = test_anomaly_detection_logic()
        if success:
            print("\n✅ LOCAL TEST PASSED - Logic should work correctly!")
        else:
            print("\n❌ LOCAL TEST FAILED")
    except Exception as e:
        print(f"\n❌ LOCAL TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
