from app.workers.celery_app import celery_app


@celery_app.task(name="aiqahub.ai.analyze")
def analyze_ai(payload: dict) -> dict:
    return {"status": "ok", "payload": payload}

