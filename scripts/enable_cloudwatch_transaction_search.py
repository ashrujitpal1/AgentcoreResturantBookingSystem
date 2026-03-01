"""
Enable CloudWatch Transaction Search for AWS X-Ray.
Steps:
  1. Put resource policy granting X-Ray permission to write to CloudWatch Logs
  2. Update X-Ray trace segment destination to CloudWatchLogs
  3. (Optional) Update indexing rule sampling percentage
"""
import json
import boto3
import argparse

def get_account_region():
    sts = boto3.client("sts")
    identity = sts.get_caller_identity()
    region = boto3.session.Session().region_name or "us-east-1"
    return identity["Account"], region

def put_resource_policy(account_id: str, region: str):
    logs = boto3.client("logs", region_name=region)
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "TransactionSearchXRayAccess",
                "Effect": "Allow",
                "Principal": {"Service": "xray.amazonaws.com"},
                "Action": "logs:PutLogEvents",
                "Resource": [
                    f"arn:aws:logs:{region}:{account_id}:log-group:aws/spans:*",
                    f"arn:aws:logs:{region}:{account_id}:log-group:/aws/application-signals/data:*"
                ],
                "Condition": {
                    "ArnLike": {
                        "aws:SourceArn": f"arn:aws:xray:{region}:{account_id}:*"
                    },
                    "StringEquals": {
                        "aws:SourceAccount": account_id
                    }
                }
            }
        ]
    }
    logs.put_resource_policy(
        policyName="TransactionSearchXRayPolicy",
        policyDocument=json.dumps(policy)
    )
    print(f"✅ Resource policy applied for account {account_id} in {region}")

def update_trace_destination():
    xray = boto3.client("xray")
    try:
        xray.update_trace_segment_destination(Destination="CloudWatchLogs")
        print("✅ X-Ray trace segment destination set to CloudWatchLogs")
    except xray.exceptions.InvalidRequestException as e:
        if "already set" in str(e):
            print("✅ X-Ray trace segment destination already set to CloudWatchLogs")
        else:
            raise

def update_sampling_percentage(percentage: float):
    xray = boto3.client("xray")
    xray.update_indexing_rule(
        name="Default",
        rule={"Probabilistic": {"DesiredSamplingPercentage": percentage}}
    )
    print(f"✅ Sampling percentage set to {percentage}%")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Enable CloudWatch Transaction Search")
    parser.add_argument("--sampling-percentage", type=float, default=None,
                        help="Optional: desired sampling percentage (0-100)")
    args = parser.parse_args()

    account_id, region = get_account_region()
    print(f"🔍 Account: {account_id} | Region: {region}")

    put_resource_policy(account_id, region)
    update_trace_destination()

    if args.sampling_percentage is not None:
        update_sampling_percentage(args.sampling_percentage)
    else:
        print("ℹ️  Skipping sampling percentage update (use --sampling-percentage to set)")
