export interface PacketHeader {
  timestamp?: number;
  src_ip: string;
  dst_ip: string;
  src_port?: number;
  dst_port?: number;
  protocol?: string;
  proto?: string;
  flags?: string;
  iface: string;
  pkt_len?: number;
}

export interface AttackInput {
  attack_type: string;
  severity: "low" | "medium" | "high" | "critical";
  packet_headers: PacketHeader[];
  host_os: "windows";
  mask_ips: false;
  extra_notes?: string;
}

export interface SOCStep {
  title: string;
  description: string;
  why: string;
  estimated_seconds: number;
  button_label: string;
  commands: {
    windows: string;
  };
}

export interface SOCResponse {
  classification: string;
  steps: SOCStep[];
  notes?: string;
}