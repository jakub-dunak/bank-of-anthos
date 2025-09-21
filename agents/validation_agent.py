from shared_queue import SharedMessageQueue
#!/usr/bin/env python3
"""
Validation Agent for Open Banking Consent Choreographer

Validates consents using AI (mocked) and sends results to Audit Agent.
"""

import time
import json
import os
from typing import Dict, List, Any
from flask import Flask, jsonify, request
import threading
from werkzeug.serving import make_server
from google import genai
import requests

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
    """Base agent class"""

    def __init__(self, name: str, a2a_queue: A2AMessageQueue):
        self.name = name
        self.a2a_queue = a2a_queue
        self.running = True

    def run_loop(self, interval_seconds: int = 10):
        print(f"[{self.name}] Starting agent...")
        while self.running:
            try:
                self.process_cycle()
            except Exception as e:
                print(f"[{self.name}] Error: {e}")
            time.sleep(interval_seconds)

    def stop(self):
        self.running = False
        print(f"[{self.name}] Stopping...")

    def process_cycle(self):
        raise NotImplementedError("Subclasses must implement process_cycle")

class ValidationAgent:
    """Validation Agent with AI-powered PSD3 compliance checking"""

    def __init__(self):
        self.name = "ValidationAgent"
        self.app = Flask(__name__)
        self.app.add_url_rule('/health', 'health', self.health_check)
        self.app.add_url_rule('/validate', 'validate', self.validate_consent, methods=['POST'])
        self.app.add_url_rule('/a2a', 'a2a_message', self.handle_a2a_message, methods=['POST'])

        # Initialize A2A queue for inter-agent communication
        self.a2a_queue = A2AMessageQueue(self.name)

        self.server = None
        self.server_thread = None

        # Initialize Google AI Platform
        try:
            # Use API key authentication (set via environment variable)
            api_key = os.getenv('GOOGLE_API_KEY')
            if api_key:
                self.client = genai.Client(api_key=api_key)
                print(f"[{self.name}] ✅ AI client initialized successfully with API key")
            else:
                print(f"[{self.name}] ❌ No GOOGLE_API_KEY found, using rule-based validation")
                self.client = None
        except Exception as e:
            print(f"[{self.name}] AI initialization failed: {e}")
            print(f"[{self.name}] Falling back to rule-based validation")
            self.client = None

    def health_check(self):
        return jsonify({"status": "healthy", "agent": "validation-agent"})

    def validate_consent(self):
        """HTTP endpoint to receive and validate consent requests"""
        try:
            trigger_data = request.get_json()
            if not trigger_data:
                return jsonify({"error": "No trigger data provided"}), 400

            print(f"[{self.name}] Received validation request: {trigger_data.get('type', 'unknown')}")

            # Perform AI-powered validation
            validation_result = self.perform_ai_validation(trigger_data)

            # Send result to audit agent via A2A
            self.send_to_audit_agent(validation_result, trigger_data)

            return jsonify(validation_result)

        except Exception as e:
            print(f"[{self.name}] Error processing validation request: {e}")
            return jsonify({"error": str(e), "decision": "error", "confidence": 0.0}), 500

    def handle_a2a_message(self):
        """Handle incoming A2A protocol messages"""
        try:
            a2a_message = request.get_json()
            if not a2a_message:
                return jsonify({"status": "rejected", "reason": "No A2A message provided"}), 400

            # Process the A2A message
            result = self.process_a2a_message(a2a_message)

            return jsonify(result)

        except Exception as e:
            print(f"[{self.name}] Error processing A2A message: {e}")
            return jsonify({"status": "error", "reason": str(e)}), 500

    def process_a2a_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming A2A message"""
        try:
            if message.get('protocol') != 'A2A/1.0':
                return {'status': 'rejected', 'reason': 'Unsupported protocol'}

            if message.get('to_agent') != self.name:
                return {'status': 'rejected', 'reason': 'Message not for this agent'}

            message_id = message.get('message_id')
            message_type = message.get('message_type')
            payload = message.get('payload', {})

            print(f"[{self.name}] Processing A2A message {message_id} of type {message_type}")

            if message_type == 'consent_validation_request':
                # Perform AI-powered validation
                validation_result = self.perform_ai_validation(payload)

                # Send result to audit agent via A2A
                audit_correlation_id = self.send_to_audit_agent(validation_result, payload, message_id)

                return {
                    'status': 'accepted',
                    'message_id': message_id,
                    'result': validation_result,
                    'audit_message_id': audit_correlation_id
                }
            else:
                return {'status': 'rejected', 'reason': f'Unknown message type: {message_type}'}

        except Exception as e:
            print(f"[{self.name}] Error processing A2A message: {e}")
            return {'status': 'error', 'reason': str(e)}

    def perform_ai_validation(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use AI to validate PSD3 compliance of the consent request"""
        if not self.client:
            # Fallback to mock validation if AI is not available
            print(f"[{self.name}] ❌ AI client not initialized - using MOCK validation")
            return self._mock_validation(trigger_data)

        try:
            print(f"[{self.name}] ✅ Using REAL AI validation with Gemini")
            # Create comprehensive prompt for PSD3 compliance analysis
            prompt = self._create_psd3_validation_prompt(trigger_data)

            # Call Gemini AI using google-genai client
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=prompt
            )
            ai_response = response.text.strip()

            print(f"[{self.name}] 🤖 AI Response received: {len(ai_response)} characters")

            # Parse AI response to extract decision and confidence
            return self._parse_ai_response(ai_response, trigger_data)

        except Exception as e:
            print(f"[{self.name}] AI validation failed: {e}")
            print(f"[{self.name}] Falling back to rule-based validation")
            return self._mock_validation(trigger_data)

    def _create_psd3_validation_prompt(self, trigger_data: Dict[str, Any]) -> str:
        """Create a comprehensive prompt for PSD3 compliance validation"""
        trigger_type = trigger_data.get('type', 'unknown')
        amount = trigger_data.get('amount', 0)
        purpose = trigger_data.get('purpose', 'unknown')
        provider = trigger_data.get('third_party_provider', 'unknown')
        data_scope = trigger_data.get('data_scope', [])

        return f"""
You are an expert PSD3 (Payment Services Directive 3) compliance validator for open banking consent requests.

Analyze the following consent request for PSD3 compliance:

Consent Request Details:
- Type: {trigger_type}
- Amount: €{amount}
- Purpose: {purpose}
- Third Party Provider: {provider}
- Data Scope: {', '.join(data_scope) if data_scope else 'Not specified'}
- User ID: {trigger_data.get('user_id', 'unknown')}

PSD3 Key Requirements to Check:
1. **Explicit Consent**: Must be clear, specific, and informed
2. **Purpose Limitation**: Data processing must be limited to specified purposes
3. **Data Minimization**: Only necessary data should be shared
4. **Right to Withdraw**: User must be able to withdraw consent easily
5. **Transparency**: Clear information about data processing
6. **High-Value Transactions**: Special scrutiny for amounts >€5000
7. **International Transfers**: Additional checks for cross-border transactions

Please analyze this request and provide:
1. Decision: APPROVE or REJECT
2. Confidence Level: 0.0 to 1.0 (how certain you are)
3. Detailed Reasoning: Explain your decision based on PSD3 requirements
4. Risk Level: LOW, MEDIUM, or HIGH

Format your response as:
DECISION: [APPROVE/REJECT]
CONFIDENCE: [0.0-1.0]
REASONING: [Detailed explanation]
RISK_LEVEL: [LOW/MEDIUM/HIGH]
"""

    def _parse_ai_response(self, ai_response: str, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI response to extract structured validation result"""
        try:
            lines = ai_response.split('\n')
            decision = "REJECT"
            confidence = 0.5
            reasoning = ai_response
            risk_level = "MEDIUM"

            for line in lines:
                line = line.strip()
                if line.startswith('DECISION:'):
                    decision = line.split(':', 1)[1].strip().upper()
                elif line.startswith('CONFIDENCE:'):
                    try:
                        confidence = float(line.split(':', 1)[1].strip())
                        confidence = max(0.0, min(1.0, confidence))  # Clamp to 0-1
                    except ValueError:
                        confidence = 0.5
                elif line.startswith('REASONING:'):
                    reasoning = line.split(':', 1)[1].strip()
                elif line.startswith('RISK_LEVEL:'):
                    risk_level = line.split(':', 1)[1].strip().upper()

            return {
                "decision": decision,
                "confidence": confidence,
                "reasoning": reasoning,
                "risk_level": risk_level,
                "valid": decision == "APPROVE",
                "ai_processed": True
            }

        except Exception as e:
            print(f"[{self.name}] Error parsing AI response: {e}")
            return self._mock_validation(trigger_data)

    def _mock_validation(self, trigger_data: Dict[str, Any]) -> Dict[str, Any]:
        """PSD3-compliant rule-based validation (simulates AI reasoning)"""
        amount = trigger_data.get('amount', 0)
        trigger_type = trigger_data.get('type', 'unknown')
        purpose = trigger_data.get('purpose', 'unknown')
        provider = trigger_data.get('third_party_provider', 'unknown')

        # PSD3 Compliance Rules (simulating AI analysis)
        risk_score = 0
        reasons = []

        # High-value transaction check (>€5000 special scrutiny per PSD3)
        if amount > 5000:
            risk_score += 3
            reasons.append("High-value transaction requires enhanced scrutiny")

        # International transfer check
        if 'international' in purpose.lower() or 'cross-border' in purpose.lower():
            risk_score += 2
            reasons.append("International transfer requires additional verification")

        # Third-party data sharing check
        if provider and provider != 'bank':
            risk_score += 1
            reasons.append("Third-party data sharing must be explicitly consented to")

        # Account activity review check
        if trigger_type == 'account_review':
            risk_score += 1
            reasons.append("Account activity review requires user confirmation")

        # Determine decision based on risk score
        if risk_score >= 4:
            return {
                "decision": "REJECT",
                "confidence": 0.85,
                "reasoning": "; ".join(reasons) + ". Multiple PSD3 compliance concerns identified.",
                "risk_level": "HIGH",
                "valid": False,
                "ai_processed": False
            }
        elif risk_score >= 2:
            return {
                "decision": "APPROVE",
                "confidence": 0.75,
                "reasoning": "; ".join(reasons) + ". Approved with conditions per PSD3 requirements.",
                "risk_level": "MEDIUM",
                "valid": True,
                "ai_processed": False
            }
        else:
            return {
                "decision": "APPROVE",
                "confidence": 0.95,
                "reasoning": "Low-risk transaction compliant with PSD3 requirements.",
                "risk_level": "LOW",
                "valid": True,
                "ai_processed": False
            }

    def send_to_audit_agent(self, validation_result: Dict[str, Any], trigger_data: Dict[str, Any], correlation_id: str = None) -> str:
        """Send validation result to audit agent via A2A protocol"""
        try:
            audit_payload = {
                "validation_result": validation_result,
                "trigger_data": trigger_data,
                "source_agent": self.name,
                "timestamp": time.time()
            }

            correlation_id = self.a2a_queue.send_message(
                target_agent='AuditAgent',
                message_type='audit_log_request',
                payload=audit_payload,
                correlation_id=correlation_id
            )

            print(f"[{self.name}] Audit log sent via A2A (ID: {correlation_id})")
            return correlation_id

        except Exception as e:
            print(f"[{self.name}] Error sending audit log via A2A: {e}")
            return None

    def start_flask_server(self):
        """Start Flask server in a separate thread"""
        def run_server():
            self.server = make_server('0.0.0.0', 8080, self.app, threaded=True)
            self.server.serve_forever()

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        print(f"[{self.name}] Flask server started on port 8080")

def main():
    print("Starting Validation Agent...")
    agent = ValidationAgent()

    # Start Flask server
    agent.start_flask_server()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down Validation Agent...")
        if agent.server:
            agent.server.shutdown()

if __name__ == "__main__":
    main()
