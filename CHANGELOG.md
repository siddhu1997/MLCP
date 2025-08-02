## 📝 Changelog

### v0.1.0 – Hybrid Alpha
- Initial protocol design and README structure
- Defined six-layer architecture: Global, Task, Agent, Operational, Temporal, Security
- Introduced context packet lifecycle
- Added support for spawning role-based agents
- Established distinctions from MCP (Model Context Protocol)
- Added SVG-based architecture diagram

## 🗺️ Roadmap

- [x] Define `context_packet.yaml` schema
- [ ] Implement base context propagation engine
- [ ] Build agent spawning logic (budget-aware)
- [ ] Add telemetry tracking for tokens, cost, and latency
- [ ] Integrate a minimal temporal layer with sprint logs
- [ ] Develop React-based dashboard for human-in-the-loop decisions
- [ ] Add OpenAPI or gRPC interfaces
- [ ] Write test harness for simulating agent sprints
- [ ] Support plugin agents (external tools, LangChain, etc.)
- [ ] Launch MLCP v0.2.0 with working prototype
