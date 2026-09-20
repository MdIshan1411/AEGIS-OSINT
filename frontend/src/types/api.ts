export interface InvestigateRequest {
  subject_name: string
  email_hint?: string
  domain_context?: string
}

export interface PlatformProfile {
  platform: string
  username: string
  url: string
  follower_count: number
  verification_status: boolean
  last_activity?: string
}

export interface TimelineEvent {
  timestamp: string
  event_type: string
  title: string
  description: string
  platform: string
  location?: string
}

export interface Evidence {
  id: string
  source_platform: string
  evidence_type: string
  content: string
  timestamp: string
  credibility_score: number
  url: string
  metadata: Record<string, string>
}

export interface Conflict {
  conflict_id: string
  conflict_type: string
  severity: string
  description: string
  affected_platforms: string[]
  evidence_ids: string[]
}

export interface ConfidenceBreakdown {
  name_match: number
  bio_similarity: number
  cross_platform_consistency: number
  evidence_corroboration: number
  match_status?: string
  match_reasons?: string[]
  mismatch_reasons?: string[]
  supporting_evidence?: string[]
  contradicting_evidence?: string[]
  missing_evidence?: string[]
  explanation?: string
}

export interface Candidate {
  candidate_id: string
  name: string
  bio?: string
  overall_confidence: number
  confidence_breakdown: ConfidenceBreakdown
  aliases: string[]
  platforms: Record<string, PlatformProfile>
  timeline_events: TimelineEvent[]
  evidence: Evidence[]
  conflicts: Conflict[]
  investigation_tags: string[]
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
}

export interface InvestigationResponse {
  investigation_id: string
  subject_name: string
  email_hint?: string
  timestamp: string
  candidates: Candidate[]
  top_candidate?: Candidate
  total_evidence_items: number
  conflicts_detected: number
  graph_nodes: any[]
  graph_edges: any[]
}

// Aliased to keep old code paths valid if they expected Investigation
export type Investigation = InvestigationResponse

// ─────────────────────────────────────────────────────────────
// INTELLIGENCE FUSION TYPES
// ─────────────────────────────────────────────────────────────

export interface ThreatComponent {
  name: string
  score: number
  weight: number
  explanation: string
  indicators: string[]
}

export interface DataSource {
  source_name: string
  category: string
  status: 'CONNECTED' | 'PARTIAL' | 'UNAVAILABLE'
  records_found: number
  confidence: number
  last_checked: string
  key_findings: string[]
}

export interface ThreatProfile {
  target_identifier: string
  risk_score: number
  threat_level: 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  bot_probability: number
  bot_explanation: string
  threat_components: ThreatComponent[]
  data_sources: DataSource[]
  total_sources_queried: number
  sources_with_data: number
  total_records: number
  recommendations: string[]
  assessment_summary: string
  confidence: number
  generated_at: string
}

export interface CircadianProfile {
  hourly_activity: number[]
  peak_hours: number[]
  sleep_gap_start: number
  sleep_duration_hours: number
  inferred_timezone: string
  consistency_score: number
}

export interface LinguisticProfile {
  avg_word_length: number
  vocabulary_richness: number
  emoji_frequency: number
  favorite_emojis: string[]
  capitalization_style: string
  punctuation_density: number
  avg_sentence_length: number
  formality_score: number
  language_detected: string
}

export interface InteractionProfile {
  reply_ratio: number
  retweet_ratio: number
  original_content_ratio: number
  engagement_style: string
  avg_response_time_minutes: number
  network_density: number
  top_interaction_topics: string[]
}

export interface TechnicalProfile {
  primary_device: string
  os_fingerprint: string
  primary_browser: string
  ip_consistency: string
  primary_region: string
  device_count: number
  session_duration_avg_minutes: number
}

export interface ContentProfile {
  top_topics: string[]
  topic_consistency: number
  content_type_distribution: Record<string, number>
  posting_frequency: string
  content_originality: number
  sentiment_distribution: Record<string, number>
}

export interface BehavioralSignature {
  target_identifier: string
  circadian: CircadianProfile
  linguistic: LinguisticProfile
  interaction: InteractionProfile
  technical: TechnicalProfile
  content: ContentProfile
  signature_strength: number
  uniqueness_score: number
  generated_at: string
}

export interface BotFactor {
  name: string
  score: number
  weight: number
  explanation: string
  indicators: string[]
}

export interface BotScore {
  target_identifier: string
  bot_probability: number
  risk_label: 'HUMAN' | 'LIKELY_HUMAN' | 'UNCERTAIN' | 'LIKELY_BOT' | 'BOT'
  factors: BotFactor[]
  explanation: string
  confidence: number
  generated_at: string
}

export interface RiskDimension {
  name: string
  probability: number
  impact: number
  combined_score: number
  level: string
  explanation: string
  mitigations: string[]
}

export interface RiskMatrixPosition {
  probability_band: number
  impact_band: number
  risk_level: string
  color: string
}

export interface RiskAssessment {
  target_identifier: string
  overall_risk_score: number
  threat_level: 'NONE' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
  dimensions: RiskDimension[]
  matrix_position: RiskMatrixPosition
  probability_label: string
  impact_label: string
  recommendations: string[]
  risk_trend: 'STABLE' | 'INCREASING' | 'DECREASING'
  historical_scores: number[]
  confidence: number
  generated_at: string
}
