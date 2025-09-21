#!/usr/bin/env python3
"""
Streamlit Dashboard for Open Banking Consent Choreographer

Demo dashboard showing agent activity, compliance metrics, and PSD3 consent flows.
Reads audit logs and displays real-time agent coordination.
"""

import streamlit as st
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


class DashboardDataManager:
    """Manages data for the Streamlit dashboard"""

    def __init__(self):
        self.audit_log_path = "/tmp/audit_log.json"
        self.agent_status_url = "http://agents-ns.svc.cluster.local:8080/status"  # Mock endpoint

    def get_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Read audit logs from audit agent API"""
        try:
            # Call audit agent API
            audit_url = "http://audit-agent-service.agents-ns.svc.cluster.local:8080/logs"
            response = requests.get(audit_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                logs = data.get("logs", [])
                # Return most recent logs
                return logs[-limit:] if logs else []
            else:
                print(f"Failed to get audit logs: HTTP {response.status_code}")
                return []
        except requests.RequestException as e:
            print(f"Error fetching audit logs from API: {e}")
            # Fallback to file reading
            return self._get_audit_logs_from_file(limit)
    
    def _get_audit_logs_from_file(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Read audit logs from file (fallback)"""
        try:
            logs = []
            with open(self.audit_log_path, 'r') as f:
                for line in f:
                    if line.strip():
                        logs.append(json.loads(line.strip()))
            # Return most recent logs
            return logs[-limit:]
        except FileNotFoundError:
            return []
        except Exception as e:
            st.error(f"Error reading audit logs: {e}")
            return []

    def get_agent_status(self) -> Dict[str, Any]:
        """Get status of all agents by checking their health endpoints"""
        agents = {
            'monitoring_agent': 'http://monitoring-agent-service.agents-ns.svc.cluster.local:8080/health',
            'validation_agent': 'http://validation-agent-service.agents-ns.svc.cluster.local:8080/health',
            'audit_agent': 'http://audit-agent-service.agents-ns.svc.cluster.local:8080/health'
        }

        status = {}
        for agent_name, health_url in agents.items():
            try:
                response = requests.get(health_url, timeout=3)
                if response.status_code == 200:
                    status[agent_name] = {
                        'status': 'running',
                        'last_seen': time.time(),
                        'health_data': response.json()
                    }
                else:
                    status[agent_name] = {
                        'status': 'unhealthy',
                        'last_seen': time.time(),
                        'error': f'HTTP {response.status_code}'
                    }
            except requests.RequestException as e:
                status[agent_name] = {
                    'status': 'unreachable',
                    'last_seen': time.time(),
                    'error': str(e)
                }

        return status

    def get_compliance_metrics(self) -> Dict[str, Any]:
        """Calculate compliance metrics from audit logs"""
        logs = self.get_audit_logs(1000)

        if not logs:
            return {
                'total_consents': 0,
                'approved_rate': 0.0,
                'rejected_rate': 0.0,
                'avg_confidence': 0.0,
                'risk_level': 'UNKNOWN'
            }

        total = len(logs)
        approved = len([log for log in logs if log.get('validation_result', {}).get('valid', False)])
        rejected = total - approved

        confidences = [log.get('validation_result', {}).get('confidence', 0.0) for log in logs]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # Calculate risk level based on rejection rate
        rejection_rate = rejected / total if total > 0 else 0
        if rejection_rate > 0.5:
            risk_level = 'HIGH'
        elif rejection_rate > 0.2:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'

        return {
            'total_consents': total,
            'approved_rate': approved / total if total > 0 else 0.0,
            'rejected_rate': rejection_rate,
            'avg_confidence': avg_confidence,
            'risk_level': risk_level
        }


