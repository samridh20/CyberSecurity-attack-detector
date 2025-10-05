import { useState, useEffect } from "react";
import { BackendStats } from "@/types/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Settings, FolderOpen, Network, Activity } from "lucide-react";
import { toast } from "sonner";

interface SettingsViewProps {
  reloadInterface: (iface: string) => Promise<any>;
  getInterfaces: () => Promise<string[]>;
  currentInterface?: string;
  backendStats?: BackendStats;
}

export const SettingsView = ({
  reloadInterface,
  getInterfaces,
  currentInterface,
  backendStats
}: SettingsViewProps) => {
  const [availableInterfaces, setAvailableInterfaces] = useState<string[]>([]);
  const [selectedInterface, setSelectedInterface] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const loadInterfaces = async () => {
      try {
        const interfaces = await getInterfaces();
        setAvailableInterfaces(interfaces);
        if (currentInterface && interfaces.includes(currentInterface)) {
          setSelectedInterface(currentInterface);
        }
      } catch (error) {
        console.error("Failed to load interfaces:", error);
      }
    };

    loadInterfaces();
  }, [getInterfaces, currentInterface]);

  const handleInterfaceChange = async () => {
    if (!selectedInterface || selectedInterface === currentInterface) {
      return;
    }

    setIsLoading(true);
    try {
      await reloadInterface(selectedInterface);
    } catch (error) {
      console.error("Failed to change interface:", error);
      // Reset selection on error
      setSelectedInterface(currentInterface || "");
    } finally {
      setIsLoading(false);
    }
  };

  const openLogFolder = () => {
    if (backendStats?.logfile_path) {
      const folderPath = backendStats.logfile_path.substring(0, backendStats.logfile_path.lastIndexOf("\\"));
      navigator.clipboard.writeText(folderPath);
      toast.info("Log folder path copied to clipboard", {
        description: folderPath
      });
    }
  };

  return (
    <div className="space-y-6 animate-slide-up">
      {/* Interface Control */}
      <Card className="border-glow bg-card/50 backdrop-blur">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 font-orbitron">
            <Network className="h-5 w-5 text-accent" />
            Network Interface Control
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-muted-foreground">Current Interface</label>
              <div className="p-3 bg-muted/30 rounded-md font-mono text-sm border border-border">
                {currentInterface || "Unknown"}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-muted-foreground">Change Interface</label>
              <div className="flex gap-2">
                <Select value={selectedInterface} onValueChange={setSelectedInterface}>
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Select interface..." />
                  </SelectTrigger>
                  <SelectContent>
                    {availableInterfaces.map((iface) => (
                      <SelectItem key={iface} value={iface}>
                        {iface}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button
                  onClick={handleInterfaceChange}
                  disabled={isLoading || !selectedInterface || selectedInterface === currentInterface}
                  className="gap-2"
                >
                  {isLoading ? "Applying..." : "Apply"}
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* System Stats */}
      <Card className="border-glow bg-card/50 backdrop-blur">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 font-orbitron">
            <Activity className="h-5 w-5 text-accent" />
            System Statistics
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {backendStats ? (
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-sm font-semibold text-muted-foreground">Status</label>
                <div className={`p-3 rounded-md font-bold text-sm border ${backendStats.status === "running"
                  ? "bg-green-500/20 border-green-500 text-green-500"
                  : "bg-red-500/20 border-red-500 text-red-500"
                  }`}>
                  {backendStats.status.toUpperCase()}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-muted-foreground">Packets/Second</label>
                <div className="p-3 bg-muted/30 rounded-md font-mono text-sm border border-border">
                  {backendStats.pps.toFixed(2)}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-muted-foreground">Total Packets</label>
                <div className="p-3 bg-muted/30 rounded-md font-mono text-sm border border-border">
                  {backendStats.packets_processed.toLocaleString()}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-muted-foreground">Total Alerts</label>
                <div className="p-3 bg-muted/30 rounded-md font-mono text-sm border border-border">
                  {backendStats.alerts_generated.toLocaleString()}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-muted-foreground">Active Flows</label>
                <div className="p-3 bg-muted/30 rounded-md font-mono text-sm border border-border">
                  {backendStats.active_flows}
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-semibold text-muted-foreground">Uptime</label>
                <div className="p-3 bg-muted/30 rounded-md font-mono text-sm border border-border">
                  {Math.floor(backendStats.uptime_seconds / 3600)}h {Math.floor((backendStats.uptime_seconds % 3600) / 60)}m
                </div>
              </div>

              {backendStats.logfile_path && (
                <div className="space-y-2 md:col-span-2">
                  <label className="text-sm font-semibold text-muted-foreground">Log File Path</label>
                  <div className="flex gap-2">
                    <div className="flex-1 p-3 bg-muted/30 rounded-md font-mono text-xs border border-border overflow-x-auto">
                      {backendStats.logfile_path}
                    </div>
                    <Button
                      onClick={openLogFolder}
                      variant="outline"
                      className="gap-2"
                    >
                      <FolderOpen className="h-4 w-4" />
                      Copy Path
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center text-muted-foreground py-8">
              <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Backend statistics not available</p>
              <p className="text-sm">Make sure the backend API is running</p>
            </div>
          )}
        </CardContent>
      </Card>

      <Card className="border-glow-accent bg-card/50 backdrop-blur">
        <CardHeader>
          <CardTitle className="font-orbitron text-warning">Security Status</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>🛡️ Real packet capture from network interface</p>
          <p>🧠 Machine learning attack classification</p>
          <p>⚡ Real-time threat detection and alerting</p>
          <p>🌐 Enterprise-grade network security monitoring</p>
          <p className="text-green-500 font-medium">🔒 Network Security Active!</p>
        </CardContent>
      </Card>
    </div>
  );
};
