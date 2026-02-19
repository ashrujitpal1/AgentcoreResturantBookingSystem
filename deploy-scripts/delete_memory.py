"""Delete and recreate AgentCore Memory with 1-day retention."""

import boto3
import sys

def delete_memory(memory_id: str, region: str = "us-east-1"):
    """Delete existing memory."""
    client = boto3.client('bedrock-agentcore-control', region_name=region)
    
    try:
        print(f"Deleting memory: {memory_id}...")
        client.delete_memory(memoryId=memory_id)
        print(f"✅ Memory {memory_id} deleted successfully")
        return True
    except Exception as e:
        print(f"❌ Error deleting memory: {str(e)}")
        return False

if __name__ == "__main__":
    memory_id = "RestaurantBookingMemory-UQuCVa50r3"
    region = sys.argv[1] if len(sys.argv) > 1 else "us-east-1"
    
    if delete_memory(memory_id, region):
        print("\nNow run: python3 deploy_agentcore_memory.py")
    else:
        sys.exit(1)
