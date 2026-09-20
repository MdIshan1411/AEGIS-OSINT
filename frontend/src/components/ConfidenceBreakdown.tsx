import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { Candidate } from '@/types/api'
import { Info, TrendingUp, CheckCircle2, XCircle, FileSearch, ShieldAlert } from 'lucide-react'

interface ConfidenceBreakdownProps {
  candidate: Candidate
}

export function ConfidenceBreakdown({ candidate }: ConfidenceBreakdownProps) {
  const breakdown = candidate.confidence_breakdown || {}

  const data = [
    {
      feature: 'Name Match',
      value: breakdown.name_match || 0,
      description: 'Jaro-Winkler + rapidfuzz string similarity with nickname expansion',
    },
    {
      feature: 'Bio Similarity',
      value: breakdown.bio_similarity || 0,
      description: 'TF-IDF cosine similarity across platform bios',
    },
    {
      feature: 'Cross-Platform',
      value: breakdown.cross_platform_consistency || 0,
      description: 'Agreement strength across GitHub, LinkedIn, X profiles',
    },
    {
      feature: 'Evidence',
      value: breakdown.evidence_corroboration || 0,
      description: 'Supporting evidence claims found and verified',
    },
  ]

  const getColor = (value: number) => {
    if (value >= 80) return '#10b981'
    if (value >= 40) return '#f59e0b'
    return '#ef4444'
  }

  const statusColor = 
    breakdown.match_status?.includes('STRONG') ? 'text-green-400' :
    breakdown.match_status?.includes('POSSIBLE') ? 'text-emerald-400' :
    breakdown.match_status?.includes('CONFLICTING') ? 'text-red-400' :
    'text-yellow-400'

  return (
    <div className="space-y-6">
      {/* Overall score hero */}
      <Card className="bg-gradient-to-r from-blue-900/30 to-cyan-900/20 border-blue-700/30">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400 font-medium">Overall Confidence</p>
              <p className="text-5xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent tabular-nums mt-1">
                {(candidate.overall_confidence || 0).toFixed(1)}%
              </p>
              <div className="mt-2 space-y-1">
                <p className="text-sm text-slate-500 flex items-center gap-2">
                  Status: <span className={`font-bold ${statusColor}`}>{breakdown.match_status?.replace(/_/g, ' ') || 'UNKNOWN'}</span>
                </p>
                <p className="text-sm text-slate-500">
                  Risk Level: <span className="font-semibold text-slate-300">{candidate.risk_level || 'LOW'}</span>
                </p>
              </div>
            </div>
            <div className="h-20 w-20 rounded-full bg-slate-800/50 flex items-center justify-center">
              <TrendingUp className="h-10 w-10 text-blue-400" />
            </div>
          </div>
          {breakdown.explanation && (
            <div className="mt-4 pt-4 border-t border-blue-800/30">
              <p className="text-slate-300 font-medium">{breakdown.explanation}</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Explanation Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {breakdown.match_reasons && breakdown.match_reasons.length > 0 && (
          <Card className="bg-slate-900/80 border-green-900/30">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2 text-green-400">
                <CheckCircle2 className="h-4 w-4" /> Why it matches
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {breakdown.match_reasons.map((reason, i) => (
                  <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">•</span> {reason}
                  </li>
                ))}
                {breakdown.supporting_evidence?.map((reason, i) => (
                  <li key={`sup-${i}`} className="text-sm text-slate-300 flex items-start gap-2">
                    <span className="text-green-500 mt-0.5">•</span> {reason}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {(breakdown.mismatch_reasons && breakdown.mismatch_reasons.length > 0) || (breakdown.contradicting_evidence && breakdown.contradicting_evidence.length > 0) ? (
          <Card className="bg-slate-900/80 border-red-900/30">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2 text-red-400">
                <XCircle className="h-4 w-4" /> Why it may not match
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {breakdown.mismatch_reasons?.map((reason, i) => (
                  <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                    <span className="text-red-500 mt-0.5">•</span> {reason}
                  </li>
                ))}
                {breakdown.contradicting_evidence?.map((reason, i) => (
                  <li key={`con-${i}`} className="text-sm text-slate-300 flex items-start gap-2">
                    <span className="text-red-500 mt-0.5">•</span> {reason}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        ) : null}

        {breakdown.missing_evidence && breakdown.missing_evidence.length > 0 && (
          <Card className="bg-slate-900/80 border-slate-700/50 md:col-span-2">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2 text-slate-400">
                <FileSearch className="h-4 w-4" /> Missing or Insufficient Data
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-slate-400">
                {breakdown.missing_evidence.map((reason, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-slate-500 mt-0.5">•</span> {reason}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Chart */}
      <Card className="bg-slate-900 border-slate-700/50">
        <CardHeader>
          <CardTitle className="text-lg">Feature Breakdown</CardTitle>
          <CardDescription>
            Per-feature contribution to the overall confidence score
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                <XAxis
                  dataKey="feature"
                  tick={{ fontSize: 11, fill: '#94a3b8' }}
                  axisLine={{ stroke: '#334155' }}
                  tickLine={{ stroke: '#334155' }}
                />
                <YAxis
                  domain={[0, 100]}
                  tick={{ fontSize: 11, fill: '#94a3b8' }}
                  axisLine={{ stroke: '#334155' }}
                  tickLine={{ stroke: '#334155' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    fontSize: '12px',
                  }}
                  labelStyle={{ color: '#e2e8f0', fontWeight: 600 }}
                  itemStyle={{ color: '#94a3b8' }}
                />
                <Bar dataKey="value" radius={[6, 6, 0, 0]} maxBarSize={60}>
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={getColor(entry.value)} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Feature details */}
          <div className="mt-6 space-y-2">
            {data.map((item) => (
              <div key={item.feature} className="flex items-start gap-3 p-3 bg-slate-800/30 rounded-lg border border-slate-700/30">
                <Info className="h-4 w-4 text-slate-500 flex-shrink-0 mt-0.5" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm text-slate-200">{item.feature}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{item.description}</p>
                </div>
                <div className="text-right flex-shrink-0">
                  <p className={`text-lg font-bold tabular-nums ${
                    item.value >= 80 ? 'text-green-400' : item.value >= 40 ? 'text-yellow-400' : 'text-red-400'
                  }`}>
                    {item.value.toFixed(1)}
                  </p>
                  <p className="text-[10px] text-slate-600">/ 100</p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
