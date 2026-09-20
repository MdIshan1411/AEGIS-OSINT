import { useState, useRef, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import axios from 'axios'
import type { EmailScanResponse, ServiceResult } from '@/types/email-scanner'
import {
  Search, Shield, ShieldAlert, ShieldCheck, ExternalLink,
  Mail, Clock, Activity, Globe, Gamepad2, Code, Briefcase,
  ShoppingCart, MonitorPlay, Loader2, Terminal, CheckCircle2,
  XCircle, AlertTriangle, ChevronDown
} from 'lucide-react'

const CATEGORY_CONFIG: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  ALL:          { label: 'All',            icon: <Globe className="w-4 h-4" />,        color: 'text-slate-300' },
  DEV:          { label: 'Developer',      icon: <Code className="w-4 h-4" />,         color: 'text-blue-400' },
  SOCIAL:       { label: 'Social',         icon: <Globe className="w-4 h-4" />,        color: 'text-purple-400' },
  PROFESSIONAL: { label: 'Professional',   icon: <Briefcase className="w-4 h-4" />,    color: 'text-cyan-400' },
  GAMING:       { label: 'Gaming',         icon: <Gamepad2 className="w-4 h-4" />,     color: 'text-green-400' },
  EMAIL:        { label: 'Email',          icon: <Mail className="w-4 h-4" />,          color: 'text-yellow-400' },
  SECURITY:     { label: 'Security',       icon: <Shield className="w-4 h-4" />,       color: 'text-red-400' },
  MEDIA:        { label: 'Media',          icon: <MonitorPlay className="w-4 h-4" />,  color: 'text-pink-400' },
  ECOMMERCE:    { label: 'E-Commerce',     icon: <ShoppingCart className="w-4 h-4" />, color: 'text-orange-400' },
  OTHER:        { label: 'Other',          icon: <Activity className="w-4 h-4" />,     color: 'text-slate-400' },
}

const STATUS_CONFIG: Record<string, { icon: React.ReactNode; color: string; bg: string; label: string }> = {
  REGISTERED:     { icon: <CheckCircle2 className="w-4 h-4" />, color: 'text-green-400',  bg: 'bg-green-500/10 border-green-500/30',  label: 'Found' },
  BREACHED:       { icon: <ShieldAlert className="w-4 h-4" />,  color: 'text-red-400',    bg: 'bg-red-500/10 border-red-500/30',      label: 'Breached' },
  SAFE:           { icon: <ShieldCheck className="w-4 h-4" />,  color: 'text-emerald-400', bg: 'bg-emerald-500/10 border-emerald-500/30', label: 'Safe' },
  NOT_REGISTERED: { icon: <XCircle className="w-4 h-4" />,      color: 'text-slate-500',  bg: 'bg-slate-800/50 border-slate-700/30',  label: 'Not Found' },
  ERROR:          { icon: <AlertTriangle className="w-4 h-4" />, color: 'text-yellow-400', bg: 'bg-yellow-500/10 border-yellow-500/30', label: 'Error' },
  TIMEOUT:        { icon: <Clock className="w-4 h-4" />,        color: 'text-orange-400', bg: 'bg-orange-500/10 border-orange-500/30', label: 'Timeout' },
}

interface EmailScannerProps {
  onBack?: () => void
}

