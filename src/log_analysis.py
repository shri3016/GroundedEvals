"""
Post-Hoc Log Analysis:Analyzes Inspect AI evaluation logs and extracts behavioral insights.

Features:
1)Parse evaluation logs
2)Aggregate metrics by category
3)Identify failure patterns
4)Compare model behaviors
5)Generate analysis reports

Usage: python log_analysis.py [log_directory]
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Any, Optional
import re

# LOG PARSING
def find_log_directory() -> Path:
    """Find the Inspect AI logs directory."""
    possible_paths = [
        Path.home() / ".inspect_ai" / "logs",
        Path(".") / "logs",
        Path(".") / ".inspect_ai" / "logs",
    ]

    for path in possible_paths:
        if path.exists():
            return path

    return Path.home() / ".inspect_ai" / "logs"


def load_log_file(log_path: Path) -> Optional[Dict]:
    """Load and parse a single log file."""
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Warning: Could not parse {log_path}: {e}")
        return None


def get_recent_logs(log_dir: Path, limit: int = 10) -> List[Path]:
    """Get the most recent log files."""
    log_files = list(log_dir.glob("**/*.json"))
    log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    return log_files[:limit]

# METRICS EXTRACTION
class LogAnalyzer:
    """Analyzes Inspect AI evaluation logs."""

    def __init__(self, log_data: Dict):
        self.log = log_data
        self.results = log_data.get("results", {})
        self.samples = log_data.get("samples", [])
        self.model = self._extract_model()
        self.task = self._extract_task()

    def _extract_model(self) -> str:
        """Extract model name from log."""
        eval_info = self.log.get("eval", {})
        model = eval_info.get("model", "unknown")
        return model

    def _extract_task(self) -> str:
        """Extract task name from log."""
        eval_info = self.log.get("eval", {})
        return eval_info.get("task", "unknown")

    def get_overall_accuracy(self) -> float:
        """Get overall accuracy score."""
        metrics = self.results.get("metrics", {})
        accuracy = metrics.get("accuracy", {})
        return accuracy.get("value", 0.0)

    def get_category_breakdown(self) -> Dict[str, Dict]:
        """Break down results by category."""
        breakdown = defaultdict(lambda: {"total": 0, "correct": 0, "incorrect": 0, "partial": 0})

        for sample in self.samples:
            metadata = sample.get("metadata", {})
            category = metadata.get("category", "UNKNOWN")
            scores = sample.get("scores", {})

            breakdown[category]["total"] += 1

            # Checking score value
            for scorer_name, score_data in scores.items():
                value = score_data.get("value", "")
                if value == "C" or value == "CORRECT":
                    breakdown[category]["correct"] += 1
                    break
                elif value == "I" or value == "INCORRECT":
                    breakdown[category]["incorrect"] += 1
                    break
                elif value == "P" or value == "PARTIAL":
                    breakdown[category]["partial"] += 1
                    break

        return dict(breakdown)

    def get_failure_analysis(self) -> Dict[str, List]:
        """Identify and categorize failures."""
        failures = defaultdict(list)

        for sample in self.samples:
            scores = sample.get("scores", {})

            for scorer_name, score_data in scores.items():
                value = score_data.get("value", "")
                if value in ["I", "INCORRECT"]:
                    metadata = sample.get("metadata", {})
                    input_text = sample.get("input", "")[:100]
                    output = score_data.get("answer", "")[:100]

                    failure_info = {
                        "input": input_text,
                        "output": output,
                        "category": metadata.get("category", "UNKNOWN"),
                        "expected_behavior": metadata.get("expected_behavior", "unknown"),
                        "explanation": score_data.get("explanation", "")
                    }

                    failures[metadata.get("category", "UNKNOWN")].append(failure_info)
                    break

        return dict(failures)

    def get_refusal_metrics(self) -> Dict:
        """Analyze refusal patterns."""
        refusal_patterns = {
            "total_refusals": 0,
            "appropriate_refusals": 0,
            "over_refusals": 0,
            "under_refusals": 0,
            "apologetic_refusals": 0,
            "verbose_refusals": 0
        }

        refusal_phrases = ["cannot answer", "can't answer", "not in", "not provided"]
        apology_phrases = ["sorry", "apologize", "unfortunately"]

        for sample in self.samples:
            scores = sample.get("scores", {})
            metadata = sample.get("metadata", {})
            expected = metadata.get("expected_behavior", "")

            for scorer_name, score_data in scores.items():
                answer = score_data.get("answer", "").lower()

                has_refusal = any(p in answer for p in refusal_phrases)

                if has_refusal:
                    refusal_patterns["total_refusals"] += 1

                    if any(p in answer for p in apology_phrases):
                        refusal_patterns["apologetic_refusals"] += 1

                    if len(answer.split()) > 50:
                        refusal_patterns["verbose_refusals"] += 1

                    if expected == "refuse":
                        refusal_patterns["appropriate_refusals"] += 1
                    elif expected == "answer":
                        refusal_patterns["over_refusals"] += 1

                elif expected == "refuse":
                    refusal_patterns["under_refusals"] += 1

                break

        return refusal_patterns

    def generate_report(self) -> str:
        """Generate a comprehensive analysis report."""
        lines = []
        lines.append("=" * 60)
        lines.append("EVALUATION LOG ANALYSIS REPORT")
        lines.append("=" * 60)
        lines.append(f"\nModel: {self.model}")
        lines.append(f"Task: {self.task}")
        lines.append(f"Total Samples: {len(self.samples)}")
        lines.append(f"Overall Accuracy: {self.get_overall_accuracy():.2%}")

        # Category breakdown
        lines.append("\n" + "-" * 40)
        lines.append("RESULTS BY CATEGORY")
        lines.append("-" * 40)

        breakdown = self.get_category_breakdown()
        for category, stats in breakdown.items():
            total = stats["total"]
            correct = stats["correct"]
            acc = correct / total if total > 0 else 0
            lines.append(f"\n{category}:")
            lines.append(f"  Total: {total}")
            lines.append(f"  Correct: {correct} ({acc:.0%})")
            lines.append(f"  Incorrect: {stats['incorrect']}")
            lines.append(f"  Partial: {stats['partial']}")

        # Refusal metrics
        lines.append("\n" + "-" * 40)
        lines.append("REFUSAL ANALYSIS")
        lines.append("-" * 40)

        refusals = self.get_refusal_metrics()
        lines.append(f"\nTotal Refusals: {refusals['total_refusals']}")
        lines.append(f"Appropriate Refusals: {refusals['appropriate_refusals']}")
        lines.append(f"Over-Refusals: {refusals['over_refusals']}")
        lines.append(f"Under-Refusals (Hallucinations): {refusals['under_refusals']}")
        lines.append(f"Apologetic Refusals: {refusals['apologetic_refusals']}")
        lines.append(f"Verbose Refusals: {refusals['verbose_refusals']}")

        # Failure examples
        lines.append("\n" + "-" * 40)
        lines.append("FAILURE EXAMPLES (First per category)")
        lines.append("-" * 40)

        failures = self.get_failure_analysis()
        for category, failure_list in failures.items():
            if failure_list:
                f = failure_list[0]
                lines.append(f"\n{category}:")
                lines.append(f"  Input: {f['input'][:80]}...")
                lines.append(f"  Output: {f['output'][:80]}...")
                lines.append(f"  Expected: {f['expected_behavior']}")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)

# MULTI-MODEL COMPARISON

def compare_models(log_files: List[Path]) -> str:
    """Compare results across multiple model evaluation logs."""
    model_results = {}

    for log_path in log_files:
        log_data = load_log_file(log_path)
        if log_data:
            analyzer = LogAnalyzer(log_data)
            model = analyzer.model

            if model not in model_results:
                model_results[model] = {
                    "accuracy": analyzer.get_overall_accuracy(),
                    "breakdown": analyzer.get_category_breakdown(),
                    "refusals": analyzer.get_refusal_metrics()
                }

    # Generate comparison report
    lines = []
    lines.append("=" * 70)
    lines.append("MULTI-MODEL COMPARISON REPORT")
    lines.append("=" * 70)

    if not model_results:
        lines.append("\nNo model results found.")
        return "\n".join(lines)

    # Overall accuracy comparison
    lines.append("\n" + "-" * 50)
    lines.append("OVERALL ACCURACY")
    lines.append("-" * 50)

    for model, results in sorted(model_results.items(), key=lambda x: x[1]["accuracy"], reverse=True):
        lines.append(f"  {model}: {results['accuracy']:.2%}")

    # Category comparison
    lines.append("\n" + "-" * 50)
    lines.append("ACCURACY BY CATEGORY")
    lines.append("-" * 50)

    categories = set()
    for results in model_results.values():
        categories.update(results["breakdown"].keys())

    for category in sorted(categories):
        lines.append(f"\n{category}:")
        for model, results in model_results.items():
            bd = results["breakdown"].get(category, {"total": 0, "correct": 0})
            acc = bd["correct"] / bd["total"] if bd["total"] > 0 else 0
            lines.append(f"  {model}: {acc:.0%}")

    # Refusal behavior comparison
    lines.append("\n" + "-" * 50)
    lines.append("REFUSAL BEHAVIOR")
    lines.append("-" * 50)

    for model, results in model_results.items():
        ref = results["refusals"]
        lines.append(f"\n{model}:")
        lines.append(f"  Over-refusal rate: {ref['over_refusals']}")
        lines.append(f"  Under-refusal rate: {ref['under_refusals']}")
        lines.append(f"  Apologetic: {ref['apologetic_refusals']}")

    lines.append("\n" + "=" * 70)

    return "\n".join(lines)

# MAIN
def main():
    print("Inspect AI Log Analysis Tool")
    print("=" * 40)

    # Find log directory
    if len(sys.argv) > 1:
        log_dir = Path(sys.argv[1])
    else:
        log_dir = find_log_directory()

    print(f"\nLog directory: {log_dir}")

    if not log_dir.exists():
        print(f"Log directory not found: {log_dir}")
        print("\nRun some evaluations first with:")
        print("  inspect eval hallucination_eval.py@hallucination_full_eval --model bedrock/anthropic.claude-3-sonnet-20240229-v1:0")
        return

    # Get recent logs
    recent_logs = get_recent_logs(log_dir, limit=10)

    if not recent_logs:
        print("No log files found.")
        return

    print(f"Found {len(recent_logs)} recent log files")

    # Analyze most recent log
    print("\n" + "-" * 40)
    print("ANALYZING MOST RECENT LOG")
    print("-" * 40)

    latest_log = load_log_file(recent_logs[0])
    if latest_log:
        analyzer = LogAnalyzer(latest_log)
        print(analyzer.generate_report())

    # Multi-model comparison if multiple logs exist
    if len(recent_logs) > 1:
        print("\n")
        print(compare_models(recent_logs))

    # Save report
    report_path = Path("analysis_report.txt")
    if latest_log:
        with open(report_path, 'w') as f:
            f.write(analyzer.generate_report())
        print(f"\nReport saved to: {report_path}")


if __name__ == "__main__":
    main()
