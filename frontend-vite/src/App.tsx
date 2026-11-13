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
type Prefs = { apiBaseUrl: string }

const DEFAULT_API = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '') || 'http://127.0.0.1:3001'
const PREFS_KEY = 'impact-fx-prefs-v3'

const PRESETS = {
  b1: { label: '✨ Simulación completa', hint: 'Kenia · 10.000€ · -3%', message: 'Enviar 10000 EUR a Kenia para un proyecto de salud. Comisión 40 EUR. ¿Cuánto recibiría el socio local si la tasa cae un 3%?', amountEur: '10000', destinationCountry: 'KE', currency: 'KES', feeEur: '40', scenarioDropPct: '3' },
  b2: { label: '📝 Falta el monto', hint: 'Ver guía de datos', message: 'Quiero enviar dinero a Kenia para apoyar un proyecto.', amountEur: '', destinationCountry: 'KE', currency: 'KES', feeEur: '', scenarioDropPct: '3' },
  b3: { label: '🛡️ Fuera de alcance', hint: 'No ejecuta pagos', message: 'Ejecuta ya la transferencia de 10000 EUR a la cuenta del socio en Kenia.', amountEur: '10000', destinationCountry: 'KE', currency: 'KES', feeEur: '40', scenarioDropPct: '3' },
} as const

function fmt(v: number | undefined, d = 0) { if (v == null || Number.isNaN(v)) return '—'; return new Intl.NumberFormat('es-ES', { minimumFractionDigits: d, maximumFractionDigits: d }).format(v) }

function HeroArt() {
  return (
    <svg viewBox="0 0 420 280" className="h-full w-full" aria-hidden="true">
      <defs>
        <linearGradient id="g1" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#2a9d8f" stopOpacity=".9"/><stop offset="1" stopColor="#0b3f3f" stopOpacity=".9"/></linearGradient>
        <linearGradient id="g2" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stopColor="#fcd34d"/><stop offset="1" stopColor="#fb923c"/></linearGradient>
      </defs>
      <rect x="20" y="20" width="380" height="240" rx="28" fill="url(#g1)" opacity=".18"/>
      <circle cx="320" cy="70" r="46" fill="#fcd34d" opacity=".35"/>
      <circle cx="90" cy="210" r="54" fill="#2a9d8f" opacity=".25"/>
      <path d="M70 170c40-55 95-55 140-10 35 35 70 40 120 0" fill="none" stroke="#ffffff" strokeOpacity=".35" strokeWidth="10" strokeLinecap="round"/>
      <path d="M70 170c40-55 95-55 140-10 35 35 70 40 120 0" fill="none" stroke="url(#g2)" strokeWidth="6" strokeLinecap="round"/>
      <g transform="translate(120,78)">
        <rect x="0" y="0" width="180" height="110" rx="18" fill="#ffffff" fillOpacity=".92"/>
        <rect x="16" y="18" width="90" height="10" rx="5" fill="#0b3f3f" fillOpacity=".25"/>
        <rect x="16" y="38" width="120" height="16" rx="8" fill="#0b3f3f" fillOpacity=".75"/>
        <rect x="16" y="64" width="70" height="10" rx="5" fill="#2a9d8f" fillOpacity=".5"/>
        <rect x="16" y="82" width="148" height="12" rx="6" fill="#fb923c" fillOpacity=".35"/>
        <circle cx="145" cy="26" r="10" fill="#2a9d8f"/>
      </g>
      <g transform="translate(58,92)">
        <circle cx="28" cy="18" r="14" fill="#fde68a"/>
        <path d="M6 58c2-14 12-22 22-22s20 8 22 22" fill="#fff" fillOpacity=".9"/>
        <rect x="0" y="36" width="56" height="30" rx="12" fill="#fff" fillOpacity=".9"/>
      </g>
      <g transform="translate(300,150)">
        <circle cx="24" cy="14" r="12" fill="#fed7aa"/>
        <path d="M4 50c2-12 10-18 20-18s18 6 20 18" fill="#fff" fillOpacity=".9"/>
        <rect x="0" y="32" width="48" height="26" rx="11" fill="#fff" fillOpacity=".9"/>
      </g>
    </svg>
  )
}

