#!/usr/bin/env python3
"""
Test script to validate the data structure fix for anomaly detection
This helps debug why anomaly was showing as False when spikes were detected
"""

import json
import logging
from shared.ai_foundry_client import AIFoundryClient

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_data_structure_scenarios():
    """Test different data structure scenarios that could cause AI to see 0.0 values"""
    
    # Scenario 1: Old format with data_points
    old_format_data = {
        "request_failed": {
            "data_points": [10, 15, 20, 94, 25],  # Spike at 94
            "statistics": {"latest": 94, "mean": 32.8}
        },
        "exception_count": {
            "data_points": [12, 18, 25, 98, 30],  # Spike at 98  
            "statistics": {"latest": 98, "mean": 36.6}
        }
    }
    
    # Scenario 2: New format with central_tendency (correct)
    new_format_data = {
        "request_failed": {
            "central_tendency": {
                "latest_value": 94.0,
                "mean": 32.8,
                "max": 94.0,
                "min": 10.0
            },
            "dispersion": {
                "std_dev": 35.2,
                "variance": 1239.04
            }
        },
        "exception_count": {
            "central_tendency": {
                "latest_value": 98.0,
                "mean": 36.6, 
                "max": 98.0,
                "min": 12.0
            },
            "dispersion": {
                "std_dev": 36.8,
                "variance": 1354.24
            }
        }
    }
    
    # Scenario 3: Broken format (missing latest_value)
    broken_format_data = {
        "request_failed": {
            "central_tendency": {
                "mean": 32.8,
                "max": 94.0,
                "min": 10.0
                # Missing latest_value!
            },
            "dispersion": {
                "std_dev": 35.2
            }
        },
        "exception_count": {
            "central_tendency": {
                "mean": 36.6,
                "max": 98.0, 
                "min": 12.0
                # Missing latest_value!
            },
            "dispersion": {
                "std_dev": 36.8
            }
        }
    }
    
    print("🔍 TESTING DATA STRUCTURE SCENARIOS\n")
    
    # Test each scenario
    scenarios = [
        ("Old Format (data_points)", old_format_data),
        ("New Format (central_tendency)", new_format_data), 
        ("Broken Format (missing latest_value)", broken_format_data)
    ]
    
    # Create AI client to test prompt building
    try:
        # Note: This will fail without proper credentials, but we can test prompt building
        ai_client = AIFoundryClient("dummy_endpoint", "dummy_key", "dummy_model")
        
        for scenario_name, test_data in scenarios:
            print(f"📊 {scenario_name}:")
            print("-" * 50)
            
            try:
                # Test the prompt building logic (this is where the 0.0 issue occurs)
                prompt = ai_client._build_analysis_prompt(test_data)
                
                # Extract the metric values from the prompt
                for metric_name in ["request_failed", "exception_count"]:
                    if f"METRIC: {metric_name}" in prompt:
                        # Find the Current value line
                        lines = prompt.split('\n')
                        for line in lines:
                            if f"METRIC: {metric_name}" in line:
                                # Find the next line with "Current:"
                                idx = lines.index(line)
                                for next_line in lines[idx:idx+5]:
                                    if "Current:" in next_line:
                                        print(f"   {metric_name}: {next_line.strip()}")
                                        break
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
            
            print()
    
    except Exception as e:
        print(f"Could not test AI client: {e}")
    
    print("\n🎯 ANALYSIS:")
    print("- Old format should show Current: 94.0, 98.0") 
    print("- New format should show Current: 94.0, 98.0")
    print("- Broken format would show Current: 0.0, 0.0 (THE BUG!)")
    print("\nIf we see 0.0 values, that explains why AI detects no anomaly!")

if __name__ == "__main__":
    test_data_structure_scenarios()
