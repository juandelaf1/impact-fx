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

    agent = data.get("agent", {})
    scenarios = agent.get("scenarios", [])
    difference = agent.get("difference", {})
    reasoning_summary = agent.get("reasoning_summary", "")
    
    st.divider()

    st.subheader("Your transfer impact")

    if demo_mode:
        st.info(
            "Demo preview · These are illustrative figures, "
            "not results from the live backend."
        )

    # Explicación del agente
    reply = data.get("reply")

    if reply:
        st.markdown("### Impact FX analysis")
        st.write(reply)

    if reasoning_summary:
        with st.expander("How the AI agent reached its conclusions"):
            st.write(reasoning_summary)

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
                    value=f"{scenario.get('amount_received', 0):,.0f}",
                    delta=(
                        f"{scenario.get('rate', 0):,.2f} "
                        "local currency / EUR"
                    ),
                    delta_color="off"
                )

                st.caption(
                    f"Transfer fee: {scenario.get('fee_eur', 0):,.2f} EUR"
                )

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

    # Herramientas utilizadas
    tools_used = agent.get("tools_used", [])

    if tools_used:
        with st.expander("AI agent tools used"):
            for tool in tools_used:
                st.write(f"• {tool}")

    # Alertas
    alerts = agent.get("alerts", [])

    if alerts:
        st.markdown("### Important alerts")

        for alert in alerts:
            st.warning(alert)
