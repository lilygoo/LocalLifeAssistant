#!/usr/bin/env python3
"""
Python Example: Calling the Public Chat API

This example demonstrates how to call the public chat API using Python.
You need a Firebase authentication token to use this API.

Prerequisites:
1. Install required packages: pip install requests firebase-admin
2. Set up Firebase Admin SDK with credentials
3. Get a Firebase ID token from your client application
"""

import requests
import json
from typing import Dict, Any, Optional


class PublicChatAPIClient:
    """Client for calling the Public Chat API"""
    
    def __init__(self, base_url: str = "http://localhost:8000", firebase_token: str = None):
        """
        Initialize the API client
        
        Args:
            base_url: Base URL of the API server
            firebase_token: Firebase ID token for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.firebase_token = firebase_token
        self.api_endpoint = f"{self.base_url}/api/public/chat"
    
    def chat(
        self,
        message: str,
        conversation_history: list = None,
        llm_provider: str = "openai",
        is_initial_response: bool = False,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a chat message to the API
        
        Args:
            message: User's message/query
            conversation_history: Previous conversation messages
            llm_provider: LLM provider to use (default: "openai")
            is_initial_response: Whether this is the first message in conversation
            conversation_id: Optional conversation ID to continue existing conversation
            
        Returns:
            API response as dictionary
            
        Raises:
            requests.HTTPError: If API request fails
        """
        if not self.firebase_token:
            raise ValueError("Firebase token is required. Set it when initializing the client.")
        
        headers = {
            "Authorization": f"Bearer {self.firebase_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "message": message,
            "conversation_history": conversation_history or [],
            "llm_provider": llm_provider,
            "is_initial_response": is_initial_response,
            "conversation_id": conversation_id
        }
        
        try:
            response = requests.post(self.api_endpoint, json=payload, headers=headers)
            response.raise_for_status()
            
            # Print rate limit headers
            print(f"Rate Limit Info:")
            print(f"  Limit: {response.headers.get('X-RateLimit-Limit', 'N/A')}")
            print(f"  Remaining: {response.headers.get('X-RateLimit-Remaining', 'N/A')}")
            print(f"  Reset: {response.headers.get('X-RateLimit-Reset', 'N/A')}")
            
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print("Error: Invalid or expired Firebase token")
            elif e.response.status_code == 403:
                print("Error: Permission denied - cannot access this conversation")
            elif e.response.status_code == 404:
                print("Error: Conversation not found")
            elif e.response.status_code == 429:
                print("Error: Rate limit exceeded")
                print(f"  Limit: {e.response.headers.get('X-RateLimit-Limit', 'N/A')}")
                print(f"  Remaining: {e.response.headers.get('X-RateLimit-Remaining', 'N/A')}")
                print(f"  Reset at: {e.response.headers.get('X-RateLimit-Reset', 'N/A')}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise


def example_usage():
    """Example usage of the API client"""
    
    import os
    
    # Get Firebase token from environment variable or prompt user
    FIREBASE_TOKEN = os.getenv("FIREBASE_TOKEN")
    
    if not FIREBASE_TOKEN:
        print("\n❌ Error: Firebase token not found!")
        print("\nTo run this example, you need to set a Firebase authentication token.")
        print("\nOption 1: Set environment variable")
        print("  export FIREBASE_TOKEN='your_token_here'")
        print("  python backend/app/api/examples/python_example.py")
        print("\nOption 2: Get token from your frontend application")
        print("  1. Open your frontend app in browser")
        print("  2. Open browser console (F12)")
        print("  3. Run: firebase.auth().currentUser.getIdToken().then(token => console.log(token))")
        print("  4. Copy the token and set it as FIREBASE_TOKEN")
        print("\nOption 3: For testing, you can use the frontend's login flow")
        print("  The frontend automatically handles Firebase authentication")
        return
    
    # Configure API base URL
    # Development: http://localhost:8000
    # Production: https://your-domain.com (replace with your actual domain)
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    # For production, uncomment and set:
    # API_BASE_URL = "https://your-domain.com"
    
    print(f"\n🔗 Connecting to API at: {API_BASE_URL}")
    print(f"🔑 Using Firebase token: {FIREBASE_TOKEN[:20]}...")
    
    client = PublicChatAPIClient(
        base_url=API_BASE_URL,
        firebase_token=FIREBASE_TOKEN
    )
    
    # Example 1: Initial message (finding events)
    print("=" * 60)
    print("Example 1: Initial message - Finding events")
    print("=" * 60)
    
    try:
        response = client.chat(
            message="Find music concerts in New York this weekend",
            is_initial_response=True
        )
        
        print(f"\nResponse: {response['message']}")
        print(f"\nFound {len(response['recommendations'])} recommendations")
        
        if response.get('extraction_summary'):
            print(f"Extracted preferences: {response['extraction_summary']}")
        
        # Save conversation_id for continuing the conversation
        conversation_id = response['conversation_id']
        print(f"\nConversation ID: {conversation_id}")
        
        # Example 2: Continue conversation
        print("\n" + "=" * 60)
        print("Example 2: Continue conversation")
        print("=" * 60)
        
        response2 = client.chat(
            message="Show me more free events",
            conversation_id=conversation_id,
            is_initial_response=False
        )
        
        print(f"\nResponse: {response2['message']}")
        print(f"Found {len(response2['recommendations'])} recommendations")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("Public Chat API - Python Example")
    print("=" * 60)
    print("\nNote: You need to set a valid Firebase token to run this example.")
    print("Get your token from Firebase Auth in your client application.\n")
    
    # Run the example (will check for FIREBASE_TOKEN environment variable)
    example_usage()

