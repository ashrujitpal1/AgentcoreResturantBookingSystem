"""
Observability - Correlation IDs, X-Ray tracing, cost tracking.
Implements comprehensive monitoring for production systems.
"""
import uuid
import time
import json
from typing import Dict, Any, Optional
from datetime import datetime
from functools import wraps
from aws_xray_sdk.core import xray_recorder
import boto3


class CorrelationContext:
    """Thread-local correlation context for distributed tracing"""
    
    _context = {}
    
    @classmethod
    def set(cls, correlation_id: str, user_id: str, session_id: str):
        cls._context = {
            "correlation_id": correlation_id,
            "user_id": user_id,
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @classmethod
    def get(cls) -> Dict[str, str]:
        return cls._context.copy()
    
    @classmethod
    def get_correlation_id(cls) -> Optional[str]:
        return cls._context.get("correlation_id")


def with_correlation_id(func):
    """Decorator to inject correlation ID into function calls"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        correlation_id = CorrelationContext.get_correlation_id()
        if not correlation_id:
            correlation_id = f"req_{uuid.uuid4()}"
            CorrelationContext.set(correlation_id, "unknown", "unknown")
        
        # Add to X-Ray segment
        xray_recorder.put_annotation("correlation_id", correlation_id)
        
        return func(*args, **kwargs)
    
    return wrapper


def trace_operation(operation_name: str):
    """Decorator for X-Ray tracing with automatic subsegment creation"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with xray_recorder.capture(operation_name) as subsegment:
                # Add correlation context
                context = CorrelationContext.get()
                for key, value in context.items():
                    subsegment.put_annotation(key, value)
                
                # Add function metadata
                subsegment.put_metadata("function", func.__name__)
                subsegment.put_metadata("args_count", len(args))
                
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    
                    # Track success
                    subsegment.put_annotation("status", "success")
                    duration = time.time() - start_time
                    subsegment.put_metadata("duration_ms", duration * 1000)
                    
                    return result
                    
                except Exception as e:
                    # Track failure
                    subsegment.put_annotation("status", "error")
                    subsegment.put_metadata("error", str(e))
                    raise
        
        return wrapper
    return decorator


class CostTracker:
    """Track LLM costs per request with CloudWatch metrics"""
    
    def __init__(self):
        self.cloudwatch = boto3.client("cloudwatch")
        self.costs = []
    
    def track_llm_call(
        self,
        correlation_id: str,
        user_id: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost: float
    ):
        """Track individual LLM call cost"""
        self.costs.append({
            "correlation_id": correlation_id,
            "user_id": user_id,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Send to CloudWatch
        try:
            self.cloudwatch.put_metric_data(
                Namespace="RestaurantBooking/LLM",
                MetricData=[
                    {
                        "MetricName": "TokenUsage",
                        "Value": input_tokens + output_tokens,
                        "Unit": "Count",
                        "Dimensions": [
                            {"Name": "Model", "Value": model},
                            {"Name": "UserId", "Value": user_id}
                        ]
                    },
                    {
                        "MetricName": "Cost",
                        "Value": cost,
                        "Unit": "None",
                        "Dimensions": [
                            {"Name": "Model", "Value": model},
                            {"Name": "UserId", "Value": user_id}
                        ]
                    }
                ]
            )
        except Exception as e:
            print(f"Failed to send CloudWatch metrics: {e}")
    
    def get_request_cost(self, correlation_id: str) -> float:
        """Get total cost for a request"""
        return sum(
            c["cost"] for c in self.costs 
            if c["correlation_id"] == correlation_id
        )
    
    def get_user_cost(self, user_id: str) -> float:
        """Get total cost for a user"""
        return sum(
            c["cost"] for c in self.costs 
            if c["user_id"] == user_id
        )


class StructuredLogger:
    """Structured logging with correlation IDs"""
    
    @staticmethod
    def log(level: str, message: str, **kwargs):
        """Log with correlation context"""
        context = CorrelationContext.get()
        
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message,
            **context,
            **kwargs
        }
        
        print(json.dumps(log_entry))
    
    @staticmethod
    def info(message: str, **kwargs):
        StructuredLogger.log("INFO", message, **kwargs)
    
    @staticmethod
    def error(message: str, **kwargs):
        StructuredLogger.log("ERROR", message, **kwargs)
    
    @staticmethod
    def warning(message: str, **kwargs):
        StructuredLogger.log("WARNING", message, **kwargs)


# Global instances
cost_tracker = CostTracker()
logger = StructuredLogger()
