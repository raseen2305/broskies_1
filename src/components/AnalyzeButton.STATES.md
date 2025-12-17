# AnalyzeButton Component States

## State 1: Ready (Not Analyzed)
```
┌─────────────────────────────────────────────────────────────────┐
│  🔍  Analyze Repositories                    [Start Analysis]   │
│  Categorize and evaluate your projects to get detailed insights │
└─────────────────────────────────────────────────────────────────┘
```
- **Background**: Primary blue gradient
- **Icon**: Search (🔍)
- **Action**: Click "Start Analysis" button

## State 2: Loading (Analyzing)
```
┌─────────────────────────────────────────────────────────────────┐
│  ⏳  Analyzing Repositories...                            42%   │
│  ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   │
│  Evaluating 5 of 12 repositories...          5 / 12 evaluated  │
│  ✓ Scoring  ✓ Categorizing  ⏳ Evaluating  ○ Complete          │
└─────────────────────────────────────────────────────────────────┘
```
- **Background**: Blue/indigo gradient
- **Icon**: Spinning loader (⏳)
- **Features**: 
  - Animated progress bar
  - Real-time percentage
  - Phase indicators
  - Evaluated count

## State 3: Complete (Analyzed)
```
┌─────────────────────────────────────────────────────────────────┐
│  ✅  Analysis Complete                          [Re-analyze]    │
│      Analyzed 2 hours ago                                       │
└─────────────────────────────────────────────────────────────────┘
```
- **Background**: Green gradient
- **Icon**: Check circle (✅)
- **Features**:
  - Relative timestamp
  - Re-analyze button

## State 4: Confirm Re-analyze
```
┌─────────────────────────────────────────────────────────────────┐
│  ⚠️  Re-analyze Repositories?                                   │
│  This will replace your previous analysis results with new data │
│  The process may take 45-60 seconds.                           │
│  [Confirm Re-analyze]  [Cancel]                                │
└─────────────────────────────────────────────────────────────────┘
```
- **Background**: Yellow/orange gradient
- **Icon**: Alert circle (⚠️)
- **Actions**: Confirm or Cancel

## State 5: Error
```
┌─────────────────────────────────────────────────────────────────┐
│  ❌  Analysis Failed                              [Retry]       │
│      Failed to fetch analysis status                           │
└─────────────────────────────────────────────────────────────────┘
```
- **Background**: Red/pink gradient
- **Icon**: Alert circle (❌)
- **Action**: Retry button

## State Transitions

```
Ready ──[Click]──> Loading ──[Success]──> Complete
  ↑                   │                      │
  │                   │                      │
  │              [Error]                [Re-analyze]
  │                   │                      │
  │                   ↓                      ↓
  └───────────────── Error ←──[Retry]── Confirm
                                             │
                                        [Cancel]
                                             │
                                             ↓
                                         Complete
```

## Progress Phases

1. **Started** (0%)
   - "Starting analysis..."

2. **Scoring** (0-20%)
   - "Calculating importance scores..."
   - All repositories scored

3. **Categorizing** (20-30%)
   - "Categorizing repositories..."
   - Repositories sorted into flagship/significant/supporting

4. **Evaluating** (30-90%)
   - "Evaluating X of Y repositories..."
   - Deep evaluation of selected repositories
   - Progress updates as each repo completes

5. **Calculating** (90-100%)
   - "Calculating overall score..."
   - Weighted average calculation

6. **Complete** (100%)
   - "Analysis complete!"
   - Results cached for 24 hours
