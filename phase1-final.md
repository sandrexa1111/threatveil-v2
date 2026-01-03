

## 1. Phase 1 – Signal Core PRD (Engineering Spec)

### 1.1 Purpose

Turn ThreatVeil from “external scanner with AI summaries” into a **Signal Platform** that:

* Normalizes *all* security evidence into a single `Signal` schema
* Maps evidence to real-world `Assets`
* Is multi-tenant (supports many organizations safely)
* Is AI-ready and graph-ready (later phases just plug into this)

This phase does **not** need EDR/cloud integrations yet – but it must be designed to accept them later without changing core structures.

---

### 1.2 Goals (what must be true when Phase 1 is done)

1. Every existing external scan (domain + optional GitHub org) produces:

   * A `Scan` record
   * A list of `Signal` records (canonical schema)
   * Asset records (domains, repos, AI artifacts…) linked to those signals

2. There is a **single place** (DB + API) where:

   * You can fetch all signals for an org
   * Filter by asset, severity, category, source
   * See raw evidence for debugging + AI grounding

3. The system is **multi-tenant safe**:

   * Every record has `org_id`
   * APIs enforce org boundaries
   * No chance to leak another tenant’s signals in queries

4. The frontend can:

   * Show signals per scan
   * Show aggregated signals per org (starting point for Daily Brief later)

---

### 1.3 Non-Goals (for Phase 1)

* No fancy graph queries yet (paths, blast radius).
* No EDR/cloud/Okta connectors yet.
* No Slack bot or daily brief yet.
* No complex ML models (just deterministic scoring you already have).

---

### 1.4 Core Entities

You already have `Scan` and `ScanAI`. Phase 1 standardizes:

#### 1) `organizations`

* Represents a customer / tenant.
* Even if you only have your own org for now, design it as multi-tenant.

#### 2) `users`

* Represent authenticated users tied to an org.

#### 3) `assets`

* Universal representation of “things attackers care about”:

  * domains, repos, buckets, IPs, external SaaS, AI agents, etc.

#### 4) `signals`

* Unified representation of “issues / evidence” found about assets.

#### 5) `scans`

* A scan is a *collection* of signals produced by a pipeline execution for a given org and optionally a target (domain + GitHub org, etc).

#### 6) `events` (optional in Phase 1)

* Generic event log for future integrations. You can stub this table now.

---

### 1.5 Canonical Schemas

#### `assets`

* **Fields (core)**:

```sql
id           UUID PK
org_id       UUID NOT NULL
type         TEXT NOT NULL  -- 'domain' | 'repository' | 'ai_agent' | ...
name         TEXT NOT NULL  -- e.g. "threatveil.com" or "org/repo"
properties   JSONB          -- additional metadata (tags, cloud IDs)
risk_tags    TEXT[]         -- e.g. ['internet_exposed','contains_pii']
created_at   TIMESTAMPTZ DEFAULT now()
updated_at   TIMESTAMPTZ DEFAULT now()
```

#### `signals`

* **Fields (core)**:

```sql
id           UUID PK
org_id       UUID NOT NULL
scan_id      UUID NULL      -- nullable, future events may not belong to a scan
asset_id     UUID NULL
source       TEXT NOT NULL  -- 'threatveil_external' | 'github' | 'otx' | ...
type         TEXT NOT NULL  -- 'cve' | 'config' | 'network' | 'secret' | ...
severity     TEXT NOT NULL  -- 'low' | 'medium' | 'high' | 'critical'
category     TEXT NOT NULL  -- 'infrastructure' | 'software' | 'data' | 'identity' | 'ai'
title        TEXT NOT NULL
detail       TEXT NOT NULL
evidence     JSONB NOT NULL
created_at   TIMESTAMPTZ DEFAULT now()
```

* **Evidence standard** (inside `evidence` jsonb):

```json
{
  "source_service": "tls_service",
  "observed_at": "2025-12-05T12:00:00Z",
  "raw": { "header_sample": { "Strict-Transport-Security": null } },
  "external_refs": ["https://securityheaders.com/..."],
  "confidence": 0.9,
  "detection_method": "rule",
  "notes_for_ai": "Missing HSTS on main HTTPS endpoint"
}
```

---

### 1.6 Functional Requirements

#### Backend – Ingestion & Normalization

1. **Refactor current scan pipeline** to:

   * Fetch raw data (HTTP headers, TLS, CT, Vulners, OTX, GitHub, AI signals).
   * Translate → structured intermediate objects.
   * Normalize → `Signal` objects.
   * Upsert `Assets` as needed.
   * Store everything in `scans`, `signals`, `assets`.

