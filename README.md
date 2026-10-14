# Network Automation & DNS Resolution Revision Project (Task 1)

This repository contains a suite of Python automation scripts, device metrics, and orchestration tools engineered to manage, monitor, verify, and remediate core network services and DNS infrastructures. The codebase interfaces with a virtualized testbed environment to execute health checks, programmatic configurations, and asynchronous stakeholder alerting.

## 🚀 Core Features & Workflows
*   **Infrastructure Diagnostic Checks:** Programmatic ICMP reachability verification across inventory nodes.
*   **DNS Infrastructure Lifecycle Automation:** Scripts to test connection states, parse query resolutions, modify parameters, and programmatically restart active DNS service contexts.
*   **Automated Verification Pipelines:** Multi-stage verification checks that evaluate if freshly pushed DNS records and modifications have properly resolved.
*   **Stakeholder Communication & Incident Alerting:** Scripts designed to dispatch transaction updates and notification alerts upon verification or service disruptions.
*   **GNS3 Testbed Orchestration:** An automated orchestration entry point to launch and synchronize the underlying network topography.

---

## 📂 Repository Directory Structure

```text
d522-Task-1-revision/
│
├── network_devices.csv             # Structured asset database tracking target inventory
├── start_gns3_network.py           # Top-level script to orchestrate the virtual lab environment
├── git-history.txt                 # Repository transaction log
├── detailed-commit-history.txt    # Granular engineering change log and file histories
│
├── 📁 Automated Diagnostics & Tracing
│   ├── b1_icmp.py                  # Core ICMP ping reachability verification utility
│   ├── b2_dns_connect_script.py    # Baseline socket connection check targeting DNS servers
│   └── b2_dns_status.py            # Diagnostic script to extract live health metrics from DNS nodes
│
├── 📁 Services Configuration & Control
│   ├── d1_connect_dns.py           # Script handling authentication and remote node execution
│   └── d2_restart_dns_script.py    # Programmatic service daemon restart utility for mitigation
│
├── 📁 Deployment Verification Pipelines
│   ├── d4_dns_settings_resolved.py # Pipeline step validating resolved record states
│   ├── d4_verify_dns_settings.py   # State tracking check evaluating standard setting alignments
│   └── d4_verify_new_dns.py        # Post-change verification script targeting updated zones
│
├── 📁 Stakeholder Notification & Alerting
│   ├── c1_email_created.py         # Formats and prepares account/ticket initiation emails
│   ├── c1_email_verified.py        # Validates email formatting and confirmation logic
│   ├── c2_alerts_script.py         # Incident condition trigger script generating alert payloads
│   └── e_resolution_email_script.py# Formats final remediation/resolution summaries for users
│
└── 📁 .vscode/
    └── settings.json               # Local environment path constraints and workspace configs
```

---

## 📑 Detailed Script Breakdowns

### 🌐 Network Diagnostics & Service Maintenance
*   **`b1_icmp.py`**
    Implements core connectivity pings targeting specific device IPs listed in the device inventory, establishing a baseline map of network plane reachability.
*   **`b2_dns_connect_script.py` & `b2_dns_status.py`**
    Performs specialized diagnostics checking both basic Layer 4 socket handshakes on Port 53 and higher-level request timeouts to report server status flags.
*   **`d2_restart_dns_script.py`**
    Used as an automated remediation step. If verification checks report an unhealthy state, this script remotely safely restarts the target system's DNS service daemon.

### 🛡️ Configuration Push Verification
*   **`d4_verify_new_dns.py` & `d4_dns_settings_resolved.py`**
    Acts as the post-change validation layer. Queries the DNS service context directly after configurations are applied to confirm that name-to-IP resolutions accurately match desired change parameters.

### 📨 Asynchronous Email Delivery & Notification Engine
*   **`c2_alerts_script.py`**
    Monitors workflow state failures and generates distinct warning payloads when network links or resolution metrics fall below established operation thresholds.
*   **`e_resolution_email_script.py`**
    Executes automatically upon successful verification validation. Prepares and dispatches an informative project summary to target stakeholders clarifying that the network anomalies have been resolved.

---

## ⚙️ Dependencies & Local Setup
1. **Device Inventory Execution:** The automation engine queries device objects directly out of the tracked `network_devices.csv` manifest file. Ensure target parameters remain accurate to your environment.
2. **Environment Cache:** Local compiled python configurations (`.pyc` runtimes) generated during simulation cycles are isolated within internal `__pycache__` footprints to keep execution clean.
