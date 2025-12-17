import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { GitBranch, Star, GitFork, Calendar, Search, ExternalLink, Code, Users, AlertCircle, CheckCircle } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { scanAPI } from '../../services/api';
import AnalyzeButton from '../AnalyzeButton';

interface RepositoriesProps {
  scanResults?: any;
  onRepositoryClick?: (repoName: string) => void;
}

interface Repository {
  id: string;
  name: string;
  full_name: string;
  description: string;
  language: string;
  stargazers_count: number;
  forks_count: number;
  watchers_count: number;
  size: number;
  updated_at: string;
  created_at: string;
  pushed_at: string;
  html_url: string;
  clone_url: string;
  topics: string[];
  license?: {
    name: string;
  };
  category?: string;  // Repository category: flagship, significant, supporting
  importance_score?: number;  // Importance score (0-100)
  analysis?: {
    acid_scores?: {
      atomicity: number;
      consistency: number;
      isolation: number;
      durability: number;
      overall: number;
    };
    quality_metrics?: {
      readability: number;
      maintainability: number;
      security: number;
      test_coverage: number;
      documentation: number;
    };
  };
  code_metrics?: {
    lines_of_code: number;
    files_count: number;
    complexity_score: number;
  };
  commit_activity?: Array<{
    date: string;
    commits: number;
  }>;
  contributors?: Array<{
    login: string;
    contributions: number;
  }>;
}

