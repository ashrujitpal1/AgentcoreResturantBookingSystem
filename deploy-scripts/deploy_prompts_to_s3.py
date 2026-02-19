"""
Upload versioned prompts to S3.
Run this script to deploy new prompt versions.
"""
import boto3
import os
import sys

# Add project root to path
sys.path.append('/Users/USER/Work/AI/AgentCore/AgentcoreResturantBookingSystem')

from dotenv import load_dotenv
load_dotenv()


def create_prompt_bucket(bucket_name: str, region: str = "us-east-1"):
    """Create S3 bucket for prompts with versioning enabled"""
    s3 = boto3.client("s3", region_name=region)
    
    try:
        if region == "us-east-1":
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region}
            )
        
        # Enable versioning
        s3.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={"Status": "Enabled"}
        )
        
        print(f"✅ Created bucket: {bucket_name} with versioning enabled")
    except s3.exceptions.BucketAlreadyOwnedByYou:
        print(f"✅ Bucket already exists: {bucket_name}")
    except Exception as e:
        print(f"❌ Error creating bucket: {e}")
        raise


def upload_prompts(bucket_name: str, prompts_dir: str = "prompts"):
    """Upload all prompts from local directory to S3"""
    s3 = boto3.client("s3")
    
    uploaded = 0
    for root, dirs, files in os.walk(prompts_dir):
        for file in files:
            if file.endswith(".md"):
                local_path = os.path.join(root, file)
                # Convert local path to S3 key
                s3_key = local_path.replace(prompts_dir + "/", "prompts/")
                
                with open(local_path, "r") as f:
                    content = f.read()
                
                s3.put_object(
                    Bucket=bucket_name,
                    Key=s3_key,
                    Body=content.encode("utf-8"),
                    ContentType="text/markdown"
                )
                
                print(f"✅ Uploaded: {s3_key}")
                uploaded += 1
    
    print(f"\n✅ Total prompts uploaded: {uploaded}")


def verify_prompts(bucket_name: str):
    """Verify all prompts are accessible"""
    from src.core.prompt_manager import PromptManager
    
    pm = PromptManager(bucket_name=bucket_name)
    
    agents = ["intent_classifier", "restaurant_finder", "booking_agent"]
    
    print("\n" + "=" * 80)
    print("VERIFYING PROMPTS")
    print("=" * 80)
    
    for agent in agents:
        try:
            prompt = pm.load_prompt(agent, "1.0.0")
            print(f"\n✅ {agent} v1.0.0")
            print(f"   Length: {len(prompt)} characters")
            print(f"   First 100 chars: {prompt[:100]}...")
        except Exception as e:
            print(f"\n❌ {agent} v1.0.0: {e}")


if __name__ == "__main__":
    BUCKET_NAME = "restaurant-booking-prompts-" + os.getenv("AWS_ACCOUNT_ID", "123456789012")
    REGION = os.getenv("AWS_REGION", "us-east-1")
    
    print("=" * 80)
    print("PROMPT DEPLOYMENT TO S3")
    print("=" * 80)
    print(f"Bucket: {BUCKET_NAME}")
    print(f"Region: {REGION}")
    print("=" * 80)
    
    # Step 1: Create bucket
    create_prompt_bucket(BUCKET_NAME, REGION)
    
    # Step 2: Upload prompts
    upload_prompts(BUCKET_NAME)
    
    # Step 3: Verify
    verify_prompts(BUCKET_NAME)
    
    print("\n" + "=" * 80)
    print("✅ Prompt deployment complete")
    print("=" * 80)
    print(f"\nUpdate .env file:")
    print(f"PROMPT_BUCKET={BUCKET_NAME}")
