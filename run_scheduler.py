#!/usr/bin/env python3
"""
Startup script for Process Scheduler Simulator with Cybersecurity
Automatically sets up the environment and starts the application
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version}")

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        print("Please run: pip install -r requirements.txt")
        return False
    return True

def check_files():
    """Check if all required files exist"""
    required_files = [
        'app.py',
        'process_scheduler_security.py',
        'requirements.txt',
        'templates/index.html',
        'static/js/app.js'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ All required files present")
    return True

def start_application():
    """Start the Flask application"""
    print("🚀 Starting Process Scheduler Simulator...")
    print("=" * 60)
    print("🔧 Features:")
    print("   - Multi-algorithm process scheduling (Round Robin, Priority)")
    print("   - Real-time cybersecurity monitoring")
    print("   - Rogue process detection and mitigation")
    print("   - DoS attack simulation")
    print("   - Machine learning anomaly detection")
    print("   - Interactive web dashboard")
    print("   - WebSocket real-time updates")
    print("=" * 60)
    print()
    print("🌐 Application will be available at: http://localhost:5000")
    print("📡 WebSocket endpoint: ws://localhost:5000/socket.io")
    print()
    print("💡 Usage Tips:")
    print("   1. Add processes using the control panel")
    print("   2. Select scheduling algorithm (Round Robin or Priority)")
    print("   3. Start simulation to see real-time execution")
    print("   4. Monitor security alerts for rogue processes")
    print("   5. View Gantt chart and performance metrics")
    print()
    print("⚠️  Note: Rogue processes will be automatically detected and terminated")
    print("=" * 60)
    print()
    
    # Wait a moment then open browser
    def open_browser():
        time.sleep(2)
        try:
            webbrowser.open('http://localhost:5000')
            print("🌐 Opening web browser...")
        except:
            print("💻 Please open http://localhost:5000 in your web browser")
    
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Start Flask app
    try:
        from app import socketio, app
        socketio.run(app, debug=False, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Error starting application: {e}")
        return False
    
    return True

def main():
    """Main startup function"""
    print("🔒 Process Scheduler Simulator with Cybersecurity")
    print("=" * 50)
    print("Starting setup and launch sequence...")
    print()
    
    # Check Python version
    check_python_version()
    
    # Check required files
    if not check_files():
        print("❌ Setup failed: Missing required files")
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Setup failed: Could not install dependencies")
        sys.exit(1)
    
    print()
    print("✅ Setup completed successfully!")
    print()
    input("Press Enter to start the application...")
    print()
    
    # Start application
    if not start_application():
        print("❌ Failed to start application")
        sys.exit(1)

if __name__ == "__main__":
    main()
