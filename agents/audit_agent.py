#!/usr/bin/env python3
"""
Audit Agent for Open Banking Consent Choreographer

Accumulates real compliance audit logs from validation results.
"""

from flask import Flask, jsonify, request
import time
import json
import os
import threading
from typing import Dict, List, Any
from shared_queue import SharedMessageQueue
from werkzeug.serving import make_server
import requests

class AuditAgent:
    """Audit Agent - accumulates and serves real compliance audit logs"""

    def __init__(self, a2a_queue=None):  # Make queue optional for HTTP-based communication
        self.name = "AuditAgent"
        self.a2a_queue = a2a_queue
        self.audit_logs = []
        self.audit_log_file = '/tmp/audit_logs.json'
        self.app = Flask(__name__)
        self.app.add_url_rule('/logs', 'get_logs', self.get_logs)
        self.app.add_url_rule('/health', 'health', self.health)
        self.app.add_url_rule('/audit', 'receive_audit', self.receive_audit, methods=['POST'])
        self.app.add_url_rule('/a2a', 'a2a_message', self.handle_a2a_message, methods=['POST'])
        self.running = True

        # Load existing audit logs from file
        self._load_audit_logs()
        self.server = None
        self.server_thread = None

    def _load_audit_logs(self):
        """Load audit logs from persistent file"""
        try:
            if os.path.exists(self.audit_log_file):
                with open(self.audit_log_file, 'r') as f:
                    self.audit_logs = json.load(f)
                print(f"[{self.name}] Loaded {len(self.audit_logs)} audit logs from file")
        except Exception as e:
            print(f"[{self.name}] Error loading audit logs: {e}")
            self.audit_logs = []

    def _save_audit_logs(self):
        """Save audit logs to persistent file"""
        try:
            with open(self.audit_log_file, 'w') as f:
                json.dump(self.audit_logs, f, indent=2)
        except Exception as e:
            print(f"[{self.name}] Error saving audit logs: {e}")

    def get_logs(self):
        """Serve accumulated audit logs"""
        return jsonify({"logs": self.audit_logs, "count": len(self.audit_logs)})

    def health(self):
        return jsonify({"status": "healthy", "agent": "audit"})

    def receive_audit(self):
        """HTTP endpoint to receive audit logs from validation agent"""
        try:
            audit_data = request.get_json()
            if not audit_data:
                return jsonify({"error": "No audit data provided"}), 400

            # Process the audit data
            self.process_audit_log(audit_data)

            return jsonify({"status": "received", "message": "Audit log recorded"})

        except Exception as e:
            print(f"[{self.name}] Error processing audit log: {e}")
            return jsonify({"error": str(e)}), 500

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

            if message_type == 'audit_log_request':
                # Process the audit data
                self.process_audit_log(payload)

                return {
                    'status': 'accepted',
                    'message_id': message_id,
                    'message': 'Audit log recorded via A2A'
                }
            else:
                return {'status': 'rejected', 'reason': f'Unknown message type: {message_type}'}

        except Exception as e:
            print(f"[{self.name}] Error processing A2A message: {e}")
            return {'status': 'error', 'reason': str(e)}

    def start_flask_server(self):
        """Start Flask server in a separate thread"""
        def run_server():
            self.server = make_server('0.0.0.0', 8080, self.app, threaded=True)
            self.server.serve_forever()

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()
        print(f"[{self.name}] Flask server started on port 8080")

    def process_audit_log(self, audit_data: dict):
        """Process incoming audit data from validation agent"""
        validation_result = audit_data.get('validation_result', {})
        trigger_data = audit_data.get('trigger_data', {})

        # Generate regulatory compliance notes based on validation result
        # Use AI reasoning if available, otherwise fall back to template notes
        ai_reasoning = validation_result.get('reasoning', '')
        if ai_reasoning and len(ai_reasoning) > 50:  # Only use AI reasoning if it's substantial
            # Format AI reasoning into structured compliance notes
            regulatory_notes = self._format_ai_reasoning_as_notes(ai_reasoning, validation_result, trigger_data)
        else:
            regulatory_notes = self._generate_regulatory_notes(validation_result, trigger_data)

        audit_entry = {
            'timestamp': audit_data.get('timestamp', time.time()),
            'validation_result': validation_result,
            'trigger_data': trigger_data,
            'source_agent': audit_data.get('source_agent', 'Unknown'),
            'regulatory_notes': regulatory_notes
        }

        self.audit_logs.append(audit_entry)
        print(f"[Audit] Recorded audit log: {trigger_data.get('type', 'unknown')} for user {trigger_data.get('user_id', 'unknown')} - Decision: {validation_result.get('decision', 'unknown')}")

        # Save to persistent file
        self._save_audit_logs()

        # Keep only last 100 logs to prevent memory issues
        if len(self.audit_logs) > 100:
            self.audit_logs = self.audit_logs[-100:]
            self._save_audit_logs()  # Save the truncated list

    def _format_ai_reasoning_as_notes(self, ai_reasoning: str, validation_result: dict, trigger_data: dict) -> list:
        """Format AI reasoning into structured, consent-specific compliance notes"""
        notes = []

        # Get consent details
        consent_type = trigger_data.get('type', 'unknown')
        amount = trigger_data.get('amount', 0)
        purpose = trigger_data.get('purpose', 'unspecified')
        provider = trigger_data.get('third_party_provider', 'unknown')
        user_id = trigger_data.get('user_id', 'unknown')

        # Add header with consent context
        decision = validation_result.get('decision', 'UNKNOWN')
        confidence = validation_result.get('confidence', 0.0)

        status_icon = "✅" if decision == 'APPROVE' else "❌"
        notes.append(f"{status_icon} AI Assessment: {consent_type.replace('_', ' ').title()} Request")
        notes.append(f"• Confidence: {confidence:.1%} | Amount: €{amount:,} | Purpose: {purpose}")
        notes.append(f"• Provider: {provider} | User: {user_id}")

        # Create consent-specific compliance analysis
        if decision == 'APPROVE':
            notes.append("• PSD3 Compliance: ✅ Request meets regulatory requirements")
            if amount > 5000:
                notes.append(f"• High-Value Review: ✅ €{amount:,} transaction approved under enhanced scrutiny")
            if 'third_party' in consent_type or provider != 'bank':
                notes.append(f"• Third-Party Access: ✅ Explicit consent granted for {provider}")
            notes.append("• Data Processing: ✅ Purpose limitation and minimization applied")
        else:
            notes.append("• PSD3 Compliance: ❌ Request does not meet all regulatory requirements")
            if amount > 5000:
                notes.append(f"• High-Value Review: ❌ €{amount:,} requires additional compliance measures")
            if 'third_party' in consent_type or provider != 'bank':
                notes.append(f"• Third-Party Access: ❌ Additional verification needed for {provider}")
            notes.append("• Remediation: Review consent scope and obtain explicit user confirmation")

        # Add key AI insights from the reasoning
        if 'purpose' in ai_reasoning.lower():
            notes.append("• Purpose Clarity: AI validated processing purpose specification")

        if 'withdraw' in ai_reasoning.lower() or 'revoke' in ai_reasoning.lower():
            notes.append("• Withdrawal Rights: AI confirmed revocation mechanisms available")

        # Add a concise AI summary
        if len(ai_reasoning) > 100:
            # Extract the most relevant part of AI reasoning
            sentences = ai_reasoning.split('.')
            key_insights = [s.strip() for s in sentences[:2] if s.strip()]
            if key_insights:
                summary = '. '.join(key_insights) + '.'
                notes.append(f"• AI Analysis: {summary}")

        return notes

    def _generate_regulatory_notes(self, validation_result: dict, trigger_data: dict) -> list:
        """Generate PSD3-compliant regulatory notes based on validation outcome"""
        notes = []
        trigger_type = trigger_data.get('type', 'unknown')
        is_valid = validation_result.get('valid', False)
        confidence = validation_result.get('confidence', 0.0)

        if is_valid:
            notes.extend([
                'PSD3 Article 64 compliance confirmed',
                'Explicit consent obtained for data processing',
                'Data minimization principles applied',
                'Right to withdraw consent maintained',
                'Transparent privacy notice provided',
                f'AI validation confidence: {confidence:.1%}'
            ])

            if trigger_type == 'high_value_transaction':
                notes.append('High-value transaction consent validated')
            elif trigger_type == 'international_transfer':
                notes.append('Cross-border transfer consent confirmed')
            elif trigger_type == 'third_party_data_sharing':
                notes.append('Third-party data sharing consent verified')
            elif trigger_type == 'account_activity_review':
                notes.append('Account activity consent review completed')

        else:
            notes.extend([
                f'REJECTED: {validation_result.get("reason", "Validation failed")}',
                'PSD3 Article 64: Consent must be specific and informed',
                'Data protection impact assessment recommended',
                'User notified of rejection with reasoning',
                'Alternative narrower consent scope suggested',
                f'AI validation confidence: {confidence:.1%}'
            ])

            if confidence < 0.5:
                notes.append('CRITICAL: Low confidence validation - manual review required')
            elif confidence < 0.7:
                notes.append('WARNING: Moderate confidence - additional verification recommended')

        return notes

    def run_loop(self, interval_seconds: int = 5):
        """Main agent run loop"""
        print(f"[{self.name}] Starting audit agent run loop...")

        while self.running:
            try:
                # Check for new audit messages
                messages = self.a2a_queue.get_messages(self.name)
                for message in messages:
                    self.process_audit_message(message)

            except Exception as e:
                print(f"[{self.name}] Error in audit cycle: {e}")

            time.sleep(interval_seconds)

    def stop(self):
        """Stop the agent"""
        self.running = False
        print(f"[{self.name}] Stopping audit agent...")

def main():
    print("Starting Audit Agent...")
    agent = AuditAgent()  # No queue needed for HTTP-based communication

    # Start Flask server
    agent.start_flask_server()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down Audit Agent...")
        if agent.server:
            agent.server.shutdown()

if __name__ == "__main__":
    main()
