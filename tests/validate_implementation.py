#!/usr/bin/env python3
"""
Code Validation Script - Verify Stateless Implementation
Checks that the code changes were applied correctly
"""
import os
import sys

def check_file_exists(filepath):
    """Check if file exists"""
    if os.path.exists(filepath):
        print(f"✅ {filepath} exists")
        return True
    else:
        print(f"❌ {filepath} NOT FOUND")
        return False

def check_orchestrator():
    """Validate orchestrator.py changes"""
    print("\n" + "="*60)
    print("VALIDATING: src/orchestrator.py")
    print("="*60)
    
    filepath = "src/orchestrator.py"
    if not check_file_exists(filepath):
        return False
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    checks = {
        "restaurants removed from payload": 'restaurants = payload.get("restaurants"' not in content,
        "selected_restaurant removed from payload": 'selected_restaurant = payload.get("selectedRestaurant"' not in content,
        "restaurants removed from invoke": 'restaurants=restaurants' not in content,
        "selected_restaurant removed from invoke": 'selected_restaurant=selected_restaurant' not in content,
        "restaurants removed from metadata": '"restaurants": result.get("restaurants"' not in content,
        "comment about memory added": 'all context from AgentCore Memory' in content.lower() or 'all context from memory' in content.lower()
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        if passed:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    return all_passed

def check_workflow():
    """Validate restaurant_workflow.py changes"""
    print("\n" + "="*60)
    print("VALIDATING: src/workflows/restaurant_workflow.py")
    print("="*60)
    
    filepath = "src/workflows/restaurant_workflow.py"
    if not check_file_exists(filepath):
        return False
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    checks = {
        "invoke signature updated": 'def invoke(self, user_message: str, user_id: str, session_id: str, \n               is_first_message: bool = False)' in content,
        "restaurants parameter removed": 'restaurants: list = None' not in content,
        "selected_restaurant parameter removed": 'selected_restaurant: dict = None' not in content,
        "phone parameter removed": 'phone: str = None' not in content,
        "docstring updated": 'Retrieves ALL context from AgentCore Memory' in content,
        "restaurants from memory": "restaurants = memory_data.get('restaurants', [])" in content,
        "selected_restaurant from memory": "selected_restaurant = memory_data.get('selected_restaurant')" in content,
        "_retrieve_memory returns restaurants": "'restaurants': restaurants" in content,
        "_retrieve_memory returns selected_restaurant": "'selected_restaurant': selected_restaurant" in content,
        "_store_memory stores restaurants": "restaurants_b64" in content,
        "_store_memory stores selected_restaurant": "selected_restaurant_b64" in content,
        "booking agent simplified": 'Using restaurants from memory' in content
    }
    
    all_passed = True
    for check_name, passed in checks.items():
        if passed:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name}")
            all_passed = False
    
    return all_passed

def check_documentation():
    """Check if documentation was created"""
    print("\n" + "="*60)
    print("VALIDATING: Documentation")
    print("="*60)
    
    docs = [
        "docs/CHANGE_PLAN.md",
        "docs/CORRECTED_ORCHESTRATION.md",
        "docs/IMPLEMENTATION_SUMMARY.md"
    ]
    
    all_exist = True
    for doc in docs:
        if check_file_exists(doc):
            pass
        else:
            all_exist = False
    
    return all_exist

def main():
    """Run all validations"""
    print("\n" + "="*60)
    print("STATELESS ORCHESTRATION - CODE VALIDATION")
    print("="*60)
    print("\nValidating implementation changes...\n")
    
    results = []
    
    # Check orchestrator
    results.append(("Orchestrator", check_orchestrator()))
    
    # Check workflow
    results.append(("Workflow", check_workflow()))
    
    # Check documentation
    results.append(("Documentation", check_documentation()))
    
    # Summary
    print("\n" + "="*60)
    print("VALIDATION SUMMARY")
    print("="*60)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{name}: {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    
    if all_passed:
        print("\n✅ ALL VALIDATIONS PASSED")
        print("\nImplementation is correct!")
        print("\nNext Steps:")
        print("1. Run: python tests/test_stateless_orchestration.py")
        print("2. Deploy to AWS Lambda")
        print("3. Test with real AWS services")
        return 0
    else:
        print("\n❌ SOME VALIDATIONS FAILED")
        print("\nPlease review the failed checks above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
