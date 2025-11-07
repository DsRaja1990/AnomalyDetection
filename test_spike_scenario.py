#!/usr/bin/env python3
"""
Test the data structure fix with mock data that matches the actual logs
"""

import json
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_spike_data_scenario():
    """Test with data that matches the actual production scenario"""
    
    # Mock data matching the production logs structure
    # Pre-filter detected: 94.0 failures and 98.0 exceptions
    mock_metrics_data = {
        "request_failed": {
            "data_points": [
                {"value": 20, "timestamp": "2025-11-06T20:29:00Z"},
                {"value": 25, "timestamp": "2025-11-06T20:30:00Z"}, 
                {"value": 30, "timestamp": "2025-11-06T20:31:00Z"},
                {"value": 35, "timestamp": "2025-11-06T20:32:00Z"},
                {"value": 94, "timestamp": "2025-11-06T20:33:00Z"}  # SPIKE!
            ],
            "statistics": {
                "central_tendency": {
                    "mean": 30.8,
                    "max": 94.0,
                    "min": 10.0,
                    # latest_value might be missing or wrong!
                    "latest_value": 10.0  # This is the BUG - should be 94!
                },
                "dispersion": {
                    "std_dev": 36.84
                }
            }
        },
        "exception_count": {
            "data_points": [
                {"value": 18, "timestamp": "2025-11-06T20:29:00Z"},
                {"value": 22, "timestamp": "2025-11-06T20:30:00Z"},
                {"value": 28, "timestamp": "2025-11-06T20:31:00Z"},
                {"value": 32, "timestamp": "2025-11-06T20:32:00Z"},
                {"value": 98, "timestamp": "2025-11-06T20:33:00Z"}  # SPIKE!
            ],
            "statistics": {
                "central_tendency": {
                    "mean": 31.6,
                    "max": 98.0,
                    "min": 12.0,
                    # latest_value might be missing or wrong!
                    "latest_value": 10.0  # This is the BUG - should be 98!
                },
                "dispersion": {
                    "std_dev": 38.82
                }
            }
        }
    }
    
    print("🧪 TESTING SPIKE DETECTION WITH MOCK DATA")
    print("=" * 60)
    
    # Simulate the function_app.py processing
    metrics_stats = {}
    for metric_name, metric_info in mock_metrics_data.items():
        if metric_info and metric_info.get("data_points"):
            # Preserve the complete statistics structure from metrics_query
            stats = metric_info["statistics"]
            data_points = metric_info["data_points"]
            
            # Add raw data points for backward compatibility
            stats["data_points"] = [dp["value"] for dp in data_points]
            
            # Ensure latest_value is correctly set in central_tendency if missing
            if "central_tendency" in stats:
                ct = stats["central_tendency"]
                original_latest = ct.get("latest_value", 0)
                if "latest_value" not in ct or ct.get("latest_value", 0) == 0:
                    # Use the last data point as latest_value if missing
                    if data_points:
                        latest_value = data_points[-1]["value"]
                        ct["latest_value"] = latest_value
                        print(f"🔧 Fixed latest_value for {metric_name}: {original_latest} → {latest_value}")
                else:
                    # Check if latest_value is wrong
                    if data_points:
                        actual_latest = data_points[-1]["value"]
                        if ct["latest_value"] != actual_latest:
                            print(f"⚠️  latest_value mismatch for {metric_name}: stored={ct['latest_value']}, actual={actual_latest}")
                            ct["latest_value"] = actual_latest
                            print(f"🔧 Fixed latest_value for {metric_name}: {original_latest} → {actual_latest}")
            
            metrics_stats[metric_name] = stats
    
    print("\n📊 KEY METRICS SUMMARY (after fix):")
    for metric_name in ['request_failed', 'exception_count']:
        if metric_name in metrics_stats:
            stats = metrics_stats[metric_name]
            values = stats.get("data_points", [])
            if values:
                total = sum(values)
                max_val = max(values)
                avg_val = sum(values) / len(values)
                latest_val = values[-1] if values else 0
                print(f"   {metric_name}: total={total:.0f}, max={max_val:.0f}, avg={avg_val:.1f}, latest={latest_val:.1f}")
                
                # Also show central_tendency data for comparison
                if "central_tendency" in stats:
                    ct = stats["central_tendency"]
                    ct_latest = ct.get("latest_value", 0)
                    ct_mean = ct.get("mean", 0)
                    print(f"     central_tendency: latest_value={ct_latest:.1f}, mean={ct_mean:.1f}")
    
    print("\n🎯 EXPECTED RESULTS:")
    print("✅ Pre-filter should detect spikes: 94 and 98")
    print("✅ AI should receive current values: 94.0 and 98.0 (not 10.0)")
    print("✅ AI should return isAnomaly=True with high confidence")

if __name__ == "__main__":
    test_spike_data_scenario()
