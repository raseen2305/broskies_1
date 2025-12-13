import React from 'react';
import { motion } from 'framer-motion';
import { 
  Sparkles, 
  Zap, 
  Star, 
  Heart, 
  Award,
  TrendingUp,
  ArrowRight,
  Download,
  Share2,
  Plus
} from 'lucide-react';
import AnimatedButton from '../components/AnimatedButton';
import AnimatedCard from '../components/AnimatedCard';
import AnimatedTooltip from '../components/AnimatedTooltip';
import FloatingActionButton from '../components/FloatingActionButton';

const AnimationShowcase: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h1 className="text-4xl md:text-5xl font-bold gradient-text mb-4">
            Animation Showcase
          </h1>
          <p className="text-xl text-gray-600">
            Explore our enhanced hover effects and animations
          </p>
        </motion.div>

        {/* Animated Buttons Section */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Animated Buttons</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            <AnimatedButton variant="primary" animationType="lift" icon={ArrowRight}>
              Lift Animation
            </AnimatedButton>
            <AnimatedButton variant="secondary" animationType="scale" icon={Zap}>
              Scale Animation
            </AnimatedButton>
            <AnimatedButton variant="outline" animationType="glow" icon={Sparkles}>
              Glow Animation
            </AnimatedButton>
            <AnimatedButton variant="success" animationType="shine" icon={Star}>
              Shine Animation
            </AnimatedButton>
            <AnimatedButton variant="danger" animationType="ripple" icon={Heart}>
              Ripple Animation
            </AnimatedButton>
            <AnimatedButton variant="ghost" loading icon={Download}>
              Loading State
            </AnimatedButton>
          </div>
        </section>

        {/* Animated Cards Section */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Animated Cards</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <AnimatedCard animationType="lift" delay={0}>
              <div className="p-6">
                <TrendingUp className="h-8 w-8 text-primary-500 mb-3" />
                <h3 className="text-lg font-semibold mb-2">Lift Effect</h3>
                <p className="text-gray-600">Smooth elevation on hover with shadow enhancement</p>
              </div>
            </AnimatedCard>

            <AnimatedCard animationType="tilt" delay={0.1}>
              <div className="p-6">
                <Zap className="h-8 w-8 text-secondary-500 mb-3" />
                <h3 className="text-lg font-semibold mb-2">Tilt Effect</h3>
                <p className="text-gray-600">3D perspective tilt animation on hover</p>
              </div>
            </AnimatedCard>

            <AnimatedCard animationType="glow" delay={0.2}>
              <div className="p-6">
                <Sparkles className="h-8 w-8 text-accent-500 mb-3" />
                <h3 className="text-lg font-semibold mb-2">Glow Effect</h3>
                <p className="text-gray-600">Glowing border and shadow animation</p>
              </div>
            </AnimatedCard>

            <AnimatedCard animationType="scale" delay={0.3}>
              <div className="p-6">
                <Star className="h-8 w-8 text-yellow-500 mb-3" />
                <h3 className="text-lg font-semibold mb-2">Scale Effect</h3>
                <p className="text-gray-600">Grows smoothly on hover interaction</p>
              </div>
            </AnimatedCard>

            <AnimatedCard animationType="border" delay={0.4}>
              <div className="p-6">
                <Award className="h-8 w-8 text-green-500 mb-3" />
                <h3 className="text-lg font-semibold mb-2">Border Effect</h3>
                <p className="text-gray-600">Animated border color and width change</p>
              </div>
            </AnimatedCard>

            <AnimatedCard animationType="lift" delay={0.5} onClick={() => alert('Card clicked!')}>
              <div className="p-6">
                <Heart className="h-8 w-8 text-red-500 mb-3" />
                <h3 className="text-lg font-semibold mb-2">Clickable Card</h3>
                <p className="text-gray-600">Interactive card with click handler</p>
              </div>
            </AnimatedCard>
          </div>
        </section>

        {/* CSS Hover Effects Section */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">CSS Hover Effects</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="card p-6 hover-lift">
              <h3 className="font-semibold mb-2">Hover Lift</h3>
              <p className="text-sm text-gray-600">Elevates with shadow</p>
            </div>

            <div className="card p-6 hover-glow">
              <h3 className="font-semibold mb-2">Hover Glow</h3>
              <p className="text-sm text-gray-600">Glowing shadow effect</p>
            </div>

            <div className="card p-6 hover-scale">
              <h3 className="font-semibold mb-2">Hover Scale</h3>
              <p className="text-sm text-gray-600">Scales up smoothly</p>
            </div>

            <div className="card p-6 hover-rotate">
              <h3 className="font-semibold mb-2">Hover Rotate</h3>
              <p className="text-sm text-gray-600">Subtle rotation tilt</p>
            </div>

            <div className="card p-6 hover-shine">
              <h3 className="font-semibold mb-2">Hover Shine</h3>
              <p className="text-sm text-gray-600">Light sweep animation</p>
            </div>

            <div className="card p-6 hover-border-glow">
              <h3 className="font-semibold mb-2">Border Glow</h3>
              <p className="text-sm text-gray-600">Pulsing border effect</p>
            </div>
          </div>
        </section>

        {/* Tooltips Section */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Animated Tooltips</h2>
          <div className="flex flex-wrap gap-8 justify-center p-12 bg-white rounded-xl shadow-lg">
            <AnimatedTooltip content="Top tooltip" position="top">
              <button className="btn-primary">Hover Top</button>
            </AnimatedTooltip>

            <AnimatedTooltip content="Bottom tooltip" position="bottom">
              <button className="btn-secondary">Hover Bottom</button>
            </AnimatedTooltip>

            <AnimatedTooltip content="Left tooltip" position="left">
              <button className="btn-outline">Hover Left</button>
            </AnimatedTooltip>

            <AnimatedTooltip content="Right tooltip" position="right">
              <button className="btn-ghost">Hover Right</button>
            </AnimatedTooltip>

            <AnimatedTooltip 
              content={
                <div className="flex items-center space-x-2">
                  <Star className="h-4 w-4" />
                  <span>Rich content tooltip</span>
                </div>
              } 
              position="top"
            >
              <button className="btn-success">Rich Tooltip</button>
            </AnimatedTooltip>
          </div>
        </section>

        {/* Micro-interactions Section */}
        <section className="mb-16">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Micro-interactions</h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            <motion.div
              className="card p-6 text-center cursor-pointer"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Sparkles className="h-8 w-8 mx-auto mb-2 text-primary-500" />
              <p className="text-sm font-medium">Tap Feedback</p>
            </motion.div>

            <div className="card p-6 text-center cursor-pointer bounce-on-hover">
              <TrendingUp className="h-8 w-8 mx-auto mb-2 text-green-500" />
              <p className="text-sm font-medium">Bounce</p>
            </div>

            <div className="card p-6 text-center cursor-pointer wiggle-on-hover">
              <Zap className="h-8 w-8 mx-auto mb-2 text-yellow-500" />
              <p className="text-sm font-medium">Wiggle</p>
            </div>

            <div className="card p-6 text-center cursor-pointer pulse-glow">
              <Star className="h-8 w-8 mx-auto mb-2 text-purple-500" />
              <p className="text-sm font-medium">Pulse Glow</p>
            </div>

            <div className="card p-6 text-center cursor-pointer slide-reveal">
              <Heart className="h-8 w-8 mx-auto mb-2 text-red-500" />
              <p className="text-sm font-medium">Slide Reveal</p>
            </div>

            <motion.div
              className="card p-6 text-center cursor-pointer"
              animate={{
                rotate: [0, 5, -5, 0],
                scale: [1, 1.05, 1]
              }}
              transition={{
                duration: 2,
                repeat: Infinity,
                repeatType: 'reverse'
              }}
            >
              <Award className="h-8 w-8 mx-auto mb-2 text-blue-500" />
              <p className="text-sm font-medium">Auto Animate</p>
            </motion.div>

            <div className="card p-6 text-center cursor-pointer gradient-animate">
              <Sparkles className="h-8 w-8 mx-auto mb-2 text-white" />
              <p className="text-sm font-medium text-white">Gradient</p>
            </div>

            <motion.div
              className="card p-6 text-center cursor-pointer"
              whileHover={{ rotateY: 180 }}
              style={{ transformStyle: 'preserve-3d' }}
            >
              <Star className="h-8 w-8 mx-auto mb-2 text-orange-500" />
              <p className="text-sm font-medium">Flip</p>
            </motion.div>
          </div>
        </section>

        {/* Floating Action Button */}
        <FloatingActionButton
          mainIcon={Plus}
          actions={[
            {
              icon: Share2,
              label: 'Share',
              onClick: () => alert('Share clicked!'),
              color: 'bg-blue-500'
            },
            {
              icon: Download,
              label: 'Download',
              onClick: () => alert('Download clicked!'),
              color: 'bg-green-500'
            },
            {
              icon: Heart,
              label: 'Favorite',
              onClick: () => alert('Favorite clicked!'),
              color: 'bg-red-500'
            }
          ]}
        />
      </div>
    </div>
  );
};

export default AnimationShowcase;
