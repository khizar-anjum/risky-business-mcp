#!/usr/bin/env python3
"""
ElevenLabs Voice Briefing Module for CVE Threat Assessment
Provides high-quality text-to-speech with fallback to espeak
"""

import os
import requests
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_elevenlabs_voice_briefing(summary_text):
    """
    Generate voice briefing using ElevenLabs API
    
    Args:
        summary_text (str): The text to convert to speech
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Get configuration from environment
    api_key = os.getenv('ELEVENLABS_API_KEY')
    voice_id = os.getenv('ELEVENLABS_VOICE_ID', '21m00Tcm4TlvDq8ikWAM')
    model_id = os.getenv('ELEVENLABS_MODEL_ID', 'eleven_multilingual_v2')
    stability = float(os.getenv('ELEVENLABS_STABILITY', '0.5'))
    similarity = float(os.getenv('ELEVENLABS_SIMILARITY_BOOST', '0.75'))
    
    if not api_key:
        print("Error: ELEVENLABS_API_KEY not found in environment")
        return False
    
    # API endpoint
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    # Request headers
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": api_key
    }
    
    # Request body
    data = {
        "text": summary_text,
        "model_id": model_id,
        "voice_settings": {
            "stability": stability,
            "similarity_boost": similarity
        }
    }
    
    try:
        # Make API request
        print("[*] Generating voice briefing with ElevenLabs...")
        response = requests.post(url, json=data, headers=headers, timeout=30)
        
        if response.status_code == 200:
            # Save audio file
            audio_path = '/tmp/threat_briefing.mp3'
            with open(audio_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            
            print(f"[+] Voice briefing generated successfully: {audio_path}")
            
            # Play the audio file
            try:
                # Try mpg123 first (better quality)
                subprocess.run(['mpg123', '-q', audio_path], check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                try:
                    # Fallback to afplay on macOS
                    subprocess.run(['afplay', audio_path], check=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    try:
                        # Try ffplay as another fallback
                        subprocess.run(['ffplay', '-nodisp', '-autoexit', audio_path], 
                                     check=True, stderr=subprocess.DEVNULL)
                    except (subprocess.CalledProcessError, FileNotFoundError):
                        print("[-] Could not play audio. Please install mpg123 or use manual playback")
                        print(f"    Audio saved at: {audio_path}")
            
            return True
        else:
            print(f"[-] ElevenLabs API error: {response.status_code}")
            print(f"    Response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"[-] Network error calling ElevenLabs API: {e}")
        return False
    except Exception as e:
        print(f"[-] Unexpected error: {e}")
        return False

def generate_voice_with_fallback(summary_text):
    """
    Generate voice briefing with fallback to espeak if ElevenLabs fails
    """
    # Try ElevenLabs first
    if generate_elevenlabs_voice_briefing(summary_text):
        return True
    
    # Fallback to espeak
    print("[!] Falling back to espeak...")
    try:
        subprocess.run(['espeak', '-v', 'en+m3', '-s', '140', summary_text], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[-] Both ElevenLabs and espeak failed")
        # Save to file as last resort
        try:
            fallback_file = '/tmp/threat_briefing.txt'
            with open(fallback_file, 'w') as f:
                f.write(summary_text)
            print(f"[!] Voice generation failed. Text saved to: {fallback_file}")
        except Exception as e:
            print(f"[-] Could not save text to file: {e}")
        return False

# Test function
if __name__ == "__main__":
    test_text = "This is a test of the ElevenLabs voice briefing system. The API is working correctly."
    print("Testing ElevenLabs voice generation...")
    generate_voice_with_fallback(test_text)