import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useState } from "react";
import { useSOCAssistant } from "@/hooks/useSOCAssistant";
import { SOCPopup } from "./SOCPopup";
import { Shield, Zap } from "lucide-react";

export const SOCTestPanel = () => {
  const [selectedAttack, setSelectedAttack] = useState<string>("DDoS");
  const [selectedSeverity, setSelectedSeverity] = useState<"low" | "medium" | "high" | "critical">("high");
  
  const { simulateAttack, isAnalyzing, socResponse, isPopupOpen, closePopup } = useSOCAssistant();

  const attackTypes = [
    "DDoS",
    "DoS", 
    "PortScan",
    "BruteForce",
    "SQLInjection",
    "XSS",
    "Man-in-the-Middle",
    "Exploit",
    "Reconnaissance"
  ];

  const severityLevels: Array<"low" | "medium" | "high" | "critical"> = [
    "low",
    "medium", 
    "high",
    "critical"
  ];

  const handleSimulate = () => {
    simulateAttack(selectedAttack, selectedSeverity);
  };

  return (
    <>
      <Card className="border-glow bg-card/50 backdrop-blur">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 font-orbitron">
            <Zap className="h-5 w-5 text-primary" />
            SOC Assistant Test Panel
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Attack Type</label>
              <Select value={selectedAttack} onValueChange={setSelectedAttack}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {attackTypes.map((attack) => (
                    <SelectItem key={attack} value={attack}>
                      {attack}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Severity Level</label>
              <Select value={selectedSeverity} onValueChange={(value: "low" | "medium" | "high" | "critical") => setSelectedSeverity(value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {severityLevels.map((severity) => (
                    <SelectItem key={severity} value={severity}>
                      <span className={`capitalize ${
                        severity === 'critical' ? 'text-red-600' :
                        severity === 'high' ? 'text-orange-600' :
                        severity === 'medium' ? 'text-yellow-600' :
                        'text-green-600'
                      }`}>
                        {severity}
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button 
            onClick={handleSimulate}
            disabled={isAnalyzing}
            className="w-full flex items-center gap-2"
          >
            <Shield className="h-4 w-4" />
            {isAnalyzing ? "Analyzing Attack..." : "Simulate Attack & Get SOC Response"}
          </Button>

          <div className="text-xs text-muted-foreground">
            This will simulate a {selectedAttack} attack with {selectedSeverity} severity and show the SOC assistant's response with actionable steps.
          </div>
        </CardContent>
      </Card>

      <SOCPopup
        isOpen={isPopupOpen}
        onClose={closePopup}
        response={socResponse}
        isLoading={isAnalyzing}
      />
    </>
  );
};