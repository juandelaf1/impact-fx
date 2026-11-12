# Fuente de tipos de cambio

`FX_SOURCE=demo` (valor por defecto) conserva las tasas ficticias locales y no
realiza peticiones externas. `FX_SOURCE=live` consulta la última referencia de
[Frankfurter v2](https://frankfurter.dev/) con un tiempo de espera de 8 segundos.
El backend carga esta opción desde `.env`; al ejecutar la herramienta directamente,
la variable debe estar definida en el entorno.

La respuesta conserva `rate`, `source`, `date` e `is_mock`: una respuesta válida
usa `source=frankfurter` e `is_mock=False`. Son tasas de referencia, no cotizaciones
en tiempo real ni importes de transferencia garantizados.

Si hay un error de red o una respuesta inválida, se emite `RuntimeWarning` y se
busca el mismo par en los datos locales, conservando su fuente, fecha e indicador
`is_mock=True`. Si ese par no existe, se devuelve un error, sin inventar una tasa.
Las consultas con `date` siguen usando exclusivamente los datos locales, incluso
en modo live; no se sustituye una fecha solicitada por la cotización más reciente.
Otros valores de `FX_SOURCE` producen un error de configuración.

Las pruebas de API simulan respuestas y fallos sin depender de internet:
`python -m unittest discover -s tests -v`.
