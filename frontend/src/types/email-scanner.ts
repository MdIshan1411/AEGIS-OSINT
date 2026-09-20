export interface ServiceResult {
  service: string
  category: string
  status: 'REGISTERED' | 'NOT_REGISTERED' | 'ERROR' | 'TIMEOUT' | 'BREACHED' | 'SAFE'
  profile_url: string | null
  confidence: number
  check_duration_ms: number
  error_message: string | null
  metadata: Record<string, any>
}

export interface CategorySummary {
  total: number
  registered: number
  breached: number
}

export interface EmailScanResponse {
  scan_id: string
  email: string
  status: string
  total_services: number
  registered_count: number
  not_registered_count: number
  error_count: number
  breached_count: number
  processing_time_ms: number
  timestamp: string
  results: ServiceResult[]
  category_summary: Record<string, CategorySummary>
}

export interface ScanHistoryItem {
  scan_id: string
  email: string
  registered_count: number
  total_services: number
  breached_count: number
  timestamp: string
}
