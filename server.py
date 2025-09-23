import asyncio
import json
import yaml
from typing import Any, Dict, List, Optional, Sequence
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from handlers.appointments import AppointmentHandler
from handlers.clients import ClientHandler
from handlers.invoices import InvoiceHandler
from handlers.notes import NotesHandler
from handlers.questionnaires import QuestionnaireHandler

class IntakeQMCPServer:
    def __init__(self):
        self.server = Server("intakeq-mcp-server")
        self.base_url = "https://intakeq.com/api/v1"
        
        # Initialize handlers
        self.appointment_handler = AppointmentHandler(self.base_url)
        self.client_handler = ClientHandler(self.base_url)
        self.invoice_handler = InvoiceHandler(self.base_url)
        self.notes_handler = NotesHandler(self.base_url)
        self.questionnaire_handler = QuestionnaireHandler(self.base_url)
        
        self.setup_tools()
    
    def setup_tools(self):
        """Register all available tools with the MCP server."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> list[Tool]:
            """List available tools."""
            return [
                # Appointment tools
                Tool(
                    name="get_appointments",
                    description="Query appointments with optional filtering",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "IntakeQ API key"},
                            "client": {"type": "string", "description": "Search by client name or email"},
                            "startDate": {"type": "string", "description": "Start date (yyyy-MM-dd)"},
                            "endDate": {"type": "string", "description": "End date (yyyy-MM-dd)"},
                            "status": {"type": "string", "enum": ["Confirmed", "Canceled", "WaitingConfirmation", "Declined", "Missed"]},
                            "practitionerEmail": {"type": "string", "description": "Filter by practitioner email"},
                            "page": {"type": "integer", "description": "Page number for pagination"}
                        },
                        "required": ["api_key"]
                    }
                ),
                Tool(
                    name="get_appointment",
                    description="Retrieve a single appointment by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "IntakeQ API key"},
                            "appointment_id": {"type": "string", "description": "Appointment ID"}
                        },
                        "required": ["api_key", "appointment_id"]
                    }
                ),
                Tool(
                    name="create_appointment",
                    description="Create a new appointment",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "IntakeQ API key"},
                            "practitioner_id": {"type": "string", "description": "Practitioner ID"},
                            "client_id": {"type": "integer", "description": "Client ID"},
                            "service_id": {"type": "string", "description": "Service ID"},
                            "location_id": {"type": "string", "description": "Location ID"},
                            "status": {"type": "string", "enum": ["Confirmed", "WaitingConfirmation"]},
                            "utc_datetime": {"type": "integer", "description": "Unix timestamp"},
                            "send_email_notification": {"type": "boolean", "default": True},
                            "reminder_type": {"type": "string", "enum": ["Sms", "Email", "Voice", "OptOut"]}
                        },
                        "required": ["api_key", "practitioner_id", "client_id", "service_id", "location_id", "status", "utc_datetime"]
                    }
                ),
                Tool(
                    name="get_booking_settings",
                    description="Get booking settings (services, locations, practitioners)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "IntakeQ API key"}
                        },
                        "required": ["api_key"]
                    }
                ),
                # Client tools
                Tool(
                    name="get_clients",
                    description="Query clients with optional filtering",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "IntakeQ API key"},
                            "search": {"type": "string", "description": "Search by name, email, or ID"},
                            "page": {"type": "integer", "description": "Page number"},
                            "includeProfile": {"type": "boolean", "description": "Include full profile"}
                        },
                        "required": ["api_key"]
                    }
                ),
                Tool(
                    name="create_client",
                    description="Create or update a client",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "IntakeQ API key"},
                            "client_data": {"type": "object", "description": "Client information"}
                        },
                        "required": ["api_key", "client_data"]
                    }
                ),
                # Invoice tools
                Tool(
                    name="get_invoices",
                    description="Query invoices with optional filtering",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "IntakeQ API key"},
                            "client_id": {"type": "integer", "description": "Filter by client ID"},
                            "status": {"type": "string", "enum": ["Draft", "Unpaid", "Paid", "PastDue", "Refunded", "Canceled"]},
                            "startDate": {"type": "string", "description": "Start date (yyyy-MM-dd)"},
                            "endDate": {"type": "string", "description": "End date (yyyy-MM-dd)"}
                        },
                        "required": ["api_key"]
                    }
                ),
                Tool(
                    name="get_invoice",
                    description="Retrieve a single invoice by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "IntakeQ API key"},
                            "invoice_id": {"type": "string", "description": "Invoice ID"}
                        },
                        "required": ["api_key", "invoice_id"]
                    }
                ),
                # Notes tools
                Tool(
                    name="get_notes",
                    description="Query treatment notes summaries",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "IntakeQ API key"},
                            "client": {"type": "string", "description": "Search by client name or email"},
                            "client_id": {"type": "integer", "description": "Filter by client ID"},
                            "status": {"type": "integer", "enum": [1, 2], "description": "1=locked, 2=unlocked"}
                        },
                        "required": ["api_key"]
                    }
                ),
                Tool(
                    name="get_note",
                    description="Get full treatment note by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "IntakeQ API key"},
                            "note_id": {"type": "string", "description": "Note ID"}
                        },
                        "required": ["api_key", "note_id"]
                    }
                ),
                # Questionnaire tools
                Tool(
                    name="get_questionnaire_templates",
                    description="Get available questionnaire templates",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "IntakeQ API key"}
                        },
                        "required": ["api_key"]
                    }
                ),
                Tool(
                    name="send_questionnaire",
                    description="Send a questionnaire to a client",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "IntakeQ API key"},
                            "questionnaire_id": {"type": "string", "description": "Questionnaire template ID"},
                            "client_id": {"type": "integer", "description": "Client ID"},
                            "client_name": {"type": "string", "description": "Client name"},
                            "client_email": {"type": "string", "description": "Client email"},
                            "practitioner_id": {"type": "string", "description": "Practitioner ID"}
                        },
                        "required": ["api_key", "questionnaire_id"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
            """Handle tool calls."""
            try:
                result = await self.route_tool_call(name, arguments)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                error_msg = f"Error calling tool {name}: {str(e)}"
                return [TextContent(type="text", text=error_msg)]
    
    async def route_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Route tool calls to appropriate handlers."""
        api_key = arguments.get('api_key')
        if not api_key:
            raise ValueError("API key is required")
        
        # Appointment tools
        if tool_name == "get_appointments":
            return await self.appointment_handler.get_appointments(api_key, arguments)
        elif tool_name == "get_appointment":
            return await self.appointment_handler.get_appointment(api_key, arguments['appointment_id'])
        elif tool_name == "create_appointment":
            appointment_data = {
                'PractitionerId': arguments['practitioner_id'],
                'ClientId': arguments['client_id'],
                'ServiceId': arguments['service_id'],
                'LocationId': arguments['location_id'],
                'Status': arguments['status'],
                'UtcDateTime': arguments['utc_datetime'],
                'SendClientEmailNotification': arguments.get('send_email_notification', True),
                'ReminderType': arguments.get('reminder_type', 'Email')
            }
            return await self.appointment_handler.create_appointment(api_key, appointment_data)
        elif tool_name == "get_booking_settings":
            return await self.appointment_handler.get_booking_settings(api_key)
        
        # Client tools
        elif tool_name == "get_clients":
            return await self.client_handler.get_clients(api_key, arguments)
        elif tool_name == "create_client":
            return await self.client_handler.create_or_update_client(api_key, arguments['client_data'])
        
        # Invoice tools
        elif tool_name == "get_invoices":
            return await self.invoice_handler.get_invoices(api_key, arguments)
        elif tool_name == "get_invoice":
            return await self.invoice_handler.get_invoice(api_key, arguments['invoice_id'])
        
        # Notes tools
        elif tool_name == "get_notes":
            return await self.notes_handler.get_notes_summary(api_key, arguments)
        elif tool_name == "get_note":
            return await self.notes_handler.get_note(api_key, arguments['note_id'])
        
        # Questionnaire tools
        elif tool_name == "get_questionnaire_templates":
            return await self.questionnaire_handler.get_questionnaire_templates(api_key)
        elif tool_name == "send_questionnaire":
            questionnaire_data = {
                'QuestionnaireId': arguments['questionnaire_id'],
                'ClientId': arguments.get('client_id'),
                'ClientName': arguments.get('client_name'),
                'ClientEmail': arguments.get('client_email'),
                'PractitionerId': arguments.get('practitioner_id')
            }
            return await self.questionnaire_handler.send_questionnaire(api_key, questionnaire_data)
        
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

