# Self-MCP

A Model Context Protocol (MCP) server that provides unified access to one's professional profile, including experience, publications, career timeline, and social media presence.

[Self-MCP](self-mcp.png)

## Features

- **Profile Overview**: Fetch comprehensive background information
- **Experience Data**: Access detailed work experience and professional history
- **Publications**: Retrieve scientific publications and conference presentations
- **Career Timeline**: Get career progression and milestones
- **Social Media Integration**: Access to LinkedIn, Instagram, Facebook, and YouTube profiles
- **Content Search**: Search across all profile content
- **LLM Integration**: Works with free LLM endpoints (Ollama, Hugging Face)

## Installation

1. **Clone or download the code files**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Optional: Install the package**:
```bash
pip install -e .
```

## Quick Start

### Running the MCP Server

```bash
python haris_profile_server.py
```

The server runs using stdio transport and communicates via JSON-RPC messages.

### Running the Client

```bash
python mcp_client.py
```

This will start an interactive chat interface where you can ask questions about Haris Gulzar's profile.

## LLM Integration Options

The client supports multiple free LLM options:

### 1. Ollama (Recommended - Local)

Install Ollama locally:
```bash
# Install Ollama from https://ollama.ai/
ollama pull llama2  # or any other model
```

### 2. Hugging Face Inference API (Free Tier)

- No setup required for basic usage
- Optional: Get a free API token from https://huggingface.co/settings/tokens
- Set the token in the client code if you want higher rate limits

### 3. Other Free LLM APIs

You can easily extend the client to work with other free LLM services:
- Together AI
- Groq
- OpenRouter (free tier)
- Local models via llama.cpp, oobabooga, etc.

## Available Tools

The MCP server provides these tools:

1. **get_profile_overview**: Professional overview and background
2. **get_experience**: Work experience and professional history  
3. **get_publications**: Scientific publications and conferences
4. **get_career_timeline**: Career progression and milestones
5. **get_social_links**: Social media profiles and links
6. **search_profile_content**: Search across all profile content

## Usage Examples

### Interactive Chat Examples

```
You: Tell me about Haris Gulzar's background
You: What is his work experience?
You: Show me his publications
You: What are his social media profiles?
You: Search for machine learning in his profile
```

### Programmatic Usage

```python
from mcp_client import HarisProfileClient

client = HarisProfileClient()
await client.connect_to_server()

# Get overview
overview = await client.call_tool("get_profile_overview")
print(overview)

# Search for specific content
results = await client.call_tool("search_profile_content", {"query": "research"})
print(results)
```

## Deployment Options

### 1. Local Development
Run both server and client locally as shown above.

### 2. Docker Deployment

Create a `Dockerfile`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["python", "haris_profile_server.py"]
```

Build and run:
```bash
docker build -t haris-profile-mcp .
docker run -p 8000:8000 haris-profile-mcp
```

### 3. Cloud Deployment

The MCP server can be deployed to:
- **Heroku**: Create a `Procfile` with `worker: python haris_profile_server.py`
- **Railway**: Direct deployment from Git repository
- **Google Cloud Run**: Use the Dockerfile above
- **AWS Lambda**: Requires adaptation for serverless environment

## Configuration

### Environment Variables

Create a `.env` file:
```bash
# Optional LLM API keys
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
HUGGINGFACE_API_KEY=your_key_here

# Server configuration
SERVER_PORT=8000
LOG_LEVEL=INFO

# Timeout settings
HTTP_TIMEOUT=30
MCP_TIMEOUT=60
```

### Custom Configuration

You can customize the server by modifying the profile URLs and social media links in `haris_profile_server.py`:

```python
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
```

## Testing

### Test the MCP Server

```bash
# Test server connectivity
python -c "
import asyncio
from mcp_client import HarisProfileClient

async def test():
    client = HarisProfileClient()
    connected = await client.connect_to_server()
    print('Connected:', connected)
    if connected:
        tools = await client.get_available_tools()
        print('Available tools:', len(tools))
        for tool in tools:
            print(f'  - {tool[\"name\"]}')

asyncio.run(test())
"
```

### Test Individual Tools

```bash
python -c "
import asyncio
from mcp_client import HarisProfileClient

async def test_tool():
    client = HarisProfileClient()
    await client.connect_to_server()
    
    # Test overview tool
    result = await client.call_tool('get_profile_overview')
    print('Overview result length:', len(result))
    print('First 200 chars:', result[:200])

