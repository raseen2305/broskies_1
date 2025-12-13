#!/usr/bin/env python3
"""
Configuration Management CLI Tool
Provides utilities for managing environment configurations across different deployment environments
"""

import argparse
import sys
import os
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.environment_manager import EnvironmentManager, Environment
from app.core.logging_config import setup_logging

def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description="Configuration Management Tool for Database Restructuring"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Detect command
    detect_parser = subparsers.add_parser('detect', help='Detect current environment')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate configuration')
    validate_parser.add_argument('--env', choices=[e.value for e in Environment], 
                               help='Specific environment to validate')
    
    # Template command
    template_parser = subparsers.add_parser('template', help='Generate environment template')
    template_parser.add_argument('environment', choices=[e.value for e in Environment],
                               help='Environment to generate template for')
    template_parser.add_argument('--output', '-o', help='Output file path')
    
    # Summary command
    summary_parser = subparsers.add_parser('summary', help='Show configuration summary')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Setup logging
    setup_logging(log_level="INFO", enable_console_logging=True)
    
    manager = EnvironmentManager()
    
    if args.command == 'detect':
        return handle_detect(manager)
    elif args.command == 'validate':
        return handle_validate(manager, args.env)
    elif args.command == 'template':
        return handle_template(manager, args.environment, args.output)
    elif args.command == 'summary':
        return handle_summary(manager)

def handle_detect(manager: EnvironmentManager) -> int:
    """Handle environment detection"""
    env = manager.detect_environment()
    print(f"Detected environment: {env.value}")
    
    loaded = manager.load_environment_config()
    if loaded:
        print(f"Loaded configuration from: {manager.loaded_env_file}")
    else:
        print("No environment configuration file found")
    
    return 0

def handle_validate(manager: EnvironmentManager, specific_env: str = None) -> int:
    """Handle configuration validation"""
    if specific_env:
        # Set environment for validation
        os.environ["ENVIRONMENT"] = specific_env
        manager.detect_environment()
    
    manager.load_environment_config()
    is_valid = manager.validate_configuration()
    
    if is_valid:
        print("✅ Configuration validation passed")
        return 0
    else:
        print("❌ Configuration validation failed")
        return 1

def handle_template(manager: EnvironmentManager, environment: str, output_path: str = None) -> int:
    """Handle template generation"""
    env = Environment(environment)
    template_path = manager.create_environment_template(env, output_path)
    print(f"Generated template: {template_path}")
    return 0

def handle_summary(manager: EnvironmentManager) -> int:
    """Handle configuration summary"""
    manager.detect_environment()
    manager.load_environment_config()
    summary = manager.get_configuration_summary()
    
    print("Configuration Summary:")
    print(f"  Environment: {summary['environment']}")
    print(f"  Config file: {summary['loaded_env_file']}")
    print(f"  Database URLs: {summary['database_urls_configured']}/6")
    print(f"  Redis: {'✅' if summary['redis_configured'] else '❌'}")
    print(f"  GitHub OAuth: {'✅' if summary['github_oauth_configured'] else '❌'}")
    print(f"  Google OAuth: {'✅' if summary['google_oauth_configured'] else '❌'}")
    print(f"  Validation errors: {summary['validation_errors']}")
    print(f"  Validation warnings: {summary['validation_warnings']}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())