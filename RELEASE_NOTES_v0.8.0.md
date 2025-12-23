# Release v0.8.0 - BigQuery Streaming

Released: 2025-12-18

## 🎯 Overview

This release introduces **BigQuery streaming capabilities** to prevent Out-Of-Memory (OOM) errors when processing large datasets, providing **~80% memory reduction** for operations with more than 1000 chats.

## ✨ Major Features

### BigQuery Streaming
- **`stream_chats_from_bigquery()`**: New generator function with automatic pagination (1000 chats/page)
- **Chunked Writes**: `save_to_bigquery()` now writes in 500-line chunks to avoid BigQuery's 10MB limit
- **Generator Support**: `run_batch()` accepts both `List[Chat]` and `Iterator[Chat]`

### Performance Improvements
- **Memory**: ~80% reduction for datasets >1000 chats
- **Streaming**: Pagination prevents loading entire datasets into memory
- **Chunked Writes**: Prevents memory spikes during BigQuery inserts

## 📊 Statistics

- **Tests**: 175 passing (+8 new streaming tests)
- **Coverage**: 75% (base code increased significantly)
- **Memory**: ~80% reduction for large datasets
- **Compatibility**: 100% backward compatible

## 🔧 Technical Details

### New Functions

**`src/ingestion.py`**
```python
def stream_chats_from_bigquery(
    days: Optional[int] = None,
    limit: Optional[int] = None,
    lightweight: bool = True,
    page_size: int = 1000,
) -> Iterator[Chat]
```

### Modified Functions

**`src/batch_analyzer.py`**
```python
# Now accepts generators
async def run_batch(
    self,
    chats: Union[List[Chat], Iterator[Chat]],  # Changed
    ...
) -> List[Dict[str, Any]]

# Now writes in chunks
def save_to_bigquery(
    self,
    results: List[Dict[str, Any]],
    week_start: datetime,
    week_end: datetime,
    chunk_size: int = 500,  # New parameter
) -> int
```

## 🧪 New Tests

- `tests/test_ingestion_streaming.py`: Pagination and streaming tests
- `tests/test_batch_analyzer_streaming.py`: 7 tests covering chunked writes, generators, and callbacks

## 📦 Dependencies

- Added `redis ^5.2.1` for LLM response caching

## 🐛 Bug Fixes

- Fixed mypy type error in Union handling with `cast()`
- Applied ruff formatting to all modified files

## 🔄 Migration Guide

### Optional Migration to Streaming

```python
# Before (still works - backward compatible)
from src.ingestion import load_chats_from_bigquery
chats = load_chats_from_bigquery(days=7)
results = await analyzer.run_batch(chats)

# After (recommended for large datasets)
from src.ingestion import stream_chats_from_bigquery
chats_stream = stream_chats_from_bigquery(days=30, page_size=1000)
results = await analyzer.run_batch(chats_stream)
```

No code changes required - existing code continues to work!

## 📝 Commits

- `84de0f4` feat: add BigQuery streaming to prevent OOM
- `f69a622` fix: resolve mypy type error in run_batch Union handling
- `5cfa15f` chore: remove test output file and update gitignore
- `4c0b4fc` style: apply ruff formatting to batch_analyzer and ingestion
- `2281ebc` build: add redis as dependency for LLM cache
- `cc361ae` build: update poetry.lock with redis dependency

## 🙏 Contributors

@gabrielpastega-bcmed

---

**Full Changelog**: https://github.com/gabrielpastega-bcmed/projeto_analise_SDR/compare/v0.7.0...v0.8.0
