# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project adheres to Semantic Versioning.

## [2.5.0] - 2025-11-21

### Added
- Developer tooling: `pyproject.toml` with Ruff/Black/Mypy config.
- `dev-requirements.txt` with pinned versions for tests and linters.
- Pre-commit hooks configuration (`.pre-commit-config.yaml`).
- Initial CHANGELOG and release scaffolding for v2.5.

### Changed
- Bumped package version to `2.5.0` in `main/setup.py` and `main/VERSION`.
- Updated displayed version to `2.5.0` in `main/README.md`.
- Pinned runtime dependencies in `main/requirements.txt` for reproducible environments.

### Planned for 2.5.x
- Consolidate GUI into a single entry with selectable modes; move i18n to JSON resource files.
- Introduce framed binary UART protocol with CRC32 across Pico and host controller.
- Implement persistent resume state on host side with hash verification.
- Add ECC/OOB handling options and visualization in Dump Analyzer.
- Enhance Pico performance (PIO/DMA ping-pong, R/B# IRQ, timing autotune).
- Expand plugin system with declarative chip specs and GUI integration.
- Strengthen tests and CI (unit/integration, pytest-qt, GitHub Actions matrix).
