import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { BarChart3 } from "lucide-react";

interface ClassDistributionProps {
  data: Array<{ name: string; count: number }>;
}

export const ClassDistribution = ({ data }: ClassDistributionProps) => {
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

  return (
    <Card className="border-glow bg-card/50 backdrop-blur">
      <CardHeader>
        <CardTitle className="flex items-center gap-2 font-orbitron">
          <BarChart3 className="h-5 w-5 text-primary" />
          Attack Class Distribution
        </CardTitle>
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
  );
};
