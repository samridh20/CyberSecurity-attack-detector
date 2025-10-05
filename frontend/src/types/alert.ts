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
