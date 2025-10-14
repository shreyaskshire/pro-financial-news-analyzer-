#!/usr/bin/env python3
"""Test script to verify all imports work"""

import sys

def test_imports():
    """Test all required imports"""
    errors = []
    
    # Test basic imports
    try:
        from flask import Flask
        print("✓ Flask imported successfully")
    except Exception as e:
        errors.append(f"✗ Flask import failed: {e}")
    
    try:
        import gunicorn
        print("✓ Gunicorn imported successfully")
    except Exception as e:
        errors.append(f"✗ Gunicorn import failed: {e}")
    
    try:
        import requests
        print("✓ Requests imported successfully")
    except Exception as e:
        errors.append(f"✗ Requests import failed: {e}")
    
    try:
        import feedparser
        print("✓ Feedparser imported successfully")
    except Exception as e:
        errors.append(f"✗ Feedparser import failed: {e}")
    
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        print("✓ APScheduler imported successfully")
    except Exception as e:
        errors.append(f"✗ APScheduler import failed: {e}")
    
    try:
        import pytz
        print("✓ pytz imported successfully")
    except Exception as e:
        errors.append(f"✗ pytz import failed: {e}")
    
    # Print results
    print("\n" + "="*50)
    if errors:
        print("ERRORS FOUND:")
        for error in errors:
            print(error)
        sys.exit(1)
    else:
        print("✓ ALL IMPORTS SUCCESSFUL!")
        sys.exit(0)

if __name__ == "__main__":
    print("Testing Python imports...\n")
    test_imports()
