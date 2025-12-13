# GitHub Developer Scoring System

Two-stage scoring system with instant feedback and deep code analysis.

## Architecture

```
backend/scoring/
├── __init__.py                 # Package initialization
├── config.py                   # Configuration and constants
├── README.md                   # This file
│
├── base/                       # Base interfaces and abstract classes
│   ├── __init__.py
│   ├── scorer.py              # BaseScorer interface
│   ├── analyzer.py            # BaseAnalyzer interface
│   └── orchestrator.py        # BaseOrchestrator interface
│
├── utils/                      # Utility functions
│   ├── __init__.py
│   ├── logger.py              # Logging utilities
│   ├── validators.py          # Validation functions
│   └── helpers.py             # Helper functions
│
├── github/                     # GitHub API services (to be created)
│   ├── __init__.py
│   ├── graphql_service.py     # GraphQL API client
│   ├── rest_service.py        # REST API client
│   └── rate_limiter.py        # Rate limiting
│
├── scoring/                    # Scoring services (to be created)
│   ├── __init__.py
│   ├── importance_scorer.py   # Repository importance scoring
│   ├── acid_scorer.py         # ACID code quality scoring
│   ├── complexity_analyzer.py # Code complexity analysis
│   └── overall_calculator.py  # Overall score calculation
│
├── orchestration/              # Workflow orchestration (to be created)
│   ├── __init__.py
│   ├── scan_orchestrator.py   # Stage 1 orchestration
│   ├── analysis_orchestrator.py # Stage 2 orchestration
│   └── progress_tracker.py    # Progress tracking
│
├── storage/                    # Database operations (to be created)
│   ├── __init__.py
│   ├── user_storage.py        # User data operations
│   ├── repository_storage.py  # Repository data operations
│   ├── analysis_storage.py    # Analysis results storage
│   └── ranking_storage.py     # Rankings storage
│
└── analytics/                  # Analytics generation (to be created)
    ├── __init__.py
    ├── score_breakdown.py     # Score breakdowns
    ├── insights_generator.py  # Insights generation
    └── recommendations.py     # Recommendations engine
```

## Configuration

All configuration is centralized in `config.py`:

```python
from backend.scoring.config import get_config

config = get_config()
print(config.FLAGSHIP_THRESHOLD)  # 70.0
```

## Base Classes

### BaseScorer

All scoring services inherit from `BaseScorer`:

```python
from backend.scoring.base import BaseScorer

class MyScorer(BaseScorer):
    def calculate_score(self, data):
        # Implementation
        pass
    
    def validate_input(self, data):
        # Validation
        pass
```

### BaseAnalyzer

All code analyzers inherit from `BaseAnalyzer`:

```python
from backend.scoring.base import BaseAnalyzer

class MyAnalyzer(BaseAnalyzer):
    async def analyze(self, code_files):
        # Analysis implementation
        pass
    
    def supports_language(self, language):
        return language in ['Python', 'JavaScript']
```

### BaseOrchestrator

All orchestrators inherit from `BaseOrchestrator`:

```python
from backend.scoring.base import BaseOrchestrator

class MyOrchestrator(BaseOrchestrator):
    async def execute(self, user_id, github_token, progress_callback=None):
        self.start_timer()
        # Orchestration logic
        duration = self.stop_timer()
        return results
```

## Utilities

### Logging

```python
from backend.scoring.utils import setup_logger, get_logger

logger = setup_logger('my_service')
logger.info("Service started")
```

### Validation

```python
from backend.scoring.utils import validate_repository_data

if validate_repository_data(repo):
    # Process repository
    pass
```

### Helpers

```python
from backend.scoring.utils import round_score, calculate_percentage, safe_divide

score = round_score(85.678, decimals=1)  # 85.7
percentage = calculate_percentage(15, 20)  # 75.0
result = safe_divide(10, 0, default=0.0)  # 0.0
```

## Development Guidelines

1. **All new services must inherit from base classes**
2. **Use the centralized configuration**
3. **Use the logging utilities**
4. **Validate all inputs**
5. **Write async code where appropriate**
6. **Add type hints**
7. **Document all public methods**

## Testing

Tests should be placed in `backend/tests/scoring/` and mirror the structure:

```
backend/tests/scoring/
├── test_config.py
├── test_base/
├── test_utils/
├── test_github/
├── test_scoring/
├── test_orchestration/
├── test_storage/
└── test_analytics/
```

## Next Steps

1. Implement GitHub API services
2. Implement scoring services
3. Implement orchestration services
4. Implement storage services
5. Implement analytics services
6. Add comprehensive tests
