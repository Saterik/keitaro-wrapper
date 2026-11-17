from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Campaign schemas
class CampaignCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    geo_code: str = Field(..., min_length=2, max_length=10)
    offer_id: int = Field(..., gt=0)
    domain_id: Optional[int] = None
    group_id: Optional[int] = None
    traffic_source_id: Optional[int] = None


class CampaignUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    domain_id: Optional[int] = None
    group_id: Optional[int] = None
    traffic_source_id: Optional[int] = None


class CampaignResponse(BaseModel):
    id: int
    keitaro_campaign_id: int
    name: str
    alias: str
    geo_code: str
    offer_id: int
    domain_id: Optional[int] = None
    group_id: Optional[int] = None
    traffic_source_id: Optional[int] = None
    stream_1_id: Optional[int] = None
    stream_2_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class CampaignWithOffersResponse(CampaignResponse):
    offers: List["CampaignOfferResponse"] = []


# Campaign Offer schemas
class CampaignOfferCreate(BaseModel):
    keitaro_offer_id: int = Field(..., gt=0)


class CampaignOfferResponse(BaseModel):
    id: int
    campaign_id: int
    keitaro_offer_id: int
    offer_name: Optional[str] = None
    stream_id: Optional[int] = None
    position: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Keitaro resource schemas
class KeitaroDomain(BaseModel):
    id: int
    name: str
    state: Optional[str] = None
    default_campaign_id: Optional[int] = None
    wildcard: Optional[bool] = None
    catch_not_found: Optional[bool] = None
    notes: Optional[str] = None
    ssl_redirect: Optional[bool] = None
    allow_indexing: Optional[bool] = None


class KeitaroGroup(BaseModel):
    id: int
    name: str
    type: str
    position: int


class KeitaroTrafficSource(BaseModel):
    id: int
    name: str
    state: Optional[str] = None
    template_name: Optional[str] = None
    postback_url: Optional[str] = None


class KeitaroOffer(BaseModel):
    id: int
    name: str
    group_id: Optional[int] = None
    offer_type: Optional[str] = None
    action_type: Optional[str] = None
    action_payload: Optional[str] = None
    affiliate_network_id: Optional[int] = None
    payout_value: Optional[float] = None
    payout_currency: Optional[str] = None
    payout_type: Optional[str] = None
    state: Optional[str] = None
    country: Optional[list[str] | str] = None
    notes: Optional[str] = None


class KeitaroStream(BaseModel):
    id: int
    campaign_id: int
    name: str
    type: str
    action_type: str
    schema: str
    position: int
    weight: Optional[int] = None
    state: str
    action_options: Optional[dict] = None
    filters: Optional[List[dict]] = None
    offers: Optional[List[dict]] = None
    landings: Optional[List[dict]] = None


class KeitaroCampaign(BaseModel):
    id: int
    name: str
    alias: str
    state: str
    type: Optional[str] = None
    cost_type: Optional[str] = None
    cost_value: Optional[float] = None
    cost_currency: Optional[str] = None
    cost_auto: Optional[bool] = None
    group_id: Optional[int] = None
    token: Optional[str] = None
    traffic_source_id: Optional[int] = None
    bind_visitors: Optional[bool] = None
    domain_id: Optional[int] = None
    parameters: Optional[dict] = None
    postbacks: Optional[List[dict]] = None


# Stream creation schemas
class StreamCreate(BaseModel):
    campaign_id: int
    name: str
    type: str
    action_type: str
    schema: str
    position: Optional[int] = None
    weight: Optional[int] = None
    action_options: Optional[dict] = None
    comments: Optional[str] = None
    state: Optional[str] = "enabled"
    collect_clicks: Optional[bool] = None
    filter_or: Optional[bool] = None
    filters: Optional[List[dict]] = None
    triggers: Optional[List[dict]] = None
    landings: Optional[List[dict]] = None
    offers: Optional[List[dict]] = None


# Response wrappers
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    detail: Optional[str] = None