# 🧠 MLCP Agent Roles & Responsibilities

This document defines the primary agent roles in MLCP v0.1 and their responsibilities within the layered context protocol. Each agent interacts with specific context layers, performs tasks based on its role category, and contributes to the evolving system state.

| Agent Name         | Purpose                                           | Inputs                          | Outputs                         | Reads From Layers                | Writes To Layers                |
|--------------------|---------------------------------------------------|----------------------------------|----------------------------------|----------------------------------|----------------------------------|
| ProductOwnerAgent  | Define task intent, assign roles, set goals       | Task, Global                     | Task directives, context updates | Global, Task, Temporal           | Task, Temporal                   |
| DeveloperAgent     | Build features or deliverables for a task         | Task, Agent, Operational         | Implementation strategy, updates | Task, Agent, Operational         | Temporal, Telemetry              |
| TesterAgent        | Validate output against acceptance criteria       | Task, Temporal                   | Test results, pass/fail status   | Task, Temporal                   | Telemetry                        |
| SecurityAgent      | Scan context and output for compliance            | Task, Security                   | Redaction flags, risk assessments| Security, Task                  | Telemetry                        |
| ScrumMasterAgent   | Coordinate agents, manage sprint progress         | Temporal, Agent, Operational     | Sprint summary, blockers         | All layers                       | Temporal, Task                   |

## Notes
- **Agent lifecycle** is managed by the context engine and routed via protocol logic.
- **Human-in-the-loop agents** may intervene at any stage depending on role configuration in `mlcp.yaml`.
- This table will evolve as agent capabilities become more fine-grained or externally extended (e.g. plugin agents).