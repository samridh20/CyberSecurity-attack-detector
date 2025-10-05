import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import { SOCResponse, SOCStep } from "@/types/soc";
import { Shield, Clock, Terminal, CheckCircle, AlertTriangle, Zap, Copy } from "lucide-react";
import { toast } from "sonner";

interface RealTimeSOCPopupProps {
  isOpen: boolean;
  onClose: () => void;
  response: SOCResponse | null;
  isLoading: boolean;
}

export const RealTimeSOCPopup = ({ isOpen, onClose, response, isLoading }: RealTimeSOCPopupProps) => {
  const [executedSteps, setExecutedSteps] = useState<Set<number>>(new Set());
  const [executingStep, setExecutingStep] = useState<number | null>(null);


  const executeStep = async (step: SOCStep, index: number) => {
    if (!step.commands.windows) {
      toast.info("No command available for this step");
      return;
    }

    setExecutingStep(index);
    
    try {
      // Copy command to clipboard
      await navigator.clipboard.writeText(step.commands.windows);
      
      // Mark as executed after a short delay
      setTimeout(() => {
        setExecutedSteps(prev => new Set([...prev, index]));
        setExecutingStep(null);
        toast.success(`✅ Step ${index + 1}: ${step.title}`, {
          description: "Command copied - execute in PowerShell",
          duration: 3000,
        });
      }, 500);
      
    } catch (error) {
      console.error('Failed to copy command:', error);
      setExecutingStep(null);
      toast.error("Failed to copy command");
    }
  };

  const executeAllSteps = async () => {
    if (!response) return;

    for (let i = 0; i < response.steps.length; i++) {
      if (!executedSteps.has(i) && response.steps[i].commands.windows) {
        await executeStep(response.steps[i], i);
        await new Promise(resolve => setTimeout(resolve, 1000)); // 1 second delay between steps
      }
    }
  };

  const getSeverityColor = (classification: string) => {
    const lower = classification.toLowerCase();
    if (lower.includes('critical')) return 'destructive';
    if (lower.includes('high')) return 'destructive';
    if (lower.includes('medium')) return 'default';
    return 'secondary';
  };

  const getSeverityIcon = (classification: string) => {
    const lower = classification.toLowerCase();
    if (lower.includes('critical') || lower.includes('high')) return <AlertTriangle className="h-4 w-4" />;
    return <Shield className="h-4 w-4" />;
  };

  if (isLoading) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-2xl border-primary border-2 border-glow bg-background/95 backdrop-blur">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 font-orbitron font-black text-glow-primary">
              <Zap className="h-5 w-5 animate-pulse-glow text-primary" />
              🚨 SOC ANALYST ACTIVATED
            </DialogTitle>
            <DialogDescription className="text-glow-accent font-space font-medium">
              Real-time attack detected! Analyzing threat and preparing immediate response...
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col items-center justify-center py-8 space-y-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary border-glow animate-pulse-glow"></div>
            <div className="text-center">
              <p className="font-orbitron font-medium text-glow-primary">Analyzing attack patterns...</p>
              <p className="text-sm text-muted-foreground font-space">Generating response plan...</p>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  if (!response) return null;

  const completedSteps = executedSteps.size;
  const totalSteps = response.steps.length;
  const progressPercentage = (completedSteps / totalSteps) * 100;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] border-primary border-2 border-glow overflow-hidden flex flex-col bg-background/95 backdrop-blur">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2 font-orbitron font-black text-glow-primary">
              <Zap className="h-5 w-5 animate-pulse-glow text-primary" />
              🚨 IMMEDIATE SOC RESPONSE REQUIRED
            </div>
          </DialogTitle>
          <DialogDescription className="text-glow-accent font-space font-semibold">
            ACTIVE ATTACK DETECTED - Execute these steps immediately to stop the threat
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="flex-1 pr-4">
          <div className="space-y-4">
            {/* Threat Classification */}
          <Card className="border-glow bg-card/50 backdrop-blur">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getSeverityIcon(response.classification)}
                  <span className="font-orbitron font-black text-glow-primary text-lg">⚠️ THREAT IDENTIFIED:</span>
                </div>
                <Badge variant={getSeverityColor(response.classification)} className="text-lg px-4 py-2 font-orbitron font-bold border-glow animate-pulse-glow">
                  {response.classification}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Progress Bar */}
          <Card className="border-glow bg-card/50 backdrop-blur">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between mb-2">
                <span className="font-orbitron font-bold text-glow-accent">📊 Response Progress</span>
                <span className="text-sm font-space font-medium text-muted-foreground">
                  {completedSteps}/{totalSteps} steps completed
                </span>
              </div>
              <Progress value={progressPercentage} className="h-2" />
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <div className="flex gap-2">
            <Button 
              onClick={executeAllSteps}
              className="flex-1 bg-primary hover:bg-primary/80 font-orbitron font-bold border-glow animate-pulse-glow"
              disabled={completedSteps === totalSteps}
            >
              <Zap className="h-4 w-4 mr-2 animate-pulse-glow" />
              ⚡ Execute All Steps
            </Button>
            <Button 
              variant="outline" 
              className="border-glow hover:bg-secondary/20 font-orbitron font-semibold"
              onClick={() => {
                const allCommands = response.steps
                  .filter(step => step.commands.windows)
                  .map((step, i) => `# Step ${i + 1}: ${step.title}\n${step.commands.windows}`)
                  .join('\n\n');
                navigator.clipboard.writeText(allCommands);
                toast.success("All commands copied to clipboard");
              }}
            >
              <Copy className="h-4 w-4 mr-2" />
              📋 Copy All
            </Button>
          </div>

          {/* Response Steps */}
          <Card className="border-glow bg-card/50 backdrop-blur">
            <CardContent className="pt-4">
              <div className="flex items-center gap-2 mb-4">
                <Terminal className="h-5 w-5 text-primary animate-pulse-glow" />
                <span className="font-orbitron font-black text-glow-primary text-lg">🚨 IMMEDIATE ACTIONS REQUIRED</span>
              </div>
              
              <ScrollArea className="h-[300px] pr-4">
                <div className="space-y-3">
                  {response.steps.map((step, index) => {
                    const isExecuted = executedSteps.has(index);
                    const isExecuting = executingStep === index;
                    const isUrgent = index < 3; // First 3 steps are most urgent
                    
                    return (
                      <Card 
                        key={index} 
                        className={`transition-all border-glow ${
                          isExecuted ? 'bg-success/10 border-success animate-pulse-glow' : 
                          isUrgent ? 'bg-destructive/10 border-destructive animate-pulse-glow' : 
                          'bg-warning/10 border-warning'
                        }`}
                      >
                        <CardContent className="pt-4">
                          <div className="flex items-start justify-between gap-4">
                            <div className="flex-1 space-y-2">
                              <div className="flex items-center gap-2">
                                <Badge variant={isUrgent ? "destructive" : "default"} className="text-xs font-orbitron font-bold border-glow">
                                  STEP {index + 1}
                                </Badge>
                                <span className="font-orbitron font-bold text-sm text-glow-accent">
                                  {step.title}
                                </span>
                                {isExecuted && (
                                  <CheckCircle className="h-4 w-4 text-green-600" />
                                )}
                                <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                  <Clock className="h-3 w-3" />
                                  {step.estimated_seconds}s
                                </div>
                              </div>
                              
                              <p className="text-sm font-space font-medium text-foreground">
                                {step.description}
                              </p>
                              
                              <p className="text-xs font-space text-muted-foreground bg-muted/50 px-3 py-2 rounded-md border-glow">
                                <strong>💡 Why:</strong> {step.why}
                              </p>
                              
                              {step.commands.windows && (
                                <div className="bg-background border-glow p-3 rounded-lg font-mono text-xs overflow-x-auto">
                                  <div className="text-muted-foreground mb-1 font-space">💻 PowerShell Command:</div>
                                  <div className="text-glow-primary font-mono">{step.commands.windows}</div>
                                </div>
                              )}
                            </div>
                            
                            <Button
                              size="sm"
                              variant={isExecuted ? "outline" : isUrgent ? "destructive" : "default"}
                              disabled={isExecuting || !step.commands.windows}
                              onClick={() => executeStep(step, index)}
                              className="shrink-0 min-w-[100px]"
                            >
                              {isExecuting ? (
                                <div className="animate-spin rounded-full h-3 w-3 border-b border-white"></div>
                              ) : isExecuted ? (
                                "✅ Done"
                              ) : (
                                step.button_label
                              )}
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Notes */}
          {response.notes && (
            <Card className="border-glow bg-card/50 backdrop-blur">
              <CardContent className="pt-4">
                <div className="text-sm font-space">
                  <strong className="text-glow-accent font-orbitron">📝 SOC Notes:</strong> <span className="text-muted-foreground">{response.notes}</span>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Footer Actions */}
          <div className="flex justify-between items-center pt-4 border-t border-glow">
            <div className="text-xs text-muted-foreground font-space font-medium">
              💡 Commands are copied to clipboard - paste and run in PowerShell as Administrator
            </div>
            <div className="flex gap-2">
              <Button variant="outline" className="border-glow hover:bg-secondary/20 font-orbitron" onClick={onClose}>
                ✅ Close (Keep Monitoring)
              </Button>
            </div>
          </div>
        </div>
        </ScrollArea>
      </DialogContent>
    </Dialog>
  );
};