"""Integration test for the full data processing and prediction pipeline."""
import pandas as pd

from src.data_processing.pipeline import process_data
from src.models.predictor import make_prediction


def test_full_pipeline_returns_predictions():
    """Test that the full pipeline returns predictions for all input rows."""
    # Simulate raw input data
    raw_data = pd.DataFrame({"feature1": [1, 2], "feature2": [3, 4]})
    processed = process_data(raw_data)
    predictions = make_prediction(processed)
    assert len(predictions) == len(raw_data)
