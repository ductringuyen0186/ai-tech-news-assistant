"""
Health Models
============

Pydantic models for health check endpoints and responses.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ComponentHealth(BaseModel):
    """Health status of a system component."""
    
    name: Optional[str] = Field(None, description="Component name")
    status: str = Field(..., description="Component status")
    message: Optional[str] = Field(None, description="Status message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional component details")
    last_checked: Optional[datetime] = Field(None, description="Last check time")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ['healthy', 'degraded', 'unhealthy']
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v


class HealthResponse(BaseModel):
    """Overall health response."""
    
    status: str = Field(..., description="Overall status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    version: Optional[str] = Field(None, description="Application version")
    uptime: Optional[str] = Field(None, description="System uptime")
    components: Dict[str, Any] = Field(default_factory=dict, description="Component health statuses")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        valid_statuses = ['healthy', 'degraded', 'unhealthy']
        if v not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}")
        return v
    

class HealthCheck(BaseModel):
    """Health check response model."""
    
    model_config = ConfigDict(extra='allow')
    
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    version: Optional[str] = Field(None, description="Application version")
    uptime: Optional[str] = Field(None, description="Human readable uptime")
    uptime_seconds: Optional[float] = Field(None, description="Uptime in seconds")
    database: Optional[Dict[str, Any]] = Field(None, description="Database status")
    services: Optional[Dict[str, Any]] = Field(None, description="Service statuses")
    components: Optional[Dict[str, Any]] = Field(None, description="Component health details")
    

class PingResponse(BaseModel):
    """Ping response model."""
    
    message: str = Field(default="pong", description="Ping response")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class MetricsResponse(BaseModel):
    """Metrics response model."""
    
    uptime: float = Field(..., description="Uptime in seconds")
    memory_usage: Optional[Dict[str, Any]] = Field(None, description="Memory usage stats")
    cpu_usage: Optional[float] = Field(None, description="CPU usage percentage")
    request_count: Optional[int] = Field(None, description="Total request count")
    error_count: Optional[int] = Field(None, description="Total error count")
