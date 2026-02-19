"""Setup script for AgentCore Memory for Restaurant Booking System."""

import sys
import boto3
from bedrock_agentcore_starter_toolkit.operations.memory.manager import MemoryManager
from bedrock_agentcore_starter_toolkit.operations.memory.models.strategies import (
    SummaryStrategy,
    UserPreferenceStrategy,
    SemanticStrategy
)


def setup_memory(region_name: str = "us-east-1") -> str:
    """Create AgentCore Memory with three standard long-term strategies.
    
    Args:
        region_name: AWS region name
    
    Returns:
        Memory ID
    """
    print(f"Setting up AgentCore Memory in region {region_name}...")
    
    # Create memory manager
    memory_manager = MemoryManager(region_name=region_name)
    
    # Create memory with three standard strategies
    memory = memory_manager.get_or_create_memory(
        name="RestaurantBookingMemory",
        strategies=[
            # Strategy 1: Session summaries (restaurant search, selection, booking details)
            SummaryStrategy(
                name="BookingSessionSummaries",
                namespaces=["/restaurant-booking/{actorId}/{sessionId}"]
            ),
            # Strategy 2: User dining preferences (cuisine, dietary restrictions, etc.)
            UserPreferenceStrategy(
                name="UserDiningPreferences",
                namespaces=["/restaurant-booking/{actorId}/preferences"]
            ),
            # Strategy 3: User booking history and facts
            SemanticStrategy(
                name="UserBookingHistory",
                namespaces=["/restaurant-booking/{actorId}/facts"]
            )
        ],        
        event_expiry_days=3,  # Minimum 3-day retention for conversation history
    )
    
    memory_id = memory.get('id')
    print(f"\n✅ Memory created successfully!")
    print(f"Memory ID: {memory_id}")
    print(f"\nAdd this to your .env file:")
    print(f"MEMORY_ID={memory_id}")
    
    return memory_id


def store_memory_id_in_ssm(param_name: str, memory_id: str, region_name: str):
    """Store memory ID in SSM Parameter Store."""
    ssm = boto3.client("ssm", region_name=region_name)
    ssm.put_parameter(Name=param_name, Value=memory_id, Type="String", Overwrite=True)
    print(f"Stored memory_id in SSM: {param_name}")


if __name__ == "__main__":
    # Get region from command line or use default
    region = sys.argv[1] if len(sys.argv) > 1 else "us-east-1"
    param_name = "/restaurant-booking/agentcore/memory_id"
    
    try:
        memory_id = setup_memory(region)
        store_memory_id_in_ssm(param_name, memory_id, region)
        
        print(f"\n🎉 AgentCore Memory deployment complete!")
        print(f"\nMemory Configuration:")
        print(f"  - Name: RestaurantBookingMemory")
        print(f"  - Memory ID: {memory_id}")
        print(f"  - SSM Parameter: {param_name}")
        print(f"  - Strategies: 3 (Session Summaries, Dining Preferences, Booking History)")
        print(f"  - Expiry: 90 days")

    except Exception as e:
        print(f"\n❌ Error setting up memory: {str(e)}")
        sys.exit(1)
