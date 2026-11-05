"""Run quality and evaluation jobs, recording the result in harness-log.md."""

import argparse
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

PART_ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = Path(__file__).resolve().parent / "harness-log.md"


def execute_job(
    command: list[str],
    job_name: str,
    log_sections: list[str],
) -> int:
    header = f"## {job_name}\n\nCommand: `{subprocess.list2cmdline(command)}`\n"
    print("\n========================================")
    print(f"JOB START: {job_name}")
    print("========================================")
    try:
        result = subprocess.run(
            command,
            cwd=PART_ROOT,
            env={
                **os.environ,
                "PYTHONPATH": os.pathsep.join(
                    (str(PART_ROOT / "src"), str(Path(__file__).resolve().parent))
                ),
            },
            text=True,
            capture_output=True,
            check=False,
        )
        output = result.stdout
        errors = result.stderr
        if output:
            print(output, end="" if output.endswith("\n") else "\n")
        if errors:
            print(errors, file=sys.stderr, end="" if errors.endswith("\n") else "\n")

        status = (
            "PASSED" if result.returncode == 0 else f"FAILED (exit {result.returncode})"
        )
        log_sections.append(
            f"{header}\nStatus: **{status}**\n\n```text\n{output}{errors}```\n"
        )
        if result.returncode:
            print(
                f"\n[JOB FAILED] {job_name} returned RC={result.returncode}. Pipeline halted."
            )
        else:
            print(f"[JOB PASSED] {job_name} completed successfully.")
        return result.returncode
    except OSError as error:
        message = f"{error.__class__.__name__}: {error}"
        log_sections.append(
            f"{header}\nStatus: **FAILED to start**\n\n```text\n{message}\n```\n"
        )
        print(f"\n[JOB FAILED] {job_name} could not start: {message}", file=sys.stderr)
        return 1


def write_log(
    log_sections: list[str],
    decision: str,
    evaluation_mode: str,
) -> None:
    document = [
        "# Part 1B Harness Log",
        "",
        "## Evaluation Configuration",
        "* **Model:** Mock LLM Adapter (scripted fixtures; no model or network call).",
        f"* **Evaluation mode:** {evaluation_mode}.",
        "* **Dataset:** 15 cases from `evals/dataset.json`.",
        "* **Evaluation thresholds:** 100% structural validity and risk-band accuracy; at least 95% exact match for each scored field; zero unsupported guesses. No 80% aggregate threshold is configured.",
        "* **Scoring method:** Layer 1 checks response structure; Layer 2 checks invariants, age/horizon matches, and clarification behavior; Layer 3 checks risk exact-match, rubric band, and abstention.",
        f"* **Run time (UTC):** {datetime.now(UTC).isoformat()}",
        "",
        "## Harness Execution 1 (Failure)",
        "* **Outcome:** FAIL (initial run before the mock adapter was added).",
        "* **Evidence:** The semantic evaluator returned `adapter_not_configured`; all three evaluation layers were `NOT_RUN`, and the CLI returned aggregate `FAIL`.",
        "",
        "## Repair Cycle",
        "* **Feedback:** Implement a mock adapter so all 15 cases can exercise the evaluation layers without API credentials or network access.",
        "* **Repair:** Added a scripted fixture adapter keyed to the dataset biographies. It simulates expected outputs and is for harness verification only, not a live model or accuracy test.",
        "",
        "## Re-evaluation",
        f"* **Outcome:** {decision}",
        "* **Evidence:** The latest pipeline output, including per-layer metrics and checks, is recorded below.",
        "",
        *log_sections,
        "## Final Human Review",
        "* **Decision:** PENDING — requires a human reviewer; the harness does not issue human acceptance.",
        "* **Limitations & residual risks:** Mock fixtures are fixed and mirror this dataset; a passing result verifies evaluator plumbing only and does not establish real-model accuracy, non-deterministic behavior, or generalization. Any live-provider evaluation requires separate approval and secure configuration.",
    ]
    LOG_PATH.write_text("\n".join(document), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    _, evaluator_arguments = parser.parse_known_args(argv)
    has_adapter = any(
        argument == "--adapter" or argument.startswith("--adapter=")
        for argument in evaluator_arguments
    )
    evaluation_mode = (
        "Configured adapter; results are not necessarily mock"
        if has_adapter
        else "MOCK fixtures; smoke test only, not model accuracy"
    )
    if not has_adapter:
        evaluator_arguments = [
            "--adapter",
            "mock_adapter:create_adapter",
            *evaluator_arguments,
        ]

    log_sections: list[str] = []
    jobs = [
        (["ruff", "check", "src", ".harness"], "LINT_GUARD"),
        (
            ["bandit", "-r", "src", ".harness/mock_adapter.py"],
            "SECURITY_SAST_GUARD",
        ),
        (
            [
                sys.executable,
                "-m",
                "financial_persona_extractor.evaluation",
                *evaluator_arguments,
            ],
            "AI_SEMANTIC_EVALUATOR",
        ),
    ]

    exit_code = 0
    decision = "INCOMPLETE"
    try:
        print(
            "INITIALIZING PART 1B AI EVALUATION PIPELINE...\n"
            "Default mode uses scripted mock fixtures; PASS is not model validation.\n"
        )
        for command, job_name in jobs:
            exit_code = execute_job(command, job_name, log_sections)
            if exit_code:
                decision = "FAIL"
                break
        else:
            decision = "PASS"
    finally:
        write_log(log_sections, decision, evaluation_mode)
        print(f"\nHarness log written to: {LOG_PATH}")

    if exit_code == 0:
        print("\n[PIPELINE SUCCESS] All configured checks passed.")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
