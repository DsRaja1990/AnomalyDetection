"""
Quick script to check if the deployed function is executing with the new code
"""
import os
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_recent_logs():
    """Check for recent function executions in Application Insights"""
    try:
        from azure.monitor.query import LogsQueryClient
        from azure.identity import DefaultAzureCredential
        
        # Initialize client
        credential = DefaultAzureCredential()
        workspace_id = "458f5c9d-edd4-4e76-97bf-a7babbb84c60"
        client = LogsQueryClient(credential)
        
        # Query for recent function logs (last 30 minutes)
        query = """
        traces
        | where cloud_RoleName == 'anamolypoc'
        | where timestamp > ago(30m)
        | where message contains 'ANOMALY DETECTION' or message contains 'STEP'
        | order by timestamp desc
        | limit 50
        | project timestamp, message
        """
        
        logger.info("🔍 Checking for recent function executions...")
        
        response = client.query_workspace(
            workspace_id=workspace_id,
            query=query,
            timespan=timedelta(minutes=30)
        )
        
        if response.tables and len(response.tables) > 0:
            rows = response.tables[0].rows
            logger.info(f"✅ Found {len(rows)} recent log entries")
            
            for row in rows:
                timestamp = row[0]
                message = row[1]
                logger.info(f"📝 {timestamp}: {message}")
        else:
            logger.warning("⚠️ No recent function logs found")
            
    except Exception as e:
        logger.error(f"❌ Error checking logs: {e}")

def check_deployment_status():
    """Verify the deployment files are as expected"""
    logger.info("🔍 VERIFYING DEPLOYMENT STATUS")
    logger.info("="*50)
    
    # Check main files exist
    files_to_check = [
        "function_app.py",
        "shared/metrics_query.py",
        "shared/ai_foundry_client.py",
        "shared/state_manager.py",
        "requirements.txt"
    ]
    
    for file_path in files_to_check:
        full_path = os.path.join(os.getcwd(), file_path)
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            mtime = datetime.fromtimestamp(os.path.getmtime(full_path))
            logger.info(f"✅ {file_path}: {size} bytes, modified {mtime}")
        else:
            logger.error(f"❌ {file_path}: NOT FOUND")
    
    # Check key markers in function_app.py
    with open("function_app.py", "r") as f:
        content = f.read()
        
    markers_to_check = [
        "=== ANOMALY DETECTION ENHANCED VERSION STARTING ===",
        "=== STEP 1: QUERYING METRICS ===", 
        "=== STEP 2: PROCESSING METRICS STATISTICS ===",
        "query_all_metrics",
        "FORCING 60-minute lookback"
    ]
    
    logger.info("\n📋 Checking for key code markers:")
    for marker in markers_to_check:
        if marker in content:
            logger.info(f"✅ Found: {marker}")
        else:
            logger.error(f"❌ Missing: {marker}")

def main():
    logger.info("🚀 DEPLOYMENT VERIFICATION STARTING")
    logger.info("Current time: " + datetime.now().isoformat())
    
    check_deployment_status()
    check_recent_logs()
    
    logger.info("🏁 Verification complete!")

if __name__ == "__main__":
    main()
