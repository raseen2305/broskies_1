import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  ArrowLeft, 
  Star, 
  GitFork, 
  Eye, 
  Calendar, 
  Code, 
  Users, 
  GitCommit, 
  GitPullRequest, 
  AlertCircle, 
  CheckCircle,
  ExternalLink,
  Activity,
  BarChart3,
  Shield,
  FileText
} from 'lucide-react';

interface RepositoryDetailProps {
  scanResults?: any;
  repositoryName?: string;
  onBack?: () => void;
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
  topics: string[];
  license?: {
    name: string;
  };
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
    overall_score: number;
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

const RepositoryDetail: React.FC<RepositoryDetailProps> = ({ 
  scanResults, 
  repositoryName: propRepositoryName,
  onBack 
}) => {
  const { repositoryName: paramRepositoryName } = useParams<{ repositoryName: string }>();
  const navigate = useNavigate();
  
  // Use prop if provided (modal mode), otherwise use URL param (normal mode)
  const repositoryName = propRepositoryName || paramRepositoryName;
  
  const handleBack = () => {
    if (onBack) {
      // Modal mode - use callback
      onBack();
    } else {
      // Normal mode - use navigation
      navigate(-1);
    }
  };
  const [repository, setRepository] = useState<Repository | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  // Get the GitHub username from scan results
  const githubUsername = scanResults?.targetUsername || scanResults?.userInfo?.login || scanResults?.userInfo?.username;

  useEffect(() => {
    // If no scan results available, redirect to repositories page
    if (!scanResults?.repositories) {
      console.log('⚠️ No scan results available, redirecting to repositories page');
      setTimeout(() => {
        navigate('/developer/dashboard/repositories', { replace: true });
      }, 100);
      return;
    }

    if (scanResults?.repositories && repositoryName) {
      const repo = scanResults.repositories.find((r: Repository) => r.name === repositoryName);
      if (repo) {
        setRepository(repo);
      } else {
        console.log('⚠️ Repository not found in scan results');
      }
      setIsLoading(false);
    }
  }, [scanResults, repositoryName, navigate]);

  const getLanguageColor = (language: string): string => {
    const colors: { [key: string]: string } = {
      'JavaScript': '#f1e05a',
      'TypeScript': '#3178c6',
      'Python': '#3572A5',
      'Java': '#b07219',
      'C++': '#f34b7d',
      'C#': '#239120',
      'Go': '#00ADD8',
      'Rust': '#dea584',
      'PHP': '#4F5D95',
      'Ruby': '#701516',
    };
    return colors[language] || '#6b7280';
  };

  const getScoreColor = (score: number): string => {
    if (score >= 80) return 'text-green-600 bg-green-50';
    if (score >= 60) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <div className="h-8 w-8 bg-gray-200 rounded animate-pulse"></div>
          <div className="h-8 bg-gray-200 rounded w-64 animate-pulse"></div>
        </div>
        <div className="card p-6 animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-48 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-full mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
        </div>
      </div>
    );
  }

