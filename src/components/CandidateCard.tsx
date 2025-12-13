import React, { useCallback, useState } from 'react';
import { motion } from 'framer-motion';
import { ExternalLink, Star, Code, ThumbsUp } from 'lucide-react';
import hrCandidatesApiService from '../services/hrCandidatesApi';
import CandidateProfileModal from './CandidateProfileModal';

/**
 * Candidate data interface
 */
export interface CandidateCardData {
  username: string;
  full_name?: string;
  profile_picture?: string;
  role_category: string;
  overall_score: number;
  upvotes: number;
  primary_languages: string[];
  github_url: string;
}

interface CandidateCardProps {
  candidate: CandidateCardData;
  onClick?: () => void;
  className?: string;
}

/**
 * CandidateCard Component
 * 
 * Displays a candidate profile card with key information for HR recruiters.
 * 
 * Features:
 * - Profile picture with fallback to initials
 * - Username and role category
 * - Overall score with color coding (green ≥8.0, yellow ≥6.0, orange <6.0)
 * - Upvotes count
 * - Top 3 primary languages as tags
 * - "View" button that navigates to candidate detail page
 * - Click handler for entire card
 * - Hover animations
 * 
 * @example
 * ```tsx
 * <CandidateCard 
 *   candidate={{
 *     username: 'john-doe',
 *     role_category: 'Full-Stack Developer',
 *     overall_score: 8.5,
 *     upvotes: 42,
 *     primary_languages: ['JavaScript', 'Python', 'TypeScript'],
 *     github_url: 'https://github.com/john-doe'
 *   }}
 * />
 * ```
 */
