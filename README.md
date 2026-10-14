=======================================================================================================================
# Network Automation & DNS Resolution Revision Project (Task 1)
=======================================================================================================================


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

=======================================================================================================================
## 📖 Usage Guide
=======================================================================================================================


All scripts within this automation suite are executed via the command-line interface. The core execution engine systematically processes the structured target assets tracked within `network_devices.csv`.

### 🎛️ Prerequisites & Environment Setup

Before executing any script, ensure your Python virtual environment is active and all required dependencies are installed:

```bash
# Activate your virtual environment (Windows template)
.venv\Scripts\activate

# Install required networking, DNS, and automation libraries
pip install netmiko dnspython paramiko
```

---

### 🔍 1. Running Core Infrastructure Diagnostics

The verification modules support both complete automated matrix scanning and targeted single-node validation.

#### A. Comprehensive ICMP Reachability Scan
To ping all devices tracked inside the `network_devices.csv` manifest file in a single sequence:
```bash
python b1_icmp.py
```

#### B. Targeted Single-Host Ping Check
To bypass the CSV matrix and target a specific network node directly, append the target destination host or IP address as an argument:
```bash
python b1_icmp.py --target 192.168.10.1
```

#### C. Running Socket and State Verification Diagnostics
To evaluate Layer 4 network connections and query response states on target DNS daemons:
```bash
# Validate that the DNS service port (Port 53) is answering socket handshakes
python b2_dns_connect_script.py

# Query status registers and fetch live runtime flags
python b2_dns_status.py
```

---

### ⚙️ 2. Executing Remote Changes & Service Remediation

These scripts handle authenticated remote access layer commands to apply administrative changes or trigger service recoveries.

#### A. Push DNS Configuration States
To log into your infrastructure targets and apply desired lookup settings:
```bash
python d1_connect_dns.py
```

#### B. Programmatic Mitigation (Service Restart Trigger)
If monitoring loops detect an inconsistent or unresponsive state, execute the service daemon reset task directly:
```bash
python d2_restart_dns_script.py
```

---

### 🧪 3. Running Post-Change Verification Pipelines

Once changes have been applied to your name servers, execute the verification pipeline sequentially to ensure configuration consistency.

```bash
# Step 1: Run standard settings validation checks
python d4_verify_dns_settings.py

# Step 2: Query modified zone files to check propagation
python d4_verify_new_dns.py

# Step 3: Confirm the target records resolve correctly across the network plane
python d4_dns_settings_resolved.py
```

---

### 📩 4. Manual Incident Payloads & Communication Alerts

While the notification engine hooks directly into your main automation scripts, you can manually trigger system alerts and client notification logs for debugging or system maintenance.

```bash
# Broadcast an incident warning alert payload to the system logs
python c2_alerts_script.py --level CRITICAL --message "Core DNS Node non-responsive"

# Dispatch a resolution brief email out to target stakeholder mail queues
python e_resolution_email_script.py
```

---

### 📋 5. Troubleshooting & Exit Codes

The core automation scripts return clean, actionable system status flags upon termination to facilitate integration into larger staging engines or cron triggers:

| Exit Code | Pipeline Meaning | System Action Required |
| :--- | :--- | :--- |
| **`0`** | **Success / Passed** | All targets responded; configurations matched baseline expectations. |
| **`1`** | **Diagnostic Failure** | ICMP or Port 53 socket handshakes timed out. Check hardware state. |
| **`2`** | **Verification Mismatch** | Settings pushed but lookup resolution did not match the expected record string. |
| **`3`** | **Authentication Fault** | Secure socket login failed. Verify user credentials inside your configuration variables. |


=======================================================================================================================
## 🚀 CI/CD Automation (Jenkins Pipeline Staging)
=======================================================================================================================


To enforce continuous infrastructure verification, this project is designed to run automatically within a CI/CD pipeline tool like **Jenkins**. The following declarative Jenkinsfile automates the deployment validation process every time a configuration change is staged or pushed.

### 📋 Pipeline Automation Topology

The automated pipeline steps through four strict execution gates:
1.  **Environment Sync:** Provisions a clean virtual environment and installs tracking dependencies.
2.  **Pre-Flight Diagnostics:** Runs the ICMP and connection checks to verify the target hardware nodes are awake.
3.  **Remediation Loop:** Handles automatic network recoveries if a core service is caught in a down state.
4.  **Post-Deployment Verification:** Ensures that any newly pushed configuration details parse and resolve correctly.

---

### 🛠️ Declarative Jenkinsfile Configuration

Create a file named `Jenkinsfile` in the root of your repository and inject the following pipeline structure:

```groovy
pipeline {
    agent any

    environment {
        // Enforces colored terminal outputs and points python to your workspace modules
        PYTHONUNBUFFERED = '1'
        PYTHONPATH       = "${WORKSPACE}"
    }

    stages {
        stage('1. Provision & Sync Dependencies') {
            steps {
                echo 'Initializing virtual environment and synchronizing automation libraries...'
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install netmiko dnspython paramiko
                '''
            }
        }

        stage('2. Pre-Flight Diagnostics') {
            steps {
                echo 'Scanning network fabric reachability metrics...'
                sh '''
                    . .venv/bin/activate
                    python b1_icmp.py
                    python b2_dns_connect_script.py
                '''
            }
        }

        stage('3. Run Post-Deployment Verification') {
            steps {
                echo 'Querying DNS nodes to confirm lookups resolve accurately...'
                sh '''
                    . .venv/bin/activate
                    python d4_verify_dns_settings.py
                    python d4_verify_new_dns.py
                    python d4_dns_settings_resolved.py
                '''
            }
        }
    }

    post {
        success {
            echo 'Pipeline Passed: Configuration is verified and healthy.'
            sh '''
                . .venv/bin/activate
                python e_resolution_email_script.py
            '''
        }
        failure {
            echo 'Pipeline Broken: Diagnostic mismatch or unresponsiveness caught during staging!'
            sh '''
                . .venv/bin/activate
                python c2_alerts_script.py --level CRITICAL --message "Jenkins Build #${BUILD_NUMBER} Failed during infrastructure staging."
            '''
        }
    }
}
```

---

### ⚙️ How to Hook this up in Jenkins

1. **Create a New Job:** Inside your Jenkins dashboard, select **New Item**, choose **Pipeline**, and name it `network-automation-staging`.
2. **Configure SCM Polling:** Scroll to the **Pipeline** configuration section down at the bottom. Switch the **Definition** dropdown menu from *Pipeline script* to **Pipeline script from SCM**.
3. **Link Your Code:** Select **Git**, input your repository URL, and specify your production branch (e.g., `*/main` or `*/Completed-Healthcare-Network-Capstone`).
4. **Build Triggers:** Check the box next to **Poll SCM** and input `H/15 * * * *` to have Jenkins automatically check your repository for infrastructure code changes every 15 minutes.
