from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class AvitoCall:
    """Модель звонка из Avito"""
    id: str
    client_phone: str
    your_phone: str
    call_time: datetime
    duration: int
    status: str  # 'successful' или 'unsuccessful'
    ad_id: Optional[str] = None
    ad_title: Optional[str] = None
    record_url: Optional[str] = None

@dataclass
class AvitoChat:
    """Модель чата из Avito"""
    chat_id: str
    client_name: str
    client_phone: Optional[str]
    messages: List[dict]
    ad_id: str
    ad_title: str
    created_time: datetime

@dataclass
class CalltouchCall:
    """Модель звонка для Calltouch API"""
    referenceId: str
    clientPhoneNumber: str
    callCenterPhoneNumber: str
    callStartTime: str
    duration: int
    waitingTime: int
    status: str
    recordUrl: Optional[str] = None
    comment: Optional[dict] = None
    addTags: Optional[List[dict]] = None
    customSources: Optional[dict] = None
