"""Build the standalone Champion Challenger assignment report."""
from pathlib import Path
import json

import pandas as pd
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"


def paragraph(doc, text, style=None):
    return doc.add_paragraph(str(text), style)


def table(doc, headers, rows):
    item = doc.add_table(rows=1, cols=len(headers))
    item.style = "Table Grid"
    for cell, value in zip(item.rows[0].cells, headers):
        cell.text = str(value)
        shade = OxmlElement("w:shd")
        shade.set(qn("w:fill"), "E7EEF4")
        cell._tc.get_or_add_tcPr().append(shade)
        for run in cell.paragraphs[0].runs:
            run.bold = True
    for values in rows:
        for cell, value in zip(item.add_row().cells, values):
            cell.text = str(value)
    for row in item.rows:
        row._tr.get_or_add_trPr().append(OxmlElement("w:cantSplit"))
        for cell in row.cells:
            for p in cell.paragraphs:
                for run in p.runs:
                    run.font.size = Pt(9)
    return item


def code(doc, text):
    for line in str(text).strip().splitlines():
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(line[:115])
        run.font.name = "Consolas"
        run.font.size = Pt(7.5)


def picture(doc, relative, caption, width=6.4):
    path = ROOT / relative
    if path.exists():
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(path), width=Inches(width))
        cap = doc.add_paragraph(caption)
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER


