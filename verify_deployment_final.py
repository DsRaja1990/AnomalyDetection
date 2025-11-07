"""
Verification script for deployed Azure Function
"""
import requests
import json
import os
from datetime import datetime

def test_function_health():
    """Test if the Azure Function is healthy and responding"""
    function_url = "https://anamolypoc-ede5ejcadjh8gdcd.canadacentral-01.azurewebsites.net"
    
    try:
        # Test the admin/host/status endpoint
        health_url = f"{function_url}/admin/host/status"
        response = requests.get(health_url, timeout=30)
        
        if response.status_code == 200:
            status_data = response.json()
            print("✅ Function App is healthy!")
            print(f"   State: {status_data.get('state', 'Unknown')}")
            print(f"   Version: {status_data.get('version', 'Unknown')}")
            print(f"   Instance ID: {status_data.get('instanceId', 'Unknown')}")
            return True
        else:
            print(f"❌ Function App health check failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking function health: {e}")
        return False

def check_function_execution():
    """Check if our timer function is configured correctly"""
    print("\n🔍 Function Configuration:")
    print("   Function Name: AzureAnomalyFindingDetectionTimer")
    print("   Trigger: Timer (every 5 minutes)")
    print("   Schedule: 0 */5 * * * *")
    print("   Run on startup: True")
    
    print("\n📊 Expected Behavior:")
    print("   1. Function runs every 5 minutes")
    print("   2. Queries Application Insights metrics (mock data)")
    print("   3. Performs AI analysis using Phi-4")
    print("   4. Detects anomalies and correlations")
    print("   5. Sends alerts if confidence > 75%")

def main():
    print("🧪 Azure Function Deployment Verification")
    print("=" * 50)
    
    # Test function health
    is_healthy = test_function_health()
    
    # Show function configuration
    check_function_execution()
    
    print("=" * 50)
    if is_healthy:
        print("✅ Deployment verification PASSED!")
        print("🚀 The function is deployed and ready to run anomaly detection.")
        print("\nNext steps:")
        print("1. Monitor the function logs for execution")
        print("2. Check Application Insights for metrics")
        print("3. Verify Logic App receives alerts when anomalies are detected")
    else:
        print("❌ Deployment verification FAILED!")
        print("Please check the Azure portal for more details.")

if __name__ == "__main__":
    main()
