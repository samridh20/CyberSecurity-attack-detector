import { useState, useCallback } from "react";
import { geminiService } from "@/lib/gemini";
import { AttackInput, SOCResponse, PacketHeader } from "@/types/soc";
import { Alert } from "@/types/alert";
import { toast } from "sonner";

export const useSOCAssistant = () => {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [socResponse, setSocResponse] = useState<SOCResponse | null>(null);
  const [isPopupOpen, setIsPopupOpen] = useState(false);

  const convertAlertToPacketHeader = (alert: Alert): PacketHeader => {
    return {
      timestamp: alert.ts,
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
    const highAttacks = ["BruteForce", "Exploit"];
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

  const analyzeAttack = useCallback(async (
    attackType: string,
    relatedAlerts: Alert[],
    extraNotes?: string
  ) => {
    if (relatedAlerts.length === 0) {
      toast.error("No alerts provided for analysis");
      return;
    }

    setIsAnalyzing(true);
    setSocResponse(null);
    setIsPopupOpen(true);

    try {
      // Convert alerts to packet headers
      const packetHeaders = relatedAlerts.map(convertAlertToPacketHeader);
      
      // Determine severity based on attack type and average probability
      const avgProbability = relatedAlerts.reduce((sum, alert) => sum + alert.prob, 0) / relatedAlerts.length;
      const severity = determineSeverity(attackType, avgProbability);

      const attackInput: AttackInput = {
        attack_type: attackType,
        severity,
        packet_headers: packetHeaders,
        host_os: "windows",
        mask_ips: false,
        extra_notes: extraNotes,
      };

      const response = await geminiService.analyzeAttack(attackInput);
      setSocResponse(response);
      
      toast.success("SOC analysis complete");
    } catch (error) {
      console.error("SOC analysis failed:", error);
      toast.error("Failed to analyze attack. Please try again.");
      setIsPopupOpen(false);
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  const simulateAttack = useCallback(async (
    attackType: string = "DDoS",
    severity: "low" | "medium" | "high" | "critical" = "high"
  ) => {
    setIsAnalyzing(true);
    setSocResponse(null);
    setIsPopupOpen(true);

    try {
      // Create simulated packet headers for demonstration
      const simulatedPacketHeaders: PacketHeader[] = [
        {
          timestamp: Date.now(),
          src_ip: "192.168.1.100",
          dst_ip: "192.168.1.1",
          src_port: 80,
          dst_port: 443,
          protocol: "TCP",
          flags: "SYN",
          iface: "eth0",
          pkt_len: 1500,
        },
        {
          timestamp: Date.now() + 1000,
          src_ip: "10.0.0.50",
          dst_ip: "192.168.1.1",
          src_port: 8080,
          dst_port: 443,
          protocol: "TCP",
          flags: "ACK",
          iface: "eth0",
          pkt_len: 1200,
        },
        {
          timestamp: Date.now() + 2000,
          src_ip: "172.16.0.25",
          dst_ip: "192.168.1.1",
          src_port: 3389,
          dst_port: 22,
          protocol: "TCP",
          flags: "RST",
          iface: "eth0",
          pkt_len: 800,
        },
      ];

      const attackInput: AttackInput = {
        attack_type: attackType,
        severity,
        packet_headers: simulatedPacketHeaders,
        host_os: "windows",
        mask_ips: false,
        extra_notes: "Simulated attack for demonstration purposes",
      };

      const response = await geminiService.analyzeAttack(attackInput);
      setSocResponse(response);
      
      toast.success(`Simulated ${attackType} attack analyzed`);
    } catch (error) {
      console.error("SOC simulation failed:", error);
      toast.error("Failed to simulate attack analysis");
      setIsPopupOpen(false);
    } finally {
      setIsAnalyzing(false);
    }
  }, []);

  const closePopup = useCallback(() => {
    setIsPopupOpen(false);
    setSocResponse(null);
  }, []);

  return {
    isAnalyzing,
    socResponse,
    isPopupOpen,
    analyzeAttack,
    simulateAttack,
    closePopup,
  };
};