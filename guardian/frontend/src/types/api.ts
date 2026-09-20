export interface Vulnerability {
  vuln_id: str;
  file_path: string;
  line_number: number;
  vulnerability_type: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  cvss_score: number;
  description: string;
  exploitation_scenario?: string;
  code_snippet: string;
  suggested_fix?: string;
  cwe_id?: string;
  owasp_category?: string;
}

export interface DependencyVulnerability {
  dep_vuln_id: string;
  package_name: string;
  current_version: string;
  cve_id: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  description: string;
  recommendation: string;
  published_date?: string;
}

export interface AuditRecord {
  audit_id: string;
  repo_url: string;
  repo_owner: string;
  repo_name: string;
  status: "QUEUED" | "SCANNING" | "ANALYZING" | "COMPLETE" | "FAILED";
  started_at: string;
  completed_at?: string;
  summary_json: {
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
}

export interface AuditDetailResponse {
  audit: AuditRecord;
  vulnerabilities: Vulnerability[];
  dependency_vulnerabilities: DependencyVulnerability[];
}
