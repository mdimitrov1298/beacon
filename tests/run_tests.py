#!/usr/bin/env python3

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_endpoints import main

if __name__ == "__main__":
    print("Running Beacon API Endpoint Tests")
    print("Make sure your server is running on http://localhost:8000")
    print()
    
    success = main()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
