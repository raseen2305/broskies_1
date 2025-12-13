import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Layers, Database, Wrench, Globe, Code, Cloud, Smartphone, TestTube } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { scanAPI } from '../../services/api';

interface TechItem {
  name: string;
  confidence: number;
  repositories: number;
  category: string;
}

interface UserStats {
  techStack: TechItem[];
}

interface TechStackProps {
  scanResults?: any;
}

const TechStack: React.FC<TechStackProps> = ({ scanResults }) => {
  const { user } = useAuth();
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadTechStack = async () => {
      // If scan results are provided, use them directly
      if (scanResults) {
        console.log('📊 TechStack using provided scan results:', scanResults);
        
        // Clear any previous errors
        setError(null);
        
        // Extract tech stack data from scan results
        let techStackData: TechItem[] = [];
        
        console.log('📊 TechStack data from backend:', scanResults.techStack);
        console.log('📊 TechStack type:', typeof scanResults.techStack);
        console.log('📊 TechStack is array:', Array.isArray(scanResults.techStack));
        
        if (scanResults.techStack && Array.isArray(scanResults.techStack) && scanResults.techStack.length > 0) {
          // Use direct techStack array if available
          console.log('✅ Using techStack from backend:', scanResults.techStack.length, 'items');
          techStackData = scanResults.techStack.map((item: any) => ({
            name: item.name || 'Unknown',
            confidence: item.usage_percentage || item.confidence || 50,
            repositories: item.repository_count || item.repositories || 0,
            category: item.type === 'language' ? 'Language' : item.type === 'framework' ? 'Framework' : item.category || 'Other'
          }));
        } else {
          // Try to infer tech stack from language data and other sources
          const languages = scanResults.languageStatistics?.language_breakdown || {};
          const repositories = scanResults.repositories || scanResults.repositoryDetails || [];
          
          // Create basic tech stack from languages
          Object.entries(languages).forEach(([language, data]: [string, any]) => {
            let category = 'Other';
            
            // Categorize languages
            if (['JavaScript', 'TypeScript', 'HTML', 'CSS', 'Vue', 'React', 'Angular'].includes(language)) {
              category = 'Frontend';
            } else if (['Python', 'Java', 'Go', 'Rust', 'C++', 'C#', 'PHP', 'Ruby', 'Node.js'].includes(language)) {
              category = 'Backend';
            } else if (['SQL', 'MongoDB', 'PostgreSQL', 'MySQL'].includes(language)) {
              category = 'Database';
            }
            
            techStackData.push({
              name: language,
              confidence: Math.min((data.percentage || 0) * 2, 100), // Convert percentage to confidence
              repositories: data.repository_count || 0,
              category
            });
          });
          
          // Add common frameworks/tools based on repository analysis
          if (repositories.length > 0) {
            const repoTopics = repositories.flatMap((repo: any) => repo.topics || []);
            const commonFrameworks = ['react', 'vue', 'angular', 'express', 'django', 'flask', 'spring', 'laravel'];
            
            commonFrameworks.forEach(framework => {
              if (repoTopics.includes(framework)) {
                const repoCount = repositories.filter((repo: any) => 
                  (repo.topics || []).includes(framework)
                ).length;
                
                let category = 'Other';
                if (['react', 'vue', 'angular'].includes(framework)) category = 'Frontend';
                if (['express', 'django', 'flask', 'spring', 'laravel'].includes(framework)) category = 'Backend';
                
                techStackData.push({
                  name: framework.charAt(0).toUpperCase() + framework.slice(1),
                  confidence: Math.min((repoCount / repositories.length) * 100, 100),
                  repositories: repoCount,
                  category
                });
              }
            });
          }
        }
        
        const transformedStats: UserStats = {
          techStack: techStackData
        };
        
        setUserStats(transformedStats);
        setIsLoading(false);
        return;
      }
      
      // Don't automatically load authenticated user data
      if (!user?.id) {
        setError('Please log in to view your tech stack or scan a GitHub profile.');
        setIsLoading(false);
        return;
      }
      
      // Let the user explicitly scan their own profile if needed
      setError('Please scan a GitHub profile to view tech stack analysis.');
      setIsLoading(false);
    };

    loadTechStack();
  }, [user?.id, scanResults]);

  const getCategoryIcon = (category: string) => {
    const icons = {
      'Frontend': <Code className="h-5 w-5" />,
      'Backend': <Database className="h-5 w-5" />,
      'Database': <Database className="h-5 w-5" />,
      'Cloud & DevOps': <Cloud className="h-5 w-5" />,
      'Testing': <TestTube className="h-5 w-5" />,
      'Build Tools': <Wrench className="h-5 w-5" />,
      'Mobile': <Smartphone className="h-5 w-5" />,
      'Other': <Layers className="h-5 w-5" />
    };
    return icons[category] || icons['Other'];
  };

  const getCategoryColor = (category: string) => {
    const colors = {
      'Frontend': 'bg-blue-100 text-blue-600 border-blue-200',
      'Backend': 'bg-green-100 text-green-600 border-green-200',
      'Database': 'bg-purple-100 text-purple-600 border-purple-200',
      'Cloud & DevOps': 'bg-orange-100 text-orange-600 border-orange-200',
      'Testing': 'bg-red-100 text-red-600 border-red-200',
      'Build Tools': 'bg-yellow-100 text-yellow-600 border-yellow-200',
      'Mobile': 'bg-pink-100 text-pink-600 border-pink-200',
      'Other': 'bg-gray-100 text-gray-600 border-gray-200'
    };
    return colors[category] || colors['Other'];
  };

  // Group technologies by category
  const groupedTechStack = userStats?.techStack?.reduce((acc, tech) => {
    if (!acc[tech.category]) {
      acc[tech.category] = [];
    }
    acc[tech.category].push(tech);
    return acc;
  }, {} as Record<string, TechItem[]>) || {};
  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <div className="h-8 bg-gray-200 rounded w-64 mb-2 animate-pulse"></div>
          <div className="h-4 bg-gray-200 rounded w-96 animate-pulse"></div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="card p-6 animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-32 mb-4"></div>
              <div className="space-y-3">
                {[...Array(3)].map((_, j) => (
                  <div key={j} className="h-4 bg-gray-200 rounded"></div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || !userStats?.techStack || userStats.techStack.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Technology Stack</h1>
          <p className="text-gray-600">Your experience with frameworks, libraries, tools, and databases</p>
        </div>
        <div className="card p-6 text-center">
          <div className="text-gray-400 mb-4">
            <Layers className="h-12 w-12 mx-auto" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Technology Stack Data</h3>
          <p className="text-gray-600 mb-4">
            {error || 'Please scan a GitHub profile to view technology stack analysis.'}
          </p>
        </div>
      </div>
    );
  }

  const getProficiencyLevel = (confidence: number) => {
    if (confidence >= 80) return { level: 'Expert', color: 'text-green-600' };
    if (confidence >= 60) return { level: 'Intermediate', color: 'text-yellow-600' };
    return { level: 'Beginner', color: 'text-red-600' };
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Technology Stack</h1>
        <p className="text-gray-600">Technologies detected from your GitHub repositories</p>
      </div>

      {/* Tech Stack Overview */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {Object.entries(groupedTechStack).map(([category, techs], index) => (
          <motion.div
            key={category}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="card p-4 text-center"
          >
            <div className={`p-2 rounded-lg inline-block mb-2 ${getCategoryColor(category)}`}>
              {getCategoryIcon(category)}
            </div>
            <h3 className="font-semibold text-gray-900">{category}</h3>
            <p className="text-sm text-gray-500">
              {techs.length} {techs.length === 1 ? 'technology' : 'technologies'}
            </p>
          </motion.div>
        ))}
      </div>

      {/* Detailed Tech Stack by Category */}
      {Object.entries(groupedTechStack).map(([category, techs], categoryIndex) => (
        <motion.div
          key={category}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 + categoryIndex * 0.1 }}
          className="card p-6"
        >
          <div className="flex items-center space-x-3 mb-6">
            <div className={`p-2 rounded-lg ${getCategoryColor(category)}`}>
              {getCategoryIcon(category)}
            </div>
            <h3 className="text-xl font-semibold text-gray-900">{category}</h3>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {techs.map((tech, index) => {
              const proficiency = getProficiencyLevel(tech.confidence);
              return (
                <motion.div
                  key={tech.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.6 + categoryIndex * 0.1 + index * 0.05 }}
                  className="flex items-center space-x-4 p-4 bg-gray-50 rounded-lg"
                >
                  <div className={`p-2 rounded-lg ${getCategoryColor(category)}`}>
                    {getCategoryIcon(category)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <h4 className="font-medium text-gray-900">{tech.name}</h4>
                      <span className={`text-sm font-medium ${proficiency.color}`}>
                        {proficiency.level}
                      </span>
                    </div>
                    <div className="flex items-center space-x-2 mb-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${tech.confidence}%` }}
                          transition={{ delay: 0.8 + categoryIndex * 0.1 + index * 0.05, duration: 0.6 }}
                          className="h-2 rounded-full bg-gradient-to-r from-primary-500 to-secondary-500"
                        />
                      </div>
                      <span className="text-sm font-medium text-gray-600">
                        {Math.round(tech.confidence)}%
                      </span>
                    </div>
                    <p className="text-xs text-gray-500">
                      Used in {tech.repositories} {tech.repositories === 1 ? 'repository' : 'repositories'}
                    </p>
                  </div>
                </motion.div>
              );
            })}
          </div>
        </motion.div>
      ))}

      {/* No Tech Stack Message */}
      {(!userStats?.techStack || userStats.techStack.length === 0) && (
        <div className="card p-8 text-center">
          <Layers className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Technologies Detected</h3>
          <p className="text-gray-600 mb-4">
            We couldn't detect any technologies from your repositories. This might happen if:
          </p>
          <ul className="text-sm text-gray-500 text-left max-w-md mx-auto space-y-1">
            <li>• Your repositories don't have clear technology indicators</li>
            <li>• Repository topics or descriptions are missing</li>
            <li>• You have mostly private repositories</li>
          </ul>
        </div>
      )}
    </div>
  );
};

export default TechStack;