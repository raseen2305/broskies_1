import React, { useState } from 'react';
import { Target, Calendar, CheckCircle, Circle, Folder, TrendingUp } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// Types (Requirements: 2.3, 6.3)
interface Milestone {
  title: string;
  description?: string;
  dueDate?: string;
  state: 'open' | 'closed';
  progress: number; // 0-100
  openIssues: number;
  closedIssues: number;
}

interface Project {
  name: string;
  description?: string;
  state: 'open' | 'closed';
  progress: number; // 0-100
}

interface RoadmapData {
  milestones: Milestone[];
  projects: Project[];
  totalMilestones: number;
  openMilestones: number;
  closedMilestones: number;
  totalProjects: number;
  openProjects: number;
  closedProjects: number;
}

interface RoadmapDisplayProps {
  roadmap: RoadmapData;
  repoName?: string;
  className?: string;
}

const RoadmapDisplay: React.FC<RoadmapDisplayProps> = ({
  roadmap,
  repoName,
  className = ''
}) => {
  const [activeTab, setActiveTab] = useState<'milestones' | 'projects'>('milestones');
  const [showAll, setShowAll] = useState(false);

  // Calculate overall progress
  const overallProgress = roadmap.totalMilestones > 0
    ? Math.round((roadmap.closedMilestones / roadmap.totalMilestones) * 100)
    : 0;

  // Format date
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'No due date';
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) return `${Math.abs(diffDays)} days overdue`;
    if (diffDays === 0) return 'Due today';
    if (diffDays === 1) return 'Due tomorrow';
    if (diffDays < 7) return `Due in ${diffDays} days`;
    return date.toLocaleDateString();
  };

  // Get due date color
  const getDueDateColor = (dateString?: string) => {
    if (!dateString) return 'text-gray-500';
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    
    if (diffDays < 0) return 'text-red-600 dark:text-red-400';
    if (diffDays < 7) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-green-600 dark:text-green-400';
  };

  const hasMilestones = roadmap.milestones && roadmap.milestones.length > 0;
  const hasProjects = roadmap.projects && roadmap.projects.length > 0;
  const hasRoadmap = hasMilestones || hasProjects;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-xl transition-shadow duration-300 ${className}`}
    >
      {/* Header */}
      <div className="p-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
              <Target className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Roadmap
              </h3>
              {repoName && (
                <p className="text-sm text-gray-600 dark:text-gray-400">{repoName}</p>
              )}
            </div>
          </div>
          <div className="text-right">
            <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              {overallProgress}%
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">Complete</div>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
          <motion.div
            className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${overallProgress}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          />
        </div>
      </div>

      {hasRoadmap ? (
        <>
          {/* Tabs */}
          <div className="flex border-b border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setActiveTab('milestones')}
              className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${
                activeTab === 'milestones'
                  ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400 bg-blue-50 dark:bg-blue-900/20'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-900/50'
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                <Target className="w-4 h-4" />
                Milestones ({roadmap.totalMilestones})
              </div>
            </button>
            <button
              onClick={() => setActiveTab('projects')}
              className={`flex-1 px-6 py-3 text-sm font-medium transition-colors ${
                activeTab === 'projects'
                  ? 'text-blue-600 dark:text-blue-400 border-b-2 border-blue-600 dark:border-blue-400 bg-blue-50 dark:bg-blue-900/20'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-gray-50 dark:hover:bg-gray-900/50'
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                <Folder className="w-4 h-4" />
                Projects ({roadmap.totalProjects})
              </div>
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            <AnimatePresence mode="wait">
              {activeTab === 'milestones' && (
                <motion.div
                  key="milestones"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  className="space-y-4"
                >
                  {hasMilestones ? (
                    <>
                      {roadmap.milestones
                        .slice(0, showAll ? undefined : 3)
                        .map((milestone, index) => (
                          <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.05 }}
                            className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700"
                          >
                            <div className="flex items-start justify-between mb-3">
                              <div className="flex items-start gap-3 flex-1">
                                <div className={`p-1.5 rounded ${
                                  milestone.state === 'closed'
                                    ? 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                                    : 'bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400'
                                }`}>
                                  {milestone.state === 'closed' ? (
                                    <CheckCircle className="w-4 h-4" />
                                  ) : (
                                    <Circle className="w-4 h-4" />
                                  )}
                                </div>
                                <div className="flex-1">
                                  <h4 className="font-medium text-gray-900 dark:text-gray-100">
                                    {milestone.title}
                                  </h4>
                                  {milestone.description && (
                                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                      {milestone.description}
                                    </p>
                                  )}
                                </div>
                              </div>
                              <span className={`text-xs font-medium px-2 py-1 rounded ${
                                milestone.state === 'closed'
                                  ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                                  : 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
                              }`}>
                                {milestone.state}
                              </span>
                            </div>

                            {/* Progress */}
                            <div className="mb-3">
                              <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
                                <span>Progress</span>
                                <span>{milestone.progress}%</span>
                              </div>
                              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                                <div
                                  className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                                  style={{ width: `${milestone.progress}%` }}
                                />
                              </div>
                            </div>

                            {/* Meta */}
                            <div className="flex items-center justify-between text-xs">
                              <div className="flex items-center gap-4 text-gray-600 dark:text-gray-400">
                                <span>{milestone.openIssues} open</span>
                                <span>{milestone.closedIssues} closed</span>
                              </div>
                              {milestone.dueDate && (
                                <div className={`flex items-center gap-1 ${getDueDateColor(milestone.dueDate)}`}>
                                  <Calendar className="w-3 h-3" />
                                  <span>{formatDate(milestone.dueDate)}</span>
                                </div>
                              )}
                            </div>
                          </motion.div>
                        ))}

                      {roadmap.milestones.length > 3 && (
                        <button
                          onClick={() => setShowAll(!showAll)}
                          className="w-full py-2 text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                        >
                          {showAll ? 'Show Less' : `Show All ${roadmap.milestones.length} Milestones`}
                        </button>
                      )}
                    </>
                  ) : (
                    <div className="text-center py-8">
                      <Target className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        No milestones found
                      </p>
                    </div>
                  )}
                </motion.div>
              )}

              {activeTab === 'projects' && (
                <motion.div
                  key="projects"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  className="space-y-4"
                >
                  {hasProjects ? (
                    <>
                      {roadmap.projects
                        .slice(0, showAll ? undefined : 3)
                        .map((project, index) => (
                          <motion.div
                            key={index}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: index * 0.05 }}
                            className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700"
                          >
                            <div className="flex items-start justify-between mb-3">
                              <div className="flex items-start gap-3 flex-1">
                                <div className={`p-1.5 rounded ${
                                  project.state === 'closed'
                                    ? 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400'
                                    : 'bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400'
                                }`}>
                                  <Folder className="w-4 h-4" />
                                </div>
                                <div className="flex-1">
                                  <h4 className="font-medium text-gray-900 dark:text-gray-100">
                                    {project.name}
                                  </h4>
                                  {project.description && (
                                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                      {project.description}
                                    </p>
                                  )}
                                </div>
                              </div>
                              <span className={`text-xs font-medium px-2 py-1 rounded ${
                                project.state === 'closed'
                                  ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                                  : 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400'
                              }`}>
                                {project.state}
                              </span>
                            </div>

                            {/* Progress */}
                            <div>
                              <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
                                <span>Progress</span>
                                <span>{project.progress}%</span>
                              </div>
                              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                                <div
                                  className="bg-purple-500 h-1.5 rounded-full transition-all duration-300"
                                  style={{ width: `${project.progress}%` }}
                                />
                              </div>
                            </div>
                          </motion.div>
                        ))}

                      {roadmap.projects.length > 3 && (
                        <button
                          onClick={() => setShowAll(!showAll)}
                          className="w-full py-2 text-sm font-medium text-purple-600 dark:text-purple-400 hover:text-purple-700 dark:hover:text-purple-300 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded-lg transition-colors"
                        >
                          {showAll ? 'Show Less' : `Show All ${roadmap.projects.length} Projects`}
                        </button>
                      )}
                    </>
                  ) : (
                    <div className="text-center py-8">
                      <Folder className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        No projects found
                      </p>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </>
      ) : (
        <div className="p-12 text-center">
          <Target className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h4 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            No Roadmap Data
          </h4>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            This repository doesn't have any milestones or projects yet
          </p>
        </div>
      )}
    </motion.div>
  );
};

export default RoadmapDisplay;
