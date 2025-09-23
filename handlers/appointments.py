# handlers/appointments.py
import aiohttp
from typing import Dict, Any, List, Optional
from datetime import datetime

class AppointmentHandler:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    async def get_appointments(self, api_key: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query appointments with optional filtering."""
        headers = {'X-Auth-Key': api_key}
        
        # Build query parameters
        query_params = {}
        if params.get('client'):
            query_params['client'] = params['client']
        if params.get('startDate'):
            query_params['startDate'] = params['startDate']
        if params.get('endDate'):
            query_params['endDate'] = params['endDate']
        if params.get('status'):
            query_params['status'] = params['status']
        if params.get('practitionerEmail'):
            query_params['practitionerEmail'] = params['practitionerEmail']
        if params.get('page'):
            query_params['page'] = params['page']
        if params.get('updatedSince'):
            query_params['updatedSince'] = params['updatedSince']
        if params.get('deletedOnly'):
            query_params['deletedOnly'] = str(params['deletedOnly']).lower()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/appointments",
                headers=headers,
                params=query_params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
    
    async def get_appointment(self, api_key: str, appointment_id: str) -> Dict[str, Any]:
        """Retrieve a single appointment by ID."""
        headers = {'X-Auth-Key': api_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/appointments/{appointment_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
    
    async def create_appointment(self, api_key: str, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new appointment."""
        headers = {
            'X-Auth-Key': api_key,
            'Content-Type': 'application/json'
        }
        
        # Validate required fields
        required_fields = ['PractitionerId', 'ClientId', 'ServiceId', 'LocationId', 'Status', 'UtcDateTime']
        for field in required_fields:
            if field not in appointment_data:
                raise ValueError(f"Missing required field: {field}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/appointments",
                headers=headers,
                json=appointment_data
            ) as response:
                if response.status in [200, 201]:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
    
    async def update_appointment(self, api_key: str, appointment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing appointment."""
        headers = {
            'X-Auth-Key': api_key,
            'Content-Type': 'application/json'
        }
        
        # Validate required fields
        if 'Id' not in appointment_data or 'UtcDateTime' not in appointment_data:
            raise ValueError("Missing required fields: Id and UtcDateTime")
        
        async with aiohttp.ClientSession() as session:
            async with session.put(
                f"{self.base_url}/appointments",
                headers=headers,
                json=appointment_data
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
    
    async def cancel_appointment(self, api_key: str, appointment_id: str, reason: str = None) -> Dict[str, Any]:
        """Cancel an appointment."""
        headers = {
            'X-Auth-Key': api_key,
            'Content-Type': 'application/json'
        }
        
        data = {'AppointmentId': appointment_id}
        if reason:
            data['Reason'] = reason
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/appointments/cancellation",
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    return {"success": True, "message": "Appointment canceled successfully"}
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
    
    async def get_booking_settings(self, api_key: str) -> Dict[str, Any]:
        """Get booking settings (services, locations, practitioners)."""
        headers = {'X-Auth-Key': api_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/appointments/settings",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
