from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Any

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
    waitingTime: Optional[int] = 0
    
    def __post_init__(self):
        """Преобразуем duration из секунд в int если нужно"""
        if isinstance(self.duration, str):
            self.duration = int(self.duration)
        if isinstance(self.waitingTime, str):
            self.waitingTime = int(self.waitingTime)

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
    first_message: str = ""  # Первое сообщение для комментария
    message_count: int = 0   # Количество сообщений
    
    def __post_init__(self):
        if not self.first_message and self.messages:
            self.first_message = self.messages[0].get("text", "")
        if self.message_count == 0:
            self.message_count = len(self.messages)

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
    
    def __post_init__(self):
        if isinstance(self.waitingTime, str):
            self.waitingTime = int(self.waitingTime)

@dataclass
class CalltouchRequest:
    """Модель заявки для Calltouch API (для чатов)"""
    requestId: str
    phone: Optional[str]
    userName: Optional[str]
    comment: str
    source: str
    medium: str = "organic"
    campaign: Optional[str] = None
    content: Optional[str] = None
    customFields: Optional[List[dict]] = None
