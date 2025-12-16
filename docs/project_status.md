# Project Status & Context
> **For AI Agents:** Read this file first to understand the current project state.

## Current State (2025-12-16)
- **Version:** 0.7.0
- **Status:** Production-ready
- **Test Coverage:** 70% (100 tests)
- **Warnings:** 0

## Key Files
| File | Description |
|------|-------------|
| `src/gemini_client.py` | Gemini API client with validation |
| `src/llm_schemas.py` | Pydantic schemas for LLM output |
| `src/batch_analyzer.py` | ETL with checkpoint + rate limiting |
| `src/insights_service.py` | Business logic for Insights page |
| `src/logging_config.py` | Centralized logging |

## Completed (2025-12-16)
- [x] LLM prompt refinement (EMPRESA context)
- [x] Schema validation (Pydantic)
- [x] Rate limiting (240 RPM)
- [x] Checkpoint recovery (ETL)
- [x] Test coverage: 51% → 70%
- [x] FutureWarning pandas corrigido
- [x] SQL injection fixes
- [x] Bandit integrated in CI

## Architecture
- ETL: BigQuery → Gemini API → BigQuery/Local
- Dashboard: Streamlit multi-page
- Logging: Structured (file + stdout)
