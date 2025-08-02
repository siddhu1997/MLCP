# 🔄 MLCP Agent Lifecycle (v0.1)

This document outlines the lifecycle of an agent within MLCP. It defines the stages from instantiation to task completion, including how context is loaded, prompts are generated, and results are returned.

---

## 1. Spawn

- Agent is instantiated by the context engine.
- Pulls role definition from `mlcp.yaml`.
- Assigned a `context_packet` with scoped layers.

## 2. Context Hydration

- Agent reads relevant fields from each enabled layer:
  - `global` for policies
  - `task` for objectives
  - `agent` for role and skills
  - `operational` for budget/time limits
  - `temporal` for history
  - `security` for scopes and redactions
- Resulting data is assembled into an internal memory object or prompt context.

## 3. Prompt Construction

- Context is formatted into a prompt template defined under `prompts/<agent>.txt`.
- Budget, role, and task metadata are injected.
- Redactions and scope enforcement are applied.
- Prompt is then sent to the underlying LLM or external agent interface.

## 4. Execution

- Agent produces a response within allowed token budget and time limits.
- Optional telemetry data is collected (e.g., latency, usage, reasoning steps).

## 5. Evaluation

- System or another agent (e.g., Tester or Human reviewer) evaluates output:
  - Does it meet acceptance criteria?
  - Was the context misused or ignored?
  - Was the token budget respected?

## 6. Context Mutation

- Agent output is used to:
  - Update `task` status or metadata
  - Append to `temporal` logs
  - Trigger events or escalate to another agent

## 7. Retire or Loop

- If the task is complete → agent retires.
- If follow-up work is needed → updated `context_packet` is forwarded.
- Memory may be saved or updated (if long-term memory is enabled).

---

## Notes

- Lifecycle is enforced by the `context_manager`.
- Each stage can emit telemetry for observability.
- Future: Lifecycle hooks can allow plugins (e.g., recruiter, reviewer, debugger agents).