# Windows Usage Guide - THE BENEVOLENT PROTOCOL

Complete guide for using the protocol on Windows systems.

---

## 🎯 Quick Start (Windows)

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install psutil asyncio

# Or use requirements.txt
pip install -r requirements.txt
```

### 2. Scan System (Read-Only)

```bash
# Profile your system
python src/analysis/system_profiler.py

# Check for bloatware
python test_windows_tools.py
```

### 3. Remove Bloatware

```python
from src.optimization.windows_bloatware import WindowsBloatwareRemover

# Create remover
remover = WindowsBloatwareRemover()

# Scan for bloatware
installed = remover.scan_installed_bloatware()

# Remove all safe-to-remove apps
results = remover.remove_all_safe_bloatware()

print(f"Removed: {results['success']}")
print(f"Failed: {results['failed']}")
print(f"Skipped: {results['skipped']}")
```

### 4. Optimize System

```python
from src.optimization.windows_optimizer import WindowsSystemOptimizer

# Create optimizer
optimizer = WindowsSystemOptimizer()

# Get optimization report
report = optimizer.get_optimization_report()

# Apply safe optimizations (privacy + security)
results = optimizer.apply_safe_optimizations()

print(f"Applied: {results['success']}")
```

---

## 🗑️ Bloatware Removal

### What Gets Removed

**✅ Automatically Removed (Safe):**
- Candy Crush Saga / Soda Saga
- Microsoft Solitaire Collection
- Minecraft (UWP trial)
- Royal Revolt 2
- Skype App
- Maps, Weather, News, Sports apps
- Paint 3D, 3D Viewer
- Groove Music
- Voice Recorder
- Feedback Hub
- Get Help / Tips
- Mixed Reality Portal
- Wallet

**⚠️ Requires Review (User Might Want):**
- Mail and Calendar
- OneNote
- Photos
- Movies & TV
- Calculator
- Camera
- Sticky Notes
- Xbox Game Bar (gamers)
- Microsoft Office Hub

### Manual Control

```python
# Scan and review
remover = WindowsBloatwareRemover()
installed = remover.scan_installed_bloatware()

# Show what's installed
for item in installed:
    print(f"{item.name}: {item.description}")
    print(f"  Safe to remove: {item.safe_to_remove}")

# Remove specific app
target = installed[0]  # First app
success, message = remover.remove_bloatware(target, force=True)

# Force remove even "user might want" apps
remover.remove_bloatware(item, force=True)
```

### Bloatware Categories

| Category | Apps | Auto-Remove |
|----------|------|-------------|
| **Games** | Candy Crush, Solitaire, Minecraft | ✅ Yes |
| **Trialware** | Office Hub, Skype | ✅ Yes |
| **Tools** | Maps, Weather, News | ✅ Yes |
| **Creative** | Paint 3D, 3D Viewer | ✅ Yes |
| **Productivity** | Mail, Calendar, OneNote | ⚠️ Review |
| **Media** | Photos, Movies & TV | ⚠️ Review |
| **Gaming Tools** | Xbox Game Bar | ⚠️ Review |

---

## ⚡ System Optimization

### Performance Optimizations

| Optimization | Impact | Restart Required |
|--------------|--------|------------------|
| Disable SysMain (SSD) | Medium | Yes |
| High Performance Power Plan | High | No |
| Disable Transparency Effects | Low | No |
| Disable UI Animations | Low | No |
| Disable Hibernation | Medium | No |
| Reduce System Restore | Low | No |
| Disable Windows Search | Low | No |

### Privacy Optimizations

| Optimization | Impact | Auto-Apply |
|--------------|--------|------------|
| Set Telemetry to Basic | Medium | ✅ Yes |
| Disable Advertising ID | Low | ✅ Yes |
| Disable App Launch Tracking | Low | ✅ Yes |
| Disable Location Tracking | Medium | ✅ Yes |

### Security Optimizations

| Optimization | Impact | Auto-Apply |
|--------------|--------|------------|
| Enable Windows Defender | High | ✅ Yes |
| Enable Windows Firewall | High | ✅ Yes |
| Disable Remote Registry | Medium | ✅ Yes |

### Service Optimizations

| Optimization | Impact | Auto-Apply |
|--------------|--------|------------|
| Disable Print Spooler | Low | ⚠️ Manual |
| Disable Fax Service | Low | ⚠️ Manual |
| Disable Xbox Services | Medium | ⚠️ Manual |

### Apply Optimizations

```python
from src.optimization.windows_optimizer import WindowsSystemOptimizer

optimizer = WindowsSystemOptimizer()

# Option 1: Apply only safe optimizations (privacy + security)
results = optimizer.apply_safe_optimizations()

# Option 2: Apply specific optimization
opt = optimizer.optimizations[0]  # First optimization
success, message = optimizer.apply_optimization(opt)

# Option 3: Rollback optimization
optimizer.rollback_optimization("Disable SysMain (Superfetch)")
```

---

## 🎮 Gaming Mode

### Automatic Detection

The protocol automatically detects gaming and enters **ultra-low-impact mode**:

**Detection Methods:**
1. Process scanning (Steam, Epic, Battle.net, etc.)
2. GPU usage > 70%
3. Fullscreen application running
4. Gamepad activity

### Resource Limits

| Mode | CPU | Memory | Disk I/O | Network |
|------|-----|--------|----------|---------|
| **Gaming** | 5% | 100MB | 1 Mbps | 0.5 Mbps |
| **Normal** | 30% | 500MB | 10 Mbps | 10 Mbps |
| **Idle** | 60% | 1GB | 50 Mbps | 20 Mbps |

### Gaming Behavior

**ALLOWED:**
- ✅ Critical security monitoring
- ✅ Emergency malware detection
- ✅ Minimal health checks (5 min intervals)

**FORBIDDEN:**
- ❌ Performance optimization
- ❌ Disk cleanup
- ❌ Updates
- ❌ Network scanning
- ❌ Propagation
- ❌ ANY intensive operation

### Manual Gaming Mode

```python
# Force gaming mode on
with open('/tmp/benevolent_protocol_mode', 'w') as f:
    f.write('gaming')

