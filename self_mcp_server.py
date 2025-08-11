#!/usr/bin/env python3
"""
MCP Server for Haris Gulzar Profile Integration
Provides unified access to profile information, experiences, publications, and social media.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Sequence
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
import re

# MCP SDK imports
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.types import (
    # CallToolRequestParams,
    CallToolResult,
    # ListPromptsRequestParams,
    ListPromptsResult,
    # ListToolsRequestParams,
    ListToolsResult,
    # GetPromptRequestParams,
    GetPromptResult,
    Prompt,
    PromptMessage,
    TextContent,
    Tool,
)
from mcp.types import (
    JSONRPCMessage,
    JSONRPCNotification,
    JSONRPCRequest,
    JSONRPCResponse,
)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("haris-profile-server")

class HarisProfileServer:
    def __init__(self):
        self.server = Server("haris-profile-server")
        self.client = httpx.AsyncClient(timeout=30.0)
        
        # Profile data URLs
        self.profile_urls = {
            "overview": "https://sites.google.com/view/haris-gulzar/home",
            "experience": "https://sites.google.com/view/haris-gulzar/experience", 
            "publications": "https://sites.google.com/view/haris-gulzar/publications",
            "career_timeline": "https://sites.google.com/view/haris-gulzar/career-timeline"
        }
        
        # Social media URLs
        self.social_urls = {
            "linkedin": "https://www.linkedin.com/in/haris-gulzar/",
            "instagram": "https://www.instagram.com/japanviaharis/",
            "facebook": "https://www.facebook.com/mharisgulzar/",
            "youtube": "https://www.youtube.com/@japanviaharis"
        }
        
        # Setup handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_prompts()
        async def handle_list_prompts() -> ListPromptsResult:
            """List available prompts"""
            return ListPromptsResult(
                prompts=[
                    Prompt(
                        name="haris_profile_assistant",
                        description="Template prompt for Haris Gulzar profile information assistant",
                        arguments=[
                            {
                                "name": "query_type",
                                "description": "Type of information requested (overview, experience, publications, career, social)",
                                "required": False
                            }
                        ]
                    )
                ]
            )
        
        @self.server.get_prompt()
        async def handle_get_prompt(
            name: str, arguments: Optional[Dict[str, str]] = None
        ) -> GetPromptResult:
            """Get prompt template"""
            if name != "haris_profile_assistant":
                raise ValueError(f"Unknown prompt: {name}")
            
            query_type = arguments.get("query_type", "general") if arguments else "general"
            
            prompt_content = f"""You are an AI assistant with access to comprehensive information about Haris Gulzar, a professional with expertise in technology and research. You have access to the following information sources:

**Available Information:**
- Professional overview and background
- Work experience and career history
- Scientific publications and conference presentations
- Career timeline and milestones
- Social media profiles and content

**Your Role:**
- Provide accurate, comprehensive information about Haris Gulzar based on the available data
- Answer questions about his professional background, research, experience, and achievements
- Share relevant social media links when appropriate
- Maintain a professional and informative tone
- If asked about information not available in your sources, clearly state the limitations

**Current Query Context:** {query_type}

