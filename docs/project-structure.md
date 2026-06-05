# Project Structure

## Top-level layout
- `docs/` — architecture, capability, and rollout documents
- `src/core/` — shared result and capability primitives
- `src/config/` — env and OMS context construction
- `src/runtime/` — token provider, request builder, OMS HTTP client
- `src/services/` — thin endpoint wrappers and service contracts
- `src/agents/` — base contracts, registry, router, and business agents
- `src/cli/` — local execution entry points
- `src/reference/` — small local reference slices derived from approved inputs
- `tests/` — unit, contract, and fixture coverage

## Wave 1 ownership
- Core abstractions live in `src/core/`
- Shared transport and auth live in `src/runtime/`
- OMS business endpoint wrappers live in `src/services/`
- Business-facing execution logic lives in `src/agents/`
