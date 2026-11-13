import html

import plotly.graph_objects as go
import streamlit as st


def _safe(value: object) -> str:
    """Escapa un valor antes de insertarlo en HTML (unsafe_allow_html)."""

    return html.escape(str(value if value is not None else ""))


def create_impact_donut(stress_amount: float, difference: float, currency: str = ""):
    """Crea un gráfico de anillo para visualizar la reducción potencial."""

    stress_amount = float(stress_amount or 0)
    difference = float(difference or 0)
    base_amount = stress_amount + difference

    reduction_pct = (difference / base_amount) * 100 if base_amount > 0 else 0

    fig = go.Figure(
        data=[
            go.Pie(
                labels=["Importe recibido", "Reducción potencial"],
                values=[stress_amount, difference],
                hole=0.72,
                marker={"colors": ["#153B30", "#E5A16F"], "line": {"color": "#FFFFFF", "width": 3}},
                textinfo="none",
                hovertemplate=(f"%{{label}}: %{{value:,.0f}} {currency}<extra></extra>"),
                sort=False,
            )
        ]
    )

    fig.add_annotation(
        text=(
            f"<b>{reduction_pct:.1f}%</b>"
            "<br><span style='font-size:12px'>Reducción potencial</span>"
        ),
        x=0.5,
        y=0.5,
        showarrow=False,
        font={"size": 19, "color": "#153B30"},
    )

    fig.update_layout(
        showlegend=True,
        legend={"orientation": "h", "yanchor": "bottom", "y": -0.15, "xanchor": "center", "x": 0.5},
        margin={"t": 20, "b": 60, "l": 10, "r": 10},
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig


def render_results(data: dict, demo_mode: bool = False):
    """Muestra los escenarios, su impacto y la explicación del agente."""

    agent = data.get("agent", {}) or {}
    scenarios = agent.get("scenarios", []) or []
    difference = agent.get("difference", {}) or {}
    reasoning_summary = agent.get("reasoning_summary", "")
    execution_mode = agent.get("execution_mode")
    degraded = bool(agent.get("degraded", False))
    fx_source = agent.get("fx_source")
    calculation_source = agent.get("calculation_source")
    reply = data.get("reply", "")

    st.divider()
    st.subheader("El impacto de tu transferencia")

    # Modo de ejecución y procedencia de los datos.
    if demo_mode or execution_mode == "frontend_demo":
        st.info(
            "Vista de demostración · Cifras orientativas generadas localmente; "
            "no proceden del backend conectado."
        )
    elif execution_mode == "deterministic_fallback" or degraded:
        st.warning(
            "Modo alternativo · Respuesta de respaldo. "
            "El flujo completo de IA y herramientas no ha finalizado."
        )
    elif execution_mode == "llm_tools":
        st.success(
            "IA + herramientas · El agente ha ejecutado las herramientas "
            "y el backend ha verificado el cálculo."
        )
    else:
        st.caption("Modo de ejecución: no disponible")

    meta_bits = []
    if execution_mode:
        meta_bits.append(f"modo={execution_mode}")
    if fx_source:
        meta_bits.append(f"fuente_tipo_cambio={fx_source}")
    if calculation_source:
        meta_bits.append(f"fuente_calculo={calculation_source}")
    meta_bits.append(f"respaldo={str(degraded).lower()}")
    st.caption(" · ".join(meta_bits))

    if fx_source == "demo":
        st.caption("Tipo de cambio: datos de demostración (tipo de referencia ficticio).")
    elif fx_source == "frankfurter":
        st.caption(
            "Tipo de cambio: Frankfurter (referencia externa; "
            "no es una cotización bancaria vinculante ni un precio ejecutable)."
        )

    if reply:
        with st.expander("Análisis de Impact FX"):
            st.write(reply)

    if not scenarios:
        if reasoning_summary:
            with st.expander("Resumen de ejecución del agente"):
                st.write(reasoning_summary)
        return

    # Datos del escenario base y del escenario adverso.
    base_scenario = next(
        (scenario for scenario in scenarios if scenario.get("name") == "base"), scenarios[0]
    )
    stress_scenario = next(
        (scenario for scenario in scenarios if scenario.get("name") != "base"),
        scenarios[1] if len(scenarios) > 1 else scenarios[0],
    )

    base_amount = float(base_scenario.get("amount_received", 0) or 0)
    stress_amount = float(stress_scenario.get("amount_received", 0) or 0)
    currency = base_scenario.get("currency", "")
    safe_currency = _safe(currency)
    difference_amount = float(difference.get("amount", 0) or 0)

    reduction_pct = (difference_amount / base_amount) * 100 if base_amount > 0 else 0

    fee = base_scenario.get("fee_eur")
    rate = base_scenario.get("rate")

    try:
        net_amount_eur = base_amount / float(rate) if rate and float(rate) > 0 else None
    except (TypeError, ValueError, ZeroDivisionError):
        net_amount_eur = None

    amount_sent = (
        net_amount_eur + float(fee) if net_amount_eur is not None and fee is not None else None
    )

    # Resumen de importes.
    info_cols = st.columns(4)
    with info_cols[0]:
        if amount_sent is not None:
            st.metric("Importe enviado (EUR)", f"{amount_sent:,.2f}")
    with info_cols[1]:
        if fee is not None:
            st.metric("Comisión (EUR)", f"{float(fee):,.2f}")
    with info_cols[2]:
        if net_amount_eur is not None:
            st.metric("Importe neto a convertir (EUR)", f"{net_amount_eur:,.2f}")
    with info_cols[3]:
        if currency:
            st.metric("Moneda de destino", currency)

    # Resultado principal: se conserva el selector CSS de la tarjeta.
    st.markdown("### Importe estimado que recibirá la entidad colaboradora")

    with st.container(border=True, key="impact_primary_card"):
        st.markdown('<div class="impact-primary-value"></div>', unsafe_allow_html=True)
        st.caption("IMPORTE ESTIMADO PARA LA ENTIDAD COLABORADORA")

        st.markdown(
            f"""
            <div style="font-size: 2.8rem; font-weight: 750;
                        color: #176B57; line-height: 1.2;">
                {base_amount:,.0f}
                <span style="font-size: 1.2rem;">{safe_currency}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.caption(
            "Importe estimado tras descontar la comisión y aplicar el tipo de cambio de referencia."
        )

        st.divider()
        st.markdown("**Cómo se calcula**")

        calculation_col1, calculation_col2 = st.columns(2)
        with calculation_col1:
            if amount_sent is not None:
                st.metric("Importe enviado", f"{amount_sent:,.2f} EUR")
        with calculation_col2:
            if fee is not None:
                st.metric("Comisión de transferencia", f"−{float(fee):,.2f} EUR")

        if net_amount_eur is not None and rate:
            st.markdown(f"**{net_amount_eur:,.2f} EUR** × **{float(rate):,.2f} {currency}/EUR**")

    # Escenario adverso: se distingue claramente del resultado principal.
    if len(scenarios) >= 2:
        st.markdown("### ¿Qué ocurre si baja el tipo de cambio?")

        with st.container(border=True, key="impact_risk_card"):
            st.markdown('<div class="impact-risk-marker"></div>', unsafe_allow_html=True)
            st.caption("ESCENARIO ADVERSO · HIPOTÉTICO")

            stress_col1, stress_col2 = st.columns(2)
            with stress_col1:
                st.metric("Importe recibido", f"{stress_amount:,.0f} {currency}")
            with stress_col2:
                st.metric(
                    "Reducción respecto al escenario base",
                    f"−{difference_amount:,.0f} {currency}",
                    delta=f"−{reduction_pct:.2f}%",
                    delta_color="inverse",
                )

            st.caption(
                "Este es un escenario adverso hipotético, no el importe que se espera recibir."
            )

        # Impacto presupuestario, si el backend proporciona estos datos.
        budget_impact = agent.get("budget_impact")
        if isinstance(budget_impact, dict):
            st.markdown("### Impacto económico potencial")
            col_impact, col_chart = st.columns([1.5, 1], gap="medium")

            with col_impact, st.container(border=True):
                st.caption("REDUCCIÓN DEL PRESUPUESTO DISPONIBLE")
                st.metric(
                    label="Reducción potencial del presupuesto",
                    value=f"{reduction_pct:.1f}%",
                    delta="Respecto al escenario base",
                    delta_color="inverse",
                )
                st.write(
                    "Un tipo de cambio menos favorable reduciría "
                    "el poder adquisitivo de los fondos recibidos "
                    "por la entidad colaboradora."
                )
                st.caption(
                    "Conviene contemplar un margen de contingencia "
                    "al planificar las actividades y los gastos locales."
                )

            with col_chart, st.container(border=True):
                st.markdown("**Comparación de escenarios**")
                fig = create_impact_donut(
                    stress_amount=stress_amount, difference=difference_amount, currency=currency
                )
                fig.update_layout(
                    height=185,
                    margin={"t": 0, "b": 35, "l": 5, "r": 5},
                    legend={
                        "orientation": "h",
                        "yanchor": "bottom",
                        "y": -0.22,
                        "xanchor": "center",
                        "x": 0.5,
                        "font": {"size": 8},
                    },
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                st.caption(
                    "Muestra la posible reducción de fondos, "
                    "no la probabilidad de que se produzca este escenario."
                )

            b1, b2, b3, b4 = st.columns(4)
            b1.metric(
                "Presupuesto del proyecto (KES)",
                f"{float(budget_impact.get('budget_total', 0) or 0):,.0f}",
            )
            b2.metric(
                "Cobertura base", f"{float(budget_impact.get('base_coverage_pct', 0) or 0):,.2f}%"
            )
            b3.metric(
                "Cobertura adversa",
                f"{float(budget_impact.get('stress_coverage_pct', 0) or 0):,.2f}%",
            )
            b4.metric(
                "Déficit potencial (KES)", f"{float(budget_impact.get('budget_gap', 0) or 0):,.0f}"
            )

            st.caption(
                "En este escenario hipotético, los fondos disponibles cubrirían "
                f"el {float(budget_impact.get('stress_coverage_pct', 0) or 0):.0f}% "
                "del presupuesto de ejemplo, con un déficit potencial de "
                f"{float(budget_impact.get('budget_gap', 0) or 0):,.0f} KES. "
                "No se atribuye el déficit a partidas concretas ni representa "
                "una pérdida real."
            )
            if budget_impact.get("is_synthetic_demo"):
                st.caption(
                    "El presupuesto mostrado utiliza datos sintéticos/de demostración (KE-HEALTH-001)."
                )

    st.caption(
        "Estimación orientativa, no una oferta vinculante. "
        "La diferencia es potencial, no una pérdida real. "
        "Es una simulación: no se ejecuta ningún pago."
    )

    # Supuestos, herramientas y trazabilidad de la ejecución.
    assumptions = agent.get("assumptions", [])
    tools_used = agent.get("tools_used", [])

    if assumptions or tools_used or reasoning_summary:
        with st.expander("Detalles del cálculo y metodología"):
            if assumptions:
                st.markdown("**Supuestos del cálculo**")
                for assumption in assumptions:
                    st.write(f"• {assumption}")

            if tools_used:
                st.markdown("**Herramientas utilizadas**")
                for tool in tools_used:
                    st.write(f"• {tool}")

            if reasoning_summary:
                st.markdown("**Resumen de ejecución del agente**")
                st.write(reasoning_summary)

    # Alertas importantes.
    alerts = agent.get("alerts", [])
    if alerts:
        st.markdown("### Avisos importantes")
        for alert in alerts:
            st.warning(alert)
