#!/usr/bin/env python3
"""
Deployment helper script for Phantoms JWT Generator
"""

import os
import sys
import subprocess
import json

def check_requirements():
    """Check if all deployment requirements are met"""
    print("🔍 Checking deployment requirements...")
    
    required_files = [
        'vercel.json',
        'netlify.toml', 
        'Procfile',
        'runtime.txt',
        'app.yaml',
        'main.py',
        'app.py',
        'DEPLOYMENT_GUIDE.md'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    print("✅ All deployment files present")
    return True

def generate_secret_key():
    """Generate a secure secret key"""
    import secrets
    key = secrets.token_hex(32)
    print(f"🔑 Generated secret key: {key}")
    print("Set this as SESSION_SECRET environment variable")
    return key

def deploy_vercel():
    """Deploy to Vercel"""
    print("🚀 Deploying to Vercel...")
    try:
        subprocess.run(['vercel', '--prod'], check=True)
        print("✅ Vercel deployment successful!")
    except subprocess.CalledProcessError:
        print("❌ Vercel deployment failed")
        print("Make sure you have Vercel CLI installed: npm i -g vercel")

def deploy_netlify():
    """Deploy to Netlify"""  
    print("🚀 Deploying to Netlify...")
    try:
        subprocess.run(['netlify', 'deploy', '--prod'], check=True)
        print("✅ Netlify deployment successful!")
    except subprocess.CalledProcessError:
        print("❌ Netlify deployment failed")
        print("Make sure you have Netlify CLI installed: npm i -g netlify-cli")

def deploy_heroku():
    """Deploy to Heroku"""
    print("🚀 Deploying to Heroku...")
    try:
        subprocess.run(['git', 'push', 'heroku', 'main'], check=True)
        print("✅ Heroku deployment successful!")
    except subprocess.CalledProcessError:
        print("❌ Heroku deployment failed")
        print("Make sure you have Heroku CLI and git repository set up")

def main():
    if len(sys.argv) < 2:
        print("Usage: python deploy.py [check|secret|vercel|netlify|heroku]")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'check':
        check_requirements()
    elif command == 'secret':
        generate_secret_key()
    elif command == 'vercel':
        if check_requirements():
            deploy_vercel()
    elif command == 'netlify':
        if check_requirements():
            deploy_netlify()
    elif command == 'heroku':
        if check_requirements():
            deploy_heroku()
    else:
        print("❌ Unknown command. Use: check, secret, vercel, netlify, or heroku")

if __name__ == "__main__":
    main()