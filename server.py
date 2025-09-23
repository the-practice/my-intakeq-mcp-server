import json
import asyncio
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
import yaml
import aiohttp

class IntakeQMCPServer:
    def __init__(self):
        self.server = Server("intakeq-mcp-server")
        self.openapi_spec = self.load_openapi_spec()
        self.base_url = "https://intakeq.com/api/v1"
        
    def load_openapi_spec(self):
        with open('openapi.yaml', 'r') as file:
            return yaml.safe_load(file)
    
    def setup_tools(self):
        # Generate tools from OpenAPI spec
        for path, methods in self.openapi_spec['paths'].items():
            for method, spec in methods.items():
                tool_name = self.generate_tool_name(path, method, spec)
                self.server.list_tools().append(self.create_tool_from_spec(
                    tool_name, path, method, spec
                ))
    
    def generate_tool_name(self, path, method, spec):
        # Convert OpenAPI operation to tool name
        operation_id = spec.get('operationId')
        if operation_id:
            return operation_id
        
        # Generate from path and method
        clean_path = path.replace('/', '_').replace('{', '').replace('}', '')
        return f"{method.lower()}{clean_path}"
    
    async def handle_tool_call(self, tool_name: str, arguments: Dict[str, Any]):
        # Route tool calls to appropriate handlers
        if tool_name.startswith('get_appointments'):
            return await self.get_appointments(arguments)
        elif tool_name.startswith('create_appointment'):
            return await self.create_appointment(arguments)
        # Add more handlers...
        
    async def get_appointments(self, params: Dict[str, Any]):
        # Implement API call to IntakeQ
        headers = {'X-Auth-Key': params.get('api_key', '')}
        query_params = {k: v for k, v in params.items() if k != 'api_key'}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/appointments",
                headers=headers,
                params=query_params
            ) as response:
                return await response.json()

async def main():
    server = IntakeQMCPServer()
    server.setup_tools()
    
    async with stdio_server() as streams:
        await server.server.run(
            streams[0], streams[1], InitializationOptions()
        )

if __name__ == "__main__":
    asyncio.run(main())
