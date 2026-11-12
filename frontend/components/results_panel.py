import streamlit as st
import plotly.graph_objects as go

def create_impact_donut(stress_amount: float, difference: float):
    """Crea un gráfico de anillo para visualizar la reducción potencial."""

    base_amount = stress_amount + difference

    reduction_pct = (
        (difference / base_amount) * 100
        if base_amount > 0
        else 0
    )

    fig = go.Figure(
        data=[
            go.Pie(
                labels=["Amount received", "Potential reduction"],
                values=[stress_amount, difference],
                hole=0.72,
                marker=dict(
                    colors=["#153B30", "#E5A16F"],
                    line=dict(color="#FFFFFF", width=3)
                ),
                textinfo="none",
                hovertemplate="%{label}: %{value:,.0f}<extra></extra>",
                sort=False
            )
        ]
    )

    fig.add_annotation(
        text=f"<b>{reduction_pct:.1f}%</b><br><span style='font-size:12px'>Potential reduction</span>",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=24, color="#153B30")
    )

    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5
        ),
        margin=dict(t=20, b=60, l=10, r=10),
        height=320,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )

    return fig

def render_results(data: dict, demo_mode: bool = False):
    """Muestra los escenarios y la explicación del agente."""

    agent = data.get("agent", {}) or {}
    scenarios = agent.get("scenarios", [])
    difference = agent.get("difference", {})
    reasoning_summary = agent.get("reasoning_summary", "")
    execution_mode = agent.get("execution_mode")
    degraded = bool(agent.get("degraded", False))
    fx_source = agent.get("fx_source")
    calculation_source = agent.get("calculation_source")

    st.divider()
    st.subheader("Your transfer impact")

    # Modo de ejecución / procedencia (contrato congelado)
    if demo_mode or execution_mode == "frontend_demo":
        st.info("Local demo preview · Illustrative local figures only (no backend/tools execution).")
    elif execution_mode == "deterministic_fallback" or degraded:
        st.warning("Deterministic fallback · Degraded response from demo_scenarios.json (LLM/tool flow not completed).")
    elif execution_mode == "llm_tools":
        st.success("AI + tools · LLM executed tools and backend verified the deterministic calculation.")
    else:
        st.caption("Execution mode: unknown")

    meta_bits = []
    if execution_mode:
        meta_bits.append(f"execution_mode={execution_mode}")
    if fx_source:
        meta_bits.append(f"fx_source={fx_source}")
    if calculation_source:
        meta_bits.append(f"calculation_source={calculation_source}")
    meta_bits.append(f"degraded={str(degraded).lower()}")
    st.caption(" · ".join(meta_bits))

    if fx_source == "demo":
        st.caption("FX source: demo/fixture (fictional reference rate).")
    elif fx_source == "frankfurter":
        st.caption("FX source: Frankfurter (external reference, not a firm quote or executable price).")

    # Explicación del agente
    reply = data.get("reply")
    if reply:
        st.markdown("### Impact FX analysis")
        st.write(reply)

    if reasoning_summary:
        with st.expander("How the result was produced"):
            st.write(reasoning_summary)

    # Resumen de importe enviado, comisión y neto (cuando hay escenarios)
    if len(scenarios) >= 1:
        s0 = scenarios[0] or {}
        fee = s0.get("fee_eur")
        rate = s0.get("rate")
        currency = s0.get("currency", "")
        amount_received = float(s0.get("amount_received", 0) or 0)
        try:
            net_amount_eur = (amount_received / float(rate)) if rate else None
        except Exception:
            net_amount_eur = None
        amount_sent = (float(net_amount_eur) + float(fee)) if (net_amount_eur is not None and fee is not None) else None
        info_cols = st.columns(4)
        with info_cols[0]:
            if amount_sent is not None:
                st.metric("Amount sent (EUR)", f"{amount_sent:,.2f}")
        with info_cols[1]:
            if fee is not None:
                st.metric("Transfer fee (EUR)", f"{float(fee):,.2f}")
        with info_cols[2]:
            if net_amount_eur is not None:
                st.metric("Net amount to convert (EUR)", f"{net_amount_eur:,.2f}")
        with info_cols[3]:
            if currency:
                st.metric("Destination currency", currency)

    # Tarjetas de escenarios
    if len(scenarios) >= 2:
        cols = st.columns(2)
        for index, scenario in enumerate(scenarios[:2]):
            with cols[index]:
                is_base = scenario.get("name") == "base"
                if is_base:
                    label = "Base scenario"
                    description = "Reference exchange rate"
                else:
                    label = "Stress scenario"
                    description = "Exchange rate under adverse conditions"

                st.markdown(f"#### {label}")
                st.caption(description)

                st.metric(
                    label=f"Amount received ({scenario.get('currency', '')})",
                    value=f"{float(scenario.get('amount_received', 0) or 0):,.0f}",
                    delta=(f"{float(scenario.get('rate', 0) or 0):,.2f} local currency / EUR"),
                    delta_color="off",
                )

                st.caption(f"Transfer fee: {float(scenario.get('fee_eur', 0) or 0):,.2f} EUR")

    # Impacto presupuestario (si está disponible y verificado en respuesta)
    budget_impact = agent.get("budget_impact")
    if budget_impact and isinstance(budget_impact, dict):
        st.markdown("### Project budget impact")
        b1, b2, b3, b4 = st.columns(4)
        b1.metric("Project budget (KES)", f"{float(budget_impact.get('budget_total', 0) or 0):,.0f}")
        b2.metric("Base coverage", f"{float(budget_impact.get('base_coverage_pct', 0) or 0):,.2f}%")
        b3.metric("Stress coverage", f"{float(budget_impact.get('stress_coverage_pct', 0) or 0):,.2f}%")
        b4.metric("Potential funding gap (KES)", f"{float(budget_impact.get('budget_gap', 0) or 0):,.0f}")
        st.caption(
            "Under this illustrative stress scenario, available funds would cover "
            f"{float(budget_impact.get('stress_coverage_pct', 0) or 0):.0f}% of the sample project budget, "
            f"leaving a potential funding gap of {float(budget_impact.get('budget_gap', 0) or 0):,.0f} KES. "
            "This does not attribute the shortfall to specific budget items and is not an actual loss."
        )
        if budget_impact.get("is_synthetic_demo"):
            st.caption("Budget shown is synthetic/demo data (KE-HEALTH-001).")

    st.caption("Estimate only (not a firm quote). Potential difference, not an actual loss. Simulation only — no payment is executed.")

         # Impact comparison: explanation + compact donut
    if len(scenarios) >= 2:
        base_scenario = next(
            (s for s in scenarios if s.get("name") == "base"),
            scenarios[0]
        )

        stress_scenario = next(
            (s for s in scenarios if s.get("name") != "base"),
            scenarios[1]
        )

        stress_amount = stress_scenario.get("amount_received", 0)
        difference_amount = difference.get("amount", 0)
        currency = difference.get("currency", "")

        col_info, col_chart = st.columns([1.8, 1], gap="large")

        with col_info:
            st.markdown("### What could this mean for your project?")

            st.warning(
                f"In the stress scenario, your project could receive "
                f"{difference_amount:,.0f} {currency} less than "
                f"in the base scenario."
            )

            st.caption(
                "This illustrates how exchange rate fluctuations "
                "could affect the funds available to your local partner."
            )

        with col_chart:
            with st.container(border=True):
                st.markdown("#### Potential impact")

                fig = create_impact_donut(
                    stress_amount=stress_amount,
                    difference=difference_amount
                )

                fig.update_layout(
                    height=230,
                    margin=dict(t=5, b=35, l=5, r=5),
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.18,
                        xanchor="center",
                        x=0.5,
                        font=dict(size=9)
                    )
                )

                fig.update_traces(
                    textinfo="none",
                    hovertemplate="%{label}: %{value:,.0f} "
                    f"{currency}<extra></extra>"
                )

                st.plotly_chart(
                    fig,
                    use_container_width=True,
                    config={"displayModeBar": False}
                )

                st.caption(
                    "Potential reduction, not probability of loss."
                )

    # Supuestos
    assumptions = agent.get("assumptions", [])

    if assumptions:
        with st.expander("Calculation assumptions"):
            for assumption in assumptions:
                st.write(f"• {assumption}")

    # Herramientas utilizadas (solo ejecuciones reales)
    tools_used = agent.get("tools_used", [])
    fx_reference = agent.get("fx_reference")
    is_fallback = agent.get("is_fallback")
    with st.expander("Execution details"):
        st.write(f"Execution mode: {execution_mode or 'n/a'}")
        st.write(f"Degraded: {str(degraded).lower()}")
        st.write(f"Is fallback: {str(bool(is_fallback)).lower() if is_fallback is not None else 'n/a'}")
        st.write(f"FX source: {fx_source or 'n/a'}")
        st.write(f"Calculation source: {calculation_source or 'n/a'}")
        if isinstance(fx_reference, dict):
            st.write(
                "FX reference: "
                f"rate={fx_reference.get('rate')}, source={fx_reference.get('source')}, "
                f"date={fx_reference.get('date')}, is_mock={str(fx_reference.get('is_mock')).lower()}"
            )
        else:
            st.write("FX reference: none")
        if tools_used:
            st.write("Tools executed successfully:")
            for tool in tools_used:
                st.write(f"• {tool}")
        else:
            st.write("Tools executed successfully: none")

    # Alertas
    alerts = agent.get("alerts", [])
    if alerts:
        st.markdown("### Important alerts")
        for alert in alerts:
            st.warning(alert)
