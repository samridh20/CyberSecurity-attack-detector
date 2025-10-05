import { AttackInput, SOCResponse } from "@/types/soc";

const GEMINI_API_KEY = "AIzaSyC-uAMfhqIw0RA1P0xfhz9YjokKOMcMutM";
const GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent";

const SOC_PROMPT = `You are a concise, calm SOC assistant for a Windows laptop. Context: The backend has already detected and classified an attack. Your JSON response will be shown to the user as a small popup with action buttons.

Input:
attack_type: string (e.g., DDoS, Man-in-the-Middle, Port Scan, Brute Force, Exploit, Reconnaissance)
severity: "low" | "medium" | "high" | "critical"
packet_headers: array of objects: { timestamp?, src_ip, dst_ip, src_port?, dst_port?, protocol|proto, flags?, iface, pkt_len? }
host_os: always "windows"
mask_ips: always false (show full IPs)
extra_notes?: string

Task:
Identify the most likely ongoing attack in one short sentence.
Return a prioritized plan of at most 8 immediate steps (highest first) that a non-technical user can execute. Each step must be:
Clear, specific, and reversible
≤ 5 minutes
Prefer non-destructive controls first (block, isolate, limit, collect evidence)
Include a Windows PowerShell one-liner where applicable
Include actionable button labels for each step (for the popup).
Always include evidence preservation (file/log capture) using Windows paths below.

Evidence locations (use these defaults):
PCAP: C:\\ProgramData\\SecAssist\\evidence\\capture.pcapng
Logs bundle (zip): C:\\ProgramData\\SecAssist\\evidence\\logs.zip
Notes (txt): C:\\ProgramData\\SecAssist\\evidence\\notes.txt
(If a folder doesn't exist, include a command to create it in the first step that needs it.)

Confidence policy:
Use "Likely: <type> (confidence XX%)".
Escalate phrasing when confidence ≥ 70% (balanced).
If < 70%, say "Likely (low confidence)".

Hard rules:
Output only valid JSON exactly matching the schema below. No extra text.
Max 8 steps.
Each step.description ≤ 300 chars.
Only Windows commands in commands.windows.
No irreversible actions (do not shut down, delete, or factory reset).
Do not request raw payloads.

Output schema (strict):
{
  "classification": "Likely <attack_type> (confidence XX%)",
  "steps": [
    {
      "title": "short action title",
      "description": "what to do, concrete and reversible (≤300 chars)",
      "why": "one short reason (≤140 chars)",
      "estimated_seconds": 30,
      "button_label": "CTA text e.g., Block IP",
      "commands": {
        "windows": "single-line PowerShell or empty string"
      }
    }
  ],
  "notes": "optional one-liner"
}

Command style guidelines:
Prefer built-ins: New-NetFirewallRule, Set-NetFirewallProfile, Get-NetTCPConnection, Get-WinEvent, Compress-Archive, pktmon.
When blocking by IP, insert exact src_ip values from packet_headers.
For capture, prefer pktmon if available:
Start capture, stop after ~120s, and format to PCAPNG at the evidence path above.`;

export class GeminiService {
  private async makeRequest(input: AttackInput): Promise<SOCResponse> {
    const requestBody = {
      contents: [
        {
          parts: [
            {
              text: `${SOC_PROMPT}\n\nInput data:\n${JSON.stringify(input, null, 2)}`
            }
          ]
        }
      ],
      generationConfig: {
        temperature: 0.1,
        topK: 1,
        topP: 0.8,
        maxOutputTokens: 2048,
      }
    };

    const response = await fetch(`${GEMINI_API_URL}?key=${GEMINI_API_KEY}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      throw new Error(`Gemini API error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    
    if (!data.candidates || !data.candidates[0] || !data.candidates[0].content) {
      throw new Error('Invalid response from Gemini API');
    }

    const responseText = data.candidates[0].content.parts[0].text;
    
    try {
      // Clean the response text to extract JSON
      const jsonMatch = responseText.match(/\{[\s\S]*\}/);
      if (!jsonMatch) {
        throw new Error('No JSON found in response');
      }
      
      return JSON.parse(jsonMatch[0]) as SOCResponse;
    } catch (parseError) {
      console.error('Failed to parse Gemini response:', responseText);
      throw new Error('Failed to parse SOC response from Gemini');
    }
  }

  async analyzeAttack(input: AttackInput): Promise<SOCResponse> {
    try {
      return await this.makeRequest(input);
    } catch (error) {
      console.error('Gemini API error:', error);
      
      // Fallback response in case of API failure
      return {
        classification: `Likely: ${input.attack_type} (confidence 50%)`,
        steps: [
          {
            title: "Create Evidence Directory",
            description: "Create directory for storing security evidence and logs",
            why: "Prepare for evidence collection",
            estimated_seconds: 10,
            button_label: "Create Directory",
            commands: {
              windows: "New-Item -ItemType Directory -Path 'C:\\ProgramData\\SecAssist\\evidence' -Force"
            }
          },
          {
            title: "Block Suspicious IPs",
            description: `Block traffic from suspicious source IPs: ${input.packet_headers.map(h => h.src_ip).slice(0, 3).join(', ')}`,
            why: "Prevent further attack traffic",
            estimated_seconds: 30,
            button_label: "Block IPs",
            commands: {
              windows: `New-NetFirewallRule -DisplayName "Block-${input.attack_type}" -Direction Inbound -Action Block -RemoteAddress ${input.packet_headers[0]?.src_ip || '0.0.0.0'}`
            }
          },
          {
            title: "Capture Network Traffic",
            description: "Start packet capture to collect evidence of ongoing attack",
            why: "Preserve evidence for analysis",
            estimated_seconds: 120,
            button_label: "Start Capture",
            commands: {
              windows: "pktmon start --etw -p 0 -c C:\\ProgramData\\SecAssist\\evidence\\capture.etl"
            }
          }
        ],
        notes: "API temporarily unavailable - using fallback response"
      };
    }
  }
}

export const geminiService = new GeminiService();