async def main():
    """Main entry point."""
    server = IntakeQMCPServer()
    
    async with stdio_server() as streams:
        await server.server.run(
            streams[0], streams[1], InitializationOptions()
        )

if __name__ == "__main__":
    asyncio.run(main())                        },
                        "required": ["api_key", "appointment_id"]
                    }
                ),
                Tool(
                    name="create_appointment",
                    description="Create a new appointment",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "IntakeQ API key"},
                            "practitioner_id": {"type": "string", "description": "Practitioner ID"},
                            "client_id": {"type": "integer", "description": "Client ID"},
                            "service_id": {"type": "string", "description": "Service ID"},
                            "location_id": {"type": "string", "description": "Location ID"},
                            "status": {"type": "string", "enum": ["Confirmed", "WaitingConfirmation"]},
                            "utc_datetime": {"type": "integer", "description": "Unix timestamp"},
                            "send_email_notification": {"type": "boolean", "default": True},
                            "reminder_type": {"type": "string", "enum": ["Sms", "Email", "Voice", "OptOut"]}
                        },
                        "required": ["api_key", "practitioner_id", "client_id", "service_id", "location_id", "status", "utc_datetime"]
                    }
                ),
                Tool(
                    name="get_booking_settings",
                    description="Get booking settings (services, locations, practitioners)",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "IntakeQ API key"}
                        },
                        "required": ["api_key"]
                    }
                ),
                # Client tools
                Tool(
                    name="get_clients",
                    description="Query clients with optional filtering",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "IntakeQ API key"},
                            "search": {"type": "string", "description": "Search by name, email, or ID"},
                            "page": {"type": "integer", "description": "Page number"},
                            "includeProfile": {"type": "boolean", "description": "Include full profile"}
                        },
                        "required": ["api_key"]
                    }
                ),
                Tool(
                    name="create_client",
                    description="Create or update a client",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "IntakeQ API key"},
                            "client_data": {"type": "object", "description": "Client information"}
                        },
                        "required": ["api_key", "client_data"]
                    }
                ),
                # Invoice tools
                Tool(
                    name="get_invoices",
                    description="Query invoices with optional filtering",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "IntakeQ API key"},
                            "client_id": {"type": "integer", "description": "Filter by client ID"},
                            "status": {"type": "string", "enum": ["Draft", "Unpaid", "Paid", "PastDue", "Refunded", "Canceled"]},
                            "startDate": {"type": "string", "description": "Start date (yyyy-MM-dd)"},
                            "endDate": {"type": "string", "description": "End date (yyyy-MM-dd)"}
                        },
                        "required": ["api_key"]
                    }
                ),
                Tool(
                    name="get_invoice",
                    description="Retrieve a single invoice by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "IntakeQ API key"},
                            "invoice_id": {"type": "string", "description": "Invoice ID"}
                        },
                        "required": ["api_key", "invoice_id"]
                    }
                ),
                # Notes tools
                Tool(
                    name="get_notes",
                    description="Query treatment notes summaries",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "IntakeQ API key"},
                            "client": {"type": "string", "description": "Search by client name or email"},
                            "client_id": {"type": "integer", "description": "Filter by client ID"},
                            "status": {"type": "integer", "enum": [1, 2], "description": "1=locked, 2=unlocked"}
                        },
                        "required": ["api_key"]
                    }
                ),
                Tool(
                    name="get_note",
                    description="Get full treatment note by ID",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "IntakeQ API key"},
                            "note_id": {"type": "string", "description": "Note ID"}
                        },
                        "required": ["api_key", "note_id"]
                    }
                ),
                # Questionnaire tools
                Tool(
                    name="get_questionnaire_templates",
                    description="Get available questionnaire templates",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "IntakeQ API key"}
                        },
                        "required": ["api_key"]
                    }
                ),
                Tool(
                    name="send_questionnaire",
                    description="Send a questionnaire to a client",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "api_key": {"type": "string", "description": "IntakeQ API key"},
                            "questionnaire_id": {"type": "string", "description": "Questionnaire template ID"},
                            "client_id": {"type": "integer", "description": "Client ID"},
                            "client_name": {"type": "string", "description": "Client name"},
                            "client_email": {"type": "string", "description": "Client email"},
                            "practitioner_id": {"type": "string", "description": "Practitioner ID"}
                        },
                        "required": ["api_key", "questionnaire_id"]
                    }
                )
            ]
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: dict) -> Sequence[TextContent]:
            """Handle tool calls."""
            try:
                result = await self.route_tool_call(name, arguments)
                return [TextContent(type="text", text=json.dumps(result, indent=2))]
            except Exception as e:
                error_msg = f"Error calling tool {name}: {str(e)}"
                return [TextContent(type="text", text=error_msg)]
    
    async def route_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Route tool calls to appropriate handlers."""
        api_key = arguments.get('api_key')
        if not api_key:
            raise ValueError("API key is required")
        
        # Appointment tools
        if tool_name == "get_appointments":
            return await self.appointment_handler.get_appointments(api_key, arguments)
        elif tool_name == "get_appointment":
            return await self.appointment_handler.get_appointment(api_key, arguments['appointment_id'])
        elif tool_name == "create_appointment":
            appointment_data = {
                'PractitionerId': arguments['practitioner_id'],
                'ClientId': arguments['client_id'],
                'ServiceId': arguments['service_id'],
                'LocationId': arguments['location_id'],
                'Status': arguments['status'],
                'UtcDateTime': arguments['utc_datetime'],
                'SendClientEmailNotification': arguments.get('send_email_notification', True),
                'ReminderType': arguments.get('reminder_type', 'Email')
            }
            return await self.appointment_handler.create_appointment(api_key, appointment_data)
        elif tool_name == "get_booking_settings":
            return await self.appointment_handler.get_booking_settings(api_key)
        
        # Client tools
        elif tool_name == "get_clients":
            return await self.client_handler.get_clients(api_key, arguments)
        elif tool_name == "create_client":
            return await self.client_handler.create_or_update_client(api_key, arguments['client_data'])
        
        # Invoice tools
        elif tool_name == "get_invoices":
            return await self.invoice_handler.get_invoices(api_key, arguments)
        elif tool_name == "get_invoice":
            return await self.invoice_handler.get_invoice(api_key, arguments['invoice_id'])
        
        # Notes tools
        elif tool_name == "get_notes":
            return await self.notes_handler.get_notes_summary(api_key, arguments)
        elif tool_name == "get_note":
            return await self.notes_handler.get_note(api_key, arguments['note_id'])
        
        # Questionnaire tools
        elif tool_name == "get_questionnaire_templates":
            return await self.questionnaire_handler.get_questionnaire_templates(api_key)
        elif tool_name == "send_questionnaire":
            questionnaire_data = {
                'QuestionnaireId': arguments['questionnaire_id'],
                'ClientId': arguments.get('client_id'),
                'ClientName': arguments.get('client_name'),
                'ClientEmail': arguments.get('client_email'),
                'PractitionerId': arguments.get('practitioner_id')
            }
            return await self.questionnaire_handler.send_questionnaire(api_key, questionnaire_data)
        
        else:
            raise ValueError(f"Unknown tool: {tool_name}")

async def main():
    """Main entry point."""
    server = IntakeQMCPServer()
    
    async with stdio_server() as streams:
        await server.server.run(
            streams[0], streams[1], InitializationOptions()
        )

if __name__ == "__main__":
    asyncio.run(main())        return f"{method.lower()}{clean_path}"
    
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
