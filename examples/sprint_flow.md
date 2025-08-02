# 🌀 MLCP Sprint Flow Simulation (v0.1)

This is a sample walkthrough of how context packets and agents interact in a simulated mini-sprint using MLCP. All examples are conceptual and meant to demonstrate protocol design, not execution code.

---

## 🎯 Task: "Design a Login Page"

### 1. ProductOwnerAgent
- **Receives empty context_packet**
- Defines:
  - `task.title`: "Design a Login Page"
  - `acceptance_criteria`: 
    - Email + Password fields
    - Login button with spinner
- Forwards to DeveloperAgent

---

### 2. DeveloperAgent
- Reads task and acceptance criteria
- Checks:
  - Available token budget
  - Relevant skills (React, Tailwind)
- Responds with:
  - Component structure idea
  - Mocked loading state
- Updates temporal layer with implementation notes
- Forwards to TesterAgent

---

### 3. TesterAgent
- Validates against `temporal.acceptance_criteria`
- Simulates test outcome:
  - Passes spinner test
  - Flags missing accessibility label
- Writes test result to telemetry layer
- Returns to ProductOwnerAgent

---

### 4. ProductOwnerAgent
- Reviews Tester feedback
- Updates task:
  - `status`: "Blocked"
  - `blockers`: "Missing accessibility label"
- Loop may continue to DeveloperAgent with new `context_packet`

---

## 📦 Observed Context Packet Transitions

| Step | From Agent | To Agent | Context Changes |
|------|------------|----------|-----------------|
| 1 → 2 | ProductOwnerAgent | DeveloperAgent | Added task, criteria |
| 2 → 3 | DeveloperAgent | TesterAgent | Implementation strategy |
| 3 → 4 | TesterAgent | ProductOwnerAgent | Test result |
| Loop | PO ↔ Dev | Bug fix cycle | Incremental updates |

---

## Notes

- Every step uses the same `context_packet.id` but appends to its history
- This is a pure simulation – real execution would involve handlers, logs, token counters, etc.