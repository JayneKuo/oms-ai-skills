# Migration Strategy

## Principle
This project is greenfield in structure.

## Allowed later reuse
- Selective reuse of old implementation code only.
- No reuse of old planning docs as architecture sources.
- Reused code must be wrapped by the new runtime and agent contracts.

## Evaluation checklist
- Does the old code match the new module boundary?
- Can it be validated against the approved OpenAPI and test environment docs?
- Does it avoid leaking old architecture assumptions into the new workspace?
