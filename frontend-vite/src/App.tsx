import { useEffect, useMemo, useState } from 'react'

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

function Badge({ tone, children }: { tone: 'green' | 'amber' | 'red' | 'slate' | 'blue'; children: string }) {
  const tones = {
    green: 'bg-brand-50 text-brand-900 ring-brand-800/20',
    amber: 'bg-amber-50 text-amber-900 ring-amber-200',
    red: 'bg-rose-50 text-rose-800 ring-rose-200',
    blue: 'bg-sky-50 text-sky-800 ring-sky-200',
    slate: 'bg-slate-100 text-slate-700 ring-slate-200',
  } as const
  return <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${tones[tone]}`}>{children}</span>
}

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</div>
      <div className="mt-1 text-xl font-semibold text-slate-900">{value}</div>
      {hint ? <div className="mt-1 text-xs text-slate-500">{hint}</div> : null}
    </div>
  )
}

function Section({ title, children, right }: { title: string; children: React.ReactNode; right?: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <h2 className="text-base font-semibold text-slate-900">{title}</h2>
        {right}
      </div>
      <div className="mt-4">{children}</div>
    </section>
  )
}

function ComparisonBars({ base, stress, currency }: { base?: number; stress?: number; currency?: string }) {
  if (!base || !stress || base <= 0) return null
  const stressPct = Math.max(0, Math.min(100, (stress / base) * 100))
  const diffPct = Math.max(0, 100 - stressPct)
  const curr = currency || ''
  return (
    <div className="mt-4 space-y-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
      <div>
        <div className="mb-1 flex items-center justify-between text-xs text-slate-600"><span>Base</span><span className="font-medium text-slate-800">{fmtNumber(base)} {curr} (100%)</span></div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-slate-200"><div className="h-full rounded-full bg-brand-700" style={{ width: '100%' }} /></div>
      </div>
      <div>
        <div className="mb-1 flex items-center justify-between text-xs text-slate-600"><span>Estrés</span><span className="font-medium text-slate-800">{fmtNumber(stress)} {curr} ({fmtNumber(stressPct, 1)}%)</span></div>
        <div className="h-3 w-full overflow-hidden rounded-full bg-slate-200"><div className="h-full rounded-full bg-amber-500" style={{ width: `${stressPct}%` }} /></div>
      </div>
      <p className="text-xs text-slate-600">Reducción potencial estimada: <span className="font-semibold text-amber-800">{fmtNumber(diffPct, 2)}%</span> frente al escenario base (orientativo, no pérdida real).</p>
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

  const modeInfo = useMemo(() => {
    const mode = agent?.execution_mode
    const degraded = !!agent?.degraded
    const isFallback = !!agent?.is_fallback
    if (mode === 'deterministic_fallback' || isFallback) {
      return { label: 'Fallback determinista', tone: 'amber' as const, detail: 'Respuesta sin flujo LLM/tools ejecutado. Resultados deterministas/fallback, no cotización firme.' }
    }
    if (degraded) {
      return { label: 'Modo degradado', tone: 'amber' as const, detail: 'Respuesta potencialmente incompleta o no totalmente verificada (no es un fallback determinista completo).' }
    }
    if (mode === 'llm_tools') {
      return { label: 'LLM + tools verificadas', tone: 'green' as const, detail: 'El agente ejecutó herramientas y el backend verificó el cálculo.' }
    }
    if (mode === 'frontend_demo') {
      return { label: 'Demo frontend', tone: 'slate' as const, detail: 'Cifras generadas localmente en frontend (si aplica).' }
    }
    return { label: mode ? `Modo: ${mode}` : 'Sin resultado', tone: 'slate' as const, detail: 'Envía una simulación para ver metadatos de ejecución y trazabilidad.' }
  }, [agent])

  function applyPreset(key: keyof typeof PRESETS) {
    const p = PRESETS[key]
    setMessage(p.message)
    setAmountEur(p.amountEur)
    setDestinationCountry(p.destinationCountry)
    setCurrency(p.currency)
    setFeeEur(p.feeEur)
    setScenarioDropPct(p.scenarioDropPct)
    setError(null)
  }

  function clearAll() {
    setMessage('')
    setAmountEur('')
    setDestinationCountry('KE')
    setCurrency('KES')
    setFeeEur('')
    setScenarioDropPct('3')
    setError(null)
    setResponse(null)
    setHttpStatus(null)
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
    const lines = [
      'Impact FX — Resumen de simulación',
      `Modo: ${a?.execution_mode || 'n/d'} | degraded=${String(!!a?.degraded)} | is_fallback=${String(!!a?.is_fallback)}`,
      `FX: ${a?.fx_reference?.rate ?? 'n/d'} (${a?.fx_reference?.source || a?.fx_source || 'n/d'}, ${a?.fx_reference?.date || 'n/d'}, is_mock=${String(a?.fx_reference?.is_mock ?? 'n/d')})`,
      `Base: ${fmtNumber(b?.amount_received)} ${b?.currency || ''} | Estrés: ${fmtNumber(st?.amount_received)} ${st?.currency || ''} | Dif: ${fmtNumber(a?.difference?.amount)} ${a?.difference?.currency || b?.currency || ''}`,
      'Nota: simulación orientativa/referencia, no cotización firme ni ejecución de pagos.',
    ]
    return lines.join('\n')
  }

  async function copySummary() {
    const text = buildSummary()
    if (!text) return
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      setCopied(false)
    }
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    setResponse(null)
    setHttpStatus(null)

    const context: ChatContext = {}
    if (amountEur !== '') context.amount_eur = Number(amountEur)
    if (destinationCountry.trim()) context.destination_country = destinationCountry.trim().toUpperCase()
    if (currency.trim()) context.currency = currency.trim().toUpperCase()
    if (feeEur !== '') context.fee_eur = Number(feeEur)
    if (scenarioDropPct !== '') context.scenario_drop_pct = Number(scenarioDropPct)

    try {
      const res = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message, context }),
      })
      setHttpStatus(res.status)
      const data = (await res.json()) as ChatResponse & { error?: string; code?: string; details?: unknown }
      const ok = res.ok
      if (!ok) {
        const details = typeof data.details === 'string' ? data.details : data.details ? JSON.stringify(data.details) : ''
        const msg = [data.error || 'request_failed', data.code, details].filter(Boolean).join(' · ')
        setError(msg)
        const item: HistoryItem = { id: crypto.randomUUID(), at: new Date().toLocaleString(), httpStatus: res.status, ok: false, summary: msg }
        saveHistory([item, ...history].slice(0, 5))
      } else {
        setResponse(data)
        const a = data.agent
        const sc = a?.scenarios || []
        const b = sc.find((s) => s.name === 'base') || sc[0]
        const st = sc.find((s) => s.name && s.name !== 'base') || sc[1]
        const item: HistoryItem = {
          id: crypto.randomUUID(), at: new Date().toLocaleString(), httpStatus: res.status, ok: true,
          mode: a?.execution_mode, degraded: !!a?.degraded, is_fallback: !!a?.is_fallback,
          base: b?.amount_received, stress: st?.amount_received, diff: a?.difference?.amount, currency: b?.currency || a?.difference?.currency,
          summary: sc.length ? `Base ${fmtNumber(b?.amount_received)} / Estrés ${fmtNumber(st?.amount_received)} ${b?.currency || ''}` : (data.reply || 'Respuesta sin escenarios').slice(0, 80),
        }
        saveHistory([item, ...history].slice(0, 5))
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error inesperado'
      setError(msg)
      setHealth('down')
    } finally {
      setLoading(false)
    }
  }

  const hasScenarios = scenarios.length > 0

  return (
    <div className="min-h-screen bg-surface">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <header className="mb-6 rounded-2xl border border-brand-900/10 bg-gradient-to-r from-brand-950 via-brand-900 to-brand-800 p-6 text-white shadow-sm sm:p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-100/90">Impact FX · Ayuda a ONGs</p>
              <h1 className="mt-2 text-2xl font-bold tracking-tight text-white sm:text-3xl">Simulador de impacto de transferencias</h1>
              <p className="mt-2 max-w-3xl text-sm text-brand-50/90">
                Estima cuánto recibe tu socio local (EUR→KES), compara escenario base vs adverso y toma decisiones con trazabilidad. Simulación orientativa: sin ejecución de pagos ni cotización firme.
              </p>
            </div>
            <div className="flex flex-col items-start gap-2 text-xs text-brand-50">
              <div className="rounded-xl border border-white/15 bg-white/10 px-3 py-2 backdrop-blur">API: <code className="font-mono text-white">{API_BASE_URL}</code></div>
              <div className="flex items-center gap-2">
                <button type="button" onClick={checkHealth} className="rounded-lg border border-white/20 bg-white/10 px-2.5 py-1.5 hover:bg-white/20">Comprobar API</button>
                {health === 'ok' ? <Badge tone="green">API disponible</Badge> : health === 'down' ? <Badge tone="red">API no disponible</Badge> : <Badge tone="slate">Estado API: sin comprobar</Badge>}
              </div>
            </div>
          </div>
        </header>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          <form onSubmit={onSubmit} className="space-y-4 lg:col-span-4">
            <Section title="1. Simulación" right={<button type="button" onClick={clearAll} className="text-xs font-medium text-brand-800 hover:underline">Limpiar</button>}>
              <div className="mb-3 flex flex-wrap gap-2">
                {Object.entries(PRESETS).map(([k, p]) => (
                  <button key={k} type="button" onClick={() => applyPreset(k as keyof typeof PRESETS)} className="rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:border-brand-700 hover:bg-brand-50 hover:text-brand-900">
                    {p.label}
                  </button>
                ))}
              </div>

              <label htmlFor="sim-message" className="block text-sm font-medium text-slate-700">Mensaje para el agente</label>
              <textarea
                id="sim-message"
                className="mt-1 w-full rounded-xl border border-slate-300 bg-white p-3 text-sm text-slate-900 shadow-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-100"
                rows={5}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Describe tu consulta o usa un ejemplo..."
              />

              <div className="mt-4 grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="sim-amount" className="block text-xs font-medium text-slate-600">Monto (EUR)</label>
                  <input id="sim-amount" type="number" min="0" step="0.01" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-100" value={amountEur} onChange={(e) => setAmountEur(e.target.value)} placeholder="10000" />
                </div>
                <div>
                  <label htmlFor="sim-fee" className="block text-xs font-medium text-slate-600">Comisión (EUR)</label>
                  <input id="sim-fee" type="number" min="0" step="0.01" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-100" value={feeEur} onChange={(e) => setFeeEur(e.target.value)} placeholder="40" />
                </div>
                <div>
                  <label htmlFor="sim-country" className="block text-xs font-medium text-slate-600">País destino</label>
                  <input id="sim-country" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm uppercase focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-100" value={destinationCountry} onChange={(e) => setDestinationCountry(e.target.value)} placeholder="KE" />
                </div>
                <div>
                  <label htmlFor="sim-currency" className="block text-xs font-medium text-slate-600">Moneda</label>
                  <input id="sim-currency" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm uppercase focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-100" value={currency} onChange={(e) => setCurrency(e.target.value)} placeholder="KES" />
                </div>
                <div className="col-span-2">
                  <label htmlFor="sim-drop" className="block text-xs font-medium text-slate-600">Caída escenario adverso (%)</label>
                  <input id="sim-drop" type="number" min="0" step="0.1" className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-100" value={scenarioDropPct} onChange={(e) => setScenarioDropPct(e.target.value)} placeholder="3" />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading || !message.trim()}
                className="mt-4 inline-flex w-full items-center justify-center rounded-xl bg-brand-800 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
              >
                {loading ? 'Calculando…' : 'Simular impacto'}
              </button>

              {httpStatus ? <p className="mt-2 text-xs text-slate-500">Estado HTTP: {httpStatus}</p> : null}
              {error ? <div className="mt-3 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800"><div className="font-medium">No se pudo completar la solicitud</div><div className="mt-1 break-words">{error}</div></div> : null}
            </Section>

            <Section title="Cómo te ayuda">
              <ul className="list-disc space-y-1 pl-5 text-sm text-slate-600">
                <li><span className="font-medium text-slate-800">Planifica:</span> estima cuánto llega y el impacto si la tasa cae.</li>
                <li><span className="font-medium text-slate-800">Transparencia:</span> verás tasa, fuente, fecha y si es dato demo.</li>
                <li><span className="font-medium text-slate-800">Límites claros:</span> no se ejecutan pagos ni es cotización firme.</li>
              </ul>
            </Section>

            <Section title="Historial reciente (local)">
              {history.length ? (
                <ul className="space-y-2">
                  {history.map((h) => (
                    <li key={h.id} className="rounded-lg border border-slate-200 bg-slate-50 p-2.5 text-xs text-slate-700">
                      <div className="flex items-center justify-between gap-2"><span className="font-medium">{h.at}</span><span>{h.ok ? `HTTP ${h.httpStatus ?? ''}` : 'Error'}</span></div>
                      <div className="mt-1">{h.summary}</div>
                    </li>
                  ))}
                </ul>
              ) : <p className="text-sm text-slate-600">Aún no hay simulaciones. Prueba con “B1 · Caso completo”.</p>}
            </Section>
          </form>

          <div className="space-y-6 lg:col-span-8">
            {!response && !error ? (
              <Section title="Resultado">
                <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
                  <p className="text-sm font-medium text-slate-800">Listo para simular</p>
                  <p className="mt-1 text-sm text-slate-600">Usa un ejemplo (B1) para ver escenarios, diferencia, trazabilidad FX y impacto presupuestario de forma clara.</p>
                </div>
              </Section>
            ) : null}

            <Section title="Respuesta del agente" right={response ? <button type="button" onClick={copySummary} className="rounded-lg border border-slate-200 px-2.5 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50">{copied ? 'Copiado' : 'Copiar resumen'}</button> : null}>
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={modeInfo.tone}>{modeInfo.label}</Badge>
                {agent?.execution_mode ? <Badge tone="slate">{`execution_mode=${agent.execution_mode}`}</Badge> : null}
                {agent ? <Badge tone={agent.degraded ? 'amber' : 'slate'}>{`degraded=${String(!!agent.degraded)}`}</Badge> : null}
                {agent ? <Badge tone={agent.is_fallback ? 'amber' : 'slate'}>{`is_fallback=${String(!!agent.is_fallback)}`}</Badge> : null}
                {agent?.fx_source ? <Badge tone="blue">{`fx_source=${agent.fx_source}`}</Badge> : null}
              </div>
              <p className="mt-3 text-sm text-slate-600">{modeInfo.detail}</p>
              <div className="mt-4 whitespace-pre-wrap rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-800">
                {response?.reply || (error ? 'Revisa el mensaje de error y ajusta los datos (ej. indica el monto para simular).' : 'Sin respuesta.')}
              </div>
            </Section>

            <Section title="Referencia de tipo de cambio (trazabilidad)">
              {agent?.fx_reference?.rate != null ? (
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <Stat label="Tasa" value={fmtNumber(Number(agent.fx_reference.rate), 4)} />
                  <Stat label="Fuente" value={String(agent.fx_reference.source || agent.fx_source || 'n/d')} />
                  <Stat label="Fecha" value={String(agent.fx_reference.date || 'n/d')} />
                  <Stat label="Dato ficticio" value={agent.fx_reference.is_mock ? 'Sí' : 'No'} />
                </div>
              ) : (
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
                  {agent?.is_fallback || agent?.execution_mode === 'deterministic_fallback'
                    ? 'Referencia FX no disponible en este resultado (fallback determinista: no se ejecutó `get_fx_reference`).'
                    : response ? 'Referencia FX no disponible en la respuesta.' : 'La referencia FX se mostrará aquí cuando haya una simulación con trazabilidad.'}
                </div>
              )}
              {agent?.fx_source === 'frankfurter' || agent?.fx_reference?.source === 'frankfurter' ? (
                <p className="mt-3 text-xs text-slate-500">Referencia externa (Frankfurter). No es cotización bancaria vinculante ni precio ejecutable.</p>
              ) : agent?.fx_source === 'demo' || agent?.fx_reference?.is_mock ? (
                <p className="mt-3 text-xs text-slate-500">Referencia de demostración/ficticia u orientativa. No es cotización firme.</p>
              ) : null}
            </Section>

            <Section title="Escenarios y diferencia (impacto estimado)">
              {hasScenarios ? (
                <>
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                    <Stat label="Recibe (base)" value={`${fmtNumber(base?.amount_received)} ${base?.currency || ''}`} hint={base?.rate != null ? `Tasa: ${fmtNumber(Number(base.rate), 4)}` : undefined} />
                    <Stat label="Recibe (estrés)" value={`${fmtNumber(stress?.amount_received)} ${stress?.currency || ''}`} hint={stress?.rate != null ? `Tasa: ${fmtNumber(Number(stress.rate), 4)}` : undefined} />
                    <Stat label="Diferencia potencial" value={`${fmtNumber(agent?.difference?.amount)} ${agent?.difference?.currency || base?.currency || ''}`} hint="Orientativo, no pérdida real" />
                  </div>
                  <ComparisonBars base={base?.amount_received} stress={stress?.amount_received} currency={base?.currency || agent?.difference?.currency} />
                  <div className="mt-4 overflow-x-auto">
                    <table className="min-w-full text-left text-sm">
                      <thead className="text-xs uppercase text-slate-500">
                        <tr>
                          <th className="py-2 pr-4">Escenario</th>
                          <th className="py-2 pr-4">Tasa</th>
                          <th className="py-2 pr-4">Comisión (EUR)</th>
                          <th className="py-2 pr-4">Recibe</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {scenarios.map((s, idx) => (
                          <tr key={`${s.name || 'scenario'}-${idx}`}>
                            <td className="py-2 pr-4 font-medium text-slate-800">{s.name || `#${idx + 1}`}</td>
                            <td className="py-2 pr-4 text-slate-700">{s.rate != null ? fmtNumber(Number(s.rate), 4) : '—'}</td>
                            <td className="py-2 pr-4 text-slate-700">{s.fee_eur != null ? fmtNumber(Number(s.fee_eur), 2) : '—'}</td>
                            <td className="py-2 pr-4 text-slate-900">{fmtNumber(s.amount_received)} {s.currency || ''}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              ) : (
                <p className="text-sm text-slate-600">{response ? 'Sin escenarios en esta respuesta (p. ej. faltan datos o la consulta no requirió cálculo). Si necesitas una estimación, indica monto, destino/moneda, comisión y variación.' : 'Los escenarios base y adverso aparecerán aquí tras la simulación.'}</p>
              )}
            </Section>

            {agent?.budget_impact ? (
              <Section title="Impacto presupuestario (demo)">
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <Stat label="Presupuesto" value={`${fmtNumber(Number(agent.budget_impact.budget_total))} ${agent.budget_impact.currency || ''}`} hint={agent.budget_impact.project_id} />
                  <Stat label="Cobertura base" value={`${fmtNumber(Number(agent.budget_impact.base_coverage_pct), 2)}%`} />
                  <Stat label="Cobertura estrés" value={`${fmtNumber(Number(agent.budget_impact.stress_coverage_pct), 2)}%`} />
                  <Stat label="Brecha potencial" value={`${fmtNumber(Number(agent.budget_impact.budget_gap))} ${agent.budget_impact.currency || ''}`} />
                </div>
                {agent.budget_impact.is_synthetic_demo ? (
                  <p className="mt-3 text-xs text-slate-500">Presupuesto sintético/de demostración. No se atribuye déficit a partidas concretas.</p>
                ) : null}
              </Section>
            ) : null}

            <details className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <summary className="cursor-pointer text-base font-semibold text-slate-900">Detalles: supuestos, alertas y herramientas</summary>
              <div className="mt-4 grid grid-cols-1 gap-6 md:grid-cols-2">
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">Supuestos</h3>
                  {agent?.assumptions?.length ? (
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700">
                      {agent.assumptions.map((a, i) => <li key={i}>{a}</li>)}
                    </ul>
                  ) : <p className="mt-2 text-sm text-slate-600">Sin supuestos reportados.</p>}
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">Alertas y herramientas</h3>
                  {agent?.alerts?.length ? (
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-amber-800">
                      {agent.alerts.map((a, i) => <li key={i}>{a}</li>)}
                    </ul>
                  ) : <p className="mt-2 text-sm text-slate-600">Sin alertas.</p>}
                  <div className="mt-3 text-sm text-slate-700">
                    <div className="font-medium text-slate-900">Tools usadas</div>
                    <div className="mt-1">{agent?.tools_used?.length ? agent.tools_used.join(', ') : 'Ninguna / no reportadas'}</div>
                  </div>
                  {agent?.reasoning_summary ? (
                    <div className="mt-3 text-sm text-slate-700">
                      <div className="font-medium text-slate-900">Resumen de ejecución</div>
                      <p className="mt-1 text-slate-600">{agent.reasoning_summary}</p>
                    </div>
                  ) : null}
                </div>
              </div>
            </details>

            <p className="px-1 text-xs text-slate-500">Impact FX ayuda a ONGs a anticipar el impacto cambiario con transparencia. Resultados orientativos/referencia; no constituyen cotización firme ni implican ejecución de pagos.</p>
          </div>
        </div>
      </div>
    </div>
  )
}
