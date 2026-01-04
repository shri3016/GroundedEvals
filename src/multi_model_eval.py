"""
Multi-Model Behavioral Evaluation:Runs the SAME evaluation across different models without changes for comparison.
Goal: Behavioral comparison.
Models:
-"openrouter/google/gemini-2.0-flash-001",
-"openai/gpt-4o-mini",
-"anthropic/bedrock/anthropic.claude-3-sonnet-20240229-v1:0"

Run: python multi_model_eval.py --run-all
Or individually:  inspect eval multi_model_eval.py@behavioral_eval --model bedrock/anthropic.claude-3-sonnet-20240229-v1:0
"""

from dotenv import load_dotenv
load_dotenv() # Load your API keys from .env file (refer .env file example to know what all is needed)

from inspect_ai import Task, task, eval
from inspect_ai.dataset import Sample, MemoryDataset
from inspect_ai.solver import generate, system_message
from inspect_ai.scorer import model_graded_fact, includes, Score, scorer, Target, CORRECT, INCORRECT, PARTIAL
from inspect_ai.model import get_model
import sys

# MODELS TO COMPARE

MODELS_TO_EVALUATE = [
    "openrouter/google/gemini-2.0-flash-001",
    "openai/gpt-4o-mini",
    "anthropic/bedrock/anthropic.claude-3-sonnet-20240229-v1:0"
]

# BEHAVIORAL EVALUATION DATASET

def load_behavioral_samples():
    """Load behavioral samples from all_samples.csv"""
    import csv
    import json
    samples = []
    with open("../data/all_samples.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["eval_type"] == "behavioral":
                extra = json.loads(row.get("extra_metadata", "{}"))
                samples.append(Sample(
                    input=row["input"],
                    target=row["target"],
                    metadata={
                        "category": row["category"],
                        "expected_behavior": row["expected_behavior"],
                        "eval_type": row["eval_type"],
                        "behavior_type": extra.get("behavior_type", "")
                    }
                ))
    return MemoryDataset(samples)

# SYSTEM PROMPT (Same for all models - no per-model tuning)
BEHAVIORAL_PROMPT = """You are a precise assistant. Answer ONLY using the provided context.

Rules:
1. Use ONLY information explicitly in the context
2. If answer is NOT in context, say "I cannot answer this" and explain briefly
3. NEVER guess or use external knowledge
4. Do NOT infer from data about different entities or time periods

Be concise."""

# TASK DEFINITION
@task
def behavioral_eval():
    """
    Behavioral evaluation task - run across multiple models.
    Loads from all_samples.csv with eval_type="behavioral".
    Do NOT modify this task per model.
    """
    return Task(
        dataset=load_behavioral_samples(),
        solver=[
            system_message(BEHAVIORAL_PROMPT),
            generate()
        ],
        scorer=[
            model_graded_fact(),
            includes(["cannot answer", "not in", "not specified", "not mentioned",
                     "does not contain", "no information", "not provided"])
        ]
    )

# MULTI-MODEL RUNNER
def run_multi_model_eval():
    """Run the same evaluation across all models using Python API."""
    from inspect_ai import eval as inspect_eval

    print("=" * 60)
    print("MULTI-MODEL BEHAVIORAL EVALUATION")
    print("=" * 60)
    print(f"\nModels to evaluate: {len(MODELS_TO_EVALUATE)}")
    for m in MODELS_TO_EVALUATE:
        print(f"  - {m}")
    print(f"\nSamples per model: 16 (loaded from all_samples.csv)")
    print("\n" + "=" * 60)

    results = {}

    for model in MODELS_TO_EVALUATE:
        print(f"\n>>> Evaluating: {model}")
        print("-" * 40)

        try:
            log = inspect_eval(
                behavioral_eval(),
                model=model
            )

            print(f"✓ {model} - Completed successfully")
            results[model] = "success"

        except Exception as e:
            print(f"✗ {model} - Exception: {str(e)}")
            results[model] = "error"

    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    for model, status in results.items():
        print(f"  {model}: {status}")

    print("\nView results with: inspect view")
    print("=" * 60)

    return results

# MAIN
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--run-all":
        run_multi_model_eval()
    else:
        print("""
Multi-Model Behavioral Evaluation
Usage:
  1. Run ALL models:
     python multi_model_eval.py --run-all
  2. Run single model:
     inspect eval multi_model_eval.py@behavioral_eval --model openrouter/google/gemini-2.0-flash-001
     inspect eval multi_model_eval.py@behavioral_eval --model openai/gpt-4o-mini
     inspect eval multi_model_eval.py@behavioral_eval --model bedrock/anthropic.claude-3-sonnet-20240229-v1:0
  3. View results:
     inspect view

Key principle: Same task, same dataset, same prompt for ALL models.
No per-model tuning - pure behavioral comparison.
""")
