import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  Shield,
  BookOpen,
  Wrench,
  TestTube,
  FileText,
  Lock,
  Zap,
  Code,
} from "lucide-react";

interface QualityMetric {
  id: string;
  title: string;
  value: number;
  color: string;
  icon: React.ReactNode;
  description: string;
  fixedLength: number;
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
  flagshipCount?: number;
  significantCount?: number;
  supportingCount?: number;
}

const AnimatedQualityWheel: React.FC<AnimatedQualityWheelProps> = ({
  qualityMetrics = {},
  overallScore = 0,
  flagshipCount = 0,
  significantCount = 0,
  supportingCount = 0,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [hoveredSegment, setHoveredSegment] = useState<number | null>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  // Define the 8 quality metrics with FIXED lengths and dynamic transparency
  const metrics: QualityMetric[] = [
    {
      id: "best_practices",
      title: "Best Practices",
      value: qualityMetrics.best_practices || 75,
      fixedLength: 55, // Longest segment (50 + 5)
      color: "#10b981", // green
      icon: <Lock className="w-5 h-5" />,
      description: "Adherence to coding standards",
    },
    {
      id: "complexity",
      title: "Complexity",
      value: qualityMetrics.complexity || 60,
      fixedLength: 50, // (45 + 5)
      color: "#F59E0B", // orange
      icon: <Code className="w-5 h-5" />,
      description: "Code complexity management",
    },
    {
      id: "performance",
      title: "Performance",
      value: qualityMetrics.performance || 85,
      fixedLength: 45, // (40 + 5)
      color: "#EF4444", // red
      icon: <Zap className="w-5 h-5" />,
      description: "Code efficiency and speed",
    },
    {
      id: "documentation",
      title: "Documentation",
      value: qualityMetrics.documentation || 50,
      fixedLength: 40, // (35 + 5)
      color: "#8B5CF6", // purple
      icon: <FileText className="w-5 h-5" />,
      description: "Quality and completeness of docs",
    },
    {
      id: "test_coverage",
      title: "Test Coverage",
      value: qualityMetrics.test_coverage || 70,
      fixedLength: 35, // (30 + 5)
      color: "#06B6D4", // cyan
      icon: <TestTube className="w-5 h-5" />,
      description: "Extent of automated testing",
    },
    {
      id: "security",
      title: "Security",
      value: qualityMetrics.security || 90,
      fixedLength: 30, // (25 + 5)
      color: "#EC4899", // pink
      icon: <Shield className="w-5 h-5" />,
      description: "Protection against vulnerabilities",
    },
    {
      id: "maintainability",
      title: "Maintainability",
      value: qualityMetrics.maintainability || 65,
      fixedLength: 25, // (20 + 5)
      color: "#84CC16", // lime
      icon: <Wrench className="w-5 h-5" />,
      description: "Ease of making changes and updates",
    },
    {
      id: "readability",
      title: "Readability",
      value: qualityMetrics.readability || 80,
      fixedLength: 20, // Shortest segment (15 + 5)
      color: "#F97316", // orange-red
      icon: <BookOpen className="w-5 h-5" />,
      description: "Code clarity and ease of understanding",
    },
  ];

  // Move circle 20% to the left to make room for right-side footer
  const centerX = 180; // Moved from 250 to 180 (20% left shift)
  const centerY = 250;
  const baseRadius = 120;

  // Calculate dynamic color with transparency based on score
  const getSegmentColor = (baseColor: string, score: number) => {
    const opacity = Math.max(0.3, Math.min(1, score / 100));
    const hex = baseColor.replace("#", "");
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
  };

  // Function to create SVG path for each segment with FIXED lengths
  const createSegmentPath = (index: number) => {
    // Calculate start angle (45 degrees per segment)
    const startAngleDeg = index * 45 - 90;
    const endAngleDeg = startAngleDeg + 45;

    const startAngle = startAngleDeg * (Math.PI / 180);
    const endAngle = endAngleDeg * (Math.PI / 180);

    // 25% thickness: inner radius is 25% smaller than base radius
    const innerRadius = isExpanded ? baseRadius * 0.75 : baseRadius * 0.8;
    // Use FIXED lengths when expanded, same radius when collapsed
    const outerRadius = isExpanded
      ? baseRadius + metrics[index].fixedLength * 2.5
      : baseRadius + 30;

    const x1 = centerX + innerRadius * Math.cos(startAngle);
    const y1 = centerY + innerRadius * Math.sin(startAngle);
    const x2 = centerX + outerRadius * Math.cos(startAngle);
    const y2 = centerY + outerRadius * Math.sin(startAngle);
    const x3 = centerX + outerRadius * Math.cos(endAngle);
    const y3 = centerY + outerRadius * Math.sin(endAngle);
    const x4 = centerX + innerRadius * Math.cos(endAngle);
    const y4 = centerY + innerRadius * Math.sin(endAngle);

    const largeArcFlag = 0; // 45 degrees is never > 180

    return `M ${x1} ${y1} L ${x2} ${y2} A ${outerRadius} ${outerRadius} 0 ${largeArcFlag} 1 ${x3} ${y3} L ${x4} ${y4} A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${x1} ${y1} Z`;
  };

  return (
    <div className="relative w-full h-full flex items-center min-h-[700px]">
      <div
        className="cursor-pointer relative flex-1"
        onMouseEnter={() => setIsExpanded(true)}
        onMouseLeave={() => {
          setIsExpanded(false);
          setHoveredSegment(null);
        }}
        onMouseMove={(e) => {
          const rect = e.currentTarget.getBoundingClientRect();
          setMousePosition({
            x: e.clientX - rect.left,
            y: e.clientY - rect.top,
          });
        }}
      >
        <svg
          width="700"
          height="700"
          viewBox="-150 -250 800 800"
          className="overflow-visible"
        >
          {/* Segments */}
          {metrics.map((metric, index) => {
            const angleDeg = index * 45 - 90;
            const angle = angleDeg * (Math.PI / 180);
            const outerRadius = isExpanded
              ? baseRadius + metric.fixedLength * 2.5
              : baseRadius + 20;

            return (
              <g key={metric.id}>
                <motion.path
                  d={createSegmentPath(index)}
                  fill={getSegmentColor(metric.color, metric.value)}
                  initial={{ scale: 0, opacity: 0 }}
                  animate={{
                    scale: 1,
                    opacity: 1,
                  }}
                  transition={{
                    delay: index * 0.1,
                    duration: 0.6,
                    type: "spring",
                    stiffness: 150,
                    damping: 15,
                  }}
                  style={{
                    transformOrigin: `${centerX}px ${centerY}px`,
                    transition: "all 0.6s cubic-bezier(0.4, 0, 0.2, 1)",
                    cursor: "pointer",
                  }}
                  onMouseEnter={() => setHoveredSegment(index)}
                  onMouseLeave={() => setHoveredSegment(null)}
                />

                {/* Title text inside segments - only when expanded */}
                {isExpanded &&
                  (() => {
                    const midRadius = (baseRadius + outerRadius) / 2;
                    const textAngle = angleDeg + 22.5; // Center of segment
                    const textAngleRad = textAngle * (Math.PI / 180);

                    return (
                      <motion.text
                        x={centerX + midRadius * Math.cos(textAngleRad)}
                        y={centerY + midRadius * Math.sin(textAngleRad)}
                        textAnchor="middle"
                        dominantBaseline="middle"
                        fill="white"
                        fontSize="12"
                        fontWeight="bold"
                        transform={`rotate(${textAngle}, ${
                          centerX + midRadius * Math.cos(textAngleRad)
                        }, ${centerY + midRadius * Math.sin(textAngleRad)})`}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: index * 0.1 + 0.3 }}
                        style={{
                          pointerEvents: "none",
                          transition: "all 0.6s cubic-bezier(0.4, 0, 0.2, 1)",
                        }}
                      >
                        {metric.title}
                      </motion.text>
                    );
                  })()}

                {/* External labels - like the reference image */}
                {isExpanded && (
                  <g
                    style={{
                      transition: "opacity 0.4s ease-in-out",
                      opacity: isExpanded ? 1 : 0,
                    }}
                  >
                    {(() => {
                      // Calculate label positioning with better spacing
                      const labelDistance = outerRadius + 100; // Increased distance for better spacing
                      const labelX = centerX + labelDistance * Math.cos(angle);
                      const labelY = centerY + labelDistance * Math.sin(angle);

                      // Determine text anchor based on position
                      const isRightSide = angleDeg > -90 && angleDeg < 90;
                      const textAnchor = isRightSide ? "start" : "end";
                      const bulletX = isRightSide ? labelX - 15 : labelX + 15; // Increased bullet spacing

                      return (
                        <>
                          {/* Connection line */}
                          <line
                            x1={centerX + outerRadius * Math.cos(angle)}
                            y1={centerY + outerRadius * Math.sin(angle)}
                            x2={labelX}
                            y2={labelY}
                            stroke="#999"
                            strokeWidth="1"
                            className="pointer-events-none"
                          />

                          {/* Bullet point */}
                          <circle
                            cx={bulletX}
                            cy={labelY}
                            r="4"
                            fill="#666"
                            className="pointer-events-none"
                          />

                          {/* Segment Name with better spacing */}
                          <text
                            x={labelX}
                            y={labelY}
                            textAnchor={textAnchor}
                            dominantBaseline="middle"
                            className="fill-gray-800 font-bold pointer-events-none"
                            fontSize="15"
                            style={{
                              letterSpacing: "0.5px", // Better letter spacing
                              fontFamily:
                                "system-ui, -apple-system, sans-serif",
                            }}
                          >
                            {metric.title}
                          </text>
                        </>
                      );
                    })()}
                  </g>
                )}
              </g>
            );
          })}

          {/* Center circle with overall score */}
          <motion.circle
            cx={centerX}
            cy={centerY}
            r={isExpanded ? baseRadius * 0.75 : baseRadius * 0.8}
            fill="white"
            stroke="#e5e7eb"
            strokeWidth="2"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: 0.8, type: "spring", stiffness: 200 }}
            style={{
              transition: "all 0.6s cubic-bezier(0.4, 0, 0.2, 1)",
            }}
          />

          <motion.text
            x={centerX}
            y={centerY - 10}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize={isExpanded ? "32" : "28"}
            fontWeight="bold"
            fill="#333"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1 }}
            style={{
              transition: "all 0.6s cubic-bezier(0.4, 0, 0.2, 1)",
            }}
          >
            {Math.round(overallScore)}
          </motion.text>

          <motion.text
            x={centerX}
            y={centerY + 15}
            textAnchor="middle"
            dominantBaseline="middle"
            fontSize={isExpanded ? "14" : "12"}
            fill="#666"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.1 }}
            style={{
              transition: "all 0.6s cubic-bezier(0.4, 0, 0.2, 1)",
            }}
          >
            Overall Score
          </motion.text>
        </svg>

        {/* Repository Distribution Footer - Right Side */}
        {(flagshipCount > 0 || significantCount > 0 || supportingCount > 0) && (
          <div className="absolute right-0 top-1/2 transform -translate-y-1/2 space-y-4">
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5, duration: 0.6 }}
              className="bg-white p-4 rounded-lg shadow-lg border"
              style={{ minWidth: "220px" }}
            >
              <h4 className="text-sm font-semibold text-gray-900 mb-4 border-b pb-2">
                Repository Distribution
              </h4>
              <div className="space-y-3">
                {flagshipCount > 0 && (
                  <motion.div
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.7, duration: 0.4 }}
                    className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg border border-yellow-200"
                  >
                    <div className="flex items-center space-x-3">
                      <span className="text-xl">🏆</span>
                      <div>
                        <div className="text-sm font-medium text-yellow-700">
                          Flagship
                        </div>
                        <div className="text-xs text-yellow-600">
                          Top-tier repositories
                        </div>
                      </div>
                    </div>
                    <div className="text-2xl font-bold text-yellow-700">
                      {flagshipCount}
                    </div>
                  </motion.div>
                )}
                {significantCount > 0 && (
                  <motion.div
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.8, duration: 0.4 }}
                    className="flex items-center justify-between p-3 bg-blue-50 rounded-lg border border-blue-200"
                  >
                    <div className="flex items-center space-x-3">
                      <span className="text-xl">⭐</span>
                      <div>
                        <div className="text-sm font-medium text-blue-700">
                          Significant
                        </div>
                        <div className="text-xs text-blue-600">
                          Important projects
                        </div>
                      </div>
                    </div>
                    <div className="text-2xl font-bold text-blue-700">
                      {significantCount}
                    </div>
                  </motion.div>
                )}
                {supportingCount > 0 && (
                  <motion.div
                    initial={{ opacity: 0, x: 10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.9, duration: 0.4 }}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200"
                  >
                    <div className="flex items-center space-x-3">
                      <span className="text-xl">📋</span>
                      <div>
                        <div className="text-sm font-medium text-gray-700">
                          Supporting
                        </div>
                        <div className="text-xs text-gray-600">
                          Additional projects
                        </div>
                      </div>
                    </div>
                    <div className="text-2xl font-bold text-gray-700">
                      {supportingCount}
                    </div>
                  </motion.div>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </div>

      {/* Hover instruction */}
      {!isExpanded && (
        <div className="absolute top-4 left-1/2 transform -translate-x-1/2 text-xs text-gray-500 text-center bg-white px-3 py-1 rounded-full shadow-sm">
          Hover to expand segments with fixed proportions
        </div>
      )}

      {/* Mouse-following tooltip for individual segments */}
      {hoveredSegment !== null && (
        <div
          className="absolute pointer-events-none z-20 bg-white p-3 rounded-lg shadow-lg border max-w-xs"
          style={{
            left: mousePosition.x + 15,
            top: mousePosition.y - 10,
            transform: mousePosition.x > 400 ? "translateX(-100%)" : "none",
          }}
        >
          <div className="flex items-center space-x-2 mb-2">
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: metrics[hoveredSegment].color }}
            />
            <h4 className="font-semibold text-gray-900 text-sm">
              {metrics[hoveredSegment].title}
            </h4>
          </div>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between">
              <span className="text-gray-600">Score:</span>
              <span
                className="font-medium"
                style={{ color: metrics[hoveredSegment].color }}
              >
                {metrics[hoveredSegment].value}%
              </span>
            </div>
            <div className="text-gray-500 text-xs mt-2 pt-2 border-t">
              {metrics[hoveredSegment].description}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AnimatedQualityWheel;
