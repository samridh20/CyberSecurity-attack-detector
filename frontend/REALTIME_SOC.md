# 🚨 Real-Time SOC Analyst System

This is an **automatic SOC (Security Operations Center) analyst** that monitors your NIDS in real-time and **automatically pops up** when attacks are detected, providing immediate step-by-step instructions to stop ongoing attacks.

## 🎯 Key Features

### **Automatic Detection & Response**
- **Real-time monitoring** of all incoming alerts
- **Automatic popup** when high-confidence attacks are detected (>60% confidence)
- **Immediate analysis** using Gemini AI within 2 seconds of detection
- **No manual intervention required** - SOC analyst activates automatically

### **Clear Step-by-Step Instructions**
- **Prioritized action list** with most critical steps first
- **PowerShell commands** ready to copy and execute
- **Time estimates** for each action (30s, 60s, etc.)
- **Clear explanations** of why each step is necessary
- **Progress tracking** showing completed vs remaining steps

### **Emergency Response Features**
- **Red alert UI** with urgent styling and notifications
- **Auto-close timer** (5 minutes) to prevent screen clutter
- **Execute All Steps** button for rapid response
- **Copy All Commands** for batch execution
- **Emergency fallback** if Gemini API is unavailable

## 🚀 How It Works

### **Automatic Trigger Conditions**
The SOC analyst automatically activates when:
- Alert confidence > 60%
- Attack class is NOT "Normal" 
- Alert is less than 10 seconds old
- Not a duplicate of recently processed alert

### **Real-Time Analysis Process**
1. **Detection**: New high-confidence alert arrives
2. **Notification**: "🚨 SOC ANALYST ACTIVATED" toast appears
3. **Analysis**: Gemini AI analyzes attack in real-time (2-3 seconds)
4. **Popup**: Red alert popup appears with immediate actions
5. **Execution**: User clicks buttons to execute PowerShell commands
6. **Tracking**: Progress bar shows completion status

### **Response Categories**
- **STEP 1-3**: Most urgent actions (red background)
- **STEP 4-6**: Important follow-up actions (yellow background)  
- **STEP 7-8**: Evidence collection and monitoring (normal background)

## 🛠️ Testing the System

### **Method 1: Run Reconnaissance Attack**
```bash
python reconnaissance_attack.py
```
- Generates realistic reconnaissance packets
- Should trigger SOC popup within 1-2 seconds
- Look for "Reconnaissance" alerts in dashboard

### **Method 2: Use Demo Trigger Button**
- Click the red "🚨 TRIGGER SOC DEMO" button on dashboard
- Instantly triggers SOC analysis for demonstration
- Shows full popup with sample reconnaissance response

### **Method 3: Manual Testing**
- Use the SOC Test Panel (bottom of dashboard)
- Select attack type and severity
- Click "Simulate Attack & Get SOC Response"

## 📋 Example SOC Response

When a reconnaissance attack is detected, you'll see:

```
🚨 IMMEDIATE SOC RESPONSE REQUIRED
THREAT IDENTIFIED: Likely: Reconnaissance (confidence 85%)

STEP 1: Block Source IP
→ New-NetFirewallRule -DisplayName "Block-192.168.1.100" -Direction Inbound -Action Block -RemoteAddress 192.168.1.100

STEP 2: Start Network Monitoring  
→ pktmon start --etw -p 0 -c C:\ProgramData\SecAssist\evidence\capture.etl

STEP 3: Check Active Connections
→ netstat -an | findstr ESTABLISHED

... (up to 8 total steps)
```

## 🎨 UI Features

### **Visual Indicators**
- **Red border** and red text for urgent alerts
- **Progress bar** showing completion percentage
- **Step badges** (STEP 1, STEP 2, etc.) with color coding
- **Checkmarks** for completed actions
- **Spinning indicators** for actions in progress

### **User Experience**
- **One-click execution** - just click the action button
- **Automatic clipboard copy** - commands ready to paste
- **Toast notifications** for each completed step
- **Auto-close timer** prevents popup from staying open forever
- **Disable auto-close** option for extended analysis

## 🔧 Configuration

### **Sensitivity Settings**
Edit `useRealTimeSOC.ts` to adjust trigger conditions:
```typescript
const shouldTriggerSOC = (alert: Alert): boolean => {
  return alert.prob > 0.6 && alert.class !== "Normal";  // Adjust 0.6 threshold
};
```

### **Timing Settings**
```typescript
// Debounce delay (wait for more alerts)
setTimeout(() => { ... }, 2000);  // 2 seconds

// Auto-close timer
if (prev >= 300) { ... }  // 5 minutes
```

### **Evidence Paths**
The SOC system uses these default Windows paths:
- **PCAP**: `C:\ProgramData\SecAssist\evidence\capture.pcapng`
- **Logs**: `C:\ProgramData\SecAssist\evidence\logs.zip`
- **Notes**: `C:\ProgramData\SecAssist\evidence\notes.txt`

## 🚨 Emergency Protocols

### **If Gemini API Fails**
- System automatically shows **emergency fallback response**
- Basic IP blocking and monitoring commands provided
- "Emergency response - SOC API unavailable" message shown

### **If No Response Needed**
- SOC only triggers for actual attacks (not normal traffic)
- Filters out low-confidence alerts automatically
- Prevents false positive spam

## 🎯 Real-World Usage

### **During Active Attack**
1. **Alert appears** - SOC popup opens automatically
2. **Read classification** - understand the threat type
3. **Execute Step 1** - usually "Block Source IP"
4. **Continue steps** - follow the prioritized list
5. **Monitor progress** - watch the progress bar fill up
6. **Keep popup open** - disable auto-close if needed

### **Post-Attack Analysis**
- All commands are logged in clipboard history
- Evidence collection steps preserve attack data
- SOC notes provide additional context
- Progress tracking shows what was completed

## 🔍 Troubleshooting

### **SOC Not Triggering**
- Check alert confidence levels (must be >60%)
- Verify attack class is not "Normal"
- Look for "SOC ANALYST ACTIVATED" toast notification
- Try the demo trigger button to test

### **Commands Not Working**
- Run PowerShell as Administrator
- Check Windows Firewall permissions
- Verify network interface names
- Use manual command execution if needed

### **API Issues**
- Check browser console for Gemini API errors
- Verify API key is valid
- Emergency fallback should activate automatically
- Try demo mode for offline testing

This system provides **immediate, actionable security response** exactly when you need it most - during an active attack! 🛡️