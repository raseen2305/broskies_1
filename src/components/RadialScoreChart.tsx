import React, { useState } from "react";
<<<<<<< HEAD

interface RadialScoreChartProps {
  scores: {
    bestPractices?: number;
    complexity?: number;
    performance?: number;
    documentation?: number;
    testCoverage?: number;
    security?: number;
    maintainability?: number;
    readability?: number;
  };
  title?: string;
}

const RadialScoreChart: React.FC<RadialScoreChartProps> = ({
  scores,
  title = "Code Quality Analysis",
}) => {
  const [isExpanded, setIsExpanded] = useState(false);

  // Fixed segment data with predetermined lengths, base colors, and dynamic transparency
  const segments = [
    {
      title: "Best Practices",
      percentage: 45, // Fixed length
      score: scores.bestPractices || 75, // Actual score for transparency
      baseColor: "#10B981", // Green
    },
    {
      title: "Complexity",
      percentage: 40,
      score: scores.complexity || 60,
      baseColor: "#F59E0B", // Orange
    },
    {
      title: "Performance",
      percentage: 35,
      score: scores.performance || 85,
      baseColor: "#EF4444", // Red
    },
    {
      title: "Documentation",
      percentage: 30,
      score: scores.documentation || 50,
      baseColor: "#8B5CF6", // Purple
    },
    {
      title: "Test Coverage",
      percentage: 25,
      score: scores.testCoverage || 70,
      baseColor: "#06B6D4", // Cyan
    },
    {
      title: "Security",
      percentage: 20,
      score: scores.security || 90,
      baseColor: "#EC4899", // Pink
    },
    {
      title: "Maintainability",
      percentage: 15,
      score: scores.maintainability || 65,
      baseColor: "#84CC16", // Lime
    },
    {
      title: "Readability",
      percentage: 10,
      score: scores.readability || 80,
      baseColor: "#F97316", // Orange-red
    },
  ];

  // Calculate dynamic color with transparency based on score
  const getSegmentColor = (baseColor: string, score: number) => {
    const opacity = Math.max(0.3, Math.min(1, score / 100));
    const hex = baseColor.replace("#", "");
    const r = parseInt(hex.substr(0, 2), 16);
    const g = parseInt(hex.substr(2, 2), 16);
    const b = parseInt(hex.substr(4, 2), 16);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
  };

  const createSegmentPath = (index: number, expanded: boolean) => {
    const angle = index * 45 - 90;
    const startAngle = angle - 22.5;
    const endAngle = angle + 22.5;
    const innerRadius = expanded ? 120 : 80;
    const outerRadius = expanded ? 120 + segments[index].percentage * 2.2 : 150;

    const startRad = (startAngle * Math.PI) / 180;
    const endRad = (endAngle * Math.PI) / 180;

    const x1 = 500 + innerRadius * Math.cos(startRad);
    const y1 = 300 + innerRadius * Math.sin(startRad);
    const x2 = 500 + outerRadius * Math.cos(startRad);
    const y2 = 300 + outerRadius * Math.sin(startRad);
    const x3 = 500 + outerRadius * Math.cos(endRad);
    const y3 = 300 + outerRadius * Math.sin(endRad);
    const x4 = 500 + innerRadius * Math.cos(endRad);
    const y4 = 300 + innerRadius * Math.sin(endRad);

    const largeArcFlag = 0;

    return `M ${x1} ${y1}
            L ${x2} ${y2}
            A ${outerRadius} ${outerRadius} 0 ${largeArcFlag} 1 ${x3} ${y3}
            L ${x4} ${y4}
            A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${x1} ${y1}
            Z`;
  };

  const overallScore = Math.round(
    segments.reduce((sum, segment) => sum + segment.score, 0) / segments.length
  );

  return (
    <div className="w-full bg-white rounded-xl shadow-lg p-6">
      <div className="text-center mb-6">
        <h3 className="text-2xl font-bold text-gray-900 mb-2">{title}</h3>
        <p className="text-gray-600 text-sm">
          Interactive radial visualization • Hover to expand segments with fixed
          proportions
        </p>
      </div>

      <div className="relative w-full" style={{ paddingBottom: "60%" }}>
        <svg
          viewBox="0 0 1000 600"
          className="absolute inset-0 w-full h-full cursor-pointer"
          onMouseEnter={() => setIsExpanded(true)}
          onMouseLeave={() => setIsExpanded(false)}
        >
          {segments.map((segment, index) => {
            const angle = index * 45 - 90;
            const expanded = isExpanded;
            const innerRadius = expanded ? 120 : 80;
            const outerRadius = expanded ? 120 + segment.percentage * 2.2 : 150;
            const midRadius = (innerRadius + outerRadius) / 2;

            return (
              <g key={index}>
                <path
                  d={createSegmentPath(index, expanded)}
                  fill={getSegmentColor(segment.baseColor, segment.score)}
                  style={{
                    transition: "all 0.6s cubic-bezier(0.4, 0, 0.2, 1)",
                    transformOrigin: "500px 300px",
                  }}
                />

                {/* Text on segment */}
                <text
                  x={500 + midRadius * Math.cos((angle * Math.PI) / 180)}
                  y={300 + midRadius * Math.sin((angle * Math.PI) / 180)}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  className="fill-white font-bold pointer-events-none"
                  fontSize={expanded ? "14" : "12"}
                  transform={`rotate(${angle + 90}, ${
                    500 + midRadius * Math.cos((angle * Math.PI) / 180)
                  }, ${300 + midRadius * Math.sin((angle * Math.PI) / 180)})`}
                  style={{
                    transition: "all 0.6s cubic-bezier(0.4, 0, 0.2, 1)",
                    opacity: expanded ? 1 : 0.8,
                  }}
                >
                  {segment.title}
                </text>
                <text
                  x={500 + midRadius * Math.cos((angle * Math.PI) / 180)}
                  y={
                    300 +
                    midRadius * Math.sin((angle * Math.PI) / 180) +
                    (expanded ? 20 : 18)
                  }
                  textAnchor="middle"
                  dominantBaseline="middle"
                  className="fill-white font-bold pointer-events-none"
                  fontSize={expanded ? "24" : "20"}
                  transform={`rotate(${angle + 90}, ${
                    500 + midRadius * Math.cos((angle * Math.PI) / 180)
                  }, ${
                    300 +
                    midRadius * Math.sin((angle * Math.PI) / 180) +
                    (expanded ? 20 : 18)
                  })`}
                  style={{
                    transition: "all 0.6s cubic-bezier(0.4, 0, 0.2, 1)",
                  }}
                >
                  {segment.score}%
                </text>

                {/* Label outside - only show when expanded */}
                <g
                  style={{
                    transition: "opacity 0.4s ease-in-out",
                    opacity: expanded ? 1 : 0,
                  }}
                >
                  <line
                    x1={500 + outerRadius * Math.cos((angle * Math.PI) / 180)}
                    y1={300 + outerRadius * Math.sin((angle * Math.PI) / 180)}
                    x2={
                      500 +
                      (outerRadius + 40) * Math.cos((angle * Math.PI) / 180)
                    }
                    y2={
                      300 +
                      (outerRadius + 40) * Math.sin((angle * Math.PI) / 180)
                    }
                    stroke="#666"
                    strokeWidth="1"
                    className="pointer-events-none"
                  />
                  <circle
                    cx={
                      500 +
                      (outerRadius + 40) * Math.cos((angle * Math.PI) / 180)
                    }
                    cy={
                      300 +
                      (outerRadius + 40) * Math.sin((angle * Math.PI) / 180)
                    }
                    r="3"
                    fill="#666"
                    className="pointer-events-none"
                  />
                  <text
                    x={
                      500 +
                      (outerRadius + 55) * Math.cos((angle * Math.PI) / 180)
                    }
                    y={
                      300 +
                      (outerRadius + 55) * Math.sin((angle * Math.PI) / 180)
                    }
                    textAnchor={angle > -90 && angle < 90 ? "start" : "end"}
                    dominantBaseline="middle"
                    className="fill-gray-700 font-bold pointer-events-none"
                    fontSize="16"
                  >
                    {segment.title}
                  </text>
                  <text
                    x={
                      500 +
                      (outerRadius + 55) * Math.cos((angle * Math.PI) / 180)
                    }
                    y={
                      300 +
                      (outerRadius + 55) * Math.sin((angle * Math.PI) / 180) +
                      15
                    }
                    textAnchor={angle > -90 && angle < 90 ? "start" : "end"}
                    dominantBaseline="middle"
                    className="fill-gray-600 pointer-events-none"
                    fontSize="12"
                  >
                    Score: {segment.score}% • Fixed Length: {segment.percentage}
                    %
                  </text>
                  <text
                    x={
                      500 +
                      (outerRadius + 55) * Math.cos((angle * Math.PI) / 180)
                    }
                    y={
                      300 +
                      (outerRadius + 55) * Math.sin((angle * Math.PI) / 180) +
                      28
                    }
                    textAnchor={angle > -90 && angle < 90 ? "start" : "end"}
                    dominantBaseline="middle"
                    className="fill-gray-600 pointer-events-none"
                    fontSize="12"
                  >
                    This visualization is 100% interactive.
                  </text>
                  <text
                    x={
                      500 +
                      (outerRadius + 55) * Math.cos((angle * Math.PI) / 180)
                    }
                    y={
                      300 +
                      (outerRadius + 55) * Math.sin((angle * Math.PI) / 180) +
                      41
                    }
                    textAnchor={angle > -90 && angle < 90 ? "start" : "end"}
                    dominantBaseline="middle"
                    className="fill-gray-600 pointer-events-none"
                    fontSize="12"
                  >
                    Adapt it to your needs.
                  </text>
                </g>
              </g>
=======
import { motion, AnimatePresence } from "framer-motion";

interface ScoreSegment {
  label: string;
  value: number;
  color: string;
  icon?: React.ReactNode;
}

interface RadialScoreChartProps {
  segments: ScoreSegment[];
  overallScore: number;
  title?: string;
  subtitle?: string;
}

export default function RadialScoreChart({
  segments,
  overallScore,
  title = "Overall Score",
  subtitle
}: RadialScoreChartProps) {
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  // Layout parameters
  const radius = 150;
  const expandOffset = 15;
  const center = 200;
  const strokeWidth = 50;

  // Calculate total for percentages
  const total = 100; // Assuming values are already percentages

  const getArcPath = (startAngle: number, endAngle: number, offset: number = 0) => {
    const rad = Math.PI / 180;
    const innerRadius = radius - strokeWidth / 2 + offset;
    const outerRadius = radius + strokeWidth / 2 + offset;

    const x1 = center + outerRadius * Math.cos(startAngle * rad);
    const y1 = center + outerRadius * Math.sin(startAngle * rad);
    const x2 = center + outerRadius * Math.cos(endAngle * rad);
    const y2 = center + outerRadius * Math.sin(endAngle * rad);

    const x3 = center + innerRadius * Math.cos(endAngle * rad);
    const y3 = center + innerRadius * Math.sin(endAngle * rad);
    const x4 = center + innerRadius * Math.cos(startAngle * rad);
    const y4 = center + innerRadius * Math.sin(startAngle * rad);

    const largeArc = endAngle - startAngle > 180 ? 1 : 0;

    return `
      M ${x1} ${y1}
      A ${outerRadius} ${outerRadius} 0 ${largeArc} 1 ${x2} ${y2}
      L ${x3} ${y3}
      A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${x4} ${y4}
      Z
    `;
  };

  let cumulativeAngle = -90;

  const handleMouseMove = (e: React.MouseEvent) => {
    setMousePosition({ x: e.clientX, y: e.clientY });
  };

  return (
    <div className="w-full flex flex-col items-center justify-center p-10">
      {/* Title */}
      {title && (
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-gray-800">{title}</h2>
          {subtitle && <p className="text-sm text-gray-500 mt-1">{subtitle}</p>}
        </div>
      )}

      {/* SVG Chart */}
      <div className="relative" onMouseMove={handleMouseMove}>
        <svg width="400" height="400" className="overflow-visible">
          {/* Segments */}
          {segments.map((seg, idx) => {
            const angle = (seg.value / total) * 360;
            const startAngle = cumulativeAngle;
            const endAngle = cumulativeAngle + angle;
            cumulativeAngle += angle;

            const isHovered = hoveredIndex === idx;

            return (
              <motion.path
                key={idx}
                d={getArcPath(startAngle, endAngle, isHovered ? expandOffset : 0)}
                fill={seg.color || "#888"}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{
                  opacity: 1,
                  scale: 1,
                  filter: isHovered ? "brightness(1.1)" : "brightness(1)"
                }}
                transition={{
                  type: "spring",
                  stiffness: 200,
                  damping: 15
                }}
                onMouseEnter={() => setHoveredIndex(idx)}
                onMouseLeave={() => setHoveredIndex(null)}
                style={{
                  cursor: "pointer",
                  transformOrigin: `${center}px ${center}px`
                }}
              />
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
            );
          })}

          {/* Center circle */}
<<<<<<< HEAD
          <circle
            cx="500"
            cy="300"
            r={isExpanded ? "120" : "80"}
            fill="white"
            stroke="#e5e7eb"
            strokeWidth="2"
            style={{
              transition: "all 0.6s cubic-bezier(0.4, 0, 0.2, 1)",
            }}
            className="pointer-events-none"
          />
          <text
            x="500"
            y="285"
            textAnchor="middle"
            dominantBaseline="middle"
            className="fill-gray-800 font-bold pointer-events-none"
            fontSize={isExpanded ? "32" : "28"}
            style={{
              transition: "all 0.6s cubic-bezier(0.4, 0, 0.2, 1)",
            }}
=======
          <motion.circle
            cx={center}
            cy={center}
            r={radius - strokeWidth / 2 - 10}
            fill="#ffffff"
            stroke="#e5e7eb"
            strokeWidth="2"
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: "spring", stiffness: 150, delay: 0.2 }}
          />

          {/* Center text - Overall Score */}
          <text
            x={center}
            y={center - 10}
            textAnchor="middle"
            className="text-5xl font-bold"
            fill="#1f2937"
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
          >
            {overallScore}
          </text>
          <text
<<<<<<< HEAD
            x="500"
            y="315"
            textAnchor="middle"
            dominantBaseline="middle"
            className="fill-gray-600 pointer-events-none"
            fontSize={isExpanded ? "16" : "14"}
            style={{
              transition: "all 0.6s cubic-bezier(0.4, 0, 0.2, 1)",
            }}
=======
            x={center}
            y={center + 20}
            textAnchor="middle"
            className="text-sm"
            fill="#6b7280"
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
          >
            Overall Score
          </text>
        </svg>
<<<<<<< HEAD
      </div>

      <p className="text-center text-gray-600 mt-6">
        Hover over the diagram to see segments expand to their fixed proportions
      </p>

      {/* Legend showing fixed lengths and actual scores */}
      {isExpanded && (
        <div className="mt-8 p-4 bg-gray-50 rounded-lg transition-all duration-700 ease-out">
          <h4 className="text-lg font-semibold text-gray-900 mb-4 text-center">
            Segment Details
          </h4>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
            {segments.map((segment, index) => (
              <div
                key={index}
                className="text-center p-3 bg-white rounded-lg shadow-sm border-l-4"
                style={{ borderLeftColor: segment.baseColor }}
              >
                <div
                  className="w-4 h-4 rounded-full mx-auto mb-2"
                  style={{
                    backgroundColor: getSegmentColor(
                      segment.baseColor,
                      segment.score
                    ),
                  }}
                />
                <div className="font-medium text-gray-900 text-xs mb-1">
                  {segment.title}
                </div>
                <div
                  className="text-lg font-bold mb-1"
                  style={{ color: segment.baseColor }}
                >
                  {segment.score}%
                </div>
                <div className="text-xs text-gray-500">
                  Fixed: {segment.percentage}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default RadialScoreChart;
=======

        {/* Tooltip */}
        <AnimatePresence>
          {hoveredIndex !== null && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.8, y: 10 }}
              transition={{ duration: 0.15 }}
              className="fixed pointer-events-none z-50"
              style={{
                left: mousePosition.x + 15,
                top: mousePosition.y - 10
              }}
            >
              <div className="bg-gray-900 text-white px-4 py-3 rounded-lg shadow-xl">
                <div className="flex items-center gap-2 mb-1">
                  {segments[hoveredIndex].icon && (
                    <span className="text-lg">{segments[hoveredIndex].icon}</span>
                  )}
                  <p className="font-semibold text-sm">
                    {segments[hoveredIndex].label}
                  </p>
                </div>
                <p className="text-2xl font-bold">
                  {segments[hoveredIndex].value}%
                </p>
              </div>
              {/* Tooltip arrow */}
              <div
                className="absolute w-2 h-2 bg-gray-900 transform rotate-45"
                style={{ left: "8px", top: "50%", marginTop: "-4px" }}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Legend (optional - can be removed if not needed) */}
      <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl">
        {segments.map((seg, idx) => (
          <motion.div
            key={idx}
            className="flex items-center gap-2 cursor-pointer"
            onMouseEnter={() => setHoveredIndex(idx)}
            onMouseLeave={() => setHoveredIndex(null)}
            whileHover={{ scale: 1.05 }}
          >
            <div
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: seg.color }}
            />
            <span className="text-xs text-gray-600">{seg.label}</span>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
>>>>>>> d5e7869ebe813aaf39e98e4cc56498e93f572085
