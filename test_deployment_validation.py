"""
Test script to validate deployment and debug the anomaly detection issues
This script tests the same logic that runs in Azure Functions
"""
import os
import logging
from datetime import datetime, timedelta
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_metrics_service():
    """Test if metrics service can be created and works"""
    try:
        from shared.metrics_query import create_metrics_service
        
        logger.info("=== TESTING METRICS SERVICE ===")
        metrics_service = create_metrics_service()
        
        if not metrics_service:
            logger.error("❌ Failed to create metrics service")
            return False
            
        logger.info("✅ Metrics service created successfully")
        logger.info(f"✅ Service type: {type(metrics_service).__name__}")
        logger.info(f"✅ Available methods: {[m for m in dir(metrics_service) if not m.startswith('_')]}")
        
        # Test workspace connection
        workspace_id = os.getenv("APPINSIGHTS_WORKSPACE_ID", "458f5c9d-edd4-4e76-97bf-a7babbb84c60")
        logger.info(f"✅ Workspace ID: {workspace_id}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error testing metrics service: {e}", exc_info=True)
        return False

def test_metrics_query():
    """Test actual metrics query with small timespan"""
    try:
        from shared.metrics_query import create_metrics_service
        
        logger.info("=== TESTING METRICS QUERY ===")
        metrics_service = create_metrics_service()
        
        if not metrics_service:
            logger.error("❌ Metrics service not available")
            return False
        
        # Test with 10 minute timespan first
        logger.info("Testing query with 10-minute timespan...")
        metrics_data = metrics_service.query_all_metrics(timespan_minutes=10)
        
        if not metrics_data:
            logger.warning("⚠️ No metrics data returned for 10 minutes")
            return False
            
        logger.info(f"✅ Query successful! Got {len(metrics_data)} metrics")
        for metric_name, data in metrics_data.items():
            data_points = data.get('data_points', [])
            logger.info(f"✅ {metric_name}: {len(data_points)} data points")
            
            if data_points:
                latest = max(data_points, key=lambda x: x['timestamp'])
                logger.info(f"   Latest: {latest['timestamp']} = {latest['value']}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing metrics query: {e}", exc_info=True)
        return False

def test_60_minute_query():
    """Test 60-minute query like production"""
    try:
        from shared.metrics_query import create_metrics_service
        
        logger.info("=== TESTING 60-MINUTE QUERY (PRODUCTION SCENARIO) ===")
        metrics_service = create_metrics_service()
        
        if not metrics_service:
            logger.error("❌ Metrics service not available")
            return False
        
        # Test with 60 minute timespan - same as production
        logger.info("Testing query with 60-minute timespan (production setting)...")
        start_time = datetime.now()
        
        metrics_data = metrics_service.query_all_metrics(timespan_minutes=60)
        
        query_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Query completed in {query_time:.1f} seconds")
        
        if not metrics_data:
            logger.warning("⚠️ No metrics data returned for 60 minutes")
            return False
            
        logger.info(f"✅ Query successful! Got {len(metrics_data)} metrics")
        
        # Check for spikes like we expect
        for metric_name, data in metrics_data.items():
            data_points = data.get('data_points', [])
            logger.info(f"✅ {metric_name}: {len(data_points)} data points")
            
            if data_points:
                values = [dp['value'] for dp in data_points]
                max_val = max(values)
                min_val = min(values)
                avg_val = sum(values) / len(values)
                
                logger.info(f"   Range: {min_val:.2f} - {max_val:.2f}, Avg: {avg_val:.2f}")
                
                # Check for spikes (value > 3x average)
                spike_threshold = avg_val * 3
                spikes = [dp for dp in data_points if dp['value'] > spike_threshold]
                
                if spikes:
                    logger.info(f"🚨 Found {len(spikes)} potential spikes in {metric_name}!")
                    for spike in spikes[:3]:  # Show first 3 spikes
                        logger.info(f"   Spike: {spike['timestamp']} = {spike['value']:.2f} (>{spike_threshold:.2f})")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing 60-minute query: {e}", exc_info=True)
        return False

def main():
    """Run all tests"""
    logger.info("🔬 DEPLOYMENT VALIDATION TEST STARTING")
    logger.info("="*50)
    
    # Test environment variables
    logger.info("=== ENVIRONMENT VARIABLES ===")
    required_vars = [
        "APPINSIGHTS_WORKSPACE_ID",
        "AI_FOUNDATION_ENDPOINT", 
        "AI_FOUNDATION_KEY"
    ]
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            logger.info(f"✅ {var}: {'*' * 20}...{value[-10:]}")
        else:
            logger.error(f"❌ {var}: NOT SET")
    
    # Run tests
    tests = [
        ("Metrics Service Creation", test_metrics_service),
        ("Basic Metrics Query", test_metrics_query),
        ("60-Minute Production Query", test_60_minute_query),
    ]
    
    passed = 0
    for test_name, test_func in tests:
        logger.info(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                logger.info(f"✅ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"💥 {test_name} CRASHED: {e}")
    
    logger.info(f"\n🏁 TEST SUMMARY: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        logger.info("🎉 All tests passed! Deployment should work correctly.")
    else:
        logger.error("⚠️ Some tests failed. Check the logs above for issues.")

if __name__ == "__main__":
    main()
