# handlers/questionnaires.py
import aiohttp
from typing import Dict, Any, List

class QuestionnaireHandler:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    async def get_intakes_summary(self, api_key: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query intake form summaries."""
        headers = {'X-Auth-Key': api_key}
        
        query_params = {}
        if params.get('client'):
            query_params['client'] = params['client']
        if params.get('startDate'):
            query_params['startDate'] = params['startDate']
        if params.get('endDate'):
            query_params['endDate'] = params['endDate']
        if params.get('page'):
            query_params['page'] = params['page']
        if params.get('all'):
            query_params['all'] = str(params['all']).lower()
        if params.get('clientId'):
            query_params['clientId'] = params['clientId']
        if params.get('externalClientId'):
            query_params['externalClientId'] = params['externalClientId']
        if params.get('updatedSince'):
            query_params['updatedSince'] = params['updatedSince']
        if params.get('deletedOnly'):
            query_params['deletedOnly'] = str(params['deletedOnly']).lower()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/intakes/summary",
                headers=headers,
                params=query_params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
    
    async def get_intake(self, api_key: str, intake_id: str) -> Dict[str, Any]:
        """Get a full intake form in JSON format."""
        headers = {'X-Auth-Key': api_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/intakes/{intake_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
    
    async def send_questionnaire(self, api_key: str, questionnaire_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send an intake package to a client."""
        headers = {
            'X-Auth-Key': api_key,
            'Content-Type': 'application/json'
        }
        
        # Validate required field
        if 'QuestionnaireId' not in questionnaire_data:
            raise ValueError("Missing required field: QuestionnaireId")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/intakes/send",
                headers=headers,
                json=questionnaire_data
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
    
    async def resend_questionnaire(self, api_key: str, resend_data: Dict[str, Any]) -> Dict[str, Any]:
        """Resend an existing intake package."""
        headers = {
            'X-Auth-Key': api_key,
            'Content-Type': 'application/json'
        }
        
        # Validate required field
        if 'IntakeId' not in resend_data:
            raise ValueError("Missing required field: IntakeId")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/intakes/resend",
                headers=headers,
                json=resend_data
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
    
    async def get_questionnaire_templates(self, api_key: str) -> List[Dict[str, Any]]:
        """Get a list of available questionnaire templates."""
        headers = {'X-Auth-Key': api_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/questionnaires",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
    
    async def get_practitioners(self, api_key: str) -> List[Dict[str, Any]]:
        """Get a list of practitioners in the account."""
        headers = {'X-Auth-Key': api_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/practitioners",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
    
    async def get_intake_pdf(self, api_key: str, intake_id: str) -> bytes:
        """Download a complete intake package as PDF."""
        headers = {'X-Auth-Key': api_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/intakes/{intake_id}/pdf",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
    
    async def update_office_use_questions(self, api_key: str, intake_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update answers to office use questions in an intake form."""
        headers = {
            'X-Auth-Key': api_key,
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/intakes",
                headers=headers,
                json=intake_data
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")