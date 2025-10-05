"""
ElevenLabs Text-to-Speech Service for Security Alerts
Handles server-side speech generation for enhanced security
"""

import asyncio
import aiohttp
import logging
from typing import Optional, Dict, Any
from pathlib import Path
import tempfile
import os

logger = logging.getLogger(__name__)

class ElevenLabsService:
    """Server-side ElevenLabs integration for security alerts"""
    
    def __init__(self, api_key: str = "sk_33e58084f0e24facac5a09da538ddd821fbc202becb6f2e5"):
        self.api_key = api_key
        self.base_url = "https://api.elevenlabs.io/v1"
        
        # Voice IDs for different alert types
        self.voice_ids = {
            "urgent": "pNInz6obpgDQGcFmaJgB",    # Adam - clear, authoritative
            "warning": "21m00Tcm4TlvDq8ikWAM",   # Rachel - professional  
            "critical": "AZnzlk1XvdvUeBnXmlld",  # Domi - intense
        }
    
    async def generate_speech_audio(
        self,
        text: str,
        voice: str = "urgent",
        stability: float = 0.5,
        similarity_boost: float = 0.8,
        style: float = 0.0,
        use_speaker_boost: bool = True
    ) -> Optional[bytes]:
        """Generate speech audio from text using ElevenLabs API"""
        
        try:
            voice_id = self.voice_ids.get(voice, self.voice_ids["urgent"])
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            
            headers = {
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
                "xi-api-key": self.api_key,
            }
            
            payload = {
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost,
                    "style": style,
                    "use_speaker_boost": use_speaker_boost,
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        logger.info(f"Generated speech audio: {len(audio_data)} bytes")
                        return audio_data
                    else:
                        error_text = await response.text()
                        logger.error(f"ElevenLabs API error: {response.status} - {error_text}")
                        return None
                        
        except Exception as e:
            logger.error(f"Speech generation failed: {e}")
            return None
    
    def create_security_alert_message(
        self,
        attack_type: str,
        source_ip: str,
        confidence: float,
        target_ip: str = None
    ) -> str:
        """Create urgent security alert message"""
        
        confidence_percent = int(confidence * 100)
        
        # Create clear, urgent message
        message_parts = [
            "ATTENTION! SECURITY ALERT!",
            f"You are under a high-confidence {attack_type} attack.",
            f"Source IP address {source_ip} detected with {confidence_percent} percent confidence."
        ]
        
        if target_ip:
            message_parts.append(f"Target: {target_ip}.")
        
        message_parts.extend([
            "Immediate security response required.",
            "Execute the recommended steps now to stop this threat.",
            "Do not ignore this alert."
        ])
        
        return " ".join(message_parts)
    
    def create_step_completion_message(self, step_number: int, step_title: str) -> str:
        """Create step completion announcement"""
        return f"Step {step_number} completed: {step_title}. Proceeding to next security action."
    
    def create_response_complete_message(self, total_steps: int) -> str:
        """Create completion message"""
        return f"Automated security response complete. All {total_steps} steps have been executed. Continue monitoring your network for additional threats."
    
    async def generate_alert_audio_stream(
        self,
        attack_type: str,
        source_ip: str,
        confidence: float,
        target_ip: str = None
    ) -> Optional[bytes]:
        """Generate complete alert audio for streaming to frontend"""
        
        try:
            logger.info(f"Generating alert audio for {attack_type} from {source_ip}")
            
            # Create alert message
            alert_message = self.create_security_alert_message(
                attack_type, source_ip, confidence, target_ip
            )
            
            logger.info(f"Alert message: {alert_message[:100]}...")
            
            # Generate audio with critical voice settings
            audio_data = await self.generate_speech_audio(
                text=alert_message,
                voice="critical",
                stability=0.3,  # More dynamic for urgency
                similarity_boost=0.9,
                use_speaker_boost=True
            )
            
            if audio_data:
                logger.info(f"Successfully generated {len(audio_data)} bytes of alert audio")
            else:
                logger.error("Failed to generate alert audio - no data returned")
            
            return audio_data
            
        except Exception as e:
            logger.error(f"Alert audio generation failed: {e}")
            return None

# Global service instance
elevenlabs_service = ElevenLabsService()