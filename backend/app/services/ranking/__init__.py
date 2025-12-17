"""
Ranking Services
Calculates and manages regional and university rankings
"""

from .regional_calculator import RegionalRankingCalculator
from .university_calculator import UniversityRankingCalculator

__all__ = [
    'RegionalRankingCalculator',
    'UniversityRankingCalculator'
]
