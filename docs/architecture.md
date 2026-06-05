# Architecture

## Goal
Build a standalone OMS agent workspace where a shared foundation supports multiple publishable multi-skill agents, with Sales Order Agent as the only implementation-first phase-1 deliverable.

## Layers
1. Reference layer: approved OMS source artifacts only.
2. Foundation layer: auth, OMS client, request shaping, error normalization, output formatting, action policy.
3. Service layer: thin wrappers for business endpoint families.
4. Skill layer: focused business capabilities mounted under agents.
5. Agent layer: publishable business agents with prompts, descriptions, and output contracts.
6. Runner layer: local CLI entry and staging validation.
