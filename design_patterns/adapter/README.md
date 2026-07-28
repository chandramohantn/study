# Adapter Pattern — ML Inference Demo

## What This Demonstrates

The Adapter pattern wraps objects with **incompatible interfaces** so they can work with your system **without changing either side**.

In ML engineering, you constantly deal with:
- Different model frameworks (sklearn, PyTorch, ONNX, TF Serving)
- Different input formats (numpy arrays, JSON dicts, single vs batch)
- Different data sources (local files, S3, databases)

Each has a different interface. Your inference service shouldn't care.

## Structure

```
adapter/
├── README.md
├── src/
│   ├── __init__.py
│   ├── model_interface.py      # Protocol — the target interface
│   ├── adapters.py             # SklearnAdapter, DictInputAdapter, BatchAdapter
│   ├── data_source_interface.py # DataSource protocol + LocalFile/InMemory adapters
│   └── inference_service.py    # Client code that uses InferenceModel
└── tests/
    ├── __init__.py
    └── test_adapters.py        # Tests for all adapters
```

## Key Concepts

| Component | Role | File |
|-----------|------|------|
| **Target Interface** | What your system expects | `model_interface.py` → `InferenceModel` |
| **Adapter** | Translates incompatible → compatible | `adapters.py` → `SklearnAdapter`, etc. |
| **Adaptee** | The thing being wrapped (sklearn model, file system) | sklearn's `RandomForestClassifier`, numpy file I/O |
| **Client** | Uses the target interface, unaware of adapters | `inference_service.py` → `InferenceService` |

## Running

```bash
# From the adapter/ directory
cd /Users/etnxcha/Desktop/Projects/study/design_patterns/adapter

# Run the demo
python -m src.inference_service

# Run tests
pytest tests/ -v
```

## Dependencies

Only `numpy` and `scikit-learn` — no heavy frameworks needed for the demo.

```bash
pip install numpy scikit-learn pytest
```

## How the Adapters Work

### SklearnAdapter
Wraps any fitted sklearn estimator. Adds `model_name`, handles missing `predict_proba()`.

### DictInputAdapter
Accepts `{"feature_a": 1.0, ...}` input (like HTTP API payloads), converts to numpy array in the correct column order, then delegates to the wrapped model.

### BatchAdapter
Normalizes input shape: if a 1D vector arrives (single sample), reshapes to 2D, calls the model, and squeezes the output back. Transparent for batch input.

### LocalFileAdapter / InMemoryAdapter
Adapt different storage backends to a unified `DataSource` protocol for ETL pipelines.

## When You'd Extend This

In production, you'd add:
- `PyTorchAdapter` — calls `model.eval()`, converts numpy↔tensor, disables grad
- `ONNXAdapter` — wraps `onnxruntime.InferenceSession`
- `SageMakerAdapter` — serializes to JSON, calls `invoke_endpoint`, deserializes
- `S3Adapter` — adapts boto3 to the `DataSource` interface

Each new adapter = one new class. **Zero changes to InferenceService or ETL pipeline.**


