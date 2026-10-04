from typing import Optional
from sqlalchemy.orm import Session
from app.models.entities import ProcessedWebhookEvent


class WebhookEventRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_delivery_id(self, delivery_id: str) -> Optional[ProcessedWebhookEvent]:
        return self.db.query(ProcessedWebhookEvent).filter(ProcessedWebhookEvent.delivery_id == delivery_id).first()

    def record_processed(self, delivery_id: str, event_type: str) -> ProcessedWebhookEvent:
        event = ProcessedWebhookEvent(delivery_id=delivery_id, event_type=event_type)
        self.db.add(event)
        self.db.flush()
        return event
