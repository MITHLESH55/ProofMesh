from typing import Any, Dict
from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.common import SuccessEnvelope
from app.services.github.webhook_service import GitHubWebhookService
from app.services.ingestion.service import IngestionService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/github", response_model=SuccessEnvelope[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def handle_github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None, alias="X-Hub-Signature-256"),
    x_github_event: str = Header(None, alias="X-GitHub-Event"),
    x_github_delivery: str = Header(None, alias="X-GitHub-Delivery"),
    db: Session = Depends(get_db),
):
    raw_body = await request.body()
    event_type, payload = GitHubWebhookService.verify_and_parse(
        raw_body=raw_body,
        signature_header=x_hub_signature_256,
        event_type_header=x_github_event,
    )

    request_id = getattr(request.state, "request_id", "req_unknown")
    ingestion_service = IngestionService(db)
    result = ingestion_service.handle_github_webhook(
        event_type=event_type,
        payload=payload,
        delivery_id=x_github_delivery,
        request_id=request_id,
    )

    return SuccessEnvelope(
        data=result,
        request_id=request_id,
    )