2. **Add `org_id`** support:

   * When a scan is triggered, the current user’s `org_id` is passed through the entire pipeline.
   * Every `Scan`, `Signal`, `Asset` created must be tied to that `org_id`.

3. **Create a Signal query API:**

   * `GET /api/v1/org/{org_id}/signals?severity=high&category=ai`
   * Returns paginated list of signals with asset info and evidence (for debugging + future Risk Brain).

4. **Create an Org summary API:**

   * `GET /api/v1/org/{org_id}/summary`
   * Returns:

     * count of signals per severity
     * count per category
     * last_scan_at
     * top 5 latest high-severity signals

This will later power the **Daily Brief** and an org-level dashboard.

---

#### Frontend – Phase 1

* You already have a scan detail page and AI risk panel.
* Add:

  * A simple **Org overview** widget:

    * `Total assets`, `High severity signals`, `AI risk signals`.
  * A minimal **Signals list view** filtered by org.

Nothing crazy: just enough to see that the Signal Core is working *end-to-end*.

---

### 1.7 Non-Functional Requirements

* **Reliability:** A failure in any external API (Vulners, OTX, etc.) must:

  * Produce partial results
  * Add `low severity` error signals so we know something failed

* **Performance:**

  * Single scan should typically complete in < 10–20 seconds.
  * Use async and `asyncio.gather` for parallel sub-services.

* **Security:**

  * Absolutely never return signals for another `org_id`.
  * No secrets in logs.
  * All external API keys stored in env variables.

---

## 2. GitHub Project: Epics & Issues

You can paste this into GitHub Projects and break into issues.

### Epic 1 — Data Model & Migrations

1. **Issue: Add `organizations` and `users` tables**

   * Create `organizations` table.
   * Create `users` table (if not already existing).
   * Add `org_id` to users.

2. **Issue: Add `assets` table**

   * Implement DB table.
   * Create SQLAlchemy model `Asset`.
   * Add helper `get_or_create_asset(org_id, type, name, properties)`.

3. **Issue: Add `signals` table**

   * Implement DB table.
   * Create SQLAlchemy model `Signal`.
   * Add helper `create_signal_from_finding(...)`.

4. **Issue: Add indexes for signals & assets**

   * Index `signals(org_id, asset_id, severity, category)`.
   * Index `assets(org_id, type, name)`.

---

### Epic 2 — Backend Refactor: Canonical Signals

5. **Issue: Create `signals` Pydantic schema**

   * Define `SignalBase`, `SignalCreate`, `SignalRead` models.
   * Ensure they match DB model closely.

6. **Issue: Refactor HTTP/TLS/DNS pipeline to emit canonical signals**

   * Replace inline risk logic with:

     * `http_finding -> Signal` transformation functions
   * Attach asset (domain) to each signal.

7. **Issue: Integrate Vulners into canonical signals**

   * Map CVEs to signals with `type='cve'`, category=software.
   * Add cvss-based severity logic.

8. **Issue: Integrate OTX into canonical signals**

   * Transform OTX pulse info into signals:

     * Usually `low|medium` unless severe context exists.

9. **Issue: Integrate GitHub AI leakage into canonical signals**

   * Use your existing `github_ai_service` outputs.
   * Create signals for:

     * AI tools detected
     * Agent configs
     * Exposed AI keys

---

### Epic 3 — Multi-Tenancy Support

10. **Issue: Add `org_id` to Scans, Signals, Assets**

    * DB migration.
    * Backfill data for dev environment (single default org).

11. **Issue: Propagate `org_id` through scan pipeline**

    * Update `POST /api/v1/scan/vendor` to read user’s org.
    * Every created record uses that org.

12. **Issue: Enforce org boundaries at API layer**

    * Ensure `scan_id` lookup always checks `org_id`.
    * Ensure `/org/{org_id}/signals` cannot be used to access other org’s data.

---

### Epic 4 — New APIs for Signals & Summary

13. **Issue: Implement `GET /api/v1/org/{org_id}/signals`**

    * Filters: severity, category, asset_id, source.
    * Pagination.

14. **Issue: Implement `GET /api/v1/org/{org_id}/summary`**

    * Aggregations:

      * per severity
      * per category
    * top 5 recent high signals.

15. **Issue: Unit tests for new APIs**

    * Use pytest + httpx.
    * Coverage for access control, filters, and shapes.

---

### Epic 5 — Frontend Integration

16. **Issue: Add Org Summary widget**

    * Show counts from `/summary` API.
    * Link to “View signals”.

17. **Issue: Add Signals list page**

    * Table with severity chip, category, title, asset, time.
    * Filter controls for severity & category.

18. **Issue: Link from scan detail to filtered signals**

    * “View all signals for this scan / asset” linking to list.

---