asyncio.run(test_tool())
"
```

## Extending the Server

### Adding New Tools

To add new tools, modify the `_setup_handlers` method in `HarisProfileServer`:

```python
Tool(
    name="get_certifications",
    description="Fetch professional certifications",
    inputSchema={
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "Certification category"
            }
        },
        "required": []
    }
)
```

And add the corresponding handler:

```python
elif name == "get_certifications":
    category = arguments.get("category", "all") if arguments else "all"
    return await self._get_certifications(category)
```

### Adding New Data Sources

1. Add URL to `profile_urls` or create a new category
2. Implement a fetching method
3. Add the tool definition
4. Update the prompt template

### Custom Content Parsing

For better content extraction from specific sites, modify the `_fetch_and_parse_content` method:

```python
async def _fetch_and_parse_content(self, url: str) -> str:
    """Enhanced content parsing for specific sites"""
    response = await self.client.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Site-specific parsing logic
    if 'sites.google.com' in url:
        return self._parse_google_sites(soup)
    elif 'linkedin.com' in url:
        return self._parse_linkedin(soup)
    # Add more site-specific parsers
    
    return self._parse_generic(soup)
```

## Integration with Other MCP Clients

This server works with any MCP-compatible client:

### Claude Desktop Integration

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "haris-profile": {
      "command": "python",
      "args": ["/path/to/haris_profile_server.py"]
    }
  }
}
```

### Custom MCP Client

```python
from mcp import ClientSession
from mcp.client.stdio import stdio_client

async def custom_client():
    session = await stdio_client(StdioServerParameters(
        command="python",
        args=["haris_profile_server.py"]
    ))
    
    # List available tools
    tools = await session.list_tools()
    
    # Call a tool
    result = await session.call_tool("get_profile_overview")
    
    return result
```

## Monitoring and Logging

### Enable Detailed Logging

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('haris_profile_server.log'),
        logging.StreamHandler()
    ]
)
```

### Health Check Endpoint

For production deployments, consider adding a health check:

```python
from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "healthy", "server": "haris-profile-mcp"}

# Run alongside MCP server
if __name__ == "__main__":
    # Start FastAPI in background
    import threading
    threading.Thread(
        target=lambda: uvicorn.run(app, host="0.0.0.0", port=8001)
    ).start()
    
    # Start MCP server
    asyncio.run(main())
```

## Troubleshooting

### Common Issues

1. **Server won't start**:
   - Check Python version (3.8+ required)
   - Verify all dependencies are installed
   - Check for port conflicts

2. **Content fetching fails**:
   - Verify URLs are accessible
   - Check network connectivity
   - Review timeout settings

3. **LLM integration not working**:
   - For Ollama: Ensure service is running (`ollama serve`)
   - For HuggingFace: Check API limits and token
   - Verify network access to API endpoints

4. **Memory issues with large profiles**:
   - Implement content chunking
   - Add caching mechanisms
   - Limit content size in parsers

### Debug Mode

Run with debug logging:

```bash
PYTHONPATH=. python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
import asyncio
from haris_profile_server import main
asyncio.run(main())
"
```

## Performance Optimization

### Caching

Add caching to reduce repeated requests:

```python
import asyncio
from functools import lru_cache
from datetime import datetime, timedelta

class CachedContent:
    def __init__(self, content: str, timestamp: datetime):
        self.content = content
        self.timestamp = timestamp
    
    def is_expired(self, ttl_minutes: int = 60) -> bool:
        return datetime.now() - self.timestamp > timedelta(minutes=ttl_minutes)

# Add to HarisProfileServer class
self.content_cache = {}

async def _fetch_and_parse_content_cached(self, url: str) -> str:
    if url in self.content_cache and not self.content_cache[url].is_expired():
        return self.content_cache[url].content
    
    content = await self._fetch_and_parse_content(url)
    self.content_cache[url] = CachedContent(content, datetime.now())
    return content
```

### Async Optimization

Fetch multiple sources concurrently:

```python
async def _get_all_profile_data(self) -> Dict[str, str]:
    """Fetch all profile data concurrently"""
    tasks = [
        self._fetch_and_parse_content(url) 
        for url in self.profile_urls.values()
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    return {
        section: result if isinstance(result, str) else f"Error: {result}"
        for section, result in zip(self.profile_urls.keys(), results)
    }
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your improvements
4. Test thoroughly
5. Submit a pull request

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd haris-profile-mcp-server

# Install development dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
python -m pytest tests/

# Format code
black *.py
```

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For questions or issues:
- Create an issue in the repository
- Contact: harisgulzar@outlook.com
- Documentation: See README and code comments

---

*This MCP server provides a foundation for integrating personal/professional profile data with AI assistants. Extend and customize it based on your specific needs.*
