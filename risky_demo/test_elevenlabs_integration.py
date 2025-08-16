#!/usr/bin/env python3
"""
Test script for ElevenLabs integration with CVE Threat Assessment
"""

from voice_briefing import generate_voice_with_fallback

# Sample CVE briefing text
sample_briefing = """
Risky Business AI Assessment. Security Alert for CVE-2025-53770. 
This is a CRITICAL vulnerability with CVSS score 9.8. 
Company is SEVERELY AFFECTED with SharePoint Server 2019 on PROD-SP-01. 
IMMEDIATE patching required. Active exploitation confirmed in the wild with 7 available proof-of-concept exploits. 
Known ransomware usage. This concludes your threat briefing.
"""

print("=" * 60)
print("Testing ElevenLabs Voice Briefing Integration")
print("=" * 60)

print("\n[*] Generating voice briefing for sample CVE assessment...")
print(f"\nText to convert:\n{sample_briefing}")

success = generate_voice_with_fallback(sample_briefing)

if success:
    print("\n[+] Voice briefing test completed successfully!")
else:
    print("\n[-] Voice briefing test failed")

print("=" * 60)