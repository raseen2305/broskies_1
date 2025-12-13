import React from 'react';
import { motion } from 'framer-motion';
import { X, SlidersHorizontal } from 'lucide-react';

/**
 * Filter state interface
 */
export interface CandidateFilters {
  language?: string;
  min_score?: number;
  max_score?: number;
  role?: string;
  search?: string;
}

interface FilterPanelProps {
  filters: CandidateFilters;
  onFilterChange: (filters: CandidateFilters) => void;
  className?: string;
}

/**
 * FilterPanel Component
 * 
 * A comprehensive filter panel for candidate search with multiple filter options.
 * 
 * Features:
 * - Language filter dropdown (JavaScript, Python, Java, TypeScript, Go, etc.)
 * - Skill level range slider (0-10 score range)
 * - Role category checkboxes (Full-Stack, Frontend, Backend, Mobile, DevOps)
 * - "Clear Filters" button
 * - Emits filter changes to parent component
 * - Collapsible design
 * - Active filter count badge
 * 
 * @example
 * ```tsx
 * const [filters, setFilters] = useState<CandidateFilters>({});
 * 
 * <FilterPanel 
 *   filters={filters}
 *   onFilterChange={setFilters}
 * />
 * ```
 */
const FilterPanel: React.FC<FilterPanelProps> = ({
  filters,
  onFilterChange,
  className = '',
}) => {
  // Available filter options
  const languages = [
    'All Languages',
    'JavaScript',
    'TypeScript',
    'Python',
    'Java',
    'Go',
    'Rust',
    'C++',
    'C#',
    'PHP',
    'Ruby',
    'Swift',
    'Kotlin',
    'Dart',
  ];

  const roles = [
    'Full-Stack Developer',
    'Frontend Developer',
    'Backend Developer',
    'Mobile Developer',
    'DevOps Engineer',
    'Data Engineer',
    'ML Engineer',
  ];

  /**
   * Handle language filter change
   */
  const handleLanguageChange = (language: string) => {
    onFilterChange({
      ...filters,
      language: language === 'All Languages' ? undefined : language,
    });
  };

  /**
   * Handle role filter change
   */
  const handleRoleChange = (role: string) => {
    onFilterChange({
      ...filters,
      role: filters.role === role ? undefined : role,
    });
  };

  /**
   * Handle score range change
   */
  const handleMinScoreChange = (value: number) => {
    onFilterChange({
      ...filters,
      min_score: value,
    });
  };

  const handleMaxScoreChange = (value: number) => {
    onFilterChange({
      ...filters,
      max_score: value,
    });
  };

  /**
   * Clear all filters
   */
  const handleClearFilters = () => {
    onFilterChange({});
  };

  /**
   * Count active filters
   */
  const getActiveFilterCount = (): number => {
    let count = 0;
    if (filters.language) count++;
    if (filters.min_score && filters.min_score > 0) count++;
    if (filters.max_score && filters.max_score < 10) count++;
    if (filters.role) count++;
    return count;
  };

  const activeFilterCount = getActiveFilterCount();

  return (
    <div className={`bg-white rounded-lg border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <SlidersHorizontal className="h-5 w-5 text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">Filters</h3>
          {activeFilterCount > 0 && (
            <span className="bg-primary-500 text-white text-xs font-medium px-2 py-1 rounded-full">
              {activeFilterCount}
            </span>
          )}
        </div>
        {activeFilterCount > 0 && (
          <button
            onClick={handleClearFilters}
            className="text-sm text-gray-500 hover:text-gray-700 flex items-center space-x-1 transition-colors"
          >
            <X className="h-4 w-4" />
            <span>Clear All</span>
          </button>
        )}
      </div>

      {/* Filter Sections */}
      <div className="p-4 space-y-6">
        {/* Language Filter */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Programming Language
          </label>
          <select
            value={filters.language || 'All Languages'}
            onChange={(e) => handleLanguageChange(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
          >
            {languages.map((language) => (
              <option key={language} value={language}>
                {language}
              </option>
            ))}
          </select>
          {filters.language && (
            <p className="mt-1 text-xs text-gray-500">
              Showing candidates who use {filters.language}
            </p>
          )}
        </div>

        {/* Skill Level Range Slider */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Skill Level (Score Range)
          </label>
          
          {/* Min Score */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-gray-600">Minimum Score</span>
              <span className="text-sm font-semibold text-primary-600">
                {filters.min_score !== undefined ? filters.min_score.toFixed(1) : '0.0'}
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="10"
              step="0.5"
              value={filters.min_score || 0}
              onChange={(e) => handleMinScoreChange(parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-500"
            />
          </div>

          {/* Max Score */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs text-gray-600">Maximum Score</span>
              <span className="text-sm font-semibold text-primary-600">
                {filters.max_score !== undefined ? filters.max_score.toFixed(1) : '10.0'}
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="10"
              step="0.5"
              value={filters.max_score !== undefined ? filters.max_score : 10}
              onChange={(e) => handleMaxScoreChange(parseFloat(e.target.value))}
              className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-500"
            />
          </div>

          <div className="flex justify-between text-xs text-gray-500 mt-2">
            <span>0.0</span>
            <span>5.0</span>
            <span>10.0</span>
          </div>
        </div>

        {/* Role Category Checkboxes */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-3">
            Role Category
          </label>
          <div className="space-y-2 max-h-48 overflow-y-auto">
            {roles.map((role) => (
              <motion.label
                key={role}
                whileHover={{ x: 2 }}
                className="flex items-center cursor-pointer group"
              >
                <input
                  type="checkbox"
                  checked={filters.role === role}
                  onChange={() => handleRoleChange(role)}
                  className="rounded border-gray-300 text-primary-500 focus:ring-primary-500 cursor-pointer"
                />
                <span className="ml-2 text-sm text-gray-700 group-hover:text-gray-900 transition-colors">
                  {role}
                </span>
              </motion.label>
            ))}
          </div>
          {filters.role && (
            <p className="mt-2 text-xs text-gray-500">
              Showing {filters.role} candidates
            </p>
          )}
        </div>

        {/* Clear Filters Button */}
        {activeFilterCount > 0 && (
          <motion.button
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            onClick={handleClearFilters}
            className="w-full px-4 py-2 bg-gray-100 text-gray-700 font-medium rounded-lg hover:bg-gray-200 transition-colors flex items-center justify-center space-x-2"
          >
            <X className="h-4 w-4" />
            <span>Clear All Filters</span>
          </motion.button>
        )}
      </div>

      {/* Active Filters Summary */}
      {activeFilterCount > 0 && (
        <div className="p-4 bg-gray-50 border-t border-gray-200">
          <p className="text-xs font-medium text-gray-600 mb-2">Active Filters:</p>
          <div className="flex flex-wrap gap-2">
            {filters.language && (
              <span className="inline-flex items-center px-2 py-1 bg-white border border-gray-200 rounded-md text-xs">
                <span className="text-gray-600">Language:</span>
                <span className="ml-1 font-medium text-gray-900">{filters.language}</span>
                <button
                  onClick={() => handleLanguageChange('All Languages')}
                  className="ml-1 text-gray-400 hover:text-gray-600"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            {filters.min_score !== undefined && filters.min_score > 0 && (
              <span className="inline-flex items-center px-2 py-1 bg-white border border-gray-200 rounded-md text-xs">
                <span className="text-gray-600">Min Score:</span>
                <span className="ml-1 font-medium text-gray-900">{filters.min_score.toFixed(1)}</span>
                <button
                  onClick={() => handleMinScoreChange(0)}
                  className="ml-1 text-gray-400 hover:text-gray-600"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            {filters.max_score !== undefined && filters.max_score < 10 && (
              <span className="inline-flex items-center px-2 py-1 bg-white border border-gray-200 rounded-md text-xs">
                <span className="text-gray-600">Max Score:</span>
                <span className="ml-1 font-medium text-gray-900">{filters.max_score.toFixed(1)}</span>
                <button
                  onClick={() => handleMaxScoreChange(10)}
                  className="ml-1 text-gray-400 hover:text-gray-600"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            {filters.role && (
              <span className="inline-flex items-center px-2 py-1 bg-white border border-gray-200 rounded-md text-xs">
                <span className="text-gray-600">Role:</span>
                <span className="ml-1 font-medium text-gray-900">{filters.role}</span>
                <button
                  onClick={() => handleRoleChange(filters.role!)}
                  className="ml-1 text-gray-400 hover:text-gray-600"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default FilterPanel;
