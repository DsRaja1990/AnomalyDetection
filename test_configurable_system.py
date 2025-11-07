"""
Test Configurable Anomaly Detection System
"""
import sys
import os

# Add the shared directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'shared'))

from anomaly_detection_configurable import AnomalyPreFilter
from config_manager import get_config

def test_configuration_system():
    """Test the configuration system"""
    print("🧪 Testing Configurable Anomaly Detection System\n")
    print("=" * 80)
    
    # Initialize with configuration
    prefilter = AnomalyPreFilter()
    config = get_config()
    
    print("📋 Configuration Summary:")
    print("-" * 40)
    summary = prefilter.get_configuration_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")
    
    print("\n🎯 Dynamic Threshold Examples:")
    print("-" * 40)
    
    # Test different baseline scenarios
    scenarios = [
        {
            "name": "High Baseline System (15±3 failures)",
            "mean": 15,
            "std": 3,
            "test_values": [10, 15, 20, 25, 35, 50]
        },
        {
            "name": "Low Baseline System (2±1 failures)", 
            "mean": 2,
            "std": 1,
            "test_values": [1, 2, 5, 8, 12, 20]
        },
        {
            "name": "No Historical Data",
            "mean": 0,
            "std": 0,
            "test_values": [5, 10, 15, 25, 35, 50]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📊 {scenario['name']}")
        
        # Create mock historical stats
        historical_stats = {
            "central_tendency": {"mean": scenario["mean"]},
            "dispersion": {"std_dev": scenario["std"]}
        } if scenario["std"] > 0 else None
        
        # Get thresholds for this scenario
        thresholds = prefilter.get_dynamic_thresholds("requests_failed", historical_stats)
        
        if thresholds:
            print(f"   Thresholds: Medium>{thresholds['medium']:.1f}, High>{thresholds['high']:.1f}, Critical>{thresholds['critical']:.1f}")
        else:
            static = config.get('failure_thresholds')['static']
            print(f"   Static Fallback: Medium>{static['medium']}, High>{static['high']}, Critical>{static['critical']}")
        
        # Test values against thresholds
        for test_value in scenario["test_values"]:
            mock_stats = {
                "latest": test_value,
                "avg": scenario["mean"],
                "central_tendency": {"mean": scenario["mean"]},
                "dispersion": {"std_dev": scenario["std"]},
                "trend": "stable"
            }
            
            should_analyze, reason = prefilter.should_trigger_ai_analysis("requests_failed", mock_stats)
            
            status = "🚨" if should_analyze else "✅"
            print(f"   {status} {test_value} failures: {reason}")

def test_environment_customization():
    """Show how users can customize thresholds via environment"""
    print(f"\n\n🔧 Environment Customization Examples")
    print("=" * 50)
    
    print("""
To customize thresholds, users can set these environment variables:

# Core Settings
ANOMALY_CONFIDENCE_THRESHOLD=0.75         # AI confidence threshold
DYNAMIC_THRESHOLDS_ENABLED=true           # Enable smart thresholds
THRESHOLD_DEVIATION_PERCENTAGE=25.0       # Deviation alert threshold

# CPU/Memory Thresholds  
THRESHOLD_CPU_CRITICAL=95.0               # 95% CPU critical
THRESHOLD_CPU_HIGH=85.0                   # 85% CPU high
THRESHOLD_MEMORY_CRITICAL=50000000        # 50MB available critical

# Failure Thresholds (for systems with high baseline)
THRESHOLD_FAILURES_STATIC_CRITICAL=100    # Static: 100 failures = critical
THRESHOLD_FAILURES_STATIC_HIGH=50         # Static: 50 failures = high  
THRESHOLD_FAILURES_STATIC_MEDIUM=20       # Static: 20 failures = medium

# Dynamic Failure Logic (statistical approach)
THRESHOLD_FAILURES_SIGMA_CRITICAL=4.0     # 4 standard deviations
THRESHOLD_FAILURES_MULTIPLIER_CRITICAL=3.0 # 300% of baseline

# Response Time Thresholds
THRESHOLD_RESPONSE_TIME_CRITICAL=10000.0  # 10 second critical
THRESHOLD_RESPONSE_TIME_HIGH=5000.0       # 5 second high

This allows each customer to adapt to their specific business context!
""")

def test_validation():
    """Test configuration validation"""
    print(f"\n🔍 Configuration Validation")
    print("=" * 30)
    
    config = get_config()
    validation = config.validate_configuration()
    
    print(f"Valid: {validation['valid']}")
    
    if validation['errors']:
        print("Errors:")
        for error in validation['errors']:
            print(f"  ❌ {error}")
    
    if validation['warnings']:
        print("Warnings:")
        for warning in validation['warnings']:
            print(f"  ⚠️  {warning}")
    
    if validation['valid'] and not validation['errors']:
        print("✅ Configuration is valid!")

if __name__ == "__main__":
    test_configuration_system()
    test_environment_customization() 
    test_validation()
