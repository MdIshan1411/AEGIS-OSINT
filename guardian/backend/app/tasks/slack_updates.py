import os
from slack_sdk.web.async_client import AsyncWebClient
from app.core.config import settings
from app.db.postgres import AsyncSessionLocal
from app.db.repositories import AuditRecordRepository, VulnerabilityRepository, DependencyVulnerabilityRepository

async def update_slack_message_on_completion(audit_id: str):
    """
    Called when scan completes. Updates Slack message with findings.
    """
    if not settings.SLACK_BOT_TOKEN:
        return
        
    slack_client = AsyncWebClient(token=settings.SLACK_BOT_TOKEN)
    
    async with AsyncSessionLocal() as db:
        audit_repo = AuditRecordRepository(db)
        vuln_repo = VulnerabilityRepository(db)
        dep_vuln_repo = DependencyVulnerabilityRepository(db)
        
        audit = await audit_repo.get(audit_id)
        if not audit or not audit.slack_channel_id or not audit.slack_message_ts:
            return
            
        vulns = await vuln_repo.get_by_audit(audit_id)
        dep_vulns = await dep_vuln_repo.get_by_audit(audit_id)
        
    critical_count = len([v for v in vulns if v.severity == "CRITICAL"])
    high_count = len([v for v in vulns if v.severity == "HIGH"])
    medium_count = len([v for v in vulns if v.severity == "MEDIUM"])
    low_count = len([v for v in vulns if v.severity == "LOW"])
    
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "✅ Security Audit Complete"}
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"🔴 *Critical*\n{critical_count}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"🟠 *High*\n{high_count}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"🟡 *Medium*\n{medium_count}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"🔵 *Low*\n{low_count}"
                }
            ]
        }
    ]
    
    # Sort vulns by severity: CRITICAL > HIGH > MEDIUM > LOW
    severity_rank = {"CRITICAL": 1, "HIGH": 2, "MEDIUM": 3, "LOW": 4}
    sorted_vulns = sorted(vulns, key=lambda x: severity_rank.get(x.severity, 5))
    
    for i, vuln in enumerate(sorted_vulns[:5]):
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{i+1}. {vuln.vulnerability_type}* ({vuln.severity})\n`{vuln.file_path}:{vuln.line_number}`"
            }
        })
        
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "View Full Report"},
                "action_id": "view_full_report",
                "value": audit_id,
                "url": f"http://localhost:5173/audits/{audit_id}" # React dashboard URL
            },
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "Create Fix PR"},
                "action_id": "create_fix_pr",
                "value": audit_id,
                "style": "primary"
            }
        ]
    })
    
    try:
        await slack_client.chat_update(
            channel=audit.slack_channel_id,
            ts=audit.slack_message_ts,
            blocks=blocks,
            text="✅ Security Audit Complete"
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to update Slack message: {e}")
