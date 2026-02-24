# Operational Mode Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    PROTOCOL STARTUP                          │
│                                                               │
│  1. Check Platform                                           │
│     ├─ Linux? → DORMANT (unless explicit consent)           │
│     ├─ Windows? → PROCEED                                    │
│     └─ macOS? → LIMITED PROCEED                              │
│                                                               │
│  2. Initialize Safety Systems                                │
│  3. Begin Mode Detection Loop                                │
└─────────────────────────────────────────────────────────────┘
                           │
                           ↓
        ┌──────────────────────────────────┐
        │   CONTINUOUS MODE DETECTION      │
        │   (Every 60 seconds)             │
        └──────────────────────────────────┘
                           │
                           ↓
            ┌──────────────────────────┐
            │  PRIORITY CHECK ORDER    │
            └──────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ↓                  ↓                  ↓
  ┌──────────┐      ┌──────────┐      ┌──────────┐
  │ GAMING?  │      │  IDLE?   │      │ BATTERY? │
  │ (Highest)│      │ (Medium) │      │  (Low)   │
  └──────────┘      └──────────┘      └──────────┘
        │                  │                  │
        │                  │                  │
   YES  │ NO          YES  │ NO          LOW  │ OK
        │                  │                  │
        ↓                  ↓                  ↓
  ┌──────────┐      ┌──────────┐      ┌──────────┐
  │  GAMING  │      │   IDLE   │      │  STEALTH │
  │   MODE   │      │   MODE   │      │   MODE   │
  └──────────┘      └──────────┘      └──────────┘
        │                  │                  │
        └──────────────────┴──────────────────┘
                           │
                           ↓
                    ┌──────────┐
                    │  NORMAL  │
                    │   MODE   │
                    └──────────┘
```

## Mode Comparison Table

| Feature | GAMING | NORMAL | IDLE | STEALTH |
|---------|--------|--------|------|---------|
| **CPU Limit** | 5% | 30% | 60% | 10% |
| **Memory Limit** | 100MB | 500MB | 1GB | 200MB |
| **Disk I/O** | 1 Mbps | 10 Mbps | 50 Mbps | 5 Mbps |
| **Network** | 0.5 Mbps | 10 Mbps | 20 Mbps | 2 Mbps |
| **Scan Interval** | 5 min | 1 min | 30 sec | 3 min |
| **Optimizations** | ❌ None | ⚠️ Light | ✅ Full | ⚠️ Critical |
| **Propagation** | ❌ No | ❌ No | ✅ Yes | ❌ No |
| **Malware Scan** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| **Background Tasks** | ❌ No | ✅ Yes | ✅ Yes | ❌ No |

## Mode Transition Triggers

```
ENTER GAMING MODE:
├─ Game process detected (Steam, Epic, Battle.net, etc.)
├─ GPU usage > 70% for 30+ seconds
├─ Fullscreen application running
├─ Gamepad active + high activity
└─ Manual toggle: "gaming" > /tmp/benevolent_protocol_mode

EXIT GAMING MODE:
├─ Game process terminated
├─ GPU usage < 50% for 60+ seconds
├─ User switches to desktop
└─ Manual toggle: "normal" > /tmp/benevolent_protocol_mode

ENTER IDLE MODE:
├─ No user input for 10+ minutes
├─ No fullscreen apps
├─ Low CPU/network activity
└─ Manual toggle: "idle" > /tmp/benevolent_protocol_mode

EXIT IDLE MODE:
├─ User input detected
├─ New process started
├─ Gaming detected
└─ Manual toggle: "normal" > /tmp/benevolent_protocol_mode

ENTER STEALTH MODE:
├─ Battery < 20% AND not charging
├─ Manual toggle: "stealth" > /tmp/benevolent_protocol_mode

EXIT STEALTH MODE:
├─ Battery > 30% OR charging
├─ Gaming detected
└─ Manual toggle: "normal" > /tmp/benevolent_protocol_mode
```

## Gaming Mode Detection Flow

```
┌─────────────────────────────────────┐
│  START GAMING DETECTION             │
│  (Every 30 seconds)                 │
└─────────────────────────────────────┘
              │
              ↓
