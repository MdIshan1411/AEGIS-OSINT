import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import type { TimelineEvent } from '@/types/api'
import { Calendar, Building2, FileText, Trophy, Zap, GitBranch } from 'lucide-react'

interface TimelineViewProps {
  events: TimelineEvent[]
}

const EVENT_ICONS: Record<string, React.ReactNode> = {
  EMPLOYMENT: <Building2 className="h-4 w-4" />,
  PROJECT: <Trophy className="h-4 w-4" />,
  PUBLICATION: <FileText className="h-4 w-4" />,
  EVENT: <Zap className="h-4 w-4" />,
  CONTRIBUTION: <GitBranch className="h-4 w-4" />,
}

const EVENT_COLORS: Record<string, string> = {
  EMPLOYMENT: 'bg-blue-500',
  PROJECT: 'bg-amber-500',
  PUBLICATION: 'bg-cyan-500',
  EVENT: 'bg-purple-500',
  CONTRIBUTION: 'bg-green-500',
}

export function TimelineView({ events }: TimelineViewProps) {
  if (!events || events.length === 0) {
    return (
      <Card className="bg-slate-900 border-slate-700/50">
        <CardContent className="pt-6">
          <div className="text-center py-12">
            <Calendar className="h-12 w-12 text-slate-700 mx-auto mb-3" />
            <p className="text-slate-500 font-medium">No timeline events found</p>
            <p className="text-xs text-slate-600 mt-1">
              Timeline events are extracted from employment history, projects, and publications
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const sortedEvents = [...events].sort(
    (a, b) =>
      new Date(b.timestamp || '').getTime() -
      new Date(a.timestamp || '').getTime()
  )

  return (
    <Card className="bg-slate-900 border-slate-700/50">
      <CardHeader>
        <CardTitle className="text-lg">Professional Timeline</CardTitle>
        <CardDescription>{events.length} events discovered across platforms</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-1">
          {sortedEvents.map((event, idx) => (
            <div key={`${event.timestamp}-${idx}`} className="flex gap-4 group">
              {/* Timeline line + dot */}
              <div className="flex flex-col items-center">
                <div
                  className={`flex items-center justify-center w-9 h-9 rounded-full flex-shrink-0 text-white shadow-lg ${
                    EVENT_COLORS[event.event_type] || 'bg-slate-600'
                  }`}
                >
                  {EVENT_ICONS[event.event_type] || <Calendar className="h-4 w-4" />}
                </div>
                {idx < sortedEvents.length - 1 && (
                  <div className="w-px h-full min-h-[3rem] bg-slate-700/50 my-1" />
                )}
              </div>

              {/* Event content */}
              <div className="flex-1 pb-6 pt-1">
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <h4 className="font-semibold text-white text-sm group-hover:text-blue-300 transition-colors">
                      {event.title}
                    </h4>
                    {event.platform && (
                      <p className="text-sm text-slate-400 mt-0.5 flex items-center gap-1">
                        <Building2 className="h-3 w-3" />
                        {event.platform} {event.location ? `- ${event.location}` : ''}
                      </p>
                    )}
                    {event.description && (
                      <p className="text-xs text-slate-500 mt-1.5 leading-relaxed">
                        {event.description}
                      </p>
                    )}
                  </div>
                  <Badge
                    variant="outline"
                    className="flex-shrink-0 text-[10px] bg-slate-800/50 border-slate-700/50 text-slate-400"
                  >
                    {event.event_type}
                  </Badge>
                </div>

                {/* Date range + confidence */}
                <div className="flex items-center gap-4 text-xs text-slate-500 mt-2">
                  <div className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    <span>
                      {event.timestamp
                        ? new Date(event.timestamp).toLocaleDateString('en-US', {
                            year: 'numeric',
                            month: 'short',
                          })
                        : 'Unknown'}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
