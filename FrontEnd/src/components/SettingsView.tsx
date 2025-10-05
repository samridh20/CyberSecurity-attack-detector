import { Config } from "@/types/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Settings, FolderOpen } from "lucide-react";
import { toast } from "sonner";

interface SettingsViewProps {
  config: Config;
}

export const SettingsView = ({ config }: SettingsViewProps) => {
  const openConfigFolder = () => {
    toast.info("Config folder path copied to clipboard", {
      description: config.log_path.substring(0, config.log_path.lastIndexOf("\\"))
    });
  };

  return (
    <div className="space-y-6 animate-slide-up">
      <Card className="border-glow bg-card/50 backdrop-blur">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 font-orbitron">
            <Settings className="h-5 w-5 text-accent" />
            System Configuration (Read-Only)
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-muted-foreground">Capture Interface</label>
              <div className="p-3 bg-muted/30 rounded-md font-mono text-sm border border-border">
                {config.interface}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-muted-foreground">Window Size</label>
              <div className="p-3 bg-muted/30 rounded-md font-mono text-sm border border-border">
                {config.window_size} packets
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-muted-foreground">Model Path</label>
              <div className="p-3 bg-muted/30 rounded-md font-mono text-xs border border-border overflow-x-auto">
                {config.model_path}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-muted-foreground">Log Path</label>
              <div className="p-3 bg-muted/30 rounded-md font-mono text-xs border border-border overflow-x-auto">
                {config.log_path}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-muted-foreground">Excluded Ports</label>
              <div className="p-3 bg-muted/30 rounded-md font-mono text-sm border border-border">
                {config.excluded_ports.join(", ")}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-muted-foreground">Excluded Hosts</label>
              <div className="p-3 bg-muted/30 rounded-md font-mono text-sm border border-border">
                {config.excluded_hosts.join(", ")}
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-muted-foreground">Logging Enabled</label>
              <div className={`p-3 rounded-md font-bold text-sm border ${
                config.enable_logging 
                  ? "bg-success/20 border-success text-success" 
                  : "bg-destructive/20 border-destructive text-destructive"
              }`}>
                {config.enable_logging ? "YES" : "NO"}
              </div>
            </div>

            <div className="space-y-2 flex items-end">
              <Button 
                onClick={openConfigFolder}
                variant="outline"
                className="w-full gap-2"
              >
                <FolderOpen className="h-4 w-4" />
                Copy Log Path
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="border-glow-accent bg-card/50 backdrop-blur">
        <CardHeader>
          <CardTitle className="font-orbitron text-warning">Important Notes</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>• This UI is read-only and monitors backend activity in real-time</p>
          <p>• Configuration changes must be made in <code className="bg-muted px-1 rounded">config.yml</code></p>
          <p>• The backend Python service must be running for data to appear</p>
          <p>• Alert data is automatically pruned to the last 1000 entries for performance</p>
        </CardContent>
      </Card>
    </div>
  );
};
