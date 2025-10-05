import { useState } from "react";
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
import { Separator } from "@/components/ui/separator";
import { SOCResponse, SOCStep } from "@/types/soc";
import { Shield, Clock, Terminal, CheckCircle, AlertTriangle } from "lucide-react";
import { toast } from "sonner";

interface SOCPopupProps {
  isOpen: boolean;
  onClose: () => void;
  response: SOCResponse | null;
  isLoading: boolean;
}

export const SOCPopup = ({ isOpen, onClose, response, isLoading }: SOCPopupProps) => {
  const [executedSteps, setExecutedSteps] = useState<Set<number>>(new Set());
  const [executingStep, setExecutingStep] = useState<number | null>(null);

  const executeStep = async (step: SOCStep, index: number) => {
    if (!step.commands.windows) {
      toast.info("No command to execute for this step");
      return;
    }

    setExecutingStep(index);
    
    try {
      // Copy command to clipboard for user to execute
      await navigator.clipboard.writeText(step.commands.windows);
      
      // Mark as executed after a short delay
      setTimeout(() => {
        setExecutedSteps(prev => new Set([...prev, index]));
        setExecutingStep(null);
        toast.success(`Step ${index + 1} command copied to clipboard`);
      }, 1000);
      
    } catch (error) {
      console.error('Failed to copy command:', error);
      setExecutingStep(null);
      toast.error("Failed to copy command to clipboard");
    }
  };

  const getSeverityColor = (classification: string) => {
    const lower = classification.toLowerCase();
    if (lower.includes('critical') || lower.includes('high')) return 'destructive';
    if (lower.includes('medium')) return 'default';
    return 'secondary';
  };

  const getConfidenceColor = (classification: string) => {
    const match = classification.match(/confidence (\d+)%/);
    if (!match) return 'secondary';
    
    const confidence = parseInt(match[1]);
    if (confidence >= 80) return 'default';
    if (confidence >= 60) return 'secondary';
    return 'outline';
  };

  if (isLoading) {
    return (
      <Dialog open={isOpen} onOpenChange={onClose}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5 animate-pulse" />
              Analyzing Attack...
            </DialogTitle>
            <DialogDescription>
              SOC Assistant is analyzing the detected attack and preparing response steps.
            </DialogDescription>
          </DialogHeader>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </DialogContent>
      </Dialog>
    );
  }

  if (!response) return null;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-primary" />
            SOC Response - Attack Detected
          </DialogTitle>
          <DialogDescription>
            Immediate response plan for the detected security incident
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Classification */}
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <AlertTriangle className="h-4 w-4" />
                  <span className="font-medium">Classification:</span>
                </div>
                <div className="flex gap-2">
                  <Badge variant={getSeverityColor(response.classification)}>
                    {response.classification.split('(')[0].trim()}
                  </Badge>
                  <Badge variant={getConfidenceColor(response.classification)}>
                    {response.classification.match(/\(([^)]+)\)/)?.[1] || 'Unknown confidence'}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Response Steps */}
          <Card>
            <CardContent className="pt-4">
              <div className="flex items-center gap-2 mb-4">
                <Terminal className="h-4 w-4" />
                <span className="font-medium">Response Steps ({response.steps.length})</span>
              </div>
              
              <ScrollArea className="h-[400px] pr-4">
                <div className="space-y-3">
                  {response.steps.map((step, index) => (
                    <Card key={index} className={`transition-all ${
                      executedSteps.has(index) ? 'bg-green-50 border-green-200' : ''
                    }`}>
                      <CardContent className="pt-4">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 space-y-2">
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-sm">
                                {index + 1}. {step.title}
                              </span>
                              {executedSteps.has(index) && (
                                <CheckCircle className="h-4 w-4 text-green-600" />
                              )}
                              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                <Clock className="h-3 w-3" />
                                {step.estimated_seconds}s
                              </div>
                            </div>
                            
                            <p className="text-sm text-muted-foreground">
                              {step.description}
                            </p>
                            
                            <p className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                              Why: {step.why}
                            </p>
                            
                            {step.commands.windows && (
                              <div className="bg-gray-100 p-2 rounded text-xs font-mono">
                                {step.commands.windows}
                              </div>
                            )}
                          </div>
                          
                          <Button
                            size="sm"
                            variant={executedSteps.has(index) ? "outline" : "default"}
                            disabled={executingStep === index}
                            onClick={() => executeStep(step, index)}
                            className="shrink-0"
                          >
                            {executingStep === index ? (
                              <div className="animate-spin rounded-full h-3 w-3 border-b border-white"></div>
                            ) : executedSteps.has(index) ? (
                              "Executed"
                            ) : (
                              step.button_label
                            )}
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Notes */}
          {response.notes && (
            <>
              <Separator />
              <div className="text-sm text-muted-foreground">
                <strong>Notes:</strong> {response.notes}
              </div>
            </>
          )}

          {/* Actions */}
          <div className="flex justify-between items-center pt-4">
            <div className="text-xs text-muted-foreground">
              Commands are copied to clipboard when you click the action buttons
            </div>
            <Button variant="outline" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};