## Contexto

<!-- ¿Qué resuelve esta PR y por qué? Vincula la issue o el ítem de backlog. -->

## Cambios

<!-- Lista de cambios relevantes por área: backend / frontend / datos / docs / CI. -->

## Contrato API

- [ ] No se modifica el contrato público (`docs/api-contract.md`, `shared/contracts/`).
- [ ] Si se modifica, se actualizan `docs/api-contract.md`, `shared/contracts/contracts.md` y las pruebas de contrato, y se explica el motivo (cambio compatible / incompatible).

## Verificación

- [ ] `python -m pytest tests -q` en verde.
- [ ] `ruff check .` y `ruff format --check .` en verde.
- [ ] `mypy backend` en verde.
- [ ] `node scripts/validate-data.mjs` en verde (si se tocan datos).
- [ ] Smoke test manual contra el backend en local (caso B1) cuando el cambio afecta a `/api/chat`.

## Datos y trazabilidad

- [ ] No se han inventado cifras ni resultados: las cifras vienen del motor determinista o de una fuente identificada (`fx_source`, `date`, `is_mock`).
- [ ] Si el flujo se degrada, la respuesta lo indica (`execution_mode`, `degraded`, `alerts`).
- [ ] No se han expuesto secretos, datos personales ni claves en el código o los logs.

## Despliegue / entorno

- [ ] Variables de entorno nuevas documentadas en `.env.example` y en el README.
- [ ] Sin cambios que requieran migración de datos existentes.
