import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { api } from '@/services/api'
import type { EmailScanResponse, ServiceResult } from '@/types/email-scanner'
import {
  Shield, ShieldAlert, ShieldCheck, ExternalLink,
  Mail, Clock, Activity, Globe, Gamepad2, Code, Briefcase,
  ShoppingCart, MonitorPlay, Loader2, Terminal, CheckCircle2,
  XCircle, AlertTriangle, ChevronDown, Fingerprint
} from 'lucide-react'

const CATEGORY_CONFIG: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  ALL:          { label: 'All',           icon: <Globe className="w-3.5 h-3.5" />,        color: 'text-slate-300' },
  DEV:          { label: 'Developer',     icon: <Code className="w-3.5 h-3.5" />,         color: 'text-blue-400' },
  SOCIAL:       { label: 'Social',        icon: <Globe className="w-3.5 h-3.5" />,        color: 'text-purple-400' },
  PROFESSIONAL: { label: 'Professional',  icon: <Briefcase className="w-3.5 h-3.5" />,    color: 'text-cyan-400' },
  GAMING:       { label: 'Gaming',        icon: <Gamepad2 className="w-3.5 h-3.5" />,     color: 'text-green-400' },
  EMAIL:        { label: 'Email',         icon: <Mail className="w-3.5 h-3.5" />,          color: 'text-yellow-400' },
  SECURITY:     { label: 'Security',      icon: <Shield className="w-3.5 h-3.5" />,       color: 'text-red-400' },
  MEDIA:        { label: 'Media',         icon: <MonitorPlay className="w-3.5 h-3.5" />,  color: 'text-pink-400' },
  ECOMMERCE:    { label: 'E-Commerce',    icon: <ShoppingCart className="w-3.5 h-3.5" />, color: 'text-orange-400' },
  OTHER:        { label: 'Other',         icon: <Activity className="w-3.5 h-3.5" />,     color: 'text-slate-400' },
}

