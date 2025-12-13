import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Code, TrendingUp, BarChart3, Award, Activity } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { scanAPI } from '../../services/api';

interface LanguageData {
  language: string;
  percentage: number;
  linesOfCode?: number;
  repositories: number;
  stars?: number;
}

interface UserStats {
  overallScore: number;
  repositoryCount: number;
  lastScanDate: string | null;
  languages: LanguageData[];
}

interface LanguagesProps {
  scanResults?: any;
}

const Languages: React.FC<LanguagesProps> = ({ scanResults }) => {
  const { user } = useAuth();
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadUserStats = async () => {
      // If scan results are provided, use them directly
      if (scanResults) {
        console.log('📊 Languages using provided scan results:', scanResults);
        
        // Clear any previous errors
        setError(null);
        
        // Extract language data from the actual scan results structure
        let languagesData: LanguageData[] = [];
        
        // Check if languages is an object (new format from backend)
        if (scanResults.languages && typeof scanResults.languages === 'object' && !Array.isArray(scanResults.languages)) {
          // Transform object format to array format
          const totalBytes = Object.values(scanResults.languages as Record<string, number>).reduce((sum: number, bytes: number) => sum + bytes, 0);
          
          languagesData = Object.entries(scanResults.languages as Record<string, number>).map(([language, bytes]) => ({
            language,
            percentage: totalBytes > 0 ? (bytes / totalBytes) * 100 : 0,
            linesOfCode: Math.round(bytes / 50), // Rough estimate: 50 bytes per line
            repositories: scanResults.repositories?.filter((r: any) => r.language === language).length || 0,
            stars: 0
          })).sort((a, b) => b.percentage - a.percentage);
        } else if (scanResults.languages && Array.isArray(scanResults.languages) && scanResults.languages.length > 0) {
          // Use direct languages array if available (old format)
          languagesData = scanResults.languages;
        } else if (scanResults.languageStatistics && scanResults.languageStatistics.language_breakdown) {
          // Transform language_breakdown to expected format (legacy format)
          const breakdown = scanResults.languageStatistics.language_breakdown;
          languagesData = Object.entries(breakdown).map(([language, data]: [string, any]) => ({
            language,
            percentage: data.percentage || 0,
            linesOfCode: data.lines_of_code || 0,
            repositories: data.repository_count || 0,
            stars: 0
          })).sort((a, b) => b.percentage - a.percentage);
        }
        
        const transformedStats: UserStats = {
          overallScore: scanResults.overallScore || scanResults.hybrid_score || 0,
          repositoryCount: scanResults.repositoryCount || 0,
          lastScanDate: new Date().toISOString(),
          languages: languagesData
        };
        
        setUserStats(transformedStats);
        setIsLoading(false);
        return;
      }
      
      // Don't automatically load authenticated user data
      if (!user?.id) {
        setError('Please log in to view your languages or scan a GitHub profile.');
        setIsLoading(false);
        return;
      }
      
      // Let the user explicitly scan their own profile if needed
      setError('Please scan a GitHub profile to view language analysis.');
      setIsLoading(false);
    };

    loadUserStats();
  }, [user?.id, scanResults]);

  // Show message if no data available
  if (!userStats || !userStats.languages || userStats.languages.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Programming Languages</h1>
          <p className="text-gray-600">Language distribution and usage statistics</p>
        </div>
        <div className="card p-8 text-center">
          <div className="text-gray-400 mb-4">
            <Code className="h-12 w-12 mx-auto" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Language Data Available</h3>
          <p className="text-gray-600">
            Please scan a GitHub profile to view language statistics.
          </p>
        </div>
      </div>
    );
  }

  // Language color mapping
  const getLanguageColor = (language: string): string => {
    const colorMap: { [key: string]: string } = {
      'JavaScript': 'bg-yellow-500',
      'TypeScript': 'bg-blue-500',
      'Python': 'bg-green-500',
      'Java': 'bg-red-500',
      'Go': 'bg-cyan-500',
      'Rust': 'bg-orange-500',
      'C++': 'bg-purple-500',
      'C#': 'bg-indigo-500',
      'PHP': 'bg-violet-500',
      'Ruby': 'bg-red-400',
      'Swift': 'bg-orange-400',
      'Kotlin': 'bg-purple-400',
      'Dart': 'bg-blue-400',
      'HTML': 'bg-orange-600',
      'CSS': 'bg-blue-600',
      'Shell': 'bg-gray-600',
    };
    return colorMap[language] || 'bg-gray-500';
  };

  const getProficiencyLevel = (percentage: number): { level: string; color: string } => {
    if (percentage >= 25) return { level: 'Expert', color: 'text-green-600' };
    if (percentage >= 15) return { level: 'Advanced', color: 'text-blue-600' };
    if (percentage >= 8) return { level: 'Intermediate', color: 'text-yellow-600' };
    return { level: 'Beginner', color: 'text-gray-600' };
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <div className="h-8 bg-gray-200 rounded w-64 mb-2 animate-pulse"></div>
          <div className="h-4 bg-gray-200 rounded w-96 animate-pulse"></div>
        </div>
        <div className="card p-6 animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-48 mb-6"></div>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="flex items-center space-x-4">
                <div className="h-4 bg-gray-200 rounded w-20"></div>
                <div className="flex-1 h-4 bg-gray-200 rounded"></div>
                <div className="h-4 bg-gray-200 rounded w-12"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error || !userStats || userStats.languages.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Programming Languages</h1>
          <p className="text-gray-600">Your language proficiency and usage statistics</p>
        </div>
        <div className="card p-8 text-center">
          <div className="text-gray-400 mb-4">
            <Code className="h-12 w-12 mx-auto" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Language Data Available</h3>
          <p className="text-gray-600 mb-4">
            {error || 'Scan your repositories to see your programming language statistics'}
          </p>
          <button
            onClick={() => window.location.href = '/developer/scan'}
            className="btn-primary"
          >
            Scan Your Repositories
          </button>
        </div>
      </div>
    );
  }

  const languages = userStats.languages;
  const totalLines = languages.reduce((sum, lang) => sum + (lang.linesOfCode || 0), 0);
  const totalRepos = languages.reduce((sum, lang) => sum + lang.repositories, 0);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Programming Languages</h1>
        <p className="text-gray-600">Your language proficiency and usage statistics</p>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-6"
        >
          <div className="flex items-center space-x-3">
            <div className="bg-primary-100 rounded-lg p-3">
              <Code className="h-6 w-6 text-primary-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Languages</p>
              <p className="text-2xl font-bold text-gray-900">{languages.length}</p>
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
            <div className="bg-secondary-100 rounded-lg p-3">
              <Activity className="h-6 w-6 text-secondary-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Total Lines</p>
              <p className="text-2xl font-bold text-gray-900">{totalLines.toLocaleString()}</p>
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
            <div className="bg-accent-100 rounded-lg p-3">
              <BarChart3 className="h-6 w-6 text-accent-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Repositories</p>
              <p className="text-2xl font-bold text-gray-900">{totalRepos}</p>
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
            <div className="bg-success-100 rounded-lg p-3">
              <Award className="h-6 w-6 text-success-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-600">Primary</p>
              <p className="text-lg font-bold text-gray-900">{languages[0]?.language || 'N/A'}</p>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Language Distribution Chart */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.4 }}
        className="card p-6"
      >
        <h3 className="text-xl font-semibold text-gray-900 mb-6">Language Distribution</h3>
        <div className="space-y-4">
          {languages.map((lang, index) => {
            const proficiency = getProficiencyLevel(lang.percentage || 0);
            return (
              <motion.div
                key={lang.language}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.5 + index * 0.1 }}
                className="flex items-center space-x-4 p-3 hover:bg-gray-50 rounded-lg transition-colors"
              >
                <div className="w-24 text-sm font-medium text-gray-700">
                  {lang.language}
                </div>
                <div className="flex-1 bg-gray-200 rounded-full h-4">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${lang.percentage || 0}%` }}
                    transition={{ delay: 0.7 + index * 0.1, duration: 0.8 }}
                    className={`h-4 rounded-full ${getLanguageColor(lang.language)}`}
                  />
                </div>
                <div className="w-16 text-sm font-semibold text-gray-900 text-right">
                  {(lang.percentage || 0).toFixed(1)}%
                </div>
                <div className={`w-20 text-xs font-medium ${proficiency.color} text-right`}>
                  {proficiency.level}
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.div>

      {/* Detailed Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {languages.map((lang, index) => {
          const proficiency = getProficiencyLevel(lang.percentage || 0);
          return (
            <motion.div
              key={lang.language}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.8 + index * 0.1 }}
              className="card p-6 hover:shadow-lg transition-shadow duration-200"
            >
              <div className="flex items-center space-x-3 mb-4">
                <div className={`w-4 h-4 rounded ${getLanguageColor(lang.language)}`} />
                <h4 className="font-semibold text-gray-900">{lang.language}</h4>
                <span className={`text-xs px-2 py-1 rounded-full ${proficiency.color} bg-opacity-10`}>
                  {proficiency.level}
                </span>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">Usage</span>
                  <div className="flex items-center space-x-2">
                    <div className="w-16 bg-gray-200 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${getLanguageColor(lang.language)}`}
                        style={{ width: `${Math.min((lang.percentage || 0) * 2, 100)}%` }}
                      />
                    </div>
                    <span className="text-sm font-medium">{(lang.percentage || 0).toFixed(1)}%</span>
                  </div>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Lines of Code</span>
                  <span className="text-sm font-medium">{(lang.linesOfCode || 0).toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Repositories</span>
                  <span className="text-sm font-medium">{lang.repositories}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Avg per Repo</span>
                  <span className="text-sm font-medium">
                    {Math.round((lang.linesOfCode || 0) / lang.repositories).toLocaleString()} lines
                  </span>
                </div>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Language Insights */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.0 }}
          className="card p-6"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Language Proficiency</h3>
          <div className="space-y-3">
            {languages.slice(0, 5).map((lang) => {
              const proficiency = getProficiencyLevel(lang.percentage || 0);
              return (
                <div key={lang.language} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center space-x-3">
                    <div className={`w-3 h-3 rounded-full ${getLanguageColor(lang.language)}`} />
                    <span className="text-sm font-medium">{lang.language}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-500">{(lang.percentage || 0).toFixed(1)}%</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${proficiency.color} bg-opacity-10`}>
                      {proficiency.level}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.1 }}
          className="card p-6"
        >
          <h3 className="text-xl font-semibold text-gray-900 mb-4">Language Insights</h3>
          <div className="space-y-4">
            <div className="p-3 bg-primary-50 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <TrendingUp className="h-4 w-4 text-primary-600" />
                <span className="text-sm font-medium text-primary-900">Most Used</span>
              </div>
              <p className="text-sm text-primary-700">
                <strong>{languages[0]?.language}</strong> makes up {languages[0]?.percentage.toFixed(1)}% of your codebase
              </p>
            </div>

            <div className="p-3 bg-secondary-50 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <BarChart3 className="h-4 w-4 text-secondary-600" />
                <span className="text-sm font-medium text-secondary-900">Most Repositories</span>
              </div>
              <p className="text-sm text-secondary-700">
                <strong>{languages.reduce((max, lang) => lang.repositories > max.repositories ? lang : max).language}</strong> is used in {languages.reduce((max, lang) => lang.repositories > max.repositories ? lang : max).repositories} repositories
              </p>
            </div>

            <div className="p-3 bg-accent-50 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <Activity className="h-4 w-4 text-accent-600" />
                <span className="text-sm font-medium text-accent-900">Total Diversity</span>
              </div>
              <p className="text-sm text-accent-700">
                You work with <strong>{languages.length} different languages</strong> across your projects
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default Languages;