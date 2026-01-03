# Phase 1.1 Structural Refinement Summary

## Overview

Phase 1.1 prepares ThreatVeilAI for Horizon (AI risk visibility) features by introducing structural refinements to the data model, service organization, and risk management system.

**Status:** ✅ **COMPLETE**

---

## Changes Implemented

### 1. Company Model ✅

**File:** `backend/models.py`

- Added `Company` model with:
  - `id`: UUID primary key
  - `name`: Optional company name
  - `primary_domain`: Indexed, unique domain identifier
  - `created_at`: Timestamp

- Updated `Scan` model:
  - Added `company_id` foreign key
  - Added relationship to `Company`
  - Scans are now linked to companies

**Impact:**
- Enables multi-domain scanning per organization
- Provides org-level context for future features
- Automatic company creation on first scan for a domain

### 2. ScanAI Model ✅

**File:** `backend/models.py`

- Added `ScanAI` model for AI-specific scan data:
  - `id`: UUID primary key
  - `scan_id`: Foreign key to Scan (one-to-one)
  - `ai_tools`: JSON list of detected AI tools/frameworks
  - `ai_vendors`: JSON list of AI vendors with risk metadata
  - `ai_keys`: JSON list of detected AI key leak signals
  - `ai_score`: Integer (0-100) for Horizon AI risk score
  - `ai_summary`: Text field for AI-specific summary
  - `created_at`: Timestamp

**Status:** Model created but not yet populated in scan flow (ready for Horizon phase)

### 3. Risk Registry ✅

**Files:**
- `backend/risk_registry.json`: Central registry of signal definitions
- `backend/services/ai/ai_registry_loader.py`: Loader and lookup functions

**Features:**
- Centralized signal definitions with severity, category, and remediation
- Pattern matching support (e.g., `cve_*`, `github_leak_*`)
- Safe defaults for missing signals
- Helper functions: `get_signal_info()`, `get_signal_severity()`, `get_signal_category()`, `get_signal_remediation()`

**Registry includes:**
- HTTP security headers (HSTS, CSP, X-Frame-Options, etc.)
- TLS certificate issues
- DNS security (DMARC, SPF)
- CVE vulnerabilities
- GitHub leak detection
- OTX threat intelligence
- Service error signals

### 4. AI Services Structure ✅

**Folder:** `backend/services/ai/`

**Files Created:**
- `__init__.py`: Package initialization
- `ai_registry_loader.py`: Risk registry loader (see above)
- `ai_scoring.py`: Placeholder AI risk scoring function
- `github_ai_service.py`: Scaffolded AI-specific GitHub scanning

**GitHub AI Service:**
- `detect_ai_libraries()`: Detect AI libraries in repos (TODO)
- `detect_ai_files()`: Detect AI-related files (TODO)
- `detect_ai_agent_configs()`: Detect AI agent configs (TODO)
- `scan_github_for_ai_indicators()`: Comprehensive AI scan (TODO)

**Status:** Scaffolded with typed signatures and docstrings, ready for Horizon implementation

### 5. Horizon Services Structure ✅

**Folder:** `backend/services/horizon/`

**Files Created:**
- `__init__.py`: Package initialization
- `horizon_service.py`: Placeholder Horizon analysis service
- `horizon_models.py`: Data models for Horizon features

**Status:** Structure prepared, not yet imported or used (ready for Horizon phase)

### 6. Database Integration ✅

**Files Updated:**
- `backend/models.py`: New models added
- `backend/main.py`: Imports updated to ensure table creation
- `backend/routes/scan.py`: Company creation/linking logic

**Migration Support:**
- `backend/migrations/README.md`: Migration guide for SQLite and Postgres
- SQLite: Auto-creates tables via SQLAlchemy
- Postgres: Alembic migration example provided

### 7. Scan Flow Updates ✅

**File:** `backend/routes/scan.py`

**Changes:**
- Automatic company creation/lookup for each scan
- Scan linked to company via `company_id`
- Backward compatible (existing scans work, company_id is nullable)

**Logic:**
1. Normalize domain to lowercase
2. Query for existing company by `primary_domain`
3. Create company if not found
4. Link scan to company

### 8. Tests ✅

**File:** `backend/tests/test_phase1_1_models.py`

