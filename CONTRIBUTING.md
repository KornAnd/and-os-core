# Contributing to AnD os Core

Thank you for your interest in contributing to **AnD os Core**!

AnD os is an engineering-grade deterministic microkernel designed for autonomous AI coding agents. To maintain highest reliability and safety standards, all contributions must strictly conform to our architecture principles.

---

## 🏛️ Guiding Invariants

1. **Clean Code Standard (Uncle Bob / Rule #37):**
   - High cohesion, loose coupling.
   - Functions do one thing well.
   - Descriptive identifiers without abbreviations.
   - Zero tolerance for silent exception swallowing (`except: pass` or bare `except:`).
2. **Spec-Before-Code (Rule #2):**
   - Architectural decisions, schemas, and interfaces must be defined before writing implementation code.
3. **Hermetic & Fast Verification (Rule #61):**
   - No code is accepted without pre-flight verification passing:
     ```bash
     python3 and_os/bin/quick_verify.py
     ```
   - All canary probes must complete in under 500ms.
4. **Zero Secrets & Air-Gap Standard (Rule #57 & Rule #58):**
   - Never commit API keys, personal credentials, absolute local host paths, or proprietary data.

---

## 🛠️ Development & Testing Workflow

1. **Fork and Clone:**
   ```bash
   git clone https://github.com/KornAnd/and-os-core.git
   cd and-os-core
   ```
2. **Run Quality Verification:**
   ```bash
   python3 and_os/bin/sys_cli.py verify
   ```
3. **Run Multi-Core Canary Probes:**
   ```bash
   python3 and_os/bin/sys_cli.py skills --probe
   ```
4. **Create a Topic Branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```
5. **Submit a Pull Request:**
   - Keep commits focused and well-documented.
   - Ensure all 9 pre-flight phases pass green.
