/**
 * ElevenLabs Text-to-Speech Integration - WORKING VERSION
 * Generates spoken alerts for high-confidence attack detections
 */

const BACKEND_API_URL = 'http://127.0.0.1:8000';

class ElevenLabsService {
    private backendUrl: string;
    private audioEnabled: boolean = false;

    constructor(backendUrl: string = BACKEND_API_URL) {
        this.backendUrl = backendUrl;
    }

    /**
     * Enable audio - must be called from user interaction
     */
    async enableAudio(): Promise<void> {
        try {
            // Create and play a minimal silent audio to unlock autoplay
            const silentAudio = new Audio();
            // Use a proper minimal WAV file (44 bytes, 1 sample of silence)
            silentAudio.src = 'data:audio/wav;base64,UklGRigAAABXQVZFZm10IBAAAAAAQESsAEBErAAAAAAAAgAQAGRhdGEEAAAAAAA=';
            silentAudio.volume = 0.01;
            silentAudio.muted = true; // Mute it completely

            // Try to play the silent audio
            await silentAudio.play();

            this.audioEnabled = true;
            console.log('✅ Audio enabled successfully');

        } catch (error) {
            console.warn('⚠️ Could not enable audio with silent audio:', error);

            // Try alternative method - create and resume audio context
            try {
                const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
                if (audioContext.state === 'suspended') {
                    await audioContext.resume();
                }
                this.audioEnabled = true;
                console.log('✅ Audio enabled via AudioContext');
            } catch (contextError) {
                console.warn('⚠️ AudioContext also failed:', contextError);
                this.audioEnabled = false;
                throw new Error('Could not enable audio - browser may be blocking autoplay');
            }
        }
    }

    /**
     * Play alert speech - WORKING VERSION
     */
    async playAlertSpeech(attackType: string, sourceIp: string, confidence: number): Promise<void> {
        try {
            console.log('🚨 Playing alert speech for:', attackType, 'from', sourceIp);

            // Auto-enable audio if not already enabled
            if (!this.audioEnabled) {
                await this.enableAudio();
            }

            if (!this.audioEnabled) {
                throw new Error('Audio not enabled - user interaction required');
            }

            // Use the backend alert endpoint
            const response = await fetch(`${this.backendUrl}/speech/alert`, {
                method: 'POST',
                headers: {
                    'Accept': 'audio/mpeg',
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    attack_type: attackType,
                    source_ip: sourceIp,
                    confidence: confidence,
                }),
            });

            if (!response.ok) {
                throw new Error(`Speech API error: ${response.status}`);
            }

            const audioBuffer = await response.arrayBuffer();
            console.log('✅ Got audio buffer:', audioBuffer.byteLength, 'bytes');

            const audioBlob = new Blob([audioBuffer], { type: 'audio/mpeg' });
            const audioUrl = URL.createObjectURL(audioBlob);

            const audio = new Audio(audioUrl);
            audio.volume = 0.8;

            // Play immediately
            await audio.play();
            console.log('✅ Audio playing!');

            // Clean up when done
            audio.addEventListener('ended', () => {
                URL.revokeObjectURL(audioUrl);
                console.log('🔊 Audio finished');
            });

        } catch (error) {
            console.error('❌ Speech failed:', error);
            throw error;
        }
    }

    /**
     * Check if audio is ready to play
     */
    isAudioReady(): boolean {
        return this.audioEnabled;
    }

    /**
     * Create urgent security alert message (for compatibility)
     */
    createAlertMessage(attackType: string, sourceIp: string, confidence: number): string {
        const confidencePercent = Math.round(confidence * 100);
        return `ATTENTION! You are under a high-confidence ${attackType} attack! Source IP address ${sourceIp} detected with ${confidencePercent} percent confidence. Immediate security response required.`;
    }

    /**
     * Create step completion announcement (for compatibility)
     */
    createStepMessage(stepNumber: number, stepTitle: string): string {
        return `Step ${stepNumber} completed: ${stepTitle}. Proceeding to next action.`;
    }

    /**
     * Create completion message (for compatibility)
     */
    createCompletionMessage(totalSteps: number): string {
        return `Security response complete. All ${totalSteps} steps have been executed. Continue monitoring for additional threats.`;
    }
}

export const elevenLabsService = new ElevenLabsService();