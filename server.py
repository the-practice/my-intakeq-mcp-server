#!/usr/bin/env python3
"""Web server wrapper for IntakeQ MCP Server."""

import os
import json
import logging
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import handlers
from handlers.appointments import AppointmentHandler
from handlers.clients import ClientHandler
from handlers.invoices import InvoiceHandler
from handlers.notes import NotesHandler
from handlers.questionnaires import QuestionnaireHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="IntakeQ MCP Server",
    description="MCP Server for IntakeQ API integration",
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

# Initialize handlers
BASE_URL = "https://intakeq.com/api/v1"
appointment_handler = AppointmentHandler(BASE_URL)
client_handler = ClientHandler(BASE_URL)
invoice_handler = InvoiceHandler(BASE_URL)
notes_handler = NotesHandler(BASE_URL)
questionnaire_handler = QuestionnaireHandler(BASE_URL)


@app.get("/")
async def root():
    """Root endpoint - server info."""
    return {
        "name": "intakeq-mcp-server",
        "version": "1.0.0",
        "status": "running",
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
    """Health check endpoint."""
    return {"status": "healthy"}


# Appointment endpoints
@app.get("/appointments")
async def get_appointments(
    x_auth_key: str = Header(..., description="IntakeQ API key"),
    client: Optional[str] = None,
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    status: Optional[str] = None,
    practitionerEmail: Optional[str] = None,
    page: Optional[int] = None
):
    """Query appointments with optional filtering."""
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
        
        result = await appointment_handler.get_appointments(x_auth_key, params)
        return result
    except Exception as e:
        logger.error(f"Error getting appointments: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/appointments/{appointment_id}")
async def get_appointment(
    appointment_id: str,
    x_auth_key: str = Header(..., description="IntakeQ API key")
):
    """Retrieve a single appointment by ID."""
    try:
        result = await appointment_handler.get_appointment(x_auth_key, appointment_id)
        return result
    except Exception as e:
        logger.error(f"Error getting appointment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/appointments")
async def create_appointment(
    request: Request,
    x_auth_key: str = Header(..., description="IntakeQ API key")
):
    """Create a new appointment."""
    try:
        data = await request.json()
        result = await appointment_handler.create_appointment(x_auth_key, data)
        return result
    except Exception as e:
        logger.error(f"Error creating appointment: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/appointments/settings")
async def get_booking_settings(
    x_auth_key: str = Header(..., description="IntakeQ API key")
):
    """Get booking settings (services, locations, practitioners)."""
    try:
        result = await appointment_handler.get_booking_settings(x_auth_key)
        return result
    except Exception as e:
        logger.error(f"Error getting booking settings: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Client endpoints
@app.get("/clients")
async def get_clients(
    x_auth_key: str = Header(..., description="IntakeQ API key"),
    search: Optional[str] = None,
    page: Optional[int] = None,
    includeProfile: Optional[bool] = None
):
    """Query clients with optional filtering."""
    try:
        params = {
            "search": search,
            "page": page,
            "includeProfile": includeProfile
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = await client_handler.get_clients(x_auth_key, params)
        return result
    except Exception as e:
        logger.error(f"Error getting clients: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clients")
async def create_client(
    request: Request,
    x_auth_key: str = Header(..., description="IntakeQ API key")
):
    """Create or update a client."""
    try:
        data = await request.json()
        result = await client_handler.create_or_update_client(x_auth_key, data)
        return result
    except Exception as e:
        logger.error(f"Error creating client: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Invoice endpoints
@app.get("/invoices")
async def get_invoices(
    x_auth_key: str = Header(..., description="IntakeQ API key"),
    clientId: Optional[int] = None,
    status: Optional[str] = None,
    startDate: Optional[str] = None,
    endDate: Optional[str] = None
):
    """Query invoices with optional filtering."""
    try:
        params = {
            "clientId": clientId,
            "status": status,
            "startDate": startDate,
            "endDate": endDate
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = await invoice_handler.get_invoices(x_auth_key, params)
        return result
    except Exception as e:
        logger.error(f"Error getting invoices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/invoices/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    x_auth_key: str = Header(..., description="IntakeQ API key")
):
    """Retrieve a single invoice by ID."""
    try:
        result = await invoice_handler.get_invoice(x_auth_key, invoice_id)
        return result
    except Exception as e:
        logger.error(f"Error getting invoice: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Notes endpoints
@app.get("/notes")
async def get_notes(
    x_auth_key: str = Header(..., description="IntakeQ API key"),
    client: Optional[str] = None,
    clientId: Optional[int] = None,
    status: Optional[int] = None
):
    """Query treatment notes summaries."""
    try:
        params = {
            "client": client,
            "clientId": clientId,
            "status": status
        }
        params = {k: v for k, v in params.items() if v is not None}
        
        result = await notes_handler.get_notes_summary(x_auth_key, params)
        return result
    except Exception as e:
        logger.error(f"Error getting notes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/notes/{note_id}")
async def get_note(
    note_id: str,
    x_auth_key: str = Header(..., description="IntakeQ API key")
):
    """Get full treatment note by ID."""
    try:
        result = await notes_handler.get_note(x_auth_key, note_id)
        return result
    except Exception as e:
        logger.error(f"Error getting note: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Questionnaire endpoints
@app.get("/questionnaires/templates")
async def get_questionnaire_templates(
    x_auth_key: str = Header(..., description="IntakeQ API key")
):
    """Get available questionnaire templates."""
    try:
        result = await questionnaire_handler.get_questionnaire_templates(x_auth_key)
        return result
    except Exception as e:
        logger.error(f"Error getting questionnaire templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/questionnaires/send")
async def send_questionnaire(
    request: Request,
    x_auth_key: str = Header(..., description="IntakeQ API key")
):
    """Send a questionnaire to a client."""
    try:
        data = await request.json()
        result = await questionnaire_handler.send_questionnaire(x_auth_key, data)
        return result
    except Exception as e:
        logger.error(f"Error sending questionnaire: {str(e)}")
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
    
    # Run the server
    uvicorn.run(
        "web_server:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