export function EmailScanner({ onBack }: EmailScannerProps) {
  const [email, setEmail] = useState('')
  const [isScanning, setIsScanning] = useState(false)
  const [scanResult, setScanResult] = useState<EmailScanResponse | null>(null)
  const [activeCategory, setActiveCategory] = useState('ALL')
  const [terminalLines, setTerminalLines] = useState<string[]>([])
  const [scanProgress, setScanProgress] = useState(0)
  const [scanTimeMs, setScanTimeMs] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const terminalRef = useRef<HTMLDivElement>(null)
  const startTimeRef = useRef<number>(0)

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [terminalLines])

  const simulateTerminalOutput = (results: ServiceResult[], elapsedMs?: number) => {
    const lines: string[] = []
    lines.push(`[TRACE-X] Email Footprint Scanner v2.0`)
    lines.push(`[SCAN] Target: ${email}`)
    lines.push(`[INIT] Loading ${results.length} service providers...`)
    lines.push(`[START] Scanning across all providers...`)
    lines.push(``)

    let idx = 0
    const interval = setInterval(() => {
      if (idx >= results.length) {
        clearInterval(interval)
        const registered = results.filter(r => r.status === 'REGISTERED' || r.status === 'BREACHED').length
        lines.push(``)
        lines.push(`[DONE] Scan complete in ${elapsedMs ?? 0}ms.`)
        lines.push(`[RESULT] ${registered}/${results.length} services matched.`)
        setTerminalLines([...lines])
        return
      }

      const r = results[idx]
      const statusIcon = r.status === 'REGISTERED' ? '✓' : r.status === 'BREACHED' ? '⚠' : r.status === 'NOT_REGISTERED' ? '✗' : '?'
      const pad = r.service.padEnd(22)
      lines.push(`  [${statusIcon}] ${pad} ${r.status.padEnd(16)} ${r.check_duration_ms}ms`)
      setTerminalLines([...lines])
      setScanProgress(Math.round(((idx + 1) / results.length) * 100))
      idx++
    }, 35)
  }

  const handleScan = async () => {
    if (!email.trim()) return
    setIsScanning(true)
    setScanResult(null)
    setError(null)
    setTerminalLines([])
    setScanProgress(0)
    setScanTimeMs(0)
    setActiveCategory('ALL')
    startTimeRef.current = performance.now()

    try {
      const res = await axios.post<EmailScanResponse>('/api/email-scanner/scan', { email: email.trim() })
      const elapsed = Math.round(performance.now() - startTimeRef.current)
      setScanTimeMs(elapsed)
      setScanResult(res.data)
      simulateTerminalOutput(res.data.results, elapsed)
    } catch (err: any) {
      const elapsed = Math.round(performance.now() - startTimeRef.current)
      setScanTimeMs(elapsed)
      const msg = err?.response?.data?.detail || 'Scan failed. Please try again.'
      setError(msg)
      setTerminalLines(prev => [...prev, `[ERROR] ${msg}`])
    } finally {
      setIsScanning(false)
    }
  }

  const filteredResults = scanResult?.results?.filter(r =>
    activeCategory === 'ALL' || r.category === activeCategory
  ) ?? []

  const categories = scanResult
    ? ['ALL', ...new Set(scanResult.results.map(r => r.category))]
    : []

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Hero Section */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-3 mb-4">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center shadow-lg shadow-violet-500/25">
            <Mail className="w-6 h-6 text-white" />
          </div>
          <div className="text-left">
            <h2 className="text-2xl font-bold bg-gradient-to-r from-violet-400 via-fuchsia-300 to-pink-400 bg-clip-text text-transparent">
              Email Footprint Scanner
            </h2>
            <p className="text-xs text-slate-500 uppercase tracking-wider font-medium">
              55+ Services • Deterministic • Real-time
            </p>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <div className="max-w-2xl mx-auto">
        <div className={`relative group transition-all duration-300 ${isScanning ? 'scale-[1.01]' : ''}`}>
          <div className="absolute -inset-0.5 bg-gradient-to-r from-violet-500 via-fuchsia-500 to-pink-500 rounded-xl opacity-30 group-hover:opacity-50 blur transition-opacity duration-300" />
          <div className="relative flex items-center bg-slate-900 rounded-xl border border-slate-700/50 overflow-hidden">
            <div className="pl-4 text-slate-500">
              <Search className="w-5 h-5" />
            </div>
            <input
              id="email-scanner-input"
              type="email"
              value={email}
              onChange={e => setEmail(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && !isScanning && handleScan()}
              placeholder="Enter email address to scan..."
              className="flex-1 bg-transparent text-white px-4 py-4 text-lg outline-none placeholder-slate-600 font-mono"
              disabled={isScanning}
            />
            <button
              id="email-scanner-submit"
              onClick={handleScan}
              disabled={isScanning || !email.trim()}
              className="m-2 px-6 py-2.5 bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white font-semibold rounded-lg hover:from-violet-500 hover:to-fuchsia-500 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200 flex items-center gap-2 text-sm"
            >
              {isScanning ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Scanning...
                </>
              ) : (
                <>
                  <Shield className="w-4 h-4" />
                  Scan
                </>
              )}
            </button>
          </div>
        </div>
        {error && (
          <p className="mt-2 text-sm text-red-400 text-center">{error}</p>
        )}
      </div>

      {/* Terminal + Progress */}
      {terminalLines.length > 0 && (
        <Card className="border-slate-800 bg-slate-950 max-w-4xl mx-auto overflow-hidden">
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
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 max-w-4xl mx-auto animate-in fade-in duration-500">
          <StatCard label="Services Checked" value={scanResult.total_services} color="text-slate-300" />
          <StatCard label="Registered" value={scanResult.registered_count} color="text-green-400" />
          <StatCard label="Not Found" value={scanResult.not_registered_count} color="text-slate-500" />
          <StatCard label="Breached" value={scanResult.breached_count} color="text-red-400" />
          <StatCard label="Scan Time" value={`${scanTimeMs}ms`} color="text-cyan-400" />
        </div>
      )}

      {/* Category Tabs */}
      {scanResult && categories.length > 0 && (
        <div className="flex flex-wrap gap-2 justify-center max-w-4xl mx-auto">
          {categories.map(cat => {
            const cfg = CATEGORY_CONFIG[cat] || CATEGORY_CONFIG.OTHER
            const count = cat === 'ALL'
              ? scanResult.results.length
              : scanResult.results.filter(r => r.category === cat).length
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
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 max-w-5xl mx-auto animate-in fade-in slide-in-from-bottom-2 duration-500">
          {filteredResults.map((result, idx) => (
            <ServiceCard key={`${result.service}-${idx}`} result={result} />
          ))}
        </div>
      )}

      {/* Empty state */}
      {!scanResult && !isScanning && terminalLines.length === 0 && (
        <div className="text-center py-16 space-y-4">
          <div className="w-20 h-20 mx-auto rounded-2xl bg-gradient-to-br from-violet-500/10 to-fuchsia-500/10 border border-violet-500/20 flex items-center justify-center">
            <Search className="w-8 h-8 text-violet-400/50" />
          </div>
          <p className="text-slate-500 text-sm max-w-md mx-auto">
            Enter an email address above to discover its digital footprint across 55+ online services, including developer platforms, social media, gaming networks, and security databases.
          </p>
          <div className="flex flex-wrap gap-2 justify-center mt-6">
            {['test@gmail.com', 'developer@proton.me', 'user@outlook.com'].map(demo => (
              <button
                key={demo}
                onClick={() => setEmail(demo)}
                className="text-xs px-3 py-1.5 rounded-full bg-slate-800/50 border border-slate-700/30 text-slate-400 hover:text-violet-300 hover:border-violet-500/30 transition-all"
              >
                {demo}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ─── Sub-components ──────────────────────────────────────────

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

      {/* Profile URL */}
      {result.profile_url && (
        <p className="text-[10px] text-slate-500 mt-2 truncate font-mono">{result.profile_url}</p>
      )}

      {/* Expandable metadata */}
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
