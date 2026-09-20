# TRACE-X: Privacy-First Digital Identity Intelligence Platform

## Phase 3: Connectors & API Routes

### What's New in Phase 3
- 4 mock connectors (GitHub, LinkedIn, X, Instagram) returning deterministic synthetic data
- 3 demo scenarios (Alice Johnson: clear match; John Smith: ambiguous; Bob Chen: location conflict)
- REST API for investigations (create, poll, get details)
- Conflict resolution endpoint
- Full async workflow: POST → background processing → GET status

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Start MongoDB (if not running)
docker run -d -p 27017:27017 mongo:latest

# Start backend
uvicorn trace_x.main:app --reload --host 0.0.0.0 --port 8000
```

### API Endpoints

#### Create Investigation
```bash
curl -X POST http://localhost:8000/api/investigate \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Johnson"}'
```

Response:
```json
{
  "investigation_id": "uuid-here",
  "status": "PENDING",
  "message": "Investigation started..."
}
```

#### Poll Investigation Status
```bash
curl http://localhost:8000/api/investigate/{investigation_id}
```

When complete, returns full Investigation object:
```json
{
  "investigation_id": "uuid",
  "query": {...},
  "status": "COMPLETE",
  "top_candidates": [
    {
      "candidate_id": "cand_123",
      "rank": 1,
      "confidence_overall": 87.5,
      "name": "Alice Johnson",
      "status": "VERIFIED",
      "confidence_breakdown": {...}
    }
  ],
  "profiles": [...],
  "timeline": [...],
  "conflicts": [...],
  "relationship_graph": {...}
}
```

#### Get Candidate Details
```bash
curl http://localhost:8000/api/candidates/{candidate_id}
```

#### Resolve Conflict
```bash
curl -X PATCH http://localhost:8000/api/investigate/{id}/conflicts/{conflict_id} \
  -H "Content-Type: application/json" \
  -d '{"resolution": "REJECTED", "resolution_note": "Travel for conference"}'
```

### Demo Scenarios

Run with these names to trigger known scenarios:

1. **Alice Johnson** (clear match >85% confidence)
```bash
   curl -X POST http://localhost:8000/api/investigate/ \
     -H "Content-Type: application/json" \
     -d '{"name": "Alice Johnson"}'
```

2. **John Smith** (ambiguous namesake <40% confidence)
```bash
   curl -X POST http://localhost:8000/api/investigate/ \
     -H "Content-Type: application/json" \
     -d '{"name": "John Smith"}'
```

3. **Bob Chen** (location conflict with penalty)
```bash
   curl -X POST http://localhost:8000/api/investigate/ \
     -H "Content-Type: application/json" \
     -d '{"name": "Bob Chen"}'
```

### Run Tests

```bash
pytest tests/ -v
```

### Architecture

```
trace_x/
├── connectors/       # Platform connectors (GitHub, LinkedIn, X, Instagram)
│   ├── base.py       # Abstract interface
│   ├── github.py     # GitHub connector
│   ├── linkedin.py   # LinkedIn connector
│   ├── x.py          # X connector
│   └── instagram.py  # Instagram connector
├── services/
│   └── investigation_service.py # Orchestrator (connectors + ML)
├── routers/
│   ├── investigate.py  # Investigation endpoints
│   └── candidates.py   # Candidate detail endpoints
├── core/
│   ├── config.py
│   └── seeds.py        # Deterministic demo data
├── db/
├── ml/
├── schemas/
└── main.py           # Updated with new routers
```

### Key Design Decisions

1. **Synthetic Data Only**: DEMO_MODE=true. All connectors return faker-generated or seeded data.
2. **Deterministic Seeds**: Same query → same results (fixed seeds based on subject name).
3. **Async Workflow**: POST creates Investigation (returns immediately), background job processes, client polls for completion.
4. **Service Layer**: All business logic in InvestigationService; routers are thin adapters.
5. **Conflict Resolution**: PATCH endpoint allows judges to experiment with conflict resolution workflow.

### Next: Phase 4 (React Frontend)

Phase 4 will add:
- Investigation dashboard (search, status polling)
- React Flow knowledge graph visualization
- Confidence breakdown charts (Recharts)
- Timeline component
- Conflict resolution UI
