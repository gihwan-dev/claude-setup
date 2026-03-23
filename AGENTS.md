# AGENTS.md

Manager-mode task bundles keep the main thread in orchestration mode.

- If `task.yaml.agent_orchestration.strategy = manager`, the main thread prefers bundle documents and structured helper results over broad repository rereads.
- After helper fan-out, do not resume broad code search or ad hoc file reading unless the task bundle explicitly allows it.
- Direct code implementation, direct validation fallback, and shared-file integration belong to the designated execution role, not the main thread.
- If a worker lane blocks or the merge boundary stops being clear, stop with split or replan instead of collapsing back to broad main-thread execution.