def main():
    result = json.loads((OUT / "metrics_summary.json").read_text(encoding="utf-8"))
    a = result["models"]["A"]["metrics"]
    b = result["models"]["B"]["metrics"]

    doc = Document()
    section = doc.sections[0]
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.top_margin = section.bottom_margin = Inches(0.7)
    section.left_margin = section.right_margin = Inches(0.75)
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(10.5)
    for name, size in [("Title", 24), ("Subtitle", 13), ("Heading 1", 17), ("Heading 2", 12)]:
        style = doc.styles[name]
        style.font.name = "Calibri"
        style.font.size = Pt(size)
        style.font.color.rgb = RGBColor(0, 0, 0)
    footer = section.footer.paragraphs[0]
    footer.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    footer.add_run("Champion Challenger Assignment | ")
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    footer._p.append(field)

    paragraph(doc, "Champion Challenger Model Comparison", "Title")
    paragraph(doc, "Hugging Face sentiment models tracked and registered with MLflow", "Subtitle")
    paragraph(doc, "Student name: ____________________________")
    paragraph(doc, "USN: ____________________________    Section: ________")
    paragraph(doc, "Repository name: <YOUR_USN>-mlflow-champion-challenger")
    paragraph(doc, "This report documents the complete individual mini project required by the supplied brief. The companion repository contains executable source, fixed evaluation data, recorded outputs, plots, screenshots, tests and reproduction instructions.")

    doc.add_heading("Task and models", 1)
    paragraph(doc, "Task: binary English sentiment classification on 60 fixed, balanced, labelled sentences. The same inputs and order are used for both models; eight separate sentences are reserved for alias-based inference.")
    table(doc, ["Role", "Hugging Face model ID", "Purpose"], [
        ["A current Champion", result["models"]["A"]["hf_model_id"], "Stronger DistilBERT baseline"],
        ["B Challenger", result["models"]["B"]["hf_model_id"], "Tiny model for speed and size trade-off"],
    ])

    doc.add_heading("Champion rule declared before the run", 1)
    paragraph(doc, "Primary metric: macro-F1, higher is better. Promote B only if B minus A is at least 0.01 and B's average latency is no more than five times A's. Otherwise A stays Champion, including ties and differences below the margin. Accuracy, precision, recall and F1 are higher-is-better; latency and model size are lower-is-better. The one percentage-point threshold avoids changing the production alias for a negligible gain.")

    doc.add_heading("Results and decision", 1)
    table(doc, ["Metric", "A", "B", "B minus A"], [
        [key, f"{a[key]:.6f}", f"{b[key]:.6f}", f"{b[key]-a[key]:+.6f}"] for key in a
    ])
    decision = (OUT / "results.md").read_text(encoding="utf-8").split("\n\n", 1)[1]
    paragraph(doc, decision)
    picture(doc, "outputs/comparison.png", "Comparison of every recorded metric")
    picture(doc, "outputs/A/confusion_matrix.png", "Model A confusion matrix", 4.2)
    picture(doc, "outputs/B/confusion_matrix.png", "Model B confusion matrix", 4.2)

    doc.add_heading("Qualitative error analysis", 1)
    disagreements = pd.read_csv(OUT / "disagreements.csv")
    qualitative = pd.read_csv(OUT / "qualitative_analysis.csv")
    rows = []
    for item in qualitative.itertuples():
        match = disagreements[disagreements.id == item.id].iloc[0]
        rows.append([item.id, match.reference, match.prediction_A, match.prediction_B, item.comment])
    table(doc, ["ID", "Reference", "A", "B", "Comment"], rows)

    doc.add_heading("MLflow tracking, model packaging and registry", 1)
    paragraph(doc, "evaluate.py creates a compare_sentiment parent run and one nested run per model. Each model run records the required run name, Hugging Face model ID, task, role, inference settings, sample count, seed, device, library versions, classification metrics, latency, parameter count, predictions, confusion matrix, requirements and README. The custom mlflow.pyfunc.PythonModel bundles the model and tokenizer and returns a DataFrame with text, prediction and confidence.")
    paragraph(doc, "register_champion.py reads the generated manifest rather than hard-coding run IDs. It registers both evaluated models under sentiment-model and assigns champion to the winner and challenger to the other version.")
    picture(doc, "screenshots/mlflow_compare.png", "MLflow compare view for the two evaluated model runs")
    picture(doc, "screenshots/registry_aliases.png", "Registered versions with Champion and Challenger aliases")

    doc.add_heading("Inference through the Champion alias", 1)
    paragraph(doc, "predict_from_mlflow.py loads models:/sentiment-model@champion. The script does not import or call a Hugging Face pipeline. It resolves the current version and model ID from registry metadata, predicts on eight new examples and writes outputs/new_data_predictions.csv.")
    code(doc, (OUT / "prediction_terminal.txt").read_text(encoding="utf-8"))
    picture(doc, "screenshots/prediction_terminal.png", "Verbatim Champion inference transcript rendered for readability")

    doc.add_heading("Repository contents and execution", 1)
    table(doc, ["Path", "Purpose"], [
        ["README.md", "Exact setup and run commands, rule, results and limitations"],
        ["evaluate.py", "Runs both candidates and logs metrics, artifacts and models"],
        ["register_champion.py", "Registers versions and assigns aliases"],
        ["predict_from_mlflow.py", "Loads the Champion alias and predicts new data"],
        ["data/", "Shared evaluation set and disjoint new inputs"],
        ["outputs/", "Predictions, metrics, plots, lab outputs and verification"],
        ["screenshots/", "MLflow comparison, registry and inference evidence"],
        ["tests/", "Rule, data, workflow, document and regression checks"],
        ["labs/", "All fourteen lab entry points and MLflow Project files"],
    ])
    code(doc, "python -m venv .venv\npython -m pip install -r requirements.txt\npython -m mlflow server --host 127.0.0.1 --port 5000\npython evaluate.py\npython register_champion.py\npython predict_from_mlflow.py\npython run_labs.py\npython -m pytest -q")

    doc.add_heading("Limitations and declaration", 1)
    paragraph(doc, "The evaluation set is small and was not randomly sampled from a target population. One changed prediction moves accuracy by about 1.67 percentage points. CPU latency depends on hardware, load and batching, and is not a production benchmark. Training overlap cannot be ruled out; confidence values are not calibrated probabilities. Both models can fail on sarcasm, mixed sentiment and domain shifts. A larger independently labelled deployment sample is required before production use.")
    paragraph(doc, "AI assistance declaration: OpenAI Codex was used to inspect the supplied project, correct portability and workflow issues, prepare the documents and verify the package. The submitter must review and understand every component and be ready to explain it in the viva.")
    paragraph(doc, "GitHub publication: create a repository named <YOUR_USN>-mlflow-champion-challenger, push the supplied repository contents with at least three commits, and add the instructor if it is private. No account publication or LMS submission is claimed in this report.")

    doc.add_heading("Verification summary", 1)
    table(doc, ["Check", "Recorded outcome"], [
        ["Shared input contract", "60 unique evaluation examples; balanced labels; 8 disjoint new examples"],
        ["Metric replay", "Accuracy, macro precision, macro recall and macro-F1 independently recalculated"],
        ["Model replay", "Both saved MLflow pyfunc models reproduce all recorded predictions"],
        ["Registry", "Champion and Challenger aliases resolve to the evaluated versions"],
        ["Alias inference", "Eight new examples predicted through models:/sentiment-model@champion"],
        ["Lab audit", "All 14 lab exercises have code, transcript evidence and recorded observations"],
        ["Repository hygiene", "Virtual environments, tracking databases, model weights and caches excluded"],
        ["Document review", "DOCX rendered page-by-page and inspected for clipping and broken layout"],
    ])
    paragraph(doc, "The screenshots and saved outputs are evidence from the supplied execution. On a fresh clone, run the commands in README.md to generate new MLflow run IDs and registry versions before using the live verification scripts.")

    doc.save(ROOT / "Champion_Challenger_Assignment_Report.docx")
    print("Built Champion_Challenger_Assignment_Report.docx")


if __name__ == "__main__":
    main()
