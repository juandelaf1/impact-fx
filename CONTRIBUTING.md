# Contribuir a Impact FX

Gracias por querer mejorar el proyecto. Esta guía resume el flujo de trabajo, las puertas de calidad y las reglas de contrato.

## Flujo de trabajo

1. **Rama**: crea una rama desde `main` con el prefijo `feat/`, `fix/` o `docs/` (`feat/nombre-corto`).
2. **Cambio pequeño y verificable**: una PR = un objetivo. Si toca backend y frontend, divídelo.
3. **Antes de abrir la PR**, ejecuta las puertas de calidad (§2).
4. **PR**: usa la plantilla (`.github/pull_request_template.md`) y enlaza el ítem de backlog o la issue.
5. **CI en verde** antes de pedir revisión (7 jobs: datos, lint, tipado, tests+cobertura, smoke, seguridad, Docker).

## Puertas de calidad (obligatorias)

```bash
pytest tests -q                                          # 46 tests
coverage run --source=backend,frontend -m pytest tests -q && coverage report
ruff check . && ruff format --check .                    # lint + formato
mypy backend                                             # tipado estático
node scripts/validate-data.mjs                           # si tocas data/
```

O, de golpe, con los hooks locales:

```bash
pip install -r dev-requirements.txt
pre-commit install
pre-commit run --all-files
```

## Reglas del contrato

- El contrato público está **congelado** (`docs/api-contract.md`, `shared/contracts/contracts.md`).
- Cualquier cambio de contrato actualiza **en la misma PR**: la documentación, los tests de contrato y la tabla de extensiones aditivas.
- Las respuestas **degradadas** siempre declaran su modo (`execution_mode`, `degraded`, `alerts`).
- **No se inventan cifras**: todo importe procede del motor determinista o de una fuente identificada (`fx_source`, `date`, `is_mock`).
- Los parámetros financieros los fija el backend desde el contexto validado; **nunca** el modelo.

## Datos

- `data/processed/` es la fuente de verdad del MVP. Los fixtures se validan con `node scripts/validate-data.mjs`.
- La matriz de cobertura (corredores, comisiones, presupuestos) vive en los datos: añadir un corredor no debe requerir tocar la lógica.

## Commits y estilo

- Mensajes en Conventional Commits: `feat(backend): ...`, `fix(api): ...`, `docs(readme): ...`, `chore(ci): ...`.
- Código en español (dominio) con identificadores en inglés; comentarios y documentación en español.
- `ruff format` decide el formato: no debates estilos en la revisión.
