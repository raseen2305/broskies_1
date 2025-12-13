import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, BookOpen, Wrench, TestTube, FileText, Lock, Zap, Code } from 'lucide-react';

interface QualityMetric {
  id: string;
  title: string;
  value: number;
  color: string;
  icon: React.ReactNode;
  description: string;
}

interface AnimatedQualityWheelProps {
  qualityMetrics?: {
    readability?: number;
    maintainability?: number;
    security?: number;
    test_coverage?: number;
    documentation?: number;
    performance?: number;
    complexity?: number;
    best_practices?: number;
  };
  overallScore?: number;
}

const AnimatedQualityWheel: React.FC<AnimatedQualityWheelProps> = ({
  qualityMetrics = {},
  overallScore = 0
}) => {
  const [hoveredSegment, setHoveredSegment] = useState<string | null>(null);
  const [animationComplete, setAnimationComplete] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setAnimationComplete(true), 2000);
    return () => clearTimeout(timer);
  }, []);

  // Define the 8 quality metrics with colors and icons
  const metrics: QualityMetric[] = [
    {
      id: 'readability',
      title: 'Readability',
      value: qualityMetrics.readability || 0,
      color: '#10b981', // green
      icon: <BookOpen className="w-5 h-5" />,
      description: 'Code clarity and ease of understanding'
    },
    {
      id: 'maintainability',
      title: 'Maintainability',
      value: qualityMetrics.maintainability || 0,
      color: '#3b82f6', // blue
      icon: <Wrench className="w-5 h-5" />,
      description: 'Ease of making changes and updates'
    },
    {
      id: 'security',
      title: 'Security',
      value: qualityMetrics.security || 0,
      color: '#ef4444', // red
      icon: <Shield className="w-5 h-5" />,
      description: 'Protection against vulnerabilities'
    },
    {
      id: 'test_coverage',
      title: 'Test Coverage',
      value: qualityMetrics.test_coverage || 0,
      color: '#f59e0b', // orange
      icon: <TestTube className="w-5 h-5" />,
      description: 'Extent of automated testing'
    },
    {
      id: 'documentation',
      title: 'Documentation',
      value: qualityMetrics.documentation || 0,
      color: '#8b5cf6', // purple
      icon: <FileText className="w-5 h-5" />,
      description: 'Quality and completeness of docs'
    },
    {
      id: 'performance',
      title: 'Performance',
      value: qualityMetrics.performance || 75,
      color: '#ec4899', // pink
      icon: <Zap className="w-5 h-5" />,
      description: 'Code efficiency and speed'
    },
    {
      id: 'complexity',
      title: 'Complexity',
      value: qualityMetrics.complexity || 70,
      color: '#14b8a6', // teal
      icon: <Code className="w-5 h-5" />,
      description: 'Code complexity management'
    },
    {
      id: 'best_practices',
      title: 'Best Practices',
      value: qualityMetrics.best_practices || 80,
      color: '#6366f1', // indigo
      icon: <Lock className="w-5 h-5" />,
      description: 'Adherence to coding standards'
    }
  ];

  // Calculate segment angles based on values (proportional sizing like in the picture)
  const totalValue = metrics.reduce((sum, m) => sum + m.value, 0);
  const radius = 140;
  const innerRadius = 80;
  const centerX = 200;
  const centerY = 200;

  // Calculate proportional angles for each segment
  const segmentAngles = metrics.map(m => (m.value / totalValue) * 360);

  // Function to create SVG path for each segment with proportional size
  const createSegmentPath = (index: number) => {
    // Calculate start angle (sum of all previous segments)
    const startAngleDeg = metrics.slice(0, index).reduce((sum, m, i) => sum + segmentAngles[i], 0) - 90;
    const endAngleDeg = startAngleDeg + segmentAngles[index];
    
    const startAngle = startAngleDeg * (Math.PI / 180);
    const endAngle = endAngleDeg * (Math.PI / 180);

    const x1 = centerX + innerRadius * Math.cos(startAngle);
    const y1 = centerY + innerRadius * Math.sin(startAngle);
    const x2 = centerX + radius * Math.cos(startAngle);
    const y2 = centerY + radius * Math.sin(startAngle);
    const x3 = centerX + radius * Math.cos(endAngle);
    const y3 = centerY + radius * Math.sin(endAngle);
    const x4 = centerX + innerRadius * Math.cos(endAngle);
    const y4 = centerY + innerRadius * Math.sin(endAngle);

    // Use large arc flag if angle > 180 degrees
    const largeArcFlag = segmentAngles[index] > 180 ? 1 : 0;

    return `M ${x1} ${y1} L ${x2} ${y2} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x3} ${y3} L ${x4} ${y4} A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${x1} ${y1} Z`;
  };

  // Function to get label position (center of each segment)
  const getLabelPosition = (index: number) => {
    // Calculate the middle angle of this segment
    const startAngleDeg = metrics.slice(0, index).reduce((sum, m, i) => sum + segmentAngles[i], 0) - 90;
    const middleAngleDeg = startAngleDeg + segmentAngles[index] / 2;
    const angle = middleAngleDeg * (Math.PI / 180);
    
    const labelRadius = radius + 40;
    return {
      x: centerX + labelRadius * Math.cos(angle),
      y: centerY + labelRadius * Math.sin(angle)
    };
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="relative w-full h-full flex items-center justify-center">
      <svg width="500" height="500" viewBox="0 0 400 400" className="overflow-visible">
        {/* Segments */}
        {metrics.map((metric, index) => {
          const isHovered = hoveredSegment === metric.id;
          const scale = isHovered ? 1.05 : 1;
          
          return (
            <g key={metric.id}>
              <motion.path
                d={createSegmentPath(index)}
                fill={metric.color}
                opacity={isHovered ? 0.95 : 0.8}
                initial={{ scale: 0, opacity: 0 }}
                animate={{ 
                  scale: animationComplete ? scale : 1,
                  opacity: isHovered ? 0.95 : 0.8
                }}
                transition={{
                  delay: index * 0.1,
                  duration: 0.5,
                  type: "spring",
                  stiffness: 150,
                  damping: 15
                }}
                style={{
                  transformOrigin: `${centerX}px ${centerY}px`,
                  cursor: 'pointer'
                }}
                onMouseEnter={() => setHoveredSegment(metric.id)}
                onMouseLeave={() => setHoveredSegment(null)}
                className="transition-all duration-300"
              />
              
              {/* Percentage text on segment */}
              <motion.text
                x={centerX + (radius - 30) * Math.cos((metrics.slice(0, index).reduce((sum, m, i) => sum + segmentAngles[i], 0) + segmentAngles[index] / 2 - 90) * Math.PI / 180)}
                y={centerY + (radius - 30) * Math.sin((metrics.slice(0, index).reduce((sum, m, i) => sum + segmentAngles[i], 0) + segmentAngles[index] / 2 - 90) * Math.PI / 180)}
                textAnchor="middle"
                dominantBaseline="middle"
                fill="white"
                fontSize="16"
                fontWeight="bold"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: index * 0.1 + 0.3 }}
                style={{ pointerEvents: 'none' }}
              >
                {metric.value}%
              </motion.text>
            </g>
          );
        })}

        {/* Center circle with overall score */}
        <motion.circle
          cx={centerX}
          cy={centerY}
          r={innerRadius}
          fill="white"
          stroke="#e5e7eb"
          strokeWidth="2"
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.8, type: "spring", stiffness: 200 }}
        />
        
        <motion.text
          x={centerX}
          y={centerY - 10}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize="32"
          fontWeight="bold"
          className={getScoreColor(overallScore)}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1 }}
        >
          {Math.round(overallScore)}
        </motion.text>
        
        <motion.text
          x={centerX}
          y={centerY + 20}
          textAnchor="middle"
          dominantBaseline="middle"
          fontSize="14"
          fill="#6b7280"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 1.1 }}
        >
          Overall Score
        </motion.text>
      </svg>

      {/* Tooltip - Pops up on hover */}
      <AnimatePresence>
        {hoveredSegment && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 10 }}
            transition={{ 
              type: "spring",
              stiffness: 300,
              damping: 20
            }}
            className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-gray-900 text-white px-6 py-4 rounded-xl shadow-2xl z-50 pointer-events-none"
          >
            {(() => {
              const metric = metrics.find(m => m.id === hoveredSegment);
              if (!metric) return null;
              
              return (
                <div className="text-center min-w-[200px]">
                  <div className="flex items-center justify-center space-x-2 mb-2">
                    <div style={{ color: metric.color }}>
                      {metric.icon}
                    </div>
                    <span className="font-bold text-lg">{metric.title}</span>
                  </div>
                  <p className="text-sm text-gray-300 mb-2">{metric.description}</p>
                  <p className="text-3xl font-bold" style={{ color: metric.color }}>
                    {metric.value}%
                  </p>
                </div>
              );
            })()}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AnimatedQualityWheel;
