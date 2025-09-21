from shared_queue import SharedMessageQueue
#!/usr/bin/env python3
"""
Monitoring Agent for Open Banking Consent Choreographer

Polls Bank of Anthos APIs to detect consent triggers for third-party data sharing.
Uses MCP (Microservices Context Provider) stub for API context wrapping.
Sends A2A messages to Validation Agent when triggers are detected.

ADK (Agent Development Kit) run loop with configurable polling interval.
"""

import os
import json
import time
import requests
from typing import Dict, List, Optional, Any
import random
import threading
from flask import Flask, jsonify

class MCPContextProvider:
    """Stub for Microservices Context Provider - wraps API calls with metadata"""

    def wrap_api_call(self, service_name: str, endpoint: str, data: Any) -> Dict[str, Any]:
        """Wrap API response with PSD3 compliance context"""
        return {
            'service': service_name,
            'endpoint': endpoint,
            'data': data,
            'timestamp': time.time(),
            'is_psd3_eligible': True,  # Mock eligibility check
            'consent_required': self._check_consent_required(data)
        }

    def _check_consent_required(self, data: Any) -> bool:
        """Mock check if data requires consent"""
        # Simulate consent triggers for demo purposes
        if isinstance(data, list) and len(data) > 0:
            # Check for transaction patterns that might indicate third-party access
            return True
        return False


