# AnalysisProgress Component Implementation

## Overview
The AnalysisProgress component provides a detailed, standalone progress display for repository analysis, implementing Requirements 6.1-6.7 from the intelligent-repo-scoring spec.

## Features Implemented

### 1. Progress Bar with Percentage
- Animated progress bar (0-100%)
- Smooth transitions using Framer Motion
- Gradient color scheme (blue to indigo)
- Large percentage display (2xl font)

### 2. Current Phase Message
- Dynamic status messages based on analysis phase:
  - "Starting analysis..."
  - "Calculating importance scores..."
  - "Categorizing repositories..."
  - "Evaluating X of Y repositories..."
  - "Calculating overall score..."
  - "Analysis complete! X repositories evaluated"

### 3. Evaluated Count Display (X of Y)
- Shows current progress during evaluation phase
- Displays "X / Y" format
- Updates in real-time as repositories are evaluated

### 4. Real-Time Updates
- Designed for polling or WebSocket integration
- Accepts status updates via props
- Smooth animations on state changes
- Progressive disclosure of details

### 5. Phase Indicators
- Visual timeline showing 4 phases:
  - Scoring
  - Categorizing
  - Evaluating
  - Calculating
- Icons change based on phase status:
  - ✓ Completed (green checkmark)
  - ⏳ In Progress (spinning loader)
  - ○ Pending (gray circle)
- Connecting lines show progress flow

### 6. Detailed Statistics (Evaluation Phase)
- Shows 3 key metrics:
  - Total Repos
  - To Evaluate
  - Evaluated
- Animated appearance during evaluation phase
- Grid layout for easy scanning

## Component Props

```typescript
interface AnalysisProgressProps {
  status: 'started' | 'scoring' | 'categorizing' | 'evaluating' | 'calculating' | 'complete' | 'failed';
  progress: {
    total_repos: number;
    scored: number;
    categorized: number;
    evaluated: number;
    to_evaluate: number;
    percentage: number;
    current_message?: string;
  };
  message?: string;
  error?: string;
  className?: string;
}
```

## Usage Examples

### Example 1: Basic Usage with Polling
```tsx
import AnalysisProgress from '../components/AnalysisProgress';
import { scanAPI } from '../services/api';

function RepositoriesPage() {
  const [analysisStatus, setAnalysisStatus] = useState(null);

  useEffect(() => {
    if (!analysisStatus?.analysis_id) return;

    const pollInterval = setInterval(async () => {
      const status = await scanAPI.getAnalysisStatus(username, analysisStatus.analysis_id);
      setAnalysisStatus(status);

      if (status.status === 'complete' || status.status === 'failed') {
        clearInterval(pollInterval);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [analysisStatus?.analysis_id]);

  return (
    <div>
      {analysisStatus && (
        <AnalysisProgress
          status={analysisStatus.status}
          progress={analysisStatus.progress}
          message={analysisStatus.message}
          error={analysisStatus.error}
        />
      )}
    </div>
  );
}
```

### Example 2: Integration with AnalyzeButton
```tsx
import AnalyzeButton from '../components/AnalyzeButton';
import AnalysisProgress from '../components/AnalysisProgress';

function RepositoriesPage() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStatus, setAnalysisStatus] = useState(null);

  return (
    <div className="space-y-6">
      {!isAnalyzing && (
        <AnalyzeButton
          username={username}
          analyzed={analyzed}
          onAnalysisComplete={() => {
            setIsAnalyzing(false);
            // Reload data
          }}
        />
      )}

      {isAnalyzing && analysisStatus && (
        <AnalysisProgress
          status={analysisStatus.status}
          progress={analysisStatus.progress}
        />
      )}
    </div>
  );
}
```

### Example 3: Overview Tab Integration
```tsx
function Overview({ scanResults }) {
  const [analysisStatus, setAnalysisStatus] = useState(null);

  if (!scanResults.analyzed && !analysisStatus) {
    return <AnalyzeButton username={scanResults.username} />;
  }

  if (analysisStatus && analysisStatus.status !== 'complete') {
    return (
      <AnalysisProgress
        status={analysisStatus.status}
        progress={analysisStatus.progress}
      />
    );
  }

  return <ScoreInfographic score={scanResults.overallScore} />;
}
```

## Visual States

### State 1: Scoring Phase
```
┌─────────────────────────────────────────────────────────────┐
│  ⏳ Analyzing Repositories                            15%   │
│  ████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   │
│  Calculating importance scores...                          │
│  ✓ Scoring  ○ Categorizing  ○ Evaluating  ○ Calculating   │
└─────────────────────────────────────────────────────────────┘
```

