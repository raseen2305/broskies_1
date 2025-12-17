import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  MapPin,
  Mail,
  ExternalLink,
  GitBranch,
  Star,
  GitFork,
  Calendar,
  Code,
  Award,
  TrendingUp,
} from 'lucide-react';
import { CandidateProfile, ScoredRepository } from '../services/hrCandidatesApi';
import hrCandidatesApiService from '../services/hrCandidatesApi';

/**
 * CandidateDetail Component
 * 
 * Detailed view of a single candidate profile for HR recruiters.
 * 
 * Features:
 * - "Back to Dashboard" button
 * - Complete profile header (name, bio, location, GitHub link)
 * - GitHub stats (repos count, stars, forks)
 * - Language proficiency breakdown chart
 * - All scored repositories with scores and categories
 * - Contact information (email if available)
 * - Fetches candidate details on mount
 * 
 * Requirements: 7.1-7.5
 */
const CandidateDetail: React.FC = () => {
  const { username } = useParams<{ username: string }>();
  const navigate = useNavigate();

  const [candidate, setCandidate] = useState<CandidateProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * Fetch candidate details
   */
  useEffect(() => {
    const fetchCandidateDetails = async () => {
      if (!username) {
        setError('No username provided');
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);

        // Call real backend API
        const profile = await hrCandidatesApiService.getCandidateDetails(username);
        setCandidate(profile);
      } catch (err: any) {
        console.error('Failed to fetch candidate details:', err);
        setError(err.message || 'Failed to load candidate details');
      } finally {
        setIsLoading(false);
      }
    };

    fetchCandidateDetails();
  }, [username]);

  /**
   * Get score color
   */
  const getScoreColor = (score: number): string => {
    if (score >= 8.0) return 'text-green-600 bg-green-100 border-green-200';
    if (score >= 6.0) return 'text-yellow-600 bg-yellow-100 border-yellow-200';
    return 'text-orange-600 bg-orange-100 border-orange-200';
  };

  /**
   * Get category color
   */
  const getCategoryColor = (category: string): string => {
    switch (category.toLowerCase()) {
      case 'flagship':
        return 'bg-purple-100 text-purple-700 border-purple-200';
      case 'significant':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      case 'supporting':
        return 'bg-gray-100 text-gray-700 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  /**
   * Get initials
   */
  const getInitials = (name: string): string => {
    return name
      .split(' ')
      .map(part => part.charAt(0).toUpperCase())
      .slice(0, 2)
      .join('');
  };

  /**
   * Format date
   */
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading candidate profile...</p>
        </div>
      </div>
    );
  }

  if (error || !candidate) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || 'Candidate not found'}</p>
          <button
            onClick={() => navigate('/hr/dashboard')}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <button
            onClick={() => navigate('/hr/dashboard')}
            className="flex items-center space-x-2 text-gray-600 hover:text-gray-900 mb-4 transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
            <span className="font-medium">Back to Dashboard</span>
          </button>

          {/* Profile Header */}
          <div className="flex items-start space-x-6">
            {/* Avatar */}
            {candidate.profile_picture ? (
              <img
                src={candidate.profile_picture}
                alt={candidate.username}
                className="w-24 h-24 rounded-full object-cover border-4 border-gray-200"
              />
            ) : (
              <div className="w-24 h-24 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center text-white font-bold text-3xl border-4 border-gray-200">
                {getInitials(candidate.full_name || candidate.username)}
              </div>
            )}

            {/* Profile Info */}
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {candidate.full_name || `@${candidate.username}`}
              </h1>
              {candidate.full_name && (
                <p className="text-lg text-gray-600 mb-2">@{candidate.username}</p>
              )}
              {candidate.bio && (
                <p className="text-gray-700 mb-3">{candidate.bio}</p>
              )}

              <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
                {candidate.location && (
                  <span className="flex items-center space-x-1">
                    <MapPin className="h-4 w-4" />
                    <span>{candidate.location}</span>
                  </span>
                )}
                {candidate.email && (
                  <span className="flex items-center space-x-1">
                    <Mail className="h-4 w-4" />
                    <span>{candidate.email}</span>
                  </span>
                )}
                <a
                  href={candidate.github_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center space-x-1 text-primary-600 hover:text-primary-700"
                >
                  <ExternalLink className="h-4 w-4" />
                  <span>GitHub Profile</span>
                </a>
              </div>
            </div>

            {/* Score Badge */}
            <div className={`px-6 py-4 rounded-lg border ${getScoreColor(candidate.overall_score)}`}>
              <div className="text-center">
                <p className="text-3xl font-bold">{candidate.overall_score.toFixed(1)}</p>
                <p className="text-sm">Overall Score</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Stats and Languages */}
          <div className="space-y-6">
            {/* GitHub Stats */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-lg border border-gray-200 p-6"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-4">GitHub Stats</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="flex items-center space-x-2 text-gray-600">
                    <GitBranch className="h-5 w-5" />
                    <span>Repositories</span>
                  </span>
                  <span className="font-bold text-gray-900">{candidate.repositories_count}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center space-x-2 text-gray-600">
                    <Star className="h-5 w-5" />
                    <span>Total Stars</span>
                  </span>
                  <span className="font-bold text-gray-900">{candidate.total_stars}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center space-x-2 text-gray-600">
                    <GitFork className="h-5 w-5" />
                    <span>Total Forks</span>
                  </span>
                  <span className="font-bold text-gray-900">{candidate.total_forks}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="flex items-center space-x-2 text-gray-600">
                    <TrendingUp className="h-5 w-5" />
                    <span>Upvotes</span>
                  </span>
                  <span className="font-bold text-gray-900">{candidate.upvotes}</span>
                </div>
              </div>
            </motion.div>

            {/* Language Proficiency */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="bg-white rounded-lg border border-gray-200 p-6"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
                <Code className="h-5 w-5" />
                <span>Language Proficiency</span>
              </h3>
              <div className="space-y-3">
                {Object.entries(candidate.language_proficiency)
                  .sort(([, a], [, b]) => b - a)
                  .map(([language, percentage], index) => (
                    <motion.div
                      key={language}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.1 }}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-gray-700">{language}</span>
                        <span className="text-sm text-gray-600">{percentage}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${percentage}%` }}
                          transition={{ duration: 0.5, delay: index * 0.1 }}
                          className="bg-gradient-to-r from-primary-500 to-primary-600 h-2 rounded-full"
                        />
                      </div>
                    </motion.div>
                  ))}
              </div>
            </motion.div>

            {/* Account Info */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="bg-white rounded-lg border border-gray-200 p-6"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Account Info</h3>
              <div className="space-y-3 text-sm">
                <div>
                  <p className="text-gray-600">Member Since</p>
                  <p className="font-medium text-gray-900">{formatDate(candidate.account_created)}</p>
                </div>
                <div>
                  <p className="text-gray-600">Last Active</p>
                  <p className="font-medium text-gray-900">{formatDate(candidate.last_active)}</p>
                </div>
                <div>
                  <p className="text-gray-600">Role Category</p>
                  <p className="font-medium text-gray-900">{candidate.role_category}</p>
                </div>
              </div>
            </motion.div>
          </div>

          {/* Right Column: Repositories */}
          <div className="lg:col-span-2">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-lg border border-gray-200 p-6"
            >
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center space-x-2">
                <Award className="h-5 w-5 text-yellow-600" />
                <span>Scored Repositories</span>
              </h3>

              <div className="space-y-4">
                {candidate.scored_repositories.map((repo, index) => (
                  <motion.div
                    key={repo.name}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="border border-gray-200 rounded-lg p-4 hover:border-primary-300 hover:shadow-md transition-all"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <a
                          href={repo.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-lg font-semibold text-primary-600 hover:text-primary-700 flex items-center space-x-2"
                        >
                          <span>{repo.name}</span>
                          <ExternalLink className="h-4 w-4" />
                        </a>
                        {repo.description && (
                          <p className="text-sm text-gray-600 mt-1">{repo.description}</p>
                        )}
                      </div>
                      <div className={`px-3 py-1 rounded-lg border text-sm font-medium ${getScoreColor(repo.score)}`}>
                        {repo.score.toFixed(1)}
                      </div>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 text-sm">
                      <span className={`px-2 py-1 rounded-md border ${getCategoryColor(repo.category)}`}>
                        {repo.category}
                      </span>
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 rounded-md border border-gray-200">
                        {repo.primary_language}
                      </span>
                      <span className="flex items-center space-x-1 text-gray-600">
                        <Star className="h-4 w-4" />
                        <span>{repo.stars}</span>
                      </span>
                      <span className="flex items-center space-x-1 text-gray-600">
                        <GitFork className="h-4 w-4" />
                        <span>{repo.forks}</span>
                      </span>
                      <span className="flex items-center space-x-1 text-gray-500">
                        <Calendar className="h-4 w-4" />
                        <span>Updated {formatDate(repo.last_updated)}</span>
                      </span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CandidateDetail;
