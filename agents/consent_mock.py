#!/usr/bin/env python3
"""
PSD3 Consent Mock Utility for Bank of Anthos

This utility generates mock PSD3-compliant consent data for testing and development.
Can be used as a PR contribution to the main Bank of Anthos repository to add
consent management capabilities.

Usage:
    python consent_mock.py --generate-consent --user-id alice --purpose budgeting
    python consent_mock.py --validate-consent --consent-id consent_123
    python consent_mock.py --list-consents --user-id alice
"""

import json
import argparse
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import uuid


class PSD3ConsentManager:
    """Mock PSD3 Consent Manager for Bank of Anthos"""

    def __init__(self):
        # Mock consent database (in production, this would be a proper database)
        self.consents = {}
        self.consent_templates = {
            'budgeting': {
                'purpose': 'budgeting_app_access',
                'description': 'Access to transaction history for budgeting applications',
                'data_scope': ['transactions', 'balances'],
                'retention_period_days': 365,
                'revocable': True,
                'third_party_categories': ['budgeting', 'financial_planning']
            },
            'payment_initiation': {
                'purpose': 'payment_initiation',
                'description': 'Initiate payments on behalf of the user',
                'data_scope': ['accounts', 'balances'],
                'retention_period_days': 90,
                'revocable': True,
                'third_party_categories': ['payment_processor']
            },
            'account_info': {
                'purpose': 'account_information',
                'description': 'Access to account information and balances',
                'data_scope': ['accounts', 'balances'],
                'retention_period_days': 180,
                'revocable': True,
                'third_party_categories': ['account_aggregator', 'financial_advisor']
            }
        }

    def generate_consent(self, user_id: str, purpose: str, third_party_name: str = None) -> Dict[str, Any]:
        """Generate a new PSD3-compliant consent"""

        if purpose not in self.consent_templates:
            raise ValueError(f"Unknown consent purpose: {purpose}")

        template = self.consent_templates[purpose]

        consent = {
            'consent_id': f"consent_{uuid.uuid4().hex[:16]}",
            'user_id': user_id,
            'third_party_name': third_party_name or f"mock_{purpose}_app",
            'purpose': template['purpose'],
            'description': template['description'],
            'data_scope': template['data_scope'],
            'permissions': self._generate_permissions(template),
            'valid_from': datetime.utcnow().isoformat() + 'Z',
            'valid_until': (datetime.utcnow() + timedelta(days=template['retention_period_days'])).isoformat() + 'Z',
            'revocable': template['revocable'],
            'status': 'active',
            'psd3_compliance': {
                'article_65_compliant': True,
                'article_66_compliant': True,
                'article_67_compliant': True,
                'consent_granularity': 'specific',
                'data_minimization': True,
                'purpose_limitation': True
            },
            'audit_trail': [{
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'action': 'consent_granted',
                'actor': 'user',
                'details': f"User {user_id} granted consent for {purpose}"
            }],
            'metadata': {
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'version': '1.0',
                'consent_framework': 'PSD3'
            }
        }

        self.consents[consent['consent_id']] = consent
        return consent

    def _generate_permissions(self, template: Dict[str, Any]) -> List[str]:
        """Generate specific permissions based on template"""
        permissions = []

        for data_type in template['data_scope']:
            permissions.extend([
                f"read:{data_type}",
                f"access:{data_type}"
            ])

        for category in template['third_party_categories']:
            permissions.append(f"share:{category}")

        return permissions

    def validate_consent(self, consent_id: str, requested_action: str = None) -> Dict[str, Any]:
        """Validate if a consent is active and allows requested action"""

        if consent_id not in self.consents:
            return {
                'valid': False,
                'reason': 'Consent not found',
                'compliant': False
            }

        consent = self.consents[consent_id]

        # Check if consent is expired
        valid_until = datetime.fromisoformat(consent['valid_until'][:-1])
        if datetime.utcnow() > valid_until:
            return {
                'valid': False,
                'reason': 'Consent expired',
                'compliant': True  # Expired gracefully
            }

        # Check if consent is revoked
        if consent['status'] != 'active':
            return {
                'valid': False,
                'reason': f"Consent status: {consent['status']}",
                'compliant': True
            }

        # Check specific action permissions
        if requested_action:
            allowed = self._check_permission(consent, requested_action)
            if not allowed:
                return {
                    'valid': False,
                    'reason': f"Action not permitted: {requested_action}",
                    'compliant': True
                }

        return {
            'valid': True,
            'reason': 'Consent valid',
            'compliant': True,
            'expires_at': consent['valid_until']
        }

    def _check_permission(self, consent: Dict[str, Any], action: str) -> bool:
        """Check if consent allows specific action"""
        return any(action.startswith(perm.split(':')[0]) for perm in consent['permissions'])

    def revoke_consent(self, consent_id: str, reason: str = None) -> bool:
        """Revoke a consent (PSD3 Article 65 compliance)"""

        if consent_id not in self.consents:
            return False

        consent = self.consents[consent_id]

        if not consent['revocable']:
            return False

        consent['status'] = 'revoked'
        consent['audit_trail'].append({
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'action': 'consent_revoked',
            'actor': 'user',
            'details': reason or 'User revoked consent'
        })

        return True

    def list_consents(self, user_id: str = None, status: str = None) -> List[Dict[str, Any]]:
        """List consents with optional filtering"""

        consents = list(self.consents.values())

        if user_id:
            consents = [c for c in consents if c['user_id'] == user_id]

        if status:
            consents = [c for c in consents if c['status'] == status]

        return consents

    def get_consent_summary(self, user_id: str) -> Dict[str, Any]:
        """Get consent summary for a user"""

        user_consents = self.list_consents(user_id=user_id)

        active_consents = [c for c in user_consents if c['status'] == 'active']
        revoked_consents = [c for c in user_consents if c['status'] == 'revoked']

        return {
            'user_id': user_id,
            'total_consents': len(user_consents),
            'active_consents': len(active_consents),
            'revoked_consents': len(revoked_consents),
            'consent_purposes': list(set(c['purpose'] for c in active_consents)),
            'third_parties': list(set(c['third_party_name'] for c in active_consents))
        }


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description='PSD3 Consent Mock Utility for Bank of Anthos')
    parser.add_argument('--generate-consent', action='store_true', help='Generate a new consent')
    parser.add_argument('--validate-consent', action='store_true', help='Validate an existing consent')
    parser.add_argument('--revoke-consent', action='store_true', help='Revoke an existing consent')
    parser.add_argument('--list-consents', action='store_true', help='List consents')
    parser.add_argument('--consent-summary', action='store_true', help='Get consent summary for user')

    parser.add_argument('--user-id', help='User ID for the operation')
    parser.add_argument('--consent-id', help='Consent ID for validation/revocation')
    parser.add_argument('--purpose', choices=['budgeting', 'payment_initiation', 'account_info'],
                       help='Purpose for consent generation')
    parser.add_argument('--third-party', help='Third party name')
    parser.add_argument('--action', help='Action to validate permission for')
    parser.add_argument('--status', choices=['active', 'revoked'], help='Filter by consent status')
    parser.add_argument('--output', choices=['json', 'pretty'], default='pretty',
                       help='Output format')

    args = parser.parse_args()

    manager = PSD3ConsentManager()

    try:
        if args.generate_consent:
            if not args.user_id or not args.purpose:
                parser.error("--generate-consent requires --user-id and --purpose")

            consent = manager.generate_consent(
                user_id=args.user_id,
                purpose=args.purpose,
                third_party_name=args.third_party
            )

            if args.output == 'json':
                print(json.dumps(consent, indent=2))
            else:
                print("✅ Consent Generated Successfully!")
                print(f"Consent ID: {consent['consent_id']}")
                print(f"User: {consent['user_id']}")
                print(f"Purpose: {consent['purpose']}")
                print(f"Third Party: {consent['third_party_name']}")
                print(f"Valid Until: {consent['valid_until']}")
                print(f"Status: {consent['status']}")

        elif args.validate_consent:
            if not args.consent_id:
                parser.error("--validate-consent requires --consent-id")

            result = manager.validate_consent(args.consent_id, args.action)

            if args.output == 'json':
                print(json.dumps(result, indent=2))
            else:
                status = "✅ Valid" if result['valid'] else "❌ Invalid"
                print(f"Consent Validation: {status}")
                print(f"Reason: {result['reason']}")
                if result.get('expires_at'):
                    print(f"Expires: {result['expires_at']}")

        elif args.revoke_consent:
            if not args.consent_id:
                parser.error("--revoke-consent requires --consent-id")

            success = manager.revoke_consent(args.consent_id, "CLI revocation")

            if args.output == 'json':
                print(json.dumps({'success': success}, indent=2))
            else:
                if success:
                    print("✅ Consent revoked successfully!")
                else:
                    print("❌ Failed to revoke consent")

        elif args.list_consents:
            consents = manager.list_consents(user_id=args.user_id, status=args.status)

            if args.output == 'json':
                print(json.dumps(consents, indent=2))
            else:
                print(f"Found {len(consents)} consents:")
                for consent in consents:
                    print(f"  • {consent['consent_id']}: {consent['purpose']} ({consent['status']})")

        elif args.consent_summary:
            if not args.user_id:
                parser.error("--consent-summary requires --user-id")

            summary = manager.get_consent_summary(args.user_id)

            if args.output == 'json':
                print(json.dumps(summary, indent=2))
            else:
                print(f"Consent Summary for {args.user_id}:")
                print(f"  Total Consents: {summary['total_consents']}")
                print(f"  Active: {summary['active_consents']}")
                print(f"  Revoked: {summary['revoked_consents']}")
                print(f"  Purposes: {', '.join(summary['consent_purposes'])}")
                print(f"  Third Parties: {', '.join(summary['third_parties'])}")

        else:
            parser.print_help()

    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
