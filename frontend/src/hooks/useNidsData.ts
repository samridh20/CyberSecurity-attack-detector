import { useState, useEffect, useCallback } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api';
import { Alert, BackendAlert, BackendStats, Stats } from '@/types/alert';
import { toast } from 'sonner';

// Convert backend alert format to frontend format
const convertBackendAlert = (backendAlert: BackendAlert): Alert => ({
  id: backendAlert.id,
  ts: backendAlert.timestamp,
  src: backendAlert.src_ip,
  dst: backendAlert.dst_ip,
  class: backendAlert.attack_class,
  prob: backendAlert.probability,
  extra: {
    pkt_len: backendAlert.packet_length || 0,
    iface: backendAlert.interface || 'unknown',
    protocol: backendAlert.protocol || 'unknown',
    flags: backendAlert.flags || 'unknown',
  },
});

// Convert backend stats to frontend stats format
const convertBackendStats = (backendStats: BackendStats, alerts: Alert[]): Stats => {
  // Calculate class distribution from alerts
  const classCounts = alerts.reduce((acc, alert) => {
    acc[alert.class] = (acc[alert.class] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const topClasses = Object.entries(classCounts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 3);

  return {
    totalAlerts: backendStats.alerts_generated,
    alertsPerSec: backendStats.alerts_per_sec,
    topClasses,
    lastAlertTime: backendStats.last_alert_ts ? backendStats.last_alert_ts * 1000 : null,
  };
};

export const useNidsData = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [stats, setStats] = useState<Stats>({
    totalAlerts: 0,
    alertsPerSec: 0,
    topClasses: [],
    lastAlertTime: null,
  });
  const [isCapturing, setIsCapturing] = useState(false);
  const [alertsHistory, setAlertsHistory] = useState<Array<{ time: number; count: number }>>([]);
  const [classDistribution, setClassDistribution] = useState<Array<{ name: string; count: number }>>([]);
  const [lastAlertCount, setLastAlertCount] = useState(0);

  const queryClient = useQueryClient();

  // Health check query
  const { data: health } = useQuery({
    queryKey: ['health'],
    queryFn: () => apiClient.getHealth(),
    refetchInterval: 5000,
    retry: 3,
  });

  // Stats query
  const { data: backendStats } = useQuery({
    queryKey: ['stats'],
    queryFn: () => apiClient.getStats(),
    refetchInterval: 1000,
    retry: 3,
  });

  // Alerts query
  const { data: backendAlerts } = useQuery({
    queryKey: ['alerts'],
    queryFn: () => apiClient.getRecentAlerts(1000),
    refetchInterval: 2000,
    retry: 3,
  });

  // Update capturing status based on health
  useEffect(() => {
    if (health) {
      setIsCapturing(health.status === 'healthy');
    }
  }, [health]);

  // Process backend alerts
  useEffect(() => {
    if (backendAlerts) {
      const convertedAlerts = backendAlerts.map(convertBackendAlert);
      
      // Sort by timestamp (newest first)
      convertedAlerts.sort((a, b) => b.ts - a.ts);
      
      // Check for new alerts and show notifications
      if (convertedAlerts.length > lastAlertCount) {
        const newAlerts = convertedAlerts.slice(0, convertedAlerts.length - lastAlertCount);
        
        newAlerts.forEach(alert => {
          if (alert.prob > 0.7 && alert.class !== "Normal") {
            toast.error(`⚠️ ${alert.class} DETECTED`, {
              description: `${alert.src} → ${alert.dst} (${(alert.prob * 100).toFixed(0)}%)`,
              className: "animate-glitch-text",
            });
          }
        });
      }
      
      setAlerts(convertedAlerts);
      setLastAlertCount(convertedAlerts.length);
    }
  }, [backendAlerts, lastAlertCount]);

  // Process backend stats
  useEffect(() => {
    if (backendStats && alerts.length > 0) {
      const convertedStats = convertBackendStats(backendStats, alerts);
      setStats(convertedStats);

      // Update class distribution
      const classCounts = alerts.reduce((acc, alert) => {
        acc[alert.class] = (acc[alert.class] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);

      const distribution = Object.entries(classCounts)
        .map(([name, count]) => ({ name, count }))
        .sort((a, b) => b.count - a.count);

      setClassDistribution(distribution);

      // Update alerts history for chart
      const now = Date.now();
      setAlertsHistory(prev => {
        const recentAlerts = alerts.filter(a => (now - (a.ts * 1000)) < 60000); // Last minute
        const newPoint = { time: now, count: recentAlerts.length };
        return [...prev.slice(-59), newPoint]; // Keep last 60 points
      });
    }
  }, [backendStats, alerts]);

  // Function to reload interface
  const reloadInterface = useCallback(async (iface: string) => {
    try {
      const result = await apiClient.reloadInterface(iface);
      
      if (result.ok) {
        toast.success(`Interface changed to ${result.active}`);
        
        // Invalidate queries to refresh data
        queryClient.invalidateQueries({ queryKey: ['health'] });
        queryClient.invalidateQueries({ queryKey: ['stats'] });
        
        return result;
      } else {
        throw new Error('Interface change failed');
      }
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Unknown error';
      toast.error(`Failed to change interface: ${message}`);
      throw error;
    }
  }, [queryClient]);

  // Function to get available interfaces
  const getInterfaces = useCallback(async () => {
    try {
      return await apiClient.getInterfaces();
    } catch (error) {
      console.error('Failed to get interfaces:', error);
      return [];
    }
  }, []);

  return {
    alerts,
    stats,
    isCapturing,
    alertsHistory,
    classDistribution,
    health,
    backendStats,
    reloadInterface,
    getInterfaces,
  };
};