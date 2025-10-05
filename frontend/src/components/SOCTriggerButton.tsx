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
    // Trigger manual analysis with reconnaissance attack
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