## 3. Backend Scaffolding for Signal Core

Your backend structure might look like:

```text
backend/app/
  core/
    config.py
    db.py
    logging_config.py
    security.py
  models/
    organization.py
    user.py
    asset.py
    signal.py
    scan.py
    scan_ai.py
  schemas/
    organization.py
    user.py
    asset.py
    signal.py
    scan.py
  services/
    scans/
      external_scan_service.py
    signals/
      signal_normalizer.py
      asset_mapper.py
    integrations/
      http_service.py
      tls_service.py
      dns_service.py
      vulners_service.py
      otx_service.py
      github_service.py
      lakera_service.py
  routes/
    org.py
    scan.py
    signals.py
```

### Key services

* `signal_normalizer.py`

  * Functions like:

    ```python
    def hsts_missing_to_signal(org_id, scan_id, asset_id, evidence_raw) -> SignalCreate: ...
    def missing_csp_to_signal(...)
    def cve_to_signal(...)
    def github_key_leak_to_signal(...)
    ```

* `asset_mapper.py`

  * Functions like:

    ```python
    def get_or_create_domain_asset(org_id: UUID, domain: str) -> Asset: ...
    def get_or_create_repo_asset(org_id: UUID, full_name: str) -> Asset: ...
    ```

* `external_scan_service.py`

  * Orchestrates:

    * external checks
    * converts to Signals
    * persists everything.

---

## 4. DB Migration Examples (SQL)

Assuming Postgres (Supabase):

> ⚠️ Adjust names if your existing tables differ.

### `organizations`

```sql
CREATE TABLE organizations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);
```

### `users` (if needed / simplified)

```sql
ALTER TABLE users ADD COLUMN org_id UUID REFERENCES organizations(id);

-- Create a default org and backfill:
INSERT INTO organizations (id, name) VALUES ('00000000-0000-0000-0000-000000000001','Default Org');
UPDATE users SET org_id = '00000000-0000-0000-0000-000000000001' WHERE org_id IS NULL;
```

### `assets`

```sql
CREATE TABLE assets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  type TEXT NOT NULL,
  name TEXT NOT NULL,
  properties JSONB DEFAULT '{}'::jsonb,
  risk_tags TEXT[] DEFAULT ARRAY[]::text[],
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_assets_org_type_name ON assets(org_id, type, name);
```

### `signals`

```sql
CREATE TABLE signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  scan_id UUID NULL REFERENCES scans(id) ON DELETE SET NULL,
  asset_id UUID NULL REFERENCES assets(id) ON DELETE SET NULL,
  source TEXT NOT NULL,
  type TEXT NOT NULL,
  severity TEXT NOT NULL,
  category TEXT NOT NULL,
  title TEXT NOT NULL,
  detail TEXT NOT NULL,
  evidence JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_signals_org_sev_cat ON signals(org_id, severity, category);
CREATE INDEX idx_signals_org_asset ON signals(org_id, asset_id);
```

### Add `org_id` to `scans`

```sql
ALTER TABLE scans ADD COLUMN org_id UUID REFERENCES organizations(id);

UPDATE scans
SET org_id = '00000000-0000-0000-0000-000000000001'
WHERE org_id IS NULL;

ALTER TABLE scans ALTER COLUMN org_id SET NOT NULL;
CREATE INDEX idx_scans_org_created ON scans(org_id, created_at DESC);
```

---

## 5. Test & Validation Plan

### 5.1 Unit Tests

* **Signal creation**:

  * When HTTP headers show missing HSTS → a `high` severity `software` signal is created.
  * When Vulners returns a CVE with cvss >= 7 → `high` severity `cve` signal is created.

* **Asset mapping**:

  * Scanning `example.com` creates/uses one `domain` asset.
  * GitHub org `my-org` scan creates `repository` assets.

* **Multi-tenancy**:

  * Two orgs scanning the same domain produce signals with different `org_id`.
  * API responses are filtered by `org_id` correctly.

### 5.2 Integration Tests

* `POST /api/v1/scan/vendor`:

  * With a valid domain, returns `scan_id`.
  * `signals` table has entries for that scan.
  * `assets` table has at least the domain asset.
  * All records share the same `org_id`.

* `GET /api/v1/org/{org_id}/signals`:

  * Returns signals only for that org.
  * Filters work.

* `GET /api/v1/org/{org_id}/summary`:

  * Returns correct counts & last_scan_at.

### 5.3 Manual Checks

* Run a few scans vs known domains:

  * A domain with bad headers → see correct software/network signals.
  * A domain with good TLS → minimal or no TLS-related signals.

* Turn off one external API (e.g. Vulners):

  * Scan still completes.
  * You get a low-severity signal “Vulners unavailable”.

---
