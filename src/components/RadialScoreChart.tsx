import React, { useState } from "react";

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
          Interactive radial visualization â€¢ Hover to expand segments with fixed
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
                    Score: {segment.score}% â€¢ Fixed Length: {segment.percentage}
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
            );
          })}

          {/* Center circle */}
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
          >
            {overallScore}
          </text>
          <text
            x="500"
            y="315"
            textAnchor="middle"
            dominantBaseline="middle"
            className="fill-gray-600 pointer-events-none"
            fontSize={isExpanded ? "16" : "14"}
            style={{
              transition: "all 0.6s cubic-bezier(0.4, 0, 0.2, 1)",
            }}
          >
            Overall Score
          </text>
        </svg>
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
