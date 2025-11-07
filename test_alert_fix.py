#!/usr/bin/env python3
"""
Test the Logic App alert sending fix
"""

import logging
from shared.logic_app_client import create_logic_app_client

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_alert_sending():
    """Test the Logic App alert sending with correct parameters"""
    
    # Test data matching the actual production scenario
    test_analysis = {
        "isAnomaly": True,
        "severity": "high",
        "confidence": 0.92,
        "trend": "increasing",
        "urgency": "high",
        "rootCause": "spike_detected",
        "businessImpact": "high",
        "cascadeRisk": 0.8,
        "reasoning": "The current value of request_failed is significantly above the mean with a high Z-score, indicating an anomaly. The deviation of 96.0% from the mean suggests a severe spike.",
        "nextValue": 85.0,
        "recommendedActions": ["investigate", "scale_up", "check_dependencies"]
    }
    
    test_historical_context = {
        "analysis_type": "consolidated_multi_metric",
        "metrics_analyzed": ["request_failed"],
        "timestamp": "2025-11-07T05:58:41.382080",
        "enhanced_scores": {"request_failed": {"score": 0.960, "confidence": 0.8, "trend": "increasing"}}
    }
    
    print("🧪 TESTING LOGIC APP ALERT SENDING")
    print("=" * 50)
    
    try:
        # Create Logic App client
        logic_app_client = create_logic_app_client()
        
        if not logic_app_client:
            print("❌ Logic App client could not be created (missing LOGIC_APP_URL)")
            return
        
        print("✅ Logic App client created successfully")
        
        # Test the corrected function call
        print("📤 Sending test alert...")
        result = logic_app_client.send_alert(
            metric_name="request_failed",
            current_value=99.0,
            analysis=test_analysis,
            historical_context=test_historical_context
        )
        
        if result:
            print("✅ Test alert sent successfully!")
        else:
            print("❌ Test alert failed")
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_alert_sending()
