import asyncio
import time
from github import Github
from app.tasks.celery_app import celery_app
from app.db.postgres import AsyncSessionLocal
from app.db.repositories import AuditRecordRepository, UserRepository, VulnerabilityRepository, GitHubIntegrationRepository

async def create_github_pr_async(audit_id: str):
    """
    Create GitHub PR with security fixes.
    """
    async with AsyncSessionLocal() as db:
        audit_repo = AuditRecordRepository(db)
        user_repo = UserRepository(db)
        vuln_repo = VulnerabilityRepository(db)
        gh_repo = GitHubIntegrationRepository(db)
        
        audit = await audit_repo.get(audit_id)
        if not audit: return
        
        user = await user_repo.get(audit.user_id)
        if not user: return
        
        vulns = await vuln_repo.get_by_audit(audit_id)
        
        github_integration = await gh_repo.get_by_user(user.user_id)
        if not github_integration or not github_integration.github_access_token:
            from slack_sdk.web.async_client import AsyncWebClient
            from app.core.config import settings
            slack_client = AsyncWebClient(token=settings.SLACK_BOT_TOKEN)
            try:
                await slack_client.chat_postMessage(
                    channel=audit.slack_channel_id,
                    text="❌ GitHub account not connected. Please authenticate first to create PRs.",
                    thread_ts=audit.slack_message_ts
                )
            except:
                pass
            return

        # Use GitHub token to auth
        gh = Github(github_integration.github_access_token)
        try:
            repo_name = f"{audit.repo_owner}/{audit.repo_name}"
            repo = gh.get_repo(repo_name)
            
            branch_name = f"guardian/security-fixes-{int(time.time())}"
            repo.create_git_ref(
                f"refs/heads/{branch_name}",
                repo.get_branch(repo.default_branch).commit.sha
            )
            
            fixes_applied = 0
            for vuln in vulns[:10]:
                if not vuln.suggested_fix or not vuln.code_snippet:
                    continue
                    
                try:
                    file = repo.get_contents(vuln.file_path, ref=branch_name)
                    original_content = file.decoded_content.decode()
                    
                    # Very simple string replacement for demo purposes
                    fixed_content = original_content.replace(vuln.code_snippet.strip(), vuln.suggested_fix.strip())
                    
                    if fixed_content != original_content:
                        repo.update_file(
                            vuln.file_path,
                            f"[GUARDIAN] Fix: {vuln.vulnerability_type} in {vuln.file_path}",
                            fixed_content,
                            file.sha,
                            branch=branch_name
                        )
                        fixes_applied += 1
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Could not apply fix for {vuln.file_path}: {e}")
            
            if fixes_applied > 0:
                pr = repo.create_pull(
                    title=f"🔒 Guardian Security Fixes ({fixes_applied} applied)",
                    body=f"GUARDIAN automatically generated security fixes for {fixes_applied} vulnerabilities.\n\nAudit ID: {audit_id}",
                    head=branch_name,
                    base=repo.default_branch
                )
                
                from slack_sdk.web.async_client import AsyncWebClient
                from app.core.config import settings
                slack_client = AsyncWebClient(token=settings.SLACK_BOT_TOKEN)
                await slack_client.chat_postMessage(
                    channel=audit.slack_channel_id,
                    text=f"✅ PR created successfully: {pr.html_url}",
                    thread_ts=audit.slack_message_ts
                )
            else:
                from slack_sdk.web.async_client import AsyncWebClient
                from app.core.config import settings
                slack_client = AsyncWebClient(token=settings.SLACK_BOT_TOKEN)
                await slack_client.chat_postMessage(
                    channel=audit.slack_channel_id,
                    text=f"⚠️ No automatic fixes could be applied cleanly.",
                    thread_ts=audit.slack_message_ts
                )
                
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"PR creation failed: {e}")
            from slack_sdk.web.async_client import AsyncWebClient
            from app.core.config import settings
            slack_client = AsyncWebClient(token=settings.SLACK_BOT_TOKEN)
            try:
                await slack_client.chat_postMessage(
                    channel=audit.slack_channel_id,
                    text=f"❌ PR creation failed: {str(e)}",
                    thread_ts=audit.slack_message_ts
                )
            except:
                pass


@celery_app.task(name="create_github_pr")
def create_github_pr(audit_id: str):
    asyncio.run(create_github_pr_async(audit_id))