  if (!repository) {
    return (
      <div className="space-y-6">
        <div className="flex items-center space-x-4">
          <button
            onClick={handleBack}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <h1 className="text-2xl font-bold text-gray-900">Repository Not Found</h1>
        </div>
        <div className="card p-8 text-center">
          <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">Repository Not Found</h3>
          <p className="text-gray-600">The requested repository could not be found.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <button
          onClick={handleBack}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="h-5 w-5" />
        </button>
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-2">
            <h1 className="text-2xl font-bold text-gray-900">{repository.name}</h1>
            {/* Category Badge */}
            {(repository as any).category && (
              <span className={`px-3 py-1 rounded-full text-sm font-semibold ${
                (repository as any).category === 'flagship' 
                  ? 'bg-yellow-100 text-yellow-800 border border-yellow-300'
                  : (repository as any).category === 'significant'
                  ? 'bg-blue-100 text-blue-800 border border-blue-300'
                  : 'bg-gray-100 text-gray-700 border border-gray-300'
              }`}>
                {(repository as any).category === 'flagship' && '🏆 '}
                {(repository as any).category === 'significant' && '⭐ '}
                {(repository as any).category === 'supporting' && '📋 '}
                {(repository as any).category.charAt(0).toUpperCase() + (repository as any).category.slice(1)}
              </span>
            )}
            {/* Importance Score */}
            {(repository as any).importance_score !== undefined && (repository as any).importance_score !== null && (
              <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${
                (repository as any).importance_score >= 70
                  ? 'bg-green-50 text-green-700 border-green-300'
                  : (repository as any).importance_score >= 50
                  ? 'bg-blue-50 text-blue-700 border-blue-300'
                  : 'bg-gray-50 text-gray-600 border-gray-300'
              }`}>
                Importance: {(repository as any).importance_score}
              </span>
            )}
          </div>
          <p className="text-gray-600">{repository.description || 'No description available'}</p>
        </div>
        <a
          href={repository.html_url || (repository.full_name ? `https://github.com/${repository.full_name}` : (githubUsername ? `https://github.com/${githubUsername}/${repository.name}` : '#'))}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors"
        >
          <ExternalLink className="h-4 w-4 mr-2" />
          View on GitHub
        </a>
      </div>

      {/* Repository Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-6"
        >
          <div className="flex items-center space-x-3">
            <div className="bg-yellow-100 rounded-lg p-3">
              <Star className="h-6 w-6 text-yellow-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Stars</p>
              <p className="text-2xl font-bold text-gray-900">{repository.stargazers_count}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card p-6"
        >
          <div className="flex items-center space-x-3">
            <div className="bg-blue-100 rounded-lg p-3">
              <GitFork className="h-6 w-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Forks</p>
              <p className="text-2xl font-bold text-gray-900">{repository.forks_count}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card p-6"
        >
          <div className="flex items-center space-x-3">
            <div className="bg-green-100 rounded-lg p-3">
              <Eye className="h-6 w-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Watchers</p>
              <p className="text-2xl font-bold text-gray-900">{repository.watchers_count}</p>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="card p-6"
        >
          <div className="flex items-center space-x-3">
            <div className="bg-purple-100 rounded-lg p-3">
              <Code className="h-6 w-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Size (KB)</p>
              <p className="text-2xl font-bold text-gray-900">{repository.size}</p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Repository Info */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="card p-6"
        >
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Repository Information</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Language</span>
              <div className="flex items-center space-x-2">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: getLanguageColor(repository.language) }}
                />
                <span className="font-medium text-gray-900">{repository.language || 'N/A'}</span>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Created</span>
              <span className="font-medium text-gray-900">{formatDate(repository.created_at)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Last Updated</span>
              <span className="font-medium text-gray-900">{formatDate(repository.updated_at)}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Last Push</span>
              <span className="font-medium text-gray-900">{formatDate(repository.pushed_at)}</span>
            </div>
            {repository.license && (
              <div className="flex items-center justify-between">
                <span className="text-gray-600">License</span>
                <span className="font-medium text-gray-900">{repository.license.name}</span>
              </div>
            )}
          </div>
        </motion.div>

        {/* Code Metrics */}
        {repository.code_metrics && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="card p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Code Metrics</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Lines of Code</span>
                <span className="font-bold text-gray-900">
                  {repository.code_metrics.lines_of_code.toLocaleString()}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Files</span>
                <span className="font-bold text-gray-900">
                  {repository.code_metrics.files_count}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Complexity Score</span>
                <span className={`font-bold px-2 py-1 rounded ${getScoreColor(repository.code_metrics.complexity_score)}`}>
                  {repository.code_metrics.complexity_score}
                </span>
              </div>
            </div>
          </motion.div>
        )}

        {/* Overall Score */}
        {repository.analysis && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="card p-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Overall Analysis</h3>
            <div className="text-center">
              <div className={`text-4xl font-bold mb-2 ${getScoreColor(repository.analysis.overall_score).split(' ')[0]}`}>
                {repository.analysis.overall_score}
              </div>
              <div className="text-sm text-gray-600">Overall Score</div>
              <div className="mt-4">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 h-2 rounded-full transition-all duration-1000"
                    style={{ width: `${repository.analysis.overall_score}%` }}
                  />
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Not Evaluated Explanation - for supporting repos */}
      {(repository as any).analyzed && !(repository as any).evaluated && (repository as any).category === 'supporting' && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="card p-6 bg-blue-50 border-2 border-blue-200"
        >
          <div className="flex items-start space-x-4">
            <div className="bg-blue-100 rounded-lg p-3 flex-shrink-0">
              <AlertCircle className="h-6 w-6 text-blue-600" />
            </div>
            <div className="flex-1">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Why wasn't this repository evaluated?</h3>
              <p className="text-gray-700 mb-3">
                This repository was categorized as <span className="font-semibold">Supporting</span> based on its importance score of {(repository as any).importance_score}. 
                The analysis system focuses deep evaluation resources on the most significant repositories to provide meaningful insights efficiently.
              </p>
              <div className="space-y-2 text-sm text-gray-600">
                <p><strong>Evaluation Criteria:</strong></p>
                <ul className="list-disc list-inside space-y-1 ml-2">
                  <li><strong>Flagship</strong> (score ≥ 70): Top-tier production-level projects - always evaluated</li>
                  <li><strong>Significant</strong> (score ≥ 50): Solid development projects - evaluated when possible</li>
                  <li><strong>Supporting</strong> (score &lt; 50): Learning/experimental projects - not evaluated</li>
                </ul>
                <p className="mt-3">
                  <strong>Importance Score Factors:</strong> Lines of code (30%), file count (30%), and production indicators like tests, CI/CD, and activity (40%).
                </p>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Evaluation Metrics - for evaluated repos */}
      {(repository as any).evaluated && (repository as any).evaluation && (
        <>
          {/* Overall Evaluation Score */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
            className="card p-6 bg-gradient-to-br from-primary-50 to-blue-50"
          >
            <div className="text-center">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Evaluation Score</h3>
              <div className={`text-6xl font-bold mb-4 ${
                (repository as any).evaluation.overall_score >= 80
                  ? 'text-green-600'
                  : (repository as any).evaluation.overall_score >= 60
                  ? 'text-yellow-600'
                  : 'text-red-600'
              }`}>
                {(repository as any).evaluation.overall_score}
              </div>
              <p className="text-gray-600">
                This repository was deeply evaluated as a {(repository as any).category} project
              </p>
            </div>
          </motion.div>

          {/* ACID Scores from Evaluation */}
          {(repository as any).evaluation.acid_scores && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 }}
              className="card p-6"
            >
              <h3 className="text-xl font-semibold text-gray-900 mb-6">ACID Score Breakdown</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="text-center">
                  <div className="bg-blue-50 rounded-lg p-6 mb-3">
                    <Activity className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                    <div className={`text-2xl font-bold ${getScoreColor((repository as any).evaluation.acid_scores.architecture).split(' ')[0]}`}>
                      {(repository as any).evaluation.acid_scores.architecture}
                    </div>
                  </div>
                  <h4 className="font-semibold text-gray-900">Architecture</h4>
                  <p className="text-sm text-gray-600 mt-1">System design and structure</p>
                </div>
                
                <div className="text-center">
                  <div className="bg-green-50 rounded-lg p-6 mb-3">
                    <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
                    <div className={`text-2xl font-bold ${getScoreColor((repository as any).evaluation.acid_scores.code_quality).split(' ')[0]}`}>
                      {(repository as any).evaluation.acid_scores.code_quality}
                    </div>
                  </div>
                  <h4 className="font-semibold text-gray-900">Code Quality</h4>
                  <p className="text-sm text-gray-600 mt-1">Code cleanliness and standards</p>
                </div>
                
                <div className="text-center">
                  <div className="bg-purple-50 rounded-lg p-6 mb-3">
                    <Shield className="h-8 w-8 text-purple-600 mx-auto mb-2" />
                    <div className={`text-2xl font-bold ${getScoreColor((repository as any).evaluation.acid_scores.innovation).split(' ')[0]}`}>
                      {(repository as any).evaluation.acid_scores.innovation}
                    </div>
                  </div>
                  <h4 className="font-semibold text-gray-900">Innovation</h4>
                  <p className="text-sm text-gray-600 mt-1">Technical creativity and novelty</p>
                </div>
                
                <div className="text-center">
                  <div className="bg-orange-50 rounded-lg p-6 mb-3">
                    <FileText className="h-8 w-8 text-orange-600 mx-auto mb-2" />
                    <div className={`text-2xl font-bold ${getScoreColor((repository as any).evaluation.acid_scores.documentation).split(' ')[0]}`}>
                      {(repository as any).evaluation.acid_scores.documentation}
                    </div>
                  </div>
                  <h4 className="font-semibold text-gray-900">Documentation</h4>
                  <p className="text-sm text-gray-600 mt-1">Code documentation quality</p>
                </div>
              </div>
            </motion.div>
          )}

          {/* Quality Metrics */}
          {(repository as any).evaluation.quality_metrics && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.9 }}
              className="card p-6"
            >
              <h3 className="text-xl font-semibold text-gray-900 mb-6">Quality Metrics</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-gray-700 font-medium">Code Quality</span>
                    <span className={`font-bold ${getScoreColor((repository as any).evaluation.quality_metrics.code_quality).split(' ')[0]}`}>
                      {(repository as any).evaluation.quality_metrics.code_quality}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full"
                      style={{ width: `${(repository as any).evaluation.quality_metrics.code_quality}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-gray-700 font-medium">Technical Excellence</span>
                    <span className={`font-bold ${getScoreColor((repository as any).evaluation.quality_metrics.technical_excellence).split(' ')[0]}`}>
                      {(repository as any).evaluation.quality_metrics.technical_excellence}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-green-500 h-2 rounded-full"
                      style={{ width: `${(repository as any).evaluation.quality_metrics.technical_excellence}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-gray-700 font-medium">Production Readiness</span>
                    <span className={`font-bold ${getScoreColor((repository as any).evaluation.quality_metrics.production_readiness).split(' ')[0]}`}>
                      {(repository as any).evaluation.quality_metrics.production_readiness}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-purple-500 h-2 rounded-full"
                      style={{ width: `${(repository as any).evaluation.quality_metrics.production_readiness}%` }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-gray-700 font-medium">Innovation Score</span>
                    <span className={`font-bold ${getScoreColor((repository as any).evaluation.quality_metrics.innovation_score).split(' ')[0]}`}>
                      {(repository as any).evaluation.quality_metrics.innovation_score}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-orange-500 h-2 rounded-full"
                      style={{ width: `${(repository as any).evaluation.quality_metrics.innovation_score}%` }}
                    />
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          {/* Strengths and Improvements */}
          {((repository as any).evaluation.strengths || (repository as any).evaluation.improvements) && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.0 }}
              className="grid grid-cols-1 md:grid-cols-2 gap-6"
            >
              {/* Strengths */}
              {(repository as any).evaluation.strengths && (repository as any).evaluation.strengths.length > 0 && (
                <div className="card p-6 bg-green-50 border-2 border-green-200">
                  <div className="flex items-center space-x-2 mb-4">
                    <CheckCircle className="h-5 w-5 text-green-600" />
                    <h3 className="text-lg font-semibold text-gray-900">Strengths</h3>
                  </div>
                  <ul className="space-y-2">
                    {(repository as any).evaluation.strengths.map((strength: string, index: number) => (
                      <li key={index} className="flex items-start space-x-2">
                        <span className="text-green-600 mt-1">✓</span>
                        <span className="text-gray-700">{strength}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Improvements */}
              {(repository as any).evaluation.improvements && (repository as any).evaluation.improvements.length > 0 && (
                <div className="card p-6 bg-yellow-50 border-2 border-yellow-200">
                  <div className="flex items-center space-x-2 mb-4">
                    <AlertCircle className="h-5 w-5 text-yellow-600" />
                    <h3 className="text-lg font-semibold text-gray-900">Improvement Areas</h3>
                  </div>
                  <ul className="space-y-2">
                    {(repository as any).evaluation.improvements.map((improvement: string, index: number) => (
                      <li key={index} className="flex items-start space-x-2">
                        <span className="text-yellow-600 mt-1">→</span>
                        <span className="text-gray-700">{improvement}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </motion.div>
          )}

          {/* Production Indicators */}
          {(repository as any).evaluation.production_indicators && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 1.1 }}
              className="card p-6"
            >
              <h3 className="text-xl font-semibold text-gray-900 mb-6">Production Readiness Indicators</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className={`p-4 rounded-lg border-2 ${
                  (repository as any).evaluation.production_indicators.has_tests
                    ? 'bg-green-50 border-green-300'
                    : 'bg-gray-50 border-gray-300'
                }`}>
                  <div className="text-center">
                    {(repository as any).evaluation.production_indicators.has_tests ? (
                      <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
                    ) : (
                      <AlertCircle className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                    )}
                    <p className="text-sm font-medium text-gray-900">Tests</p>
                  </div>
                </div>

                <div className={`p-4 rounded-lg border-2 ${
                  (repository as any).evaluation.production_indicators.has_ci_cd
                    ? 'bg-green-50 border-green-300'
                    : 'bg-gray-50 border-gray-300'
                }`}>
                  <div className="text-center">
                    {(repository as any).evaluation.production_indicators.has_ci_cd ? (
                      <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
                    ) : (
                      <AlertCircle className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                    )}
                    <p className="text-sm font-medium text-gray-900">CI/CD</p>
                  </div>
                </div>

                <div className={`p-4 rounded-lg border-2 ${
                  (repository as any).evaluation.production_indicators.has_docker
                    ? 'bg-green-50 border-green-300'
                    : 'bg-gray-50 border-gray-300'
                }`}>
                  <div className="text-center">
                    {(repository as any).evaluation.production_indicators.has_docker ? (
                      <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
                    ) : (
                      <AlertCircle className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                    )}
                    <p className="text-sm font-medium text-gray-900">Docker</p>
                  </div>
                </div>

                <div className={`p-4 rounded-lg border-2 ${
                  (repository as any).evaluation.production_indicators.has_monitoring
                    ? 'bg-green-50 border-green-300'
                    : 'bg-gray-50 border-gray-300'
                }`}>
                  <div className="text-center">
                    {(repository as any).evaluation.production_indicators.has_monitoring ? (
                      <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
                    ) : (
                      <AlertCircle className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                    )}
                    <p className="text-sm font-medium text-gray-900">Monitoring</p>
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </>
      )}

      {/* Legacy ACID Scores - for non-evaluated repos with old analysis */}
      {!((repository as any).evaluated) && repository.analysis?.acid_scores && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
          className="card p-6"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-6">ACID Score Breakdown</h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="text-center">
              <div className="bg-blue-50 rounded-lg p-6 mb-3">
                <Activity className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                <div className={`text-2xl font-bold ${getScoreColor(repository.analysis.acid_scores.atomicity).split(' ')[0]}`}>
                  {repository.analysis.acid_scores.atomicity}
                </div>
              </div>
              <h4 className="font-semibold text-gray-900">Atomicity</h4>
              <p className="text-sm text-gray-600 mt-1">Code organization and modularity</p>
            </div>
            
            <div className="text-center">
              <div className="bg-green-50 rounded-lg p-6 mb-3">
                <CheckCircle className="h-8 w-8 text-green-600 mx-auto mb-2" />
                <div className={`text-2xl font-bold ${getScoreColor(repository.analysis.acid_scores.consistency).split(' ')[0]}`}>
                  {repository.analysis.acid_scores.consistency}
                </div>
              </div>
              <h4 className="font-semibold text-gray-900">Consistency</h4>
              <p className="text-sm text-gray-600 mt-1">Code style and conventions</p>
            </div>
            
            <div className="text-center">
              <div className="bg-purple-50 rounded-lg p-6 mb-3">
                <Shield className="h-8 w-8 text-purple-600 mx-auto mb-2" />
                <div className={`text-2xl font-bold ${getScoreColor(repository.analysis.acid_scores.isolation).split(' ')[0]}`}>
                  {repository.analysis.acid_scores.isolation}
                </div>
              </div>
              <h4 className="font-semibold text-gray-900">Isolation</h4>
              <p className="text-sm text-gray-600 mt-1">Component separation and encapsulation</p>
            </div>
            
            <div className="text-center">
              <div className="bg-orange-50 rounded-lg p-6 mb-3">
                <BarChart3 className="h-8 w-8 text-orange-600 mx-auto mb-2" />
                <div className={`text-2xl font-bold ${getScoreColor(repository.analysis.acid_scores.durability).split(' ')[0]}`}>
                  {repository.analysis.acid_scores.durability}
                </div>
              </div>
              <h4 className="font-semibold text-gray-900">Durability</h4>
              <p className="text-sm text-gray-600 mt-1">Long-term maintainability</p>
            </div>
          </div>
        </motion.div>
      )}

      {/* Quality Metrics */}
      {repository.analysis?.quality_metrics && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
          className="card p-6"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-6">Quality Metrics</h3>
          <div className="space-y-4">
            {Object.entries(repository.analysis.quality_metrics).map(([metric, score], index) => (
              <div key={metric} className="flex items-center space-x-4">
                <div className="w-32 text-sm font-medium text-gray-700 capitalize">
                  {metric.replace('_', ' ')}
                </div>
                <div className="flex-1 bg-gray-200 rounded-full h-3">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${score}%` }}
                    transition={{ delay: 1.0 + index * 0.1, duration: 0.8 }}
                    className={`h-3 rounded-full ${
                      score >= 80 ? 'bg-green-500' : 
                      score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                  />
                </div>
                <div className={`w-16 text-sm font-semibold text-right ${getScoreColor(score).split(' ')[0]}`}>
                  {score}%
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Topics */}
      {repository.topics && repository.topics.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.9 }}
          className="card p-6"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Topics</h3>
          <div className="flex flex-wrap gap-2">
            {repository.topics.map(topic => (
              <span
                key={topic}
                className="px-3 py-1 bg-blue-50 text-blue-700 text-sm rounded-full border border-blue-200"
              >
                {topic}
              </span>
            ))}
          </div>
        </motion.div>
      )}

      {/* Contributors */}
      {repository.contributors && repository.contributors.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.0 }}
          className="card p-6"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Contributors</h3>
          <div className="space-y-3">
            {repository.contributors.slice(0, 10).map((contributor, index) => (
              <div key={contributor.login} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="w-8 h-8 bg-gray-300 rounded-full flex items-center justify-center">
                    <Users className="h-4 w-4 text-gray-600" />
                  </div>
                  <span className="font-medium text-gray-900">{contributor.login}</span>
                </div>
                <span className="text-sm text-gray-600">{contributor.contributions} contributions</span>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Commit Activity */}
      {repository.commit_activity && repository.commit_activity.length > 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.1 }}
          className="card p-6"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Recent Commit Activity</h3>
          <div className="space-y-2">
            {repository.commit_activity.slice(0, 10).map((activity, index) => (
              <div key={activity.date} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded">
                <div className="flex items-center space-x-3">
                  <GitCommit className="h-4 w-4 text-gray-500" />
                  <span className="text-sm text-gray-700">{formatDate(activity.date)}</span>
                </div>
                <span className="text-sm font-medium text-gray-900">{activity.commits} commits</span>
              </div>
            ))}
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default RepositoryDetail;