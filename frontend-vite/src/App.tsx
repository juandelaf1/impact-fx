import { useMemo, useState } from 'react'

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

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') || 'http://127.0.0.1:3001'

function fmtNumber(value: number | undefined, digits = 0) {
  if (value === undefined || value === null || Number.isNaN(value)) return '—'
  return new Intl.NumberFormat('es-ES', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value)
}

function Badge({ tone, children }: { tone: 'green' | 'amber' | 'red' | 'slate'; children: string }) {
  const tones = {
    green: 'bg-brand-50 text-brand-900 ring-brand-800/20',
    amber: 'bg-amber-50 text-amber-900 ring-amber-200',
    red: 'bg-rose-50 text-rose-800 ring-rose-200',
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

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <h2 className="text-base font-semibold text-slate-900">{title}</h2>
      <div className="mt-4">{children}</div>
    </section>
  )
}

export default function App() {
  const [message, setMessage] = useState('Enviar 10000 EUR a Kenia para un proyecto de salud. Comisión 40 EUR. ¿Cuánto recibiría el socio local si la tasa cae un 3%?')
  const [amountEur, setAmountEur] = useState('10000')
  const [destinationCountry, setDestinationCountry] = useState('KE')
  const [currency, setCurrency] = useState('KES')
  const [feeEur, setFeeEur] = useState('40')
  const [scenarioDropPct, setScenarioDropPct] = useState('3')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [response, setResponse] = useState<ChatResponse | null>(null)
  const [httpStatus, setHttpStatus] = useState<number | null>(null)

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
    return { label: mode ? `Modo: ${mode}` : 'Modo no disponible', tone: 'slate' as const, detail: 'Sin metadatos de ejecución.' }
  }, [agent])

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
      if (!res.ok) {
        const details = typeof data.details === 'string' ? data.details : data.details ? JSON.stringify(data.details) : ''
        throw new Error([data.error || 'request_failed', data.code, details].filter(Boolean).join(' · '))
      }
      setResponse(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Error inesperado')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <header className="mb-6 rounded-2xl border border-brand-900/10 bg-gradient-to-r from-brand-950 via-brand-900 to-brand-800 p-6 text-white shadow-sm sm:p-8">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-100/90">Impact FX · Ayuda a ONGs</p>
              <h1 className="mt-2 text-2xl font-bold tracking-tight text-white sm:text-3xl">Simulador de impacto de transferencias</h1>
              <p className="mt-2 max-w-3xl text-sm text-brand-50/90">
                Transparencia para decisiones EUR→KES: estima cuánto recibe el socio local, compara escenarios y muestra supuestos, límites y trazabilidad. Referencia/demo, no cotización ejecutable ni ejecución de pagos.
              </p>
            </div>
            <div className="rounded-xl border border-white/15 bg-white/10 px-3 py-2 text-xs text-brand-50 backdrop-blur">
              API: <code className="font-mono text-white">{API_BASE_URL}</code>
            </div>
          </div>
        </header>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          <form onSubmit={onSubmit} className="space-y-4 lg:col-span-4">
            <Section title="Solicitud">
              <label className="block text-sm font-medium text-slate-700">Mensaje</label>
              <textarea
                className="mt-1 w-full rounded-xl border border-slate-300 bg-white p-3 text-sm text-slate-900 shadow-sm focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-200"
                rows={6}
                value={message}
                onChange={(e) => setMessage(e.target.value)}
              />

              <div className="mt-4 grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-600">Monto (EUR)</label>
                  <input className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" value={amountEur} onChange={(e) => setAmountEur(e.target.value)} />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600">Comisión (EUR)</label>
                  <input className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" value={feeEur} onChange={(e) => setFeeEur(e.target.value)} />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600">País destino</label>
                  <input className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" value={destinationCountry} onChange={(e) => setDestinationCountry(e.target.value)} />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-600">Moneda</label>
                  <input className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" value={currency} onChange={(e) => setCurrency(e.target.value)} />
                </div>
                <div className="col-span-2">
                  <label className="block text-xs font-medium text-slate-600">Caída escenario (%)</label>
                  <input className="mt-1 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" value={scenarioDropPct} onChange={(e) => setScenarioDropPct(e.target.value)} />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading || !message.trim()}
                className="mt-4 inline-flex w-full items-center justify-center rounded-xl bg-brand-800 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
              >
                {loading ? 'Calculando…' : 'Simular impacto'}
              </button>

              {httpStatus ? <p className="mt-2 text-xs text-slate-500">HTTP: {httpStatus}</p> : null}
              {error ? <div className="mt-3 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-800">{error}</div> : null}
            </Section>

            <Section title="Notas">
              <ul className="list-disc space-y-1 pl-5 text-sm text-slate-600">
                <li>No se ejecutan pagos (solo simulación).</li>
                <li>Tipos de cambio de referencia/demo, no cotización firme.</li>
                <li>Configura <code>VITE_API_BASE_URL</code> para apuntar al backend.</li>
              </ul>
            </Section>
          </form>

          <div className="space-y-6 lg:col-span-8">
            <Section title="Respuesta del agente">
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={modeInfo.tone}>{modeInfo.label}</Badge>
                {agent?.execution_mode ? <Badge tone="slate">{`execution_mode=${agent.execution_mode}`}</Badge> : null}
                <Badge tone={agent?.degraded ? 'amber' : 'slate'}>{`degraded=${String(!!agent?.degraded)}`}</Badge>
                <Badge tone={agent?.is_fallback ? 'amber' : 'slate'}>{`is_fallback=${String(!!agent?.is_fallback)}`}</Badge>
                {agent?.fx_source ? <Badge tone="slate">{`fx_source=${agent.fx_source}`}</Badge> : null}
                {agent?.calculation_source ? <Badge tone="slate">{`calc=${agent.calculation_source}`}</Badge> : null}
              </div>
              <p className="mt-3 text-sm text-slate-600">{modeInfo.detail}</p>
              <div className="mt-4 whitespace-pre-wrap rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm leading-6 text-slate-800">
                {response?.reply || 'Envía una solicitud para ver la respuesta integrada del agente.'}
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
                    : 'Referencia FX no disponible en la respuesta del agente.'}
                </div>
              )}
              {agent?.fx_source === 'frankfurter' || agent?.fx_reference?.source === 'frankfurter' ? (
                <p className="mt-3 text-xs text-slate-500">Referencia externa (Frankfurter). No es cotización bancaria vinculante ni precio ejecutable.</p>
              ) : agent?.fx_source === 'demo' || agent?.fx_reference?.is_mock ? (
                <p className="mt-3 text-xs text-slate-500">Referencia de demostración/ficticia u orientativa. No es cotización firme.</p>
              ) : null}
            </Section>

            <Section title="Escenarios y diferencia">
              {scenarios.length ? (
                <>
                  <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                    <Stat label="Escenario base" value={`${fmtNumber(base?.amount_received)} ${base?.currency || ''}`} hint={base?.rate != null ? `Tasa: ${fmtNumber(Number(base.rate), 4)}` : undefined} />
                    <Stat label="Escenario adverso" value={`${fmtNumber(stress?.amount_received)} ${stress?.currency || ''}`} hint={stress?.rate != null ? `Tasa: ${fmtNumber(Number(stress.rate), 4)}` : undefined} />
                    <Stat label="Diferencia" value={`${fmtNumber(agent?.difference?.amount)} ${agent?.difference?.currency || base?.currency || ''}`} hint="Estimación orientativa, no pérdida real" />
                  </div>
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
                <p className="text-sm text-slate-600">Sin escenarios en la respuesta (p. ej. falta de datos o respuesta no simulada).</p>
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

            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
              <Section title="Supuestos">
                {agent?.assumptions?.length ? (
                  <ul className="list-disc space-y-1 pl-5 text-sm text-slate-700">
                    {agent.assumptions.map((a, i) => <li key={i}>{a}</li>)}
                  </ul>
                ) : <p className="text-sm text-slate-600">Sin supuestos reportados.</p>}
              </Section>
              <Section title="Alertas y herramientas">
                {agent?.alerts?.length ? (
                  <ul className="mb-3 list-disc space-y-1 pl-5 text-sm text-amber-800">
                    {agent.alerts.map((a, i) => <li key={i}>{a}</li>)}
                  </ul>
                ) : null}
                <div className="text-sm text-slate-700">
                  <div className="font-medium text-slate-900">Tools usadas</div>
                  <div className="mt-1">{agent?.tools_used?.length ? agent.tools_used.join(', ') : 'Ninguna / no reportadas'}</div>
                </div>
                {agent?.reasoning_summary ? (
                  <div className="mt-3 text-sm text-slate-700">
                    <div className="font-medium text-slate-900">Resumen de ejecución</div>
                    <p className="mt-1 text-slate-600">{agent.reasoning_summary}</p>
                  </div>
                ) : null}
              </Section>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
