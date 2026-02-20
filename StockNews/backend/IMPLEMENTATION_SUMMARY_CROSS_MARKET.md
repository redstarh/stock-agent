# Cross-Market Analysis Implementation Summary

## Overview
Implemented cross-market analysis feature that uses AWS Bedrock Claude to analyze how US news impacts Korean stock market themes.

## Changes Made

### 1. Database Schema
- **Table:** `news_event`
- **New Column:** `kr_impact_themes VARCHAR(500)` - stores JSON array of Korean theme impacts from US news
- **Migration:** Direct ALTER TABLE command executed on SQLite database

### 2. Model Layer (`app/models/news_event.py`)
- Added `kr_impact_themes` field to `NewsEvent` model
- Field is nullable and stores JSON string

### 3. Core Analysis Module (`app/processing/cross_market.py`)
**New file** containing:
- `analyze_kr_impact(title, body)` function
- Uses Bedrock Claude via `app/core/llm.call_llm()`
- Returns list of impact dictionaries: `[{"theme": str, "impact": float, "direction": str}]`
- Korean themes: AI, 반도체, 2차전지, 바이오, 자동차, 조선, 방산, 로봇, 금융, 엔터, 게임, 에너지, 부동산, 통신, 철강, 항공

### 4. Pipeline Integration (`app/collectors/pipeline.py`)
- Modified `_analyze_single()` to accept `market` parameter (default: "KR")
- Added cross-market analysis for US news only
- Analysis runs in parallel with other LLM calls (sentiment, summary)
- Results stored as JSON in `NewsEvent.kr_impact_themes` field

### 5. Theme API Enhancement (`app/api/themes.py`)
- Modified `/theme/strength` endpoint to incorporate US news cross-market impacts
- Query additional US news with `kr_impact_themes` data
- Blend impact scores into global theme calculations
- Impact direction mapped: "up" → positive, "down" → negative, "neutral" → 0

### 6. New API Endpoint (`app/api/collect.py`)
- **New endpoint:** `POST /collect/analyze-cross-market?limit=100`
- Re-analyzes existing US news that lack cross-market data
- Uses ThreadPoolExecutor (5 workers) for parallel analysis
- Updates database with analysis results

## Data Flow

```
US News → Pipeline Collection
    ↓
_analyze_single(market="US")
    ↓
analyze_kr_impact() [Bedrock Claude]
    ↓
kr_impact_themes JSON → NewsEvent.kr_impact_themes
    ↓
Theme Strength API reads kr_impact_themes
    ↓
Blends US impacts into Korean theme scores
```

## Example Impact Data

```json
[
  {"theme": "반도체", "impact": 0.85, "direction": "up"},
  {"theme": "AI", "impact": 0.92, "direction": "up"}
]
```

## Verification

✅ All modules import successfully
✅ `kr_impact_themes` column exists in database
✅ 100 US news records exist in database for testing
✅ LSP diagnostics clean (no type errors)
✅ Schema tests pass
✅ Function signatures correct

## Usage

### Automatic (for new US news):
- Just collect US news via `/collect/us` or scheduler
- Cross-market analysis runs automatically in pipeline

### Manual (for existing US news):
```bash
curl -X POST http://localhost:8001/collect/analyze-cross-market?limit=100
```

### Query theme strength with cross-market data:
```bash
curl http://localhost:8001/theme/strength?market=KR&limit=20
```

## Technical Notes

- Cross-market analysis only runs for `market="US"` news
- Uses same Bedrock client as other LLM operations
- Graceful degradation: if analysis fails, empty array stored
- JSON validation ensures data integrity
- Thread-safe parallel execution in pipeline
- Impact values normalized to 0.0-1.0 range
- Direction constrainted to: "up", "down", "neutral"

## Files Modified

1. `/Users/redstar/AgentDev/StockNews/backend/stocknews.db` (schema)
2. `/Users/redstar/AgentDev/StockNews/backend/app/models/news_event.py`
3. `/Users/redstar/AgentDev/StockNews/backend/app/processing/cross_market.py` (new)
4. `/Users/redstar/AgentDev/StockNews/backend/app/collectors/pipeline.py`
5. `/Users/redstar/AgentDev/StockNews/backend/app/api/themes.py`
6. `/Users/redstar/AgentDev/StockNews/backend/app/api/collect.py`

## Integration with StockAgent

The cross-market impact data enhances the theme strength scores returned by `/theme/strength` endpoint, which StockAgent can use for:
- Better understanding of global market correlations
- Enhanced theme-based trading signals
- Risk assessment across markets
