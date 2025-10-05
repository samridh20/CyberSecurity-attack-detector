import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { BarChart3, Shield } from "lucide-react";
import { useSOCAssistant } from "@/hooks/useSOCAssistant";
import { SOCPopup } from "./SOCPopup";

interface ClassDistributionProps {
  data: Array<{ name: string; count: number }>;
}

export const ClassDistribution = ({ data }: ClassDistributionProps) => {
  const { simulateAttack, isAnalyzing, socResponse, isPopupOpen, closePopup } = useSOCAssistant();

  const getBarColor = (name: string) => {
    const colors: Record<string, string> = {
      DoS: "hsl(var(--destructive))",
      DDoS: "hsl(var(--destructive))",
      PortScan: "hsl(var(--warning))",
      BruteForce: "hsl(var(--warning))",
      SQLInjection: "hsl(var(--primary))",
      XSS: "hsl(var(--primary))",
      Normal: "hsl(var(--success))",
    };
    return colors[name] || "hsl(var(--secondary))";
  };

  const handleSimulateAttack = () => {
    // Get the most common attack type from the data, or default to DDoS
    const topAttack = data.length > 0 ? data[0].name : "DDoS";
    simulateAttack(topAttack, "high");
  };

  return (
    <>
      <Card className="border-glow bg-card/50 backdrop-blur">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2 font-orbitron">
              <BarChart3 className="h-5 w-5 text-primary" />
              Attack Class Distribution
            </CardTitle>
            <Button
              size="sm"
              variant="outline"
              onClick={handleSimulateAttack}
              disabled={isAnalyzing}
              className="flex items-center gap-2"
            >
              <Shield className="h-4 w-4" />
              {isAnalyzing ? "Analyzing..." : "SOC Response"}
            </Button>
          </div>
        </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis 
              dataKey="name" 
              stroke="hsl(var(--muted-foreground))"
              style={{ fontSize: '12px' }}
            />
            <YAxis 
              stroke="hsl(var(--muted-foreground))"
              style={{ fontSize: '12px' }}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: 'hsl(var(--popover))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '0.5rem',
              }}
            />
            <Bar 
              dataKey="count" 
              fill="hsl(var(--primary))"
              radius={[8, 8, 0, 0]}
            />
          </BarChart>
        </ResponsiveContainer>
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
