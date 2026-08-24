# Manual verification tests

These tests each build one or more full multi-year `Panchaanga` objects from scratch
(real ephemeris computation, 7-11+ minutes per test) to verify a specific festival
conversion byte-for-byte against a direct reproduction of the original logic. They were
useful during active migration work but are too expensive to run on every push, so they
are **not** part of the regular suite (`pytest jyotisha_tests`, what CI runs).

Run them explicitly and occasionally, e.g. when touching the intersection/vaara-conditioned/
month-transition engines in `jyotisha/panchaanga/temporal/festival/applier/`:

```
pytest jyotisha_manual_tests
```

The regular safety net before merging is `jyotisha_tests/spatio_temporal` (a handful of
full-panchaanga golden-fixture comparisons against generated ICS/TeX/MD/JSON output).
