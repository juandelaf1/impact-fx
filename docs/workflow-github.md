# Flujo de trabajo Git y CI/CD — Impact FX

## Modelo recomendado: GitHub Flow (simple, adecuado para 4 personas)
1. `main` es la rama estable (demo/deploy).
2. Para cada tarea/issue, crear una rama desde `main`: `feat/<id>-descripcion`, `fix/<id>-descripcion`, `docs/<id>-descripcion`, `chore/<id>-descripcion`.
3. Hacer commits pequeños y descriptivos (`tipo(scope): mensaje`).
4. Abrir **Pull Request (PR)** hacia `main`, enlazando el issue con `Closes #N` en la descripción.
5. Obtener **al menos 1 aprobación** de otro miembro del equipo, resolver comentarios y asegurarse de que el CI pase.
6. Hacer merge a `main` (preferible squash o merge commit según acuerdo) y borrar la rama.

> Alternativa (si se prefiere): añadir rama `dev` como integración y promover a `main` por release/demo. Para el alcance y tiempo del hackathon, GitHub Flow directo a `main` es más simple.

## Protección de `main` (objetivo)
- Requerir PR para merge (sin pushes directos).
- Requerir **1 aprobación** y resolución de conversaciones.
- Requerir checks de CI en verde.
- **Estado:** la protección con revisiones obligatorias en repos privados de cuenta personal requiere GitHub Pro (limitación del plan). Opciones:
  - Hacer el repo público, o usar una organización con el plan adecuado, y activar la protección; o
  - **Aplicar la regla por acuerdo de equipo** (no push directo a `main`, PR + 1 aprobación) mientras tanto.

## CI/CD
- **CI (activo):** workflow `.github/workflows/ci.yml` se ejecuta en `push` y `pull_request` a `main`. Actualmente valida datos/golden cases (`node scripts/validate-data.mjs`).
- **Extensión (cuando se cierre stack D-003):** añadir jobs de lint/test/build para backend y frontend.
- **CD (despliegue):** conectar la plataforma elegida (Vercel/Netlify para front, Render/Railway/Fly para back) al repo/rama `main` o configurar acción de deploy. Credenciales como secretos del repositorio (`Settings > Secrets and variables > Actions`), nunca en el código.

## Issues, PRs y Project (seguimiento)
- Crear **issues** por tarea del backlog (`docs/backlog.md`) con etiquetas (p.ej. `must`, `should`, `backend`, `frontend`, `agent`, `data`, `docs`) y responsable.
- En cada PR incluir `Closes #N` (o `Refs #N`) para vincular y cerrar automáticamente el issue al merge. **Con `Closes #N` el issue se cierra solo al mergear**; con `Refs #N` solo se referencia.
- **GitHub Project (v2):** https://github.com/users/juandelaf1/projects/4 — *Impact FX - Reto Ebury*.
  - **Campos:** `Status` (Todo / In Progress / In Review / Blocked / Done), `Priority` (Must / Should / Could), `Area` (Backend / Frontend / Agent / Data / Docs / DevOps), `Owner` (Juan / Laura / Gema / Jose / Todos).
  - Contiene los issues #1, #2, #4, #5, #6, #7, #8, #9 y #16 con los campos ya rellenados.
  - **Vistas:** `Tabla - Sprint Impact FX`, `Tablero - Kanban` (columnas por `Status`) y `Roadmap - Sprint del reto`.
  - Enlazado al repositorio (`juandelaf1/impact-fx`), por lo que los issues y PRs aparecen en la pestaña **Development** del repo.
  - Automatización native (Projects > Workflows): al cerrar un issue → `Status = Done`; al mergear un PR con `Closes #N` → el issue pasa a `Done`.
- Mantener `docs/backlog.md` y el Project alineados en los hitos principales.
