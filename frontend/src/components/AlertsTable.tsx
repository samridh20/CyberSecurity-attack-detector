import { useState } from "react";
import { Alert } from "@/types/alert";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronUp, Download } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { toast } from "sonner";

interface AlertsTableProps {
  alerts: Alert[];
}

export const AlertsTable = ({ alerts }: AlertsTableProps) => {
  const [expandedRow, setExpandedRow] = useState<string | null>(null);

  const getProbabilityColor = (prob: number) => {
    if (prob >= 0.8) return "text-destructive";
    if (prob >= 0.5) return "text-warning";
    return "text-success";
  };

  const getClassColor = (className: string) => {
    const dangerClasses = ["DoS", "DDoS", "SQLInjection", "XSS"];
    const warningClasses = ["PortScan", "BruteForce"];
    
    if (dangerClasses.includes(className)) return "text-destructive";
    if (warningClasses.includes(className)) return "text-warning";
    return "text-success";
  };

  const exportToCSV = () => {
    const headers = ["Timestamp", "Source", "Destination", "Type", "Probability"];
    const rows = alerts.map(alert => [
      new Date(alert.ts * 1000).toLocaleString(),
      alert.src,
      alert.dst,
      alert.class,
      alert.prob.toFixed(2)
    ]);

    const csv = [headers, ...rows].map(row => row.join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ids-alerts-${Date.now()}.csv`;
    a.click();
    
    toast.success("Alerts exported to CSV");
  };

  const toggleRow = (id: string) => {
    setExpandedRow(expandedRow === id ? null : id);
  };

  return (
    <Card className="border-glow bg-card/50 backdrop-blur">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="font-orbitron">Recent Alerts</CardTitle>
        <Button onClick={exportToCSV} variant="outline" size="sm" className="gap-2">
          <Download className="h-4 w-4" />
          Export CSV
        </Button>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border border-border overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/50">
                <TableHead className="w-12"></TableHead>
                <TableHead className="font-orbitron">Timestamp</TableHead>
                <TableHead className="font-orbitron">Source</TableHead>
                <TableHead className="font-orbitron">Destination</TableHead>
                <TableHead className="font-orbitron">Class</TableHead>
                <TableHead className="font-orbitron">Probability</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {alerts.slice(0, 100).map((alert, index) => (
                <>
                  <TableRow 
                    key={alert.id} 
                    className={`hover:bg-muted/30 transition-colors cursor-pointer ${
                      index === 0 ? 'animate-glitch' : ''
                    }`}
                    onClick={() => toggleRow(alert.id)}
                  >
                    <TableCell>
                      <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                        {expandedRow === alert.id ? (
                          <ChevronUp className="h-4 w-4" />
                        ) : (
                          <ChevronDown className="h-4 w-4" />
                        )}
                      </Button>
                    </TableCell>
                    <TableCell className="font-mono text-xs">
                      {new Date(alert.ts * 1000).toLocaleTimeString()}
                    </TableCell>
                    <TableCell className="font-mono text-xs">{alert.src}</TableCell>
                    <TableCell className="font-mono text-xs">{alert.dst}</TableCell>
                    <TableCell className={`font-bold ${getClassColor(alert.class)}`}>
                      {alert.class}
                    </TableCell>
                    <TableCell className={`font-bold ${getProbabilityColor(alert.prob)}`}>
                      {(alert.prob * 100).toFixed(0)}%
                    </TableCell>
                  </TableRow>
                  {expandedRow === alert.id && (
                    <TableRow>
                      <TableCell colSpan={6} className="bg-muted/20">
                        <div className="p-4 space-y-2">
                          <h4 className="font-semibold text-sm text-primary">Additional Details</h4>
                          <pre className="text-xs bg-background/50 p-3 rounded overflow-auto">
                            {JSON.stringify(alert.extra, null, 2)}
                          </pre>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            <div>
                              <span className="text-muted-foreground">Packet Length:</span>{" "}
                              <span className="font-mono">{alert.extra.pkt_len} bytes</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Interface:</span>{" "}
                              <span className="font-mono">{alert.extra.iface}</span>
                            </div>
                          </div>
                        </div>
                      </TableCell>
                    </TableRow>
                  )}
                </>
              ))}
            </TableBody>
          </Table>
        </div>
        {alerts.length > 100 && (
          <p className="text-sm text-muted-foreground mt-4 text-center">
            Showing 100 of {alerts.length} alerts
          </p>
        )}
      </CardContent>
    </Card>
  );
};
