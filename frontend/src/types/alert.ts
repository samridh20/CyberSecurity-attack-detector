export interface Alert {
  id: string;
  ts: number;
  src: string;
  dst: string;
  class: string;
  prob: number;
  extra: {
    pkt_len: number;
    iface: string;
    [key: string]: any;
  };
}

export interface Config {
  interface: string;
  excluded_ports: number[];
  excluded_hosts: string[];
  window_size: number;
  model_path: string;
  log_path: string;
  enable_logging: boolean;
}

export interface Stats {
  totalAlerts: number;
  alertsPerSec: number;
  topClasses: Array<{ name: string; count: number }>;
  lastAlertTime: number | null;
}

// Backend API types
export interface BackendAlert {
  id: string;
  timestamp: number;
  src_ip: string;
  dst_ip: string;
  attack_class: string;
  probability: number;
  packet_length?: number;
  interface?: string;
  protocol?: string;
  flags?: string;
}

export interface BackendStats {
  pps: number;
  alerts_per_sec: number;
  last_alert_ts: number | null;
  logfile_path: string | null;
  packets_processed: number;
  alerts_generated: number;
  active_flows: number;
  uptime_seconds: number;
  status: string;
}
