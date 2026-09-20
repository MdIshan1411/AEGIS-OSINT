import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { KnowledgeGraph } from './KnowledgeGraph'
import { ConfidenceBreakdown } from './ConfidenceBreakdown'
import { TimelineView } from './TimelineView'
import { ConflictPanel } from './ConflictPanel'
import { CandidateCard } from './CandidateCard'
import { ActiveAccounts } from './ActiveAccounts'
import { ThreatProfilePanel } from './ThreatProfile'
import { BehavioralAnalysisPanel } from './BehavioralAnalysis'
import { RiskMatrixPanel } from './RiskMatrix'
import { useInvestigation } from '@/hooks/useInvestigation'
import {
  Loader2, ArrowLeft, CheckCircle2, AlertCircle, Clock,
  Users, Network, BarChart3, Calendar, AlertTriangle, Fingerprint,
  ShieldAlert, Brain, Target,
} from 'lucide-react'

interface InvestigationDetailProps {
  investigationId: string
  onBack: () => void
}

export function InvestigationDetail({ investigationId, onBack }: InvestigationDetailProps) {
  const { investigation, loading, error } = useInvestigation(investigationId)
  const [activeTab, setActiveTab] = useState('candidates')

  // Loading state
  if (loading && !investigation) {
    return (
      <div className="flex flex-col items-center justify-center py-24">
        <div className="relative">
          <div className="w-20 h-20 rounded-full border-4 border-slate-700 border-t-blue-500 animate-spin" />
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-10 h-10 rounded-full bg-blue-500/20 animate-pulse" />
          </div>
        </div>
        <p className="text-slate-300 font-medium mt-6">Processing investigation...</p>
        <p className="text-sm text-slate-500 mt-2">Searching across GitHub, LinkedIn, X, Instagram</p>
        <p className="text-xs text-slate-600 mt-4 font-mono">{investigationId}</p>
      </div>
    )
  }

  // Error state
  if (error) {
    return (
      <Card className="bg-red-900/10 border-red-700/30 max-w-lg mx-auto mt-12">
        <CardContent className="pt-6 text-center">
          <AlertCircle className="h-10 w-10 text-red-400 mx-auto mb-3" />
          <p className="text-red-200 font-medium">{error}</p>
          <Button onClick={onBack} variant="outline" className="mt-4">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Dashboard
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (!investigation) return null

  // Backend is synchronous now, so if we have it, it's complete
  const isComplete = true
  const isProcessing = false

  const currentStatus = { icon: <CheckCircle2 className="h-4 w-4" />, color: 'text-green-400', bg: 'bg-green-500/10 border-green-500/20' }

  return (
    <div className="space-y-6">
      {/* Header bar */}
      <div className="flex flex-col md:flex-row items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3 mb-3 flex-wrap">
            <Button variant="ghost" size="sm" onClick={onBack} className="text-slate-400 hover:text-white">
              <ArrowLeft className="h-4 w-4 mr-1.5" />
              Back
            </Button>
            <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full border text-sm ${currentStatus.color} ${currentStatus.bg}`}>
              {currentStatus.icon}
              <span className="font-medium">COMPLETE</span>
            </div>
          </div>
          <h2 className="text-3xl font-bold text-white tracking-tight">
            {investigation.subject_name}
          </h2>
          <p className="text-sm text-slate-500 mt-2 font-mono">
            {investigationId}
          </p>
        </div>

        {isComplete && (
          <div className="text-right text-sm space-y-1">
            <p className="text-slate-400">
              ⚡ Generated from scratch
            </p>
            <p className="text-xs text-slate-600">
              {new Date(investigation.timestamp).toLocaleString()}
            </p>
          </div>
        )}
      </div>

      {/* Still processing */}
      {isProcessing && (
        <Card className="bg-blue-900/10 border-blue-700/30">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <Loader2 className="h-5 w-5 animate-spin text-blue-400" />
              <div>
                <p className="text-blue-200 font-medium">Investigation in progress...</p>
                <p className="text-sm text-blue-400/60 mt-0.5">Auto-refreshing every 2 seconds</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Top candidate hero - ONLY if email was provided */}
      {isComplete && investigation.top_candidate && investigation.email_hint && (
        <Card className="bg-gradient-to-r from-blue-900/20 via-slate-900/50 to-cyan-900/20 border-blue-700/20 shadow-xl shadow-blue-500/5">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Users className="h-5 w-5 text-blue-400" />
              Top Candidate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <CandidateCard candidate={investigation.top_candidate} isTop={true} rank={1} />
          </CardContent>
        </Card>
      )}

      {/* Tabbed content */}
      {isComplete && (
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="bg-slate-800/50 border border-slate-700/30 p-1 flex-wrap h-auto gap-0.5">
            <TabsTrigger value="candidates" className="gap-1.5">
              <Users className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">Candidates</span>
              <Badge variant="secondary" className="ml-1 h-5 px-1.5 text-[10px] bg-slate-700">
                {investigation.candidates.length}
              </Badge>
            </TabsTrigger>
            {/* Deep Intelligence Tabs - ONLY if email was provided */}
            {investigation.email_hint && (
              <>
                <TabsTrigger value="active-accounts" className="gap-1.5 text-violet-400 data-[state=active]:text-violet-300">
                  <Fingerprint className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Active Accounts</span>
                </TabsTrigger>
                <TabsTrigger value="threat-intel" className="gap-1.5 text-red-400 data-[state=active]:text-red-300">
                  <ShieldAlert className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Threat Intel</span>
                </TabsTrigger>
                <TabsTrigger value="behavioral" className="gap-1.5 text-purple-400 data-[state=active]:text-purple-300">
                  <Brain className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Behavioral</span>
                </TabsTrigger>
                <TabsTrigger value="risk-matrix" className="gap-1.5 text-orange-400 data-[state=active]:text-orange-300">
                  <Target className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Risk Matrix</span>
                </TabsTrigger>
                <TabsTrigger value="breakdown" className="gap-1.5">
                  <BarChart3 className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Confidence</span>
                </TabsTrigger>
                <TabsTrigger value="timeline" className="gap-1.5">
                  <Calendar className="h-3.5 w-3.5" />
                  <span className="hidden sm:inline">Timeline</span>
                </TabsTrigger>
                {investigation.conflicts_detected > 0 && (
                  <TabsTrigger value="conflicts" className="gap-1.5 text-red-400 data-[state=active]:text-red-300">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    <span className="hidden sm:inline">Conflicts</span>
                    <Badge variant="destructive" className="ml-1 h-5 px-1.5 text-[10px]">
                      {investigation.conflicts_detected}
                    </Badge>
                  </TabsTrigger>
                )}
              </>
            )}
          </TabsList>

          <TabsContent value="candidates" className="space-y-3">
            {investigation.candidates.map((candidate, idx) => (
              <CandidateCard
                key={candidate.candidate_id}
                candidate={candidate}
                rank={idx + 1}
                isTop={candidate.candidate_id === investigation.top_candidate?.candidate_id}
              />
            ))}
          </TabsContent>

          {/* Deep Intelligence Content - ONLY if email was provided */}
          {investigation.email_hint && (
            <>
              <TabsContent value="active-accounts">
                <ActiveAccounts
                  emailHint={investigation.email_hint}
                  subjectName={investigation.subject_name}
                />
              </TabsContent>

              <TabsContent value="threat-intel">
                <ThreatProfilePanel
                  subjectName={investigation.subject_name}
                  emailHint={investigation.email_hint}
                />
              </TabsContent>

              <TabsContent value="behavioral">
                <BehavioralAnalysisPanel
                  subjectName={investigation.subject_name}
                  emailHint={investigation.email_hint}
                />
              </TabsContent>

              <TabsContent value="risk-matrix">
                <RiskMatrixPanel
                  subjectName={investigation.subject_name}
                  emailHint={investigation.email_hint}
                />
              </TabsContent>

              <TabsContent value="graph">
                <Card className="bg-slate-900 border-slate-700/50">
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <Network className="h-5 w-5 text-blue-400" />
                      Relationship Knowledge Graph
                    </CardTitle>
                    <CardDescription>
                      Interactive visualization. Drag nodes, zoom, and pan. Red dashed lines indicate conflicts.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <KnowledgeGraph graph={{ nodes: investigation.graph_nodes, edges: investigation.graph_edges }} />
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="breakdown">
                {investigation.top_candidate && (
                  <ConfidenceBreakdown candidate={investigation.top_candidate} />
                )}
              </TabsContent>

              <TabsContent value="timeline">
                <TimelineView events={investigation.candidates.flatMap(c => c.timeline_events)} />
              </TabsContent>

              {investigation.conflicts_detected > 0 && (
                <TabsContent value="conflicts">
                  <ConflictPanel
                    conflicts={investigation.candidates.flatMap(c => c.conflicts)}
                    investigationId={investigationId}
                  />
                </TabsContent>
              )}
            </>
          )}
        </Tabs>
      )}
    </div>
  )
}
