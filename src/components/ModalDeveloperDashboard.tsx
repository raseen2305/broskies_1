/**
 * Modal Developer Dashboard
 * 
 * A version of DeveloperDashboard that uses internal state for navigation
 * instead of React Router, so it doesn't change the browser URL when used in a modal.
 */

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  BarChart3, 
  Code, 
  Layers, 
  GitBranch, 
  Award,
  GitPullRequest,
  AlertCircle,
  X
} from 'lucide-react';
import Overview from './dashboard/Overview';
import Languages from './dashboard/Languages';
import TechStack from './dashboard/TechStack';
import Repositories from './dashboard/Repositories';
import RepositoryDetail from './dashboard/RepositoryDetail';
import ContributionCalendar from './dashboard/ContributionCalendar';
import PullRequestAnalysis from './dashboard/PullRequestAnalysis';
import IssueAnalysis from './dashboard/IssueAnalysis';
import ExternalRankingWidget from './ExternalRankingWidget';

interface ModalDeveloperDashboardProps {
  scanResults: any;
}

type TabType = 'overview' | 'rankings' | 'languages' | 'tech-stack' | 'repositories' | 'pull-requests' | 'issues' | 'activity';

const ModalDeveloperDashboard: React.FC<ModalDeveloperDashboardProps> = ({ scanResults }) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [selectedRepository, setSelectedRepository] = useState<string | null>(null);

  const navItems = [
    { id: 'overview' as TabType, icon: BarChart3, label: 'Overview' },
    { id: 'rankings' as TabType, icon: Award, label: 'Rankings' },
    { id: 'languages' as TabType, icon: Code, label: 'Languages' },
    { id: 'tech-stack' as TabType, icon: Layers, label: 'Tech Stack' },
    { id: 'repositories' as TabType, icon: GitBranch, label: 'Repositories' },
    { id: 'pull-requests' as TabType, icon: GitPullRequest, label: 'Pull Requests' },
    { id: 'issues' as TabType, icon: AlertCircle, label: 'Issues' },
  ];

  const handleRepositoryClick = (repoName: string) => {
    setSelectedRepository(repoName);
  };

  const handleBackToRepositories = () => {
    setSelectedRepository(null);
  };

  const renderContent = () => {
    // If a repository is selected, show repository detail
    if (selectedRepository) {
      return (
        <RepositoryDetail 
          scanResults={scanResults}
          repositoryName={selectedRepository}
          onBack={handleBackToRepositories}
        />
      );
    }

    // Otherwise show the active tab content
    switch (activeTab) {
      case 'overview':
        return <Overview scanResults={scanResults} />;
      
      case 'rankings':
        return (
          <div className="p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Rankings</h2>
            <ExternalRankingWidget githubUsername={scanResults.targetUsername} />
          </div>
        );
      
      case 'languages':
        return <Languages scanResults={scanResults} />;
      
      case 'tech-stack':
        return <TechStack scanResults={scanResults} />;
      
      case 'repositories':
        return (
          <Repositories 
            scanResults={scanResults}
            onRepositoryClick={handleRepositoryClick}
          />
        );
      
      case 'pull-requests':
        return <PullRequestAnalysis scanResults={scanResults} />;
      
      case 'issues':
        return <IssueAnalysis scanResults={scanResults} />;
      
      case 'activity':
        return <ContributionCalendar scanResults={scanResults} />;
      
      default:
        return <Overview scanResults={scanResults} />;
    }
  };

  return (
    <div className="flex h-full bg-gray-50">
      {/* Sidebar Navigation */}
      <div className="w-64 bg-white border-r border-gray-200 flex-shrink-0 overflow-y-auto">
        <div className="p-4">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
            Navigation
          </h3>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveTab(item.id);
                    setSelectedRepository(null); // Clear selected repo when changing tabs
                  }}
                  className={`
                    w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors
                    ${isActive 
                      ? 'bg-primary-50 text-primary-700 border-l-4 border-primary-600' 
                      : 'text-gray-700 hover:bg-gray-50 border-l-4 border-transparent'
                    }
                  `}
                >
                  <Icon className={`h-5 w-5 ${isActive ? 'text-primary-600' : 'text-gray-400'}`} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={selectedRepository || activeTab}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
            className="h-full"
          >
            {renderContent()}
          </motion.div>
        </AnimatePresence>
      </div>
    </div>
  );
};

export default ModalDeveloperDashboard;
