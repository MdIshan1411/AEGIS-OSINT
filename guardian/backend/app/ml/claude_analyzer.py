import json
from anthropic import AsyncAnthropic
import os
from typing import List

from app.db.models import Vulnerability
from app.db.repositories import VulnerabilityRepository
from app.core.config import settings

# Initialize Anthropic client
# Expects CLAUDE_API_KEY in environment
claude_client = AsyncAnthropic(api_key=settings.CLAUDE_API_KEY)

async def analyze_file_for_vulnerabilities(
    file_path: str,
    file_content: str,
    language: str,
    audit_id: str,
    vuln_repo: VulnerabilityRepository
) -> List[Vulnerability]:
    """
    Use Claude to analyze a single file for security vulnerabilities.
    """
    system_prompt = f"""
    You are a senior cybersecurity engineer with 15+ years of experience.
    You specialize in code security reviews for {language}.
    
    When analyzing code, you:
    1. Identify ALL security vulnerabilities
    2. Explain exploitation scenarios (how an attacker would abuse this)
    3. Suggest fixes with corrected code
    4. Assign severity (CRITICAL/HIGH/MEDIUM/LOW)
    5. Assign CVSS scores (0-10)
    6. Map to CWE IDs and OWASP categories
    7. Consider context (is this a web app? CLI? Library?)
    8. Think about business impact
    
    Output MUST be valid JSON array of objects, no markdown code blocks outside of JSON strings.
    """
    
    user_prompt = f"""
    Analyze this {language} code for security vulnerabilities.
    
    FILE: {file_path}
    
    CODE:
    ```{language}
    {file_content}
    ```
    
    For EACH vulnerability, provide JSON with:
    {{
      "vulnerability_type": "SQL_INJECTION|XSS|HARDCODED_SECRET|...",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "line_number": <int>,
      "description": "What's the vulnerability?",
      "exploitation_scenario": "How could an attacker exploit this?",
      "code_snippet": "<vulnerable code from file>",
      "suggested_fix": "<corrected code>",
      "cwe_id": "CWE-89",
      "owasp_category": "A03:2021 Injection",
      "cvss_score": <float 0-10>
    }}
    
    Return as JSON array. If no vulnerabilities, return [].
    """
    
    try:
        response = await claude_client.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=4000,
            temperature=0,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        response_text = response.content[0].text
        # Clean up in case Claude outputs markdown formatting around json
        if response_text.startswith("```json"):
            response_text = response_text.strip("`").replace("json\n", "", 1)
            
        vulns_json = json.loads(response_text)
        
        vulns = []
        for vuln_dict in vulns_json:
            vuln = Vulnerability(
                audit_id=audit_id,
                file_path=file_path,
                line_number=vuln_dict.get("line_number", 1),
                vulnerability_type=vuln_dict.get("vulnerability_type", "UNKNOWN"),
                severity=vuln_dict.get("severity", "MEDIUM"),
                cvss_score=float(vuln_dict.get("cvss_score", 0.0)),
                description=vuln_dict.get("description", ""),
                exploitation_scenario=vuln_dict.get("exploitation_scenario", ""),
                code_snippet=vuln_dict.get("code_snippet", ""),
                suggested_fix=vuln_dict.get("suggested_fix", ""),
                cwe_id=vuln_dict.get("cwe_id", ""),
                owasp_category=vuln_dict.get("owasp_category", ""),
            )
            await vuln_repo.create(vuln)
            vulns.append(vuln)
        
        return vulns
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Claude analysis failed for {file_path}: {e}")
        return []
