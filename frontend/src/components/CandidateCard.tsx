import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { Candidate } from '@/types/api'
import { CheckCircle2, AlertCircle, XCircle } from 'lucide-react'

interface CandidateCardProps {
  candidate: Candidate
  rank?: number
  isTop?: boolean
}

export function CandidateCard({ candidate, rank, isTop = false }: CandidateCardProps) {
  const confidenceColor = (conf: number) => {
    if (conf >= 80) return 'bg-green-900/20 border-green-700/50'
    if (conf >= 40) return 'bg-yellow-900/20 border-yellow-700/50'
    return 'bg-red-900/20 border-red-700/50'
  }

  const riskConfig: Record<string, { icon: React.ReactNode; color: string }> = {
    LOW: { icon: <CheckCircle2 className="h-4 w-4" />, color: 'text-green-400' },
    MEDIUM: { icon: <AlertCircle className="h-4 w-4" />, color: 'text-yellow-400' },
    HIGH: { icon: <AlertCircle className="h-4 w-4" />, color: 'text-orange-400' },
    CRITICAL: { icon: <XCircle className="h-4 w-4" />, color: 'text-red-400' },
  }

  const risk = riskConfig[candidate.risk_level || 'LOW'] || riskConfig.LOW

  return (
    <Card
      className={`border transition-all duration-200 ${confidenceColor(candidate.overall_confidence || 0)} ${
        isTop ? 'ring-1 ring-blue-500/50 shadow-lg shadow-blue-500/10' : ''
      }`}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2 flex-wrap">
              {rank && (
                <Badge variant="outline" className="bg-slate-800/80 text-slate-300 border-slate-600 font-mono">
                  #{rank}
                </Badge>
              )}
              <div className={`flex items-center gap-1 ${risk.color}`}>
                {risk.icon}
                <span className="text-xs font-medium">{candidate.risk_level || 'LOW'} RISK</span>
              </div>
            </div>
            <CardTitle className="text-xl truncate">{candidate.name}</CardTitle>
            {candidate.bio && (
              <p className="text-sm text-slate-400 mt-1.5 line-clamp-2">{candidate.bio}</p>
            )}
          </div>
          <div className="text-right flex-shrink-0">
            <div className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-cyan-300 bg-clip-text text-transparent tabular-nums">
              {(candidate.overall_confidence || 0).toFixed(1)}%
            </div>
            <p className="text-xs text-slate-500 mt-0.5">Confidence</p>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-4">
          {/* Aliases */}
          {candidate.aliases && candidate.aliases.length > 0 && (
            <div>
              <p className="text-xs font-medium text-slate-500 mb-1.5 uppercase tracking-wider">Aliases</p>
              <div className="flex flex-wrap gap-1.5">
                {candidate.aliases.map((alias) => (
                  <Badge key={alias} variant="secondary" className="text-xs bg-slate-800 text-slate-300 border-slate-700">
                    {alias}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Confidence breakdown grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            <ConfidenceCell label="Name" value={candidate.confidence_breakdown?.name_match} />
            <ConfidenceCell label="Bio" value={candidate.confidence_breakdown?.bio_similarity} />
            <ConfidenceCell label="Cross-Platform" value={candidate.confidence_breakdown?.cross_platform_consistency} />
            <ConfidenceCell label="Evidence" value={candidate.confidence_breakdown?.evidence_corroboration} />
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function ConfidenceCell({ label, value }: { label: string; value?: number }) {
  const rawValue = value ?? 5.0
  const safeValue = Math.max(5.0, Math.min(98.0, Number(rawValue) || 5.0))
  const color =
    safeValue >= 80 ? 'text-green-400' : safeValue >= 40 ? 'text-yellow-400' : 'text-red-400'

  const bgBar =
    safeValue >= 80 ? 'bg-green-500/20' : safeValue >= 40 ? 'bg-yellow-500/20' : 'bg-red-500/20'

  return (
    <div className="bg-slate-800/50 rounded-lg p-2.5 relative overflow-hidden" title={`${label}: ${safeValue.toFixed(1)}/100`}>
      {/* Background fill bar */}
      <div
        className={`absolute bottom-0 left-0 h-1 rounded-full ${bgBar}`}
        style={{ width: `${Math.min(safeValue, 100)}%` }}
      />
      <p className={`text-lg font-bold tabular-nums ${color}`}>{safeValue.toFixed(0)}</p>
      <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">{label}</p>
    </div>
  )
}
