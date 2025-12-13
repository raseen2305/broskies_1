import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { 
  Code, 
  BarChart3, 
  Shield, 
  Users, 
  Zap, 
  GitBranch,
  ArrowRight,
  Play,
  Pause
} from 'lucide-react';

const features = [
  {
    id: 'acid-scoring',
    icon: <Code className="h-12 w-12 text-primary-500" />,
    title: "ACID Scoring System",
    description: "Advanced algorithm evaluating Atomicity, Consistency, Isolation, and Durability of code",
    color: "bg-primary-50 border-primary-200",
    details: [
      "Atomicity: Function modularity and single responsibility",
      "Consistency: Code standards and formatting",
      "Isolation: Dependencies and architecture quality",
      "Durability: Testing and maintainability"
    ],
    demo: "See how ACID scoring works with real repositories"
  },
  {
    id: 'analytics',
    icon: <BarChart3 className="h-12 w-12 text-secondary-500" />,
    title: "Comprehensive Analytics",
    description: "Detailed insights on code quality, maintainability, security, and best practices",
    color: "bg-purple-50 border-purple-200",
    details: [
      "Code quality metrics and trends",
      "Security vulnerability detection",
      "Performance optimization suggestions",
      "Best practices compliance"
    ],
    demo: "Explore interactive analytics dashboard"
  },
  {
    id: 'security',
    icon: <Shield className="h-12 w-12 text-accent-500" />,
    title: "Security Assessment",
    description: "Automated vulnerability detection and security best practices evaluation",
    color: "bg-cyan-50 border-cyan-200",
    details: [
      "OWASP Top 10 vulnerability scanning",
      "Dependency security analysis",
      "Code injection detection",
      "Security best practices scoring"
    ],
    demo: "View security assessment report"
  },
  {
    id: 'hr-views',
    icon: <Users className="h-12 w-12 text-success-500" />,
    title: "HR-Optimized Views",
    description: "Streamlined candidate profiles designed for efficient hiring decisions",
    color: "bg-green-50 border-green-200",
    details: [
      "Skill-based candidate filtering",
      "Comparative analysis tools",
      "Hiring recommendation engine",
      "Interview question suggestions"
    ],
    demo: "Experience HR dashboard preview"
  },
  {
    id: 'real-time',
    icon: <Zap className="h-12 w-12 text-warning-500" />,
    title: "Real-time Scanning",
    description: "Fast repository analysis with live progress tracking and instant results",
    color: "bg-yellow-50 border-yellow-200",
    details: [
      "Sub-minute repository analysis",
      "Live progress indicators",
      "Instant result notifications",
      "Batch processing capabilities"
    ],
    demo: "Watch real-time scanning in action"
  },
  {
    id: 'github-integration',
    icon: <GitBranch className="h-12 w-12 text-red-500" />,
    title: "GitHub Integration",
    description: "Seamless connection with GitHub API for comprehensive repository analysis",
    color: "bg-red-50 border-red-200",
    details: [
      "OAuth secure authentication",
      "Automatic repository discovery",
      "Commit history analysis",
      "Collaboration metrics"
    ],
    demo: "Connect your GitHub account"
  }
];

