from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from database import get_db
from models import Campaign, CampaignOffer
from schemas import (
    CampaignCreate, CampaignUpdate, CampaignResponse, 
    CampaignWithOffersResponse, CampaignOfferCreate, CampaignOfferResponse,
    KeitaroDomain, KeitaroGroup, KeitaroTrafficSource, KeitaroOffer,
    APIResponse, ErrorResponse
)
from services.campaign_service import CampaignService
from keitaro_client import keitaro_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


# Keitaro resource endpoints (for dropdowns in UI) - MUST come before /{campaign_id}
@router.get("/resources/domains", response_model=List[KeitaroDomain])
async def get_domains():
    """Get all domains from Keitaro."""
    try:
        domains = await keitaro_client.get_domains()
        return domains
    except Exception as e:
        logger.error(f"Failed to get domains: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resources/groups", response_model=List[KeitaroGroup])
async def get_groups():
    """Get all campaign groups from Keitaro."""
    try:
        groups = await keitaro_client.get_groups("campaigns")
        return groups
    except Exception as e:
        logger.error(f"Failed to get groups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resources/traffic-sources", response_model=List[KeitaroTrafficSource])
async def get_traffic_sources():
    """Get all traffic sources from Keitaro."""
    try:
        sources = await keitaro_client.get_traffic_sources()
        return sources
    except Exception as e:
        logger.error(f"Failed to get traffic sources: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resources/offers", response_model=List[KeitaroOffer])
async def get_offers():
    """Get all offers from Keitaro."""
    try:
        offers = await keitaro_client.get_offers()
        return offers
    except Exception as e:
        logger.error(f"Failed to get offers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("", response_model=CampaignResponse, status_code=201)
async def create_campaign(
    data: CampaignCreate,
    db: Session = Depends(get_db)
):
    """Create a new campaign with two streams: geo filter to Google and offer redirect."""
    service = CampaignService(db)
    try:
        campaign = await service.create_campaign(data)
        return campaign
    except Exception as e:
        logger.error(f"Failed to create campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[CampaignResponse])
async def list_campaigns(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """List all campaigns."""
    service = CampaignService(db)
    campaigns = await service.list_campaigns(skip, limit)
    return campaigns


@router.get("/{campaign_id}", response_model=CampaignWithOffersResponse)
async def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db)
):
    """Get a campaign by ID with its offers."""
    service = CampaignService(db)
    campaign = await service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    offers = await service.get_campaign_offers(campaign_id)
    
    # Build response with offers
    response = CampaignWithOffersResponse.model_validate(campaign)
    response.offers = [CampaignOfferResponse.model_validate(o) for o in offers]
    return response


@router.put("/{campaign_id}", response_model=CampaignResponse)
async def update_campaign(
    campaign_id: int,
    data: CampaignUpdate,
    db: Session = Depends(get_db)
):
    """Update campaign settings."""
    service = CampaignService(db)
    campaign = await service.update_campaign(campaign_id, data.model_dump(exclude_unset=True))
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign


@router.delete("/{campaign_id}", response_model=APIResponse)
async def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db)
):
    """Delete a campaign."""
    service = CampaignService(db)
    success = await service.delete_campaign(campaign_id)
    if not success:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return APIResponse(success=True, message="Campaign deleted successfully")


# Offer management endpoints
@router.post("/{campaign_id}/offers", response_model=CampaignOfferResponse, status_code=201)
async def add_offer_to_campaign(
    campaign_id: int,
    data: CampaignOfferCreate,
    db: Session = Depends(get_db)
):
    """Add an offer to an existing campaign."""
    service = CampaignService(db)
    campaign_offer = await service.add_offer_to_campaign(campaign_id, data)
    if not campaign_offer:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign_offer


@router.delete("/{campaign_id}/offers/{offer_id}", response_model=APIResponse)
async def remove_offer_from_campaign(
    campaign_id: int,
    offer_id: int,
    db: Session = Depends(get_db)
):
    """Remove an offer from a campaign."""
    service = CampaignService(db)
    success = await service.remove_offer_from_campaign(campaign_id, offer_id)
    if not success:
        raise HTTPException(status_code=404, detail="Campaign or offer not found")
    return APIResponse(success=True, message="Offer removed from campaign")


@router.get("/{campaign_id}/offers", response_model=List[CampaignOfferResponse])
async def get_campaign_offers(
    campaign_id: int,
    db: Session = Depends(get_db)
):
    """Get all offers in a campaign."""
    service = CampaignService(db)
    campaign = await service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    offers = await service.get_campaign_offers(campaign_id)
    return offers