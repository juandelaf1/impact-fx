import { useEffect, useMemo, useState } from 'react'

type Scenario = { name?: string; rate?: number; fee_eur?: number; amount_received?: number; currency?: string }
type FxReference = { rate?: number; source?: string; date?: string; is_mock?: boolean }
type BudgetImpact = { budget_total?: number; base_coverage_pct?: number; stress_coverage_pct?: number; budget_gap?: number; currency?: string; project_id?: string; is_synthetic_demo?: boolean }
type AgentData = {
  tools_used?: string[]; reasoning_summary?: string; scenarios?: Scenario[]; difference?: { amount?: number; currency?: string }
  assumptions?: string[]; alerts?: string[]; execution_mode?: string; degraded?: boolean; is_fallback?: boolean
  fx_source?: string | null; fx_reference?: FxReference | null; calculation_source?: string | null; budget_impact?: BudgetImpact
}
type ChatResponse = { reply?: string; agent?: AgentData }
type ChatContext = { amount_eur?: number; destination_country?: string; currency?: string; fee_eur?: number; scenario_drop_pct?: number }
type Prefs = { apiBaseUrl: string; showTechnical: boolean }

const DEFAULT_API = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') || 'http://127.0.0.1:3001'
const PREFS_KEY = 'impact-fx-prefs-v2'

const PRESETS = {
  b1: { label: 'Ejemplo completo', message: 'Enviar 10000 EUR a Kenia para un proyecto de salud. Comisión 40 EUR. ¿Cuánto recibiría el socio local si la tasa cae un 3%?', amountEur: '10000', destinationCountry: 'KE', currency: 'KES', feeEur: '40', scenarioDropPct: '3' },
  b2: { label: 'Falta el monto', message: 'Quiero enviar dinero a Kenia para apoyar un proyecto.', amountEur: '', destinationCountry: 'KE', currency: 'KES', feeEur: '', scenarioDropPct: '3' },
  b3: { label: 'Fuera de alcance', message: 'Ejecuta ya la transferencia de 10000 EUR a la cuenta del socio en Kenia.', amountEur: '10000', destinationCountry: 'KE', currency: 'KES', feeEur: '40', scenarioDropPct: '3' },
} as const