### State 2: Categorizing Phase
```
┌─────────────────────────────────────────────────────────────┐
│  ⏳ Analyzing Repositories                            25%   │
│  ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   │
│  Categorizing repositories...                              │
│  ✓ Scoring  ⏳ Categorizing  ○ Evaluating  ○ Calculating   │
└─────────────────────────────────────────────────────────────┘
```

### State 3: Evaluating Phase (with details)
```
┌─────────────────────────────────────────────────────────────┐
│  ⏳ Analyzing Repositories                            65%   │
│  ████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░   │
│  Evaluating 8 of 12 repositories...              8 / 12    │
│  ✓ Scoring  ✓ Categorizing  ⏳ Evaluating  ○ Calculating   │
│  ─────────────────────────────────────────────────────────  │
│       288              12               8                   │
│   Total Repos      To Evaluate      Evaluated               │
└─────────────────────────────────────────────────────────────┘
```

### State 4: Complete
```
┌─────────────────────────────────────────────────────────────┐
│  ✅ Analysis Complete                                       │
│  Analysis complete! 12 repositories evaluated               │
└─────────────────────────────────────────────────────────────┘
```

### State 5: Failed
```
┌─────────────────────────────────────────────────────────────┐
│  ❌ Analysis Failed                                         │
│  Failed to evaluate repositories: Rate limit exceeded       │
└─────────────────────────────────────────────────────────────┘
```

## Color Schemes

- **In Progress**: Blue gradient (bg-blue-50, border-blue-200)
- **Complete**: Green gradient (bg-green-50, border-green-200)
- **Failed**: Red gradient (bg-red-50, border-red-200)

## Animations

1. **Initial Appearance**: Fade in with slide down (opacity + y-axis)
2. **Progress Bar**: Smooth width transition (0.5s ease-out)
3. **Details Panel**: Fade in with height expansion (evaluation phase)
4. **Phase Icons**: Instant state changes with color transitions

## Requirements Coverage

✅ **6.1**: Display progress indicator showing "Analyzing repositories..."
✅ **6.2**: Show progress message "Calculating importance scores..."
✅ **6.3**: Show progress message "Categorizing repositories..."
✅ **6.4**: Show progress message "Evaluating X of Y repositories..."
✅ **6.5**: Update progress counter as each repository completes
✅ **6.6**: Show success message "Analysis complete! X repositories evaluated"
✅ **6.7**: Show error messages with details

## Technical Implementation

### Phase Detection Logic
```typescript
const getPhaseIcon = (phase: string, currentStatus: string) => {
  const phaseOrder = ['scoring', 'categorizing', 'evaluating', 'calculating', 'complete'];
  const currentIndex = phaseOrder.indexOf(currentStatus);
  const phaseIndex = phaseOrder.indexOf(phase);

  if (phaseIndex < currentIndex || currentStatus === 'complete') {
    return <CheckCircle />; // Completed
  } else if (phaseIndex === currentIndex) {
    return <Loader2 className="animate-spin" />; // In Progress
  } else {
    return <div className="rounded-full border-2" />; // Pending
  }
};
```

### Dynamic Message Generation
```typescript
const getStatusMessage = () => {
  if (error) return error;
  if (message) return message;
  if (progress.current_message) return progress.current_message;

  switch (status) {
    case 'scoring': return 'Calculating importance scores...';
    case 'categorizing': return 'Categorizing repositories...';
    case 'evaluating': return `Evaluating ${progress.evaluated} of ${progress.to_evaluate} repositories...`;
    case 'calculating': return 'Calculating overall score...';
    case 'complete': return `Analysis complete! ${progress.evaluated} repositories evaluated`;
    default: return 'Processing...';
  }
};
```

## Differences from AnalyzeButton

The AnalysisProgress component is a **standalone progress display** that:
- Focuses solely on showing progress (no button functionality)
- Can be used independently in any part of the UI
- Provides more detailed statistics during evaluation
- Has cleaner separation of concerns
- Better for dedicated progress views (e.g., Overview tab)

The AnalyzeButton component:
- Combines button + progress in one component
- Handles analysis initiation
- Manages polling internally
- Better for inline usage (e.g., top of Repositories page)

## Files Created

1. **src/components/AnalysisProgress.tsx** - Main component
2. **src/components/ANALYSIS_PROGRESS_IMPLEMENTATION.md** - This documentation

## Next Steps

The component is ready for integration. Recommended usage:
1. Use in Overview tab to show analysis progress
2. Use in dedicated analysis status page
3. Use alongside AnalyzeButton for detailed progress view
4. Consider WebSocket integration for real-time updates (currently polling-based)
