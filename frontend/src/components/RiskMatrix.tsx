import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  AlertTriangle, Loader2, TrendingUp, TrendingDown, Minus,
  ShieldAlert, Target, Crosshair, Clock, Zap, CheckCircle2,
} from 'lucide-react'
import type { RiskAssessment } from '@/types/api'

interface RiskMatrixProps {
  subjectName: string
  emailHint?: string
}

const LEVEL_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  NONE: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', border: 'border-emerald-500/30' },
  LOW: { bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/30' },
  MEDIUM: { bg: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-yellow-500/30' },
  HIGH: { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/30' },
  CRITICAL: { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/30' },
}

const TREND_ICONS: Record<string, JSX.Element> = {
  STABLE: <Minus className="h-4 w-4 text-slate-400" />,
  INCREASING: <TrendingUp className="h-4 w-4 text-red-400" />,
  DECREASING: <TrendingDown className="h-4 w-4 text-emerald-400" />,
}

// 5×5 risk matrix colors (row=impact 5→1, col=probability 1→5)
const MATRIX_COLORS: string[][] = [
  ['bg-yellow-600/30', 'bg-orange-600/40', 'bg-red-600/50', 'bg-red-700/60', 'bg-red-800/70'],
  ['bg-yellow-500/25', 'bg-yellow-600/30', 'bg-orange-600/40', 'bg-red-600/50', 'bg-red-700/60'],
  ['bg-green-600/25', 'bg-yellow-500/25', 'bg-yellow-600/30', 'bg-orange-600/40', 'bg-red-600/50'],
  ['bg-green-600/20', 'bg-green-600/25', 'bg-yellow-500/25', 'bg-yellow-600/30', 'bg-orange-600/40'],
  ['bg-emerald-600/20', 'bg-green-600/20', 'bg-green-600/25', 'bg-yellow-500/25', 'bg-yellow-600/30'],
]

export function RiskMatrixPanel({ subjectName, emailHint }: RiskMatrixProps) {
  const [data, setData] = useState<RiskAssessment | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      setError(null)
      try {
        const res = await fetch('http://localhost:8000/api/intelligence/risk-assessment', {
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
        <Loader2 className="h-10 w-10 text-orange-400 animate-spin" />
        <p className="text-slate-400 mt-4">Calculating risk dimensions...</p>
      </div>
    )
  }

  if (error || !data) {
    return (
      <Card className="bg-red-900/10 border-red-700/30">
        <CardContent className="pt-6 text-center">
          <AlertTriangle className="h-8 w-8 text-red-400 mx-auto mb-2" />
          <p className="text-red-300">{error || 'Failed to load risk assessment'}</p>
        </CardContent>
      </Card>
    )
  }

  const colors = LEVEL_COLORS[data.threat_level] || LEVEL_COLORS.MEDIUM
  const pBand = data.matrix_position.probability_band
  const iBand = data.matrix_position.impact_band

  return (
    <div className="space-y-6">
      {/* ── Header: Overall Risk ── */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className={`${colors.bg} ${colors.border} border`}>
          <CardContent className="pt-6 text-center">
            <ShieldAlert className={`h-10 w-10 mx-auto mb-2 ${colors.text}`} />
            <p className={`text-4xl font-bold ${colors.text}`}>{data.overall_risk_score}</p>
            <p className="text-xs text-slate-500 mt-1">Overall Risk Score</p>
            <Badge className={`mt-2 ${colors.bg} ${colors.text} ${colors.border} border`}>
              {data.threat_level}
            </Badge>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardContent className="pt-6 text-center">
            <Target className="h-10 w-10 mx-auto mb-2 text-blue-400" />
            <p className="text-lg font-semibold text-white">{data.probability_label}</p>
            <p className="text-xs text-slate-500">Probability Assessment</p>
            <p className="text-lg font-semibold text-white mt-2">{data.impact_label}</p>
            <p className="text-xs text-slate-500">Impact Assessment</p>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700/50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-center gap-2 mb-3">
              {TREND_ICONS[data.risk_trend]}
              <span className="text-sm text-slate-300">Trend: {data.risk_trend}</span>
            </div>
            {/* Mini Sparkline */}
            <div className="flex items-end gap-1 h-12 justify-center">
              {data.historical_scores.map((score, i) => {
                const height = Math.max((score / 100) * 48, 3)
                const isLast = i === data.historical_scores.length - 1
                return (
                  <div key={i}
                    className={`w-3 rounded-t transition-all ${isLast ? 'bg-blue-500' : 'bg-slate-700'}`}
                    style={{ height: `${height}px` }}
                    title={`${score}`}
                  />
                )
              })}
            </div>
            <p className="text-[10px] text-slate-600 text-center mt-2">Historical Risk Trend (7 assessments)</p>
          </CardContent>
        </Card>
      </div>

      {/* ── 5×5 Risk Matrix ── */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-slate-300 flex items-center gap-2">
            <Crosshair className="h-4 w-4 text-orange-400" /> Probability × Impact Matrix
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex">
            {/* Y-axis label */}
            <div className="flex flex-col justify-between pr-2 py-1">
              <span className="text-[9px] text-slate-500 rotate-0">Severe</span>
              <span className="text-[9px] text-slate-500 rotate-0">Major</span>
              <span className="text-[9px] text-slate-500 rotate-0">Moderate</span>
              <span className="text-[9px] text-slate-500 rotate-0">Minor</span>
              <span className="text-[9px] text-slate-500 rotate-0">Negligible</span>
            </div>
            {/* Matrix grid */}
            <div className="flex-1">
              <div className="grid grid-rows-5 gap-1">
                {[5, 4, 3, 2, 1].map((impactRow) => (
                  <div key={impactRow} className="grid grid-cols-5 gap-1">
                    {[1, 2, 3, 4, 5].map((probCol) => {
                      const isActive = probCol === pBand && impactRow === iBand
                      const rowIdx = 5 - impactRow
                      const colIdx = probCol - 1
                      const bgColor = MATRIX_COLORS[rowIdx]?.[colIdx] || 'bg-slate-700/30'
                      return (
                        <div key={probCol}
                          className={`h-8 rounded-sm flex items-center justify-center transition-all
                            ${bgColor}
                            ${isActive ? 'ring-2 ring-white ring-offset-1 ring-offset-slate-900 scale-110 z-10' : ''}
                          `}
                        >
                          {isActive && (
                            <div className="w-2.5 h-2.5 rounded-full bg-white animate-pulse" />
                          )}
                        </div>
                      )
                    })}
                  </div>
                ))}
              </div>
              {/* X-axis labels */}
              <div className="grid grid-cols-5 gap-1 mt-1">
                {['Very Low', 'Low', 'Moderate', 'High', 'Very High'].map((label) => (
                  <span key={label} className="text-[9px] text-slate-500 text-center">{label}</span>
                ))}
              </div>
              <p className="text-[10px] text-slate-600 text-center mt-1">← Probability →</p>
            </div>
          </div>
          <p className="text-[10px] text-slate-600 mt-1">↑ Impact</p>
        </CardContent>
      </Card>

      {/* ── Risk Dimensions ── */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-slate-300 flex items-center gap-2">
            <Zap className="h-4 w-4 text-yellow-400" /> Risk Dimensions
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {data.dimensions.map((dim, i) => {
            const dimColors: Record<string, string> = {
              NEGLIGIBLE: 'text-emerald-400',
              LOW: 'text-green-400',
              MODERATE: 'text-yellow-400',
              HIGH: 'text-orange-400',
              CRITICAL: 'text-red-400',
            }
            const barColors: Record<string, string> = {
              NEGLIGIBLE: 'bg-emerald-500',
              LOW: 'bg-green-500',
              MODERATE: 'bg-yellow-500',
              HIGH: 'bg-orange-500',
              CRITICAL: 'bg-red-500',
            }
            return (
              <div key={i} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-slate-300 font-medium">{dim.name}</span>
                  <Badge variant="outline" className={`text-xs ${dimColors[dim.level] || 'text-slate-400'} border-slate-700`}>
                    {dim.level}
                  </Badge>
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <div className="flex justify-between text-[10px] mb-0.5">
                      <span className="text-slate-500">Probability</span>
                      <span className="text-slate-400">{(dim.probability * 100).toFixed(0)}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${barColors[dim.level] || 'bg-slate-600'}`}
                        style={{ width: `${dim.probability * 100}%` }} />
                    </div>
                  </div>
                  <div>
                    <div className="flex justify-between text-[10px] mb-0.5">
                      <span className="text-slate-500">Impact</span>
                      <span className="text-slate-400">{(dim.impact * 100).toFixed(0)}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-slate-900 rounded-full overflow-hidden">
                      <div className={`h-full rounded-full ${barColors[dim.level] || 'bg-slate-600'}`}
                        style={{ width: `${dim.impact * 100}%` }} />
                    </div>
                  </div>
                </div>
                <p className="text-xs text-slate-500">{dim.explanation}</p>
              </div>
            )
          })}
        </CardContent>
      </Card>

      {/* ── Recommendations ── */}
      <Card className="bg-slate-800/50 border-slate-700/50">
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-slate-300 flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-400" /> Mitigation Recommendations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2">
            {data.recommendations.map((rec, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <span className={`mt-0.5 ${rec.includes('CRITICAL') || rec.includes('ALERT') ? 'text-red-400' : 'text-emerald-400'}`}>▸</span>
                <span className={`${rec.includes('CRITICAL') || rec.includes('ALERT') ? 'text-red-300 font-medium' : 'text-slate-300'}`}>{rec}</span>
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Footer */}
      <div className="text-center text-xs text-slate-600">
        Confidence: {(data.confidence * 100).toFixed(1)}% • Generated {new Date(data.generated_at).toLocaleTimeString()}
      </div>
    </div>
  )
}
