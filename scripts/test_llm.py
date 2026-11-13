import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

# Buscamos el .env en la raíz del proyecto.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

# Leemos la clave y el modelo sin mostrarlos en pantalla.
api_key = os.getenv("LLM_API_KEY")
model = os.getenv("LLM_MODEL")

if not api_key or not model:
    raise ValueError("Falta configurar LLM_API_KEY o LLM_MODEL en .env")

# Creamos la conexión con Groq usando nuestra clave.
client = Groq(api_key=api_key)

# Enviamos una petición corta para comprobar la conexión.
response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "user",
            "content": "Responde únicamente: Conexión correcta",
        }
    ],
    max_tokens=2048,
)

# repr permite distinguir una respuesta vacía de una respuesta con texto.
print("Respuesta:", repr(response.choices[0].message.content))

# Indica si terminó normalmente o si agotó los tokens disponibles.
print("Motivo de finalización:", response.choices[0].finish_reason)