const Repositories: React.FC<RepositoriesProps> = ({ scanResults, onRepositoryClick }) => {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const handleRepositoryClick = (repoName: string) => {
    if (onRepositoryClick) {
      // Modal mode - use callback
      onRepositoryClick(repoName);
    } else {
      // Normal mode - use navigation
      navigate(`/developer/dashboard/repositories/${repoName}`);
    }
  };
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('stars');
  const [filterLanguage, setFilterLanguage] = useState('all');
  const [filterCategory, setFilterCategory] = useState<string>('all');
  
  // Get the GitHub username from scan results
  const githubUsername = scanResults?.targetUsername || scanResults?.userInfo?.login || scanResults?.userInfo?.username;

  useEffect(() => {
    const loadRepositories = async () => {
      if (scanResults?.repositories || scanResults?.repositoryDetails) {
        // Use scan results if available
        console.log('📊 [Repositories] scanResults.repositories exists:', !!scanResults.repositories);
        console.log('📊 [Repositories] scanResults.repositoryDetails exists:', !!scanResults.repositoryDetails);
        
        // Check which has categories
        const reposWithCat = scanResults.repositories?.filter((r: any) => r.category).length || 0;
        const detailsWithCat = scanResults.repositoryDetails?.filter((r: any) => r.category).length || 0;
        console.log('📊 [Repositories] repositories with categories:', reposWithCat);
        console.log('📊 [Repositories] repositoryDetails with categories:', detailsWithCat);
        
        // Prefer repositories over repositoryDetails if it has categories
        const repos = (scanResults.repositories && reposWithCat > 0) 
          ? scanResults.repositories 
          : (scanResults.repositoryDetails || scanResults.repositories || []);
        
        console.log('📊 [Repositories] Loading repos:', repos.length);
        console.log('📊 [Repositories] With categories:', repos.filter((r: any) => r.category).length);
        console.log('📊 [Repositories] Sample repo:', repos[0]);
        setRepositories(repos);
        setIsLoading(false);
      } else if (user?.id) {
        // Fallback to API call
        try {
          setIsLoading(true);
          setError(null);
          const response = await scanAPI.getUserRepositories(user.id);
          setRepositories(response.repositories || []);
        } catch (error: any) {
          console.error('Failed to load repositories:', error);
          setError('Failed to load repositories. Please scan a GitHub profile first.');
        } finally {
          setIsLoading(false);
        }
      } else {
        setIsLoading(false);
        setError('No repository data available. Please scan a GitHub profile first.');
      }
    };

    loadRepositories();
  }, [scanResults, user?.id]);

  // Get unique languages for filter
  const languages = ['all', ...Array.from(new Set(repositories.map(repo => repo.language).filter(Boolean)))];

  // Get category counts
  const categoryCounts = {
    all: repositories.length,
    flagship: repositories.filter(r => r.category === 'flagship').length,
    significant: repositories.filter(r => r.category === 'significant').length,
    supporting: repositories.filter(r => r.category === 'supporting').length
  };

  // Filter and sort repositories
  const filteredRepositories = repositories
    .filter(repo => 
      repo.name.toLowerCase().includes(searchTerm.toLowerCase()) &&
      (filterLanguage === 'all' || repo.language === filterLanguage) &&
      (filterCategory === 'all' || repo.category === filterCategory)
    )
    .sort((a, b) => {
      switch (sortBy) {
        case 'importance':
          const importanceA = a.importance_score || 0;
          const importanceB = b.importance_score || 0;
          return importanceB - importanceA;
        case 'evaluation':
          const evalA = a.evaluation?.overall_score || 0;
          const evalB = b.evaluation?.overall_score || 0;
          return evalB - evalA;
        case 'score':
          const scoreA = a.analysis?.acid_scores?.overall || a.evaluation?.overall_score || 0;
          const scoreB = b.analysis?.acid_scores?.overall || b.evaluation?.overall_score || 0;
          return scoreB - scoreA;
        case 'stars':
          return (b.stargazers_count || 0) - (a.stargazers_count || 0);
        case 'updated':
          return new Date(b.updated_at || 0).getTime() - new Date(a.updated_at || 0).getTime();
        case 'name':
          return a.name.localeCompare(b.name);
        default:
          return 0;
      }
    });

  const getLanguageColor = (language: string): string => {
    const colors: { [key: string]: string } = {
      'JavaScript': 'bg-yellow-100 text-yellow-800',
      'TypeScript': 'bg-blue-100 text-blue-800',
      'Python': 'bg-green-100 text-green-800',
      'Java': 'bg-red-100 text-red-800',
      'C++': 'bg-purple-100 text-purple-800',
      'C#': 'bg-indigo-100 text-indigo-800',
      'Go': 'bg-cyan-100 text-cyan-800',
      'Rust': 'bg-orange-100 text-orange-800',
      'PHP': 'bg-violet-100 text-violet-800',
      'Ruby': 'bg-pink-100 text-pink-800',
    };
    return colors[language] || 'bg-gray-100 text-gray-800';
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <div className="h-8 bg-gray-200 rounded w-48 mb-2 animate-pulse"></div>
            <div className="h-4 bg-gray-200 rounded w-64 animate-pulse"></div>
          </div>
        </div>
        <div className="grid gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="card p-6 animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-48 mb-4"></div>
              <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
              <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Repositories</h1>
          <p className="text-gray-600">Detailed analysis of scanned repositories</p>
        </div>
        <div className="card p-8 text-center">
          <div className="text-red-500 mb-4">
            <AlertCircle className="h-12 w-12 mx-auto" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Repository Data</h3>
          <p className="text-gray-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Repositories</h1>
        <p className="text-gray-600">
          Detailed analysis of {repositories.length} repositories
          {scanResults?.scanType === 'other' && ` from ${scanResults.username}`}
        </p>
      </div>

      {/* Analyze Button - Show for both self and external scans */}
      {githubUsername && (
        <AnalyzeButton
          username={githubUsername}
          analyzed={scanResults?.repositories?.some((r: any) => r.analysis?.acid_scores?.overall) || false}
          analyzedAt={scanResults?.analyzedAt}
          onAnalysisComplete={async () => {
            // AnalyzeButton already updated localStorage with analysis results
            // Wait a moment to ensure localStorage write completes, then reload
            console.log('Analysis complete, waiting for localStorage sync...');
            await new Promise(resolve => setTimeout(resolve, 200));
            console.log('Reloading to show categories...');
            window.location.reload();
          }}
        />
      )}

      {/* Category Filter Buttons - shown after analysis */}
      {scanResults?.analyzed && (categoryCounts.flagship > 0 || categoryCounts.significant > 0 || categoryCounts.supporting > 0) && (
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setFilterCategory('all')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              filterCategory === 'all'
                ? 'bg-primary-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All ({categoryCounts.all})
          </button>
          {categoryCounts.flagship > 0 && (
            <button
              onClick={() => setFilterCategory('flagship')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                filterCategory === 'flagship'
                  ? 'bg-yellow-500 text-white'
                  : 'bg-yellow-50 text-yellow-700 hover:bg-yellow-100 border border-yellow-200'
              }`}
            >
              🥇 Flagship ({categoryCounts.flagship})
            </button>
          )}
          {categoryCounts.significant > 0 && (
            <button
              onClick={() => setFilterCategory('significant')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                filterCategory === 'significant'
                  ? 'bg-blue-500 text-white'
                  : 'bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200'
              }`}
            >
              🥈 Significant ({categoryCounts.significant})
            </button>
          )}
          {categoryCounts.supporting > 0 && (
            <button
              onClick={() => setFilterCategory('supporting')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                filterCategory === 'supporting'
                  ? 'bg-gray-500 text-white'
                  : 'bg-gray-50 text-gray-700 hover:bg-gray-100 border border-gray-200'
              }`}
            >
              🥉 Supporting ({categoryCounts.supporting})
            </button>
          )}
        </div>
      )}

      {/* Filters and Search */}
      <div className="card p-6">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-5 w-5" />
              <input
                type="text"
                placeholder="Search repositories..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Language Filter */}
          <div>
            <select
              value={filterLanguage}
              onChange={(e) => setFilterLanguage(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              {languages.map(lang => (
                <option key={lang} value={lang}>
                  {lang === 'all' ? 'All Languages' : lang}
                </option>
              ))}
            </select>
          </div>

          {/* Sort */}
          <div>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="stars">Most Stars</option>
              {scanResults?.analyzed && <option value="importance">Importance Score</option>}
              {scanResults?.analyzed && <option value="evaluation">Evaluation Score</option>}
              <option value="score">Highest Score</option>
              <option value="updated">Recently Updated</option>
              <option value="name">Name (A-Z)</option>
            </select>
          </div>
        </div>
      </div>

      {/* Repository List */}
      {scanResults?.analyzed && filterCategory === 'all' && (categoryCounts.flagship > 0 || categoryCounts.significant > 0 || categoryCounts.supporting > 0) ? (
        /* Categorized View - Show repositories organized by category */
        <div className="space-y-8">
          {/* Flagship Repositories Section */}
          {categoryCounts.flagship > 0 && (
            <div>
              <div className="flex items-center space-x-3 mb-4">
                <div className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-yellow-100 to-yellow-50 rounded-lg border-2 border-yellow-300">
                  <span className="text-2xl">🏆</span>
                  <h2 className="text-xl font-bold text-yellow-900">Flagship Projects</h2>
                  <span className="px-2 py-1 bg-yellow-200 text-yellow-900 text-sm font-semibold rounded-full">
                    {categoryCounts.flagship}
                  </span>
                </div>
              </div>
              <p className="text-gray-600 mb-4 text-sm">Your most important and impactful repositories</p>
              <div className="grid gap-6">
                {filteredRepositories
                  .filter(repo => repo.category === 'flagship')
                  .map((repo, index) => (
                    <motion.div
                      key={repo.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="card p-6 hover:shadow-lg transition-shadow duration-200 border-l-4 border-yellow-400"
                    >
            <div className="flex flex-col space-y-4">
              {/* Header with title and badges */}
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <h3 className="text-lg sm:text-xl font-semibold text-gray-900 break-words">{repo.name}</h3>
                    {repo.language && (
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getLanguageColor(repo.language)}`}>
                        {repo.language}
                      </span>
                    )}
                    {/* Category Badge - shown after analysis */}
                    {repo.category && (
                      <span className={`px-2 sm:px-3 py-1 rounded-full text-xs font-semibold ${
                        repo.category === 'flagship' 
                          ? 'bg-yellow-100 text-yellow-800 border border-yellow-300'
                          : repo.category === 'significant'
                          ? 'bg-blue-100 text-blue-800 border border-blue-300'
                          : 'bg-gray-100 text-gray-700 border border-gray-300'
                      }`}>
                        {repo.category === 'flagship' && '🥇 '}
                        {repo.category === 'significant' && '🥈 '}
                        {repo.category === 'supporting' && '🥉 '}
                        {repo.category.charAt(0).toUpperCase() + repo.category.slice(1)}
                      </span>
                    )}
                  </div>
                  <p className="text-sm sm:text-base text-gray-600 mb-3">{repo.description || 'No description available'}</p>
                </div>

                {/* Score display - moves to top right on desktop, inline on mobile */}
                {(repo.evaluated && repo.evaluation?.overall_score) || (repo.analysis?.acid_scores?.overall) ? (
                  <div className="flex items-center gap-3 sm:flex-col sm:items-center">
                    {repo.evaluated && repo.evaluation?.overall_score ? (
                      <div className="text-center">
                        <div className={`text-xl sm:text-2xl font-bold ${getScoreColor(repo.evaluation.overall_score)}`}>
                          {repo.evaluation.overall_score}
                        </div>
                        <div className="text-xs text-gray-500">Eval Score</div>
                      </div>
                    ) : repo.analyzed && !repo.evaluated ? (
                      <div className="text-center px-3 py-2 bg-gray-50 rounded-lg border border-gray-200">
                        <div className="text-xs text-gray-500 font-medium">Not Evaluated</div>
                      </div>
                    ) : repo.analysis?.acid_scores?.overall ? (
                      <div className="text-center">
                        <div className={`text-xl sm:text-2xl font-bold ${getScoreColor(repo.analysis.acid_scores.overall)}`}>
                          {repo.analysis.acid_scores.overall}
                        </div>
                        <div className="text-xs text-gray-500">ACID Score</div>
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </div>
              
              {/* Repository Stats */}
              <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs sm:text-sm text-gray-500">
                <div className="flex items-center space-x-1">
                  <Star className="h-3 w-3 sm:h-4 sm:w-4" />
                  <span>{repo.stargazers_count || 0}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <GitFork className="h-3 w-3 sm:h-4 sm:w-4" />
                  <span>{repo.forks_count || 0}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Calendar className="h-3 w-3 sm:h-4 sm:w-4" />
                  <span className="hidden sm:inline">Updated {formatDate(repo.updated_at)}</span>
                  <span className="sm:hidden">{formatDate(repo.updated_at)}</span>
                </div>
                {repo.code_metrics?.lines_of_code && (
                  <div className="flex items-center space-x-1">
                    <Code className="h-3 w-3 sm:h-4 sm:w-4" />
                    <span>{(repo.code_metrics.lines_of_code || 0).toLocaleString()} lines</span>
                  </div>
                )}
                {/* Importance Score - shown after analysis */}
                {repo.importance_score !== undefined && repo.importance_score !== null && (
                  <div className="flex items-center space-x-1">
                    <span className="font-medium text-gray-700">Importance:</span>
                    <span className={`font-semibold ${getScoreColor(repo.importance_score)}`}>
                      {repo.importance_score}
                    </span>
                  </div>
                )}
              </div>

              {/* Action buttons */}
              <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 pt-2">
                <button
                  onClick={() => handleRepositoryClick(repo.name)}
                  className="flex-1 sm:flex-none inline-flex items-center justify-center px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
                >
                  <Code className="h-4 w-4 mr-1" />
                  Details
                </button>
                <a
                  href={repo.html_url || (repo.full_name ? `https://github.com/${repo.full_name}` : (githubUsername ? `https://github.com/${githubUsername}/${repo.name}` : '#'))}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex-1 sm:flex-none inline-flex items-center justify-center px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  <ExternalLink className="h-4 w-4 mr-1" />
                  GitHub
                </a>
              </div>
            </div>

            {/* Analysis Metrics */}
            {repo.analysis && (
              <div className="border-t pt-4">
                <h4 className="font-medium text-gray-900 mb-3">Code Quality Analysis</h4>
                
                {/* ACID Scores */}
                {repo.analysis.acid_scores && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                    <div className="text-center">
                      <div className={`text-lg font-semibold ${getScoreColor(repo.analysis.acid_scores.atomicity)}`}>
                        {repo.analysis.acid_scores.atomicity}
                      </div>
                      <div className="text-xs text-gray-500">Atomicity</div>
                    </div>
                    <div className="text-center">
                      <div className={`text-lg font-semibold ${getScoreColor(repo.analysis.acid_scores.consistency)}`}>
                        {repo.analysis.acid_scores.consistency}
                      </div>
                      <div className="text-xs text-gray-500">Consistency</div>
                    </div>
                    <div className="text-center">
                      <div className={`text-lg font-semibold ${getScoreColor(repo.analysis.acid_scores.isolation)}`}>
                        {repo.analysis.acid_scores.isolation}
                      </div>
                      <div className="text-xs text-gray-500">Isolation</div>
                    </div>
                    <div className="text-center">
                      <div className={`text-lg font-semibold ${getScoreColor(repo.analysis.acid_scores.durability)}`}>
                        {repo.analysis.acid_scores.durability}
                      </div>
                      <div className="text-xs text-gray-500">Durability</div>
                    </div>
                  </div>
                )}

                {/* Quality Metrics */}
                {repo.analysis.quality_metrics && (
                  <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div className="text-center">
                      <div className={`text-sm font-semibold ${getScoreColor(repo.analysis.quality_metrics.readability)}`}>
                        {repo.analysis.quality_metrics.readability}%
                      </div>
                      <div className="text-xs text-gray-500">Readability</div>
                    </div>
                    <div className="text-center">
                      <div className={`text-sm font-semibold ${getScoreColor(repo.analysis.quality_metrics.maintainability)}`}>
                        {repo.analysis.quality_metrics.maintainability}%
                      </div>
                      <div className="text-xs text-gray-500">Maintainability</div>
                    </div>
                    <div className="text-center">
                      <div className={`text-sm font-semibold ${getScoreColor(repo.analysis.quality_metrics.security)}`}>
                        {repo.analysis.quality_metrics.security}%
                      </div>
                      <div className="text-xs text-gray-500">Security</div>
                    </div>
                    <div className="text-center">
                      <div className={`text-sm font-semibold ${getScoreColor(repo.analysis.quality_metrics.test_coverage)}`}>
                        {repo.analysis.quality_metrics.test_coverage}%
                      </div>
                      <div className="text-xs text-gray-500">Test Coverage</div>
                    </div>
                    <div className="text-center">
                      <div className={`text-sm font-semibold ${getScoreColor(repo.analysis.quality_metrics.documentation)}`}>
                        {repo.analysis.quality_metrics.documentation}%
                      </div>
                      <div className="text-xs text-gray-500">Documentation</div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Topics */}
            {repo.topics && repo.topics.length > 0 && (
              <div className="border-t pt-4">
                <div className="flex flex-wrap gap-2">
                  {repo.topics.slice(0, 8).map(topic => (
                    <span
                      key={topic}
                      className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full"
                    >
                      {topic}
                    </span>
                  ))}
                  {repo.topics.length > 8 && (
                    <span className="px-2 py-1 bg-gray-50 text-gray-500 text-xs rounded-full">
                      +{repo.topics.length - 8} more
                    </span>
                  )}
                </div>
              </div>
            )}
          </motion.div>
        ))}
              </div>
            </div>
          )}

          {/* Significant Repositories Section */}
          {categoryCounts.significant > 0 && filteredRepositories.filter(r => r.category === 'significant').length > 0 && (
            <div>
              <div className="flex items-center space-x-3 mb-4">
                <div className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-100 to-blue-50 rounded-lg border-2 border-blue-300">
                  <span className="text-2xl">⭐</span>
                  <h2 className="text-xl font-bold text-blue-900">Significant Projects</h2>
                  <span className="px-2 py-1 bg-blue-200 text-blue-900 text-sm font-semibold rounded-full">
                    {filteredRepositories.filter(r => r.category === 'significant').length}
                  </span>
                </div>
              </div>
              <p className="text-gray-600 mb-4 text-sm">Important repositories with notable contributions</p>
              <div className="grid gap-6">
                {filteredRepositories
                  .filter(repo => repo.category === 'significant')
                  .map((repo, index) => (
                    <motion.div
                      key={repo.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="card p-6 hover:shadow-lg transition-shadow duration-200 border-l-4 border-blue-400"
                    >
                      {/* Same repository card content as above */}
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <h3 className="text-xl font-semibold text-gray-900">{repo.name}</h3>
                            {repo.language && (
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getLanguageColor(repo.language)}`}>
                                {repo.language}
                              </span>
                            )}
                            {repo.category && (
                              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                                repo.category === 'flagship' 
                                  ? 'bg-yellow-100 text-yellow-800 border border-yellow-300'
                                  : repo.category === 'significant'
                                  ? 'bg-blue-100 text-blue-800 border border-blue-300'
                                  : 'bg-gray-100 text-gray-700 border border-gray-300'
                              }`}>
                                {repo.category === 'flagship' && '🏆 '}
                                {repo.category === 'significant' && '⭐ '}
                                {repo.category === 'supporting' && '📋 '}
                                {repo.category.charAt(0).toUpperCase() + repo.category.slice(1)}
                              </span>
                            )}
                          </div>
                          <p className="text-gray-600 mb-3">{repo.description || 'No description available'}</p>
                          
                          <div className="flex items-center space-x-6 text-sm text-gray-500">
                            <div className="flex items-center space-x-1">
                              <Star className="h-4 w-4" />
                              <span>{repo.stargazers_count || 0}</span>
                            </div>
                            <div className="flex items-center space-x-1">
                              <GitFork className="h-4 w-4" />
                              <span>{repo.forks_count || 0}</span>
                            </div>
                            <div className="flex items-center space-x-1">
                              <Calendar className="h-4 w-4" />
                              <span>Updated {formatDate(repo.updated_at)}</span>
                            </div>
                            {repo.importance_score !== undefined && repo.importance_score !== null && (
                              <div className="flex items-center space-x-1">
                                <span className="font-medium text-gray-700">Importance:</span>
                                <span className={`font-semibold ${getScoreColor(repo.importance_score)}`}>
                                  {repo.importance_score}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center space-x-3">
                          {repo.evaluated && repo.evaluation?.overall_score ? (
                            <div className="text-center">
                              <div className={`text-2xl font-bold ${getScoreColor(repo.evaluation.overall_score)}`}>
                                {repo.evaluation.overall_score}
                              </div>
                              <div className="text-xs text-gray-500">Eval Score</div>
                            </div>
                          ) : repo.analyzed && !repo.evaluated ? (
                            <div className="text-center px-3 py-2 bg-gray-50 rounded-lg border border-gray-200">
                              <div className="text-xs text-gray-500 font-medium">Not Evaluated</div>
                            </div>
                          ) : null}
                          <button
                            onClick={() => handleRepositoryClick(repo.name)}
                            className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
                          >
                            <Code className="h-4 w-4 mr-1" />
                            Details
                          </button>
                          <a
                            href={repo.html_url || (repo.full_name ? `https://github.com/${repo.full_name}` : (githubUsername ? `https://github.com/${githubUsername}/${repo.name}` : '#'))}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                          >
                            <ExternalLink className="h-4 w-4 mr-1" />
                            GitHub
                          </a>
                        </div>
                      </div>
                    </motion.div>
                  ))}
              </div>
            </div>
          )}

          {/* Supporting Repositories Section */}
          {categoryCounts.supporting > 0 && filteredRepositories.filter(r => r.category === 'supporting').length > 0 && (
            <div>
              <div className="flex items-center space-x-3 mb-4">
                <div className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-gray-100 to-gray-50 rounded-lg border-2 border-gray-300">
                  <span className="text-2xl">📋</span>
                  <h2 className="text-xl font-bold text-gray-900">Supporting Projects</h2>
                  <span className="px-2 py-1 bg-gray-200 text-gray-900 text-sm font-semibold rounded-full">
                    {filteredRepositories.filter(r => r.category === 'supporting').length}
                  </span>
                </div>
              </div>
              <p className="text-gray-600 mb-4 text-sm">Supporting and experimental repositories</p>
              <div className="grid gap-6">
                {filteredRepositories
                  .filter(repo => repo.category === 'supporting')
                  .map((repo, index) => (
                    <motion.div
                      key={repo.id}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.1 }}
                      className="card p-6 hover:shadow-lg transition-shadow duration-200 border-l-4 border-gray-300"
                    >
                      {/* Same repository card content */}
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1">
                          <div className="flex items-center space-x-3 mb-2">
                            <h3 className="text-xl font-semibold text-gray-900">{repo.name}</h3>
                            {repo.language && (
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getLanguageColor(repo.language)}`}>
                                {repo.language}
                              </span>
                            )}
                            {repo.category && (
                              <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                                repo.category === 'flagship' 
                                  ? 'bg-yellow-100 text-yellow-800 border border-yellow-300'
                                  : repo.category === 'significant'
                                  ? 'bg-blue-100 text-blue-800 border border-blue-300'
                                  : 'bg-gray-100 text-gray-700 border border-gray-300'
                              }`}>
                                {repo.category === 'flagship' && '🏆 '}
                                {repo.category === 'significant' && '⭐ '}
                                {repo.category === 'supporting' && '📋 '}
                                {repo.category.charAt(0).toUpperCase() + repo.category.slice(1)}
                              </span>
                            )}
                          </div>
                          <p className="text-gray-600 mb-3">{repo.description || 'No description available'}</p>
                          
                          <div className="flex items-center space-x-6 text-sm text-gray-500">
                            <div className="flex items-center space-x-1">
                              <Star className="h-4 w-4" />
                              <span>{repo.stargazers_count || 0}</span>
                            </div>
                            <div className="flex items-center space-x-1">
                              <GitFork className="h-4 w-4" />
                              <span>{repo.forks_count || 0}</span>
                            </div>
                            <div className="flex items-center space-x-1">
                              <Calendar className="h-4 w-4" />
                              <span>Updated {formatDate(repo.updated_at)}</span>
                            </div>
                            {repo.importance_score !== undefined && repo.importance_score !== null && (
                              <div className="flex items-center space-x-1">
                                <span className="font-medium text-gray-700">Importance:</span>
                                <span className={`font-semibold ${getScoreColor(repo.importance_score)}`}>
                                  {repo.importance_score}
                                </span>
                              </div>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center space-x-3">
                          {repo.evaluated && repo.evaluation?.overall_score ? (
                            <div className="text-center">
                              <div className={`text-2xl font-bold ${getScoreColor(repo.evaluation.overall_score)}`}>
                                {repo.evaluation.overall_score}
                              </div>
                              <div className="text-xs text-gray-500">Eval Score</div>
                            </div>
                          ) : repo.analyzed && !repo.evaluated ? (
                            <div className="text-center px-3 py-2 bg-gray-50 rounded-lg border border-gray-200">
                              <div className="text-xs text-gray-500 font-medium">Not Evaluated</div>
                            </div>
                          ) : null}
                          <button
                            onClick={() => handleRepositoryClick(repo.name)}
                            className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
                          >
                            <Code className="h-4 w-4 mr-1" />
                            Details
                          </button>
                          <a
                            href={repo.html_url || (repo.full_name ? `https://github.com/${repo.full_name}` : (githubUsername ? `https://github.com/${githubUsername}/${repo.name}` : '#'))}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                          >
                            <ExternalLink className="h-4 w-4 mr-1" />
                            GitHub
                          </a>
                        </div>
                      </div>
                    </motion.div>
                  ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        /* Standard List View - when not analyzed or filter is active */
        <div className="grid gap-6">
          {filteredRepositories.map((repo, index) => (
            <motion.div
              key={repo.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className="card p-6 hover:shadow-lg transition-shadow duration-200"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-2">
                    <h3 className="text-xl font-semibold text-gray-900">{repo.name}</h3>
                    {repo.language && (
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${getLanguageColor(repo.language)}`}>
                        {repo.language}
                      </span>
                    )}
                    {repo.category && (
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${
                        repo.category === 'flagship' 
                          ? 'bg-yellow-100 text-yellow-800 border border-yellow-300'
                          : repo.category === 'significant'
                          ? 'bg-blue-100 text-blue-800 border border-blue-300'
                          : 'bg-gray-100 text-gray-700 border border-gray-300'
                      }`}>
                        {repo.category === 'flagship' && '🏆 '}
                        {repo.category === 'significant' && '⭐ '}
                        {repo.category === 'supporting' && '📋 '}
                        {repo.category.charAt(0).toUpperCase() + repo.category.slice(1)}
                      </span>
                    )}
                  </div>
                  <p className="text-gray-600 mb-3">{repo.description || 'No description available'}</p>
                  
                  <div className="flex items-center space-x-6 text-sm text-gray-500">
                    <div className="flex items-center space-x-1">
                      <Star className="h-4 w-4" />
                      <span>{repo.stargazers_count || 0}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <GitFork className="h-4 w-4" />
                      <span>{repo.forks_count || 0}</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <Calendar className="h-4 w-4" />
                      <span>Updated {formatDate(repo.updated_at)}</span>
                    </div>
                    {repo.code_metrics?.lines_of_code && (
                      <div className="flex items-center space-x-1">
                        <Code className="h-4 w-4" />
                        <span>{(repo.code_metrics.lines_of_code || 0).toLocaleString()} lines</span>
                      </div>
                    )}
                    {repo.importance_score !== undefined && repo.importance_score !== null && (
                      <div className="flex items-center space-x-1">
                        <span className="font-medium text-gray-700">Importance:</span>
                        <span className={`font-semibold ${getScoreColor(repo.importance_score)}`}>
                          {repo.importance_score}
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  {repo.evaluated && repo.evaluation?.overall_score ? (
                    <div className="text-center">
                      <div className={`text-2xl font-bold ${getScoreColor(repo.evaluation.overall_score)}`}>
                        {repo.evaluation.overall_score}
                      </div>
                      <div className="text-xs text-gray-500">Eval Score</div>
                    </div>
                  ) : repo.analyzed && !repo.evaluated ? (
                    <div className="text-center px-3 py-2 bg-gray-50 rounded-lg border border-gray-200">
                      <div className="text-xs text-gray-500 font-medium">Not Evaluated</div>
                    </div>
                  ) : repo.analysis?.acid_scores?.overall ? (
                    <div className="text-center">
                      <div className={`text-2xl font-bold ${getScoreColor(repo.analysis.acid_scores.overall)}`}>
                        {repo.analysis.acid_scores.overall}
                      </div>
                      <div className="text-xs text-gray-500">ACID Score</div>
                    </div>
                  ) : null}
                  <button
                    onClick={() => handleRepositoryClick(repo.name)}
                    className="inline-flex items-center px-3 py-2 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
                  >
                    <Code className="h-4 w-4 mr-1" />
                    Details
                  </button>
                  <a
                    href={repo.html_url || (repo.full_name ? `https://github.com/${repo.full_name}` : (githubUsername ? `https://github.com/${githubUsername}/${repo.name}` : '#'))}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                  >
                    <ExternalLink className="h-4 w-4 mr-1" />
                    GitHub
                  </a>
                </div>
              </div>

              {repo.analysis && (
                <div className="border-t pt-4">
                  <h4 className="font-medium text-gray-900 mb-3">Code Quality Analysis</h4>
                  
                  {repo.analysis.acid_scores && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                      <div className="text-center">
                        <div className={`text-lg font-semibold ${getScoreColor(repo.analysis.acid_scores.atomicity)}`}>
                          {repo.analysis.acid_scores.atomicity}
                        </div>
                        <div className="text-xs text-gray-500">Atomicity</div>
                      </div>
                      <div className="text-center">
                        <div className={`text-lg font-semibold ${getScoreColor(repo.analysis.acid_scores.consistency)}`}>
                          {repo.analysis.acid_scores.consistency}
                        </div>
                        <div className="text-xs text-gray-500">Consistency</div>
                      </div>
                      <div className="text-center">
                        <div className={`text-lg font-semibold ${getScoreColor(repo.analysis.acid_scores.isolation)}`}>
                          {repo.analysis.acid_scores.isolation}
                        </div>
                        <div className="text-xs text-gray-500">Isolation</div>
                      </div>
                      <div className="text-center">
                        <div className={`text-lg font-semibold ${getScoreColor(repo.analysis.acid_scores.durability)}`}>
                          {repo.analysis.acid_scores.durability}
                        </div>
                        <div className="text-xs text-gray-500">Durability</div>
                      </div>
                    </div>
                  )}

                  {repo.analysis.quality_metrics && (
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                      <div className="text-center">
                        <div className={`text-sm font-semibold ${getScoreColor(repo.analysis.quality_metrics.readability)}`}>
                          {repo.analysis.quality_metrics.readability}%
                        </div>
                        <div className="text-xs text-gray-500">Readability</div>
                      </div>
                      <div className="text-center">
                        <div className={`text-sm font-semibold ${getScoreColor(repo.analysis.quality_metrics.maintainability)}`}>
                          {repo.analysis.quality_metrics.maintainability}%
                        </div>
                        <div className="text-xs text-gray-500">Maintainability</div>
                      </div>
                      <div className="text-center">
                        <div className={`text-sm font-semibold ${getScoreColor(repo.analysis.quality_metrics.security)}`}>
                          {repo.analysis.quality_metrics.security}%
                        </div>
                        <div className="text-xs text-gray-500">Security</div>
                      </div>
                      <div className="text-center">
                        <div className={`text-sm font-semibold ${getScoreColor(repo.analysis.quality_metrics.test_coverage)}`}>
                          {repo.analysis.quality_metrics.test_coverage}%
                        </div>
                        <div className="text-xs text-gray-500">Test Coverage</div>
                      </div>
                      <div className="text-center">
                        <div className={`text-sm font-semibold ${getScoreColor(repo.analysis.quality_metrics.documentation)}`}>
                          {repo.analysis.quality_metrics.documentation}%
                        </div>
                        <div className="text-xs text-gray-500">Documentation</div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {repo.topics && repo.topics.length > 0 && (
                <div className="border-t pt-4">
                  <div className="flex flex-wrap gap-2">
                    {repo.topics.slice(0, 8).map(topic => (
                      <span
                        key={topic}
                        className="px-2 py-1 bg-blue-50 text-blue-700 text-xs rounded-full"
                      >
                        {topic}
                      </span>
                    ))}
                    {repo.topics.length > 8 && (
                      <span className="px-2 py-1 bg-gray-50 text-gray-500 text-xs rounded-full">
                        +{repo.topics.length - 8} more
                      </span>
                    )}
                  </div>
                </div>
              )}
            </motion.div>
          ))}
        </div>
      )}

      {filteredRepositories.length === 0 && !isLoading && (
        <div className="card p-8 text-center">
          <div className="text-gray-400 mb-4">
            <GitBranch className="h-12 w-12 mx-auto" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Repositories Found</h3>
          <p className="text-gray-600">
            {searchTerm || filterLanguage !== 'all' 
              ? 'Try adjusting your search or filter criteria.'
              : 'No repositories available to display.'
            }
          </p>
        </div>
      )}
    </div>
  );
};

export default Repositories;



