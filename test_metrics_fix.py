"""
Test the fixed metrics aggregation locally
"""
import asyncio
import sys
import os
from pathlib import Path

# Add the shared directory to the path
sys.path.insert(0, str(Path(__file__).parent / "shared"))

from shared.metrics_query import MetricsQueryClient

async def test_metrics_aggregation():
    """Test the new aggregated KQL queries"""
    print("🔍 Testing metrics aggregation fix...")
    
    try:
        # Initialize the metrics client
        workspace_id = "458f5c9d-edd4-4e76-97bf-a7babbb84c60"
        client = MetricsQueryClient(workspace_id)
        print(f"✅ Created MetricsQueryClient for workspace: {workspace_id}")
        
        # Test the specific metrics that were problematic
        test_metrics = ['exception_count', 'request_failed']
        timespan = 60  # 60 minutes
        
        for metric_name in test_metrics:
            print(f"\n📊 Testing {metric_name}:")
            try:
                result = await client.query_metric(metric_name, timespan)
                if result and 'data_points' in result:
                    data_points = result['data_points']
                    print(f"   ✅ Retrieved {len(data_points)} data points")
                    
                    if data_points:
                        values = [dp['value'] for dp in data_points]
                        print(f"   📈 Value range: {min(values):.1f} to {max(values):.1f}")
                        print(f"   📊 Total: {sum(values):.1f}")
                        print(f"   🔥 Recent 5 values: {values[-5:]}")
                        
                        # Check if we're getting proper aggregation (not all 1.0s)
                        if all(v == 1.0 for v in values[:10]):  # Check first 10 values
                            print(f"   ❌ WARNING: Still getting individual records (all 1.0s)")
                        else:
                            print(f"   ✅ SUCCESS: Getting aggregated data!")
                    else:
                        print(f"   ⚠️  No data points returned")
                else:
                    print(f"   ❌ No result returned")
                    
            except Exception as e:
                print(f"   ❌ Error testing {metric_name}: {e}")
        
    except Exception as e:
        print(f"❌ Error setting up test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Testing metrics aggregation fix...")
    print("This will verify that the KQL queries are now properly aggregating data\n")
    
    asyncio.run(test_metrics_aggregation())
    
    print("\n✅ Test completed!")
