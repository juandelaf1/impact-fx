import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


# Añadimos la raíz del proyecto para poder importar nuestras funciones.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from backend.src.tools.get_fx_reference import get_fx_reference
from backend.src.tools.calculate_transfer_scenarios import (
    calculate_transfer_scenarios,
)


# Cargamos la configuración privada sin mostrar la clave.
load_dotenv(PROJECT_ROOT / ".env", override=True)

api_key = os.getenv("LLM_API_KEY")
model = os.getenv("LLM_MODEL")

if not api_key or not model:
    raise ValueError("Configura LLM_API_KEY y LLM_MODEL en .env.")

client = Groq(api_key=api_key)

# Leemos las instrucciones que hemos preparado para el agente.
agent_dir = PROJECT_ROOT / "backend" / "src" / "agent"
system_prompt = (agent_dir / "system_prompt.txt").read_text(
    encoding="utf-8"
)

# Leemos las definiciones y las adaptamos al formato de Groq.
definitions = json.loads(
    (agent_dir / "tool_definitions.json").read_text(encoding="utf-8")
)
tools = [
    {"type": "function", "function": definition}
    for definition in definitions
]

# Solo permitimos ejecutar estas dos funciones.
# Nunca ejecutamos código arbitrario generado por el modelo.
available_functions = {
    "get_fx_reference": get_fx_reference,
    "calculate_transfer_scenarios": calculate_transfer_scenarios,
}

# La cobertura se limita explícitamente al caso de esta prueba.
# No sustituye la matriz definitiva que está preparando José.
messages = [
    {"role": "system", "content": system_prompt},
    {
        "role": "system",
        "content": (
            "Configuración de esta prueba: corredor cubierto EUR→KES, "
            "destino KE (Kenia). Usa los fixtures locales de demo. "
            "Las tasas son ficticias. La comisión la aporta el usuario."
        ),
    },
{
    "role": "user",
    "content": "Quiero enviar dinero a Kenia para un proyecto de salud.",
},
]

# Guardamos las llamadas reales para comprobar qué ha ejecutado.
executed_tools = []
calculation_result = None
final_reply = None

# Limitamos las rondas para evitar un bucle sin fin.
for round_number in range(8):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        max_tokens=2048,
    )

    message = response.choices[0].message

    # Si no pide herramientas, esperamos una respuesta final con texto.
    if not message.tool_calls:
        if not message.content:
            raise RuntimeError(
                "El modelo no devolvió texto. Motivo: "
                f"{response.choices[0].finish_reason}"
            )

        final_reply = message.content
        break

    # Conservamos la petición del modelo antes de añadir los resultados.
    messages.append(
        message.model_dump(
            include={"role", "content", "tool_calls"},
            exclude_none=True,
        )
    )

    for call in message.tool_calls:
        name = call.function.name
        arguments = json.loads(call.function.arguments)

        print(f"\nHerramienta solicitada: {name}")
        print("Parámetros:", arguments)

        if name not in available_functions:
            raise RuntimeError(f"Herramienta no permitida: {name}")

        # Ejecutamos la función de Python con los parámetros solicitados.
        result = available_functions[name](**arguments)
        executed_tools.append(name)

        if name == "calculate_transfer_scenarios":
            calculation_result = result

        print("Resultado:", json.dumps(result, ensure_ascii=False))

        # Devolvemos el resultado al modelo para que pueda continuar.
        messages.append(
            {
                "role": "tool",
                "tool_call_id": call.id,
                "content": json.dumps(result, ensure_ascii=False),
            }
        )

if final_reply is None:
    raise RuntimeError("Se alcanzó el límite de rondas sin respuesta final.")

# Sin importe, el agente no debe ejecutar el cálculo.
assert "calculate_transfer_scenarios" not in executed_tools, (
    "El agente calculó sin disponer del importe."
)

print("\nRESPUESTA FINAL:\n")
print(final_reply)
print("\nOK: no se ha ejecutado el cálculo sin importe.")