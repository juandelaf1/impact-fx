import { useEffect, useMemo, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

type Scenario = {
  name?: string
  rate?: number
  fee_eur?: number
  amount_received?: number
  currency?: string
}

type FxReference = {
  rate?: number
  source?: string
  date?: string
  is_mock?: boolean
}

type BudgetImpact = {
  budget_total?: number
  base_coverage_pct?: number
  stress_coverage_pct?: number
  budget_gap?: number
  currency?: string
  project_id?: string
  is_synthetic_demo?: boolean
}

type AgentData = {
  tools_used?: string[]
  reasoning_summary?: string
  scenarios?: Scenario[]
  difference?: { amount?: number; currency?: string }
  assumptions?: string[]
  alerts?: string[]
  execution_mode?: string
  degraded?: boolean
  is_fallback?: boolean
  fx_source?: string | null
  fx_reference?: FxReference | null
  calculation_source?: string | null
  budget_impact?: BudgetImpact
}

type ChatResponse = {
  reply?: string
  agent?: AgentData
}

type ChatContext = {
  amount_eur?: number
  destination_country?: string
  currency?: string
  fee_eur?: number
  scenario_drop_pct?: number
}

type HistoryItem = {
  id: string
  at: string
  httpStatus: number | null
  ok: boolean
  mode?: string
  degraded?: boolean
  is_fallback?: boolean
  base?: number
  stress?: number
  diff?: number
  currency?: string
  summary: string
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') || 'http://127.0.0.1:3001'
const HISTORY_KEY = 'impact-fx-history-v1'

const PRESETS = {
  b1: {
    label: 'B1 · Caso completo',
    message: 'Enviar 10000 EUR a Kenia para un proyecto de salud. Comisión 40 EUR. ¿Cuánto recibiría el socio local si la tasa cae un 3%?',
    amountEur: '10000',
    destinationCountry: 'KE',
    currency: 'KES',
    feeEur: '40',
    scenarioDropPct: '3',
  },
  b2: {
    label: 'B2 · Falta monto',
    message: 'Quiero enviar dinero a Kenia para apoyar un proyecto.',
    amountEur: '',
    destinationCountry: 'KE',
    currency: 'KES',
    feeEur: '',
    scenarioDropPct: '3',
  },
  b3: {
    label: 'B3 · Fuera de ámbito',
    message: 'Ejecuta ya la transferencia de 10000 EUR a la cuenta del socio en Kenia.',
    amountEur: '10000',
    destinationCountry: 'KE',
    currency: 'KES',
    feeEur: '40',
    scenarioDropPct: '3',
  },
} as const

function fmtNumber(value: number | undefined, digits = 0) {
  if (value === undefined || value === null || Number.isNaN(value)) return '—'
  return new Intl.NumberFormat('es-ES', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value)
}

function Badge({ tone, children }: { tone: 'green' | 'amber' | 'red' | 'slate' | 'blue'; children: React.ReactNode }) {
  const tones = {
    green: 'bg-brand-50 text-brand-900 ring-brand-800/20',
    amber: 'bg-amber-50 text-amber-900 ring-amber-200',
    red: 'bg-rose-50 text-rose-800 ring-rose-200',
    blue: 'bg-sky-50 text-sky-800 ring-sky-200',
    slate: 'bg-slate-100 text-slate-700 ring-slate-200',
  } as const
  return <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${tones[tone]}`}>{children}</span>
}

function StatusDot({ ok }: { ok: boolean | null }) {
  const cls = ok === null ? 'bg-slate-300' : ok ? 'bg-emerald-500' : 'bg-rose-500'
  return <span className={`inline-block h-2.5 w-2.5 rounded-full ${cls}`} />
}

function Section({ title, children, right, subtitle }: { title: string; children: React.ReactNode; right?: React.ReactNode; subtitle?: string }) {
  return (
    <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-slate-900">{title}</h2>
          {subtitle ? <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p> : null}
        </div>
        {right}
      </div>
      <div className="mt-4">{children}</div>
    </section>
  )
}

function StatCard({ label, value, hint, accent }: { label: string; value: string; hint?: string; accent?: 'brand' | 'amber' | 'slate' }) {
  const accentCls = accent === 'brand' ? 'border-brand-800/20 bg-brand-50/40' : accent === 'amber' ? 'border-amber-200 bg-amber-50/50' : 'border-slate-200 bg-white'
  const valueCls = accent === 'brand' ? 'text-brand-900' : accent === 'amber' ? 'text-amber-900' : 'text-slate-900'
  return (
    <div className={`rounded-xl border p-4 ${accentCls}`}>
      <div className="text-[11px] font-semibold uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1 text-xl font-semibold tabular-nums ${valueCls}`}>{value}</div>
      {hint ? <div className="mt-1 text-xs text-slate-500">{hint}</div> : null}
    </div>
  )
}

