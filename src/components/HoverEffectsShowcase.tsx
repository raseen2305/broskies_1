import React from 'react';
import { motion } from 'framer-motion';
import { 
  Sparkles, 
  Zap, 
  Star, 
  Heart, 
  Award,
  TrendingUp
} from 'lucide-react';

const HoverEffectsShowcase: React.FC = () => {
  const effects = [
    {
      title: 'Lift Effect',
      description: 'Smooth elevation on hover',
      className: 'hover-lift',
      icon: TrendingUp
    },
    {
      title: 'Glow Effect',
      description: 'Glowing shadow animation',
      className: 'hover-glow',
      icon: Sparkles
    },
    {
      title: 'Scale Effect',
      description: 'Grows on interaction',
      className: 'hover-scale',
      icon: Zap
    },
    {
      title: 'Rotate Effect',
      description: 'Subtle rotation tilt',
      className: 'hover-rotate',
      icon: Star
    },
    {
      title: 'Shine Effect',
      description: 'Light sweep animation',
      className: 'hover-shine',
      icon: Heart
    },
    {
      title: 'Border Glow',
      description: 'Pulsing border effect',
      className: 'hover-border-glow',
      icon: Award
    }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 p-6">
      {effects.map((effect, index) => (
        <motion.div
          key={index}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: index * 0.1 }}
          className={`card p-6 ${effect.className}`}
        >
          <div className="flex items-center space-x-3 mb-3">
            <div className="w-10 h-10 bg-gradient-to-br from-primary-500 to-secondary-500 rounded-lg flex items-center justify-center">
              <effect.icon className="h-5 w-5 text-white" />
            </div>
            <h3 className="font-semibold text-gray-900">{effect.title}</h3>
          </div>
          <p className="text-sm text-gray-600">{effect.description}</p>
        </motion.div>
      ))}
    </div>
  );
};

export default HoverEffectsShowcase;
