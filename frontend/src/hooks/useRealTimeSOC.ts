import { useState, useEffect, useRef } from "react";
import { geminiService } from "@/lib/gemini";
import { AttackInput, SOCResponse, PacketHeader } from "@/types/soc";
import { Alert } from "@/types/alert";
import { toast } from "sonner";

export const useRealTimeSOC = (alerts: Alert[]) => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [socResponse, setSocResponse] = useState<SOCResponse | null>(null);
  const [isPopupOpen, setIsPopupOpen] = useState(false);
  const [lastProcessedAlertId, setLastProcessedAlertId] = useState<string>("");
  const analysisTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const convertAlertToPacketHeader = (alert: Alert): PacketHeader => {
    return {
      timestamp: alert.ts * 1000, // Convert to milliseconds
      src_ip: alert.src,
      dst_ip: alert.dst,
      iface: alert.extra.iface || "unknown",
      pkt_len: alert.extra.pkt_len,
      protocol: alert.extra.protocol,
      flags: alert.extra.flags,
    };
  };

  const determineSeverity = (attackType: string, probability: number): "low" | "medium" | "high" | "critical" => {
    const criticalAttacks = ["DDoS", "DoS", "SQLInjection", "XSS"];
    const highAttacks = ["BruteForce", "Exploit", "Exploits"];
    const mediumAttacks = ["PortScan", "Reconnaissance"];

    if (criticalAttacks.some(attack => attackType.toLowerCase().includes(attack.toLowerCase()))) {
      return probability > 0.8 ? "critical" : "high";
    }
    
    if (highAttacks.some(attack => attackType.toLowerCase().includes(attack.toLowerCase()))) {
      return probability > 0.7 ? "high" : "medium";
    }
    
    if (mediumAttacks.some(attack => attackType.toLowerCase().includes(attack.toLowerCase()))) {
      return probability > 0.6 ? "medium" : "low";
    }

    // Default based on probability
    if (probability > 0.8) return "high";
    if (probability > 0.6) return "medium";
    return "low";
  };

  const shouldTriggerSOC = (alert: Alert): boolean => {
    // Trigger SOC for high-confidence attacks (not Normal traffic)
    return alert.prob > 0.6 && alert.class !== "Normal" && alert.class !== "normal";
  };

  const analyzeAttackRealTime = async (newAlerts: Alert[]) => {
    if (newAlerts.length === 0) return;

    // Get the most recent high-confidence attack
    const triggerAlert = newAlerts.find(shouldTriggerSOC);
    if (!triggerAlert) return;

    // Prevent duplicate analysis for the same alert
    if (triggerAlert.id === lastProcessedAlertId) return;
    
    setLastProcessedAlertId(triggerAlert.id);
    setIsAnalyzing(true);
    setSocResponse(null);
    setIsPopupOpen(true);

    // Show immediate notification
    toast.warning(`🚨 SOC ANALYST ACTIVATED`, {
      description: `Analyzing ${triggerAlert.class} attack in real-time...`,
      duration: 3000,
    });

    try {
      // Get related alerts from the same source or attack type
      const relatedAlerts = alerts
        .filter(alert => 
          (alert.src === triggerAlert.src || alert.class === triggerAlert.class) &&
          alert.prob > 0.5 &&
          (Date.now() - (alert.ts * 1000)) < 60000 // Last minute
        )
        .slice(0, 10); // Limit to 10 most relevant

      // Convert alerts to packet headers
      const packetHeaders = relatedAlerts.map(convertAlertToPacketHeader);
      
      // Determine severity
      const avgProbability = relatedAlerts.reduce((sum, alert) => sum + alert.prob, 0) / relatedAlerts.length;
      const severity = determineSeverity(triggerAlert.class, avgProbability);

      const attackInput: AttackInput = {
        attack_type: triggerAlert.class,
        severity,
        packet_headers: packetHeaders,
        host_os: "windows",
        mask_ips: false,
        extra_notes: `Real-time detection: ${relatedAlerts.length} related packets from ${triggerAlert.src}`,
      };

      const response = await geminiService.analyzeAttack(attackInput);
      setSocResponse(response);
      
      // Show success notification with action count
      toast.success(`🛡️ SOC ANALYSIS COMPLETE`, {
        description: `${response.steps.length} immediate actions recommended`,
        duration: 5000,
      });

    } catch (error) {
      console.error("Real-time SOC analysis failed:", error);
      toast.error("SOC analysis failed - using emergency protocols");
      
      // Emergency fallback response
      setSocResponse({
        classification: `Likely: ${triggerAlert.class} (confidence ${Math.round(triggerAlert.prob * 100)}%)`,
        steps: [
          {
            title: "Block Source IP",
            description: `Immediately block traffic from ${triggerAlert.src} using Windows Firewall`,
            why: "Prevent continued attack from this source",
            estimated_seconds: 30,
            button_label: "Block IP Now",
            commands: {
              windows: `New-NetFirewallRule -DisplayName "Block-${triggerAlert.src}" -Direction Inbound -Action Block -RemoteAddress ${triggerAlert.src}`
            }
          },
          {
            title: "Monitor Network",
            description: "Start network monitoring to capture additional attack traffic",
            why: "Collect evidence and detect related attacks",
            estimated_seconds: 60,
            button_label: "Start Monitoring",
            commands: {
              windows: "netstat -an | findstr ESTABLISHED"
            }
          },
          {
            title: "Check System Logs",
            description: "Review Windows security logs for related events",
            why: "Identify if attack was successful",
            estimated_seconds: 120,
            button_label: "Check Logs",
            commands: {
              windows: "Get-WinEvent -LogName Security -MaxEvents 50 | Where-Object {$_.TimeCreated -gt (Get-Date).AddMinutes(-5)}"
            }
          }
        ],
        notes: "Emergency response - SOC API unavailable"
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Monitor for new alerts and trigger SOC analysis
  useEffect(() => {
    if (alerts.length === 0) return;

    // Clear any existing timeout
    if (analysisTimeoutRef.current) {
      clearTimeout(analysisTimeoutRef.current);
    }

    // Debounce analysis to avoid spam (wait 2 seconds for more alerts)
    analysisTimeoutRef.current = setTimeout(() => {
      // Get alerts from the last 10 seconds
      const recentAlerts = alerts.filter(alert => 
        (Date.now() - (alert.ts * 1000)) < 10000
      );

      if (recentAlerts.length > 0) {
        analyzeAttackRealTime(recentAlerts);
      }
    }, 2000);

    return () => {
      if (analysisTimeoutRef.current) {
        clearTimeout(analysisTimeoutRef.current);
      }
    };
  }, [alerts]);

  const closePopup = () => {
    setIsPopupOpen(false);
    setSocResponse(null);
  };

  const manualAnalysis = async (attackType: string) => {
    const recentAlerts = alerts
      .filter(alert => alert.class === attackType && (Date.now() - (alert.ts * 1000)) < 60000)
      .slice(0, 5);

    if (recentAlerts.length > 0) {
      await analyzeAttackRealTime(recentAlerts);
    } else {
      toast.error(`No recent ${attackType} alerts found`);
    }
  };

  return {
    isAnalyzing,
    socResponse,
    isPopupOpen,
    closePopup,
    manualAnalysis,
  };
};