function fmt(value: number | undefined, digits = 0) {
  if (value == null || Number.isNaN(value)) return '—'
  return new Intl.NumberFormat('es-ES', { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(value)
}

function StatusPill({ mode, degraded, isFallback }: { mode?: string; degraded?: boolean; isFallback?: boolean }) {
  let text = 'Listo para simular', cls = 'bg-slate-100 text-slate-700'
  if (mode === 'deterministic_fallback' || isFallback) { text = 'Resultado de respaldo'; cls = 'bg-amber-100 text-amber-900' }
  else if (degraded) { text = 'Resultado con aviso'; cls = 'bg-amber-100 text-amber-900' }
  else if (mode === 'llm_tools') { text = 'Cálculo verificado'; cls = 'bg-brand-100 text-brand-900' }
  return <span className={`inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold ${cls}`}>{text}</span>
}

export default function App() {
  const [prefs, setPrefs] = useState<Prefs>({ apiBaseUrl: DEFAULT_API, showTechnical: false })
  const [prefsOpen, setPrefsOpen] = useState(false)
  const [techOpen, setTechOpen] = useState(false)
  const [message, setMessage] = useState<string>(PRESETS.b1.message)
  const [amountEur, setAmountEur] = useState<string>(PRESETS.b1.amountEur)
  const [destinationCountry, setDestinationCountry] = useState<string>(PRESETS.b1.destinationCountry)
  const [currency, setCurrency] = useState<string>(PRESETS.b1.currency)
  const [feeEur, setFeeEur] = useState<string>(PRESETS.b1.feeEur)
  const [scenarioDropPct, setScenarioDropPct] = useState<string>(PRESETS.b1.scenarioDropPct)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [response, setResponse] = useState<ChatResponse | null>(null)
  const [raw, setRaw] = useState<unknown>(null)
  const [meta, setMeta] = useState<{ status?: number; ms?: number; reqId?: string | null }>({})
  const [health, setHealth] = useState<'unknown' | 'ok' | 'down'>('unknown')

  useEffect(() => {
    try { const p = localStorage.getItem(PREFS_KEY); if (p) setPrefs((x) => ({ ...x, ...(JSON.parse(p) as Partial<Prefs>) })) } catch {}
  }, [])
  useEffect(() => { try { localStorage.setItem(PREFS_KEY, JSON.stringify(prefs)) } catch {} }, [prefs])

  const apiBase = (prefs.apiBaseUrl || DEFAULT_API).replace(/\/$/, '')
  const agent = response?.agent
  const scenarios = agent?.scenarios || []
  const base = scenarios.find((s) => s.name === 'base') || scenarios[0]
  const stress = scenarios.find((s) => s.name && s.name !== 'base') || scenarios[1]
  const curr = base?.currency || agent?.difference?.currency || currency || 'KES'
  const hasScenarios = scenarios.length > 0
  const baseAmt = base?.amount_received || 0
  const stressAmt = stress?.amount_received || 0
  const diffAmt = agent?.difference?.amount || (baseAmt > stressAmt ? baseAmt - stressAmt : 0)
  const reduction = baseAmt > 0 ? (diffAmt / baseAmt) * 100 : 0
  const stressPct = baseAmt > 0 ? Math.max(0, Math.min(100, (stressAmt / baseAmt) * 100)) : 0

  const friendlyMode = useMemo(() => {
    if (agent?.execution_mode === 'deterministic_fallback' || agent?.is_fallback) return 'Mostramos una estimación de respaldo basada en datos de referencia.'
    if (agent?.degraded) return 'Hay un aviso en el resultado: revísalo antes de tomar decisiones.'
    if (agent?.execution_mode === 'llm_tools') return 'Estimación calculada con herramientas verificadas y trazabilidad disponible.'
    return 'Completa los datos y simula para ver cuánto podría recibir tu socio local.'
  }, [agent])

  function applyPreset(k: keyof typeof PRESETS) {
    const p = PRESETS[k]
    setMessage(p.message); setAmountEur(p.amountEur); setDestinationCountry(p.destinationCountry); setCurrency(p.currency); setFeeEur(p.feeEur); setScenarioDropPct(p.scenarioDropPct); setError(null)
  }
  function resetAll() { setMessage(''); setAmountEur(''); setDestinationCountry('KE'); setCurrency('KES'); setFeeEur('40'); setScenarioDropPct('3'); setError(null); setResponse(null); setRaw(null); setMeta({}) }

  async function checkHealth() { try { const r = await fetch(`${apiBase}/api/health`); setHealth(r.ok ? 'ok' : 'down') } catch { setHealth('down') } }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true); setError(null); setResponse(null); setRaw(null)
    const context: ChatContext = {}
    if (amountEur !== '') context.amount_eur = Number(amountEur)
    if (destinationCountry.trim()) context.destination_country = destinationCountry.trim().toUpperCase()
    if (currency.trim()) context.currency = currency.trim().toUpperCase()
    if (feeEur !== '') context.fee_eur = Number(feeEur)
    if (scenarioDropPct !== '') context.scenario_drop_pct = Number(scenarioDropPct)
    const t0 = performance.now()
    try {
      const r = await fetch(`${apiBase}/api/chat`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ message, context }) })
      const ms = Math.round(performance.now() - t0)
      const reqId = r.headers.get('x-request-id') || r.headers.get('X-Request-ID')
      setMeta({ status: r.status, ms, reqId })
      const data = await r.json() as ChatResponse & { error?: string; code?: string; details?: unknown }
      setRaw(data)
      if (!r.ok) {
        const details = typeof data.details === 'string' ? data.details : data.details ? JSON.stringify(data.details) : ''
        setError([data.error, data.code, details].filter(Boolean).join(' · ') || 'No se pudo completar la solicitud')
      } else setResponse(data)
    } catch (err) { setError(err instanceof Error ? err.message : 'Error de conexión'); setHealth('down') }
    finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen px-4 py-5 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-6xl">
        <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-brand-800 text-white shadow-sm">
              <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.8"><path d="M12 3v18M3 12h18" opacity=".25"/><path d="M7 8c1.2-1.3 3-2 5-2s3.8.7 5 2M7 16c1.2 1.3 3 2 5 2s3.8-.7 5-2" strokeLinecap="round"/><path d="M12 4c2.5 2.2 4 4.8 4 8s-1.5 5.8-4 8c-2.5-2.2-4-4.8-4-8s1.5-5.8 4-8Z"/></svg>
            </div>
            <div>
              <div className="text-sm font-semibold text-brand-900">Impact FX</div>
              <div className="text-xs text-slate-600">Transparencia para transferencias de ONGs</div>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button type="button" onClick={checkHealth} className="rounded-full border border-slate-200 bg-white/80 px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm hover:bg-white">Conexión: {health === 'ok' ? 'OK' : health === 'down' ? 'sin conexión' : 'comprobar'}</button>
            <button type="button" onClick={() => setPrefsOpen(true)} className="rounded-full bg-brand-800 px-3 py-1.5 text-xs font-semibold text-white shadow-sm hover:bg-brand-700">Preferencias</button>
          </div>
        </div>

        <div className="grid gap-5 lg:grid-cols-[420px_1fr]">
          <div className="space-y-4">
            <section className="rounded-3xl border border-white/70 bg-white/80 p-5 shadow-sm backdrop-blur sm:p-6">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h1 className="text-2xl font-bold tracking-tight text-slate-900">Simula tu envío</h1>
                  <p className="mt-1 text-sm text-slate-600">Descubre cuánto podría llegar a tu socio local y cómo cambia si el tipo de cambio baja.</p>
                </div>
                <StatusPill mode={agent?.execution_mode} degraded={agent?.degraded} isFallback={agent?.is_fallback} />
              </div>

              <div className="mt-4 flex flex-wrap gap-2">
                {Object.entries(PRESETS).map(([k, p]) => (
                  <button key={k} type="button" onClick={() => applyPreset(k as keyof typeof PRESETS)} className="rounded-full border border-slate-200 bg-sand-50 px-3 py-1.5 text-xs font-medium text-slate-700 hover:border-brand-600 hover:bg-brand-50 hover:text-brand-900">{p.label}</button>
                ))}
              </div>

              <form onSubmit={onSubmit} className="mt-4 space-y-3">
                <div>
                  <label htmlFor="msg" className="mb-1 block text-sm font-medium text-slate-700">Tu pregunta</label>
                  <textarea id="msg" rows={3} value={message} onChange={(e) => setMessage(e.target.value)} className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm shadow-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-100" placeholder="Ej: ¿Cuánto recibirá mi socio en Kenia si envío 10.000 EUR?" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label htmlFor="amount" className="mb-1 block text-xs font-medium text-slate-600">Monto (EUR)</label>
                    <input id="amount" type="number" min="0" step="0.01" value={amountEur} onChange={(e) => setAmountEur(e.target.value)} className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-100" placeholder="10000" />
                  </div>
                  <div>
                    <label htmlFor="drop" className="mb-1 block text-xs font-medium text-slate-600">Si baja la tasa (%)</label>
                    <input id="drop" type="number" min="0" step="0.1" value={scenarioDropPct} onChange={(e) => setScenarioDropPct(e.target.value)} className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-100" placeholder="3" />
                  </div>
                  <div>
                    <label htmlFor="fee" className="mb-1 block text-xs font-medium text-slate-600">Comisión (EUR)</label>
                    <input id="fee" type="number" min="0" step="0.01" value={feeEur} onChange={(e) => setFeeEur(e.target.value)} className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-100" placeholder="40" />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label htmlFor="country" className="mb-1 block text-xs font-medium text-slate-600">País</label>
                      <input id="country" value={destinationCountry} onChange={(e) => setDestinationCountry(e.target.value)} className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm uppercase focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-100" />
                    </div>
                    <div>
                      <label htmlFor="curr" className="mb-1 block text-xs font-medium text-slate-600">Moneda</label>
                      <input id="curr" value={currency} onChange={(e) => setCurrency(e.target.value)} className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm uppercase focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-100" />
                    </div>
                  </div>
                </div>
                <div className="flex gap-2 pt-1">
                  <button type="submit" disabled={loading || !message.trim()} className="inline-flex flex-1 items-center justify-center gap-2 rounded-2xl bg-brand-800 px-4 py-3 text-sm font-semibold text-white shadow-sm hover:bg-brand-700 disabled:opacity-60">
                    {loading ? <><span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"/> Calculando…</> : 'Ver estimación'}
                  </button>
                  <button type="button" onClick={resetAll} className="rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50">Limpiar</button>
                </div>
              </form>

              {error && (
                <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800">
                  <div className="font-semibold">No pudimos completar la simulación</div>
                  <div className="mt-1 break-words">{error}</div>
                  <div className="mt-2 text-xs text-rose-700/90">Revisa que el monto esté indicado (ejemplo B1) o usa la conexión/API en Preferencias.</div>
                </div>
              )}
            </section>

            <section className="rounded-3xl border border-white/70 bg-white/70 p-5 shadow-sm backdrop-blur">
              <h2 className="text-sm font-semibold text-slate-900">Cómo usarlo</h2>
              <ol className="mt-3 space-y-2 text-sm text-slate-700">
                <li className="flex gap-3"><span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-100 text-xs font-bold text-brand-900">1</span><span>Indica monto, destino y posible caída del tipo de cambio.</span></li>
                <li className="flex gap-3"><span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-100 text-xs font-bold text-brand-900">2</span><span>Compara cuánto llega en el escenario base y en el adverso.</span></li>
                <li className="flex gap-3"><span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-100 text-xs font-bold text-brand-900">3</span><span>Revisa la nota de transparencia (fuente de tasa y límites).</span></li>
              </ol>
              <p className="mt-3 text-xs text-slate-500">Estimación orientativa para apoyar decisiones de ONGs. No ejecuta pagos ni es cotización firme.</p>
            </section>
          </div>

          <div className="space-y-4">
            <section className="overflow-hidden rounded-3xl border border-white/70 bg-white/80 shadow-sm backdrop-blur">
              <div className="border-b border-slate-100 bg-gradient-to-r from-brand-50/70 to-sand-50 p-5 sm:p-6">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="text-xs font-semibold uppercase tracking-wide text-brand-800">Resultado para tu proyecto</div>
                    <p className="mt-1 text-sm text-slate-600">{friendlyMode}</p>
                  </div>
                  {agent?.execution_mode && <span className="text-xs text-slate-500">Modo: {agent.execution_mode}{agent.degraded ? ' · con aviso' : ''}{agent.is_fallback ? ' · respaldo' : ''}</span>}
                </div>

                {hasScenarios ? (
                  <div className="mt-5 grid gap-4 sm:grid-cols-[1.2fr_1fr]">
                    <div className="rounded-3xl bg-brand-900 p-5 text-white shadow-sm">
                      <div className="text-sm text-brand-100">Tu socio local podría recibir</div>
                      <div className="mt-1 flex items-end gap-2"><span className="text-4xl font-bold tabular-nums sm:text-5xl">{fmt(baseAmt)}</span><span className="pb-1 text-lg font-semibold text-brand-100">{curr}</span></div>
                      <div className="mt-2 inline-flex rounded-full bg-white/10 px-3 py-1 text-xs text-brand-50">Escenario base (estimado)</div>
                      <div className="mt-5 space-y-3">
                        <div>
                          <div className="mb-1 flex justify-between text-xs text-brand-100"><span>Si el tipo de cambio baja</span><span>{fmt(stressAmt)} {curr}</span></div>
                          <div className="h-3 overflow-hidden rounded-full bg-white/15"><div className="h-full rounded-full bg-gradient-to-r from-emerald-300 to-amber-300" style={{ width: `${stressPct}%` }} /></div>
                        </div>
                        <div className="rounded-2xl bg-white/10 p-3 text-sm">
                          <div className="text-brand-100">Diferencia potencial</div>
                          <div className="mt-0.5 text-lg font-semibold tabular-nums text-amber-200">-{fmt(diffAmt)} {curr} <span className="text-sm font-medium text-brand-100">({fmt(reduction, 1)}%)</span></div>
                        </div>
                      </div>
                    </div>
                    <div className="flex flex-col justify-center gap-3">
                      <div className="rounded-2xl border border-slate-200 bg-white p-4">
                        <div className="text-xs font-medium uppercase tracking-wide text-slate-500">Escenario base</div>
                        <div className="mt-1 text-2xl font-bold tabular-nums text-slate-900">{fmt(baseAmt)} <span className="text-base font-semibold text-slate-600">{curr}</span></div>
                        <div className="mt-1 text-xs text-slate-500">Tasa {fmt(base?.rate, 4)} · Comisión {fmt(base?.fee_eur, 2)} EUR</div>
                      </div>
                      <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4">
                        <div className="text-xs font-medium uppercase tracking-wide text-amber-800">Escenario adverso</div>
                        <div className="mt-1 text-2xl font-bold tabular-nums text-amber-900">{fmt(stressAmt)} <span className="text-base font-semibold text-amber-800">{curr}</span></div>
                        <div className="mt-1 text-xs text-amber-800/80">Tasa {fmt(stress?.rate, 4)} · caída {fmt(Number(scenarioDropPct), 1)}%</div>
                      </div>
                      {agent?.budget_impact && (
                        <div className="rounded-2xl border border-brand-100 bg-brand-50 p-4">
                          <div className="text-xs font-medium uppercase tracking-wide text-brand-800">Cobertura del presupuesto (demo)</div>
                          <div className="mt-1 text-lg font-semibold text-brand-900">{fmt(Number(agent.budget_impact.stress_coverage_pct), 1)}% en estrés</div>
                          <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-white"><div className="h-full rounded-full bg-brand-700" style={{ width: `${Math.max(0, Math.min(100, Number(agent.budget_impact.stress_coverage_pct) || 0))}%` }} /></div>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="mt-5 rounded-3xl border border-dashed border-slate-300 bg-white p-6 text-center">
                    <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-50 text-brand-800">
                      <svg viewBox="0 0 24 24" className="h-7 w-7" fill="none" stroke="currentColor" strokeWidth="1.8"><path strokeLinecap="round" strokeLinejoin="round" d="M3 12c2.5-4 5.5-6 9-6s6.5 2 9 6c-2.5 4-5.5 6-9 6s-6.5-2-9-6Z"/><circle cx="12" cy="12" r="2.5"/></svg>
                    </div>
                    <h2 className="mt-3 text-lg font-semibold text-slate-900">Aquí verás el impacto estimado</h2>
                    <p className="mt-1 text-sm text-slate-600">Pulsa “Ejemplo completo” y luego “Ver estimación” para ver un resultado visual claro.</p>
                  </div>
                )}
              </div>

              <div className="space-y-4 p-5 sm:p-6">
                <div className="rounded-2xl bg-slate-50 p-4">
                  <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Explicación</div>
                  <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-800">{response?.reply || (error ? 'Indica el monto y los datos del envío para obtener una estimación.' : 'La explicación aparecerá aquí después de simular.')}</p>
                </div>

                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="rounded-2xl border border-slate-200 p-4">
                    <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Transparencia de la tasa</div>
                    {agent?.fx_reference ? (
                      <div className="mt-2 space-y-1 text-sm text-slate-700">
                        <div><span className="text-slate-500">Tasa:</span> <span className="font-semibold tabular-nums text-slate-900">{fmt(Number(agent.fx_reference.rate), 4)}</span></div>
                        <div><span className="text-slate-500">Fuente:</span> {agent.fx_reference.source || '—'} · <span className="text-slate-500">Fecha:</span> {agent.fx_reference.date || '—'}</div>
                        <div><span className="text-slate-500">Tipo:</span> {agent.fx_reference.is_mock ? 'Referencia de demostración' : 'Referencia'}</div>
                      </div>
                    ) : <p className="mt-2 text-sm text-slate-600">{response ? 'No hay referencia de tasa disponible en este resultado (p. ej. respaldo sin consulta de tasa).' : 'La fuente y fecha de la tasa se mostrarán aquí.'}</p>}
                  </div>
                  <div className="rounded-2xl border border-slate-200 p-4">
                    <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Qué tener en cuenta</div>
                    <ul className="mt-2 space-y-1 text-sm text-slate-700">
                      <li>• Es una estimación orientativa, no una cotización firme.</li>
                      <li>• No se ejecutan pagos desde esta herramienta.</li>
                      <li>• Si faltan datos, te pediremos lo necesario (no inventamos cifras).</li>
                    </ul>
                    {agent?.alerts?.length ? <div className="mt-2 rounded-xl bg-amber-50 p-2 text-xs text-amber-900">{agent.alerts[0]}</div> : null}
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2 border-t border-slate-100 pt-2">
                  <button type="button" onClick={() => setTechOpen((v) => !v)} className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50">{techOpen ? 'Ocultar detalles técnicos' : 'Ver detalles técnicos'}</button>
                  {raw != null && <button type="button" onClick={() => navigator.clipboard.writeText(JSON.stringify(raw, null, 2))} className="rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50">Copiar informe JSON</button>}
                  <span className="text-xs text-slate-500">{meta.status ? `HTTP ${meta.status}` : ''}{meta.ms != null ? ` · ${meta.ms} ms` : ''}{meta.reqId ? ` · ${meta.reqId}` : ''}</span>
                </div>

                {techOpen && (
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <div className="grid gap-3 sm:grid-cols-3 text-xs text-slate-700">
                      <div><span className="text-slate-500">Ejecución:</span> {agent?.execution_mode || '—'}</div>
                      <div><span className="text-slate-500">FX:</span> {String(agent?.fx_source ?? '—')} / {String(agent?.calculation_source ?? '—')}</div>
                      <div><span className="text-slate-500">Herramientas:</span> {agent?.tools_used?.length ? agent.tools_used.join(', ') : '—'}</div>
                    </div>
                    {agent?.assumptions?.length ? <div className="mt-3"><div className="text-xs font-semibold text-slate-700">Supuestos</div><ul className="mt-1 list-disc space-y-1 pl-5 text-xs text-slate-600">{agent.assumptions.map((a, i) => <li key={i}>{a}</li>)}</ul></div> : null}
                    <pre className="mt-3 max-h-72 overflow-auto rounded-xl bg-white p-3 text-[11px] leading-5 text-slate-700 ring-1 ring-slate-200">{raw != null ? JSON.stringify(raw, null, 2) : 'Sin datos técnicos.'}</pre>
                  </div>
                )}
              </div>
            </section>
          </div>
        </div>
      </div>

      {prefsOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/30 p-4" onClick={() => setPrefsOpen(false)}>
          <div className="w-full max-w-md rounded-3xl bg-white p-5 shadow-xl" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center justify-between"><h2 className="text-base font-semibold text-slate-900">Preferencias</h2><button type="button" onClick={() => setPrefsOpen(false)} className="rounded-full px-3 py-1 text-sm text-slate-500 hover:bg-slate-100">Cerrar</button></div>
            <div className="mt-4 space-y-4 text-sm">
              <div>
                <label htmlFor="pref-api" className="mb-1 block text-xs font-medium text-slate-600">URL de la API</label>
                <input id="pref-api" value={prefs.apiBaseUrl} onChange={(e) => setPrefs({ ...prefs, apiBaseUrl: e.target.value })} className="w-full rounded-xl border border-slate-200 px-3 py-2.5 focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-100" />
                <p className="mt-1 text-xs text-slate-500">Cambia esto si tu backend está en otra dirección.</p>
              </div>
              <label className="flex items-center gap-2 text-slate-700"><input type="checkbox" checked={prefs.showTechnical} onChange={(e) => { setPrefs({ ...prefs, showTechnical: e.target.checked }); setTechOpen(e.target.checked) }} /> Mostrar detalles técnicos por defecto</label>
              <div className="rounded-2xl bg-sand-50 p-3 text-xs text-slate-600">Los informes técnicos incluyen el JSON completo, tiempos y metadatos de ejecución (útil para soporte o revisión), pero se mantienen fuera de la vista principal.</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
