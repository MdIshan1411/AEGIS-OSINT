from pathlib import Path
from typing import List, Dict, Callable
import httpx
from datetime import datetime

from app.db.models import DependencyVulnerability
from app.db.repositories import DependencyVulnerabilityRepository

def parse_npm_dependencies(content: str) -> Dict[str, str]:
    import json
    try:
        data = json.loads(content)
        deps = data.get("dependencies", {})
        deps.update(data.get("devDependencies", {}))
        return deps
    except Exception:
        return {}

def parse_pip_dependencies(content: str) -> Dict[str, str]:
    deps = {}
    for line in content.splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            parts = line.split("==")
            if len(parts) == 2:
                deps[parts[0].strip()] = parts[1].strip()
            else:
                deps[line.split(">")[0].split("<")[0].strip()] = "latest"
    return deps

async def query_cve_database(package_name: str, version: str) -> List[dict]:
    """
    Mock query to a CVE database like OSV or Dependencies.dev
    In a real scenario, this would make an HTTP request.
    For the hackathon, we simulate findings for known vulnerable packages.
    """
    mock_findings = []
    package_lower = package_name.lower()
    
    # Simulate finding for lodash
    if "lodash" in package_lower:
        mock_findings.append({
            "id": "CVE-2021-23337",
            "severity": "HIGH",
            "description": "lodash prototype pollution",
            "fixed_in_version": "4.17.21",
            "published_date": datetime(2021, 2, 15)
        })
    # Simulate finding for django
    elif "django" in package_lower and version.startswith("2.0"):
        mock_findings.append({
            "id": "CVE-2022-22818",
            "severity": "MEDIUM",
            "description": "Django possible XSS via template tag",
            "fixed_in_version": "2.2.27",
            "published_date": datetime(2022, 2, 1)
        })
        
    return mock_findings

async def scan_dependencies(
    repo_path: Path,
    audit_id: str,
    dep_vuln_repo: DependencyVulnerabilityRepository
) -> List[DependencyVulnerability]:
    """
    Scan for outdated/vulnerable dependencies.
    """
    dependency_files: Dict[str, Callable[[str], Dict[str, str]]] = {
        "package.json": parse_npm_dependencies,
        "requirements.txt": parse_pip_dependencies,
    }
    
    all_vulns = []
    
    for filename, parser in dependency_files.items():
        manifest_path = repo_path / filename
        if not manifest_path.exists():
            continue
            
        content = manifest_path.read_text(errors="ignore")
        dependencies = parser(content)
        
        for package_name, version in dependencies.items():
            cves = await query_cve_database(package_name, version)
            
            for cve in cves:
                vuln = DependencyVulnerability(
                    audit_id=audit_id,
                    package_name=package_name,
                    current_version=version,
                    cve_id=cve["id"],
                    severity=cve["severity"],
                    description=cve["description"],
                    recommendation=f"Upgrade to {cve['fixed_in_version']} or later",
                    published_date=cve["published_date"],
                )
                await dep_vuln_repo.create(vuln)
                all_vulns.append(vuln)
                
    return all_vulns
