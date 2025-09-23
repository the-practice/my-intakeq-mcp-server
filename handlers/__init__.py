# handlers/__init__.py
"""Handler modules for IntakeQ MCP server."""

from .appointments import AppointmentHandler
from .clients import ClientHandler
from .invoices import InvoiceHandler
from .notes import NotesHandler

__all__ = ['AppointmentHandler', 'ClientHandler', 'InvoiceHandler', 'NotesHandler']