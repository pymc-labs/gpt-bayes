import os
import io
import datetime
import dill
import requests
import pandas as pd
import arviz as az
from flask import Flask, request, jsonify
from pymc_marketing.mmm import MMM, GeometricAdstock, LogisticSaturation
from google.cloud import storage
import logging

app = Flask(__name__)

# Bucket name should be provided via environment variable.
MODEL_BUCKET = os.environ.get("MODEL_BUCKET", "bayes-gpt-models")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/run_mmm', methods=['POST'])
def run_mmm():
    """
    Cloud Run function to fit an MMM model, upload the fitted model to Cloud Storage,
    and return the filename.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "failed", "error": "No JSON payload provided"}), 400

        # Extract file reference and download URL.
        file_refs = data.get("openaiFileIdRefs", [])
        if not file_refs:
            return jsonify({"status": "failed", "error": "No file references provided"}), 400
        
        download_link = file_refs[0].get("download_link", "")
        if not download_link:
            return jsonify({"status": "failed", "error": "Download link missing"}), 400

        logger.info("Downloading CSV from: %s", download_link)
        response = requests.get(download_link)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))

        # Extract model parameters.
        date_column = data.get("date_column", "date")
        channel_columns = data.get("channel_columns", [])
        adstock_max_lag = data.get("adstock_max_lag", 8)
        yearly_seasonality = data.get("yearly_seasonality", 2)
        y_column = data.get("y_column", "y")

        # Process the DataFrame.
        df[date_column] = pd.to_datetime(df[date_column])
        X = df.drop(y_column, axis=1)
        y = df[y_column].astype(float)

        # Fit the MMM model.
        logger.info("Fitting MMM model...")
        mmm = MMM(
            adstock=GeometricAdstock(l_max=adstock_max_lag),
            saturation=LogisticSaturation(),
            date_column=date_column,
            channel_columns=channel_columns,
            control_columns=None,
            yearly_seasonality=yearly_seasonality,
        )
        mmm.fit(X, y, nuts_sampler="numpyro")
        logger.info("MMM model fitting completed.")

        # (Optional) Create a summary using ArviZ for debugging.
        summary = (
            az.summary(
                mmm.fit_result,
                var_names=['alpha', 'beta', 'sigma', 'intercept', 'lam', 'gamma_control'],
                filter_vars="like"
            )
            .to_dict()
        )

        # Serialize the fitted model.
        serialized_model = dill.dumps(mmm)

        # Upload to Cloud Storage.
        storage_client = storage.Client()
        bucket = storage_client.bucket(MODEL_BUCKET)
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        model_filename = f"mmm_model_{timestamp}.pkl"
        blob = bucket.blob(model_filename)
        blob.upload_from_string(serialized_model, content_type="application/octet-stream")
        logger.info("Model uploaded as: %s", model_filename)

        # Return the model filename and optional summary.
        return jsonify({
            "status": "completed",
            "model_filename": model_filename,
            "summary": summary
        })

    except Exception as e:
        logger.exception("Error in MMM Cloud Run function")
        return jsonify({"status": "failed", "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
