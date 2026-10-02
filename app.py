from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
import os

app = Flask(__name__)
CORS(app)

app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

TEXT = {
    "en": {
        "uploaded": "Dataset uploaded successfully.",
        "unsupported": "Please upload a CSV or Excel file.",
        "no_file": "Please upload a dataset.",
        "question": "Your question was received."
    },
    "te": {
        "uploaded": "డేటాసెట్ విజయవంతంగా అప్‌లోడ్ అయింది.",
        "unsupported": "దయచేసి CSV లేదా Excel ఫైల్‌ను అప్‌లోడ్ చేయండి.",
        "no_file": "దయచేసి డేటాసెట్‌ను అప్‌లోడ్ చేయండి.",
        "question": "మీ ప్రశ్న అందింది."
    },
    "hi": {
        "uploaded": "डेटासेट सफलतापूर्वक अपलोड हो गया।",
        "unsupported": "कृपया CSV या Excel फ़ाइल अपलोड करें।",
        "no_file": "कृपया डेटासेट अपलोड करें।",
        "question": "आपका प्रश्न प्राप्त हुआ।"
    },
    "ta": {
        "uploaded": "தரவுத்தொகுப்பு வெற்றிகரமாக பதிவேற்றப்பட்டது.",
        "unsupported": "CSV அல்லது Excel கோப்பை பதிவேற்றவும்.",
        "no_file": "தரவுத்தொகுப்பை பதிவேற்றவும்.",
        "question": "உங்கள் கேள்வி பெறப்பட்டது."
    },
    "kn": {
        "uploaded": "ಡೇಟಾಸೆಟ್ ಯಶಸ್ವಿಯಾಗಿ ಅಪ್‌ಲೋಡ್ ಆಗಿದೆ.",
        "unsupported": "ದಯವಿಟ್ಟು CSV ಅಥವಾ Excel ಫೈಲ್ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.",
        "no_file": "ದಯವಿಟ್ಟು ಡೇಟಾಸೆಟ್ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.",
        "question": "ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಸ್ವೀಕರಿಸಲಾಗಿದೆ."
    },
    "ml": {
        "uploaded": "ഡാറ്റാസെറ്റ് വിജയകരമായി അപ്‌ലോഡ് ചെയ്തു.",
        "unsupported": "CSV അല്ലെങ്കിൽ Excel ഫയൽ അപ്‌ലോഡ് ചെയ്യുക.",
        "no_file": "ഡാറ്റാസെറ്റ് അപ്‌ലോഡ് ചെയ്യുക.",
        "question": "നിങ്ങളുടെ ചോദ്യം ലഭിച്ചു."
    }
}


def clean_value(value):
    if pd.isna(value):
        return None

    if isinstance(value, np.integer):
        return int(value)

    if isinstance(value, np.floating):
        return float(value)

    return value


def load_dataset(file):
    filename = file.filename.lower()

    if filename.endswith(".csv"):
        return pd.read_csv(file)

    if filename.endswith(".xlsx") or filename.endswith(".xls"):
        return pd.read_excel(file)

    return None


def analyze_dataset(df):

    numeric = df.select_dtypes(include=np.number)

    categorical = df.select_dtypes(exclude=np.number)

    missing = df.isnull().sum()

    missing = {
        str(column): int(value)
        for column, value in missing.items()
        if value > 0
    }

    duplicates = int(df.duplicated().sum())

    statistics = {}

    if not numeric.empty:

        description = numeric.describe().round(3)

        statistics = {
            str(column): {
                str(index): clean_value(value)
                for index, value in description[column].items()
            }
            for column in description.columns
        }

    category_summary = {}

    for column in categorical.columns[:15]:

        counts = (
            df[column]
            .astype(str)
            .value_counts()
            .head(10)
        )

        category_summary[str(column)] = {
            str(key): int(value)
            for key, value in counts.items()
        }

    correlations = {}

    if numeric.shape[1] >= 2:

        correlation_matrix = numeric.corr().round(3)

        for column in correlation_matrix.columns:

            correlations[str(column)] = {
                str(key): clean_value(value)
                for key, value in correlation_matrix[column].items()
            }

    preview = []

    for row in df.head(10).to_dict(orient="records"):

        preview.append({
            str(key): clean_value(value)
            for key, value in row.items()
        })

    return {
        "rows": int(df.shape[0]),
        "columns": int(df.shape[1]),
        "column_names": [
            str(column)
            for column in df.columns
        ],
        "numeric_columns": [
            str(column)
            for column in numeric.columns
        ],
        "categorical_columns": [
            str(column)
            for column in categorical.columns
        ],
        "missing_values": missing,
        "duplicate_rows": duplicates,
        "statistics": statistics,
        "category_summary": category_summary,
        "correlations": correlations,
        "preview": preview
    }


@app.route("/")
def home():

    return jsonify({
        "status": "success",
        "message": "SupplyIQ AI Dataset Intelligence API is running."
    })


@app.route("/api/health")
def health():

    return jsonify({
        "status": "healthy"
    })


@app.route("/api/analyze", methods=["POST"])
def analyze():

    language = request.form.get("language", "en")

    if language not in TEXT:
        language = "en"

    file = request.files.get("file")

    analysis_type = request.form.get(
        "analysis",
        "overview"
    )

    question = request.form.get(
        "question",
        ""
    ).strip()

    if not file:

        return jsonify({
            "status": "error",
            "message": TEXT[language]["no_file"]
        }), 400

    try:

        df = load_dataset(file)

    except Exception as error:

        return jsonify({
            "status": "error",
            "message": f"Could not read the dataset: {str(error)}"
        }), 400

    if df is None:

        return jsonify({
            "status": "error",
            "message": TEXT[language]["unsupported"]
        }), 400

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    result = analyze_dataset(df)

    if analysis_type == "missing":

        result["focus"] = {
            "type": "missing_values",
            "data": result["missing_values"]
        }

    elif analysis_type == "statistics":

        result["focus"] = {
            "type": "statistics",
            "data": result["statistics"]
        }

    elif analysis_type == "correlation":

        result["focus"] = {
            "type": "correlation",
            "data": result["correlations"]
        }

    elif analysis_type == "categories":

        result["focus"] = {
            "type": "categories",
            "data": result["category_summary"]
        }

    else:

        result["focus"] = {
            "type": "overview",
            "data": {
                "rows": result["rows"],
                "columns": result["columns"],
                "numeric_columns": len(
                    result["numeric_columns"]
                ),
                "categorical_columns": len(
                    result["categorical_columns"]
                ),
                "missing_columns": len(
                    result["missing_values"]
                ),
                "duplicate_rows": result["duplicate_rows"]
            }
        }

    result["question"] = question

    if question:

        result["message"] = TEXT[language]["question"]

    else:

        result["message"] = TEXT[language]["uploaded"]

    result["language"] = language

    return jsonify({
        "status": "success",
        "result": result
    })


if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port
)
