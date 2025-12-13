import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronLeft, ChevronRight, Quote, Star } from 'lucide-react';
import { Testimonial } from '../types';

const testimonials: Testimonial[] = [
  {
    id: '1',
    name: 'Sarah Chen',
    role: 'Senior Developer',
    company: 'TechCorp',
    content: 'BroskiesHub completely transformed how I showcase my coding skills. The ACID scoring system gave me insights I never knew I needed, and it helped me land my dream job!',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Sarah&backgroundColor=b6e3f4',
    rating: 5
  },
  {
    id: '2',
    name: 'Marcus Rodriguez',
    role: 'Tech Lead',
    company: 'StartupXYZ',
    content: 'As a hiring manager, BroskiesHub saves me hours of manual code review. The comprehensive analytics help me identify top talent quickly and make confident hiring decisions.',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Marcus&backgroundColor=c084fc',
    rating: 5
  },
  {
    id: '3',
    name: 'Emily Johnson',
    role: 'Full Stack Developer',
    company: 'DevStudio',
    content: 'The personalized roadmap feature is incredible! It showed me exactly which skills to focus on next. My code quality improved significantly after following the recommendations.',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Emily&backgroundColor=fbbf24',
    rating: 5
  },
  {
    id: '4',
    name: 'David Kim',
    role: 'HR Director',
    company: 'InnovateLabs',
    content: 'BroskiesHub revolutionized our hiring process. We reduced time-to-hire by 75% and improved candidate quality significantly. The ROI has been phenomenal.',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=David&backgroundColor=34d399',
    rating: 5
  },
  {
    id: '5',
    name: 'Lisa Wang',
    role: 'Frontend Developer',
    company: 'DesignTech',
    content: 'I love how BroskiesHub breaks down my coding patterns and suggests improvements. It\'s like having a senior developer mentor available 24/7. Highly recommended!',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Lisa&backgroundColor=f472b6',
    rating: 5
  },
  {
    id: '6',
    name: 'Alex Thompson',
    role: 'CTO',
    company: 'ScaleUp Inc',
    content: 'The security assessment feature caught vulnerabilities we missed in our code reviews. BroskiesHub has become an essential part of our development workflow.',
    avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Alex&backgroundColor=a78bfa',
    rating: 5
  }
];