def create_metrics_charts(logs: List[Dict[str, Any]]):
    """Create interactive charts for dashboard"""

    if not logs:
        return None, None, None

    # Convert to DataFrame for easier plotting
    df = pd.DataFrame(logs)

    # Timeline chart
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    timeline_data = df.groupby(df['timestamp'].dt.hour).size().reset_index(name='count')

    fig_timeline = px.line(timeline_data, x='timestamp', y='count',
                          title='Consent Requests Over Time',
                          labels={'timestamp': 'Hour', 'count': 'Requests'})

    # Validation results pie chart
    valid_counts = df['validation_result'].apply(lambda x: x.get('valid', False) if isinstance(x, dict) else False).value_counts()

    # Map boolean values to proper labels
    labels = []
    for valid_bool in valid_counts.index:
        labels.append('Approved' if valid_bool else 'Rejected')

    fig_pie = px.pie(values=valid_counts.values, names=labels,
                    title='Consent Validation Results')

    # Confidence distribution
    confidence_data = df['validation_result'].apply(lambda x: x.get('confidence', 0.0) if isinstance(x, dict) else 0.0)
    fig_confidence = px.histogram(confidence_data, nbins=10,
                                 title='AI Validation Confidence Distribution',
                                 labels={'value': 'Confidence Score', 'count': 'Frequency'})

    return fig_timeline, fig_pie, fig_confidence


def trigger_consent_ui():
    """UI for manually triggering consent requests"""
    col_trigger, col_status = st.columns([1, 2])
    
    with col_trigger:
        consent_type = st.selectbox(
            "Consent Type:",
            ["third_party_balance_access", "open_banking_consent", "third_party_transaction_sharing"],
            help="Select the type of consent to trigger for demo purposes"
        )
        
        user_id = st.text_input("User ID:", value=f"user_{int(time.time()) % 1000}", help="Demo user identifier")
        provider = st.selectbox(
            "Third Party Provider:",
            ["FinTech Corp", "Budget Tracker", "Investment App", "Lending Platform", "Insurance Provider"],
            help="Select the third-party service requesting consent"
        )
        
        if st.button("🚀 Trigger Consent", type="primary", use_container_width=True):
            # Call the consent trigger API
            try:
                response = requests.post(
                    "http://monitoring-api.agents-ns.svc.cluster.local:8080/trigger-consent",
                    timeout=5
                )
                if response.status_code == 200:
                    st.success(f"✅ Consent triggered successfully!\n\n**{consent_type}** for **{user_id}** with **{provider}**")
                    time.sleep(2)  # Give time for processing
                    st.rerun()  # Refresh to show new data
                else:
                    st.error(f"❌ Failed to trigger consent: HTTP {response.status_code}")
            except requests.RequestException as e:
                st.error(f"❌ Connection error: {e}")
    
    with col_status:
        st.markdown("### 📋 Trigger Status")
        st.info("Click 'Trigger Consent' to simulate a real-world consent request. The system will:\n\n1. **Monitoring Agent** detects the request\n2. **Validation Agent** applies PSD3 compliance rules\n3. **Audit Agent** logs the decision\n4. **Dashboard** shows real-time results")