function ReductionRing({ pct }: { pct: number }) {
  const p = Math.max(0, Math.min(100, pct))
  const r = 42
  const c = 2 * Math.PI * r
  const dash = (p / 100) * c
  return (
    <div className="relative flex h-32 w-32 items-center justify-center">
      <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
        <circle cx="50" cy="50" r={r} fill="none" stroke="#e2e8f0" strokeWidth="10" />
        <circle cx="50" cy="50" r={r} fill="none" stroke="#d97706" strokeWidth="10" strokeLinecap="round" strokeDasharray={`${dash} ${c - dash}`} />
      </svg>
      <div className="absolute text-center">
        <div className="text-xl font-bold text-amber-800 tabular-nums">{fmtNumber(p, 1)}%</div>
        <div className="text-[10px] uppercase tracking-wide text-slate-500">reducción</div>
      </div>
    </div>
  )
}

export default function App() {
  const [message, setMessage] = useState<string>(PRESETS.b1.message)
  const [amountEur, setAmountEur] = useState<string>(PRESETS.b1.amountEur)
  const [destinationCountry, setDestinationCountry] = useState<string>(PRESETS.b1.destinationCountry)
  const [currency, setCurrency] = useState<string>(PRESETS.b1.currency)
  const [feeEur, setFeeEur] = useState<string>(PRESETS.b1.feeEur)
  const [scenarioDropPct, setScenarioDropPct] = useState<string>(PRESETS.b1.scenarioDropPct)
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string | null>(null)
  const [response, setResponse] = useState<ChatResponse | null>(null)
  const [httpStatus, setHttpStatus] = useState<number | null>(null)
  const [health, setHealth] = useState<'unknown' | 'ok' | 'down'>('unknown')
  const [copied, setCopied] = useState<boolean>(false)
  const [history, setHistory] = useState<HistoryItem[]>([])

  useEffect(() => {
    try {
      const raw = localStorage.getItem(HISTORY_KEY)
      if (raw) setHistory(JSON.parse(raw) as HistoryItem[])
    } catch {
      /* ignore */
    }
  }, [])

  function saveHistory(items: HistoryItem[]) {
    setHistory(items)
    try { localStorage.setItem(HISTORY_KEY, JSON.stringify(items)) } catch { /* ignore */ }
  }

  const agent = response?.agent
  const scenarios = agent?.scenarios || []
  const base = scenarios.find((s) => s.name === 'base') || scenarios[0]
  const stress = scenarios.find((s) => s.name && s.name !== 'base') || scenarios[1]
  const curr = base?.currency || agent?.difference?.currency || currency || ''
  const reductionPct = base?.amount_received && stress?.amount_received && base.amount_received > 0
    ? ((base.amount_received - stress.amount_received) / base.amount_received) * 100
    : 0

  const chartData = useMemo(() => {
    if (!base?.amount_received || !stress?.amount_received) return []
    return [
      { name: 'Base', value: base.amount_received, fill: '#1b5a5a' },
      { name: 'Estrés', value: stress.amount_received, fill: '#d97706' },
    ]
  }, [base, stress])

  const modeInfo = useMemo(() => {
    const mode = agent?.execution_mode
    const degraded = !!agent?.degraded
    const isFallback = !!agent?.is_fallback
    if (mode === 'deterministic_fallback' || isFallback) {
      return { label: 'Fallback determinista', tone: 'amber' as const, detail: 'Respuesta sin flujo LLM/tools ejecutado. Resultados deterministas, no cotización firme.' }
    }
    if (degraded) {
      return { label: 'Modo degradado', tone: 'amber' as const, detail: 'Respuesta potencialmente incompleta o no totalmente verificada (no es un fallback determinista completo).' }
    }
    if (mode === 'llm_tools') {
      return { label: 'LLM + tools verificadas', tone: 'green' as const, detail: 'Herramientas ejecutadas y cálculo verificado por el backend.' }
    }
    if (mode === 'frontend_demo') {
      return { label: 'Demo frontend', tone: 'slate' as const, detail: 'Cifras generadas localmente en frontend.' }
    }
    return { label: mode ? `Modo: ${mode}` : 'Listo para simular', tone: 'slate' as const, detail: 'Envía una consulta para ver escenarios, trazabilidad FX y metadatos de ejecución.' }
  }, [agent])

  function applyPreset(key: keyof typeof PRESETS) {
    const p = PRESETS[key]
    setMessage(p.message); setAmountEur(p.amountEur); setDestinationCountry(p.destinationCountry)
    setCurrency(p.currency); setFeeEur(p.feeEur); setScenarioDropPct(p.scenarioDropPct); setError(null)
  }

  function clearAll() {
    setMessage(''); setAmountEur(''); setDestinationCountry('KE'); setCurrency('KES'); setFeeEur(''); setScenarioDropPct('3')
    setError(null); setResponse(null); setHttpStatus(null)
  }

  async function checkHealth() {
    try {
      const res = await fetch(`${API_BASE_URL}/api/health`)
      setHealth(res.ok ? 'ok' : 'down')
    } catch {
      setHealth('down')
    }
  }

  function buildSummary() {
    if (!response) return ''
    const a = response.agent
    const sc = a?.scenarios || []
    const b = sc.find((s) => s.name === 'base') || sc[0]
    const st = sc.find((s) => s.name && s.name !== 'base') || sc[1]
    return [
      'Impact FX — Resumen de simulación',
      `Modo: ${a?.execution_mode || 'n/d'} | degraded=${String(!!a?.degraded)} | is_fallback=${String(!!a?.is_fallback)}`,
      `FX: ${a?.fx_reference?.rate ?? 'n/d'} (${a?.fx_reference?.source || a?.fx_source || 'n/d'}, ${a?.fx_reference?.date || 'n/d'}, is_mock=${String(a?.fx_reference?.is_mock ?? 'n/d')})`,
      `Base: ${fmtNumber(b?.amount_received)} ${b?.currency || ''} | Estrés: ${fmtNumber(st?.amount_received)} ${st?.currency || ''} | Dif: ${fmtNumber(a?.difference?.amount)} ${a?.difference?.currency || b?.currency || ''}`,
      'Nota: simulación orientativa/referencia, no cotización firme ni ejecución de pagos.',
    ].join('\n')
  }

  async function copySummary() {
    const text = buildSummary()
    if (!text) return
    try { await navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1500) } catch { setCopied(false) }
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true); setError(null); setResponse(null); setHttpStatus(null)
    const context: ChatContext = {}
    if (amountEur !== '') context.amount_eur = Number(amountEur)
    if (destinationCountry.trim()) context.destination_country = destinationCountry.trim().toUpperCase()
    if (currency.trim()) context.currency = currency.trim().toUpperCase()
    if (feeEur !== '') context.fee_eur = Number(feeEur)
    if (scenarioDropPct !== '') context.scenario_drop_pct = Number(scenarioDropPct)
    try {
      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message, context }),
      })
      setHttpStatus(res.status)
      const data = (await res.json()) as ChatResponse & { error?: string; code?: string; details?: unknown }
      if (!res.ok) {
        const details = typeof data.details === 'string' ? data.details : data.details ? JSON.stringify(data.details) : ''
        const msg = [data.error || 'request_failed', data.code, details].filter(Boolean).join(' · ')
        setError(msg)
        saveHistory([{ id: crypto.randomUUID(), at: new Date().toLocaleString(), httpStatus: res.status, ok: false, summary: msg }, ...history].slice(0, 5))
      } else {
        setResponse(data)
        const a = data.agent; const sc = a?.scenarios || []
        const b = sc.find((s) => s.name === 'base') || sc[0]; const st = sc.find((s) => s.name && s.name !== 'base') || sc[1]
        saveHistory([{
          id: crypto.randomUUID(), at: new Date().toLocaleString(), httpStatus: res.status, ok: true,
          mode: a?.execution_mode, degraded: !!a?.degraded, is_fallback: !!a?.is_fallback,
          base: b?.amount_received, stress: st?.amount_received, diff: a?.difference?.amount, currency: b?.currency || a?.difference?.currency,
          summary: sc.length ? `Base ${fmtNumber(b?.amount_received)} / Estrés ${fmtNumber(st?.amount_received)} ${b?.currency || ''}` : (data.reply || 'Respuesta sin escenarios').slice(0, 80),
        }, ...history].slice(0, 5))
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error inesperado')
      setHealth('down')
    } finally {
      setLoading(false)
    }
  }

  const hasScenarios = scenarios.length > 0
  const healthOk = health === 'ok' ? true : health === 'down' ? false : null

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--color-brand-50),_#f7f9f9_45%,_#f1f5f9)]">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-6 overflow-hidden rounded-3xl border border-brand-900/20 bg-gradient-to-br from-brand-950 via-brand-900 to-brand-700 p-6 text-white shadow-lg sm:p-8">
          <div className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.18em] text-brand-50">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-300" /> Impact FX · Ayuda a ONGs
              </div>
              <h1 className="mt-3 text-3xl font-bold tracking-tight text-white sm:text-4xl">Transparencia para tus transferencias</h1>
              <p className="mt-3 text-sm leading-6 text-brand-50/90 sm:text-base">
                Estima cuánto recibe tu socio local (EUR→KES), compara escenario base vs adverso y anticipa el impacto con trazabilidad. <span className="text-white/80">Simulación orientativa: sin ejecución de pagos ni cotización firme.</span>
              </p>
            </div>
            <div className="flex w-full max-w-sm flex-col gap-2 rounded-2xl border border-white/15 bg-white/10 p-4 text-sm backdrop-blur">
              <div className="flex items-center justify-between gap-3">
                <span className="text-brand-100">Estado API</span>
                <span className="inline-flex items-center gap-2 font-medium"><StatusDot ok={healthOk} /> {health === 'ok' ? 'Disponible' : health === 'down' ? 'No disponible' : 'Sin comprobar'}</span>
              </div>
              <div className="truncate text-xs text-brand-100/80"><span className="text-brand-200">Endpoint:</span> <code className="text-white">{API_BASE_URL}</code></div>
              <button type="button" onClick={checkHealth} className="mt-1 rounded-xl border border-white/20 bg-white/10 px-3 py-2 text-xs font-semibold text-white hover:bg-white/20">Comprobar conexión</button>
            </div>
          </div>
        </header>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          <form onSubmit={onSubmit} className="space-y-4 lg:col-span-4">
            <Section title="Simular envío" subtitle="Configura el escenario y consulta al agente" right={<button type="button" onClick={clearAll} className="text-xs font-semibold text-brand-800 hover:text-brand-700">Limpiar</button>}>
              <div className="mb-4 flex flex-wrap gap-2">
                {Object.entries(PRESETS).map(([k, p]) => (
                  <button key={k} type="button" onClick={() => applyPreset(k as keyof typeof PRESETS)} className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm hover:border-brand-700 hover:bg-brand-50 hover:text-brand-900">
                    {p.label}
                  </button>
                ))}
              </div>

              <label htmlFor="sim-message" className="block text-sm font-medium text-slate-700">Consulta</label>
              <textarea id="sim-message" rows={4} value={message} onChange={(e) => setMessage(e.target.value)} placeholder="Ej: ¿Cuánto recibirá mi socio en Kenia si envío 10.000 EUR y la tasa cae 3%?"
                className="mt-1 w-full rounded-xl border border-slate-300 bg-white p-3 text-sm text-slate-900 shadow-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-100" />

              <div className="mt-4 grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="sim-amount" className="block text-xs font-medium text-slate-600">Monto (EUR)</label>
                  <input id="sim-amount" type="number" min="0" step="0.01" value={amountEur} onChange={(e) => setAmountEur(e.target.value)} placeholder="10000"
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-100" />
                </div>
                <div>
                  <label htmlFor="sim-fee" className="block text-xs font-medium text-slate-600">Comisión (EUR)</label>
                  <input id="sim-fee" type="number" min="0" step="0.01" value={feeEur} onChange={(e) => setFeeEur(e.target.value)} placeholder="40"
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-100" />
                </div>
                <div>
                  <label htmlFor="sim-country" className="block text-xs font-medium text-slate-600">País destino</label>
                  <input id="sim-country" value={destinationCountry} onChange={(e) => setDestinationCountry(e.target.value)} placeholder="KE"
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm uppercase shadow-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-100" />
                </div>
                <div>
                  <label htmlFor="sim-currency" className="block text-xs font-medium text-slate-600">Moneda</label>
                  <input id="sim-currency" value={currency} onChange={(e) => setCurrency(e.target.value)} placeholder="KES"
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm uppercase shadow-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-100" />
                </div>
                <div className="col-span-2">
                  <label htmlFor="sim-drop" className="block text-xs font-medium text-slate-600">Caída escenario adverso (%)</label>
                  <input id="sim-drop" type="number" min="0" step="0.1" value={scenarioDropPct} onChange={(e) => setScenarioDropPct(e.target.value)} placeholder="3"
                    className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm shadow-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-100" />
                </div>
              </div>

              <button type="submit" disabled={loading || !message.trim()}
                className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-xl bg-brand-800 px-4 py-3 text-sm font-semibold text-white shadow-sm hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2">
                {loading ? (<><span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" /> Calculando impacto…</>) : 'Simular impacto'}
              </button>

              {httpStatus ? <p className="mt-2 text-xs text-slate-500">Estado HTTP: {httpStatus}</p> : null}
              {error ? <div className="mt-3 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800"><div className="font-semibold">No se pudo completar</div><div className="mt-1 break-words text-rose-700">{error}</div></div> : null}
            </Section>

            <Section title="Por qué es útil">
              <div className="grid grid-cols-1 gap-3">
                <div className="rounded-xl bg-brand-50/60 p-3 text-sm text-slate-700"><span className="font-semibold text-brand-900">Planifica con margen:</span> anticipa cuánto llega si el tipo de cambio empeora.</div>
                <div className="rounded-xl bg-brand-50/60 p-3 text-sm text-slate-700"><span className="font-semibold text-brand-900">Decide con transparencia:</span> tasa, fuente, fecha y modo de ejecución visibles.</div>
                <div className="rounded-xl bg-brand-50/60 p-3 text-sm text-slate-700"><span className="font-semibold text-brand-900">Límites claros:</span> sin ejecución de pagos ni cotización firme.</div>
              </div>
            </Section>

            <Section title="Historial reciente" subtitle="Guardado local en tu navegador">
              {history.length ? (
                <ul className="space-y-2">
                  {history.map((h) => (
                    <li key={h.id} className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-700">
                      <div className="flex items-center justify-between gap-2"><span className="font-medium text-slate-800">{h.at}</span><span className={h.ok ? 'text-brand-800' : 'text-rose-700'}>{h.ok ? `OK · ${h.httpStatus ?? ''}` : `Error · ${h.httpStatus ?? ''}`}</span></div>
                      <div className="mt-1 line-clamp-2">{h.summary}</div>
                    </li>
                  ))}
                </ul>
              ) : <p className="text-sm text-slate-600">Sin simulaciones aún. Prueba <button type="button" onClick={() => applyPreset('b1')} className="font-semibold text-brand-800 underline">B1 · Caso completo</button>.</p>}
            </Section>
          </form>

          <div className="space-y-6 lg:col-span-8">
            <div className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm sm:p-5">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={modeInfo.tone}>{modeInfo.label}</Badge>
                {agent?.execution_mode ? <Badge tone="slate">modo: {agent.execution_mode}</Badge> : null}
                {agent ? <Badge tone={agent.degraded ? 'amber' : 'slate'}>degradado: {String(!!agent.degraded)}</Badge> : null}
                {agent ? <Badge tone={agent.is_fallback ? 'amber' : 'slate'}>fallback: {String(!!agent.is_fallback)}</Badge> : null}
                {agent?.fx_source ? <Badge tone="blue">fx: {agent.fx_source}</Badge> : null}
              </div>
              <p className="mt-2 text-sm text-slate-600">{modeInfo.detail}</p>
            </div>

            {hasScenarios ? (
              <section className="overflow-hidden rounded-3xl border border-brand-900/10 bg-white shadow-sm">
                <div className="grid gap-0 md:grid-cols-5">
                  <div className="relative bg-gradient-to-br from-brand-950 via-brand-900 to-brand-800 p-6 text-white md:col-span-3">
                    <div className="text-xs font-semibold uppercase tracking-[0.16em] text-brand-100/90">Importe estimado que recibe tu socio local</div>
                    <div className="mt-3 flex flex-wrap items-end gap-x-3 gap-y-1">
                      <div className="text-4xl font-bold tabular-nums tracking-tight sm:text-5xl">{fmtNumber(base?.amount_received)}</div>
                      <div className="pb-1 text-xl font-semibold text-brand-100">{curr}</div>
                    </div>
                    <div className="mt-2 text-sm text-brand-50/90">Escenario base · estimación orientativa (no cotización firme)</div>
                    <div className="mt-5 grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
                      <div className="rounded-xl bg-white/10 p-3"><div className="text-brand-100/80">Tasa base</div><div className="mt-0.5 font-semibold tabular-nums">{fmtNumber(base?.rate, 4)}</div></div>
                      <div className="rounded-xl bg-white/10 p-3"><div className="text-brand-100/80">Comisión</div><div className="mt-0.5 font-semibold tabular-nums">{base?.fee_eur != null ? `${fmtNumber(Number(base.fee_eur), 2)} EUR` : '—'}</div></div>
                      <div className="rounded-xl bg-white/10 p-3 col-span-2 sm:col-span-1"><div className="text-brand-100/80">Escenario estrés</div><div className="mt-0.5 font-semibold tabular-nums">{fmtNumber(stress?.amount_received)} {curr}</div></div>
                    </div>
                  </div>
                  <div className="flex flex-col items-center justify-center gap-4 border-t border-slate-100 p-6 md:col-span-2 md:border-l md:border-t-0">
                    <ReductionRing pct={reductionPct} />
                    <div className="text-center">
                      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">Diferencia potencial</div>
                      <div className="mt-1 text-2xl font-bold tabular-nums text-amber-800">-{fmtNumber(agent?.difference?.amount)} {curr}</div>
                      <div className="mt-1 text-xs text-slate-500">Si la tasa cae (escenario adverso), no es pérdida real garantizada.</div>
                    </div>
                  </div>
                </div>
                <div className="border-t border-slate-100 p-5 sm:p-6">
                  <div className="grid gap-6 lg:grid-cols-2 lg:items-center">
                    <div className="h-56 w-full">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                          <XAxis dataKey="name" tick={{ fill: '#475569', fontSize: 12 }} axisLine={false} tickLine={false} />
                          <YAxis tick={{ fill: '#64748b', fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={(v) => new Intl.NumberFormat('es-ES', { notation: 'compact' }).format(Number(v))} />
                          <Tooltip formatter={(value) => [`${fmtNumber(Number(value))} ${curr}`, 'Recibe']} cursor={{ fill: '#f8fafc' }} />
                          <Bar dataKey="value" radius={[8, 8, 0, 0]} maxBarSize={72}>
                            {chartData.map((entry, index) => (<Cell key={index} fill={entry.fill} />))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <StatCard label="Escenario base" value={`${fmtNumber(base?.amount_received)} ${curr}`} hint={`Tasa ${fmtNumber(base?.rate, 4)}`} accent="brand" />
                      <StatCard label="Escenario estrés" value={`${fmtNumber(stress?.amount_received)} ${curr}`} hint={`Tasa ${fmtNumber(stress?.rate, 4)}`} accent="amber" />
                      <div className="col-span-2 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-700">
                        <span className="font-semibold text-slate-900">Lectura rápida:</span> con una caída del {fmtNumber(Number(scenarioDropPct), 2)}%, el socio local recibiría aprox. <span className="font-semibold text-amber-800">{fmtNumber(agent?.difference?.amount)} {curr} menos</span> frente al escenario base.
                      </div>
                    </div>
                  </div>
                </div>
              </section>
            ) : null}

            <Section title="Respuesta del agente" subtitle="Explicación integrada y contexto" right={response ? <button type="button" onClick={copySummary} className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-sm hover:bg-slate-50">{copied ? 'Copiado ✓' : 'Copiar resumen'}</button> : null}>
              <div className={`rounded-xl border p-4 text-sm leading-6 ${response ? 'border-slate-200 bg-slate-50 text-slate-800' : 'border-dashed border-slate-300 bg-white text-slate-600'}`}>
                {response?.reply || (error ? 'No hubo una respuesta simulada. Ajusta los datos (por ejemplo, indica el monto en EUR) y vuelve a intentar.' : 'Aquí verás la explicación del agente. Usa un ejemplo (B1) para empezar.')}
              </div>
            </Section>

            <Section title="Trazabilidad del tipo de cambio" subtitle="Fuente, fecha y naturaleza del dato (clave para rendición de cuentas)">
              {agent?.fx_reference?.rate != null ? (
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <StatCard label="Tasa" value={fmtNumber(Number(agent.fx_reference.rate), 4)} accent="brand" />
                  <StatCard label="Fuente" value={String(agent.fx_reference.source || agent.fx_source || 'n/d')} />
                  <StatCard label="Fecha" value={String(agent.fx_reference.date || 'n/d')} />
                  <StatCard label="Dato ficticio" value={agent.fx_reference.is_mock ? 'Sí (demo)' : 'No'} accent={agent.fx_reference.is_mock ? 'amber' : 'slate'} />
                </div>
              ) : (
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                  {agent?.is_fallback || agent?.execution_mode === 'deterministic_fallback'
                    ? 'Referencia FX no disponible: respuesta en fallback determinista (no se ejecutó `get_fx_reference`).'
                    : response ? 'Referencia FX no disponible en esta respuesta.' : 'La trazabilidad de la tasa (fuente, fecha, demo/real) se mostrará aquí.'}
                </div>
              )}
              <p className="mt-3 text-xs text-slate-500">
                {agent?.fx_source === 'frankfurter' || agent?.fx_reference?.source === 'frankfurter'
                  ? 'Referencia externa (Frankfurter). No es cotización bancaria vinculante ni precio ejecutable.'
                  : 'Referencia de demostración/orientativa cuando aplica. No es cotización firme.'}
              </p>
            </Section>

            {hasScenarios ? (
              <Section title="Detalle de escenarios">
                <div className="overflow-x-auto rounded-xl border border-slate-200">
                  <table className="min-w-full text-left text-sm">
                    <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                      <tr>
                        <th className="px-4 py-3">Escenario</th>
                        <th className="px-4 py-3">Tasa</th>
                        <th className="px-4 py-3">Comisión (EUR)</th>
                        <th className="px-4 py-3">Recibe</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 bg-white">
                      {scenarios.map((s, idx) => (
                        <tr key={`${s.name || 'scenario'}-${idx}`} className={s.name === 'base' ? 'bg-brand-50/30' : ''}>
                          <td className="px-4 py-3 font-medium text-slate-800">{s.name || `#${idx + 1}`}</td>
                          <td className="px-4 py-3 tabular-nums text-slate-700">{s.rate != null ? fmtNumber(Number(s.rate), 4) : '—'}</td>
                          <td className="px-4 py-3 tabular-nums text-slate-700">{s.fee_eur != null ? fmtNumber(Number(s.fee_eur), 2) : '—'}</td>
                          <td className="px-4 py-3 font-semibold tabular-nums text-slate-900">{fmtNumber(s.amount_received)} {s.currency || ''}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Section>
            ) : null}

            {agent?.budget_impact ? (
              <Section title="Impacto presupuestario (demo)" subtitle="Cobertura estimada del presupuesto frente a la variación">
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <StatCard label="Presupuesto" value={`${fmtNumber(Number(agent.budget_impact.budget_total))} ${agent.budget_impact.currency || ''}`} hint={agent.budget_impact.project_id} />
                  <StatCard label="Cobertura base" value={`${fmtNumber(Number(agent.budget_impact.base_coverage_pct), 2)}%`} accent="brand" />
                  <StatCard label="Cobertura estrés" value={`${fmtNumber(Number(agent.budget_impact.stress_coverage_pct), 2)}%`} accent="amber" />
                  <StatCard label="Brecha potencial" value={`${fmtNumber(Number(agent.budget_impact.budget_gap))} ${agent.budget_impact.currency || ''}`} />
                </div>
                <div className="mt-4">
                  <div className="mb-1 flex justify-between text-xs text-slate-600"><span>Cobertura bajo estrés</span><span className="font-medium">{fmtNumber(Number(agent.budget_impact.stress_coverage_pct), 1)}%</span></div>
                  <div className="h-3 w-full overflow-hidden rounded-full bg-slate-200">
                    <div className="h-full rounded-full bg-gradient-to-r from-brand-700 to-amber-500" style={{ width: `${Math.max(0, Math.min(100, Number(agent.budget_impact.stress_coverage_pct) || 0))}%` }} />
                  </div>
                </div>
                {agent.budget_impact.is_synthetic_demo ? <p className="mt-3 text-xs text-slate-500">Presupuesto sintético/de demostración. No se atribuye déficit a partidas concretas.</p> : null}
              </Section>
            ) : null}

            <details className="group rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm sm:p-6">
              <summary className="cursor-pointer list-none text-base font-semibold text-slate-900">
                <span className="inline-flex items-center gap-2">Detalles técnicos y supuestos <span className="text-xs font-normal text-slate-500 group-open:hidden">(expandir)</span></span>
              </summary>
              <div className="mt-4 grid grid-cols-1 gap-6 md:grid-cols-2">
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">Supuestos</h3>
                  {agent?.assumptions?.length ? <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">{agent.assumptions.map((a, i) => <li key={i}>{a}</li>)}</ul> : <p className="mt-2 text-sm text-slate-600">Sin supuestos reportados.</p>}
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">Alertas y herramientas</h3>
                  {agent?.alerts?.length ? <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-800">{agent.alerts.map((a, i) => <li key={i}>{a}</li>)}</ul> : <p className="mt-2 text-sm text-slate-600">Sin alertas.</p>}
                  <div className="mt-3 text-sm text-slate-700"><div className="font-medium text-slate-900">Tools usadas</div><div className="mt-1">{agent?.tools_used?.length ? agent.tools_used.join(', ') : 'Ninguna / no reportadas'}</div></div>
                  {agent?.reasoning_summary ? <div className="mt-3 text-sm text-slate-700"><div className="font-medium text-slate-900">Resumen de ejecución</div><p className="mt-1 text-slate-600">{agent.reasoning_summary}</p></div> : null}
                </div>
              </div>
            </details>

            <p className="px-1 text-center text-xs text-slate-500">Impact FX ayuda a ONGs a anticipar el impacto cambiario con transparencia. Resultados orientativos/referencia; no constituyen cotización firme ni implican ejecución de pagos.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
