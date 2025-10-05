import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Activity, Shield, Clock, AlertTriangle } from "lucide-react";
import { Stats, Alert } from "@/types/alert";
import { AlertsChart } from "./AlertsChart";
import { ClassDistribution } from "./ClassDistribution";
import { SOCTestPanel } from "./SOCTestPanel";
import { RealTimeSOCPopup } from "./RealTimeSOCPopup";
import { useRealTimeSOC } from "@/hooks/useRealTimeSOC";
import { SOCTriggerButton } from "./SOCTriggerButton";

interface DashboardProps {
  stats: Stats;
  isCapturing: boolean;
  alertsHistory: Array<{ time: number; count: number }>;
  classDistribution: Array<{ name: string; count: number }>;
  alerts: Alert[];
}

export const Dashboard = ({ stats, isCapturing, alertsHistory, classDistribution, alerts }: DashboardProps) => {
  // Real-time SOC integration - automatically triggers on new attacks
  const { isAnalyzing, socResponse, isPopupOpen, closePopup } = useRealTimeSOC(alerts);

  const formatTime = (timestamp: number | null) => {
    if (!timestamp) return "No alerts yet";
    return new Date(timestamp).toLocaleTimeString();
  };

  return (
    <div className="space-y-6 animate-slide-up">
      {/* Status Bar */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card className="border-glow bg-card/50 backdrop-blur">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-space font-semibold">Status</CardTitle>
            <Shield className={`h-4 w-4 ${isCapturing ? 'text-success' : 'text-muted-foreground'}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-orbitron font-bold text-glow-accent">
              {isCapturing ? "ACTIVE" : "IDLE"}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Capture {isCapturing ? "Running" : "Stopped"}
            </p>
          </CardContent>
        </Card>

        <Card className="border-glow bg-card/50 backdrop-blur">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-space font-semibold">Total Alerts</CardTitle>
            <AlertTriangle className="h-4 w-4 text-warning" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-orbitron font-bold text-glow-primary">
              {stats.totalAlerts.toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats.alertsPerSec.toFixed(1)} alerts/sec
            </p>
          </CardContent>
        </Card>

        <Card className="border-glow bg-card/50 backdrop-blur">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-space font-semibold">Top Type</CardTitle>
            <Activity className="h-4 w-4 text-secondary" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-orbitron font-bold text-glow-purple">
              {stats.topClasses[0]?.name || "N/A"}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {stats.topClasses[0]?.count || 0} detections
            </p>
          </CardContent>
        </Card>

        <Card className="border-glow bg-card/50 backdrop-blur">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-space font-semibold">Last Alert</CardTitle>
            <Clock className="h-4 w-4 text-accent" />
          </CardHeader>
          <CardContent>
            <div className="text-sm font-orbitron font-bold text-foreground">
              {formatTime(stats.lastAlertTime)}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Most recent detection
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        <AlertsChart data={alertsHistory} />
        <ClassDistribution data={classDistribution} />
      </div>

      {/* SOC Test Panel */}
      <SOCTestPanel />

      {/* Real-Time SOC Demo Trigger */}
      <div className="flex justify-center">
        <SOCTriggerButton alerts={alerts} />
      </div>

      {/* Real-Time SOC Popup */}
      <RealTimeSOCPopup
        isOpen={isPopupOpen}
        onClose={closePopup}
        response={socResponse}
        isLoading={isAnalyzing}
      />
    </div>
  );
};
