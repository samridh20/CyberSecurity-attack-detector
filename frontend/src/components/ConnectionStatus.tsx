import { useState, useEffect } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Wifi, WifiOff, AlertCircle } from 'lucide-react';
import { apiClient } from '@/lib/api';

export const ConnectionStatus = () => {
  const [status, setStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const checkConnection = async () => {
      try {
        await apiClient.getHealth();
        setStatus('connected');
        setError('');
      } catch (err) {
        setStatus('error');
        setError(err instanceof Error ? err.message : 'Connection failed');
      }
    };

    checkConnection();
    const interval = setInterval(checkConnection, 5000);
    return () => clearInterval(interval);
  }, []);

  const getStatusIcon = () => {
    switch (status) {
      case 'connected':
        return <Wifi className="h-4 w-4 text-green-500" />;
      case 'error':
        return <WifiOff className="h-4 w-4 text-red-500" />;
      default:
        return <AlertCircle className="h-4 w-4 text-yellow-500 animate-pulse" />;
    }
  };

  const getStatusText = () => {
    switch (status) {
      case 'connected':
        return 'Backend Connected';
      case 'error':
        return `Backend Error: ${error}`;
      default:
        return 'Connecting...';
    }
  };

  return (
    <Card className="border-glow bg-card/50 backdrop-blur">
      <CardContent className="flex items-center gap-2 p-3">
        {getStatusIcon()}
        <span className="text-sm font-medium">{getStatusText()}</span>
      </CardContent>
    </Card>
  );
};