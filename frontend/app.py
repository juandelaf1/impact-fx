import streamlit as st
from pathlib import Path

from services.api import send_chat_message, check_api_health, APIError
from services.demo_data import get_demo_response
from components.results_panel import render_results


# --------------------------------------------------
# CONFIGURACIÓN DE LA PÁGINA
# --------------------------------------------------

st.set_page_config(
    page_title="Impact FX",
    page_icon="🌍",
    layout="wide"
)


# --------------------------------------------------
# CARGA DE ESTILOS CSS
# --------------------------------------------------

CSS_PATH = Path(__file__).parent / "styles" / "custom.css"

if CSS_PATH.exists():
    with open(CSS_PATH, encoding="utf-8") as css_file:
        st.markdown(
            f"<style>{css_file.read()}</style>",
            unsafe_allow_html=True
        )


# --------------------------------------------------
# CABECERA
# --------------------------------------------------

st.markdown(
    """
    <div class="main-header">
        <p class="eyebrow">TRANSPARENCIA FINANCIERA PARA PROYECTOS DE IMPACTO SOCIAL</p>
        <h1>Impact <span>FX</span></h1>
        <p class="subtitle">
            Cada transferencia cuenta.
            Comprende cómo las fluctuaciones del tipo de cambio afectan al impacto de tu proyecto.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# --------------------------------------------------
# FORMULARIO DE TRANSFERENCIA
# --------------------------------------------------

st.subheader("Calcula el impacto de tu transferencia")

st.write(
    "Descubre cuánto dinero podría recibir tu entidad colaboradora "
    "y cómo las variaciones del tipo de cambio pueden afectar a tu proyecto."
)

st.markdown("### Datos de la transferencia")

with st.form("transfer_form"):

    col1, col2 = st.columns(2)

    with col1:
        amount_eur = st.number_input(
            "Importe de la transferencia (€)",
            min_value=1.0,
            value=10000.0,
            step=500.0
        )

        destination = st.selectbox(
            "País de destino",
            options=["Kenya"]
        )

    with col2:
        fee_eur = st.number_input(
            "Comisión de transferencia (€)",
            min_value=0.0,
            value=40.0,
            step=5.0
        )

        scenario_drop_pct = st.slider(
            "Caída del tipo de cambio (%)",
            min_value=0.0,
            max_value=20.0,
            value=3.0,
            step=0.5
        )

    submitted = st.form_submit_button(
        "Calcular impacto",
        use_container_width=True,
        type="primary"
    )


# --------------------------------------------------
# PROCESAMIENTO DE LA TRANSFERENCIA
# --------------------------------------------------

if submitted and fee_eur >= amount_eur:
    st.session_state.pop("results", None)
    st.session_state.pop("demo_mode", None)
    st.session_state.pop("connection_error", None)
    st.session_state.pop("connection_error_status", None)
    st.error("La comisión debe ser inferior al importe de la transferencia.")

if submitted and fee_eur < amount_eur:

    context = {
        "amount_eur": amount_eur,
        "destination_country": "KE",
        "currency": "KES",
        "fee_eur": fee_eur,
        "scenario_drop_pct": scenario_drop_pct
    }

    # El mensaje interno para el agente se mantiene en inglés.
    message = (
        f"Estimate the impact of transferring {amount_eur} EUR "
        f"to Kenya for a social impact project."
    )

    with st.spinner("Analizando tu transferencia..."):

        if check_api_health():

            try:
                response_data = send_chat_message(
                    message=message,
                    context=context
                )

                st.session_state["results"] = response_data
                st.session_state["demo_mode"] = False
                st.session_state.pop("connection_error", None)
                st.session_state.pop("connection_error_status", None)

            except APIError as error:
                st.session_state.pop("results", None)
                st.session_state.pop("demo_mode", None)
                st.session_state["connection_error"] = str(error)
                st.session_state["connection_error_status"] = getattr(
                    error, "status_code", None
                )

        else:
            st.session_state["results"] = get_demo_response(
                amount_eur=amount_eur,
                fee_eur=fee_eur,
                scenario_drop_pct=scenario_drop_pct
            )

            st.session_state["demo_mode"] = True
            st.session_state.pop("connection_error", None)
            st.session_state.pop("connection_error_status", None)


# --------------------------------------------------
# VISUALIZACIÓN DE RESULTADOS
# --------------------------------------------------

if st.session_state.get("connection_error"):
    status = st.session_state.get("connection_error_status")
    msg = st.session_state["connection_error"]

    if status == 422:
        st.warning(f"Faltan datos: {msg}")
        st.info(
            "Proporciona la información que falta (por ejemplo, el importe, "
            "la moneda de destino o la comisión) e inténtalo de nuevo. "
            "No se estimarán cifras sin los datos necesarios."
        )
    elif status == 400:
        st.error(f"Datos no válidos: {msg}")
    elif status == 502:
        st.error(f"Error del servicio: {msg}")
    else:
        st.error(f"No se ha podido procesar la transferencia: {msg}")

if st.session_state.get("results"):
    render_results(
        st.session_state["results"],
        demo_mode=st.session_state.get("demo_mode", False)
    )


# --------------------------------------------------
# PIE DE PÁGINA
# --------------------------------------------------

st.divider()

st.caption(
    "Impact FX ofrece estimaciones orientativas con fines informativos. "
    "Los tipos de cambio y las comisiones pueden variar. "
    "No se ejecutan pagos."
)