const FeaturesShowcase: React.FC = () => {
  const [activeFeature, setActiveFeature] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const handleFeatureClick = (featureId: string) => {
    setActiveFeature(activeFeature === featureId ? null : featureId);
  };

  const startDemo = () => {
    setIsPlaying(true);
    // Simulate demo playback
    setTimeout(() => setIsPlaying(false), 3000);
  };

  return (
    <section id="features" className="py-20 bg-white relative overflow-hidden">
      {/* Background decorations */}
      <div className="absolute inset-0 opacity-5">
        <div className="absolute top-20 left-10 w-32 h-32 bg-primary-500 rounded-full animate-pulse"></div>
        <div className="absolute bottom-20 right-10 w-24 h-24 bg-secondary-500 rounded-full animate-bounce-slow"></div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
        <div className="text-center mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <span className="inline-block px-4 py-2 bg-primary-100 text-primary-600 rounded-full text-sm font-medium mb-4">
              ✨ Powerful Features
            </span>
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Why Choose BroskiesHub?
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Go beyond resumes with comprehensive code analysis and data-driven insights that reveal true developer potential
            </p>
          </motion.div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={feature.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              className={`card p-8 text-center transition-all duration-300 border-2 ${feature.color} hover:scale-105 cursor-pointer group relative`}
              onClick={() => handleFeatureClick(feature.id)}
              whileHover={{ y: -5 }}
            >
              {/* Feature Icon */}
              <div className="flex justify-center mb-6">
                <motion.div 
                  className="p-3 bg-white rounded-full shadow-md group-hover:shadow-lg transition-shadow duration-300"
                  whileHover={{ rotate: 360 }}
                  transition={{ duration: 0.6 }}
                >
                  {feature.icon}
                </motion.div>
              </div>

              {/* Feature Content */}
              <h3 className="text-xl font-semibold text-gray-900 mb-4 group-hover:text-primary-600 transition-colors">
                {feature.title}
              </h3>
              <p className="text-gray-600 leading-relaxed mb-6">
                {feature.description}
              </p>

              {/* Expandable Details */}
              <motion.div
                initial={false}
                animate={{ 
                  height: activeFeature === feature.id ? 'auto' : 0,
                  opacity: activeFeature === feature.id ? 1 : 0
                }}
                transition={{ duration: 0.3 }}
                className="overflow-hidden"
              >
                <div className="border-t border-gray-200 pt-4 mb-4">
                  <ul className="text-left space-y-2">
                    {feature.details.map((detail, detailIndex) => (
                      <motion.li
                        key={detailIndex}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ 
                          opacity: activeFeature === feature.id ? 1 : 0,
                          x: activeFeature === feature.id ? 0 : -10
                        }}
                        transition={{ delay: detailIndex * 0.1 }}
                        className="flex items-start text-sm text-gray-600"
                      >
                        <span className="text-primary-500 mr-2">•</span>
                        {detail}
                      </motion.li>
                    ))}
                  </ul>
                </div>
              </motion.div>

              {/* Demo Button - Commented out for now */}
              {/*
              <motion.button
                onClick={(e) => {
                  e.stopPropagation();
                  startDemo();
                }}
                className="w-full bg-gradient-to-r from-primary-500 to-secondary-500 text-white py-2 px-4 rounded-lg font-medium hover:shadow-lg transition-all duration-200 flex items-center justify-center space-x-2 group-hover:scale-105"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                {isPlaying ? (
                  <>
                    <Pause className="h-4 w-4" />
                    <span>Playing Demo...</span>
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    <span>Try Demo</span>
                  </>
                )}
              </motion.button>
              */}

              {/* Hover Arrow */}
              <motion.div
                className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity duration-200"
                initial={{ rotate: 0 }}
                whileHover={{ rotate: 45 }}
              >
                <ArrowRight className="h-5 w-5 text-primary-500" />
              </motion.div>
            </motion.div>
          ))}
        </div>

        {/* Interactive Demo Section - Commented out for now */}
        {/*
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.8 }}
          className="mt-16 text-center"
        >
          <div className="bg-gradient-to-r from-primary-500 to-secondary-500 rounded-2xl p-8 text-white">
            <h3 className="text-2xl font-bold mb-4">
              Ready to Experience the Power?
            </h3>
            <p className="text-lg mb-6 opacity-90">
              See how BroskiesHub transforms code analysis with our interactive demo
            </p>
            <motion.button
              onClick={startDemo}
              className="bg-white text-primary-500 hover:bg-gray-100 font-semibold py-3 px-8 rounded-lg transition-colors duration-200 inline-flex items-center space-x-2"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Play className="h-5 w-5" />
              <span>Start Interactive Demo</span>
            </motion.button>
          </div>
        </motion.div>
        */}
      </div>
    </section>
  );
};

export default FeaturesShowcase;