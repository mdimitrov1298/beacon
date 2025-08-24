#!/usr/bin/env python3

import subprocess
import time
import requests
import sys
import os

def run_command(command, check=True):
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Command failed: {result.stderr}")
        return False
    return result

def wait_for_server(url, max_attempts=30, delay=2):
    print(f"Waiting for server to be ready at {url}...")
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{url}/health", timeout=5)
            if response.status_code == 200:
                print(f"Server is ready after {attempt * delay} seconds")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(delay)
    
    print("Server failed to start within expected time")
    return False

def main():
    print("Starting Docker-based testing...")
    
    print("\n1. Building Docker image...")
    if not run_command("docker build -f Dockerfile.test -t beacon-test ."):
        print("Failed to build Docker image")
        return False
    
    print("\n2. Stopping any existing containers...")
    run_command("docker stop beacon-test-container 2>/dev/null || true", check=False)
    run_command("docker rm beacon-test-container 2>/dev/null || true", check=False)
    
    print("\n3. Starting test container...")
    container_cmd = [
        "docker run -d",
        "--name beacon-test-container",
        "-p 8000:8000",
        "-v $(pwd)/beacon.db:/app/beacon.db",
        "-v $(pwd)/beacon_test.db:/app/beacon_test.db",
        "-v $(pwd)/beacon_dev.db:/app/beacon_dev.db",
        "-v $(pwd)/beacon_commercial_register.db:/app/beacon_commercial_register.db",
        "-e ENVIRONMENT=testing",
        "beacon-test"
    ]
    
    if not run_command(" ".join(container_cmd)):
        print("Failed to start container")
        return False
    
    print("\n4. Waiting for server to start...")
    if not wait_for_server("http://localhost:8000"):
        print("Server failed to start")
        return False
    
    print("\n5. Running tests...")
    if not run_command("python tests/run_tests.py"):
        print("Tests failed")
        return False
    
    print("\n6. Cleaning up...")
    run_command("docker stop beacon-test-container", check=False)
    run_command("docker rm beacon-test-container", check=False)
    
    print("\nDocker-based testing completed successfully!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