┌─────────────────────────────────────┐
│  Check Running Processes            │
│  ┌─────────────────────────────┐   │
│  │ steam.exe                   │   │
│  │ FortniteClient.exe          │   │
│  │ Overwatch.exe               │   │
│  │ [200+ known games]          │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
              │
              ↓
    ┌─────────────────┐
    │ Game Process?   │──YES──→ GAMING MODE (40% confidence)
    └─────────────────┘
              │ NO
              ↓
┌─────────────────────────────────────┐
│  Check GPU Usage                    │
│  ┌─────────────────────────────┐   │
│  │ nvidia-smi / AMD GPU stats  │   │
│  │ Usage > 70%?                │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
              │
              ↓
    ┌─────────────────┐
    │ GPU > 70%?      │──YES──→ +30% confidence
    └─────────────────┘
              │ NO
              ↓
┌─────────────────────────────────────┐
│  Check Fullscreen Application       │
│  ┌─────────────────────────────┐   │
│  │ Exclusive fullscreen mode?  │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
              │
              ↓
    ┌─────────────────┐
    │ Fullscreen?     │──YES──→ +20% confidence
    └─────────────────┘
              │ NO
              ↓
┌─────────────────────────────────────┐
│  Check Gamepad/Input Activity       │
│  ┌─────────────────────────────┐   │
│  │ Gamepad connected?          │   │
│  │ High input frequency?       │   │
│  └─────────────────────────────┘   │
└─────────────────────────────────────┘
              │
              ↓
    ┌─────────────────┐
    │ Gamepad Active? │──YES──→ +10% confidence
    └─────────────────┘
              │ NO
              ↓
    ┌─────────────────┐
    │ Total > 50%?    │──YES──→ GAMING MODE ACTIVATED
    └─────────────────┘
              │ NO
              ↓
         NORMAL MODE
```

## Resource Usage Over Time (Example)

```
Time    │ User Activity    │ Mode    │ CPU │ Memory │ Operations
────────┼──────────────────┼─────────┼─────┼────────┼────────────
00:00   │ Idle             │ IDLE    │ 45% │ 800MB  │ Full optimization
00:15   │ User returns     │ NORMAL  │ 25% │ 300MB  │ Light optimization
00:30   │ Browsing web     │ NORMAL  │ 28% │ 350MB  │ Standard scanning
01:00   │ Starts game      │ GAMING  │ 4%  │ 80MB   │ Security only
01:45   │ Still gaming     │ GAMING  │ 3%  │ 75MB   │ Security only
02:30   │ Exits game       │ NORMAL  │ 26% │ 320MB  │ Light optimization
03:00   │ Leaves computer  │ IDLE    │ 50% │ 900MB  │ Full optimization
03:30   │ Still away       │ IDLE    │ 55% │ 950MB  │ Deep scanning
04:00   │ User returns     │ NORMAL  │ 22% │ 280MB  │ Standard mode
04:30   │ Battery low      │ STEALTH │ 8%  │ 150MB  │ Critical only
```

## Platform Decision Tree

```
                    ┌─────────────┐
                    │   START     │
                    └─────────────┘
                          │
                          ↓
                  ┌───────────────┐
                  │ Detect OS     │
                  └───────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ↓                 ↓                 ↓
  ┌──────────┐      ┌──────────┐      ┌──────────┐
  │  Linux   │      │ Windows  │      │  macOS   │
  └──────────┘      └──────────┘      └──────────┘
        │                 │                 │
        ↓                 ↓                 ↓
  ┌──────────┐      ┌──────────┐      ┌──────────┐
  │ Explicit │      │ PROCEED  │      │ LIMITED  │
  │ Consent? │      │          │      │ PROCEED  │
  └──────────┘      └──────────┘      └──────────┘
        │
    YES │ NO
        │
   ┌────┴────┐
   │         │
   ↓         ↓
┌──────┐ ┌────────┐
│PROCEED│ │DORMANT │
└──────┘ └────────┘
```

---

**Key Principle:** The protocol adapts to the user's context, never interfering with important activities like gaming, while maximizing helpfulness during idle times.
