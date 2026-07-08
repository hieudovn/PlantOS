# E2V2-3: Processing Profiles (7 MVP Steps)

## Context

Edge v2 enables no-code signal processing through Processing Profiles. This phase implements 7 must-have processing steps and the ProcessingEngine pipeline. Both raw and processed values are stored in DuckDB. A preview feature shows step-by-step transformation so users can validate profiles before applying.

## Plan Reference

- `docs/phase-edge-v2-productization-plan.md` §10
- `docs/01-project-constitution.md`
- `docs/60-edge-center-strategy.md`

## Constitution Checklist

- [x] Processing uses signal_id, not raw tag names
- [x] No free-form scripting (only predefined step types)
- [x] Profiles are versioned (profile_id + version tracking)
- [x] Raw + processed stored separately
- [x] Preview before apply (governed low-code principle)

## Implementation Checklist

### Data Model

- [ ] **3.1** Define `ProcessingProfile` and `ProcessingStep` in `edge-v2/agent/processing/profiles.py`:
  ```python
  @dataclass
  class ProcessingProfile:
      profile_id: str
      name: str
      description: str
      steps: list[ProcessingStep]
      created_at: datetime
      updated_at: datetime

  @dataclass
  class ProcessingStep:
      type: str  # one of 7 MVP types
      params: dict
      order: int
  ```

- [ ] **3.2** Define `ProcessedReading`:
  ```python
  @dataclass
  class ProcessedReading:
      signal_id: str
      value: float
      quality: str  # GOOD / STALE / BAD
      timestamp: datetime
      profile_id: str | None
  ```

### DuckDB Schema — Raw + Processed

- [ ] **3.3** Create raw_measurements table in `edge-v2/agent/buffer/`:
  ```sql
  CREATE TABLE IF NOT EXISTS raw_measurements (
      ts TIMESTAMPTZ NOT NULL,
      signal_id VARCHAR NOT NULL,
      raw_value DOUBLE,
      source_ref VARCHAR,
      connector VARCHAR,
      quality_hint VARCHAR,
      PRIMARY KEY (signal_id, ts)
  );
  ```

- [ ] **3.4** Create processed_measurements table:
  ```sql
  CREATE TABLE IF NOT EXISTS processed_measurements (
      ts TIMESTAMPTZ NOT NULL,
      signal_id VARCHAR NOT NULL,
      value DOUBLE,
      quality VARCHAR,
      source VARCHAR,
      profile_id VARCHAR,
      synced BOOLEAN DEFAULT FALSE,
      retry_count INTEGER DEFAULT 0,
      PRIMARY KEY (signal_id, ts)
  );
  ```

### Processing Engine

- [ ] **3.5** Implement `ProcessingEngine` in `edge-v2/agent/processing/engine.py`:
  ```python
  class ProcessingEngine:
      def apply(self, raw_value: float, profile: ProcessingProfile,
                history: list[float]) -> ProcessedReading:
          value = raw_value
          quality = "GOOD"
          for step in sorted(profile.steps, key=lambda s: s.order):
              value, quality = self._apply_step(step, value, quality, history)
          return ProcessedReading(value=value, quality=quality, ...)
  ```

### 7 MVP Processing Steps

Implement each step as a pure function in `edge-v2/agent/processing/steps/`. Each returns `(new_value: float, new_quality: str)`.

- [ ] **3.6** `scale_offset.py` — `y = x * scale + offset`
- [ ] **3.7** `linear_calibration.py` — `y = a * x + b`
- [ ] **3.8** `clamp.py` — clamp value to [min, max]
- [ ] **3.9** `moving_average.py` — SMA with window size, requires history
- [ ] **3.10** `quality_range.py` — set quality BAD if value outside [min, max]
- [ ] **3.11** `stale_check.py` — set quality STALE if timestamp older than max_age_seconds
- [ ] **3.12** `baseline_subtract.py` — `y = x - baseline`

### Processing API

- [ ] **3.13** `GET /api/processing/profiles` — list all profiles
- [ ] **3.14** `POST /api/processing/profiles` — create profile
- [ ] **3.15** `GET /api/processing/profiles/{id}` — get profile detail
- [ ] **3.16** `PUT /api/processing/profiles/{id}` — update profile
- [ ] **3.17** `DELETE /api/processing/profiles/{id}` — delete profile (only if no signals assigned)
- [ ] **3.18** `POST /api/processing/profiles/{id}/preview` — preview with sample data
  - Request: `{"raw_samples": [723, 721, 718, 725, 720]}`
  - Response: step-by-step output for each step + final values
- [ ] **3.19** `GET /api/processing/profiles/{id}/signals` — list signals using this profile

### Data Pipeline Integration

- [ ] **3.20** Wire processing into main loop in `main.py`:
  ```python
  for connector in self.connectors.get_running():
      readings = await connector.read_tags(...)
      for reading in readings:
          # Store raw
          self.buffer.write_raw(reading)
          # Process
          profile = self.config.get_profile_for_signal(reading.signal_id)
          processed = self.processing.apply(reading.raw_value, profile, history)
          # Store processed
          self.buffer.write_processed(processed)
  ```

### Console UI

- [ ] **3.21** Create `processing.html` — profile list with cards
- [ ] **3.22** Create profile editor modal:
  - Add step dropdown (7 types + "Coming Soon" grayed out for 8 later types)
  - Reorder steps (drag or up/down buttons)
  - Remove step (✕ button)
  - Per-step parameter form
- [ ] **3.23** Create preview panel:
  - Input sample values (paste CSV or use live data)
  - Step-by-step output table
  - Color-coded: green = passed, yellow = clamped, red = BAD quality
  - Warning messages (e.g., "5/5 values clamped")
- [ ] **3.24** Update connections tag mapping to include processing profile selector

### Tests

- [ ] **3.25** Unit tests for all 7 step types (pure functions, easy to test)
- [ ] **3.26** Pipeline integration tests (multi-step profiles)
- [ ] **3.27** Quality propagation tests (GOOD → STALE → BAD through pipeline)
- [ ] **3.28** Preview accuracy tests (verify step-by-step output matches engine)
- [ ] **3.29** Raw + processed storage tests (both tables populated correctly)

## Files to Create

```
edge-v2/agent/processing/
  __init__.py
  engine.py
  profiles.py
  steps/
    __init__.py
    scale_offset.py
    linear_calibration.py
    clamp.py
    moving_average.py
    quality_range.py
    stale_check.py
    baseline_subtract.py

edge-v2/agent/web/routes/
  processing.py

edge-v2/console/static/
  processing.html
  js/processing.js
```

## Files to Modify

- `edge-v2/agent/main.py` — wire ProcessingEngine, data pipeline
- `edge-v2/agent/buffer/` — add raw_measurements + processed_measurements tables

## Acceptance Criteria

```text
✅ User can create a processing profile with 7 MVP step types
✅ User can assign profile to a signal via connector tag mapping
✅ Raw → processed transformation is correct for each step type
✅ Preview shows step-by-step output with clear warnings
✅ Quality flags propagate correctly (GOOD → STALE → BAD)
✅ Both raw and processed values stored in DuckDB
✅ Store-and-forward sync uses processed_measurements table
✅ All 7 step types have unit tests (>90% coverage)
✅ Remaining 8 step types show "Coming Soon" in UI
```

## Red Flags

- Stop if: processing step modifies quality but engine ignores it
- Stop if: raw values are synced to Center (raw must stay local)
- Stop if: preview output doesn't match actual engine output
- Stop if: constitution violation (free-form scripting, raw tag access in processing)
