# 🧱 MLCP Layer Engineering Plan (v0.1)

This document provides an engineering overview of each layer in the Multi-Layered Context Protocol. Each layer has a specific role in context propagation and agent reasoning.

---

## 🌐 Global Layer
- **Purpose**: Holds immutable truths, policies, and organisation-level settings.
- **Storage**: Read-only YAML/JSON (`config/global_context.yaml`), cached in memory.
- **Access Pattern**: All agents can read. Never mutated at runtime.
- **Engineering Notes**:
  - Validate schema at startup
  - Hash for immutability
  - May support per-org overrides in future

---

## 🎯 Task Layer
- **Purpose**: Represents the current task being worked on and its evolution.
- **Storage**: MongoDB collection `tasks`, linked via `task_id`.
- **Access Pattern**: Readable by all agents. Writable by ProductOwner, Developer, ScrumMaster.
- **Engineering Notes**:
  - Track status, assignees, priority
  - Log diffs for traceability
  - Consider relational model if needed

---

## 🧠 Agent Layer
- **Purpose**: Stores agent profile, skills, role, and memory.
- **Storage**: MongoDB collection `agents`; memory may use Redis/vector DB.
- **Access Pattern**: Agents read their own profile. System updates memory post-task.
- **Engineering Notes**:
  - Role-specific prompt templates
  - Memory plugins for long-term learning
  - Track agent performance and skill claims

---

## ⚙️ Operational Layer
- **Purpose**: Conveys live execution settings: token limits, timeouts, retries.
- **Storage**: Embedded within each `context_packet`.
- **Access Pattern**: Read during prompt construction. Updated as task progresses.
- **Engineering Notes**:
  - Enforce budget constraints pre-invoke
  - Retry logic to support graceful degradation
  - Retry escalation policies

---

## ⏳ Temporal Layer
- **Purpose**: Maintains logs, sprint history, and predictive insights.
- **Storage**: MongoDB collection `temporal_logs`, indexed by `sprint_id`, `agent_id`.
- **Access Pattern**: Readable by ScrumMaster, ProductOwner. Writable by all agents.
- **Engineering Notes**:
  - Retain acceptance criteria and time-based metrics
  - Add support for forecasting modules
  - Archive or compress old context records

---

## 🔐 Security Layer
- **Purpose**: Controls read/write scopes and field redactions per agent.
- **Storage**: Rules in `security_rules.yaml` + overrides in context_packet.
- **Access Pattern**: Read for permission checks. Written by SecurityAgent or PO.
- **Engineering Notes**:
  - Context-aware masking engine
  - Scoped visibility per role
  - Redact sensitive fields pre-agent input or output