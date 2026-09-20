import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Shield, ShieldAlert, ShieldCheck, ShieldX, Bot, Database,
  AlertTriangle, CheckCircle2, XCircle, Loader2, ChevronDown, ChevronUp,
  Radio, Wifi, WifiOff, Info,
} from 'lucide-react'
import type { ThreatProfile as ThreatProfileType, ThreatComponent, DataSource } from '@/types/api'

interface ThreatProfileProps {
  subjectName: string
  emailHint?: string
}

const THREAT_COLORS: Record<string, { bg: string; text: string; border: string; glow: string }> = {
  NONE: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/30', glow: 'shadow-emerald-500/20' },
  LOW: { bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/30', glow: 'shadow-green-500/20' },
  MEDIUM: { bg: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-yellow-500/30', glow: 'shadow-yellow-500/20' },
  HIGH: { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/30', glow: 'shadow-orange-500/20' },
  CRITICAL: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/30', glow: 'shadow-red-500/20' },
}

const SOURCE_STATUS_ICON: Record<string, JSX.Element> = {
  CONNECTED: <Wifi className="h-3 w-3 text-emerald-400" />,
  PARTIAL: <Radio className="h-3 w-3 text-yellow-400" />,
  UNAVAILABLE: <WifiOff className="h-3 w-3 text-slate-600" />,
}

export function ThreatProfilePanel({ subjectName, emailHint }: ThreatProfileProps) {
  const [profile, setProfile] = useState<ThreatProfileType | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showSources, setShowSources] = useState(false)

  useEffect(() => {
    const fetchProfile = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch('http://localhost:8000/api/intelligence/threat-profile', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            target_identifier: emailHint || subjectName,
            email_hint: emailHint || '',
            subject_name: subjectName,
          }),
        })
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        const data = await res.json()
        setProfile(data)
      } catch (e: any) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    }
    fetchProfile()
  }, [subjectName, emailHint])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-16">
        <Loader2 className="h-10 w-10 text-blue-400 animate-spin" />
        <p className="text-slate-400 mt-4">Fusing intelligence from 26+ sources...</p>
      </div>
    )
  }

  if (error || !profile) {
    return (
      <Card className="bg-red-900/10 border-red-700/30">
        <CardContent className="pt-6 text-center">
          <AlertTriangle className="h-8 w-8 text-red-400 mx-auto mb-2" />
          <p className="text-red-300">{error || 'Failed to load threat profile'}</p>
        </CardContent>
      </Card>
    )
  }

  const colors = THREAT_COLORS[profile.threat_level] || THREAT_COLORS.MEDIUM
  const riskPct = Math.min(profile.risk_score, 100)

  return (
    <div className="space-y-6">
      {/* ── Hero Section: Threat Level + Risk Score ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Threat Level Gauge */}
        <Card className={`${colors.bg} ${colors.border} border shadow-lg ${colors.glow}`}>
          <CardContent className="pt-6 text-center">
            <div className="relative w-32 h-32 mx-auto mb-4">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="42" fill="none" stroke="currentColor" strokeWidth="6" className="text-slate-800" />
                <circle cx="50" cy="50" r="42" fill="none" stroke="currentColor" strokeWidth="6"
                  className={colors.text}
                  strokeDasharray={`${riskPct * 2.64} 264`}
                  strokeLinecap="round"
                  style={{ transition: 'stroke-dasharray 1.5s ease-out' }}
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={`text-3xl font-bold ${colors.text}`}>{profile.risk_score}</span>
                <span className="text-xs text-slate-500">/ 100</span>
              </div>
            </div>
            <Badge className={`${colors.bg} ${colors.text} border ${colors.border} text-sm px-3 py-1`}>
              {profile.threat_level === 'NONE' ? '✅' : profile.threat_level === 'CRITICAL' ? '🚨' : '⚠️'} {profile.threat_level}
            </Badge>
            <p className="text-xs text-slate-500 mt-2">Threat Level Assessment</p>
          </CardContent>
        </Card>

        {/* Bot Probability */}
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardContent className="pt-6 text-center">
            <Bot className={`h-10 w-10 mx-auto mb-3 ${profile.bot_probability < 0.15 ? 'text-emerald-400' : profile.bot_probability < 0.4 ? 'text-yellow-400' : 'text-red-400'}`} />
            <p className="text-3xl font-bold text-white mb-1">
              {(profile.bot_probability * 100).toFixed(1)}%
            </p>
            <Badge variant="outline" className={`${profile.bot_probability < 0.15 ? 'text-emerald-400 border-emerald-500/30' : 'text-yellow-400 border-yellow-500/30'}`}>
              {profile.bot_probability < 0.10 ? 'HUMAN ✓' : profile.bot_probability < 0.30 ? 'LIKELY HUMAN' : 'UNCERTAIN'}
            </Badge>
            <p className="text-xs text-slate-500 mt-3 leading-relaxed line-clamp-3">{profile.bot_explanation}</p>
          </CardContent>
        </Card>

        {/* Data Sources Summary */}
        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardContent className="pt-6 text-center">
            <Database className="h-10 w-10 mx-auto mb-3 text-blue-400" />
            <p className="text-3xl font-bold text-white mb-1">{profile.sources_with_data}</p>
            <p className="text-xs text-slate-500">of {profile.total_sources_queried} sources returned data</p>
            <div className="mt-3 flex justify-center gap-2">
              <Badge variant="outline" className="text-emerald-400 border-emerald-500/30 text-xs">
                {profile.data_sources.filter(s => s.status === 'CONNECTED').length} Connected
              </Badge>
              <Badge variant="outline" className="text-yellow-400 border-yellow-500/30 text-xs">
                {profile.data_sources.filter(s => s.status === 'PARTIAL').length} Partial
              </Badge>
            </div>
            <p className="text-xs text-slate-500 mt-2">{profile.total_records} total records collected</p>
          </CardContent>
        </Card>
      </div>

      {/* ── Assessment Summary ── */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-slate-300 flex items-center gap-2">
            <Info className="h-4 w-4" /> Assessment Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-slate-300 text-sm leading-relaxed">{profile.assessment_summary}</p>
        </CardContent>
      </Card>

      {/* ── Threat Components ── */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-slate-300 flex items-center gap-2">
            <ShieldAlert className="h-4 w-4" /> Threat Components
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {profile.threat_components.map((comp, i) => (
            <div key={i} className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-slate-300 font-medium">{comp.name}</span>
                <span className={`text-sm font-mono ${comp.score < 0.1 ? 'text-emerald-400' : comp.score < 0.3 ? 'text-yellow-400' : 'text-red-400'}`}>
                  {(comp.score * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-1000 ease-out ${comp.score < 0.1 ? 'bg-emerald-500' : comp.score < 0.3 ? 'bg-yellow-500' : 'bg-red-500'}`}
                  style={{ width: `${Math.max(comp.score * 100, 2)}%` }}
                />
              </div>
              <p className="text-xs text-slate-500">{comp.explanation}</p>
              <div className="flex flex-wrap gap-1.5">
                {comp.indicators.map((ind, j) => (
                  <Badge key={j} variant="outline" className="text-xs text-slate-400 border-slate-700">
                    {ind}
                  </Badge>
                ))}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* ── Recommendations ── */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-slate-300 flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4" /> Recommendations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {profile.recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className="text-emerald-400 mt-0.5">▸</span>
                <span className="text-slate-300">{rec}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* ── Data Sources (Collapsible) ── */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader className="pb-3 cursor-pointer" onClick={() => setShowSources(!showSources)}>
          <CardTitle className="text-sm font-medium text-slate-300 flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Database className="h-4 w-4" /> Intelligence Sources ({profile.total_sources_queried})
            </span>
            {showSources ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </CardTitle>
        </CardHeader>
        {showSources && (
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {profile.data_sources.map((src, i) => (
                <div key={i} className="flex items-center justify-between p-2 rounded-md bg-slate-900/50 border border-slate-800">
                  <div className="flex items-center gap-2">
                    {SOURCE_STATUS_ICON[src.status]}
                    <span className="text-xs text-slate-300">{src.source_name}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-[10px] text-slate-500 border-slate-700">{src.category}</Badge>
                    <span className="text-[10px] text-slate-600">{src.records_found}r</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        )}
      </Card>

      {/* ── Confidence Footer ── */}
      <div className="text-center text-xs text-slate-600">
        Assessment confidence: {(profile.confidence * 100).toFixed(1)}% • Generated {new Date(profile.generated_at).toLocaleTimeString()}
      </div>
    </div>
  )
}
