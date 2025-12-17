import React from "react";
import RadialScoreChart from "./RadialScoreChart";
import {
  BookOpen,
  Code,
  Zap,
  FileText,
  TestTube,
  Shield,
  Wrench,
  Lock
} from "lucide-react";

interface CodeQualityScoreProps {
  scores: {
    readability?: number;
    maintainability?: number;
    security?: number;
    testCoverage?: number;
    documentation?: number;
    performance?: number;
    complexity?: number;
    bestPractices?: number;
  };
  overallScore: number;
  repositoryCount?: number;
  analyzedDate?: string;
}

export default function CodeQualityScore({
  scores,
  overallScore,
  repositoryCount = 5,
  analyzedDate
}: CodeQualityScoreProps) {
  // Define segments with colors matching the image
  const segments = [
    {
      label: "Readability",
      value: scores.readability || 75,
      color: "#10b981", // green
      icon: <BookOpen size={16} />
    },
    {
      label: "Maintainability",
      value: scores.maintainability || 70,
      color: "#3b82f6", // blue
      icon: <Wrench size={16} />
    },
    {
      label: "Security",
      value: scores.security || 85,
      color: "#ef4444", // red
      icon: <Shield size={16} />
    },
    {
      label: "Test Coverage",
      value: scores.testCoverage || 60,
      color: "#f59e0b", // orange
      icon: <TestTube size={16} />
    },
    {
      label: "Documentation",
      value: scores.documentation || 65,
      color: "#8b5cf6", // purple
      icon: <FileText size={16} />
    },
    {
      label: "Performance",
      value: scores.performance || 75,
      color: "#ec4899", // pink
      icon: <Zap size={16} />
    },
    {
      label: "Complexity",
      value: scores.complexity || 70,
      color: "#14b8a6", // teal
      icon: <Code size={16} />
    },
    {
      label: "Best Practices",
      value: scores.bestPractices || 80,
      color: "#a78bfa", // light purple
      icon: <Lock size={16} />
    }
  ];

  const subtitle = `Based on ${repositoryCount} evaluated repositories${
    analyzedDate ? ` • Analyzed ${analyzedDate}` : ""
  }`;

  return (
    <div className="w-full bg-gradient-to-br from-gray-50 to-gray-100 rounded-2xl shadow-lg">
      <RadialScoreChart
        segments={segments}
        overallScore={overallScore}
        title="Your Code Quality Score"
        subtitle={subtitle}
      />
    </div>
  );
}
