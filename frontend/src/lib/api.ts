/**
 * API client for NIDS backend integration
 */

const API_BASE_URL = 'http://127.0.0.1:8000';

export interface ApiAlert {
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

export interface ApiStats {
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

export interface ApiHealth {
  status: string;
  version: string;
  active_iface: string;
  timestamp: number;
}

export interface ApiConfig {
  capture?: {
    interface?: string;
  };
  [key: string]: any;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request to ${endpoint} failed:`, error);
      throw error;
    }
  }

  async getHealth(): Promise<ApiHealth> {
    return this.request<ApiHealth>('/health');
  }

  async getStats(): Promise<ApiStats> {
    return this.request<ApiStats>('/stats');
  }

  async getRecentAlerts(limit: number = 100): Promise<ApiAlert[]> {
    return this.request<ApiAlert[]>(`/alerts/recent?limit=${limit}`);
  }

  async getInterfaces(): Promise<string[]> {
    return this.request<string[]>('/capture/interfaces');
  }

  async reloadInterface(iface: string): Promise<{ ok: boolean; active: string; message: string }> {
    return this.request('/capture/reload', {
      method: 'POST',
      body: JSON.stringify({ iface }),
    });
  }

  async getConfig(): Promise<ApiConfig> {
    return this.request<ApiConfig>('/config');
  }
}

export const apiClient = new ApiClient();