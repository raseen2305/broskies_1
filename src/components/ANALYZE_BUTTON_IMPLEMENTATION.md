# AnalyzeButton Component Implementation

## Overview
The AnalyzeButton component provides a user-initiated analysis interface for repository categorization and evaluation, implementing Requirements 2.1-2.7 from the intelligent-repo-scoring spec.

## Features Implemented

### 1. Button States (Ready, Loading, Complete)
- **Ready State**: Displays when analysis has not been performed
  - Shows "Analyze Repositories" button with clear call-to-action
  - Gradient background (primary-50 to blue-50)
  - Search icon and descriptive text
  
- **Loading State**: Displays during analysis
  - Animated spinner and progress bar
  - Real-time percentage display
  - Phase indicators (Scoring → Categorizing → Evaluating → Complete)
  - Current status message with evaluated count
  
- **Complete State**: Displays after successful analysis
  - Green success indicator with checkmark
  - Shows "Analyzed X hours/days ago" timestamp
  - Re-analyze button for refreshing results

### 2. Click Handler to Initiate Analysis
- Calls `scanAPI.initiateAnalysis(username, 15)` 
- Handles max_evaluate parameter (default: 15 repositories)
- Sets up initial analysis state with analysis_id

### 3. Analysis Status and Progress
- Polls analysis status every 2 seconds using `scanAPI.getAnalysisStatus()`
- Displays progress information:
  - Overall percentage (0-100%)
  - Current phase message
  - Evaluated count (X of Y repositories)
- Phase-specific messages:
  - "Starting analysis..."
  - "Calculating importance scores..."
  - "Categorizing repositories..."
  - "Evaluating X of Y repositories..."
  - "Calculating overall score..."
  - "Analysis complete!"

### 4. Re-analyze Functionality
- Shows confirmation dialog before re-analyzing
- Warns user that previous results will be replaced
- Provides "Confirm Re-analyze" and "Cancel" options
- Clears previous state and initiates fresh analysis

### 5. Error Handling
- Displays error state with red gradient background
- Shows specific error message
- Provides "Retry" button to restart analysis
- Handles API failures gracefully

## API Integration

### New API Methods Added to `scanAPI`:


```typescript
// Initiate analysis
initiateAnalysis(username: string, maxEvaluate: number = 15)

// Get analysis status (for polling)
getAnalysisStatus(username: string, analysisId: string)

// Get analysis results
getAnalysisResults(username: string, analysisId: string)
```

## Component Props

```typescript
interface AnalyzeButtonProps {
  username: string;              // GitHub username to analyze
  analyzed: boolean;             // Whether analysis has been completed
  analyzedAt?: string;           // Timestamp of last analysis
  onAnalysisComplete?: () => void; // Callback when analysis finishes
  className?: string;            // Additional CSS classes
}
```

## Usage Example

```tsx
import AnalyzeButton from '../AnalyzeButton';

<AnalyzeButton
  username={githubUsername}
  analyzed={scanResults?.analyzed || false}
  analyzedAt={scanResults?.analyzedAt}
  onAnalysisComplete={() => {
    // Reload scan results or update UI
    window.location.reload();
  }}
/>
```

## Integration with Repositories Page

The component has been integrated into `src/components/dashboard/Repositories.tsx`:
- Only displays for external user scans (`scanType === 'other'`)
- Positioned below the page header
- Triggers page reload on analysis completion to show updated results

## Visual Design

### Color Schemes by State:
- **Ready**: Primary blue gradient (from-primary-50 to-blue-50)
- **Loading**: Blue/indigo gradient (from-blue-50 to-indigo-50)
- **Complete**: Green gradient (from-green-50 to-emerald-50)
- **Confirm**: Yellow/orange gradient (from-yellow-50 to-orange-50)
- **Error**: Red/pink gradient (from-red-50 to-pink-50)

### Animations:
- Smooth fade-in/fade-out transitions using Framer Motion
- Animated progress bar with width transition
- Spinning loader icon during analysis
- Scale animation for confirmation dialog

## Requirements Coverage

✅ **2.1**: Display "Analyze Repositories" button at top of page
✅ **2.2**: Show button in enabled state with clear call-to-action text
✅ **2.3**: Disable button and show loading state on click
✅ **2.4**: Display progress indicator showing current phase
✅ **2.5**: Update UI with results on completion
✅ **2.6**: Hide/disable button after analysis complete (shows re-analyze instead)
✅ **2.7**: Re-enable button and show error message with retry option on failure

## Technical Implementation Details

### State Management:
- `isAnalyzing`: Boolean flag for loading state
- `analysisStatus`: Full status object with progress details
- `error`: Error message string
- `showReanalyzeConfirm`: Boolean for confirmation dialog

### Polling Strategy:
- 2-second interval for status checks
- Automatic cleanup on component unmount
- Stops polling on completion or failure

### Time Formatting:
- Displays relative time (e.g., "2 hours ago", "3 days ago")
- Handles edge cases ("just now" for recent analyses)

## Files Modified

1. **Created**: `src/components/AnalyzeButton.tsx` (new component)
2. **Modified**: `src/services/api.ts` (added 3 new API methods)
3. **Modified**: `src/components/dashboard/Repositories.tsx` (integrated component)

## Testing Recommendations

1. Test all button states (ready, loading, complete, error)
2. Verify polling behavior and cleanup
3. Test re-analyze confirmation flow
4. Verify error handling and retry functionality
5. Test with different analysis durations
6. Verify timestamp formatting for various time ranges
7. Test component unmounting during active analysis

## Next Steps

The component is ready for use. Next tasks in the spec include:
- Task 10: Create Frontend Analysis Progress Component (separate detailed progress view)
- Task 11: Update Repository Card Component (show categories and scores)
- Task 12: Update Repositories Page Layout (filters and sorting)