Please use the available tools to fetch the most relevant and up-to-date information to answer the user's questions about Haris Gulzar."""

            return GetPromptResult(
                description="Profile information assistant for Haris Gulzar",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(type="text", text=prompt_content)
                    )
                ]
            )
        
        @self.server.list_tools()
        async def handle_list_tools() -> ListToolsResult:
            """List available tools"""
            return ListToolsResult(
                tools=[
                    Tool(
                        name="get_profile_overview",
                        description="Fetch Haris Gulzar's professional overview and background information",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    ),
                    Tool(
                        name="get_experience",
                        description="Fetch detailed work experience and professional history",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    ),
                    Tool(
                        name="get_publications",
                        description="Fetch scientific publications and conference presentations",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    ),
                    Tool(
                        name="get_career_timeline",
                        description="Fetch career timeline and professional milestones",
                        inputSchema={
                            "type": "object",
                            "properties": {},
                            "required": []
                        }
                    ),
                    Tool(
                        name="get_social_links",
                        description="Get social media profiles and links",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "platform": {
                                    "type": "string",
                                    "description": "Specific platform (linkedin, instagram, facebook, youtube) or 'all' for all platforms",
                                    "enum": ["linkedin", "instagram", "facebook", "youtube", "all"]
                                }
                            },
                            "required": []
                        }
                    ),
                    Tool(
                        name="search_profile_content",
                        description="Search across all profile content for specific information",
                        inputSchema={
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "Search query to find specific information"
                                }
                            },
                            "required": ["query"]
                        }
                    )
                ]
            )
        
        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: Optional[Dict[str, Any]] = None
        ) -> CallToolResult:
            """Handle tool calls"""
            try:
                if name == "get_profile_overview":
                    return await self._get_profile_overview()
                elif name == "get_experience":
                    return await self._get_experience()
                elif name == "get_publications":
                    return await self._get_publications()
                elif name == "get_career_timeline":
                    return await self._get_career_timeline()
                elif name == "get_social_links":
                    platform = arguments.get("platform", "all") if arguments else "all"
                    return await self._get_social_links(platform)
                elif name == "search_profile_content":
                    if not arguments or "query" not in arguments:
                        raise ValueError("Query parameter is required for search")
                    return await self._search_profile_content(arguments["query"])
                else:
                    raise ValueError(f"Unknown tool: {name}")
            except Exception as e:
                logger.error(f"Error in tool {name}: {str(e)}")
                return CallToolResult(
                    content=[TextContent(type="text", text=f"Error: {str(e)}")]
                )
    
    async def _fetch_and_parse_content(self, url: str) -> str:
        """Fetch and parse content from a Google Sites page"""
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract main content from Google Sites
            content_parts = []
            
            # Try different selectors for Google Sites content
            selectors = [
                'div[data-dtype="d"]',  # Main content div
                '.zfr3Q',  # Text content
                '.uGdb3',  # Content sections
                'p', 'h1', 'h2', 'h3', 'li'  # Fallback to basic elements
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    for element in elements:
                        text = element.get_text(strip=True)
                        if text and len(text) > 10:  # Filter out very short snippets
                            content_parts.append(text)
                    break
            
            if content_parts:
                return "\n\n".join(content_parts[:20])  # Limit to avoid too much content
            else:
                # Fallback: get all text content
                return soup.get_text(separator='\n', strip=True)[:2000]
                
        except Exception as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return f"Unable to fetch content from {url}. Error: {str(e)}"
    
    async def _get_profile_overview(self) -> CallToolResult:
        """Fetch profile overview"""
        content = await self._fetch_and_parse_content(self.profile_urls["overview"])
        return CallToolResult(
            content=[TextContent(
                type="text", 
                text=f"Profile Overview:\n\n{content}\n\nSource: {self.profile_urls['overview']}"
            )]
        )
    
    async def _get_experience(self) -> CallToolResult:
        """Fetch work experience"""
        content = await self._fetch_and_parse_content(self.profile_urls["experience"])
        return CallToolResult(
            content=[TextContent(
                type="text", 
                text=f"Work Experience:\n\n{content}\n\nSource: {self.profile_urls['experience']}"
            )]
        )
    
    async def _get_publications(self) -> CallToolResult:
        """Fetch publications"""
        content = await self._fetch_and_parse_content(self.profile_urls["publications"])
        return CallToolResult(
            content=[TextContent(
                type="text", 
                text=f"Publications and Conferences:\n\n{content}\n\nSource: {self.profile_urls['publications']}"
            )]
        )
    
    async def _get_career_timeline(self) -> CallToolResult:
        """Fetch career timeline"""
        content = await self._fetch_and_parse_content(self.profile_urls["career_timeline"])
        return CallToolResult(
            content=[TextContent(
                type="text", 
                text=f"Career Timeline:\n\n{content}\n\nSource: {self.profile_urls['career_timeline']}"
            )]
        )
    
    async def _get_social_links(self, platform: str = "all") -> CallToolResult:
        """Get social media links"""
        if platform == "all":
            social_info = "Social Media Profiles:\n\n"
            for platform_name, url in self.social_urls.items():
                social_info += f"• {platform_name.title()}: {url}\n"
        elif platform in self.social_urls:
            social_info = f"{platform.title()}: {self.social_urls[platform]}"
        else:
            social_info = f"Platform '{platform}' not found. Available platforms: {', '.join(self.social_urls.keys())}"
        
        return CallToolResult(
            content=[TextContent(type="text", text=social_info)]
        )
    
    async def _search_profile_content(self, query: str) -> CallToolResult:
        """Search across all profile content"""
        results = []
        search_query = query.lower()
        
        for section_name, url in self.profile_urls.items():
            content = await self._fetch_and_parse_content(url)
            
            # Simple text search
            if search_query in content.lower():
                # Extract relevant paragraphs
                paragraphs = content.split('\n\n')
                relevant_paragraphs = [
                    p for p in paragraphs 
                    if search_query in p.lower() and len(p.strip()) > 20
                ]
                
                if relevant_paragraphs:
                    results.append({
                        "section": section_name.title(),
                        "url": url,
                        "matches": relevant_paragraphs[:3]  # Limit matches
                    })
        
        if results:
            search_results = f"Search results for '{query}':\n\n"
            for result in results:
                search_results += f"**{result['section']}:**\n"
                for match in result['matches']:
                    search_results += f"• {match[:200]}...\n"
                search_results += f"Source: {result['url']}\n\n"
        else:
            search_results = f"No results found for '{query}' in the profile content."
        
        return CallToolResult(
            content=[TextContent(type="text", text=search_results)]
        )
    
    async def run(self):
        """Run the MCP server"""
        from mcp.server.stdio import stdio_server
        
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="haris-profile-server",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=NotificationOptions(),
                        experimental_capabilities={}
                    )
                )
            )

async def main():
    """Main entry point"""
    server = HarisProfileServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())

