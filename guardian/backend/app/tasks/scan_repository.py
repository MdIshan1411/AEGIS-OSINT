import asyncio
import os
import tempfile
import git
from pathlib import Path
from datetime import datetime
import uuid

from app.tasks.celery_app import celery_app
from app.db.postgres import AsyncSessionLocal
from app.db.repositories import AuditRecordRepository, VulnerabilityRepository, DependencyVulnerabilityRepository
from app.ml.claude_analyzer import analyze_file_for_vulnerabilities
from app.ml.dependency_scanner import scan_dependencies
# from app.tasks.slack_updates import update_slack_message_on_completion # to be created

def enumerate_code_files(repo_path: Path, max_files: int = 5000, max_size_mb: int = 100) -> list[Path]:
    ignore_dirs = {
        ".git", "node_modules", "__pycache__", ".venv", "venv",
        "build", "dist", ".egg-info", ".tox", ".pytest_cache",
        ".gradle", "target", "bin", "obj", "vendor"
    }
    code_extensions = {
        ".py", ".js", ".ts", ".jsx", ".tsx",
        ".java", ".go", ".rs", ".rb", ".php",
        ".cs", ".cpp", ".c", ".h", ".swift",
        ".kt", ".scala", ".groovy", ".sh", ".bash"
    }
    
    files = []
    total_size = 0
    for file_path in repo_path.rglob("*"):
        if any(part in ignore_dirs for part in file_path.parts):
            continue
        if file_path.suffix not in code_extensions:
            continue
        if not file_path.is_file():
            continue
            
        file_size = file_path.stat().st_size
        if file_size > 1_000_000:  # >1MB skip
            continue
            
        total_size += file_size
        if total_size > max_size_mb * 1_000_000:
            break
        if len(files) >= max_files:
            break
        files.append(file_path)
    return files

def detect_language(file_path: Path) -> str:
    ext_to_lang = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".jsx": "javascript", ".tsx": "typescript", ".java": "java",
        ".go": "go", ".rs": "rust", ".rb": "ruby", ".php": "php",
        ".cs": "csharp", ".cpp": "cpp", ".c": "c", ".swift": "swift",
        ".kt": "kotlin", ".scala": "scala", ".sh": "bash",
    }
    return ext_to_lang.get(file_path.suffix, "unknown")

async def scan_repository_async(audit_id: str, channel_id: str):
    async with AsyncSessionLocal() as db:
        audit_repo = AuditRecordRepository(db)
        vuln_repo = VulnerabilityRepository(db)
        dep_vuln_repo = DependencyVulnerabilityRepository(db)
        
        audit = await audit_repo.get(audit_id)
        if not audit:
            return
            
        audit.status = "SCANNING"
        await audit_repo.update(audit)
        
        # Clone repo
        clone_dir = Path(tempfile.gettempdir()) / f"guardian_scans" / audit_id
        clone_dir.mkdir(parents=True, exist_ok=True)
        try:
            # Using GitPython to clone
            git.Repo.clone_from(audit.repo_url, clone_dir)
            
            audit.repo_clone_path = str(clone_dir)
            await audit_repo.update(audit)
            
            code_files = enumerate_code_files(clone_dir)
            audit.total_files_scanned = len(code_files)
            # Rough LOC
            loc = 0
            for f in code_files:
                try:
                    loc += sum(1 for _ in open(f, errors="ignore"))
                except:
                    pass
            audit.total_loc = loc
            await audit_repo.update(audit)
            
            for file_path in code_files:
                language = detect_language(file_path)
                content = file_path.read_text(errors="ignore")
                
                await analyze_file_for_vulnerabilities(
                    str(file_path.relative_to(clone_dir)),
                    content,
                    language,
                    audit_id,
                    vuln_repo
                )
                
            await scan_dependencies(clone_dir, audit_id, dep_vuln_repo)
            
            vulns = await vuln_repo.get_by_audit(audit_id)
            dep_vulns = await dep_vuln_repo.get_by_audit(audit_id)
            
            summary = {
                "critical": len([v for v in vulns if v.severity == "CRITICAL"]),
                "high": len([v for v in vulns if v.severity == "HIGH"]),
                "medium": len([v for v in vulns if v.severity == "MEDIUM"]),
                "low": len([v for v in vulns if v.severity == "LOW"]),
                "dependency_critical": len([v for v in dep_vulns if v.severity == "CRITICAL"]),
                "total_issues": len(vulns) + len(dep_vulns),
            }
            
            audit.status = "COMPLETE"
            audit.completed_at = datetime.utcnow()
            audit.execution_time_ms = int((datetime.utcnow() - audit.started_at).total_seconds() * 1000)
            audit.summary_json = summary
            await audit_repo.update(audit)
            
            # Post Slack update
            from app.tasks.slack_updates import update_slack_message_on_completion
            await update_slack_message_on_completion(audit_id)
            
        except Exception as e:
            audit.status = "FAILED"
            audit.error_message = str(e)
            await audit_repo.update(audit)
            import logging
            logging.getLogger(__name__).error(f"Scan failed: {e}")

@celery_app.task(name="scan_repository")
def scan_repository(audit_id: str, channel_id: str):
    # Celery runs sync functions, so we use asyncio.run to call the async logic
    asyncio.run(scan_repository_async(audit_id, channel_id))
