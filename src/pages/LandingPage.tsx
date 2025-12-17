import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Users, 
  GitBranch, 
  Menu, 
  X, 
  ArrowRight,
  CheckCircle,
  Star,
  TrendingUp,
  Award,
  Target
} from 'lucide-react';
import TestimonialsCarousel from '../components/TestimonialsCarousel';
import FeaturesShowcase from '../components/FeaturesShowcase';

const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const scrollToSection = (sectionId: string) => {
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen">
      {/* Navigation */}
      <nav className="bg-white/95 backdrop-blur-sm shadow-sm border-b border-gray-100 fixed w-full top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <GitBranch className="h-8 w-8 text-primary-500" />
              <span className="ml-2 text-xl font-bold text-gray-900">BroskiesHub</span>
            </div>
            
            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center space-x-8">
              <button
                onClick={() => scrollToSection('features')}
                className="text-gray-600 hover:text-primary-500 transition-colors"
              >
                Features
              </button>
              <button
                onClick={() => scrollToSection('how-it-works')}
                className="text-gray-600 hover:text-primary-500 transition-colors"
              >
                How It Works
              </button>
              <button
                onClick={() => scrollToSection('pricing')}
                className="text-gray-600 hover:text-primary-500 transition-colors"
              >
                Pricing
              </button>
              <div className="flex space-x-4">
                <button
                  onClick={() => navigate('/developer/auth')}
                  className="btn-outline"
                >
                  For Developers
                </button>
                <button
                  onClick={() => navigate('/hr/auth')}
                  className="btn-primary"
                >
                  Hire Now
                </button>
              </div>
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden">
              <button
                onClick={() => setIsMenuOpen(!isMenuOpen)}
                className="text-gray-600 hover:text-primary-500"
              >
                {isMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
              </button>
            </div>
          </div>

          {/* Mobile Navigation */}
          {isMenuOpen && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="md:hidden py-4 border-t border-gray-100"
            >
              <div className="flex flex-col space-y-4">
                <button
                  onClick={() => {
                    scrollToSection('features');
                    setIsMenuOpen(false);
                  }}
                  className="text-gray-600 hover:text-primary-500 text-left"
                >
                  Features
                </button>
                <button
                  onClick={() => {
                    scrollToSection('how-it-works');
                    setIsMenuOpen(false);
                  }}
                  className="text-gray-600 hover:text-primary-500 text-left"
                >
                  How It Works
                </button>
                <button
                  onClick={() => {
                    scrollToSection('pricing');
                    setIsMenuOpen(false);
                  }}
                  className="text-gray-600 hover:text-primary-500 text-left"
                >
                  Pricing
                </button>
                <div className="flex flex-col space-y-2 pt-4">
                  <button
                    onClick={() => navigate('/developer/auth')}
                    className="btn-outline w-full"
                  >
                    For Developers
                  </button>
                  <button
                    onClick={() => navigate('/hr/auth')}
                    className="btn-primary w-full"
                  >
                    Hire Now
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </nav>

      {/* Hero Section */}
      <section className="gradient-bg text-white pt-24 pb-20 relative overflow-hidden">
        {/* Background decorations */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-10 w-20 h-20 bg-white rounded-full animate-bounce-slow"></div>
          <div className="absolute top-40 right-20 w-16 h-16 bg-accent-500 rounded-full animate-pulse"></div>
          <div className="absolute bottom-20 left-1/4 w-12 h-12 bg-secondary-500 rounded-full animate-bounce-slow"></div>
        </div>
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mb-6"
          >
            <span className="inline-flex items-center px-4 py-2 bg-white/10 backdrop-blur-sm rounded-full text-sm font-medium mb-6">
              <Star className="h-4 w-4 mr-2" />
              Trusted by 10,000+ developers and 500+ companies
            </span>
          </motion.div>
          
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold mb-6 leading-tight"
          >
            Evaluate Code Quality,
            <br />
            <span className="text-accent-500">Hire with Confidence</span>
          </motion.h1>
          
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-lg sm:text-xl md:text-2xl mb-8 text-gray-100 max-w-4xl mx-auto leading-relaxed"
          >
            Our AI-powered platform analyzes GitHub repositories using advanced ACID scoring 
            to provide comprehensive developer evaluations beyond traditional resumes.
          </motion.p>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="flex flex-col sm:flex-row gap-4 justify-center mb-12"
          >
            <motion.button
              onClick={() => navigate('/developer/auth')}
              className="bg-white text-primary-500 hover:bg-gray-100 font-semibold py-4 px-8 rounded-lg transition-all duration-200 flex items-center justify-center group relative overflow-hidden"
              whileHover={{ scale: 1.05, y: -2 }}
              whileTap={{ scale: 0.98 }}
            >
              <motion.div
                className="absolute inset-0 bg-gradient-to-r from-primary-100 to-secondary-100"
                initial={{ x: '-100%' }}
                whileHover={{ x: '100%' }}
                transition={{ duration: 0.6 }}
              />
              <span className="relative z-10">Scan Repositories</span>
              <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform relative z-10" />
            </motion.button>
            <motion.button
              onClick={() => navigate('/hr/auth')}
              className="bg-transparent border-2 border-white text-white hover:bg-white hover:text-primary-500 font-semibold py-4 px-8 rounded-lg transition-all duration-200 flex items-center justify-center group relative overflow-hidden"
              whileHover={{ scale: 1.05, y: -2 }}
              whileTap={{ scale: 0.98 }}
            >
              <motion.div
                className="absolute inset-0 bg-white"
                initial={{ scale: 0, opacity: 0 }}
                whileHover={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.3 }}
              />
              <span className="relative z-10">Find Top Talent</span>
              <Users className="ml-2 h-5 w-5 group-hover:scale-110 transition-transform relative z-10" />
            </motion.button>
          </motion.div>

          {/* Stats */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-3xl mx-auto"
          >
            {[
              { number: '10K+', label: 'Developers' },
              { number: '500+', label: 'Companies' },
              { number: '1M+', label: 'Repositories Analyzed' },
              { number: '95%', label: 'Accuracy Rate' }
            ].map((stat, index) => (
              <motion.div 
                key={index} 
                className="text-center"
                whileHover={{ scale: 1.1, y: -5 }}
                transition={{ duration: 0.2 }}
              >
                <motion.div 
                  className="text-2xl md:text-3xl font-bold text-white"
                  initial={{ opacity: 0, scale: 0 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.5, delay: 0.8 + index * 0.1 }}
                >
                  {stat.number}
                </motion.div>
                <div className="text-sm text-gray-200">{stat.label}</div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* Features Section */}
      <FeaturesShowcase />

      {/* How It Works Section */}
      <section id="how-it-works" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
                How It Works
              </h2>
              <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                Simple, fast, and accurate - get comprehensive developer insights in minutes
              </p>
            </motion.div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                step: "01",
                icon: <GitBranch className="h-8 w-8 text-primary-500" />,
                title: "Connect GitHub",
                description: "Securely connect your GitHub account or provide a repository URL for analysis"
              },
              {
                step: "02",
                icon: <TrendingUp className="h-8 w-8 text-secondary-500" />,
                title: "AI Analysis",
                description: "Our advanced algorithms analyze code quality, security, and best practices across all repositories"
              },
              {
                step: "03",
                icon: <Award className="h-8 w-8 text-accent-500" />,
                title: "Get Insights",
                description: "Receive detailed reports with ACID scores, skill assessments, and personalized recommendations"
              }
            ].map((step, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.2 }}
                whileHover={{ y: -10 }}
                className="text-center relative"
              >
                <div className="mb-6">
                  <motion.div 
                    className="inline-flex items-center justify-center w-16 h-16 bg-white rounded-full shadow-lg mb-4"
                    whileHover={{ 
                      scale: 1.1, 
                      rotate: 360,
                      boxShadow: '0 10px 30px rgba(0, 0, 0, 0.2)'
                    }}
                    transition={{ duration: 0.5 }}
                  >
                    {step.icon}
                  </motion.div>
                  <motion.div 
                    className="absolute -top-2 -right-2 w-8 h-8 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-full flex items-center justify-center text-white text-sm font-bold"
                    animate={{ 
                      scale: [1, 1.1, 1],
                      rotate: [0, 5, -5, 0]
                    }}
                    transition={{ 
                      duration: 2,
                      repeat: Infinity,
                      repeatType: 'reverse'
                    }}
                  >
                    {step.step}
                  </motion.div>
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-4">
                  {step.title}
                </h3>
                <p className="text-gray-600 leading-relaxed">
                  {step.description}
                </p>
                {index < 2 && (
                  <div className="hidden md:block absolute top-8 left-full w-full">
                    <ArrowRight className="h-6 w-6 text-gray-300 mx-auto" />
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Benefits Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <h2 className="text-4xl font-bold text-gray-900 mb-6">
                Traditional Hiring vs. BroskiesHub
              </h2>
              <p className="text-xl text-gray-600 mb-8">
                See the difference data-driven hiring makes
              </p>
              
              <div className="space-y-6">
                {[
                  {
                    traditional: "Resume-based screening",
                    broskieshub: "Code quality analysis",
                    icon: <CheckCircle className="h-5 w-5 text-green-500" />
                  },
                  {
                    traditional: "Subjective interviews",
                    broskieshub: "Objective ACID scoring",
                    icon: <CheckCircle className="h-5 w-5 text-green-500" />
                  },
                  {
                    traditional: "Limited skill visibility",
                    broskieshub: "Comprehensive skill mapping",
                    icon: <CheckCircle className="h-5 w-5 text-green-500" />
                  },
                  {
                    traditional: "Time-consuming process",
                    broskieshub: "Instant insights",
                    icon: <CheckCircle className="h-5 w-5 text-green-500" />
                  }
                ].map((comparison, index) => (
                  <div key={index} className="flex items-start space-x-4">
                    {comparison.icon}
                    <div>
                      <div className="text-gray-500 line-through text-sm">
                        {comparison.traditional}
                      </div>
                      <div className="text-gray-900 font-medium">
                        {comparison.broskieshub}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="bg-gradient-to-br from-primary-500 to-secondary-500 rounded-2xl p-8 text-white"
            >
              <h3 className="text-2xl font-bold mb-6">Success Metrics</h3>
              <div className="space-y-6">
                {[
                  { metric: "Hiring Accuracy", value: "95%", increase: "+40%" },
                  { metric: "Time to Hire", value: "3 days", decrease: "-75%" },
                  { metric: "Developer Satisfaction", value: "4.8/5", increase: "+25%" },
                  { metric: "Cost per Hire", value: "$500", decrease: "-60%" }
                ].map((stat, index) => (
                  <div key={index} className="flex justify-between items-center">
                    <span className="text-gray-100">{stat.metric}</span>
                    <div className="text-right">
                      <div className="text-2xl font-bold">{stat.value}</div>
                      <div className={`text-sm ${stat.increase ? 'text-green-300' : 'text-green-300'}`}>
                        {stat.increase || stat.decrease}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <TestimonialsCarousel />

      {/* Pricing Section */}
      <section id="pricing" className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
            >
              <h2 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
                Simple, Transparent Pricing
              </h2>
              <p className="text-xl text-gray-600 max-w-3xl mx-auto">
                Choose the plan that fits your needs. Start free, upgrade when you're ready.
              </p>
            </motion.div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {[
              {
                name: "Developer",
                price: "Free",
                description: "Perfect for individual developers",
                features: [
                  "Scan up to 5 repositories",
                  "Basic ACID scoring",
                  "Code quality insights",
                  "GitHub integration",
                  "Personal dashboard"
                ],
                cta: "Get Started",
                popular: false
              },
              {
                name: "Professional",
                price: "$29",
                period: "/month",
                description: "For serious developers and freelancers",
                features: [
                  "Unlimited repository scans",
                  "Advanced analytics",
                  "Security assessments",
                  "Skill roadmaps",
                  "Priority support",
                  "API access"
                ],
                cta: "Start Free Trial",
                popular: true
              },
              {
                name: "Enterprise",
                price: "Custom",
                description: "For companies and HR teams",
                features: [
                  "Everything in Professional",
                  "Team management",
                  "Bulk candidate analysis",
                  "Custom integrations",
                  "Dedicated support",
                  "SLA guarantee"
                ],
                cta: "Contact Sales",
                popular: false
              }
            ].map((plan, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                whileHover={{ 
                  y: -10,
                  scale: plan.popular ? 1.05 : 1.03,
                  boxShadow: plan.popular 
                    ? '0 25px 50px -12px rgba(59, 130, 246, 0.25)' 
                    : '0 20px 25px -5px rgba(0, 0, 0, 0.1)'
                }}
                className={`card p-8 relative ${
                  plan.popular 
                    ? 'border-2 border-primary-500 shadow-xl scale-105' 
                    : 'border border-gray-200'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <span className="bg-primary-500 text-white px-4 py-1 rounded-full text-sm font-medium">
                      Most Popular
                    </span>
                  </div>
                )}
                
                <div className="text-center mb-8">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                  <div className="mb-4">
                    <span className="text-4xl font-bold text-gray-900">{plan.price}</span>
                    {plan.period && <span className="text-gray-600">{plan.period}</span>}
                  </div>
                  <p className="text-gray-600">{plan.description}</p>
                </div>

                <ul className="space-y-4 mb-8">
                  {plan.features.map((feature, featureIndex) => (
                    <li key={featureIndex} className="flex items-start">
                      <CheckCircle className="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0" />
                      <span className="text-gray-700">{feature}</span>
                    </li>
                  ))}
                </ul>

                <motion.button
                  onClick={() => {
                    if (plan.name === 'Enterprise') {
                      // For now, redirect to HR auth for enterprise inquiries
                      navigate('/hr/auth');
                    } else {
                      navigate('/developer/auth');
                    }
                  }}
                  className={`w-full py-3 px-6 rounded-lg font-semibold transition-colors duration-200 relative overflow-hidden ${
                    plan.popular
                      ? 'bg-primary-500 text-white hover:bg-primary-600'
                      : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                  }`}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <motion.div
                    className={`absolute inset-0 ${
                      plan.popular 
                        ? 'bg-gradient-to-r from-primary-600 to-secondary-600' 
                        : 'bg-gray-200'
                    }`}
                    initial={{ x: '-100%' }}
                    whileHover={{ x: '100%' }}
                    transition={{ duration: 0.6 }}
                  />
                  <span className="relative z-10">{plan.cta}</span>
                </motion.button>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 gradient-bg text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-6">
              Ready to Transform Your Hiring?
            </h2>
            <p className="text-xl text-gray-100 mb-8 max-w-2xl mx-auto">
              Join thousands of companies already using BroskiesHub to find and hire the best developers based on actual code quality.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button
                onClick={() => navigate('/developer/auth')}
                className="bg-white text-primary-500 hover:bg-gray-100 font-semibold py-4 px-8 rounded-lg transition-colors duration-200 flex items-center justify-center"
              >
                <Target className="mr-2 h-5 w-5" />
                Start Your Analysis
              </button>
              <button
                onClick={() => navigate('/hr/auth')}
                className="bg-transparent border-2 border-white text-white hover:bg-white hover:text-primary-500 font-semibold py-4 px-8 rounded-lg transition-all duration-200 flex items-center justify-center"
              >
                <Users className="mr-2 h-5 w-5" />
                Find Developers
              </button>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-8">
            <div className="lg:col-span-2">
              <div className="flex items-center mb-6">
                <GitBranch className="h-8 w-8 text-primary-500" />
                <span className="ml-2 text-2xl font-bold">BroskiesHub</span>
              </div>
              <p className="text-gray-400 mb-6 max-w-md">
                Revolutionizing developer hiring through intelligent code analysis. 
                Make data-driven hiring decisions with confidence.
              </p>
              <div className="flex space-x-4">
                <a href="#" className="text-gray-400 hover:text-white transition-colors">
                  <span className="sr-only">Twitter</span>
                  <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" />
                  </svg>
                </a>
                <a href="#" className="text-gray-400 hover:text-white transition-colors">
                  <span className="sr-only">LinkedIn</span>
                  <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                  </svg>
                </a>
                <a href="#" className="text-gray-400 hover:text-white transition-colors">
                  <span className="sr-only">GitHub</span>
                  <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                  </svg>
                </a>
              </div>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">For Developers</h4>
              <ul className="space-y-3 text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">Scan Repositories</a></li>
                <li><a href="#" className="hover:text-white transition-colors">View Analytics</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Improve Skills</a></li>
                <li><a href="#" className="hover:text-white transition-colors">API Documentation</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-4">For Companies</h4>
              <ul className="space-y-3 text-gray-400">
                <li><a href="#" className="hover:text-white transition-colors">Find Candidates</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Compare Profiles</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Hiring Tools</a></li>
                <li><a href="#" className="hover:text-white transition-colors">Enterprise Solutions</a></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-gray-800 pt-8">
            <div className="flex flex-col md:flex-row justify-between items-center">
              <p className="text-gray-400 text-sm">
                &copy; 2024 BroskiesHub. All rights reserved.
              </p>
              <div className="flex space-x-6 mt-4 md:mt-0">
                <a href="#" className="text-gray-400 hover:text-white text-sm transition-colors">Privacy Policy</a>
                <a href="#" className="text-gray-400 hover:text-white text-sm transition-colors">Terms of Service</a>
                <a href="#" className="text-gray-400 hover:text-white text-sm transition-colors">Cookie Policy</a>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;