def main():
    """Main Streamlit dashboard"""

    st.set_page_config(
        page_title="Open Banking Consent Choreographer",
        page_icon="🏦",
        layout="wide"
    )

    st.title("🏦 Open Banking Consent Choreographer")
    st.markdown("*PSD3 Compliant Multi-Agent System for Bank of Anthos*")

    # Initialize data manager
    data_manager = DashboardDataManager()

    # Sidebar with system info
    with st.sidebar:
        st.header("System Status")

        agent_status = data_manager.get_agent_status()

        for agent, status in agent_status.items():
            status_color = "🟢" if status['status'] == 'running' else "🔴"
            st.write(f"{status_color} {agent.replace('_', ' ').title()}")

        st.divider()

        # Compliance metrics
        metrics = data_manager.get_compliance_metrics()

        st.metric("Total Consents", metrics['total_consents'])
        st.metric("Approval Rate", f"{metrics['approved_rate']:.1%}")
        st.metric("Risk Level", metrics['risk_level'])

        # Refresh button
        if st.button("🔄 Refresh Data"):
            st.rerun()

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        st.header("Agent Activity Flow")

        # Agent coordination diagram (ASCII art for demo)
        st.code("""
        ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
        │ Monitoring Agent │ -> │ Validation Agent │ -> │   Audit Agent   │
        │                 │    │   (Gemini AI)    │    │                 │
        │ - API Polling   │    │ - Consent Check  │    │ - Log Reports   │
        │ - Trigger Detect│    │ - PSD3 Validate │    │ - Compliance    │
        └─────────────────┘    └──────────────────┘    └─────────────────┘
               │                        │                        │
               ▼                        ▼                        ▼
        ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
        │  ledger-writer  │    │   user-service   │    │   Dashboard     │
        │   /transactions │    │    /users        │    │   (Streamlit)   │
        └─────────────────┘    └──────────────────┘    └─────────────────┘
        """, language="text")

        # Manual Consent Trigger Section
        st.subheader("🎯 Manual Consent Trigger")
        trigger_consent_ui()
        st.divider()
        st.subheader("Recent Activity")

        logs = data_manager.get_audit_logs(10)

        if logs:
            for log in reversed(logs):  # Show newest first
                with st.expander(f"🔍 {log.get('trigger_data', {}).get('type', 'Unknown')} - {datetime.fromtimestamp(log.get('timestamp', 0)).strftime('%Y-%m-%d %H:%M:%S')}"):
                    col_a, col_b = st.columns(2)

                    with col_a:
                        st.write("**Trigger Details:**")
                        st.json(log.get('trigger_data', {}))

                    with col_b:
                        st.write("**Validation Result:**")
                        validation = log.get('validation_result', {})
                        status = "✅ Valid" if validation.get('valid', False) else "❌ Invalid"
                        st.write(f"**Status:** {status}")
                        st.write(f"**Confidence:** {validation.get('confidence', 0.0):.2f}")
                        st.write(f"**Reason:** {validation.get('reasoning', 'N/A')}")

                    st.write("**Compliance Notes:**")
                    for note in log.get('regulatory_notes', []):
                        st.write(f"• {note}")
        else:
            st.info("No audit logs available yet. Agents are initializing...")

    with col2:
        st.header("Compliance Metrics")

        # Create charts
        logs_all = data_manager.get_audit_logs(500)
        fig_timeline, fig_pie, fig_confidence = create_metrics_charts(logs_all)

        if fig_pie:
            st.plotly_chart(fig_pie, use_container_width=True)

        if fig_confidence:
            st.plotly_chart(fig_confidence, use_container_width=True)

        st.subheader("Key Statistics")

        if logs_all:
            # Trigger type distribution
            trigger_types = {}
            for log in logs_all:
                trigger_type = log.get('trigger_data', {}).get('type', 'unknown')
                trigger_types[trigger_type] = trigger_types.get(trigger_type, 0) + 1

            st.write("**Trigger Types:**")
            for trigger_type, count in trigger_types.items():
                st.write(f"• {trigger_type}: {count}")

        # System health
        st.subheader("System Health")

        # Mock real-time metrics
        import random
        cpu_usage = random.uniform(15, 45)
        memory_usage = random.uniform(20, 60)
        api_latency = random.uniform(50, 200)

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("CPU Usage", f"{cpu_usage:.1f}%")
        with col_b:
            st.metric("Memory Usage", f"{memory_usage:.1f}%")
        with col_c:
            st.metric("API Latency", f"{api_latency:.0f}ms")

    # Footer
    st.divider()
    st.markdown("""
    **GKE Turns 10 Hackathon Project** | *Open Banking Consent Choreographer*

    This system demonstrates PSD3-compliant consent management using multi-agent AI on GKE.
    All agents run autonomously, coordinating via A2A protocol to ensure regulatory compliance.
    """)


if __name__ == "__main__":
    main()
