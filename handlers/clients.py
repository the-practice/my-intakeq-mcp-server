# handlers/clients.py
import aiohttp
from typing import Dict, Any, List

class ClientHandler:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    async def get_clients(self, api_key: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query clients with optional filtering."""
        headers = {'X-Auth-Key': api_key}
        
        query_params = {}
        if params.get('search'):
            query_params['search'] = params['search']
        if params.get('page'):
            query_params['page'] = params['page']
        if params.get('includeProfile'):
            query_params['includeProfile'] = str(params['includeProfile']).lower()
        if params.get('dateCreatedStart'):
            query_params['dateCreatedStart'] = params['dateCreatedStart']
        if params.get('dateCreatedEnd'):
            query_params['dateCreatedEnd'] = params['dateCreatedEnd']
        if params.get('dateUpdatedStart'):
            query_params['dateUpdatedStart'] = params['dateUpdatedStart']
        if params.get('dateUpdatedEnd'):
            query_params['dateUpdatedEnd'] = params['dateUpdatedEnd']
        if params.get('externalClientId'):
            query_params['externalClientId'] = params['externalClientId']
        if params.get('deletedOnly'):
            query_params['deletedOnly'] = str(params['deletedOnly']).lower()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/clients",
                headers=headers,
                params=query_params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
    
    async def create_or_update_client(self, api_key: str, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update a client."""
        headers = {
            'X-Auth-Key': api_key,
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/clients",
                headers=headers,
                json=client_data
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
    
    async def add_client_tag(self, api_key: str, client_id: int, tag: str) -> Dict[str, Any]:
        """Add a tag to a client."""
        headers = {
            'X-Auth-Key': api_key,
            'Content-Type': 'application/json'
        }
        
        data = {
            'ClientId': client_id,
            'Tag': tag
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/clientTags",
                headers=headers,
                json=data
            ) as response:
                if response.status == 200:
                    return {"success": True, "message": "Tag added successfully"}
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
    
    async def remove_client_tag(self, api_key: str, client_id: int, tag: str) -> Dict[str, Any]:
        """Remove a tag from a client."""
        headers = {'X-Auth-Key': api_key}
        
        params = {
            'clientId': client_id,
            'tag': tag
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.delete(
                f"{self.base_url}/clientTags",
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    return {"success": True, "message": "Tag removed successfully"}
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
    
    async def get_client_diagnoses(self, api_key: str, client_id: int) -> List[Dict[str, Any]]:
        """Get diagnoses for a specific client."""
        headers = {'X-Auth-Key': api_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/client/{client_id}/diagnoses",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
