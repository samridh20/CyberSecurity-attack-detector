import { Alert, Config } from "@/types/alert";

const ATTACK_CLASSES = ["DoS", "DDoS", "PortScan", "BruteForce", "SQLInjection", "XSS", "Normal"];
const INTERFACES = ["Ethernet", "WiFi", "VPN"];

const generateRandomIP = () => {
  return `${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}.${Math.floor(Math.random() * 255)}`;
};

export const generateMockAlert = (): Alert => {
  const attackClass = ATTACK_CLASSES[Math.floor(Math.random() * ATTACK_CLASSES.length)];
  const probability = attackClass === "Normal" ? Math.random() * 0.3 : 0.5 + Math.random() * 0.5;

  return {
    id: `alert-${Date.now()}-${Math.random()}`,
    ts: Date.now() / 1000,
    src: generateRandomIP(),
    dst: generateRandomIP(),
    class: attackClass,
    prob: probability,
    extra: {
      pkt_len: Math.floor(Math.random() * 1500) + 64,
      iface: INTERFACES[Math.floor(Math.random() * INTERFACES.length)],
      protocol: Math.random() > 0.5 ? "TCP" : "UDP",
      flags: Math.random() > 0.7 ? "SYN" : "ACK",
    },
  };
};

export const mockConfig: Config = {
  interface: "Ethernet",
  excluded_ports: [22, 443, 8080],
  excluded_hosts: ["192.168.1.1", "10.0.0.1"],
  window_size: 100,
  model_path: "C:\\IDS\\models\\rf_model.pkl",
  log_path: "C:\\IDS\\logs\\alerts.jsonl",
  enable_logging: true,
};

export const generateInitialAlerts = (count: number = 50): Alert[] => {
  const alerts: Alert[] = [];
  const now = Date.now() / 1000;
  
  for (let i = 0; i < count; i++) {
    const alert = generateMockAlert();
    alert.ts = now - (count - i) * 2; // Space alerts 2 seconds apart
    alerts.push(alert);
  }
  
  return alerts;
};