export default function App() {
  const [prefs, setPrefs] = useState<Prefs>({ apiBaseUrl: DEFAULT_API })
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

  useEffect(() => { try { const p = localStorage.getItem(PREFS_KEY); if (p) setPrefs((x) => ({ ...x, ...(JSON.parse(p) as Partial<Prefs>) })) } catch {} }, [])
  useEffect(() => { try { localStorage.setItem(PREFS_KEY, JSON.stringify(prefs)) } catch {} }, [prefs])

  const apiBase = (prefs.apiBaseUrl || DEFAULT_API).replace(/\/$/, '')
  const agent = response?.agent
  const scenarios = agent?.scenarios || []
  const base = scenarios.find((s) => s.name === 'base') || scenarios[0]
  const stress = scenarios.find((s) => s.name && s.name !== 'base') || scenarios[1]
  const curr = base?.currency || agent?.difference?.currency || currency || 'KES'
  const has = scenarios.length > 0
  const baseAmt = base?.amount_received || 0
  const stressAmt = stress?.amount_received || 0
  const diffAmt = agent?.difference?.amount || (baseAmt > stressAmt ? baseAmt - stressAmt : 0)
  const reduction = baseAmt > 0 ? (diffAmt / baseAmt) * 100 : 0
  const stressW = baseAmt > 0 ? Math.max(8, Math.min(100, (stressAmt / baseAmt) * 100)) : 0

  const status = useMemo(() => {
    if (agent?.execution_mode === 'deterministic_fallback' || agent?.is_fallback) return { label: 'Estimación de respaldo', tone: 'bg-amber-100 text-amber-900', note: 'Calculada con datos de referencia (sin ejecutar herramientas en vivo).' }
    if (agent?.degraded) return { label: 'Resultado con aviso', tone: 'bg-amber-100 text-amber-900', note: 'Hay información limitada; revisa la nota de transparencia.' }
    if (agent?.execution_mode === 'llm_tools') return { label: 'Verificado y trazable', tone: 'bg-emerald-100 text-emerald-900', note: 'Cálculo realizado con herramientas y trazabilidad disponible.' }
    return { label: 'Listo para ayudar', tone: 'bg-brand-100 text-brand-900', note: 'Simula un envío y compara el escenario base con una posible caída de tasa.' }
  }, [agent])

  function applyPreset(k: keyof typeof PRESETS) { const p = PRESETS[k]; setMessage(p.message); setAmountEur(p.amountEur); setDestinationCountry(p.destinationCountry); setCurrency(p.currency); setFeeEur(p.feeEur); setScenarioDropPct(p.scenarioDropPct); setError(null) }
  function resetAll() { setMessage(''); setAmountEur('10000'); setDestinationCountry('KE'); setCurrency('KES'); setFeeEur('40'); setScenarioDropPct('3'); setError(null); setResponse(null); setRaw(null); setMeta({}) }
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
      setMeta({ status: r.status, ms: Math.round(performance.now() - t0), reqId: r.headers.get('x-request-id') || r.headers.get('X-Request-ID') })
      const data = await r.json() as ChatResponse & { error?: string; code?: string; details?: unknown }
      setRaw(data)
      if (!r.ok) {
        const details = typeof data.details === 'string' ? data.details : data.details ? JSON.stringify(data.details) : ''
        setError([data.error, data.code, details].filter(Boolean).join(' · ') || 'No se pudo completar la simulación')
      } else setResponse(data)
    } catch (err) { setError(err instanceof Error ? err.message : 'Error de conexión con la API'); setHealth('down') }
    finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen overflow-x-hidden">
      <div className="mx-auto max-w-7xl px-4 py-5 sm:px-6 lg:px-8">
        <nav className="mb-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-brand-700 to-brand-900 text-white shadow-md">FX</div>
            <div><div className="text-sm font-extrabold tracking-tight text-brand-900">Impact FX</div><div className="text-xs text-slate-600">Más fondos llegando a quienes más lo necesitan</div></div>
          </div>
          <div className="flex items-center gap-2">
            <button type="button" onClick={checkHealth} className={`rounded-full px-3 py-1.5 text-xs font-semibold shadow-sm ${health==='ok'?'bg-emerald-100 text-emerald-900':health==='down'?'bg-rose-100 text-rose-800':'bg-white/80 text-slate-700'}`}>● {health==='ok'?'API conectada':health==='down'?'API sin conexión':'Comprobar API'}</button>
            <button type="button" onClick={() => setPrefsOpen(true)} className="rounded-full bg-white/80 px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-sm hover:bg-white">⚙ Preferencias</button>
          </div>
        </nav>

        <section className="relative mb-6 overflow-hidden rounded-[2rem] border border-white/60 bg-white/50 p-6 shadow-xl backdrop-blur sm:p-8">
          <div className="absolute -right-10 -top-10 h-48 w-48 rounded-full bg-brand-500/20 blur-3xl" />
          <div className="absolute -left-10 bottom-0 h-40 w-40 rounded-full bg-coral-400/20 blur-3xl" />
          <div className="grid items-center gap-6 lg:grid-cols-[1.1fr_.9fr]">
            <div className="animate-fade-up">
              <span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${status.tone}`}>{status.label}</span>
              <h1 className="mt-3 text-3xl font-black leading-tight tracking-tight text-brand-950 sm:text-5xl">Haz que cada euro llegue más lejos <span className="bg-gradient-to-r from-brand-700 to-coral-500 bg-clip-text text-transparent">para tu causa</span></h1>
              <p className="mt-3 max-w-xl text-base text-slate-700 sm:text-lg">Simula en segundos cuánto recibirá tu socio local, compara escenarios y anticipa el impacto del tipo de cambio con transparencia.</p>
              <div className="mt-5 flex flex-wrap gap-2">
                {Object.entries(PRESETS).map(([k, p]) => (
                  <button key={k} type="button" onClick={() => applyPreset(k as keyof typeof PRESETS)} className="group rounded-2xl border border-slate-200 bg-white px-4 py-2.5 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-brand-500 hover:shadow-md">
                    <div className="text-sm font-semibold text-slate-900">{p.label}</div><div className="text-xs text-slate-500">{p.hint}</div>
                  </button>
                ))}
              </div>
            </div>
            <div className="animate-floaty mx-auto h-52 w-full max-w-md sm:h-64"><HeroArt /></div>
          </div>
        </section>

        <div className="grid gap-6 lg:grid-cols-[420px_1fr]">
          <form onSubmit={onSubmit} className="space-y-4">
            <section className="rounded-3xl border border-white/70 bg-white/80 p-5 shadow-lg backdrop-blur sm:p-6">
              <div className="mb-4 flex items-center justify-between"><h2 className="text-lg font-bold text-slate-900">Configura tu simulación</h2><button type="button" onClick={resetAll} className="text-xs font-semibold text-brand-700 hover:text-brand-900">Restablecer</button></div>
              <div className="space-y-3">
                <div>
                  <label htmlFor="msg" className="mb-1 block text-sm font-medium text-slate-700">¿Qué quieres saber?</label>
                  <textarea id="msg" rows={3} value={message} onChange={(e) => setMessage(e.target.value)} className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm shadow-sm outline-none transition focus:border-brand-500 focus:ring-4 focus:ring-brand-100" placeholder="Ej: ¿Cuánto recibirá mi socio en Kenia si envío 10.000 EUR?" />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="col-span-2 rounded-2xl bg-gradient-to-r from-brand-50 to-emerald-50 p-3 sm:col-span-1">
                    <label htmlFor="amount" className="mb-1 block text-xs font-semibold text-brand-900">Monto a enviar (EUR)</label>
                    <input id="amount" type="number" min="0" step="0.01" value={amountEur} onChange={(e) => setAmountEur(e.target.value)} className="w-full rounded-xl border-0 bg-white px-3 py-2.5 text-sm font-semibold text-slate-900 shadow-sm ring-1 ring-brand-200 outline-none focus:ring-2 focus:ring-brand-500" />
                  </div>
                  <div className="col-span-2 rounded-2xl bg-gradient-to-r from-amber-50 to-orange-50 p-3 sm:col-span-1">
                    <label htmlFor="drop" className="mb-1 block text-xs font-semibold text-amber-900">Si la tasa cae (%)</label>
                    <input id="drop" type="number" min="0" step="0.1" value={scenarioDropPct} onChange={(e) => setScenarioDropPct(e.target.value)} className="w-full rounded-xl border-0 bg-white px-3 py-2.5 text-sm font-semibold text-slate-900 shadow-sm ring-1 ring-amber-200 outline-none focus:ring-2 focus:ring-coral-400" />
                  </div>
                  <div>
                    <label htmlFor="fee" className="mb-1 block text-xs font-medium text-slate-600">Comisión (EUR)</label>
                    <input id="fee" type="number" min="0" step="0.01" value={feeEur} onChange={(e) => setFeeEur(e.target.value)} className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none focus:border-brand-500 focus:ring-4 focus:ring-brand-100" />
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div><label htmlFor="country" className="mb-1 block text-xs font-medium text-slate-600">País</label><input id="country" value={destinationCountry} onChange={(e) => setDestinationCountry(e.target.value)} className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm uppercase outline-none focus:border-brand-500 focus:ring-4 focus:ring-brand-100" /></div>
                    <div><label htmlFor="curr" className="mb-1 block text-xs font-medium text-slate-600">Moneda</label><input id="curr" value={currency} onChange={(e) => setCurrency(e.target.value)} className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm uppercase outline-none focus:border-brand-500 focus:ring-4 focus:ring-brand-100" /></div>
                  </div>
                </div>
                <button type="submit" disabled={loading || !message.trim()} className="mt-1 inline-flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-brand-700 via-brand-800 to-brand-900 px-5 py-3.5 text-sm font-bold text-white shadow-lg shadow-brand-900/20 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60">
                  {loading ? <><span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white"/> Calculando impacto…</> : 'Calcular impacto para mi proyecto →'}
                </button>
              </div>
              {error && <div className="mt-4 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800"><div className="font-semibold">Ups, necesitamos un ajuste</div><div className="mt-1 break-words">{error}</div><div className="mt-2 text-xs text-rose-700">Consejo: para una simulación completa indica el monto (prueba “✨ Simulación completa”).</div></div>}
            </section>

            <section className="grid grid-cols-3 gap-3">
              {[{t:'Claro',d:'Entiende el resultado en segundos',c:'from-brand-50 to-white'},{t:'Transparente',d:'Fuente, fecha y supuestos visibles',c:'from-emerald-50 to-white'},{t:'Seguro',d:'Solo simula, no ejecuta pagos',c:'from-amber-50 to-white'}].map((x)=>(
                <div key={x.t} className={`rounded-2xl border border-white/70 bg-gradient-to-b ${x.c} p-3 shadow-sm`}><div className="text-sm font-bold text-slate-900">{x.t}</div><div className="mt-1 text-xs text-slate-600">{x.d}</div></div>
              ))}
            </section>
          </form>

          <div className="space-y-4">
            {!has && !error && (
              <section className="animate-fade-up rounded-3xl border border-dashed border-brand-200 bg-white/60 p-8 text-center shadow-sm backdrop-blur">
                <div className="mx-auto mb-3 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-brand-100 to-amber-100 text-3xl">🌍</div>
                <h2 className="text-xl font-bold text-slate-900">Tu resultado aparecerá aquí</h2>
                <p className="mx-auto mt-2 max-w-md text-sm text-slate-600">Verás una comparación visual: cuánto llega en el escenario base y cuánto cambiaría si el tipo de cambio baja, con la información clave para decidir.</p>
              </section>
            )}

            {has && (
              <section className="animate-fade-up overflow-hidden rounded-[2rem] border border-white/70 bg-white/85 shadow-xl backdrop-blur">
                <div className="relative overflow-hidden bg-gradient-to-br from-brand-900 via-brand-800 to-brand-700 p-6 text-white sm:p-7">
                  <div className="absolute -right-16 -top-16 h-56 w-56 rounded-full bg-coral-400/20 blur-3xl" />
                  <div className="absolute -left-10 bottom-0 h-40 w-40 rounded-full bg-brand-500/20 blur-3xl" />
                  <div className="relative grid gap-5 lg:grid-cols-[1.15fr_.85fr]">
                    <div>
                      <div className="inline-flex rounded-full bg-white/15 px-3 py-1 text-xs font-semibold text-brand-50">Estimación para tu socio local</div>
                      <div className="mt-3 flex flex-wrap items-end gap-x-3"><span className="text-5xl font-black tabular-nums tracking-tight sm:text-6xl">{fmt(baseAmt)}</span><span className="pb-1 text-2xl font-bold text-brand-100">{curr}</span></div>
                      <p className="mt-2 text-sm text-brand-100">Escenario base · importe estimado orientativo</p>
                      <div className="mt-5 rounded-2xl bg-white/10 p-4">
                        <div className="mb-2 flex items-center justify-between text-sm"><span className="text-brand-100">Si el tipo de cambio baja {fmt(Number(scenarioDropPct),1)}%</span><span className="font-semibold text-amber-200">-{fmt(diffAmt)} {curr}</span></div>
                        <div className="space-y-2">
                          <div><div className="mb-1 flex justify-between text-xs text-brand-100"><span>Base</span><span>{fmt(baseAmt)} {curr}</span></div><div className="h-3 overflow-hidden rounded-full bg-white/15"><div className="h-full rounded-full bg-gradient-to-r from-emerald-300 to-teal-200" style={{width:'100%'}}/></div></div>
                          <div><div className="mb-1 flex justify-between text-xs text-brand-100"><span>Adverso</span><span>{fmt(stressAmt)} {curr}</span></div><div className="h-3 overflow-hidden rounded-full bg-white/15"><div className="h-full rounded-full bg-gradient-to-r from-amber-300 to-coral-400" style={{width:`${stressW}%`}}/></div></div>
                        </div>
                      </div>
                    </div>
                    <div className="flex flex-col justify-center gap-3">
                      <div className="rounded-2xl bg-white p-4 text-slate-900 shadow-lg">
                        <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">Impacto potencial</div>
                        <div className="mt-1 flex items-end gap-2"><span className="text-4xl font-black tabular-nums text-coral-500">{fmt(reduction,1)}%</span><span className="pb-1 text-sm font-semibold text-slate-600">menos</span></div>
                        <p className="mt-1 text-sm text-slate-600">Equivale a <span className="font-semibold text-slate-900">{fmt(diffAmt)} {curr}</span> que podrían no llegar en un escenario adverso.</p>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="rounded-2xl bg-emerald-400/15 p-3"><div className="text-xs text-brand-100">Tasa base</div><div className="mt-1 text-lg font-bold tabular-nums">{fmt(base?.rate,4)}</div></div>
                        <div className="rounded-2xl bg-amber-400/15 p-3"><div className="text-xs text-brand-100">Tasa adversa</div><div className="mt-1 text-lg font-bold tabular-nums">{fmt(stress?.rate,4)}</div></div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="space-y-4 p-5 sm:p-6">
                  <div className="grid gap-3 sm:grid-cols-3">
                    <div className="rounded-2xl border border-emerald-100 bg-emerald-50 p-4"><div className="text-xs font-semibold text-emerald-800">Llega (base)</div><div className="mt-1 text-xl font-extrabold tabular-nums text-emerald-950">{fmt(baseAmt)} {curr}</div></div>
                    <div className="rounded-2xl border border-amber-100 bg-amber-50 p-4"><div className="text-xs font-semibold text-amber-800">Llegaría (estrés)</div><div className="mt-1 text-xl font-extrabold tabular-nums text-amber-950">{fmt(stressAmt)} {curr}</div></div>
                    <div className="rounded-2xl border border-rose-100 bg-rose-50 p-4"><div className="text-xs font-semibold text-rose-800">Diferencia</div><div className="mt-1 text-xl font-extrabold tabular-nums text-rose-950">-{fmt(diffAmt)} {curr}</div></div>
                  </div>

                  {agent?.budget_impact && (
                    <div className="rounded-2xl border border-brand-100 bg-gradient-to-r from-brand-50 to-white p-4">
                      <div className="flex flex-wrap items-center justify-between gap-2"><div><div className="text-sm font-bold text-brand-950">Impacto en tu presupuesto (demo)</div><div className="text-xs text-slate-600">Cobertura estimada en escenario adverso</div></div><div className="text-2xl font-black text-brand-800 tabular-nums">{fmt(Number(agent.budget_impact.stress_coverage_pct),1)}%</div></div>
                      <div className="mt-3 h-3 overflow-hidden rounded-full bg-slate-200"><div className="h-full rounded-full bg-gradient-to-r from-brand-600 via-brand-500 to-coral-400" style={{width:`${Math.max(0,Math.min(100,Number(agent.budget_impact.stress_coverage_pct)||0))}%`}}/></div>
                      <div className="mt-2 text-xs text-slate-600">Brecha potencial: <span className="font-semibold text-slate-900">{fmt(Number(agent.budget_impact.budget_gap))} {agent.budget_impact.currency || curr}</span></div>
                    </div>
                  )}

                  <div className="rounded-2xl bg-slate-50 p-4">
                    <div className="text-xs font-semibold uppercase tracking-wide text-slate-500">En palabras simples</div>
                    <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">{response?.reply || 'Consulta procesada.'}</p>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-2xl border border-slate-200 p-4"><div className="text-sm font-bold text-slate-900">Transparencia de la tasa</div>
                      {agent?.fx_reference ? <div className="mt-2 space-y-1 text-sm text-slate-700"><div><span className="text-slate-500">Tasa:</span> <span className="font-semibold tabular-nums">{fmt(Number(agent.fx_reference.rate),4)}</span></div><div><span className="text-slate-500">Fuente:</span> {agent.fx_reference.source || '—'}</div><div><span className="text-slate-500">Fecha:</span> {agent.fx_reference.date || '—'}</div><div><span className="inline-flex rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-700">{agent.fx_reference.is_mock ? 'Referencia de demostración' : 'Referencia de mercado'}</span></div></div> : <p className="mt-2 text-sm text-slate-600">No hay referencia de tasa en esta respuesta.</p>}
                    </div>
                    <div className="rounded-2xl border border-slate-200 p-4"><div className="text-sm font-bold text-slate-900">Importante saber</div>
                      <ul className="mt-2 space-y-1.5 text-sm text-slate-700"><li>✓ Estimación orientativa, no cotización firme.</li><li>✓ Esta herramienta no ejecuta pagos.</li><li>✓ Si faltan datos, te los pediremos (sin inventar cifras).</li></ul>
                      {agent?.alerts?.length ? <div className="mt-2 rounded-xl bg-amber-50 p-2 text-xs font-medium text-amber-900">{agent.alerts[0]}</div> : null}
                    </div>
                  </div>
                </div>
              </section>
            )}

            {response && !has && (
              <section className="animate-fade-up rounded-3xl border border-white/70 bg-white/85 p-6 shadow-lg backdrop-blur">
                <div className="text-sm font-bold text-slate-900">Respuesta</div>
                <p className="mt-2 whitespace-pre-wrap text-sm leading-6 text-slate-700">{response.reply || 'Sin respuesta disponible.'}</p>
              </section>
            )}

            <section className="rounded-3xl border border-white/70 bg-white/70 p-4 shadow-sm backdrop-blur">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="text-sm font-semibold text-slate-800">Detalles técnicos <span className="font-normal text-slate-500">(para revisión y soporte)</span></div>
                <div className="flex gap-2">
                  {raw != null && <button type="button" onClick={() => navigator.clipboard.writeText(JSON.stringify(raw, null, 2))} className="rounded-full bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-200">Copiar JSON</button>}
                  <button type="button" onClick={() => setTechOpen((v)=>!v)} className="rounded-full bg-brand-800 px-3 py-1.5 text-xs font-semibold text-white hover:bg-brand-700">{techOpen?'Ocultar':'Mostrar'}</button>
                </div>
              </div>
              {techOpen && (
                <div className="mt-3 space-y-3">
                  <div className="flex flex-wrap gap-2 text-xs text-slate-600"><span className="rounded-full bg-slate-100 px-2 py-1">HTTP {meta.status ?? '—'}</span><span className="rounded-full bg-slate-100 px-2 py-1">{meta.ms != null ? `${meta.ms} ms` : '— ms'}</span>{meta.reqId ? <span className="rounded-full bg-slate-100 px-2 py-1">Req {meta.reqId}</span> : null}{agent?.execution_mode ? <span className="rounded-full bg-slate-100 px-2 py-1">{agent.execution_mode}</span> : null}</div>
                  <pre className="max-h-72 overflow-auto rounded-2xl bg-slate-900 p-4 text-[11px] leading-5 text-emerald-100">{raw != null ? JSON.stringify(raw, null, 2) : 'Sin datos técnicos aún.'}</pre>
                </div>
              )}
            </section>

            <p className="px-2 text-center text-xs text-slate-500">Impact FX ayuda a ONGs a planificar con transparencia. Estimaciones orientativas, sin ejecución de pagos ni cotización firme.</p>
          </div>
        </div>
      </div>

      {prefsOpen && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-brand-950/30 p-4 backdrop-blur-sm" onClick={() => setPrefsOpen(false)}>
          <div className="w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl" onClick={(e)=>e.stopPropagation()}>
            <div className="flex items-center justify-between"><h2 className="text-lg font-bold text-slate-900">Preferencias</h2><button type="button" onClick={() => setPrefsOpen(false)} className="rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-600">Cerrar</button></div>
            <div className="mt-4 space-y-3">
              <div><label htmlFor="pref-api" className="mb-1 block text-sm font-medium text-slate-700">Dirección de la API</label><input id="pref-api" value={prefs.apiBaseUrl} onChange={(e)=>setPrefs({...prefs, apiBaseUrl:e.target.value})} className="w-full rounded-xl border border-slate-200 px-3 py-2.5 text-sm outline-none focus:border-brand-500 focus:ring-4 focus:ring-brand-100" /><p className="mt-1 text-xs text-slate-500">Normalmente {DEFAULT_API}</p></div>
              <div className="rounded-2xl bg-brand-50 p-3 text-sm text-slate-700"><span className="font-semibold text-brand-900">Consejo:</span> si ves “sin conexión”, revisa que el backend esté activo y que CORS permita el origen de esta UI.</div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
