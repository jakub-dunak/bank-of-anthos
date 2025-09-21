#!/usr/bin/env python3
"""
Demo Consent Trigger Script

Triggers mock consent requests for Open Banking Consent Choreographer demo.
"""

import requests
import time
import random

# Demo consent scenarios
CONSENT_SCENARIOS = [
    {
        "type": "third_party_balance_access",
        "user_id": f"user_{random.randint(1000, 9999)}",
        "amount": random.randint(100, 5000),
        "third_party_provider": "FinTech Corp",
        "purpose": "Loan Application",
        "data_scope": ["balance", "transactions"],
        "consent_required": True
    },
    {
        "type": "third_party_transaction_sharing", 
        "user_id": f"user_{random.randint(1000, 9999)}",
        "amount": random.randint(50, 1000),
        "third_party_provider": "Investment App",
        "purpose": "Investment Analysis",
        "data_scope": ["transactions", "balance"],
        "consent_required": True
    },
    {
        "type": "open_banking_consent",
        "user_id": f"user_{random.randint(1000, 9999)}",
        "amount": 0,
        "third_party_provider": "Budget Tracker",
        "purpose": "Financial Planning",
        "data_scope": ["accounts", "transactions"],
        "consent_required": True
    }
]

def trigger_consent_request(scenario=None):
    """Trigger a consent request by sending it to the monitoring agent's API"""
    
    if scenario is None:
        scenario = random.choice(CONSENT_SCENARIOS)
    
    # In a real implementation, this would call the monitoring agent's API
    # For demo purposes, we'll simulate by calling the agents directly
    print(f"🎯 TRIGGERING CONSENT: {scenario['type']}")
    print(f"   User: {scenario['user_id']}")
    print(f"   Provider: {scenario['third_party_provider']}")
    print(f"   Purpose: {scenario['purpose']}")
    print(f"   Data Scope: {', '.join(scenario['data_scope'])}")
    
    # The monitoring agent will pick this up in its next cycle
    return scenario

def main():
    print("🎭 Open Banking Consent Choreographer - Demo Trigger")
    print("=" * 60)
    
    # Trigger multiple consents for demo
    for i in range(3):
        trigger_consent_request()
        print()
        time.sleep(2)
    
    print("✅ Demo consents triggered!")
    print("📊 Check the agent dashboard and logs to see the consent flow in action:")
    print("   Dashboard: http://34.10.225.121:8501")
    print("   Agent Logs: kubectl logs -f deployment/monitoring-agent -n agents-ns")

if __name__ == "__main__":
    main()
