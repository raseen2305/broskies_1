# AnalysisProgress Component States

## Component Anatomy

```
┌─────────────────────────────────────────────────────────────┐
│  [Icon] [Title]                     
             [Percentage]  │
│  ████████████████████████████████████░░░░░░░░░░░░░░░░░░░░░   │
│  [Status Message]                           [Count Display]  │
│  [Phase 1] ─ [Phase 2] ─ [Phase 3] ─ [Phase 4]             │
│  ─────────────────────────────────────────────────────────  │
│  [Detailed Statistics - shown during evaluation only]       │
└─────────────────────────────────────────────────────────────┘
```

## State Progression

### 1. Started (0-10%)
```
Status: started
Message: "Starting analysis..."
Progress: 0-10%
Phase Indicators: All pending (○)
```

**Visual:**
```
┌─────────────────────────────────────────────────────────────┐
│  ⏳ Analyzing Repositories                             5%   │
│  ██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   │
│  Starting analysis...                                       │
│  ○ Scoring ─ ○ Categorizing ─ ○ Evaluating ─ ○ Calculating │
└─────────────────────────────────────────────────────────────┘
```

### 2. Scoring (10-20%)
```
Status: scoring
Message: "Calculating importance scores..."
Progress: 10-20%
Phase Indicators: Scoring (⏳), Others pending (○)
```

**Visual:**
```
┌─────────────────────────────────────────────────────────────┐
│  ⏳ Analyzing Repositories                            15%   │
│  ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   │
│  Calculating importance scores...                          │
│  ⏳ Scoring ─ ○ Categorizing ─ ○ Evaluating ─ ○ Calculating │
└─────────────────────────────────────────────────────────────┘
```

### 3. Categorizing (20-30%)
```
Status: categorizing
Message: "Categorizing repositories..."
Progress: 20-30%
Phase Indicators: Scoring (✓), Categorizing (⏳), Others pending (○)
```

**Visual:**
```
┌─────────────────────────────────────────────────────────────┐
│  ⏳ Analyzing Repositories                            25%   │
│  ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   │
│  Categorizing repositories...                              │
│  ✓ Scoring ─ ⏳ Categorizing ─ ○ Evaluating ─ ○ Calculating │
└─────────────────────────────────────────────────────────────┘
```

### 4. Evaluating - Start (30-35%)
```
Status: evaluating
Message: "Evaluating 1 of 12 repositories..."
Progress: 30-35%
Phase Indicators: Scoring (✓), Categorizing (✓), Evaluating (⏳), Calculating (○)
Detailed Stats: Visible
```

**Visual:**
```
┌─────────────────────────────────────────────────────────────┐
│  ⏳ Analyzing Repositories                            32%   │
│  ████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   │
│  Evaluating 1 of 12 repositories...               1 / 12   │
│  ✓ Scoring ─ ✓ Categorizing ─ ⏳ Evaluating ─ ○ Calculating │
│  ─────────────────────────────────────────────────────────  │
│       288              12               1                   │
│   Total Repos      To Evaluate      Evaluated               │
└─────────────────────────────────────────────────────────────┘
```

### 5. Evaluating - Mid (50-60%)
```
Status: evaluating
Message: "Evaluating 6 of 12 repositories..."
Progress: 50-60%
Detailed Stats: Updated counts
```

**Visual:**
```
┌─────────────────────────────────────────────────────────────┐
│  ⏳ Analyzing Repositories                            55%   │
│  ████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   │
│  Evaluating 6 of 12 repositories...               6 / 12   │
│  ✓ Scoring ─ ✓ Categorizing ─ ⏳ Evaluating ─ ○ Calculating │
│  ─────────────────────────────────────────────────────────  │
│       288              12               6                   │
│   Total Repos      To Evaluate      Evaluated               │
└─────────────────────────────────────────────────────────────┘
```

### 6. Evaluating - Near Complete (80-90%)
```
Status: evaluating
Message: "Evaluating 11 of 12 repositories..."
Progress: 80-90%
```

**Visual:**
```
┌─────────────────────────────────────────────────────────────┐
│  ⏳ Analyzing Repositories                            85%   │
│  ████████████████████████████████████████░░░░░░░░░░░░░░░   │
│  Evaluating 11 of 12 repositories...             11 / 12   │
│  ✓ Scoring ─ ✓ Categorizing ─ ⏳ Evaluating ─ ○ Calculating │
│  ─────────────────────────────────────────────────────────  │
│       288              12              11                   │
│   Total Repos      To Evaluate      Evaluated               │
└─────────────────────────────────────────────────────────────┘
```

