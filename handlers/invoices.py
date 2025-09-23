# handlers/invoices.py
import aiohttp
from typing import Dict, Any, List

class InvoiceHandler:
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    async def get_invoices(self, api_key: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query invoices with optional filtering."""
        headers = {'X-Auth-Key': api_key}
        
        query_params = {}
        if params.get('clientId'):
            query_params['clientId'] = params['clientId']
        if params.get('startDate'):
            query_params['startDate'] = params['startDate']
        if params.get('endDate'):
            query_params['endDate'] = params['endDate']
        if params.get('status'):
            query_params['status'] = params['status']
        if params.get('practitionerEmail'):
            query_params['practitionerEmail'] = params['practitionerEmail']
        if params.get('number'):
            query_params['number'] = params['number']
        if params.get('page'):
            query_params['page'] = params['page']
        if params.get('lastUpdatedStartDate'):
            query_params['lastUpdatedStartDate'] = params['lastUpdatedStartDate']
        if params.get('lastUpdatedEndDate'):
            query_params['lastUpdatedEndDate'] = params['lastUpdatedEndDate']
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/invoices",
                headers=headers,
                params=query_params
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
    
    async def get_invoice(self, api_key: str, invoice_id: str) -> Dict[str, Any]:
        """Retrieve a single invoice by ID."""
        headers = {'X-Auth-Key': api_key}
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{self.base_url}/invoices/{invoice_id}",
                headers=headers
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status} - {await response.text()}")