const CandidateCard: React.FC<CandidateCardProps> = ({
  candidate,
  onClick,
  className = '',
}) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  /**
   * Get score color based on value
   * Green: >9, Blue: 8-9, Yellow: 7-8, Orange: <7
   */
  const getScoreColor = (score: number): string => {
    if (score > 9.0) return 'bg-gradient-to-br from-green-100 to-emerald-100 text-green-700 border-green-300 shadow-green-200/50';
    if (score >= 8.0) return 'bg-gradient-to-br from-blue-100 to-indigo-100 text-blue-700 border-blue-300 shadow-blue-200/50';
    if (score >= 7.0) return 'bg-gradient-to-br from-yellow-100 to-amber-100 text-yellow-700 border-yellow-300 shadow-yellow-200/50';
    return 'bg-gradient-to-br from-orange-100 to-red-100 text-orange-700 border-orange-300 shadow-orange-200/50';
  };

  /**
   * Get initials from username for avatar fallback
   */
  const getInitials = (username: string): string => {
    return username
      .split('-')
      .map(part => part.charAt(0).toUpperCase())
      .slice(0, 2)
      .join('');
  };

  /**
   * Get language color for tags
   */
  const getLanguageColor = (language: string): string => {
    const colors: Record<string, string> = {
      'JavaScript': 'bg-yellow-100 text-yellow-800 border-yellow-300',
      'TypeScript': 'bg-blue-100 text-blue-800 border-blue-300',
      'Python': 'bg-green-100 text-green-800 border-green-300',
      'Java': 'bg-red-100 text-red-800 border-red-300',
      'Go': 'bg-cyan-100 text-cyan-800 border-cyan-300',
      'Rust': 'bg-orange-100 text-orange-800 border-orange-300',
      'C++': 'bg-pink-100 text-pink-800 border-pink-300',
      'C#': 'bg-purple-100 text-purple-800 border-purple-300',
      'Ruby': 'bg-red-100 text-red-800 border-red-300',
      'PHP': 'bg-indigo-100 text-indigo-800 border-indigo-300',
      'Swift': 'bg-orange-100 text-orange-800 border-orange-300',
      'Kotlin': 'bg-purple-100 text-purple-800 border-purple-300',
    };
    return colors[language] || 'bg-gray-100 text-gray-800 border-gray-300';
  };

  /**
   * Get language emoji/icon
   */
  const getLanguageIcon = (language: string): string => {
    const icons: Record<string, string> = {
      'JavaScript': '🟨',
      'TypeScript': '🔷',
      'Python': '🐍',
      'Java': '☕',
      'Go': '🔵',
      'Rust': '🦀',
      'C++': '⚙️',
      'C#': '💜',
      'Ruby': '💎',
      'PHP': '🐘',
      'Swift': '🍎',
      'Kotlin': '🟣',
    };
    return icons[language] || '💻';
  };

  /**
   * Handle card click
   */
  const handleCardClick = () => {
    if (onClick) {
      onClick();
    } else {
      // Open modal instead of navigating
      setIsModalOpen(true);
    }
  };

  /**
   * Handle view button click
   */
  const handleViewClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    // Open modal instead of navigating
    setIsModalOpen(true);
  };

  /**
   * Handle hover to prefetch candidate profile data
   * This improves perceived performance by loading data before navigation
   */
  const handleMouseEnter = useCallback(() => {
    // Prefetch candidate profile data on hover
    hrCandidatesApiService.prefetchCandidateProfile(candidate.username);
  }, [candidate.username]);

  return (
    <>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        whileHover={{ 
          y: -6, 
          scale: 1.01,
          boxShadow: '0 20px 40px rgba(99, 102, 241, 0.15), 0 0 0 2px rgba(99, 102, 241, 0.1)',
          transition: { duration: 0.3, ease: "easeOut" }
        }}
        transition={{ duration: 0.3 }}
        onClick={handleCardClick}
        onMouseEnter={handleMouseEnter}
        className={`
          bg-white/90 backdrop-blur-sm rounded-2xl border-2 border-gray-200 p-7
          cursor-pointer transition-all duration-300
          hover:border-indigo-300 shadow-lg hover:shadow-2xl
          relative overflow-hidden group
          ${className}
        `}
      >
      {/* Gradient border effect on hover */}
      <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 opacity-0 group-hover:opacity-100 transition-opacity duration-300 -z-10 blur-xl"></div>
      <div className="flex items-start justify-between">
        {/* Left Section: Profile Info */}
        <div className="flex items-start space-x-4 flex-1">
          {/* Profile Picture / Avatar */}
          <div className="flex-shrink-0 relative group/avatar">
            {candidate.profile_picture ? (
              <img
                src={candidate.profile_picture}
                alt={candidate.username}
                className="w-20 h-20 rounded-full object-cover border-3 border-white shadow-lg group-hover/avatar:scale-110 transition-transform duration-300 ring-2 ring-indigo-200"
              />
            ) : (
              <div className="w-20 h-20 rounded-full bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-xl border-3 border-white shadow-lg group-hover/avatar:scale-110 transition-transform duration-300 ring-2 ring-indigo-200">
                {getInitials(candidate.username)}
              </div>
            )}
          </div>

          {/* Candidate Details */}
          <div className="flex-1 min-w-0">
            {/* Username and Full Name */}
            <div className="mb-3">
              <h3 className="text-xl font-bold text-gray-900 truncate group-hover:text-indigo-700 transition-colors duration-200">
                {candidate.full_name || `@${candidate.username}`}
              </h3>
              {candidate.full_name && (
                <p className="text-sm text-gray-600 font-medium">@{candidate.username}</p>
              )}
            </div>

            {/* Role Category */}
            <div className="mb-4">
              <span className="inline-flex items-center px-4 py-1.5 rounded-full text-sm font-semibold bg-gradient-to-r from-blue-100 to-indigo-100 text-indigo-700 border-2 border-indigo-200 shadow-sm">
                <Code className="h-4 w-4 mr-1.5" />
                {candidate.role_category}
              </span>
            </div>

            {/* Metrics Row */}
            <div className="flex items-center space-x-3 mb-4">
              {/* Overall Score */}
              <div className={`flex items-center space-x-2.5 px-4 py-2 rounded-xl border-2 shadow-md ${getScoreColor(candidate.overall_score)}`}>
                <Star className="h-5 w-5 fill-current" />
                <div className="flex flex-col">
                  <span className="text-xl font-extrabold leading-none">
                    {candidate.overall_score.toFixed(1)}
                  </span>
                  <span className="text-xs font-semibold leading-none mt-1 opacity-80">rating</span>
                </div>
              </div>

              {/* Upvotes */}
              <div className="flex items-center space-x-2.5 px-4 py-2 rounded-xl bg-gradient-to-br from-purple-100 to-pink-100 text-purple-700 border-2 border-purple-200 shadow-md">
                <ThumbsUp className="h-5 w-5 fill-current" />
                <div className="flex flex-col">
                  <span className="text-xl font-extrabold leading-none">
                    {candidate.upvotes}
                  </span>
                  <span className="text-xs font-semibold leading-none mt-1 opacity-80">upvotes</span>
                </div>
              </div>
            </div>

            {/* Primary Languages */}
            <div className="flex flex-wrap gap-2">
              {candidate.primary_languages.slice(0, 3).map((language) => (
                <motion.span
                  key={language}
                  whileHover={{ scale: 1.05 }}
                  className={`px-3 py-1.5 text-sm font-bold rounded-lg border-2 shadow-sm transition-all duration-200 ${getLanguageColor(language)}`}
                >
                  <span className="mr-1">{getLanguageIcon(language)}</span>
                  {language}
                </motion.span>
              ))}
              {candidate.primary_languages.length > 3 && (
                <span className="px-3 py-1.5 bg-gradient-to-br from-gray-100 to-gray-200 text-gray-600 text-sm font-bold rounded-lg border-2 border-gray-300 shadow-sm">
                  +{candidate.primary_languages.length - 3} more
                </span>
              )}
            </div>
          </div>
        </div>

        {/* Right Section: Actions */}
        <div className="flex flex-col space-y-3 ml-6">
          <motion.button
            whileHover={{ scale: 1.08, y: -2 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleViewClick}
            className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-bold rounded-xl hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 flex items-center justify-center space-x-2 shadow-lg hover:shadow-xl relative overflow-hidden group/btn"
          >
            <span className="relative z-10">View Profile</span>
            <ExternalLink className="h-5 w-5 relative z-10 group-hover/btn:translate-x-1 transition-transform duration-200" />
            <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-pink-600 opacity-0 group-hover/btn:opacity-100 transition-opacity duration-300"></div>
          </motion.button>

          <motion.a
            whileHover={{ scale: 1.05, y: -2 }}
            whileTap={{ scale: 0.95 }}
            href={candidate.github_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="px-6 py-3 bg-gradient-to-br from-gray-100 to-gray-200 text-gray-800 font-bold rounded-xl hover:from-gray-200 hover:to-gray-300 transition-all duration-200 text-center border-2 border-gray-300 shadow-md hover:shadow-lg"
          >
            GitHub
          </motion.a>
        </div>
      </div>
    </motion.div>

    {/* Candidate Profile Modal */}
    <CandidateProfileModal
      key={candidate.username}
      username={candidate.username}
      isOpen={isModalOpen}
      onClose={() => setIsModalOpen(false)}
    />
  </>
  );
};

export default CandidateCard;
