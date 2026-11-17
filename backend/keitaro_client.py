import httpx
import json
from typing import Optional, Dict, Any, List
from config import settings


class KeitaroClient:
    def __init__(self, api_url: str = None, api_key: str = None):
        self.api_url = (api_url or settings.keitaro_api_url).rstrip('/')
        self.api_key = api_key or settings.keitaro_api_key
        self.base_url = f"{self.api_url}/admin_api/v1"
        
        self.client = httpx.AsyncClient(
            headers={"Api-Key": self.api_key},
            timeout=30.0
        )
    
    async def close(self):
        await self.client.aclose()
    
    def _build_url(self, endpoint: str) -> str:
        return f"{self.base_url}/{endpoint.lstrip('/')}"
    
    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[Any, Any]:
        url = self._build_url(endpoint)
        response = await self.client.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    # Campaigns
    async def create_campaign(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "campaigns", json=data)
    
    async def get_campaign(self, campaign_id: int) -> Dict[str, Any]:
        return await self._request("GET", f"campaigns/{campaign_id}")
    
    async def update_campaign(self, campaign_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("PUT", f"campaigns/{campaign_id}", json=data)
    
    async def delete_campaign(self, campaign_id: int) -> Dict[str, Any]:
        return await self._request("DELETE", f"campaigns/{campaign_id}")
    
    async def get_campaigns(self, **params) -> List[Dict[str, Any]]:
        return await self._request("GET", "campaigns", params=params)
    
    async def enable_campaign(self, campaign_id: int) -> Dict[str, Any]:
        return await self._request("POST", f"campaigns/{campaign_id}/enable")
    
    async def disable_campaign(self, campaign_id: int) -> Dict[str, Any]:
        return await self._request("POST", f"campaigns/{campaign_id}/disable")
    
    # Streams
    async def create_stream(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "streams", json=data)
    
    async def get_stream(self, stream_id: int) -> Dict[str, Any]:
        return await self._request("GET", f"streams/{stream_id}")
    
    async def update_stream(self, stream_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        # Keitaro uses POST for stream updates
        return await self._request("POST", f"streams/{stream_id}", json=data)
    
    async def delete_stream(self, stream_id: int) -> Dict[str, Any]:
        return await self._request("DELETE", f"streams/{stream_id}")
    
    async def get_campaign_streams(self, campaign_id: int) -> List[Dict[str, Any]]:
        return await self._request("GET", f"campaigns/{campaign_id}/streams")
    
    async def enable_stream(self, stream_id: int) -> Dict[str, Any]:
        return await self._request("POST", f"streams/{stream_id}/enable")
    
    async def disable_stream(self, stream_id: int) -> Dict[str, Any]:
        return await self._request("POST", f"streams/{stream_id}/disable")
    
    async def get_stream_schemas(self) -> List[Dict[str, Any]]:
        return await self._request("GET", "stream_schemas")
    
    async def get_stream_types(self) -> List[Dict[str, Any]]:
        return await self._request("GET", "stream_types")
    
    async def get_stream_actions(self) -> List[Dict[str, Any]]:
        return await self._request("GET", "stream_actions")
    
    # Offers
    async def create_offer(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "offers", json=data)
    
    async def get_offer(self, offer_id: int) -> Dict[str, Any]:
        return await self._request("GET", f"offers/{offer_id}")
    
    async def get_offers(self, **params) -> List[Dict[str, Any]]:
        return await self._request("GET", "offers", params=params)
    
    async def update_offer(self, offer_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("PUT", f"offers/{offer_id}", json=data)
    
    async def delete_offer(self, offer_id: int) -> Dict[str, Any]:
        return await self._request("DELETE", f"offers/{offer_id}")
    
    # Domains
    async def get_domains(self, **params) -> List[Dict[str, Any]]:
        return await self._request("GET", "domains", params=params)
    
    async def get_domain(self, domain_id: int) -> Dict[str, Any]:
        return await self._request("GET", f"domains/{domain_id}")
    
    # Groups
    async def get_groups(self, group_type: str = "campaigns") -> List[Dict[str, Any]]:
        return await self._request("GET", "groups", params={"type": group_type})
    
    async def create_group(self, name: str, group_type: str = "campaigns", position: int = 0) -> Dict[str, Any]:
        return await self._request("POST", "groups", json={
            "name": name,
            "type": group_type,
            "position": position
        })
    
    # Traffic Sources
    async def get_traffic_sources(self, **params) -> List[Dict[str, Any]]:
        return await self._request("GET", "traffic_sources", params=params)
    
    async def get_traffic_source(self, source_id: int) -> Dict[str, Any]:
        return await self._request("GET", f"traffic_sources/{source_id}")
    
    async def create_traffic_source(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return await self._request("POST", "traffic_sources", json=data)


# Global client instance
keitaro_client = KeitaroClient()