# ElevenLabs Text-to-Speech Integration Plan

## Overview
This document outlines the plan to replace the current `espeak` voice generation with ElevenLabs API for higher quality, more natural-sounding voice briefings in the CVE Threat Assessment system.

## Current Implementation
- **Technology**: espeak (local TTS engine)
- **Method**: Subprocess call to espeak command
- **Voice**: Robotic, synthetic voice
- **Latency**: Instant (local processing)
- **Cost**: Free

## Proposed ElevenLabs Implementation

### 1. Prerequisites

#### Account Setup
1. Sign up for ElevenLabs account at https://elevenlabs.io
2. Navigate to Profile Settings
3. Copy your `xi-api-key`
4. Add key to `.env` file (already created)

#### Dependencies
```bash
# Python packages
pip install requests python-dotenv

# Audio playback (choose based on OS)
# Linux:
sudo apt-get install mpg123

# macOS:
brew install mpg123

# Alternative Python-based playback:
pip install playsound  # or pygame
```

### 2. API Endpoint Details

**Endpoint**: `POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}`

**Headers**:
```json
{
  "Accept": "audio/mpeg",
  "Content-Type": "application/json",
  "xi-api-key": "YOUR_API_KEY"
}
```

**Request Body**:
```json
{
  "text": "Your text to convert",
  "model_id": "eleven_multilingual_v2",
  "voice_settings": {
    "stability": 0.5,
    "similarity_boost": 0.75
  }
}
```

### 3. Implementation Code

```python
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
        return False
```

### 4. Integration with CLAUDE.md

Replace the current Step 6 implementation:

**Current**:
```python
subprocess.run(['espeak', '-v', 'en+m3', '-s', '140', summary_text])
```

**New**:
```python
# Import at the top of the file
from voice_briefing import generate_voice_with_fallback

# In Step 6
generate_voice_with_fallback(summary_text)
```

### 5. Available Voice Options

#### Professional Voices
- **Rachel** (`21m00Tcm4TlvDq8ikWAM`) - Calm, professional, news anchor style
- **Adam** (`pNInz6obpgDQGcFmaJgB`) - Deep, authoritative, masculine
- **Sarah** (`EXAVITQu4vr4xnSDxMaL`) - Young, friendly, energetic
- **George** (`JBFqnCBsd6RMkjVDRZzb`) - British accent, professional

#### Model Options
1. **eleven_multilingual_v2** (Default)
   - Highest quality
   - Supports 29+ languages
   - ~500ms latency

2. **eleven_turbo_v2_5**
   - Ultra-fast generation
   - 75ms latency
   - Ideal for real-time applications

3. **eleven_monolingual_v1**
   - English-optimized
   - Good balance of quality and speed

### 6. Voice Settings Explained

- **Stability** (0.0 - 1.0)
  - Lower values: More emotional, varied delivery
  - Higher values: More consistent, stable tone
  - Recommended: 0.5 for briefings

- **Similarity Boost** (0.0 - 1.0)
  - Lower values: More creative interpretation
  - Higher values: Closer to original voice profile
  - Recommended: 0.75 for clarity

### 7. Cost Considerations

#### Free Tier
- 10,000 characters/month
- ~3 minutes of audio
- Good for testing

#### Starter Plan ($5/month)
- 30,000 characters/month
- ~10 minutes of audio

#### Creator Plan ($22/month)
- 100,000 characters/month
- ~30 minutes of audio

### 8. Error Handling Strategy

1. **Primary**: Try ElevenLabs API
2. **Fallback 1**: If API fails, use espeak
3. **Fallback 2**: If both fail, save text to file
4. **Logging**: Record all failures for debugging

### 9. Security Best Practices

1. **Never commit `.env` file** - Add to `.gitignore`
2. **Use environment variables** for all sensitive data
3. **Implement rate limiting** to avoid exceeding quotas
4. **Cache generated audio** for repeated briefings
5. **Validate API responses** before processing

### 10. Testing Plan

1. **Unit Tests**:
   - Test API connection
   - Test voice generation with sample text
   - Test fallback mechanism

2. **Integration Tests**:
   - Test with actual CVE briefings
   - Test various text lengths
   - Test special characters and formatting

3. **Performance Tests**:
   - Measure API response times
   - Compare with espeak performance
   - Test under network issues

### 11. Migration Steps

1. **Phase 1**: Development
   - Set up ElevenLabs account
   - Add API key to `.env`
   - Implement `generate_elevenlabs_voice_briefing()` function
   - Test with sample texts

2. **Phase 2**: Integration
   - Add fallback mechanism
   - Update CLAUDE.md to use new function
   - Test with actual CVE assessments

3. **Phase 3**: Deployment
   - Update documentation
   - Monitor API usage
   - Gather user feedback

### 12. Monitoring & Maintenance

- **Track API usage** to avoid exceeding limits
- **Monitor audio quality** feedback
- **Update voice models** as new versions release
- **Review costs** monthly
- **Maintain fallback** systems

## Conclusion

The ElevenLabs integration will provide:
- ✅ Natural, professional voice quality
- ✅ Multiple voice options
- ✅ Multilingual support
- ✅ Adjustable voice characteristics
- ✅ Fallback to espeak for reliability

Trade-offs:
- ❌ Requires API key and internet connection
- ❌ Has usage limits and potential costs
- ❌ Slightly higher latency than local TTS
- ❌ Dependency on external service

The implementation provides a robust solution with proper error handling and fallback mechanisms to ensure voice briefings are always available.