const TestimonialsCarousel: React.FC = () => {
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);

  useEffect(() => {
    if (!isAutoPlaying) return;

    const interval = setInterval(() => {
      setCurrentIndex((prevIndex) => 
        prevIndex === testimonials.length - 1 ? 0 : prevIndex + 1
      );
    }, 5000);

    return () => clearInterval(interval);
  }, [isAutoPlaying]);

  const goToPrevious = () => {
    setCurrentIndex(currentIndex === 0 ? testimonials.length - 1 : currentIndex - 1);
    setIsAutoPlaying(false);
  };

  const goToNext = () => {
    setCurrentIndex(currentIndex === testimonials.length - 1 ? 0 : currentIndex + 1);
    setIsAutoPlaying(false);
  };

  const goToSlide = (index: number) => {
    setCurrentIndex(index);
    setIsAutoPlaying(false);
  };

  const renderStars = (rating: number) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        className={`h-4 w-4 ${
          i < rating ? 'text-yellow-400 fill-current' : 'text-gray-300'
        }`}
      />
    ));
  };

  return (
    <section className="py-20 bg-gradient-to-br from-gray-50 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Loved by Developers & HR Teams
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Join thousands of satisfied users who have transformed their hiring process
            </p>
          </motion.div>
        </div>

        <div className="relative max-w-4xl mx-auto">
          {/* Main Testimonial */}
          <div className="relative overflow-hidden">
            <AnimatePresence mode="wait">
              <motion.div
                key={currentIndex}
                initial={{ opacity: 0, x: 100 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -100 }}
                transition={{ duration: 0.5 }}
                className="bg-white rounded-2xl shadow-xl p-8 md:p-12 relative"
              >
                <Quote className="absolute top-6 left-6 h-8 w-8 text-primary-500 opacity-20" />
                
                <div className="text-center mb-8">
                  <div className="flex justify-center mb-4">
                    {renderStars(testimonials[currentIndex].rating)}
                  </div>
                  <blockquote className="text-lg md:text-xl text-gray-700 leading-relaxed mb-6">
                    "{testimonials[currentIndex].content}"
                  </blockquote>
                </div>

                <div className="flex items-center justify-center space-x-4">
                  <img
                    src={testimonials[currentIndex].avatar}
                    alt={testimonials[currentIndex].name}
                    className="w-16 h-16 rounded-full object-cover border-4 border-primary-100"
                  />
                  <div className="text-left">
                    <div className="font-semibold text-gray-900 text-lg">
                      {testimonials[currentIndex].name}
                    </div>
                    <div className="text-gray-600">
                      {testimonials[currentIndex].role}
                    </div>
                    <div className="text-primary-500 font-medium">
                      {testimonials[currentIndex].company}
                    </div>
                  </div>
                </div>
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Navigation Arrows */}
          <button
            onClick={goToPrevious}
            className="absolute left-4 top-1/2 transform -translate-y-1/2 bg-white rounded-full p-3 shadow-lg hover:shadow-xl transition-shadow duration-200 text-gray-600 hover:text-primary-500"
            aria-label="Previous testimonial"
          >
            <ChevronLeft className="h-6 w-6" />
          </button>
          
          <button
            onClick={goToNext}
            className="absolute right-4 top-1/2 transform -translate-y-1/2 bg-white rounded-full p-3 shadow-lg hover:shadow-xl transition-shadow duration-200 text-gray-600 hover:text-primary-500"
            aria-label="Next testimonial"
          >
            <ChevronRight className="h-6 w-6" />
          </button>

          {/* Dots Indicator */}
          <div className="flex justify-center space-x-2 mt-8">
            {testimonials.map((_, index) => (
              <button
                key={index}
                onClick={() => goToSlide(index)}
                className={`w-3 h-3 rounded-full transition-all duration-200 ${
                  index === currentIndex
                    ? 'bg-primary-500 scale-125'
                    : 'bg-gray-300 hover:bg-gray-400'
                }`}
                aria-label={`Go to testimonial ${index + 1}`}
              />
            ))}
          </div>
        </div>

        {/* Thumbnail Testimonials */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
          {testimonials.slice(0, 3).map((testimonial, index) => (
            <motion.div
              key={testimonial.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              className="bg-white rounded-xl p-6 shadow-md hover:shadow-lg transition-shadow duration-200 cursor-pointer"
              onClick={() => goToSlide(testimonials.findIndex(t => t.id === testimonial.id))}
            >
              <div className="flex items-center space-x-3 mb-4">
                <img
                  src={testimonial.avatar}
                  alt={testimonial.name}
                  className="w-12 h-12 rounded-full object-cover"
                />
                <div>
                  <div className="font-semibold text-gray-900">{testimonial.name}</div>
                  <div className="text-sm text-gray-600">{testimonial.role}</div>
                </div>
              </div>
              <div className="flex mb-3">
                {renderStars(testimonial.rating)}
              </div>
              <p className="text-gray-700 text-sm overflow-hidden" style={{ 
                display: '-webkit-box',
                WebkitLineClamp: 3,
                WebkitBoxOrient: 'vertical'
              }}>
                "{testimonial.content}"
              </p>
            </motion.div>
          ))}
        </div>

        {/* Auto-play Control */}
        <div className="text-center mt-8">
          <button
            onClick={() => setIsAutoPlaying(!isAutoPlaying)}
            className="text-sm text-gray-500 hover:text-primary-500 transition-colors duration-200"
          >
            {isAutoPlaying ? 'Pause' : 'Resume'} auto-play
          </button>
        </div>
      </div>
    </section>
  );
};

export default TestimonialsCarousel;