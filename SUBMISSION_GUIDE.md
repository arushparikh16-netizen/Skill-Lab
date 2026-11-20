# Final submission guide

## Files to use

| File | Purpose |
|---|---|
| MLflow_Lab_Book_Completed.docx | Completed editable lab record covering the mini project and Labs 01 through 14 |
| Champion_Challenger_Assignment_Report.docx | Standalone assignment report with results, plots and MLflow evidence |
| MLflow_Champion_Challenger_Repository.zip | Clean runnable repository archive |

## Fill these fields before submission

1. Enter your name, USN, section, course title and course code in `student.json`.
2. Run `python build_documents.py` and visually check the regenerated Word files.
3. Name the GitHub repository `<YOUR_USN>-mlflow-champion-challenger`.
4. Commit and push the repository. If it is private, add the instructor as a collaborator.
5. Submit the GitHub URL on the LMS and keep the receipt.

## Reproduce the execution

Follow `README.md` in order. Create a virtual environment, install the constrained
dependencies, start the MLflow server, then run `evaluate.py`,
`register_champion.py`, `predict_from_mlflow.py` and `run_labs.py`. Finally run
the tests, `verify_submission.py` and `audit_labs.py`.

Tracking databases, environments, cached model weights and raw artifact stores are
excluded from the repository. Saved outputs and screenshots document the supplied
execution; a fresh run creates new run IDs and registry versions.

## What is already included

- Both models evaluated on identical saved inputs.
- Macro-F1 decision rule with a one-point promotion margin and latency guardrail.
- Predictions, metrics, confusion matrices, comparison chart and qualitative errors.
- MLflow model packages, registry and alias code, and Champion alias inference.
- Eight disjoint new-data predictions.
- Code, output evidence and observations for all fourteen labs.
- Tests, reproducibility instructions and an AI-assistance declaration.

No GitHub publication, collaborator invitation or LMS submission is claimed by the
local package. Those steps require the submitter's account and identity.
