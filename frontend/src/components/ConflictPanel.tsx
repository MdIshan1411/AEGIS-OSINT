import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type { Conflict } from '@/types/api'
import { api } from '@/services/api'
import { AlertTriangle, CheckCircle, XCircle, Loader2, MapPin } from 'lucide-react'

interface ConflictPanelProps {
  conflicts: Conflict[]
  investigationId: string
}

const SEVERITY_STYLES: Record<string, { bg: string; border: string; badge: string }> = {
  HIGH: {
    bg: 'bg-red-900/15',
    border: 'border-red-700/40',
    badge: 'bg-red-900/50 text-red-300 border-red-700/50',
  },
  MEDIUM: {
    bg: 'bg-yellow-900/15',
    border: 'border-yellow-700/40',
    badge: 'bg-yellow-900/50 text-yellow-300 border-yellow-700/50',
  },
  LOW: {
    bg: 'bg-blue-900/15',
    border: 'border-blue-700/40',
    badge: 'bg-blue-900/50 text-blue-300 border-blue-700/50',
  },
}

export function ConflictPanel({ conflicts, investigationId }: ConflictPanelProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <AlertTriangle className="h-5 w-5 text-amber-400" />
        <h3 className="font-semibold text-white">
          {conflicts.length} Conflict{conflicts.length !== 1 ? 's' : ''} Detected
        </h3>
      </div>

      {conflicts.map((conflict) => {
        const severity = SEVERITY_STYLES[conflict.severity] || SEVERITY_STYLES.MEDIUM

        return (
          <Card
            key={conflict.conflict_id}
            className={`border ${severity.bg} ${severity.border} transition-all duration-200`}
          >
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                    <MapPin className="h-4 w-4 text-slate-400" />
                    <Badge variant="outline" className={severity.badge}>
                      {conflict.severity}
                    </Badge>
                    <Badge variant="outline" className="bg-slate-800/50 text-slate-300 border-slate-700/50 text-xs">
                      {conflict.conflict_type}
                    </Badge>
                  </div>
                  <CardTitle className="text-base">{conflict.description}</CardTitle>
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-3">
              {/* Platforms involved */}
              {conflict.affected_platforms && conflict.affected_platforms.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  <span className="text-xs text-slate-500">Affected Platforms:</span>
                  {conflict.affected_platforms.map((platform) => (
                    <Badge key={platform} variant="secondary" className="text-[10px] bg-slate-800 border-slate-700">
                      {platform}
                    </Badge>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
