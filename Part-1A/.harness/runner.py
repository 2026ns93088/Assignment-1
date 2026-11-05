import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = PROJECT_ROOT / "src"
TEST_DIR = PROJECT_ROOT / "tests"


def run_check(command, step_name):
    print(f"\n--- Running {step_name} ---")
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
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
    run_check(["ruff", "check", str(SOURCE_DIR)], "Syntax & Lint Guard")

    # 2. Security / SAST Guard
    run_check(["bandit", "-r", str(SOURCE_DIR)], "Security SAST Guard")

    # 3. Unit & Contract Tests
    run_check(
        ["pytest", str(TEST_DIR), "-v"],
        "Unit & Contract Tests",
    )

    print("\n[SUCCESS] All harness gates passed perfectly.")
