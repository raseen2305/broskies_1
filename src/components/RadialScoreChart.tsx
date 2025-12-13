import React, { useState } from "react";
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
            );
          })}

          {/* Center circle */}
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
          >
            {overallScore}
          </text>
          <text
            x={center}
            y={center + 20}
            textAnchor="middle"
            className="text-sm"
            fill="#6b7280"
          >
            Overall Score
          </text>
        </svg>

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
