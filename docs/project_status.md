# Project Status & Context
> **For AI Agents:** Read this file first to understand the current project state.

## Current State (2025-12-17)
- **Version:** 0.7.0
- **Status:** Production-ready
- **Test Coverage:** 83% (123 tests passing)
- **CI:** ✅ Passing (Python 3.12, 3.13, 3.14)
- **Warnings:** 0

## Key Files
| File | Description |
|------|-------------|
| `src/gemini_client.py` | Gemini API client with validation |
| `src/llm_schemas.py` | Pydantic schemas for LLM output |
| `src/batch_analyzer.py` | ETL with checkpoint + rate limiting |
| `src/context_provider.py` | Interface for business context |
| `src/insights_service.py` | Business logic for Insights page |
| `src/logging_config.py` | Centralized logging |
| `config/settings.py` | Typed configuration (Gemini, BigQuery, Catalog) |

## Completed Optimizations (2025-12-17)

### Phase 1: Cleanup & Consolidation ✅
- Removed `src/llm_analysis.py` (redundant mock)
- Migrated `main.py` to use `GeminiClient`
- Removed empty directories

### Phase 2: Architecture for Integration ✅
- Created `config/settings.py` (typed dataclasses)
- Created `src/context_provider.py` (abstract interface)
- Prepared for external catalog integration

### Phase 3: Code Quality ✅
- Coverage: 64% → 83%
- Tests: 93 → 123
- Added BigQuery test mocks
- CI passing on Python 3.12/3.13/3.14

## Architecture
- ETL: BigQuery → Gemini API → BigQuery/Local
- Dashboard: Streamlit multi-page
- Logging: Structured (file + stdout)
- Config: Environment-based with typed dataclasses
