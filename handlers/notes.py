# handlers/notes.py
import aiohttp
from typing import Dict, Any, List

class NotesHandler:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    async def get_notes_summary(self, api_key: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query treatment note summaries."""
        headers = {'X-Auth-Key': api_key}
        
        query_params = {}
        if params.get('client'):
            query_params['client'] = params['client']
        if params.get('clientId'):
            query_params['clientId'] = params['clientId']
        if params.get('status'):
            query_params['status'] = params['status']
        if params.get('startDate'):
            query_params['startDate'] = params['startDate']
        if params.get('endDate'):
            query_params['endDate'] = params['endDate']
        if params.get('page'):
            query_params['page'] = params['page']
        if params.get('updatedSince'):
            query_params['updatedSince'] = params['updatedSince']
        if params.get('deletedOnly'):
            query_params['deletedOnly'] = str(params['deletedOnly']).lower()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/notes/summary",
                headers=headers,
                params=query_params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
    
    async def get_note(self, api_key: str, note_id: str) -> Dict[str, Any]:
        """Get a full treatment note in JSON format."""
        headers = {'X-Auth-Key': api_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/notes/{note_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
    
    async def get_note_pdf(self, api_key: str, note_id: str) -> bytes:
        """Download a treatment note as PDF."""
        headers = {'X-Auth-Key': api_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/notes/{note_id}/pdf",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
