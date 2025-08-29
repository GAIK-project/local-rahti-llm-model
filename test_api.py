#!/usr/bin/env python3
"""
Simple test for Gemma API on CSC Rahti 2
"""

import os

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BASE_URL = "https://gemma-llm-gaik.2.rahtiapp.fi"
API_KEY = os.getenv("API_KEY")

def test_gemma_api():
    """Test Gemma API with a simple prompt"""
    
    # Health check
    print("🔍 Testing health...")
    health = requests.get(f"{BASE_URL}/healthz")
    print(f"Health: {health.json()}")
    
    if not health.json().get("ready"):
        print("❌ API not ready")
        return
    
    # Test text generation
    print("\n🤖 Testing text generation...")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "prompt": "What is the capital of Finland?",
        "max_new_tokens": 50,
        "temperature": 0.7
    }
    
    response = requests.post(f"{BASE_URL}/v1/generate", headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Response: {result['output']}")
        print(f"\n🌐 Try docs: {BASE_URL}/docs")
    else:
        print(f"❌ Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_gemma_api()
    test_gemma_api()
