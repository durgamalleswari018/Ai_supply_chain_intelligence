from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import os

app = Flask(__name__)
CORS(app)

app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

@app.route("/")
def home():
    return jsonify({
        "status": "success",
        "message": "SupplyIQ backend is running"
    })

@app.route("/api/health")
def health():
    return jsonify({
        "status": "healthy"
    })

def clean(value):
    if pd.isna(value):
        return None
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    return value

def read_file(file):
    name = file.filename.lower()

    if name.endswith(".csv"):
        return pd.read_csv(file)

    if name.endswith(".xlsx"):
        return pd.read_excel(file)

    if name.endswith(".xls"):
        return pd.read_excel(file)

    raise ValueError("Only CSV, XLSX and XLS files are supported.")

def analyze(df):

    df.columns = [str(c).strip() for c in df.columns]

    numeric = df.select_dtypes(include=np.number)
    categorical = df.select_dtypes(exclude=np.number)

    missing = {}
    for column in df.columns:
        count = int(df[column].isna().sum())
        if count > 0:
            missing[column] = count

    statistics = {}

    for column in numeric.columns:
        series = numeric[column].dropna()

        if len(series) > 0:
            statistics[column] = {
                "count": int(series.count()),
                "mean": round(float(series.mean()), 3),
                "median": round(float(series.median()), 3),
                "minimum": round(float(series.min()), 3),
                "maximum": round(float(series.max()), 3),
                "standard_deviation": round(float(series.std()), 3)
            }

    categories = {}

    for column in categorical.columns:
        values = df[column].astype(str).value_counts().head(10)

        categories[column] = {
            str(k): int(v)
            for k, v in values.items()
        }

    correlations = {}

    if len(numeric.columns) >= 2:
        corr = numeric.corr()

        for column in corr.columns:
            correlations[column] = {
                str(k): clean(v)
                for k, v in corr[column].items()
            }

    preview = []

    for row in df.head(10).to_dict(orient="records"):
        preview.append({
            str(k): clean(v)
            for k, v in row.items()
        })

    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": list(df.columns),
        "numeric_columns": list(numeric.columns),
        "categorical_columns": list(categorical.columns),
        "missing_values": missing,
        "duplicate_rows": int(df.duplicated().sum()),
        "statistics": statistics,
        "categories": categories,
        "correlations": correlations,
        "preview": preview
    }

@app.route("/api/analyze", methods=["POST"])
def analyze_file():

    if "file" not in request.files:
        return jsonify({
            "status": "error",
            "message": "No dataset was uploaded."
        }), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({
            "status": "error",
            "message": "Please select a dataset."
        }), 400

    try:

        df = read_file(file)

        if df.empty:
            return jsonify({
                "status": "error",
                "message": "The uploaded dataset is empty."
            }), 400

        result = analyze(df)

        result["analysis_type"] = request.form.get(
            "analysis",
            "overview"
        )

        result["question"] = request.form.get(
            "question",
            ""
        )

        result["language"] = request.form.get(
            "language",
            "en"
        )

        return jsonify({
            "status": "success",
            "result": result
        })

    except Exception as error:

        return jsonify({
            "status": "error",
            "message": str(error)
        }), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