const STATUS_CONFIG: Record<string, { icon: React.ReactNode; color: string; bg: string; label: string }> = {
  REGISTERED:     { icon: <CheckCircle2 className="w-4 h-4" />, color: 'text-green-400',   bg: 'bg-green-500/10 border-green-500/30',  label: 'Found' },
  BREACHED:       { icon: <ShieldAlert className="w-4 h-4" />,  color: 'text-red-400',     bg: 'bg-red-500/10 border-red-500/30',      label: 'Breached' },
  SAFE:           { icon: <ShieldCheck className="w-4 h-4" />,  color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/30', label: 'Safe' },
  NOT_REGISTERED: { icon: <XCircle className="w-4 h-4" />,      color: 'text-slate-500',   bg: 'bg-slate-800/50 border-slate-700/30',  label: 'Not Found' },
  ERROR:          { icon: <AlertTriangle className="w-4 h-4" />, color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/30', label: 'Error' },
  TIMEOUT:        { icon: <Clock className="w-4 h-4" />,        color: 'text-orange-400',  bg: 'bg-orange-500/10 border-orange-500/30', label: 'Timeout' },
}

const PRIORITY_SERVICES = [
  "Google (Gmail)",
  "GitHub",
  "GitLab",
  "Docker Hub",
  "DEV.to",
  "LinkedIn",
  "X (Twitter)",
  "Instagram",
  "Spotify",
  "Chess.com",
  "Discord",
  "Steam",
  "Dropbox",
  "Gravatar",
  "HackerRank",
  "Have I Been Pwned",
  "Amazon",
  "Flipkart",
  "YouTube",
  "Apple iCloud"
]

interface ActiveAccountsProps {
  emailHint: string
  subjectName: string
}

export function ActiveAccounts({ emailHint, subjectName }: ActiveAccountsProps) {
  const [scanResult, setScanResult] = useState<EmailScanResponse | null>(null)
  const [isScanning, setIsScanning] = useState(false)
  const [scanTimeMs, setScanTimeMs] = useState(0)
  const [activeCategory, setActiveCategory] = useState('ALL')
  const [terminalLines, setTerminalLines] = useState<string[]>([])
  const [scanProgress, setScanProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const terminalRef = useRef<HTMLDivElement>(null)
  const startTimeRef = useRef<number>(0)
  const hasScannedRef = useRef(false)

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [terminalLines])

  // Auto-scan on mount
  useEffect(() => {
    if (emailHint && !hasScannedRef.current) {
      hasScannedRef.current = true
      runScan()
    }
  }, [emailHint])

  const simulateTerminalOutput = (results: ServiceResult[], elapsedMs: number) => {
    const lines: string[] = []
    lines.push(`[TRACE-X] Active Accounts Scanner v2.0`)
    lines.push(`[TARGET] ${subjectName} <${emailHint}>`)
    lines.push(`[INIT] Loading ${results.length} service providers...`)
    lines.push(`[START] Checking registrations across all providers...`)
    lines.push(``)

    let idx = 0
    const interval = setInterval(() => {
      if (idx >= results.length) {
        clearInterval(interval)
        const registered = results.filter(r => r.status === 'REGISTERED' || r.status === 'BREACHED').length
        lines.push(``)
        lines.push(`[DONE] Scan complete in ${elapsedMs}ms.`)
        lines.push(`[RESULT] ${registered}/${results.length} active accounts found.`)
        setTerminalLines([...lines])
        return
      }

      const r = results[idx]
      // Only print lines for successful checks, registered hits, or priority checks
      if (r.status === 'REGISTERED' || r.status === 'BREACHED' || PRIORITY_SERVICES.includes(r.service)) {
        const statusIcon = r.status === 'REGISTERED' ? '✓' : r.status === 'BREACHED' ? '⚠' : r.status === 'NOT_REGISTERED' ? '✗' : '?'
        const pad = r.service.padEnd(22)
        lines.push(`  [${statusIcon}] ${pad} ${r.status.padEnd(16)} ${r.check_duration_ms}ms`)
        setTerminalLines([...lines])
      }
      setScanProgress(Math.round(((idx + 1) / results.length) * 100))
      idx++
    }, 35)
  }

  const runScan = async () => {
    setIsScanning(true)
    setScanResult(null)
    setError(null)
    setTerminalLines([])
    setScanProgress(0)
    setScanTimeMs(0)
    startTimeRef.current = performance.now()

    try {
      const res = await api.scanEmail(emailHint)
      const elapsed = Math.round(performance.now() - startTimeRef.current)
      setScanTimeMs(elapsed)
      setScanResult(res)
      simulateTerminalOutput(res.results, elapsed)
    } catch (err: any) {
      const elapsed = Math.round(performance.now() - startTimeRef.current)
      setScanTimeMs(elapsed)
      const msg = err?.response?.data?.detail || 'Scan failed.'
      setError(msg)
      setTerminalLines(prev => [...prev, `[ERROR] ${msg}`])
    } finally {
      setIsScanning(false)
    }
  }

  // Filter the raw results for UI display
  const baseFilteredServices = scanResult?.results?.filter(r => {
    if (r.status === 'ERROR' || r.status === 'TIMEOUT') return false;
    if (r.status === 'REGISTERED' || r.status === 'BREACHED') return true;
    return PRIORITY_SERVICES.includes(r.service);
  }) ?? []

  const filteredResults = baseFilteredServices.filter(r =>
    activeCategory === 'ALL' || r.category === activeCategory
  )

  const categories = baseFilteredServices.length > 0
    ? ['ALL', ...new Set(baseFilteredServices.map(r => r.category))]
    : []

  return (
    <div className="space-y-4">
      {/* Header card */}
      <Card className="bg-slate-900 border-slate-700/50">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Fingerprint className="h-5 w-5 text-violet-400" />
            Active Accounts
          </CardTitle>
          <CardDescription>
            Checking <span className="text-violet-300 font-mono">{emailHint}</span> across 120+ online services using real HTTP probes
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Terminal + Progress */}
      {terminalLines.length > 0 && (
        <Card className="border-slate-800 bg-slate-950 overflow-hidden">
          <CardHeader className="pb-2 flex flex-row items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-green-400" />
              <CardTitle className="text-sm font-mono text-green-400">Scan Output</CardTitle>
            </div>
            {scanProgress > 0 && scanProgress < 100 && (
              <span className="text-xs text-slate-500 font-mono">{scanProgress}%</span>
            )}
          </CardHeader>
          {scanProgress > 0 && (
            <div className="px-6 pb-1">
              <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-violet-500 to-fuchsia-500 rounded-full transition-all duration-200"
                  style={{ width: `${scanProgress}%` }}
                />
              </div>
            </div>
          )}
          <CardContent className="pt-2">
            <div
              ref={terminalRef}
              className="bg-black/50 rounded-lg p-4 font-mono text-xs text-green-300/80 max-h-48 overflow-y-auto leading-5 whitespace-pre"
            >
              {terminalLines.map((line, i) => (
                <div key={i} className={
                  line.includes('[ERROR]') ? 'text-red-400' :
                  line.includes('[DONE]') || line.includes('[RESULT]') ? 'text-green-400 font-bold' :
                  line.includes('[✓]') ? 'text-green-400/70' :
                  line.includes('[⚠]') ? 'text-red-400/80' :
                  line.includes('[✗]') ? 'text-slate-600' :
                  'text-green-300/60'
                }>{line}</div>
              ))}
              {isScanning && <span className="animate-pulse">█</span>}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Summary Stats */}
      {scanResult && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <StatCard label="Services Checked" value={baseFilteredServices.length} color="text-slate-300" />
          <StatCard label="Registered" value={baseFilteredServices.filter(r => r.status === 'REGISTERED').length} color="text-green-400" />
          <StatCard label="Not Found" value={baseFilteredServices.filter(r => r.status === 'NOT_REGISTERED').length} color="text-slate-500" />
          <StatCard label="Breached" value={baseFilteredServices.filter(r => r.status === 'BREACHED').length} color="text-red-400" />
          <StatCard label="Scan Time" value={`${scanTimeMs}ms`} color="text-cyan-400" />
        </div>
      )}

      {/* Category Tabs */}
      {scanResult && categories.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {categories.map(cat => {
            const cfg = CATEGORY_CONFIG[cat] || CATEGORY_CONFIG.OTHER
            const count = cat === 'ALL'
              ? baseFilteredServices.length
              : baseFilteredServices.filter(r => r.category === cat).length
            const isActive = activeCategory === cat

            return (
              <button
                key={cat}
                onClick={() => setActiveCategory(cat)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-200 border ${
                  isActive
                    ? 'bg-violet-600/20 border-violet-500/50 text-violet-300'
                    : 'bg-slate-800/50 border-slate-700/30 text-slate-400 hover:border-slate-600'
                }`}
              >
                {cfg.icon}
                {cfg.label}
                <span className={`ml-0.5 ${isActive ? 'text-violet-400' : 'text-slate-600'}`}>
                  {count}
                </span>
              </button>
            )
          })}
        </div>
      )}

      {/* Results Grid */}
      {scanResult && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {filteredResults.map((result, idx) => (
            <ServiceCard key={`${result.service}-${idx}`} result={result} />
          ))}
        </div>
      )}

      {/* Loading state */}
      {isScanning && !scanResult && (
        <div className="text-center py-12">
          <Loader2 className="w-8 h-8 text-violet-400 animate-spin mx-auto mb-3" />
          <p className="text-slate-400 text-sm">Scanning active accounts for {emailHint}...</p>
        </div>
      )}

      {error && (
        <div className="text-center py-8">
          <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-3" />
          <p className="text-red-300 text-sm">{error}</p>
        </div>
      )}
    </div>
  )
}

// ── Sub-components ──────────────────────────────────────────

function StatCard({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 text-center">
      <p className={`text-2xl font-bold tabular-nums ${color}`}>{value}</p>
      <p className="text-[10px] uppercase tracking-wider text-slate-500 mt-1 font-medium">{label}</p>
    </div>
  )
}

function ServiceCard({ result }: { result: ServiceResult }) {
  const statusCfg = STATUS_CONFIG[result.status] || STATUS_CONFIG.ERROR
  const catCfg = CATEGORY_CONFIG[result.category] || CATEGORY_CONFIG.OTHER
  const [expanded, setExpanded] = useState(false)

  const hasMetadata = result.metadata && Object.keys(result.metadata).length > 0

  return (
    <div className={`rounded-xl border p-4 transition-all duration-200 hover:scale-[1.01] ${statusCfg.bg}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={statusCfg.color}>{statusCfg.icon}</span>
            <span className="font-semibold text-sm text-white truncate">{result.service}</span>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="outline" className={`text-[10px] ${catCfg.color} border-current/20`}>
              {catCfg.label}
            </Badge>
            <span className={`text-[10px] font-medium ${statusCfg.color}`}>{statusCfg.label}</span>
            <span className="text-[10px] text-slate-600">{result.check_duration_ms}ms</span>
          </div>
        </div>

        {result.profile_url && (
          <a
            href={result.profile_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-slate-500 hover:text-violet-400 transition-colors flex-shrink-0 p-1"
            title="Open profile"
          >
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        )}
      </div>

      {result.profile_url && (
        <p className="text-[10px] text-slate-500 mt-2 truncate font-mono">{result.profile_url}</p>
      )}

      {hasMetadata && (
        <div className="mt-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-[10px] text-slate-500 hover:text-slate-300 flex items-center gap-1 transition-colors"
          >
            <ChevronDown className={`w-3 h-3 transition-transform ${expanded ? 'rotate-180' : ''}`} />
            {expanded ? 'Hide' : 'Show'} details
          </button>
          {expanded && (
            <div className="mt-2 space-y-1 text-[10px] text-slate-400 font-mono bg-black/20 rounded p-2">
              {Object.entries(result.metadata).map(([k, v]) => (
                <div key={k}>
                  <span className="text-slate-500">{k}:</span>{' '}
                  <span className="text-slate-300">{typeof v === 'object' ? JSON.stringify(v) : String(v)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
