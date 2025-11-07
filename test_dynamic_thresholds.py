"""
Test Dynamic Threshold Logic for Baseline Failure Scenarios
"""
import sys
import os

# Add the shared directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from anomaly_detection import AnomalyPreFilter

def test_baseline_failure_scenarios():
    """
    Test how dynamic thresholds handle scenarios where 10-20 failures are normal baseline
    """
    prefilter = AnomalyPreFilter()
    
    # Test scenarios
    test_cases = [
        {
            "name": "Normal Operations - 15 failures (baseline)",
            "current_failures": 15,
            "historical_mean": 12.5,  # Average 12-13 failures normally
            "historical_std": 2.0,    # Low variance, stable system
            "expected_alert": False,
            "scenario": "Business with naturally higher failure rate but stable"
        },
        {
            "name": "Moderate Spike - 25 failures",
            "current_failures": 25,
            "historical_mean": 12.5,  
            "historical_std": 2.0,    
            "expected_alert": True,
            "expected_severity": "medium",  # 25 > 12.5 + (2 * 2.0) = 16.5
            "scenario": "2x baseline - worth investigating"
        },
        {
            "name": "High Spike - 40 failures", 
            "current_failures": 40,
            "historical_mean": 12.5,
            "historical_std": 2.0,
            "expected_alert": True,
            "expected_severity": "high",  # 40 > 12.5 + (2.5 * 2.0) = 17.5
            "scenario": "3x baseline - serious issue"
        },
        {
            "name": "Critical Spike - 99 failures (like your example)",
            "current_failures": 99,
            "historical_mean": 12.5,
            "historical_std": 2.0,
            "expected_alert": True,
            "expected_severity": "critical",  # 99 > 12.5 + (3 * 2.0) = 18.5
            "scenario": "8x baseline - major incident"
        },
        {
            "name": "New System - No Historical Data",
            "current_failures": 25,
            "historical_mean": 0,     # No history
            "historical_std": 0,      # No variance data
            "expected_alert": True,
            "expected_severity": "high",  # Falls back to static: 25 > 10 (medium) but <= 50
            "scenario": "Uses improved static fallback thresholds"
        }
    ]
    
    print("🧪 Testing Dynamic Threshold Logic for Business Contexts\n")
    print("=" * 80)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📊 Test Case {i}: {test_case['name']}")
        print(f"   Scenario: {test_case['scenario']}")
        print(f"   Current: {test_case['current_failures']} failures")
        print(f"   Baseline: μ={test_case['historical_mean']}, σ={test_case['historical_std']}")
        
        # Create mock stats with historical context
        mock_stats = {
            "latest": test_case["current_failures"],
            "avg": test_case["historical_mean"],
            "central_tendency": {
                "mean": test_case["historical_mean"],
                "median": test_case["historical_mean"]
            },
            "dispersion": {
                "std_dev": test_case["historical_std"],
                "variance": test_case["historical_std"] ** 2
            },
            "trend": "stable"
        }
        
        # Test the logic
        should_analyze, reason = prefilter.should_trigger_ai_analysis(
            "requests_failed", 
            mock_stats
        )
        
        # Calculate expected thresholds for display
        if test_case["historical_std"] > 0:
            mean = test_case["historical_mean"]
            std = test_case["historical_std"]
            critical_thresh = max(mean + (3 * std), mean * 2.0)
            high_thresh = max(mean + (2.5 * std), mean * 1.5)
            medium_thresh = max(mean + (2 * std), mean * 1.2)
            
            print(f"   Thresholds: Medium>{medium_thresh:.1f}, High>{high_thresh:.1f}, Critical>{critical_thresh:.1f}")
        else:
            print(f"   Fallback Thresholds: Medium>10, High>25, Critical>50")
        
        # Display results
        if should_analyze:
            print(f"   🚨 ALERT: {reason}")
        else:
            print(f"   ✅ OK: {reason}")
        
        # Validate expectations
        expected = test_case.get("expected_alert", False)
        if should_analyze == expected:
            print(f"   ✅ Result matches expectation")
        else:
            print(f"   ❌ Expected: {expected}, Got: {should_analyze}")

def test_threshold_calculations():
    """
    Show the actual threshold calculations for a baseline of 15 failures
    """
    print("\n\n🔢 Detailed Threshold Calculations")
    print("=" * 50)
    
    baseline_scenarios = [
        {"mean": 15, "std": 3, "desc": "Stable system (15±3 failures)"},
        {"mean": 15, "std": 8, "desc": "Variable system (15±8 failures)"},
        {"mean": 0, "std": 0, "desc": "No historical data"}
    ]
    
    for scenario in baseline_scenarios:
        mean = scenario["mean"]
        std = scenario["std"]
        desc = scenario["desc"]
        
        print(f"\n📈 {desc}")
        
        if std > 0:
            # Statistical thresholds
            critical_stat = mean + (3 * std)
            high_stat = mean + (2.5 * std)
            medium_stat = mean + (2 * std)
            
            # Minimum practical thresholds
            critical_min = mean * 2.0
            high_min = mean * 1.5
            medium_min = mean * 1.2
            
            # Final thresholds (max of statistical and practical)
            critical_final = max(critical_stat, critical_min)
            high_final = max(high_stat, high_min)
            medium_final = max(medium_stat, medium_min)
            
            print(f"   Statistical:  Medium>{medium_stat:.1f}, High>{high_stat:.1f}, Critical>{critical_stat:.1f}")
            print(f"   Practical:    Medium>{medium_min:.1f}, High>{high_min:.1f}, Critical>{critical_min:.1f}")
            print(f"   🎯 Final:     Medium>{medium_final:.1f}, High>{high_final:.1f}, Critical>{critical_final:.1f}")
            
        else:
            print(f"   🔄 Fallback:   Medium>10, High>25, Critical>50")

if __name__ == "__main__":
    test_baseline_failure_scenarios()
    test_threshold_calculations()