### 7. Calculating (90-99%)
```
Status: calculating
Message: "Calculating overall score..."
Progress: 90-99%
Phase Indicators: All complete except Calculating (⏳)
Detailed Stats: Hidden
```

**Visual:**
```
┌─────────────────────────────────────────────────────────────┐
│  ⏳ Analyzing Repositories                            95%   │
│  ██████████████████████████████████████████████████░░░░░░   │
│  Calculating overall score...                              │
│  ✓ Scoring ─ ✓ Categorizing ─ ✓ Evaluating ─ ⏳ Calculating │
└─────────────────────────────────────────────────────────────┘
```

### 8. Complete (100%)
```
Status: complete
Message: "Analysis complete! 12 repositories evaluated"
Progress: 100%
Phase Indicators: All complete (✓)
Background: Green
```

**Visual:**
```
┌─────────────────────────────────────────────────────────────┐
│  ✅ Analysis Complete                                       │
│  Analysis complete! 12 repositories evaluated               │
└─────────────────────────────────────────────────────────────┘
```

### 9. Failed
```
Status: failed
Message: Error message
Background: Red
```

**Visual:**
```
┌─────────────────────────────────────────────────────────────┐
│  ❌ Analysis Failed                                         │
│  Failed to evaluate repositories: Rate limit exceeded       │
└─────────────────────────────────────────────────────────────┘
```

## Progress Percentage Mapping

| Phase | Start % | End % | Duration |
|-------|---------|-------|----------|
| Started | 0 | 10 | ~1s |
| Scoring | 10 | 20 | ~2s |
| Categorizing | 20 | 30 | ~1s |
| Evaluating | 30 | 90 | ~45-60s |
| Calculating | 90 | 100 | ~1s |

## Phase Icon States

| Icon | Meaning | Color |
|------|---------|-------|
| ○ | Pending | Gray (border-gray-300) |
| ⏳ | In Progress | Blue (text-blue-600, spinning) |
| ✓ | Complete | Green (text-green-600) |

## Color Coding

### Text Colors
- **Title**: text-gray-900 (dark)
- **Percentage**: text-blue-600 (in progress) / text-green-600 (complete)
- **Message**: text-gray-700 (in progress) / text-green-700 (complete) / text-red-700 (failed)
- **Count**: text-gray-500 (secondary info)
- **Stats Labels**: text-gray-500 (secondary)
- **Stats Values**: text-gray-900 (total), text-blue-600 (to evaluate), text-green-600 (evaluated)

### Background Colors
- **In Progress**: bg-blue-50 with border-blue-200
- **Complete**: bg-green-50 with border-green-200
- **Failed**: bg-red-50 with border-red-200

### Progress Bar
- **Track**: bg-gray-200
- **Fill**: bg-gradient-to-r from-blue-500 to-indigo-600

## Responsive Behavior

The component is fully responsive:
- Progress bar scales to container width
- Phase indicators stack on mobile (if needed)
- Stats grid maintains 3-column layout
- Text sizes remain readable on all screens

## Animation Timings

- **Initial appearance**: 0.3s fade + slide
- **Progress bar**: 0.5s ease-out transition
- **Details panel**: 0.3s fade + height expansion
- **Phase icons**: Instant state change

## Accessibility

- Semantic HTML structure
- ARIA labels for progress bar
- Color is not the only indicator (icons + text)
- High contrast ratios for text
- Keyboard navigation support (if interactive)

## Integration Points

### With AnalyzeButton
```tsx
{!isAnalyzing && <AnalyzeButton />}
{isAnalyzing && <AnalysisProgress />}
```

### With Overview Tab
```tsx
{!analyzed && <AnalyzeButton />}
{analyzing && <AnalysisProgress />}
{analyzed && <ScoreInfographic />}
```

### Standalone Usage
```tsx
<AnalysisProgress
  status="evaluating"
  progress={{
    total_repos: 288,
    scored: 288,
    categorized: 288,
    evaluated: 6,
    to_evaluate: 12,
    percentage: 55
  }}
/>
```
