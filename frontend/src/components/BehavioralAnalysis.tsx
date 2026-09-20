import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Brain, Clock, MessageSquare, Smartphone, FileText, Loader2,
  AlertTriangle, Sun, Moon, Globe, Zap,
} from 'lucide-react'
import type { BehavioralSignature } from '@/types/api'

interface BehavioralAnalysisProps {
  subjectName: string
  emailHint?: string
}

export function BehavioralAnalysisPanel({ subjectName, emailHint }: BehavioralAnalysisProps) {
  const [data, setData] = useState<BehavioralSignature | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch('http://localhost:8000/api/intelligence/behavioral-analysis', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            target_identifier: emailHint || subjectName,
            email_hint: emailHint || '',
            subject_name: subjectName,
          }),
        })
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        setData(await res.json())
      } catch (e: any) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [subjectName, emailHint])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <Loader2 className="h-10 w-10 text-purple-400 animate-spin" />
        <p className="text-slate-400 mt-4">Analyzing behavioral patterns...</p>
      </div>
    )
  }

  if (error || !data) {
    return (
      <Card className="bg-red-900/10 border-red-700/30">
        <CardContent className="pt-6 text-center">
          <AlertTriangle className="h-8 w-8 text-red-400 mx-auto mb-2" />
          <p className="text-red-300">{error || 'Failed to load behavioral analysis'}</p>
        </CardContent>
      </Card>
    )
  }

  const maxActivity = Math.max(...data.circadian.hourly_activity, 0.01)

  return (
    <div className="space-y-6">
      {/* ── Signature Strength Header ── */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Brain className="h-6 w-6 text-purple-400" />
          <div>
            <h3 className="text-lg font-semibold text-white">Behavioral Fingerprint</h3>
            <p className="text-xs text-slate-500">Unique behavioral signature for identity correlation</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-sm text-slate-400">Signature Strength</p>
          <p className="text-2xl font-bold text-purple-400">{(data.signature_strength * 100).toFixed(0)}%</p>
        </div>
      </div>

      {/* ── Circadian Rhythm Heatmap ── */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-slate-300 flex items-center gap-2">
            <Clock className="h-4 w-4 text-blue-400" /> Circadian Rhythm Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {/* 24-hour activity bars */}
            <div className="flex items-end gap-[2px] h-20">
              {data.circadian.hourly_activity.map((val, hour) => {
                const height = (val / maxActivity) * 100
                const isPeak = data.circadian.peak_hours.includes(hour)
                return (
                  <div key={hour} className="flex-1 flex flex-col items-center gap-1">
                    <div
                      className={`w-full rounded-t transition-all duration-500 ${isPeak ? 'bg-purple-500' : val < 0.1 ? 'bg-slate-800' : 'bg-blue-500/60'}`}
                      style={{ height: `${Math.max(height, 3)}%` }}
                      title={`${hour}:00 — ${(val * 100).toFixed(0)}% activity`}
                    />
                  </div>
                )
              })}
            </div>
            {/* Hour labels */}
            <div className="flex gap-[2px]">
              {data.circadian.hourly_activity.map((_, hour) => (
                <div key={hour} className="flex-1 text-center">
                  <span className="text-[8px] text-slate-600">{hour % 6 === 0 ? `${hour}h` : ''}</span>
                </div>
              ))}
            </div>
            {/* Summary badges */}
            <div className="flex flex-wrap gap-2 mt-2">
              <Badge variant="outline" className="text-xs text-blue-400 border-blue-500/30">
                <Sun className="h-3 w-3 mr-1" /> Peak: {data.circadian.peak_hours.map(h => `${h}:00`).join(', ')}
              </Badge>
              <Badge variant="outline" className="text-xs text-indigo-400 border-indigo-500/30">
                <Moon className="h-3 w-3 mr-1" /> Sleep: {data.circadian.sleep_gap_start}:00 ({data.circadian.sleep_duration_hours}h)
              </Badge>
              <Badge variant="outline" className="text-xs text-cyan-400 border-cyan-500/30">
                <Globe className="h-3 w-3 mr-1" /> {data.circadian.inferred_timezone}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ── Two-Column Grid ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Linguistic Profile */}
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-300 flex items-center gap-2">
              <FileText className="h-4 w-4 text-emerald-400" /> Linguistic Profile
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <MetricBar label="Vocabulary Richness" value={data.linguistic.vocabulary_richness} color="emerald" />
            <MetricBar label="Formality Score" value={data.linguistic.formality_score} color="blue" />
            <MetricBar label="Content Originality" value={data.content.content_originality} color="purple" />
            <div className="grid grid-cols-2 gap-2 mt-3">
              <MiniStat label="Avg Word Length" value={`${data.linguistic.avg_word_length}`} />
              <MiniStat label="Avg Sentence" value={`${data.linguistic.avg_sentence_length} words`} />
              <MiniStat label="Emoji Rate" value={`${data.linguistic.emoji_frequency}/100w`} />
              <MiniStat label="Cap Style" value={data.linguistic.capitalization_style} />
            </div>
            {data.linguistic.favorite_emojis.length > 0 && (
              <div className="flex items-center gap-1 mt-2">
                <span className="text-xs text-slate-500">Favorites:</span>
                {data.linguistic.favorite_emojis.map((e, i) => (
                  <span key={i} className="text-sm">{e}</span>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Interaction Profile */}
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-slate-300 flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-cyan-400" /> Interaction Profile
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <MetricBar label="Original Content" value={data.interaction.original_content_ratio} color="cyan" />
            <MetricBar label="Reply Ratio" value={data.interaction.reply_ratio} color="blue" />
            <MetricBar label="Reshare Ratio" value={data.interaction.retweet_ratio} color="indigo" />
            <div className="grid grid-cols-2 gap-2 mt-3">
              <MiniStat label="Engagement" value={data.interaction.engagement_style} highlight />
              <MiniStat label="Avg Response" value={`${data.interaction.avg_response_time_minutes.toFixed(0)}min`} />
              <MiniStat label="Network Density" value={`${(data.interaction.network_density * 100).toFixed(0)}%`} />
              <MiniStat label="Posting" value={data.content.posting_frequency} />
            </div>
            <div className="flex flex-wrap gap-1.5 mt-2">
              {data.interaction.top_interaction_topics.map((topic, i) => (
                <Badge key={i} variant="outline" className="text-[10px] text-cyan-400 border-cyan-500/30">
                  {topic}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* ── Technical Fingerprint ── */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-slate-300 flex items-center gap-2">
            <Smartphone className="h-4 w-4 text-orange-400" /> Technical Fingerprint
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <TechCard icon="📱" label="Device" value={data.technical.primary_device} />
            <TechCard icon="💻" label="OS" value={data.technical.os_fingerprint} />
            <TechCard icon="🌐" label="Browser" value={data.technical.primary_browser} />
            <TechCard icon="📍" label="Region" value={data.technical.primary_region} />
          </div>
          <div className="flex gap-3 mt-3">
            <Badge variant="outline" className="text-xs text-slate-400 border-slate-700">
              IP: {data.technical.ip_consistency}
            </Badge>
            <Badge variant="outline" className="text-xs text-slate-400 border-slate-700">
              {data.technical.device_count} device{data.technical.device_count > 1 ? 's' : ''}
            </Badge>
            <Badge variant="outline" className="text-xs text-slate-400 border-slate-700">
              ~{data.technical.session_duration_avg_minutes.toFixed(0)}min sessions
            </Badge>
          </div>
        </CardContent>
      </Card>

      {/* ── Content & Sentiment ── */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-slate-300 flex items-center gap-2">
            <Zap className="h-4 w-4 text-yellow-400" /> Content & Sentiment Analysis
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Content Type Distribution */}
            <div>
              <p className="text-xs text-slate-500 mb-2">Content Type Mix</p>
              <div className="flex h-4 rounded-full overflow-hidden">
                {Object.entries(data.content.content_type_distribution).map(([type, pct]) => {
                  const colors: Record<string, string> = {
                    text: 'bg-blue-500', link: 'bg-purple-500',
                    image: 'bg-emerald-500', video: 'bg-orange-500',
                  }
                  return (
                    <div key={type} className={`${colors[type] || 'bg-slate-600'}`}
                      style={{ width: `${pct * 100}%` }}
                      title={`${type}: ${(pct * 100).toFixed(0)}%`}
                    />
                  )
                })}
              </div>
              <div className="flex justify-between mt-1.5">
                {Object.entries(data.content.content_type_distribution).map(([type, pct]) => (
                  <span key={type} className="text-[10px] text-slate-500 capitalize">{type} {(pct * 100).toFixed(0)}%</span>
                ))}
              </div>
            </div>

            {/* Sentiment Distribution */}
            <div>
              <p className="text-xs text-slate-500 mb-2">Sentiment Distribution</p>
              <div className="flex h-4 rounded-full overflow-hidden">
                {data.content.sentiment_distribution.positive != null && (
                  <div className="bg-emerald-500" style={{ width: `${data.content.sentiment_distribution.positive * 100}%` }} />
                )}
                {data.content.sentiment_distribution.neutral != null && (
                  <div className="bg-slate-500" style={{ width: `${data.content.sentiment_distribution.neutral * 100}%` }} />
                )}
                {data.content.sentiment_distribution.negative != null && (
                  <div className="bg-red-500" style={{ width: `${data.content.sentiment_distribution.negative * 100}%` }} />
                )}
              </div>
              <div className="flex justify-between mt-1.5">
                <span className="text-[10px] text-emerald-400">Positive {((data.content.sentiment_distribution.positive ?? 0) * 100).toFixed(0)}%</span>
                <span className="text-[10px] text-slate-400">Neutral {((data.content.sentiment_distribution.neutral ?? 0) * 100).toFixed(0)}%</span>
                <span className="text-[10px] text-red-400">Negative {((data.content.sentiment_distribution.negative ?? 0) * 100).toFixed(0)}%</span>
              </div>
            </div>
          </div>

          {/* Topics */}
          <div className="flex flex-wrap gap-1.5 mt-4">
            {data.content.top_topics.map((topic, i) => (
              <Badge key={i} variant="outline" className="text-xs text-yellow-400 border-yellow-500/30">
                {topic}
              </Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Footer */}
      <div className="text-center text-xs text-slate-600">
        Uniqueness: {(data.uniqueness_score * 100).toFixed(0)}% • Generated {new Date(data.generated_at).toLocaleTimeString()}
      </div>
    </div>
  )
}

// ── Helper Components ──

function MetricBar({ label, value, color }: { label: string; value: number; color: string }) {
  const colorMap: Record<string, string> = {
    emerald: 'bg-emerald-500', blue: 'bg-blue-500', purple: 'bg-purple-500',
    cyan: 'bg-cyan-500', indigo: 'bg-indigo-500', yellow: 'bg-yellow-500',
  }
  return (
    <div>
      <div className="flex justify-between text-xs mb-1">
        <span className="text-slate-400">{label}</span>
        <span className="text-slate-300 font-mono">{(value * 100).toFixed(0)}%</span>
      </div>
      <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden">
        <div className={`h-full rounded-full transition-all duration-700 ${colorMap[color] || 'bg-blue-500'}`}
          style={{ width: `${value * 100}%` }} />
      </div>
    </div>
  )
}

function MiniStat({ label, value, highlight }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className="bg-slate-900/50 rounded-md px-2 py-1.5">
      <p className="text-[10px] text-slate-600 uppercase">{label}</p>
      <p className={`text-xs font-medium ${highlight ? 'text-cyan-400 capitalize' : 'text-slate-300'}`}>{value}</p>
    </div>
  )
}

function TechCard({ icon, label, value }: { icon: string; label: string; value: string }) {
  return (
    <div className="bg-slate-900/50 rounded-lg p-3 text-center">
      <span className="text-xl">{icon}</span>
      <p className="text-[10px] text-slate-600 mt-1 uppercase">{label}</p>
      <p className="text-xs text-slate-300 font-medium mt-0.5 truncate">{value}</p>
    </div>
  )
}
