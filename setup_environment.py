#!/usr/bin/env python3
"""
Environment Configuration for Ancient Free Will Database

This script sets up proper environment variable management for secure API key handling.
Follows security best practices for production systems.

Author: Romain Girardi
Date: 2025-01-17
"""

import os
from pathlib import Path
from typing import Optional


class EnvironmentConfig:
    """Secure environment configuration management."""
    
    def __init__(self):
        self.project_root = Path("/Users/romaingirardi/Documents/Ancient Free Will Database")
        self.env_file = self.project_root / ".env"
        self.env_example_file = self.project_root / ".env.example"
        
    def create_env_example(self) -> None:
        """Create .env.example file with template."""
        env_example_content = """# Ancient Free Will Database - Environment Configuration
# Copy this file to .env and fill in your actual values

# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=ancient_free_will_db
POSTGRES_USER=free_will_user
POSTGRES_PASSWORD=free_will_password

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_HTTP_PORT=6333
QDRANT_GRPC_PORT=6334

# Application Configuration
LOG_LEVEL=INFO
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSIONS=3072
"""
        
        with open(self.env_example_file, 'w') as f:
            f.write(env_example_content)
            
        print(f"✅ Created .env.example template")
        
    def create_env_file(self, gemini_api_key: str) -> None:
        """Create .env file with actual configuration."""
        env_content = f"""# Ancient Free Will Database - Environment Configuration
# Generated automatically - DO NOT COMMIT TO VERSION CONTROL

# Gemini API Configuration
GEMINI_API_KEY={gemini_api_key}

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5433
POSTGRES_DB=ancient_free_will_db
POSTGRES_USER=free_will_user
POSTGRES_PASSWORD=free_will_password

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_HTTP_PORT=6333
QDRANT_GRPC_PORT=6334

# Application Configuration
LOG_LEVEL=INFO
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIMENSIONS=3072
"""
        
        with open(self.env_file, 'w') as f:
            f.write(env_content)
            
        print(f"✅ Created .env file with configuration")
        
    def load_env_file(self) -> None:
        """Load environment variables from .env file."""
        if self.env_file.exists():
            from dotenv import load_dotenv
            load_dotenv(self.env_file)
            print(f"✅ Loaded environment variables from .env")
        else:
            print(f"⚠️  .env file not found. Using system environment variables.")
            
    def get_gemini_api_key(self) -> Optional[str]:
        """Get Gemini API key from environment."""
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEY not found in environment variables")
            print("   Please set it using one of these methods:")
            print("   1. Create .env file with GEMINI_API_KEY=your_key")
            print("   2. Export: export GEMINI_API_KEY='your_key'")
            print("   3. Run: python3 setup_environment.py --api-key your_key")
            return None
        return api_key
        
    def validate_configuration(self) -> bool:
        """Validate that all required environment variables are set."""
        # Load environment variables first
        self.load_env_file()
        
        required_vars = [
            'GEMINI_API_KEY',
            'POSTGRES_HOST',
            'POSTGRES_PORT',
            'POSTGRES_DB',
            'POSTGRES_USER',
            'POSTGRES_PASSWORD',
            'QDRANT_HOST',
            'QDRANT_HTTP_PORT'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
                
        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            return False
            
        print("✅ All required environment variables are set")
        return True
        
    def setup_gitignore(self) -> None:
        """Ensure .env files are in .gitignore."""
        gitignore_path = self.project_root / ".gitignore"
        
        # Read existing .gitignore
        existing_content = ""
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                existing_content = f.read()
                
        # Add environment files if not already present
        env_patterns = [
            "# Environment files",
            ".env",
            ".env.local",
            ".env.*.local",
            "*.env"
        ]
        
        needs_update = False
        for pattern in env_patterns:
            if pattern not in existing_content:
                needs_update = True
                break
                
        if needs_update:
            with open(gitignore_path, 'a') as f:
                f.write("\n")
                for pattern in env_patterns:
                    f.write(f"{pattern}\n")
            print("✅ Updated .gitignore to exclude environment files")
        else:
            print("✅ .gitignore already excludes environment files")


def main():
    """Main function to set up environment configuration."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Set up environment configuration")
    parser.add_argument("--api-key", help="Gemini API key to set")
    parser.add_argument("--setup-only", action="store_true", help="Only create template files")
    
    args = parser.parse_args()
    
    config = EnvironmentConfig()
    
    print("🔧 Setting up environment configuration...")
    
    # Create template files
    config.create_env_example()
    config.setup_gitignore()
    
    if args.setup_only:
        print("✅ Environment template setup complete")
        print("   Next steps:")
        print("   1. Copy .env.example to .env")
        print("   2. Edit .env with your actual API key")
        print("   3. Run your scripts")
        return
        
    if args.api_key:
        # Create .env file with provided API key
        config.create_env_file(args.api_key)
        print("✅ Environment configuration complete")
    else:
        # Load existing .env file
        config.load_env_file()
        
    # Validate configuration
    if config.validate_configuration():
        print("🎉 Environment configuration is ready!")
    else:
        print("❌ Environment configuration incomplete")


if __name__ == "__main__":
    main()
