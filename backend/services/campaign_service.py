from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
import logging

from models import Campaign, CampaignOffer
from keitaro_client import keitaro_client
from schemas import CampaignCreate, CampaignOfferCreate
from config import settings

logger = logging.getLogger(__name__)


class CampaignService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_campaign(self, data: CampaignCreate) -> Campaign:
        """
        Create a new campaign in Keitaro with two streams:
        1. First stream: catches traffic from specified geo and redirects to Google
        2. Second stream: sends traffic to the specified offer
        """
        # Get default domain, group, traffic source if not provided
        domain_id = data.domain_id
        group_id = data.group_id
        traffic_source_id = data.traffic_source_id
        
        if not domain_id:
            domains = await keitaro_client.get_domains()
            if domains:
                domain_id = domains[0]["id"]
        
        if not group_id:
            groups = await keitaro_client.get_groups("campaigns")
            if groups:
                group_id = groups[0]["id"]
        
        if not traffic_source_id:
            sources = await keitaro_client.get_traffic_sources()
            if sources:
                traffic_source_id = sources[0]["id"]
        
        # Create campaign name with prefix
        full_name = f"{settings.campaign_prefix}{data.name}"
        
        # Create campaign in Keitaro
        campaign_data = {
            "name": full_name,
            "alias": full_name.lower().replace(" ", "-"),
            "state": "enabled",
            "cost_type": "CPC",
            "cost_value": 0,
            "cost_currency": "USD",
            "cost_auto": True,
            "group_id": group_id,
            "traffic_source_id": traffic_source_id,
            "domain_id": domain_id,
            "bind_visitors": True
        }
        
        keitaro_campaign = await keitaro_client.create_campaign(campaign_data)
        keitaro_campaign_id = keitaro_campaign["id"]
        
        # Create Stream 1: Geo filter -> Redirect to Google
        stream_1_data = {
            "campaign_id": keitaro_campaign_id,
            "name": "Geo Filter -> Google",
            "type": "regular",
            "action_type": "redirect",
            "schema": "redirect",
            "position": 1,
            "weight": 100,
            "state": "enabled",
            "action_options": {
                "url": "https://www.google.com",
                "redirect_type": "302"
            },
            "filters": [
                {
                    "name": "country",
                    "operator": "in",
                    "values": [data.geo_code.upper()]
                }
            ],
            "filter_or": False
        }
        
        stream_1 = await keitaro_client.create_stream(stream_1_data)
        stream_1_id = stream_1["id"]
        
        # Create Stream 2: Offer redirect (for all other traffic)
        # Get offer details
        offer = await keitaro_client.get_offer(data.offer_id)
        
        stream_2_data = {
            "campaign_id": keitaro_campaign_id,
            "name": f"Offer -> {offer.get('name', 'Offer')}",
            "type": "regular",
            "action_type": "offer",
            "schema": "offer",
            "position": 2,
            "weight": 100,
            "state": "enabled",
            "action_options": {},
            "offers": [
                {
                    "offer_id": data.offer_id,
                    "weight": 100
                }
            ],
            "filters": []
        }
        
        stream_2 = await keitaro_client.create_stream(stream_2_data)
        stream_2_id = stream_2["id"]
        
        # Save to local database
        campaign = Campaign(
            keitaro_campaign_id=keitaro_campaign_id,
            name=full_name,
            alias=keitaro_campaign["alias"],
            geo_code=data.geo_code.upper(),
            offer_id=data.offer_id,
            domain_id=domain_id,
            group_id=group_id,
            traffic_source_id=traffic_source_id,
            stream_1_id=stream_1_id,
            stream_2_id=stream_2_id
        )
        
        self.db.add(campaign)
        self.db.commit()
        self.db.refresh(campaign)
        
        # Add the initial offer to campaign_offers
        campaign_offer = CampaignOffer(
            campaign_id=campaign.id,
            keitaro_offer_id=data.offer_id,
            offer_name=offer.get("name"),
            stream_id=stream_2_id,
            position=1
        )
        
        self.db.add(campaign_offer)
        self.db.commit()
        
        logger.info(f"Created campaign {campaign.name} (Keitaro ID: {keitaro_campaign_id})")
        return campaign
    
    async def get_campaign(self, campaign_id: int) -> Optional[Campaign]:
        return self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
    
    async def get_campaign_by_keitaro_id(self, keitaro_id: int) -> Optional[Campaign]:
        return self.db.query(Campaign).filter(Campaign.keitaro_campaign_id == keitaro_id).first()
    
    async def list_campaigns(self, skip: int = 0, limit: int = 100) -> List[Campaign]:
        return self.db.query(Campaign).offset(skip).limit(limit).all()
    
    async def update_campaign(self, campaign_id: int, data: Dict[str, Any]) -> Optional[Campaign]:
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            return None
        
        update_data = {k: v for k, v in data.items() if v is not None}
        
        # Update in Keitaro if needed
        keitaro_update = {}
        if "domain_id" in update_data:
            keitaro_update["domain_id"] = update_data["domain_id"]
        if "group_id" in update_data:
            keitaro_update["group_id"] = update_data["group_id"]
        if "traffic_source_id" in update_data:
            keitaro_update["traffic_source_id"] = update_data["traffic_source_id"]
        if "name" in update_data:
            keitaro_update["name"] = update_data["name"]
        
        if keitaro_update:
            await keitaro_client.update_campaign(campaign.keitaro_campaign_id, keitaro_update)
        
        # Update local
        for key, value in update_data.items():
            if hasattr(campaign, key):
                setattr(campaign, key, value)
        
        self.db.commit()
        self.db.refresh(campaign)
        return campaign
    
    async def delete_campaign(self, campaign_id: int) -> bool:
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            return False
        
        # Delete from Keitaro
        try:
            await keitaro_client.delete_campaign(campaign.keitaro_campaign_id)
        except Exception as e:
            logger.warning(f"Failed to delete campaign from Keitaro: {e}")
        
        # Delete local
        self.db.delete(campaign)
        self.db.commit()
        return True
    
    # Offer management
    async def add_offer_to_campaign(self, campaign_id: int, data: CampaignOfferCreate) -> Optional[CampaignOffer]:
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            return None
        
        # Get offer details
        offer = await keitaro_client.get_offer(data.keitaro_offer_id)
        
        # Get current max position
        max_position = self.db.query(CampaignOffer).filter(
            CampaignOffer.campaign_id == campaign_id
        ).count()
        
        # Update the second stream in Keitaro to include the new offer
        # We need to get the current stream and update its offers
        stream = await keitaro_client.get_stream(campaign.stream_2_id)
        current_offers = stream.get("offers", [])
        
        # Add new offer to the stream
        current_offers.append({
            "offer_id": data.keitaro_offer_id,
            "weight": 100
        })
        
        # Update stream with new offers list
        await keitaro_client.update_stream(campaign.stream_2_id, {
            "offers": current_offers,
            "campaign_id": campaign.keitaro_campaign_id,
            "name": stream["name"],
            "type": stream["type"],
            "action_type": stream["action_type"],
            "schema": stream["schema"],
            "position": stream["position"],
            "weight": stream.get("weight"),
            "state": stream["state"],
            "action_options": stream.get("action_options", {}),
            "filters": stream.get("filters", [])
        })
        
        # Save to local database
        campaign_offer = CampaignOffer(
            campaign_id=campaign_id,
            keitaro_offer_id=data.keitaro_offer_id,
            offer_name=offer.get("name"),
            stream_id=campaign.stream_2_id,
            position=max_position + 1
        )
        
        self.db.add(campaign_offer)
        self.db.commit()
        self.db.refresh(campaign_offer)
        
        logger.info(f"Added offer {data.keitaro_offer_id} to campaign {campaign_id}")
        return campaign_offer
    
    async def remove_offer_from_campaign(self, campaign_id: int, offer_id: int) -> bool:
        campaign = await self.get_campaign(campaign_id)
        if not campaign:
            return False
        
        # Find the offer in local DB
        campaign_offer = self.db.query(CampaignOffer).filter(
            CampaignOffer.campaign_id == campaign_id,
            CampaignOffer.keitaro_offer_id == offer_id
        ).first()
        
        if not campaign_offer:
            return False
        
        # Update the stream in Keitaro to remove this offer
        stream = await keitaro_client.get_stream(campaign.stream_2_id)
        current_offers = stream.get("offers", [])
        
        # Remove the offer
        updated_offers = [o for o in current_offers if o.get("offer_id") != offer_id]
        
        await keitaro_client.update_stream(campaign.stream_2_id, {
            "offers": updated_offers,
            "campaign_id": campaign.keitaro_campaign_id,
            "name": stream["name"],
            "type": stream["type"],
            "action_type": stream["action_type"],
            "schema": stream["schema"],
            "position": stream["position"],
            "weight": stream.get("weight"),
            "state": stream["state"],
            "action_options": stream.get("action_options", {}),
            "filters": stream.get("filters", [])
        })
        
        # Delete from local DB
        self.db.delete(campaign_offer)
        self.db.commit()
        
        logger.info(f"Removed offer {offer_id} from campaign {campaign_id}")
        return True
    
    async def get_campaign_offers(self, campaign_id: int) -> List[CampaignOffer]:
        return self.db.query(CampaignOffer).filter(
            CampaignOffer.campaign_id == campaign_id
        ).order_by(CampaignOffer.position).all()