**Tests Added:**
- `test_company_creation()`: Verify Company model works
- `test_scan_linked_to_company()`: Verify Scan-Company relationship
- `test_scan_ai_model()`: Verify ScanAI model and relationships
- `test_risk_registry_loader()`: Verify registry loading and lookups
- `test_risk_registry_helper_functions()`: Test helper functions

**Existing Tests:**
- All existing tests still pass
- No breaking changes to API contract

---

## File Structure

```
backend/
├── models.py                    # Updated: Company, ScanAI models
├── risk_registry.json           # New: Central risk registry
├── main.py                      # Updated: Model imports
├── routes/
│   └── scan.py                  # Updated: Company creation logic
├── services/
│   ├── ai/                      # New: AI services folder
│   │   ├── __init__.py
│   │   ├── ai_registry_loader.py
│   │   ├── ai_scoring.py
│   │   └── github_ai_service.py
│   └── horizon/                  # New: Horizon services folder
│       ├── __init__.py
│       ├── horizon_service.py
│       └── horizon_models.py
├── migrations/
│   └── README.md                # New: Migration guide
└── tests/
    └── test_phase1_1_models.py  # New: Phase 1.1 tests
```

---

## Database Schema Changes

### New Tables

**companies:**
- `id` (VARCHAR, PK)
- `name` (VARCHAR, nullable)
- `primary_domain` (VARCHAR, unique, indexed)
- `created_at` (TIMESTAMP)

**scan_ai:**
- `id` (VARCHAR, PK)
- `scan_id` (VARCHAR, FK to scans, unique)
- `ai_tools` (JSON/JSONB)
- `ai_vendors` (JSON/JSONB)
- `ai_keys` (JSON/JSONB)
- `ai_score` (INTEGER)
- `ai_summary` (TEXT)
- `created_at` (TIMESTAMP)

### Modified Tables

**scans:**
- Added: `company_id` (VARCHAR, FK to companies, nullable, indexed)

---

## How to Run Migrations

### SQLite (Default)

No manual migration needed. Tables are auto-created on startup via:
```python
Base.metadata.create_all(bind=engine)
```

### Postgres/Supabase

**Option 1: Using Alembic**
```bash
alembic revision -m "add_company_and_scan_ai_models"
# Then add migration content from backend/migrations/README.md
alembic upgrade head
```

**Option 2: Manual SQL**
```sql
-- See backend/migrations/README.md for full SQL
CREATE TABLE companies (...);
ALTER TABLE scans ADD COLUMN company_id VARCHAR;
CREATE TABLE scan_ai (...);
```

---

## Testing

### Run Phase 1.1 Tests
```bash
PYTHONPATH=/Users/macbookairm2/threatveil pytest backend/tests/test_phase1_1_models.py -v
```

### Run All Tests
```bash
PYTHONPATH=/Users/macbookairm2/threatveil pytest backend/tests/ -v
```

### Verify Existing Tests Still Pass
```bash
PYTHONPATH=/Users/macbookairm2/threatveil pytest backend/tests/test_scan_smoke.py -v
```

---

## Backward Compatibility

✅ **All existing functionality preserved:**
- API contract unchanged (`/api/v1/scan/vendor` works as before)
- Existing scans continue to work
- `company_id` is nullable (existing scans have NULL)
- No breaking changes to frontend

✅ **New features are additive:**
- Company creation is automatic and transparent
- ScanAI model exists but is not yet populated
- Risk registry is available but not yet integrated into scoring

---

## Next Steps (Horizon Phase)

1. **Populate ScanAI:**
   - Wire `github_ai_service.py` into scan flow
   - Detect AI tools, vendors, and keys
   - Compute `ai_score` using `ai_scoring.py`

2. **Integrate Risk Registry:**
   - Use registry for severity/category lookups in scoring
   - Add remediation guidance to signals

3. **Implement Horizon Service:**
   - Complete `horizon_service.py` implementation
   - Add Horizon API endpoints
   - Build Horizon dashboard

4. **Multi-Domain Features:**
   - Company-level risk aggregation
   - Cross-domain analysis
   - Org-wide reporting

---

## Summary

Phase 1.1 successfully prepares ThreatVeilAI for Horizon features by:

✅ Adding Company model for multi-domain support
✅ Creating ScanAI model for AI-specific data
✅ Introducing centralized risk registry
✅ Organizing AI services in dedicated folders
✅ Preparing Horizon service structure
✅ Maintaining full backward compatibility
✅ Adding comprehensive tests

**All tests pass, no breaking changes, ready for Horizon implementation.**


