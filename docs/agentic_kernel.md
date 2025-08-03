# Agentic Kernel (DRAFT)

> ⚠️ **This is a working draft.**  
> The Agentic Kernel specification is actively evolving and will be updated as MLCP's architecture matures. Expect breaking changes, placeholder APIs, and exploratory features.

## 🔧 Responsibilities

- Orchestrate agent lifecycle: spawn, kill, suspend
- Enforce access controls based on agent roles
- Provide syscall interfaces for file access, web access, and context interactions
- Manage collaborative development to reduce merge conflicts
- Route privileged operations through approval flows
- Interface with the Temporal Layer for predictive conflict and telemetry

---

## 🧬 Core Concepts

### 1. Role-Based Permissions

Each agent type (Developer, Architect, ProductOwner, etc.) has strictly defined syscall access and context visibility.

- Developers can read/write local code, raise PRs, and message peers.
- Architects can review PRs, provide approvals, and advise on structure.
- Product Owners can spawn agents and update task contexts.
- Only the Kernel or human approvers can perform final merges.

### 2. System Call Layer (Syscalls)

Agents interact with the world through syscall functions exposed by the Kernel:

| Syscall            | Description                                 |
|--------------------|---------------------------------------------|
| `read`, `write`    | Access to files in sandboxed directories    |
| `readContext`      | Read from specified MLCP context layers     |
| `spawn`            | Spawn new agents of specific type           |
| `fetch`            | Controlled web access via allowlist         |
| `openPullRequest`  | Raise PRs with diff patch and reviewers     |
| `reviewPullRequest`| Submit reviews, comments, or approvals      |
| `mergePullRequest` | Final merge of approved PRs (kernel-only)   |
| `reserve`          | Soft-lock files for coordination            |
| `suggestPaths`     | Suggest safe working paths to minimise conflicts |
| `sendEvent`        | Telemetry or coordination dispatch          |
| `sendMessage`      | Informal agent-to-agent communication       |

### 3. Web Access Control

Web calls must go through `kernel.fetch()`:
- Domains must be allowlisted
- Telemetry is always recorded
- Optionally budget-aware or human-approved
- Payloads may be inspected for security

### 4. Pull Request Protocol

All Developer commits must go through a PR:
- PRs can only be raised via `openPullRequest`
- Assigned reviewers must approve the code
- Updated diffs are pushed via `pushPRUpdate`
- Final merge handled via `mergePullRequest` by Kernel or lead agent
- Review latency, comments, and approval rates are logged for sprint analysis

### 5. Parallel Development & Conflict Minimisation

To avoid merge conflicts:
- Agents write in sandboxed workspaces
- Changes are committed via diff patches
- Kernel suggests non-overlapping paths
- Soft-locks (`reserve`) allow advisory coordination
- Merge conflicts are handled via `raiseMergeConflict()` or routed to human approvers

---

## 🧩 File Structure & Config

The Agentic Kernel is configured via:

- `agentic-kernel.yaml`: Role policies, syscall permissions, collaboration strategies
- `telemetry.log`: Syscall events, PR logs, conflict data
- Optional integration with `temporal.yaml` for predictive insights

---

## 🛣 Roadmap

The following features are planned:
- Auto-generated `agentic-kernel.yaml` via Kernel UI
- Live syscall interception and auditing
- Fine-grained layer access gating
- Web call cost prediction via Token Economy layer
- Agent impersonation prevention and role validation

---

## 🔐 Philosophy

The Agentic Kernel enables high autonomy while enforcing guardrails. It ensures MLCP agents:
- Operate ethically and securely
- Collaborate productively without bottlenecks
- Stay within bounds defined by project context and budget

---

> The Agentic Kernel is not just a gatekeeper — it’s a conductor of multi-agent orchestration under the MLCP framework.
You might wanna check [this](../config/agentic_kernel.yaml) out too!

