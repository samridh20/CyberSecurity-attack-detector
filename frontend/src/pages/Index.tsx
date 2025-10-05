import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dashboard } from "@/components/Dashboard";
import { AlertsTable } from "@/components/AlertsTable";
import { SettingsView } from "@/components/SettingsView";
import { ConnectionStatus } from "@/components/ConnectionStatus";
import { useNidsData } from "@/hooks/useNidsData";
import { Shield, Wifi, WifiOff } from "lucide-react";

const Index = () => {
  const {
    alerts,
    stats,
    isCapturing,
    alertsHistory,
    classDistribution,
    health,
    backendStats,
    reloadInterface,
    getInterfaces,
  } = useNidsData();

  return (
    <div className="min-h-screen bg-background p-4 md:p-8 font-space">
      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4 mb-2">
            <Shield className="h-12 w-12 text-primary animate-pulse-glow" />
            <div>
              <h1 className="text-4xl md:text-6xl font-orbitron font-black text-glow-primary tracking-tight">
                NIDS SECURITY
              </h1>
              <p className="text-muted-foreground text-sm md:text-base">
                Network Intrusion Detection System - REAL PACKET MONITORING
              </p>
            </div>
          </div>
          
          {/* Status Indicators */}
          <div className="flex flex-col gap-2">
            <ConnectionStatus />
            <div className="flex items-center gap-2">
              {isCapturing ? (
                <Wifi className="h-6 w-6 text-green-500 animate-pulse" />
              ) : (
                <WifiOff className="h-6 w-6 text-red-500" />
              )}
              <div className="text-right">
                <div className={`text-sm font-medium ${isCapturing ? 'text-green-500' : 'text-red-500'}`}>
                  {isCapturing ? 'CAPTURING' : 'OFFLINE'}
                </div>
                {health && (
                  <div className="text-xs text-muted-foreground">
                    Interface: {health.active_iface}
                  </div>
                )}
              </div>
            </div>
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
            alerts={alerts}
          />
        </TabsContent>

        <TabsContent value="alerts">
          <AlertsTable alerts={alerts} />
        </TabsContent>

        <TabsContent value="settings">
          <SettingsView 
            reloadInterface={reloadInterface}
            getInterfaces={getInterfaces}
            currentInterface={health?.active_iface}
            backendStats={backendStats}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Index;
