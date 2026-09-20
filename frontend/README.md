# TRACE-X Phase 4: React Frontend

Privacy-first entity resolution platform with interactive dashboard, knowledge graph visualization, and confidence breakdown charts.

## Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Backend must be running on http://localhost:8000
# Vite proxy automatically forwards /api calls to backend
```

## Features

### Investigation Dashboard
- **Search** by subject name (name, email optional)
- **Async workflow**: create investigation, get ID immediately, poll for results
- **Demo scenarios**: Alice Johnson (clear match), John Smith (ambiguous), Bob Chen (location conflict)

### Investigation Detail View
- **Real-time status** polling (PENDING → PROCESSING → COMPLETE)
- **Top candidate** summary with confidence score
- **Tabbed interface**:
  - **Candidates**: Ranked list with per-feature confidence breakdown
  - **Knowledge Graph**: React Flow visualization (interactive, zoomable)
  - **Confidence**: Recharts bar chart + Bayesian explanation
  - **Timeline**: Vertical timeline of employment, projects, events
  - **Conflicts**: Detected contradictions with resolution UI

### Knowledge Graph
- **Interactive React Flow** visualization
- **Node types**: PERSON (blue), PROFILE (purple), ORGANIZATION (green), EVENT (amber), PROJECT (red), PUBLICATION (cyan), CONFLICT (red dashed)
- **Edges**: Relationships with confidence labels
- **Controls**: Zoom, pan, fit-to-view, minimap

### Confidence Breakdown
- **Recharts bar chart** showing per-feature scores (0-100)
- **Bayesian explanation**: prior → likelihood ratios → log-odds → posterior
- **Hover tooltips**: Each feature explained

### Timeline
- **Vertical timeline** (mobile) / **horizontal** (desktop) with icons
- **Event types**: EMPLOYMENT, PROJECT, PUBLICATION, EVENT, CONTRIBUTION
- **Date ranges** and confidence scores per event

### Conflict Resolution
- **List of detected conflicts** with severity (HIGH/MEDIUM/LOW)
- **Resolution UI**: Mark as EXPLAINED or REJECTED with note
- **Auto-refresh**: Confidence recalculates on conflict rejection

## Architecture

```text
src/
├── components/
│ ├── InvestigationDashboard.tsx # Search + create
│ ├── InvestigationDetail.tsx    # Main results view (tabs)
│ ├── CandidateCard.tsx          # Ranked candidate card
│ ├── KnowledgeGraph.tsx         # React Flow viz
│ ├── ConfidenceBreakdown.tsx    # Recharts + explanation
│ ├── TimelineView.tsx           # Event timeline
│ ├── ConflictPanel.tsx          # Conflict resolution
│ ├── Header.tsx                 # App header
│ └── ui/                        # shadcn/ui components
├── hooks/
│ └── useInvestigation.ts        # Poll status, fetch data
├── services/
│ └── api.ts                     # Axios API client
├── types/
│ └── api.ts                     # TypeScript interfaces
├── lib/
│ └── utils.ts                   # tailwind-merge helpers
├── App.tsx                      # Router (dashboard ↔ detail)
└── main.tsx                     # Entry point
```

## Demo Scenarios

### Scenario A: Alice Johnson (Clear Match)
- Expected: Confidence >85%, status VERIFIED
- 3 profiles across GitHub, LinkedIn, X
- Consistent name, bio, location
- No conflicts

### Scenario B: John Smith (Ambiguous)
- Expected: Confidence <40%, status LOW_CONFIDENCE
- 3 different Johns (AI researcher, marketing manager, fitness coach)
- Different locations, bios, companies
- No single clear match

### Scenario C: Bob Chen (Location Conflict)
- Expected: Confidence 71% (after -15 penalty), 1 conflict
- Strong name/bio match across GitHub, LinkedIn, X
- Impossible travel: San Francisco + Tokyo simultaneously
- Conflict can be REJECTED (travel for conference)

## UI Components (shadcn/ui)

- **Button**: CTA buttons with loading states
- **Card**: Content containers with headers/footers
- **Input**: Search fields
- **Tabs**: Multi-section views
- **Badge**: Status labels, aliases, event types
- **Tailwind**: Responsive grid, dark theme (slate-950 background)

## Styling

- **Dark mode**: Slate-950 background, slate-300 text
- **Color scheme**:
  - Green (>80% confidence): #10b981
  - Yellow (40-80%): #f59e0b
  - Red (<40%): #ef4444
  - Blue (primary): #3b82f6
- **Responsive**: Mobile-first (Tailwind breakpoints)
- **Accessible**: WCAG 2.1 AA (semantic HTML, ARIA, keyboard nav)

## Tests

```bash
npm run test
```

Tests cover:
- Dashboard form submission
- Investigation detail rendering
- Candidate card display
- Knowledge graph generation

## Build

```bash
npm run build
# Output: dist/
```

## Phase 4 Checklist

- ✅ Search interface (dashboard)
- ✅ Async workflow (POST → GET poll)
- ✅ Real-time status updates
- ✅ Candidate ranking + detail cards
- ✅ Knowledge graph (React Flow) visualization
- ✅ Confidence breakdown charts (Recharts)
- ✅ Timeline component
- ✅ Conflict resolution UI
- ✅ Mobile responsive
- ✅ Accessible (WCAG 2.1 AA)
- ✅ TypeScript throughout
- ✅ Tests for critical components
- ✅ Dark theme + professional design
- ✅ shadcn/ui components

## Next Steps

- Advanced filtering (by platform, date range, confidence)
- Bulk investigations (CSV upload)
- Investigation history/bookmarks
- Export to PDF/JSON
- Real connector authentication (Phase 5)
