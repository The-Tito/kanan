# Forma de trabajo

## Ramas (gitflow)

- `main`: solo versiones liberadas, cada una con su etiqueta `vX.Y.Z`.
- `develop`: integración; siempre debe pasar las pruebas.
- `feature/<nombre>`: sale de `develop` y regresa a `develop` con `git merge --no-ff`.
- `release/<versión>`: sale de `develop`, recibe solo ajustes de versión y documentación, y se
  integra a `main` (con etiqueta) y de vuelta a `develop`.
- `hotfix/<nombre>`: sale de `main` y regresa a `main` y `develop`.

## Commits

Formato [Conventional Commits](https://www.conventionalcommits.org/) en español:

```
<tipo>(<ámbito>): <resumen en imperativo>
```

Tipos usados: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`.

## Antes de integrar una rama

```bash
ruff check .
```

```bash
pytest
```

## Registro

- Cada fase tiene su plan en `docs/planes/` antes de escribir código.
- Toda decisión con alternativas reales se anota como ADR en `docs/decisiones/`.
- Al cerrar una fase se agrega una entrada en `docs/bitacora.md`.
