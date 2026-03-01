#!/usr/bin/env python3
"""Scan and delete all MCP targets from AgentCore Gateway."""
import boto3
import sys

def list_and_delete_gateway_targets(gateway_name: str = None, gateway_id: str = None, region: str = "us-east-1"):
    """
    Scan and delete all MCP targets from the specified gateway.
    
    Args:
        gateway_name: Gateway name (e.g., 'restaurant-booking-gateway')
        gateway_id: Gateway ID (if known)
        region: AWS region
    """
    client = boto3.client('bedrock-agent', region_name='us-east-1')
    
    # Find gateway by name if ID not provided
    if not gateway_id and gateway_name:
        print(f"🔍 Searching for gateway: {gateway_name}")
        try:
            response = client.list_agents(maxResults=50)
            for agent in response.get('agentSummaries', []):
                if agent['agentName'] == gateway_name:
                    gateway_id = agent['agentId']
                    print(f"✅ Found gateway: {gateway_id}")
                    break
        except Exception as e:
            print(f"❌ Error searching for gateway: {e}")
            return
    
    if not gateway_id:
        print("❌ Gateway not found")
        return
    
    print(f"\n🔍 Scanning gateway targets: {gateway_id}")
    
    try:
        # List all action groups (targets)
        response = client.list_agent_action_groups(
            agentId=gateway_id,
            agentVersion='DRAFT',
            maxResults=100
        )
        
        targets = response.get('actionGroupSummaries', [])
        
        if not targets:
            print("✅ No targets found")
            return
        
        print(f"\n📋 Found {len(targets)} MCP targets:")
        for target in targets:
            print(f"  - {target.get('actionGroupName', 'Unknown')} ({target['actionGroupId']})")
        
        # Ask for confirmation
        confirm = input(f"\n⚠️  Delete all {len(targets)} targets? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Cancelled")
            return
        
        # Delete each target
        print("\n🗑️  Deleting targets...")
        deleted = 0
        for target in targets:
            target_id = target['actionGroupId']
            target_name = target.get('actionGroupName', 'Unknown')
            
            try:
                client.delete_agent_action_group(
                    agentId=gateway_id,
                    agentVersion='DRAFT',
                    actionGroupId=target_id
                )
                print(f"✅ Deleted: {target_name}")
                deleted += 1
            except Exception as e:
                print(f"❌ Failed to delete {target_name}: {str(e)}")
        
        print(f"\n✅ Successfully deleted {deleted}/{len(targets)} targets")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  By name: python3 scan_delete_gateway_targets.py restaurant-booking-gateway")
        print("  By ID:   python3 scan_delete_gateway_targets.py --id <gateway_id>")
        sys.exit(1)
    
    if sys.argv[1] == '--id':
        gateway_id = sys.argv[2] if len(sys.argv) > 2 else None
        list_and_delete_gateway_targets(gateway_id=gateway_id)
    else:
        gateway_name = sys.argv[1]
        list_and_delete_gateway_targets(gateway_name=gateway_name)
