import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Target, TrendingUp, Clock, CheckCircle, BookOpen, ExternalLink, Star } from 'lucide-react';
import { useAuth } from '../../contexts/AuthContext';
import { scanAPI } from '../../services/api';

interface RoadmapItem {
  title: string;
  description: string;
  priority: string;
  category: string;
  estimatedTime: string;
  skills: (string | { name: string; [key: string]: any })[];
  resources: (string | { name: string; [key: string]: any })[];
}

interface UserStats {
  roadmap: RoadmapItem[];
}

interface RoadmapProps {
  scanResults?: any;
}

const Roadmap: React.FC<RoadmapProps> = ({ scanResults }) => {
  const { user } = useAuth();
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadRoadmap = async () => {
      // If scan results are provided, use them directly
      if (scanResults) {
        console.log('📊 Roadmap using provided scan results:', scanResults);
        
        // Clear any previous errors
        setError(null);
        
        // Check if roadmap is available or if there's a reason it's unavailable
        let roadmapData: RoadmapItem[] = [];
        let unavailableReason: string | null = null;
        
        if (scanResults.roadmap && scanResults.roadmap.length > 0) {
          roadmapData = scanResults.roadmap;
        } else if (scanResults.roadmap_unavailable_reason) {
          unavailableReason = scanResults.roadmap_unavailable_reason;
        }
        
        const transformedStats: UserStats = {
          roadmap: roadmapData
        };
        
        // Set error if roadmap is unavailable with a reason
        if (unavailableReason) {
          setError(unavailableReason);
        }
        
        setUserStats(transformedStats);
        setIsLoading(false);
        return;
      }
      
      // Don't automatically load authenticated user data
      if (!user?.id) {
        setError('Please log in to view your roadmap or scan a GitHub profile.');
        setIsLoading(false);
        return;
      }
      
      // Let the user explicitly scan their own profile if needed
      setError('Please scan a GitHub profile to view learning roadmap.');
      setIsLoading(false);
    };

    loadRoadmap();
  }, [user?.id, scanResults]);

  const getPriorityColor = (priority: string) => {
    const colors = {
      'High': 'bg-red-100 text-red-600 border-red-200',
      'Medium': 'bg-yellow-100 text-yellow-600 border-yellow-200',
      'Low': 'bg-green-100 text-green-600 border-green-200'
    };
    return colors[priority] || colors['Medium'];
  };

  const getPriorityIcon = (priority: string) => {
    if (priority === 'High') return <Target className="h-4 w-4" />;
    if (priority === 'Medium') return <TrendingUp className="h-4 w-4" />;
    return <CheckCircle className="h-4 w-4" />;
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div>
          <div className="h-8 bg-gray-200 rounded w-64 mb-2 animate-pulse"></div>
          <div className="h-4 bg-gray-200 rounded w-96 animate-pulse"></div>
        </div>
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="card p-6 animate-pulse">
              <div className="h-6 bg-gray-200 rounded w-48 mb-4"></div>
              <div className="space-y-2">
                <div className="h-4 bg-gray-200 rounded"></div>
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || !userStats?.roadmap || userStats.roadmap.length === 0) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Learning Roadmap</h1>
          <p className="text-gray-600">Personalized recommendations for your skill development</p>
        </div>
        <div className="card p-6 text-center">
          <div className="text-gray-400 mb-4">
            <Target className="h-12 w-12 mx-auto" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No Roadmap Available</h3>
          <p className="text-gray-600 mb-4">
            {error || 'Please scan a GitHub profile to generate a personalized learning roadmap.'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Learning Roadmap</h1>
        <p className="text-gray-600">Personalized recommendations based on your current skills and GitHub activity</p>
      </div>

      {/* Roadmap Overview */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="card p-4 text-center"
        >
          <Target className="h-8 w-8 text-red-500 mx-auto mb-2" />
          <h3 className="font-semibold text-gray-900">High Priority</h3>
          <p className="text-sm text-gray-500">
            {userStats?.roadmap?.filter(item => item.priority === 'High').length || 0} recommendations
          </p>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="card p-4 text-center"
        >
          <TrendingUp className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
          <h3 className="font-semibold text-gray-900">Medium Priority</h3>
          <p className="text-sm text-gray-500">
            {userStats?.roadmap?.filter(item => item.priority === 'Medium').length || 0} recommendations
          </p>
        </motion.div>
        
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="card p-4 text-center"
        >
          <Clock className="h-8 w-8 text-blue-500 mx-auto mb-2" />
          <h3 className="font-semibold text-gray-900">Total Time</h3>
          <p className="text-sm text-gray-500">
            {userStats?.roadmap?.length ? `${userStats.roadmap.length} learning paths` : 'No paths yet'}
          </p>
        </motion.div>
      </div>

      {/* Roadmap Items */}
      <div className="space-y-4">
        {userStats?.roadmap?.map((item, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 + index * 0.1 }}
            className="card p-6"
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h3 className="text-xl font-semibold text-gray-900">{item.title}</h3>
                  <span className={`px-2 py-1 rounded-full text-xs font-medium border ${getPriorityColor(item.priority)}`}>
                    <div className="flex items-center space-x-1">
                      {getPriorityIcon(item.priority)}
                      <span>{item.priority}</span>
                    </div>
                  </span>
                </div>
                <p className="text-gray-600 mb-3">{item.description}</p>
                <div className="flex items-center space-x-4 text-sm text-gray-500">
                  <div className="flex items-center space-x-1">
                    <Clock className="h-4 w-4" />
                    <span>{item.estimatedTime}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <BookOpen className="h-4 w-4" />
                    <span>{item.category}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Skills to Learn */}
            {item.skills && item.skills.length > 0 && (
              <div className="mb-4">
                <h4 className="font-medium text-gray-900 mb-2">Skills to Master:</h4>
                <div className="flex flex-wrap gap-2">
                  {item.skills.map((skill, skillIndex) => (
                    <span
                      key={skillIndex}
                      className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
                    >
                      {typeof skill === 'string' 
                        ? skill 
                        : typeof skill === 'object' && skill?.name 
                          ? skill.name 
                          : JSON.stringify(skill)
                      }
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Learning Resources */}
            {item.resources && item.resources.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 mb-2">Recommended Resources:</h4>
                <div className="space-y-2">
                  {item.resources.map((resource, resourceIndex) => (
                    <div
                      key={resourceIndex}
                      className="flex items-center space-x-2 text-sm text-gray-600"
                    >
                      <ExternalLink className="h-4 w-4 text-gray-400" />
                      <span>
                        {typeof resource === 'string' 
                          ? resource 
                          : typeof resource === 'object' && resource?.name 
                            ? resource.name 
                            : JSON.stringify(resource)
                        }
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        ))}
      </div>

      {/* No Roadmap Message */}
      {(!userStats?.roadmap || userStats.roadmap.length === 0) && (
        <div className="card p-8 text-center">
          <Target className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Learning Path Generated</h3>
          <p className="text-gray-600 mb-4">
            We need more information about your repositories to generate personalized recommendations.
          </p>
          <div className="text-sm text-gray-500 max-w-md mx-auto">
            <p>Try adding more repositories with clear technology indicators, topics, or descriptions to get better recommendations.</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default Roadmap;