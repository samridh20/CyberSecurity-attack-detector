import { Button } from "@/components/ui/button";
import { Shield, Zap } from "lucide-react";
import { useRealTimeSOC } from "@/hooks/useRealTimeSOC";
import { Alert } from "@/types/alert";

interface SOCTriggerButtonProps {
  alerts: Alert[];
}

export const SOCTriggerButton = ({ alerts }: SOCTriggerButtonProps) => {
  const { manualAnalysis } = useRealTimeSOC(alerts);

  const triggerSOCDemo = () => {
    // Create a fake high-confidence reconnaissance alert to trigger SOC
    const fakeAlert: Alert = {
      id: `demo-${Date.now()}`,
      ts: Date.now() / 1000,
      src: "192.168.1.100",
      dst: "192.168.1.1", 
      class: "Reconnaissance",
      prob: 0.85,
      extra: {
        pkt_len: 64,
        iface: "eth0",
        protocol: "tcp",
        flags: "SYN"
      }
    };

    // Trigger manual analysis
    manualAnalysis("Reconnaissance");
  };

  return (
    <Button 
      onClick={triggerSOCDemo}
      className="bg-red-600 hover:bg-red-700 text-white"
      size="sm"
    >
      <Zap className="h-4 w-4 mr-2" />
      🚨 TRIGGER SOC DEMO
    </Button>
  );
};