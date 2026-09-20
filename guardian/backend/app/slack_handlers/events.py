from fastapi import Request
from app.main import app, logger

@app.post("/api/slack/events")
async def slack_events(request: Request):
    """
    Endpoint for Slack Events API (e.g. url_verification, app_mention)
    """
    payload_body = await request.body()
    
    # Slack interactive payloads are URL-encoded if they come from buttons
    content_type = request.headers.get("content-type", "")
    
    if "application/x-www-form-urlencoded" in content_type:
        import json
        form = await request.form()
        payload = json.loads(form.get("payload", "{}"))
        
        if payload.get("type") == "block_actions":
            for action in payload.get("actions", []):
                if action.get("action_id") == "create_fix_pr":
                    audit_id = action.get("value")
                    from app.tasks.github_pr import create_github_pr
                    create_github_pr.delay(audit_id)
                    
                    # Acknowledge click
                    from slack_sdk.web.async_client import AsyncWebClient
                    from app.core.config import settings
                    slack_client = AsyncWebClient(token=settings.SLACK_BOT_TOKEN)
                    try:
                        await slack_client.chat_postMessage(
                            channel=payload["channel"]["id"],
                            text="🔄 Creating PR with fixes...",
                            thread_ts=payload["message"].get("thread_ts", payload["message"]["ts"])
                        )
                    except:
                        pass
        return {"status": "ok"}
    
    payload = await request.json()
    
    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge")}
        
    return {"status": "ok"}
