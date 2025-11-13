/**
 * JavaScript Example: Calling the Public Chat API
 * 
 * This example demonstrates how to call the public chat API using JavaScript/Node.js.
 * You need a Firebase authentication token to use this API.
 * 
 * Prerequisites:
 * 1. Install required packages: npm install axios
 * 2. Get a Firebase ID token from your client application
 */

const axios = require('axios');

class PublicChatAPIClient {
    /**
     * Initialize the API client
     * @param {string} baseUrl - Base URL of the API server
     * @param {string} firebaseToken - Firebase ID token for authentication
     */
    constructor(baseUrl = 'http://localhost:8000', firebaseToken = null) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.firebaseToken = firebaseToken;
        this.apiEndpoint = `${this.baseUrl}/api/public/chat`;
    }

    /**
     * Send a chat message to the API
     * @param {Object} options - Chat request options
     * @param {string} options.message - User's message/query
     * @param {Array} options.conversationHistory - Previous conversation messages
     * @param {string} options.llmProvider - LLM provider to use (default: "openai")
     * @param {boolean} options.isInitialResponse - Whether this is the first message
     * @param {string|null} options.conversationId - Optional conversation ID to continue
     * @returns {Promise<Object>} API response
     */
    async chat({
        message,
        conversationHistory = [],
        llmProvider = 'openai',
        isInitialResponse = false,
        conversationId = null
    }) {
        if (!this.firebaseToken) {
            throw new Error('Firebase token is required. Set it when initializing the client.');
        }

        const headers = {
            'Authorization': `Bearer ${this.firebaseToken}`,
            'Content-Type': 'application/json'
        };

        const payload = {
            message,
            conversation_history: conversationHistory,
            llm_provider: llmProvider,
            is_initial_response: isInitialResponse,
            conversation_id: conversationId
        };

        try {
            const response = await axios.post(this.apiEndpoint, payload, { headers });
            
            // Print rate limit headers
            console.log('Rate Limit Info:');
            console.log(`  Limit: ${response.headers['x-ratelimit-limit'] || 'N/A'}`);
            console.log(`  Remaining: ${response.headers['x-ratelimit-remaining'] || 'N/A'}`);
            console.log(`  Reset: ${response.headers['x-ratelimit-reset'] || 'N/A'}`);
            
            return response.data;
        } catch (error) {
            if (error.response) {
                const status = error.response.status;
                const data = error.response.data;
                
                if (status === 401) {
                    console.error('Error: Invalid or expired Firebase token');
                } else if (status === 403) {
                    console.error('Error: Permission denied - cannot access this conversation');
                } else if (status === 404) {
                    console.error('Error: Conversation not found');
                } else if (status === 429) {
                    console.error('Error: Rate limit exceeded');
                    console.error(`  Limit: ${error.response.headers['x-ratelimit-limit'] || 'N/A'}`);
                    console.error(`  Remaining: ${error.response.headers['x-ratelimit-remaining'] || 'N/A'}`);
                    console.error(`  Reset at: ${error.response.headers['x-ratelimit-reset'] || 'N/A'}`);
                } else {
                    console.error(`Error: ${status} - ${data.detail || 'Unknown error'}`);
                }
            } else {
                console.error(`Unexpected error: ${error.message}`);
            }
            throw error;
        }
    }
}

/**
 * Example usage
 */
async function exampleUsage() {
    // Initialize client with your Firebase token
    // In production, get this token from your Firebase Auth client
    const FIREBASE_TOKEN = 'YOUR_FIREBASE_TOKEN_HERE';
    
    // Configure API base URL
    // Development: http://localhost:8000
    // Production: https://your-domain.com (replace with your actual domain)
    const API_BASE_URL = process.env.API_BASE_URL || 'http://localhost:8000';
    
    // For production, uncomment and set:
    // const API_BASE_URL = 'https://your-domain.com';
    
    const client = new PublicChatAPIClient(API_BASE_URL, FIREBASE_TOKEN);
    
    try {
        // Example 1: Initial message (finding events)
        console.log('='.repeat(60));
        console.log('Example 1: Initial message - Finding events');
        console.log('='.repeat(60));
        
        const response = await client.chat({
            message: 'Find music concerts in New York this weekend',
            isInitialResponse: true
        });
        
        console.log(`\nResponse: ${response.message}`);
        console.log(`\nFound ${response.recommendations.length} recommendations`);
        
        if (response.extraction_summary) {
            console.log(`Extracted preferences: ${response.extraction_summary}`);
        }
        
        // Save conversation_id for continuing the conversation
        const conversationId = response.conversation_id;
        console.log(`\nConversation ID: ${conversationId}`);
        
        // Example 2: Continue conversation
        console.log('\n' + '='.repeat(60));
        console.log('Example 2: Continue conversation');
        console.log('='.repeat(60));
        
        const response2 = await client.chat({
            message: 'Show me more free events',
            conversationId: conversationId,
            isInitialResponse: false
        });
        
        console.log(`\nResponse: ${response2.message}`);
        console.log(`Found ${response2.recommendations.length} recommendations`);
        
    } catch (error) {
        console.error('Error:', error.message);
    }
}

// Run example (uncomment after setting FIREBASE_TOKEN)
// exampleUsage();

module.exports = PublicChatAPIClient;

