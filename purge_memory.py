"""
Purge AgentCore Memory - Delete events for testing/cleanup
"""
import os
import boto3
from dotenv import load_dotenv

load_dotenv()

def purge_memory(user_id: str = None, session_id: str = None, purge_all: bool = False):
    """
    Delete events from AgentCore Memory
    
    Args:
        user_id: Delete all events for this user (actorId)
        session_id: Delete all events for this session
        purge_all: Delete all events (requires listing all actors first)
    """
    memory_id = os.getenv('MEMORY_ID')
    if not memory_id:
        print("❌ MEMORY_ID not found in .env")
        return
    
    client = boto3.client('bedrock-agentcore')
    
    try:
        if purge_all:
            # For purge_all, we need to delete the entire memory
            print("⚠️  Deleting entire memory (all sessions, all users)...")
            try:
                client.delete_memory(memoryId=memory_id)
                print("✅ Memory deleted successfully")
                print("\n⚠️  You'll need to recreate the memory:")
                print("   python deploy_agentcore_memory.py")
                return
            except Exception as e:
                print(f"❌ Failed to delete memory: {e}")
                print("\nTrying event-by-event deletion...")
                # Fallback: try to list and delete events without filters
                # This won't work with current API, so just inform user
                print("❌ Cannot list all events without actorId or sessionId")
                print("   Use --user or --session instead")
                return
        
        # List events (API requires both actorId and sessionId)
        if not user_id or not session_id:
            print("❌ Both --user and --session are required")
            print("   Example: python purge_memory.py --user test_user --session req_abc123")
            return
        
        params = {'memoryId': memory_id, 'actorId': user_id, 'sessionId': session_id, 'maxResults': 100}
        
        response = client.list_events(**params)
        events = response.get('events', [])
        
        if not events:
            print("✅ No events found to delete")
            return
        
        print(f"Found {len(events)} events to delete")
        
        # Delete each event
        deleted = 0
        for event in events:
            event_id = event.get('eventId')
            try:
                client.delete_event(
                    memoryId=memory_id,
                    eventId=event_id
                )
                deleted += 1
                print(f"✅ Deleted event {event_id}")
            except Exception as e:
                print(f"❌ Failed to delete {event_id}: {e}")
        
        print(f"\n✅ Purged {deleted}/{len(events)} events")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("""
Usage:
  python purge_memory.py --user <user_id> --session <session_id>  # Delete events for specific session
  python purge_memory.py --all                                      # Delete entire memory (recreate required)
        """)
        sys.exit(1)
    
    if sys.argv[1] == '--user' and len(sys.argv) > 3 and sys.argv[3]:
        purge_memory(user_id=sys.argv[2], session_id=sys.argv[4] if len(sys.argv) > 4 else None)
    elif sys.argv[1] == '--all':
        confirm = input("⚠️  Delete ENTIRE memory? Type 'yes' to confirm: ")
        if confirm.lower() == 'yes':
            purge_memory(purge_all=True)
        else:
            print("Cancelled")
    else:
        print("Invalid arguments")
