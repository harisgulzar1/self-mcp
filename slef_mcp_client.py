#!/usr/bin/env python3
"""
MCP Client for Haris Gulzar Profile Server
Connects to the MCP server and integrates with free LLM endpoints.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional
import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("haris-profile-client")

class HarisProfileClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.http_client = httpx.AsyncClient(timeout=60.0)
        
    async def connect_to_server(self, server_path: str = "python haris_profile_server.py"):
        """Connect to the MCP server"""
        try:
            server_params = StdioServerParameters(
                command=server_path.split()[0],
                args=server_path.split()[1:] if len(server_path.split()) > 1 else [],
            )
            
            self.session = await stdio_client(server_params)
            logger.info("Connected to Haris Profile MCP Server")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to server: {e}")
            return False
    
    async def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools from the server"""
        if not self.session:
            raise RuntimeError("Not connected to server")
        
        result = await self.session.list_tools()
        return [{"name": tool.name, "description": tool.description} for tool in result.tools]
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> str:
        """Call a tool on the server"""
        if not self.session:
            raise RuntimeError("Not connected to server")
        
        try:
            result = await self.session.call_tool(tool_name, arguments or {})
            
            # Extract text content from the result
            content_parts = []
            for content in result.content:
                if hasattr(content, 'text'):
                    content_parts.append(content.text)
                else:
                    content_parts.append(str(content))
            
            return "\n".join(content_parts)
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return f"Error: {str(e)}"
    
    async def query_llm_with_context(self, user_query: str, context_data: str = "") -> str:
        """Query a free LLM with context from MCP tools"""
        
        # Using Ollama as an example free LLM endpoint
        # You can replace this with any other free LLM service
        try:
            # Try Ollama first (local)
            ollama_response = await self._query_ollama(user_query, context_data)
            if ollama_response:
                return ollama_response
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
        
        # Fallback to Hugging Face Inference API (free tier)
        try:
            hf_response = await self._query_huggingface(user_query, context_data)
            if hf_response:
                return hf_response
        except Exception as e:
            logger.warning(f"Hugging Face API error: {e}")
        
        # Final fallback - return context with basic formatting
        return self._format_basic_response(user_query, context_data)
    
    async def _query_ollama(self, query: str, context: str) -> Optional[str]:
        """Query local Ollama instance"""
        try:
            prompt = f"""Based on the following information about Haris Gulzar, please answer the user's question:

Context Information:
{context}

User Question: {query}

Please provide a comprehensive and helpful answer based on the available information."""

            response = await self.http_client.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "llama2",  # You can change this to any available model
                    "prompt": prompt,
                    "stream": False
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return None
    
    async def _query_huggingface(self, query: str, context: str) -> Optional[str]:
        """Query Hugging Face Inference API (free tier)"""
        try:
            # Using a free model from Hugging Face
            api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-large"
            
            prompt = f"Context: {context[:1000]}\n\nQuestion: {query}\n\nAnswer:"
            
            response = await self.http_client.post(
                api_url,
                json={"inputs": prompt},
                headers={"Authorization": "Bearer YOUR_HF_TOKEN"}  # Optional, works without token but with rate limits
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "").replace(prompt, "").strip()
        except Exception as e:
            logger.error(f"Hugging Face API error: {e}")
            return None
    
    def _format_basic_response(self, query: str, context: str) -> str:
        """Basic response formatting when no LLM is available"""
        return f"""Based on the available information about Haris Gulzar:

{context}

Your question: "{query}"

I've provided the relevant information above. For more detailed analysis, please consider setting up a local LLM (like Ollama) or using a cloud LLM service."""

    async def interactive_chat(self):
        """Interactive chat interface"""
        print("=== Haris Gulzar Profile Assistant ===")
        print("Ask questions about Haris's profile, experience, publications, etc.")
        print("Available commands:")
        print("- /tools : List available tools")
        print("- /help : Show this help")
        print("- /quit : Exit")
        print()
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.lower() in ['/quit', '/exit', 'quit', 'exit']:
                    break
                elif user_input.lower() == '/help':
                    print("Available commands:")
                    print("- Ask any question about Haris Gulzar")
                    print("- /tools : List available MCP tools")
                    print("- /help : Show this help")
                    print("- /quit : Exit")
                    continue
                elif user_input.lower() == '/tools':
                    tools = await self.get_available_tools()
                    print("Available tools:")
                    for tool in tools:
                        print(f"- {tool['name']}: {tool['description']}")
                    continue
                elif not user_input:
                    continue
                
                # Determine which tools to use based on the query
                relevant_tools = self._determine_relevant_tools(user_input)
                
                # Gather context from relevant tools
                context_parts = []
                for tool_name in relevant_tools:
                    print(f"Fetching information from {tool_name}...")
                    tool_result = await self.call_tool(tool_name)
                    context_parts.append(f"=== {tool_name} ===\n{tool_result}")
                
                context_data = "\n\n".join(context_parts)
                
                # Query LLM with context
                print("Generating response...")
                response = await self.query_llm_with_context(user_input, context_data)
                print(f"Assistant: {response}\n")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def _determine_relevant_tools(self, query: str) -> List[str]:
        """Determine which tools are most relevant for the query"""
        query_lower = query.lower()
        tools = []
        
        # Keywords to tool mapping
        tool_keywords = {
            "get_profile_overview": ["overview", "about", "background", "who is", "introduction"],
            "get_experience": ["experience", "work", "job", "career", "professional", "employment"],
            "get_publications": ["publication", "paper", "research", "conference", "academic"],
            "get_career_timeline": ["timeline", "history", "when", "career path", "progression"],
            "get_social_links": ["social", "linkedin", "instagram", "facebook", "youtube", "contact"]
        }
        
        # Check for specific keywords
        for tool, keywords in tool_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                tools.append(tool)
        
        # If no specific tools found, use general tools
        if not tools:
            tools = ["get_profile_overview", "get_experience"]
        
        # For search queries, add search tool
        if any(word in query_lower for word in ["find", "search", "look for", "about"]):
            search_query = query.replace("search for", "").replace("find", "").replace("look for", "").strip()
            if search_query:
                tools.insert(0, "search_profile_content")
        
        return tools[:3]  # Limit to 3 tools to avoid too much context

async def main():
    """Main function to run the client"""
    client = HarisProfileClient()
    
    # Connect to server
    print("Connecting to Haris Profile MCP Server...")
    if not await client.connect_to_server():
        print("Failed to connect to server. Make sure the server is running.")
        return
    
    # Start interactive chat
    await client.interactive_chat()
    
    print("Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())

