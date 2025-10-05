import { useState, useEffect } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dashboard } from "@/components/Dashboard";
import { AlertsTable } from "@/components/AlertsTable";
import { SettingsView } from "@/components/SettingsView";
import { Alert, Stats } from "@/types/alert";
import { generateMockAlert, generateInitialAlerts, mockConfig } from "@/utils/mockData";
import { toast } from "sonner";
import { Shield } from "lucide-react";

const Index = () => {
  const [alerts, setAlerts] = useState<Alert[]>(generateInitialAlerts());
  const [stats, setStats] = useState<Stats>({
    totalAlerts: 0,
    alertsPerSec: 0,
    topClasses: [],
    lastAlertTime: null,
  });
  const [isCapturing, setIsCapturing] = useState(true);
  const [alertsHistory, setAlertsHistory] = useState<Array<{ time: number; count: number }>>([]);
  const [classDistribution, setClassDistribution] = useState<Array<{ name: string; count: number }>>([]);

  // Simulate real-time alert generation
  useEffect(() => {
    const interval = setInterval(() => {
      const newAlert = generateMockAlert();
      
      setAlerts(prev => {
        const updated = [newAlert, ...prev].slice(0, 1000); // Keep last 1000
        return updated;
      });

      // Show toast with glitch effect for high-probability threats
      if (newAlert.prob > 0.7 && newAlert.class !== "Normal") {
        toast.error(`⚠️ ${newAlert.class} DETECTED`, {
          description: `${newAlert.src} → ${newAlert.dst} (${(newAlert.prob * 100).toFixed(0)}%)`,
          className: "animate-glitch-text",
        });
      }
    }, 2000 + Math.random() * 3000); // Random interval 2-5 seconds

    return () => clearInterval(interval);
  }, []);

  // Update stats when alerts change
  useEffect(() => {
    const classCounts = alerts.reduce((acc, alert) => {
      acc[alert.class] = (acc[alert.class] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);

    const topClasses = Object.entries(classCounts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 3);

    const distribution = Object.entries(classCounts)
      .map(([name, count]) => ({ name, count }))
      .sort((a, b) => b.count - a.count);

    setClassDistribution(distribution);

    setStats({
      totalAlerts: alerts.length,
      alertsPerSec: alerts.length > 0 ? 0.3 + Math.random() * 0.4 : 0,
      topClasses,
      lastAlertTime: alerts.length > 0 ? alerts[0].ts * 1000 : null,
    });

    // Update history for chart
    const now = Date.now();
    setAlertsHistory(prev => {
      const newPoint = { time: now, count: alerts.filter(a => (now - a.ts * 1000) < 5000).length };
      return [...prev.slice(-60), newPoint]; // Keep last 60 points
    });
  }, [alerts]);

  return (
    <div className="min-h-screen bg-background p-4 md:p-8 font-space">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center gap-4 mb-2">
          <Shield className="h-12 w-12 text-primary animate-pulse-glow" />
          <div>
            <h1 className="text-4xl md:text-6xl font-orbitron font-black text-glow-primary tracking-tight">
              IDS MONITOR
            </h1>
            <p className="text-muted-foreground text-sm md:text-base">
              Real-time Intrusion Detection System
            </p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <Tabs defaultValue="dashboard" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-3 mb-8 bg-muted/50 backdrop-blur">
          <TabsTrigger value="dashboard" className="font-orbitron data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            Dashboard
          </TabsTrigger>
          <TabsTrigger value="alerts" className="font-orbitron data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            Alerts
          </TabsTrigger>
          <TabsTrigger value="settings" className="font-orbitron data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            Settings
          </TabsTrigger>
        </TabsList>

        <TabsContent value="dashboard">
          <Dashboard 
            stats={stats}
            isCapturing={isCapturing}
            alertsHistory={alertsHistory}
            classDistribution={classDistribution}
          />
        </TabsContent>

        <TabsContent value="alerts">
          <AlertsTable alerts={alerts} />
        </TabsContent>

        <TabsContent value="settings">
          <SettingsView config={mockConfig} />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Index;
