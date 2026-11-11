import streamlit as st
from pathlib import Path

from services.api import send_chat_message, check_api_health, APIError
from services.demo_data import get_demo_response
from components.results_panel import render_results


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Impact FX",
    page_icon="🌍",
    layout="wide"
)


# --------------------------------------------------
# LOAD CUSTOM CSS
# --------------------------------------------------

CSS_PATH = Path(__file__).parent / "styles" / "custom.css"

if CSS_PATH.exists():
    with open(CSS_PATH, encoding="utf-8") as css_file:
        st.markdown(
            f"<style>{css_file.read()}</style>",
            unsafe_allow_html=True
        )


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.markdown(
    """
    <div class="main-header">
        <p class="eyebrow">FINANCIAL TRANSPARENCY FOR SOCIAL IMPACT</p>
        <h1>Impact <span>FX</span></h1>
        <p class="subtitle">
            Make every transfer count.
            Understand how exchange rates affect your project's impact.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# TRANSFER FORM
# --------------------------------------------------

st.subheader("Calculate your transfer impact")

st.write(
    "Explore how much money your local partner could receive "
    "and how exchange rate fluctuations may affect your project."
)

st.markdown("### Transfer details")

with st.form("transfer_form"):

    col1, col2 = st.columns(2)

    with col1:
        amount_eur = st.number_input(
            "Transfer amount (€)",
            min_value=1.0,
            value=10000.0,
            step=500.0
        )

        destination = st.selectbox(
            "Destination country",
            options=["Kenya"]
        )

    with col2:
        fee_eur = st.number_input(
            "Transfer fee (€)",
            min_value=0.0,
            value=40.0,
            step=5.0
        )

        scenario_drop_pct = st.slider(
            "Exchange rate drop (%)",
            min_value=0.0,
            max_value=20.0,
            value=3.0,
            step=0.5
        )

    submitted = st.form_submit_button(
        "Calculate impact",
        use_container_width=True,
        type="primary"
    )


# --------------------------------------------------
# PROCESS TRANSFER
# --------------------------------------------------

if submitted and fee_eur >= amount_eur:
    st.session_state.pop("results", None)
    st.session_state.pop("demo_mode", None)
    st.session_state.pop("connection_error", None)
    st.error(
        "The transfer fee must be lower than the transfer amount."
    )

if submitted and fee_eur < amount_eur:

    context = {
        "amount_eur": amount_eur,
        "destination_country": "KE",
        "currency": "KES",
        "fee_eur": fee_eur,
        "scenario_drop_pct": scenario_drop_pct
    }

    message = (
        f"Estimate the impact of transferring {amount_eur} EUR "
        f"to Kenya for a social impact project."
    )

    with st.spinner("Analyzing your transfer..."):

        if check_api_health():

            try:
                response_data = send_chat_message(
                    message=message,
                    context=context
                )

                st.session_state["results"] = response_data
                st.session_state["demo_mode"] = False
                st.session_state.pop("connection_error", None)

            except APIError as error:
                st.session_state.pop("results", None)
                st.session_state["connection_error"] = str(error)

        else:
            st.session_state["results"] = get_demo_response(
                amount_eur=amount_eur,
                fee_eur=fee_eur,
                scenario_drop_pct=scenario_drop_pct
            )

            st.session_state["demo_mode"] = True
            st.session_state.pop("connection_error", None)


# --------------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------------

if st.session_state.get("connection_error"):
    st.error(
        f"Could not process the transfer: "
        f"{st.session_state['connection_error']}"
    )

if st.session_state.get("results"):

    render_results(
        st.session_state["results"],
        demo_mode=st.session_state.get("demo_mode", False)
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Impact FX provides illustrative estimates for informational purposes. "
    "Exchange rates and fees are not guaranteed. No payments are executed."
)
