#!/usr/bin/env python3
"""Delete all MCP targets from AgentCore Gateway."""
import boto3
import sys

def delete_all_gateway_targets(gateway_id: str, region: str = "us-east-1"):
    """
    Scan and delete all MCP targets from the specified gateway.
    
    Args:
        gateway_id: Gateway identifier
        region: AWS region
    """
    client = boto3.client('bedrock-agent', region_name=region)
    
    print(f"🔍 Scanning gateway: {gateway_id}")
    
    try:
        # List all targets
        response = client.list_agent_action_groups(
            agentId=gateway_id,
            agentVersion='DRAFT'
        )
        
        targets = response.get('actionGroupSummaries', [])
        
        if not targets:
            print("✅ No targets found")
            return
        
        print(f"📋 Found {len(targets)} targets")
        
        # Delete each target
        for target in targets:
            target_id = target['actionGroupId']
            target_name = target.get('actionGroupName', 'Unknown')
            
            try:
                client.delete_agent_action_group(
                    agentId=gateway_id,
                    agentVersion='DRAFT',
                    actionGroupId=target_id
                )
                print(f"✅ Deleted: {target_name} ({target_id})")
            except Exception as e:
                print(f"❌ Failed to delete {target_name}: {str(e)}")
        
        print(f"\n✅ Deleted {len(targets)} targets")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 delete_gateway_targets.py <gateway_id> [region]")
        print("Example: python3 delete_gateway_targets.py restaurant-booking-gateway us-east-1")
        sys.exit(1)
    
    gateway_id = sys.argv[1]
    region = sys.argv[2] if len(sys.argv) > 2 else "us-east-1"
    
    delete_all_gateway_targets(gateway_id, region)
