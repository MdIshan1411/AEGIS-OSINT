import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, Search, Fingerprint, Shield, Network } from 'lucide-react'
import { api } from '@/services/api'

interface InvestigationDashboardProps {
  onInvestigationCreated: (id: string) => void
}

export function InvestigationDashboard({ onInvestigationCreated }: InvestigationDashboardProps) {
  const [subjectName, setSubjectName] = useState('')
  const [email, setEmail] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleCreateInvestigation = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const response = await api.createInvestigation({
        subject_name: subjectName,
        email_hint: email || undefined,
        domain_context: undefined,
      })
      onInvestigationCreated(response.investigation_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create investigation')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-12">
      {/* Hero */}
      <div className="text-center space-y-6 pt-8">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-sm font-medium">
          <Shield className="h-4 w-4" />
          Privacy-First Entity Resolution
        </div>
        <h2 className="text-4xl md:text-5xl font-bold text-white leading-tight">
          Discover Digital
          <br />
          <span className="bg-gradient-to-r from-blue-400 via-cyan-300 to-teal-400 bg-clip-text text-transparent">
            Identity Connections
          </span>
        </h2>
        <p className="text-lg text-slate-400 max-w-2xl mx-auto leading-relaxed">
          Search across GitHub, LinkedIn, X, and Instagram. TRACE-X correlates profiles,
          detects conflicts, and returns ranked candidates with auditable evidence.
        </p>
      </div>

      {/* Feature pills */}
      <div className="flex flex-wrap justify-center gap-3">
        {[
          { icon: <Fingerprint className="h-4 w-4" />, text: 'Bayesian Confidence Scoring' },
          { icon: <Network className="h-4 w-4" />, text: 'Knowledge Graph Visualization' },
          { icon: <Shield className="h-4 w-4" />, text: 'Conflict Detection & Resolution' },
        ].map((feature) => (
          <div
            key={feature.text}
            className="flex items-center gap-2 px-4 py-2 rounded-full bg-slate-800/50 border border-slate-700/50 text-sm text-slate-300"
          >
            {feature.icon}
            {feature.text}
          </div>
        ))}
      </div>

      {/* Search Card */}
      <Card className="max-w-2xl mx-auto bg-slate-900/80 border-slate-700/50 backdrop-blur-sm shadow-2xl shadow-blue-500/5">
        <CardHeader>
          <CardTitle className="text-xl">Start Investigation</CardTitle>
          <CardDescription>
            Provide subject details to begin cross-platform entity resolution
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleCreateInvestigation} className="space-y-4">
            <div>
              <label htmlFor="subject-name" className="block text-sm font-medium text-slate-300 mb-2">
                Subject Name <span className="text-red-400">*</span>
              </label>
              <Input
                id="subject-name"
                placeholder="e.g., Alice Johnson, Bob Chen, John Smith"
                value={subjectName}
                onChange={(e) => setSubjectName(e.target.value)}
                disabled={loading}
                required
                aria-required="true"
              />
              <p className="text-xs text-slate-500 mt-1.5">
                Try demo scenarios: Alice Johnson, Bob Chen, or John Smith
              </p>
            </div>

            <div>
              <label htmlFor="subject-email" className="block text-sm font-medium text-slate-300 mb-2">
                Email Hint <span className="text-slate-500">(optional)</span>
              </label>
              <Input
                id="subject-email"
                type="email"
                placeholder="user@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
              />
            </div>

            {error && (
              <div
                className="p-3 bg-red-900/30 border border-red-700/50 rounded-lg text-red-200 text-sm flex items-start gap-2"
                role="alert"
              >
                <span className="text-red-400 mt-0.5">⚠</span>
                {error}
              </div>
            )}

            <Button
              type="submit"
              disabled={loading || !subjectName.trim()}
              className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white shadow-lg shadow-blue-500/25 h-11"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating Investigation...
                </>
              ) : (
                <>
                  <Search className="mr-2 h-4 w-4" />
                  Create Investigation
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Demo Scenarios */}
      <Card className="max-w-2xl mx-auto bg-slate-900/50 border-slate-800/50">
        <CardHeader>
          <CardTitle className="text-lg">Demo Scenarios</CardTitle>
          <CardDescription>Click to autofill — each triggers a different ML outcome</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {[
              {
                name: 'Alice Johnson',
                desc: 'Clear match across platforms',
                badge: '>85% confidence',
                color: 'border-green-700/40 hover:border-green-600/60 hover:bg-green-900/10',
                badgeColor: 'text-green-400',
              },
              {
                name: 'John Smith',
                desc: 'Ambiguous namesake — 3 different people',
                badge: '<40% confidence',
                color: 'border-yellow-700/40 hover:border-yellow-600/60 hover:bg-yellow-900/10',
                badgeColor: 'text-yellow-400',
              },
              {
                name: 'Bob Chen',
                desc: 'Location conflict flagged (SF + Tokyo)',
                badge: 'Conflict detected',
                color: 'border-red-700/40 hover:border-red-600/60 hover:bg-red-900/10',
                badgeColor: 'text-red-400',
              },
            ].map((scenario) => (
              <button
                key={scenario.name}
                onClick={() => setSubjectName(scenario.name)}
                className={`p-4 bg-slate-800/30 rounded-lg border text-left transition-all duration-200 group ${scenario.color}`}
                aria-label={`Autofill ${scenario.name}`}
              >
                <p className="font-semibold text-white group-hover:text-blue-300 transition-colors">
                  {scenario.name}
                </p>
                <p className="text-xs text-slate-400 mt-1">{scenario.desc}</p>
                <p className={`text-xs font-medium mt-2 ${scenario.badgeColor}`}>
                  {scenario.badge}
                </p>
              </button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
