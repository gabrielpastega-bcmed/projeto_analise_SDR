# Project Status & Context
> **For AI Agents:** Read this file first to understand the current project state.

## Current State (2025-12-17)
- **Version:** 0.8.0
- **Status:** Production-ready
- **Test Coverage:** 75% (175 tests passing)
- **CI:** ✅ Passing (Python 3.12, 3.13, 3.14)
- **Warnings:** 0

## Key Files
| File | Description |
|------|-------------|
| `src/gemini_client.py` | Gemini API client with validation |
| `src/llm_schemas.py` | Pydantic schemas for LLM output |
| `src/batch_analyzer.py` | ETL with checkpoint + rate limiting + **streaming** |
| `src/ingestion.py` | Data loading with **BigQuery streaming** |
| `src/llm_cache.py` | Redis cache for LLM responses |
| `src/metrics.py` | Token/cost tracking |
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

### Phase 4: BigQuery Streaming & Performance ✅ (v0.8.0)
- **Streaming ingestion**: `stream_chats_from_bigquery()` with pagination
- **Chunked writes**: `save_to_bigquery()` with 500-line chunks
- **Generator support**: `run_batch()` accepts iterators
- **Tests**: 123 → 175 (+52 tests including cache and metrics)
- **Performance**: ~80% memory reduction for large datasets
- **Redis cache**: LLM response caching for cost savings

## Architecture
- ETL: BigQuery → Gemini API → BigQuery/Local
- **New**: Streaming support for large datasets (prevents OOM)
- Dashboard: Streamlit multi-page
- Logging: Structured (file + stdout)
- Config: Environment-based with typed dataclasses
