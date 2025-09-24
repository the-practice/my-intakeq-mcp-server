#!/usr/bin/env python3
"""Web server wrapper for IntakeQ MCP Server with VAPI authentication."""

import os
import json
import logging
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Header, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import handlers
from handlers.appointments import AppointmentHandler
from handlers.clients import ClientHandler
from handlers.invoices import InvoiceHandler
from handlers.notes import NotesHandler
from handlers.questionnaires import QuestionnaireHandler
from fastapi_mcp import FastApiMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security configuration
VAPI_AUTH_TOKEN = os.environ.get("VAPI_AUTH_TOKEN", "")  # Token that VAPI will send
INTAKEQ_API_KEY = os.environ.get("INTAKEQ_API_KEY", "")  # Your actual IntakeQ API key

if not INTAKEQ_API_KEY:
    logger.warning("INTAKEQ_API_KEY not set in environment variables!")

if not VAPI_AUTH_TOKEN:
    logger.warning("VAPI_AUTH_TOKEN not set in environment variables! Authentication will be disabled.")

# Create FastAPI app
app = FastAPI(
    title="IntakeQ MCP Server",
    description="MCP Server for IntakeQ API integration with VAPI authentication",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer(auto_error=False)

# Initialize handlers
BASE_URL = "https://intakeq.com/api/v1"
appointment_handler = AppointmentHandler(BASE_URL)
client_handler = ClientHandler(BASE_URL)
invoice_handler = InvoiceHandler(BASE_URL)
notes_handler = NotesHandler(BASE_URL)
questionnaire_handler = QuestionnaireHandler(BASE_URL)

# Mount MCP transport at /mcp (exposes /mcp, /mcp/sse, etc.)
mcp = FastApiMCP(app)
mcp.mount_http()


async def verify_vapi_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> bool:
    """Verify the VAPI authentication token."""
    # If no VAPI token is configured, allow all requests (for testing)
    if not VAPI_AUTH_TOKEN:
        logger.warning("No VAPI_AUTH_TOKEN configured, skipping authentication")
        return True
    
    # Check if credentials were provided
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify the token
    if credentials.credentials != VAPI_AUTH_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return True


@app.get("/")
async def root():
    """Root endpoint - server info."""
    return {
        "name": "intakeq-mcp-server",
        "version": "1.0.0",
        "status": "running",
        "authentication": "Bearer token required" if VAPI_AUTH_TOKEN else "Disabled (no token configured)",
        "mcp": {
            "base": "/mcp",
            "sse": "/mcp/sse",
            "messages": "/mcp/messages"
        },
        "endpoints": {
            "appointments": "/appointments",
            "clients": "/clients",
            "invoices": "/invoices",
            "notes": "/notes",
            "questionnaires": "/questionnaires"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint - no auth required."""
    return {
        "status": "healthy",
        "intakeq_configured": bool(INTAKEQ_API_KEY),
        "auth_configured": bool(VAPI_AUTH_TOKEN)
    }


# Appointment endpoints
@app.get("/appointments")
async def get_appointments(
    authenticated: bool = Depends(verify_vapi_token),
    client: Optional[str] = None,
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    status: Optional[str] = None,
    practitionerEmail: Optional[str] = None,
    page: Optional[int] = None
):
    """Query appointments with optional filtering."""
    if not INTAKEQ_API_KEY:
        raise HTTPException(status_code=500, detail="IntakeQ API key not configured")
    
    try:
        params = {
            "client": client,
            "startDate": startDate,
            "endDate": endDate,
            "status": status,
            "practitionerEmail": practitionerEmail,
            "page": page
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        # Use internal IntakeQ API key
        result = await appointment_handler.get_appointments(INTAKEQ_API_KEY, params)
        return result
    except Exception as e:
        logger.error(f"Error getting appointments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/appointments/{appointment_id}")
async def get_appointment(
    appointment_id: str,
    authenticated: bool = Depends(verify_vapi_token)
):
    """Retrieve a single appointment by ID."""
    if not INTAKEQ_API_KEY:
        raise HTTPException(status_code=500, detail="IntakeQ API key not configured")
    
    try:
        result = await appointment_handler.get_appointment(INTAKEQ_API_KEY, appointment_id)
        return result
    except Exception as e:
        logger.error(f"Error getting appointment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/appointments")
async def create_appointment(
    request: Request,
    authenticated: bool = Depends(verify_vapi_token)
):
    """Create a new appointment."""
    if not INTAKEQ_API_KEY:
        raise HTTPException(status_code=500, detail="IntakeQ API key not configured")
    
    try:
        data = await request.json()
        result = await appointment_handler.create_appointment(INTAKEQ_API_KEY, data)
        return result
    except Exception as e:
        logger.error(f"Error creating appointment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/appointments")
async def update_appointment(
    request: Request,
    authenticated: bool = Depends(verify_vapi_token)
):
    """Update an existing appointment."""
    if not INTAKEQ_API_KEY:
        raise HTTPException(status_code=500, detail="IntakeQ API key not configured")
    
    try:
        data = await request.json()
        result = await appointment_handler.update_appointment(INTAKEQ_API_KEY, data)
        return result
    except Exception as e:
        logger.error(f"Error updating appointment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/appointments/cancel")
async def cancel_appointment(
    request: Request,
    authenticated: bool = Depends(verify_vapi_token)
):
    """Cancel an appointment."""
    if not INTAKEQ_API_KEY:
        raise HTTPException(status_code=500, detail="IntakeQ API key not configured")
    
    try:
        data = await request.json()
        appointment_id = data.get("appointment_id") or data.get("AppointmentId")
        reason = data.get("reason") or data.get("Reason")
        
        if not appointment_id:
            raise HTTPException(status_code=400, detail="appointment_id is required")
        
        result = await appointment_handler.cancel_appointment(INTAKEQ_API_KEY, appointment_id, reason)
        return result
    except Exception as e:
        logger.error(f"Error canceling appointment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/appointments/settings")
async def get_booking_settings(
    authenticated: bool = Depends(verify_vapi_token)
):
    """Get booking settings (services, locations, practitioners)."""
    if not INTAKEQ_API_KEY:
        raise HTTPException(status_code=500, detail="IntakeQ API key not configured")
    
    try:
        result = await appointment_handler.get_booking_settings(INTAKEQ_API_KEY)
        return result
    except Exception as e:
        logger.error(f"Error getting booking settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Client endpoints
@app.get("/clients")
async def get_clients(
    authenticated: bool = Depends(verify_vapi_token),
    search: Optional[str] = None,
    page: Optional[int] = None,
    includeProfile: Optional[bool] = None,
    dateCreatedStart: Optional[str] = None,
    dateCreatedEnd: Optional[str] = None
):
    """Query clients with optional filtering."""
    if not INTAKEQ_API_KEY:
        raise HTTPException(status_code=500, detail="IntakeQ API key not configured")
    
    try:
        params = {
            "search": search,
            "page": page,
            "includeProfile": includeProfile,
            "dateCreatedStart": dateCreatedStart,
            "dateCreatedEnd": dateCreatedEnd
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = await client_handler.get_clients(INTAKEQ_API_KEY, params)
        return result
    except Exception as e:
        logger.error(f"Error getting clients: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clients")
async def create_client(
    request: Request,
    authenticated: bool = Depends(verify_vapi_token)
):
    """Create or update a client."""
    if not INTAKEQ_API_KEY:
        raise HTTPException(status_code=500, detail="IntakeQ API key not configured")
    
    try:
        data = await request.json()
        result = await client_handler.create_or_update_client(INTAKEQ_API_KEY, data)
        return result
    except Exception as e:
        logger.error(f"Error creating client: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clients/{client_id}/tags")
async def add_client_tag(
    client_id: int,
    request: Request,
    authenticated: bool = Depends(verify_vapi_token)
):
    """Add a tag to a client."""
    if not INTAKEQ_API_KEY:
        raise HTTPException(status_code=500, detail="IntakeQ API key not configured")
    
    try:
        data = await request.json()
        tag = data.get("tag")
        if not tag:
            raise HTTPException(status_code=400, detail="tag is required")
        
        result = await client_handler.add_client_tag(INTAKEQ_API_KEY, client_id, tag)
        return result
    except Exception as e:
        logger.error(f"Error adding client tag: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/clients/{client_id}/tags/{tag}")
async def remove_client_tag(
    client_id: int,
    tag: str,
    authenticated: bool = Depends(verify_vapi_token)
):
    """Remove a tag from a client."""
    if not INTAKEQ_API_KEY:
        raise HTTPException(status_code=500, detail="IntakeQ API key not configured")
    
    try:
        result = await client_handler.remove_client_tag(INTAKEQ_API_KEY, client_id, tag)
        return result
    except Exception as e:
        logger.error(f"Error removing client tag: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Invoice endpoints
@app.get("/invoices")
async def get_invoices(
    authenticated: bool = Depends(verify_vapi_token),
    clientId: Optional[int] = None,
    status: Optional[str] = None,
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    page: Optional[int] = None
):
    """Query invoices with optional filtering."""
    if not INTAKEQ_API_KEY:
        raise HTTPException(status_code=500, detail="IntakeQ API key not configured")
    
    try:
        params = {
            "clientId": clientId,
            "status": status,
            "startDate": startDate,
            "endDate": endDate,
            "page": page
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = await invoice_handler.get_invoices(INTAKEQ_API_KEY, params)
        return result
    except Exception as e:
        logger.error(f"Error getting invoices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    authenticated: bool = Depends(verify_vapi_token)
):
    """Retrieve a single invoice by ID."""
    if not INTAKEQ_API_KEY:
        raise HTTPException(status_code=500, detail="IntakeQ API key not configured")
    
    try:
        result = await invoice_handler.get_invoice(INTAKEQ_API_KEY, invoice_id)
        return result
    except Exception as e:
        logger.error(f"Error getting invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Notes endpoints
@app.get("/notes")
async def get_notes(
    authenticated: bool = Depends(verify_vapi_token),
    client: Optional[str] = None,
    clientId: Optional[int] = None,
    status: Optional[int] = None,
    page: Optional[int] = None
):
    """Query treatment notes summaries."""
    if not INTAKEQ_API_KEY:
        raise HTTPException(status_code=500, detail="IntakeQ API key not configured")
    
    try:
        params = {
            "client": client,
            "clientId": clientId,
            "status": status,
            "page": page
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = await notes_handler.get_notes_summary(INTAKEQ_API_KEY, params)
        return result
    except Exception as e:
        logger.error(f"Error getting notes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/notes/{note_id}")
async def get_note(
    note_id: str,
    authenticated: bool = Depends(verify_vapi_token)
):
    """Get full treatment note by ID."""
    if not INTAKEQ_API_KEY:
        raise HTTPException(status_code=500, detail="IntakeQ API key not configured")
    
    try:
        result = await notes_handler.get_note(INTAKEQ_API_KEY, note_id)
        return result
    except Exception as e:
        logger.error(f"Error getting note: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Questionnaire endpoints
@app.get("/questionnaires/templates")
async def get_questionnaire_templates(
    authenticated: bool = Depends(verify_vapi_token)
):
    """Get available questionnaire templates."""
    if not INTAKEQ_API_KEY:
        raise HTTPException(status_code=500, detail="IntakeQ API key not configured")
    
    try:
        result = await questionnaire_handler.get_questionnaire_templates(INTAKEQ_API_KEY)
        return result
    except Exception as e:
        logger.error(f"Error getting questionnaire templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/questionnaires/practitioners")
async def get_practitioners(
    authenticated: bool = Depends(verify_vapi_token)
):
    """Get list of practitioners."""
    if not INTAKEQ_API_KEY:
        raise HTTPException(status_code=500, detail="IntakeQ API key not configured")
    
    try:
        result = await questionnaire_handler.get_practitioners(INTAKEQ_API_KEY)
        return result
    except Exception as e:
        logger.error(f"Error getting practitioners: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/questionnaires/intakes")
async def get_intakes(
    authenticated: bool = Depends(verify_vapi_token),
    client: Optional[str] = None,
    clientId: Optional[int] = None,
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    page: Optional[int] = None
):
    """Get intake form summaries."""
    if not INTAKEQ_API_KEY:
        raise HTTPException(status_code=500, detail="IntakeQ API key not configured")
    
    try:
        params = {
            "client": client,
            "clientId": clientId,
            "startDate": startDate,
            "endDate": endDate,
            "page": page
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = await questionnaire_handler.get_intakes_summary(INTAKEQ_API_KEY, params)
        return result
    except Exception as e:
        logger.error(f"Error getting intakes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/questionnaires/intakes/{intake_id}")
async def get_intake(
    intake_id: str,
    authenticated: bool = Depends(verify_vapi_token)
):
    """Get a full intake form."""
    if not INTAKEQ_API_KEY:
        raise HTTPException(status_code=500, detail="IntakeQ API key not configured")
    
    try:
        result = await questionnaire_handler.get_intake(INTAKEQ_API_KEY, intake_id)
        return result
    except Exception as e:
        logger.error(f"Error getting intake: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/questionnaires/send")
async def send_questionnaire(
    request: Request,
    authenticated: bool = Depends(verify_vapi_token)
):
    """Send a questionnaire to a client."""
    if not INTAKEQ_API_KEY:
        raise HTTPException(status_code=500, detail="IntakeQ API key not configured")
    
    try:
        data = await request.json()
        result = await questionnaire_handler.send_questionnaire(INTAKEQ_API_KEY, data)
        return result
    except Exception as e:
        logger.error(f"Error sending questionnaire: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/questionnaires/resend")
async def resend_questionnaire(
    request: Request,
    authenticated: bool = Depends(verify_vapi_token)
):
    """Resend an existing questionnaire."""
    if not INTAKEQ_API_KEY:
        raise HTTPException(status_code=500, detail="IntakeQ API key not configured")
    
    try:
        data = await request.json()
        result = await questionnaire_handler.resend_questionnaire(INTAKEQ_API_KEY, data)
        return result
    except Exception as e:
        logger.error(f"Error resending questionnaire: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Error handler
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    # Get port from environment variable (Render sets this)
    port = int(os.environ.get("PORT", 8000))
    
    # Log configuration status
    logger.info(f"Starting IntakeQ MCP Server on port {port}")
    logger.info(f"VAPI Authentication: {'Enabled' if VAPI_AUTH_TOKEN else 'Disabled'}")
    logger.info(f"IntakeQ API Key: {'Configured' if INTAKEQ_API_KEY else 'Not configured'}")
    
    # Run the server
    uvicorn.run(
        "web_server:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
