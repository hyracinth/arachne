## engineering log
##### 2026.02.20
**Problem**: After a bulk data migration, the primary key desynced from the table's actual `MAX(id)`.
**Resolution**: Synced sequence using setval.
```
SELECT setval(pg_get_serial_sequence('arachne.attacks', 'id'), coalesce(max(id), 1)) FROM arachne.attacks;
```

##### 2026.02.18
**Problem**: Bot payloads often contain binary `NUL` characters which PostgreSQL's `TEXT` type rejects.
**Resolution**: Added additional cleaning in the Enricher service to scrub `0x00` bytes before database ingestion.

##### 2026.02.15
**Problem**: Geo data look up could potentially clog up attack traffic.
**Resolution**: Decoupled enricher logic to a standalone service, allowing ingestion to take in traffic without impact.

##### 2026.02.13
**Problem**: Non-standard protocol payloads. Bots (or scanners) sometimes send HTTP requests
**Resolution**: Enhanced logic to handle unstructured payloads and updated database to store larger strings

##### 2026.02.13
**Problem**: "Ghost" connections. Bots sometimes disconnect without any inputs
**Resolution**: Enhanced logic to capture traffic regardless of payload