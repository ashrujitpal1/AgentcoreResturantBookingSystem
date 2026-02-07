"""
MCP Tool wrappers for Lambda functions.
These tools are called by Strands agents through the workflow.
"""
import boto3
import json
import os
from typing import Dict, Any, Optional


class MCPToolClient:
    """Client for invoking Lambda functions"""
    
    def __init__(self):
        self.lambda_client = boto3.client("lambda")
    
    def invoke_lambda(self, function_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke Lambda function directly"""
        response = self.lambda_client.invoke(
            FunctionName=function_name,
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
        )
        
        result = json.loads(response['Payload'].read())
        return result
    
    def fetch_restaurant_details(self, **kwargs) -> Dict[str, Any]:
        return self.invoke_lambda("fetchRestaurantDetails-dev", kwargs)
    
    def fetch_restaurant_details_by_id(self, **kwargs) -> Dict[str, Any]:
        return self.invoke_lambda("fetchRestaurantDetailsById-dev", kwargs)
    
    def search_user_details(self, **kwargs) -> Dict[str, Any]:
        return self.invoke_lambda("searchUserDetails-dev", kwargs)
    
    def register_user(self, **kwargs) -> Dict[str, Any]:
        return self.invoke_lambda("registerUser-dev", kwargs)
    
    def token_amount_calculation(self, **kwargs) -> Dict[str, Any]:
        return self.invoke_lambda("tokenAmountCalculation-dev", kwargs)
    
    def book_a_table(self, **kwargs) -> Dict[str, Any]:
        return self.invoke_lambda("bookATable-dev", kwargs)
    
    def payment_api(self, **kwargs) -> Dict[str, Any]:
        return self.invoke_lambda("paymentAPI-dev", kwargs)


def get_mcp_tools() -> Dict[str, Any]:
    """Get dictionary of MCP tool functions"""
    client = MCPToolClient()
    
    return {
        "fetchRestaurantDetails": client.fetch_restaurant_details,
        "fetchRestaurantDetailsById": client.fetch_restaurant_details_by_id,
        "searchUserDetails": client.search_user_details,
        "registerUser": client.register_user,
        "tokenAmountCalculation": client.token_amount_calculation,
        "bookATable": client.book_a_table,
        "paymentAPI": client.payment_api
    }