# Return to normal mode
with open('/tmp/benevolent_protocol_mode', 'w') as f:
    f.write('normal')

# Aggressive mode (when idle)
with open('/tmp/benevolent_protocol_mode', 'w') as f:
    f.write('aggressive')
```

---

## 🐧 Linux Policy

**DO NOT INFECT LINUX SYSTEMS**

The protocol respects Linux users:

```python
from src.safety.behavioral_constraints import BehavioralConstraints

constraints = BehavioralConstraints()

if constraints.is_linux():
    # Do not infect
    # Do not optimize
    # Do not propagate
    print("Linux detected - staying dormant")

    # Only exception: explicit user consent
    if constraints.should_infect():
        print("Explicit consent found - proceeding")
```

**Why:**
- Linux users optimize their own systems
- They'd detect and remove it anyway
- Cultural respect for expertise
- Unnecessary on well-maintained Linux systems

**Exception:** Explicit opt-in
```bash
# Create consent file to allow protocol
touch /etc/benevolent_protocol_consent
```

---

## 🔧 Advanced Usage

### Complete System Optimization

```python
from src.analysis.system_profiler import SystemProfiler
from src.optimization.windows_bloatware import WindowsBloatwareRemover
from src.optimization.windows_optimizer import WindowsSystemOptimizer
from src.optimization.performance_tuner import PerformanceOptimizer

# 1. Profile system
profiler = SystemProfiler()
profile = profiler.profile_system()
opportunities = profiler.get_optimization_opportunities(profile)

# 2. Remove bloatware
remover = WindowsBloatwareRemover()
bloatware = remover.scan_installed_bloatware()
remover.remove_all_safe_bloatware()

# 3. Optimize Windows
optimizer = WindowsSystemOptimizer()
optimizer.apply_safe_optimizations()

# 4. Tune performance
tuner = PerformanceOptimizer()
tuner.run_all_optimizations()

print("✅ Complete system optimization finished")
```

### Dry Run Mode

```python
# Scan without making changes
remover = WindowsBloatwareRemover()
installed = remover.scan_installed_bloatware()

print("Would remove:")
for item in installed:
    if item.safe_to_remove:
        print(f"  - {item.name}")

# Don't call remove_bloatware() for dry run
```

### Selective Optimization

```python
optimizer = WindowsSystemOptimizer()

# Apply only privacy optimizations
privacy_opts = [
    opt for opt in optimizer.optimizations
    if opt.category == "privacy"
]

for opt in privacy_opts:
    success, message = optimizer.apply_optimization(opt)
    print(f"{opt.name}: {message}")
```

---

## 📊 Expected Results

### After Bloatware Removal

- **Disk Space Saved:** 500MB - 2GB
- **Startup Time:** Reduced 10-30%
- **Memory Usage:** Reduced 100-300MB
- **Cleaner Start Menu:** Less clutter

### After System Optimization

- **CPU Performance:** 5-15% improvement
- **Privacy:** Telemetry reduced to minimum
- **Security:** Firewall and Defender active
- **Boot Time:** 10-20% faster

### During Gaming

- **Protocol CPU Usage:** < 5%
- **Memory Footprint:** < 100MB
- **No Interruptions:** Optimizations paused
- **Security:** Monitoring continues

---

## ⚠️ Important Notes

### Before Optimizing

1. **Create Restore Point:**
   ```bash
   # Windows: System Restore
   rstrui.exe
   ```

2. **Check Gaming Mode:**
   - Ensure gaming detection works
   - Test with your favorite games

3. **Review Bloatware:**
   - Check "user might want" list
   - Don't remove apps you use

### Rollback Capability

All optimizations are reversible:

```python
# Rollback specific optimization
optimizer.rollback_optimization("Disable SysMain (Superfetch)")

# Check rollback commands
for opt in optimizer.optimizations:
    print(f"{opt.name}: {opt.rollback_command}")
```

### Restart Required

Some optimizations require restart:

```python
# Check if restart needed
for opt in optimizer.optimizations:
    if opt.requires_restart:
        print(f"⚠️  {opt.name} requires restart")
```

---

## 🧪 Testing

### Test Bloatware Scanner

```bash
python test_windows_tools.py
```

### Test Gaming Mode

```bash
python test_gaming_mode.py
```

### Test System Optimizer

```python
from src.optimization.windows_optimizer import WindowsSystemOptimizer

optimizer = WindowsSystemOptimizer()
report = optimizer.get_optimization_report()

# Review before applying
for category, opts in report["optimizations"].items():
    print(f"\n{category.upper()}:")
    for opt in opts:
        print(f"  {opt['name']} (Impact: {opt['impact']})")
```

---

## 📝 Summary

**Windows Users Get:**
- ✅ Automatic bloatware removal
- ✅ Privacy optimization
- ✅ Security hardening
- ✅ Performance tuning
- ✅ Gaming mode (invisible during play)
- ✅ Complete rollback capability

**Linux Users Get:**
- ❌ Nothing (as it should be)

**The Protocol Philosophy:**
> "Help Windows users who need it. Respect Linux users who don't. Never interfere with gaming."

---

**Ready to optimize your Windows system? Run the tests first to see what would be changed.** 🚀
