@app.route("/api/analyze", methods=["POST"])
def analyze_file():
    if "file" not in request.files:
        return jsonify({
            "status": "error",
            "message": "No dataset was uploaded."
        }), 400

    file = request.files["file"]

    try:
        if file.filename.lower().endswith(".csv"):
            df = pd.read_csv(file)
        elif file.filename.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(file)
        else:
            return jsonify({
                "status": "error",
                "message": "Only CSV and Excel files are supported."
            }), 400

        numeric = df.select_dtypes(include=np.number)

        result = {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "column_names": [str(x) for x in df.columns],
            "missing_values": {
                str(k): int(v)
                for k, v in df.isnull().sum().items()
                if v > 0
            },
            "duplicate_rows": int(df.duplicated().sum()),
            "numeric_columns": [str(x) for x in numeric.columns],
            "statistics": numeric.describe().round(2).to_dict(),
            "preview": df.head(10).fillna("").astype(str).to_dict("records")
        }

        return jsonify({
            "status": "success",
            "result": result
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400
