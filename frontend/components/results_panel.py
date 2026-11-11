import streamlit as st


def render_results(data: dict, demo_mode: bool = False):
    """Muestra los escenarios y la explicación del agente."""

    agent = data.get("agent", {})
    scenarios = agent.get("scenarios", [])
    difference = agent.get("difference", {})
    
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

    # Tarjetas de escenarios
    if len(scenarios) >= 2:
        cols = st.columns(2)

        for index, scenario in enumerate(scenarios[:2]):
            with cols[index]:
                is_base = scenario.get("name") == "base"

                label = "Base scenario" if is_base else "Stress scenario"

                st.markdown(f"#### {label}")

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

    # Diferencia entre escenarios
    if difference:
        st.markdown("### Potential impact difference")

        amount = difference.get("amount", 0)
        currency = difference.get("currency", "")

        st.metric(
            label="Difference between scenarios",
            value=f"{amount:,.0f} {currency}",
            delta="Potential amount lost",
            delta_color="inverse"
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
