from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Campaign(Base):
    __tablename__ = "campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    keitaro_campaign_id = Column(Integer, unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    alias = Column(String(255), nullable=False)
    geo_code = Column(String(10), nullable=False)
    offer_id = Column(Integer, nullable=False)
    domain_id = Column(Integer, nullable=True)
    group_id = Column(Integer, nullable=True)
    traffic_source_id = Column(Integer, nullable=True)
    stream_1_id = Column(Integer, nullable=True)  # Google redirect stream
    stream_2_id = Column(Integer, nullable=True)  # Offer stream
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationship to track offers added to this campaign
    offers = relationship("CampaignOffer", back_populates="campaign", cascade="all, delete-orphan")


class CampaignOffer(Base):
    __tablename__ = "campaign_offers"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    keitaro_offer_id = Column(Integer, nullable=False)
    offer_name = Column(String(255), nullable=True)
    stream_id = Column(Integer, nullable=True)  # Stream ID in Keitaro for this offer
    position = Column(Integer, default=0)  # Position in the stream order
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    campaign = relationship("Campaign", back_populates="offers")