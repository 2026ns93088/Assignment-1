import subprocess
import sys

def run_check(command, step_name):
    print(f"\n--- Running {step_name} ---")
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"\n[FAIL] {step_name} failed. Harness execution stopped.")
        sys.exit(1)
    else:
        print(f"[PASS] {step_name} passed.")

if __name__ == "__main__":
    print("Starting Deterministic Harness Validation...")
    
    # 1. Syntax & Lint Guard
    run_check("ruff check ../src/", "Syntax & Lint Guard")
    
    # 2. Security / SAST Guard
    run_check("bandit -r ../src/", "Security SAST Guard")
    
    # 3. Unit & Contract Tests
    run_check("pytest ../tests/ -v", "Unit & Contract Tests")
    
    print("\n[SUCCESS] All harness gates passed perfectly.")