class A2AMessageQueue:
    """Agent-to-Agent (A2A) protocol implementation with HTTP-based messaging"""

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.agent_endpoints = {
            'ValidationAgent': 'http://validation-agent-service.agents-ns.svc.cluster.local:8080/a2a',
            'AuditAgent': 'http://audit-agent-service.agents-ns.svc.cluster.local:8080/a2a'
        }

    def send_message(self, target_agent: str, message_type: str, payload: Dict[str, Any], correlation_id: str = None) -> str:
        """Send A2A message to target agent using HTTP protocol"""
        if correlation_id is None:
            correlation_id = f"{self.agent_name}_{int(time.time())}_{hash(str(payload))}"

        a2a_message = {
            'protocol': 'A2A/1.0',
            'message_id': correlation_id,
            'from_agent': self.agent_name,
            'to_agent': target_agent,
            'message_type': message_type,
            'timestamp': time.time(),
            'payload': payload,
            'headers': {
                'content_type': 'application/json',
                'priority': 'normal'
            }
        }

        try:
            endpoint = self.agent_endpoints.get(target_agent)
            if not endpoint:
                print(f"[A2A] No endpoint configured for agent: {target_agent}")
                return correlation_id

            response = requests.post(endpoint, json=a2a_message, timeout=10)

            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'accepted':
                    print(f"[A2A] Message {correlation_id} sent to {target_agent}")
                    return correlation_id
                else:
                    print(f"[A2A] Message {correlation_id} rejected by {target_agent}: {result.get('reason', 'unknown')}")
            else:
                print(f"[A2A] Failed to send message to {target_agent}: HTTP {response.status_code}")

        except requests.RequestException as e:
            print(f"[A2A] Error sending message to {target_agent}: {e}")

        return correlation_id

    def receive_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming A2A message - should be overridden by subclasses"""
        return {'status': 'accepted', 'message_id': message.get('message_id')}


class ADKAgent:
    """Stub for Agent Development Kit - base agent class"""

    def __init__(self, name: str, a2a_queue: A2AMessageQueue):
        self.name = name
        self.a2a_queue = a2a_queue
        self.running = True

    def run_loop(self, interval_seconds: int = 10):
        """Main agent run loop"""
        print(f"[{self.name}] Starting agent run loop...")
        while self.running:
            try:
                self.process_cycle()
            except Exception as e:
                print(f"[{self.name}] Error in run cycle: {e}")
            time.sleep(interval_seconds)

    def stop(self):
        """Stop the agent"""
        self.running = False
        print(f"[{self.name}] Stopping agent...")


class MonitoringAgent(ADKAgent):
    """Monitoring Agent - detects consent triggers from API polling"""

    def __init__(self, a2a_queue: A2AMessageQueue):
        super().__init__("MonitoringAgent", a2a_queue)
        self.a2a_queue = a2a_queue  # Store reference to A2A queue
        self.mcp = MCPContextProvider()

        # Service endpoints (internal cluster addresses)
        self.transaction_history_url = "http://transactionhistory.default.svc.cluster.local:8080/transactions"
        self.user_service_url = "http://userservice.default.svc.cluster.local:8080"
        self.contacts_url = "http://contacts.default.svc.cluster.local:8080/contacts"

        # Demo account IDs to monitor (these would normally come from user service)
        self.monitored_accounts = ['1234567890', '0987654321', '1111111111']

        # Mock JWT token (in production, get from user-service POST /login)
        self.jwt_token = os.getenv("MOCK_JWT_TOKEN", "mock.jwt.token.for.demo")

        # Track last seen transaction IDs to detect new activity
        self.last_transaction_count = 0

    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API calls"""
        return {
            'Authorization': f'Bearer {self.jwt_token}',
            'Content-Type': 'application/json'
        }

    def poll_transactions(self) -> Optional[List[Dict[str, Any]]]:
        """Poll transaction history from Bank of Anthos transaction service"""
        all_transactions = []

        for account_id in self.monitored_accounts:
            try:
                # Try with auth headers first
                headers = self.get_auth_headers()
                url = f"{self.transaction_history_url}/{account_id}"
                response = requests.get(url, headers=headers, timeout=5)

                # If auth fails, try without authentication (for demo)
                if response.status_code == 401:
                    print(f"[Monitoring] Auth failed for account {account_id}, trying without auth...")
                    response = requests.get(url, timeout=5)

                if response.status_code == 200:
                    account_transactions = response.json()
                    if isinstance(account_transactions, list):
                        # Add account_id to each transaction for tracking
                        for tx in account_transactions:
                            tx['account_id'] = account_id
                        all_transactions.extend(account_transactions)
                        print(f"[Monitoring] Polled {len(account_transactions)} transactions for account {account_id}")
                    else:
                        print(f"[Monitoring] Unexpected response format for account {account_id}")
                else:
                    print(f"[Monitoring] Failed to poll account {account_id}: HTTP {response.status_code}")

            except requests.RequestException as e:
                print(f"[Monitoring] Error polling account {account_id}: {e}")

        print(f"[Monitoring] Total transactions polled: {len(all_transactions)}")
        return all_transactions if all_transactions else None

    def poll_users(self) -> Optional[List[Dict[str, Any]]]:
        """Poll user data from user-service"""
        try:
            # Mock polling multiple users for demo (normally would have specific user IDs)
            user_ids = ['testuser', 'alice', 'bob']  # Mock user IDs from repo

            users = []
            for user_id in user_ids:
                headers = self.get_auth_headers()
                url = f"{self.user_service_url}/users/{user_id}"
                response = requests.get(url, headers=headers, timeout=5)

                if response.status_code == 200:
                    users.append(response.json())
                else:
                    print(f"[Monitoring] Failed to get user {user_id}: HTTP {response.status_code}")

            print(f"[Monitoring] Polled {len(users)} users")
            return users

        except requests.RequestException as e:
            print(f"[Monitoring] Error polling users: {e}")
            return None

    def detect_consent_triggers(self, transactions: List[Dict], users: List[Dict]) -> List[Dict[str, Any]]:
        """Detect potential consent triggers from real Bank of Anthos transaction data"""
        triggers = []

        if not transactions:
            return triggers

        # Track transactions per account to detect new activity
        current_tx_count = len(transactions)
        new_transactions = []

        if current_tx_count > self.last_transaction_count:
            # Get only new transactions since last check
            new_transaction_count = current_tx_count - self.last_transaction_count
            new_transactions = transactions[-new_transaction_count:]
            self.last_transaction_count = current_tx_count

        # Process all transactions (including previously seen ones) for pattern detection
        for transaction in transactions:
            trigger = self._analyze_transaction_for_consent(transaction)
            if trigger:
                triggers.append(trigger)

        # If no triggers from new transactions, check for periodic review patterns
        if not triggers and new_transactions:
            # Check for patterns that require consent review
            account_activity = {}
            for tx in new_transactions:
                account = tx.get('account_id', 'unknown')
                if account not in account_activity:
                    account_activity[account] = []
                account_activity[account].append(tx)

            # Trigger periodic review if account has multiple recent transactions
            for account, txs in account_activity.items():
                if len(txs) >= 3:  # Multiple transactions indicate active usage
                    trigger = {
                        'type': 'account_activity_review',
                        'user_id': account,
                        'transaction_count': len(txs),
                        'timestamp': time.time(),
                        'reason': f'Multiple transactions detected for account {account} - consent review required'
                    }
                    triggers.append(trigger)
                    print(f"[Monitoring] Account activity consent trigger: {trigger}")

        print(f"[Monitoring] Detected {len(triggers)} consent triggers")
        return triggers

    def _analyze_transaction_for_consent(self, transaction: Dict) -> Optional[Dict[str, Any]]:
        """Analyze individual transaction for consent requirements"""
        try:
            amount = abs(float(transaction.get('amount', 0)))
            account_id = transaction.get('account_id', 'unknown')
            timestamp = transaction.get('timestamp', time.time())

            # PSD3 Consent Trigger Rules:
            # 1. High-value transactions (> €5000 or equivalent)
            if amount > 5000:
                return {
                    'type': 'high_value_transaction',
                    'transaction_id': transaction.get('id', 'unknown'),
                    'amount': amount,
                    'user_id': account_id,
                    'timestamp': timestamp,
                    'reason': f'High-value transaction (€{amount:.2f}) detected - PSD3 consent required for processing'
                }

            # 2. International transfers (detect by routing numbers or currency)
            from_routing = transaction.get('from_routing_num', '')
            to_routing = transaction.get('to_routing_num', '')
            if from_routing != to_routing and from_routing and to_routing:
                return {
                    'type': 'international_transfer',
                    'transaction_id': transaction.get('id', 'unknown'),
                    'amount': amount,
                    'user_id': account_id,
                    'timestamp': timestamp,
                    'reason': f'International transfer detected (routing: {from_routing} → {to_routing}) - consent required'
                }

            # 3. Third-party data sharing indicators (large amounts to new recipients)
            if amount > 1000:
                return {
                    'type': 'third_party_data_sharing',
                    'transaction_id': transaction.get('id', 'unknown'),
                    'amount': amount,
                    'user_id': account_id,
                    'timestamp': timestamp,
                    'reason': f'Large transaction (€{amount:.2f}) may indicate third-party data sharing - consent verification required'
                }

        except (ValueError, TypeError) as e:
            print(f"[Monitoring] Error analyzing transaction {transaction.get('id', 'unknown')}: {e}")

        return None

    def process_cycle(self):
        """Main processing cycle - poll APIs and detect triggers"""
        print(f"[{self.name}] Starting monitoring cycle...")

        # Poll APIs via MCP
        transactions = self.poll_transactions()
        users = self.poll_users()

        if transactions is not None and users is not None:
            # Wrap data with MCP context
            wrapped_transactions = self.mcp.wrap_api_call('ledger-writer', '/transactions', transactions)
            wrapped_users = self.mcp.wrap_api_call('user-service', '/users', users)

            # Detect consent triggers
            triggers = self.detect_consent_triggers(transactions, users)

            # Send A2A messages to Validation Agent for each trigger
            for trigger in triggers:
                message = {
                    'trigger_type': trigger['type'],
                    'data': trigger,
                    'source_agent': self.name,
                    'context': {
                        'transactions': wrapped_transactions,
                        'users': wrapped_users
                    }
                }
                # Send message to validation agent via HTTP
                self.send_to_validation_agent(trigger)
        else:
            print(f"[{self.name}] API polling failed - using demo mode")
            # In demo mode, periodically generate mock triggers
            self.generate_demo_trigger_and_send()

    def generate_demo_trigger_and_send(self):
        """Generate and send a demo consent trigger for testing"""
        import random

        # Generate random demo triggers
        trigger_types = [
            'third_party_sharing',
            'high_value_transaction',
            'international_transfer',
            'account_review'
        ]

        purposes = [
            'investment_advice',
            'loan_application',
            'insurance_quote',
            'tax_planning'
        ]

        providers = [
            'FinTechCorp',
            'InvestmentApp',
            'LoanProvider',
            'InsuranceHub'
        ]

        # Create demo trigger
        trigger = {
            'type': random.choice(trigger_types),
            'amount': random.randint(100, 10000),
            'purpose': random.choice(purposes),
            'third_party_provider': random.choice(providers),
            'user_id': f'user_{random.randint(1000, 9999)}',
            'data_scope': ['transactions', 'balance'],
            'consent_required': True,
            'timestamp': time.time()
        }

        print(f"[{self.name}] Generated demo trigger: {trigger['type']} for {trigger['purpose']}")
        self.send_to_validation_agent(trigger)

    def send_to_validation_agent(self, trigger: Dict[str, Any]):
        """Send consent trigger to validation agent via A2A protocol"""
        correlation_id = self.a2a_queue.send_message(
            target_agent='ValidationAgent',
            message_type='consent_validation_request',
            payload=trigger
        )
        print(f"[{self.name}] Sent consent validation request via A2A (ID: {correlation_id})")

    def generate_demo_trigger(self) -> Dict[str, Any]:
        """Generate a mock consent trigger for demo purposes"""
        import time
        import random
        
        # Mock third-party data sharing request
        mock_triggers = [
            {
                "type": "third_party_balance_access",
                "user_id": f"user_{random.randint(1000, 9999)}",
                "amount": random.randint(100, 5000),
                "timestamp": time.time(),
                "third_party_provider": "FinTech Corp",
                "purpose": "Loan Application",
                "data_scope": ["balance", "transactions"],
                "consent_required": True
            },
            {
                "type": "third_party_transaction_sharing", 
                "user_id": f"user_{random.randint(1000, 9999)}",
                "amount": random.randint(50, 1000),
                "timestamp": time.time(),
                "third_party_provider": "Investment App",
                "purpose": "Investment Analysis",
                "data_scope": ["transactions", "balance"],
                "consent_required": True
            },
            {
                "type": "open_banking_consent",
                "user_id": f"user_{random.randint(1000, 9999)}",
                "amount": 0,
                "timestamp": time.time(),
                "third_party_provider": "Budget Tracker",
                "purpose": "Financial Planning",
                "data_scope": ["accounts", "transactions"],
                "consent_required": True
            }
        ]
        
        return random.choice(mock_triggers)

    def start_api_server(self):
        """Start Flask API server for demo consent triggering"""
        app = Flask(__name__)
        
        @app.route("/trigger-consent", methods=["POST"])
        def trigger_consent():
            try:
                demo_trigger = self.generate_demo_trigger()
                print(f"[Monitoring] 🎯 API: Triggered consent: {demo_trigger['type']}")
                self.a2a_queue.send_message('ValidationAgent', 'consent_validation_request', demo_trigger)
                return jsonify({
                    "status": "success",
                    "trigger": demo_trigger,
                    "message": "Consent trigger sent to validation agent"
                })
            except Exception as e:
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @app.route("/health", methods=["GET"])
        def health():
            return jsonify({"status": "healthy", "agent": "monitoring"})
        
        print(f"[{self.name}] Starting API server on port 8080...")
        app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)


def main():
    """Main entry point"""
    print("Starting Open Banking Consent Monitoring Agent...")

    # Initialize A2A queue for inter-agent communication
    a2a_queue = A2AMessageQueue("MonitoringAgent")

    # Create and start monitoring agent
    agent = MonitoringAgent(a2a_queue)

    # Start API server in background thread
    api_thread = threading.Thread(target=agent.start_api_server, daemon=True)
    api_thread.start()

    try:
        agent.run_loop(interval_seconds=int(os.getenv('MONITORING_INTERVAL', '30')))
    except KeyboardInterrupt:
        print("Shutting down monitoring agent...")
        agent.stop()


if __name__ == "__main__":
    main()

