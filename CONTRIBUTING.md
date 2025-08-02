# 🤝 Contributing to MLCP

Welcome, and thank you for your interest in contributing to MLCP!

We use a **proposal-first (RFC)** model to ensure the protocol and architecture evolve with thoughtfulness and traceability.

---

## 🧩 Contribution Workflow

### 1. 📝 Submit an RFC
All non-trivial contributions must begin as an RFC.

- Create a new file in `rfcs/` using the template in `rfcs/000-template.md`
- Filename should follow the format: `rfcs/###-short-title.md`
- Your RFC should explain the motivation, design, alternatives, and integration plan
- Open a GitHub Issue to discuss it with the maintainers

> Only approved RFCs can proceed to PR stage.

### 2. ✅ Get Approval
- We’ll review and provide feedback on the RFC
- You may be asked to iterate and refine
- Once accepted, your RFC will be marked as **"Approved"**

### 3. 🚀 Submit a Pull Request
- Reference the approved RFC in your PR description
- Follow existing code structure and conventions
- Include test cases and documentation where applicable

---

## 🧪 Contributions That *Don’t* Need RFCs
- Typos, grammar fixes in docs
- Visual or style improvements to diagrams
- Small configuration tweaks (e.g. `.gitignore`)

---

## 🧰 Development Guidelines
- Use Python 3.10+
- Stick to `black` for formatting and `ruff` for linting
- Tests go under `tests/` and must use `pytest`

---

## 🌱 Contributor Philosophy

We believe in:
- **Protocol > Pipeline** — every change should improve coordination, not just code
- **Readability over cleverness**
- **Design clarity before implementation**

---

Ready to propose something? Check out [rfcs/000-template.md](./rfcs/000-template.md) and start a conversation!
