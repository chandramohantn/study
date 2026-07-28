# Adapter Pattern

## The One-Line Summary

**You have something that DOESN'T fit your interface. Wrap it to make it fit — without changing either side.**

---

## The Problem

You've built your ML inference service. It expects models to have a `predict(features)` method. It works great with sklearn.

Then your team says: "We need to serve a PyTorch model too." PyTorch models don't have `predict()`. They have `forward()`. They expect `torch.Tensor`, not `numpy.ndarray`. They need `model.eval()` and `torch.no_grad()`.

You can't change PyTorch. You can't change your inference service. You need something in between.

```python
# Your system expects THIS interface:
class InferenceModel(Protocol):
    def predict(self, features: np.ndarray) -> np.ndarray: ...

# But PyTorch models look like THIS:
# model(torch.FloatTensor(data))  ← completely different!

# And ONNX models look like THIS:
# session.run(None, {"input": data.astype(np.float32)})  ← also different!

# And a remote SageMaker endpoint looks like THIS:
# client.invoke_endpoint(Body=json.dumps(data))  ← ALSO different!
```

**Without Adapter, your inference service becomes a mess of if/else:**

```python
# ❌ WITHOUT ADAPTER

class InferenceService:
    def predict(self, features, model_type: str):
        if model_type == "sklearn":
            return self.model.predict(features)
        elif model_type == "pytorch":
            import torch
            with torch.no_grad():
                tensor = torch.FloatTensor(features)
                output = self.model(tensor)
                return output.numpy()
        elif model_type == "onnx":
            return self.session.run(None, {"input": features.astype(np.float32)})[0]
        elif model_type == "sagemaker":
            import json, boto3
            response = boto3.client("sagemaker-runtime").invoke_endpoint(
                EndpointName=self.endpoint,
                Body=json.dumps(features.tolist()),
            )
            return np.array(json.loads(response["Body"].read()))
```

---

## How Adapter Solves It

Each incompatible thing gets a **wrapper (adapter)** that translates its interface to yours:

```python
from typing import Protocol
import numpy as np


# ─── YOUR interface (what your system expects) ───

class InferenceModel(Protocol):
    """Every model must look like this to your system."""
    def predict(self, features: np.ndarray) -> np.ndarray: ...


# ─── ADAPTERS: each wraps a different "shape" ───

class SklearnAdapter:
    """Sklearn already matches — minimal adaptation needed."""
    def __init__(self, model):
        self._model = model

    def predict(self, features: np.ndarray) -> np.ndarray:
        return self._model.predict(features)


class PyTorchAdapter:
    """TRANSLATES: numpy → tensor, forward() → predict(), grad off."""
    def __init__(self, model, device: str = "cpu"):
        import torch
        self._model = model
        self._model.eval()
        self._device = device

    def predict(self, features: np.ndarray) -> np.ndarray:
        import torch
        with torch.no_grad():
            tensor = torch.FloatTensor(features).to(self._device)
            output = self._model(tensor)  # forward()
            return output.argmax(dim=1).cpu().numpy()


class ONNXAdapter:
    """TRANSLATES: session.run() → predict(), handles input naming."""
    def __init__(self, model_path: str):
        import onnxruntime as ort
        self._session = ort.InferenceSession(model_path)
        self._input_name = self._session.get_inputs()[0].name

    def predict(self, features: np.ndarray) -> np.ndarray:
        features = features.astype(np.float32)
        outputs = self._session.run(None, {self._input_name: features})
        return outputs[0]


class SageMakerAdapter:
    """TRANSLATES: HTTP API → predict(), handles serialization."""
    def __init__(self, endpoint_name: str):
        import boto3
        self._client = boto3.client("sagemaker-runtime")
        self._endpoint = endpoint_name

    def predict(self, features: np.ndarray) -> np.ndarray:
        import json
        response = self._client.invoke_endpoint(
            EndpointName=self._endpoint,
            ContentType="application/json",
            Body=json.dumps({"instances": features.tolist()}),
        )
        result = json.loads(response["Body"].read())
        return np.array(result["predictions"])


# ─── Your service is clean — works with ANY adapted model ───

class InferenceService:
    def __init__(self, model: InferenceModel):
        self.model = model  # Doesn't know or care what's behind the adapter

    def predict(self, features: np.ndarray) -> dict:
        predictions = self.model.predict(features)
        return {"predictions": predictions.tolist()}


# Usage:
service = InferenceService(model=PyTorchAdapter(pytorch_model, device="cuda"))
service = InferenceService(model=ONNXAdapter("model.onnx"))
service = InferenceService(model=SageMakerAdapter("my-endpoint"))
```

---

## Key Difference from Strategy

| | Strategy | Adapter |
|---|---|---|
| **You built it** | Yes — all strategies were designed BY YOU | No — the adaptee (PyTorch, ONNX, etc.) was built by SOMEONE ELSE |
| **Interface match** | All strategies match the interface FROM THE START | The adaptee has a DIFFERENT interface |
| **Purpose** | CHOOSE between alternatives | BRIDGE an incompatibility |
| **Without the pattern** | If/else to select algorithm | If/else to handle different shapes |
| **Adding a new one** | Write new strategy (matches interface) | Write new adapter (translates interface) |

### The Mental Test

Ask: **"Does the thing I'm wrapping already have the interface I need?"**

- **YES** → You're choosing between alternatives = **Strategy**
- **NO** → You're bridging an incompatibility = **Adapter**

```python
# STRATEGY: You wrote StandardScaler to have fit_transform(). 
# You wrote RobustScaler to have fit_transform(). Same interface by design.

# ADAPTER: PyTorch's forward(tensor) doesn't match your predict(numpy).
# TensorFlow's model.signatures["serving_default"](tf_constant) doesn't match either.
# You ADAPT them to fit.
```

---

## When to Use Adapter

- Integrating a third-party library that doesn't match your interface
- Supporting multiple model formats (sklearn, PyTorch, ONNX, TF)
- Reading from different data sources (S3, GCS, local, database)
- Consuming different API response formats
- Migrating from one library to another (old ↔ new interface)

---

## Real-World ML Example: Data Source Adapters

```python
from typing import Protocol
import pandas as pd
from pathlib import Path


class DataSource(Protocol):
    """YOUR interface — all data sources must look like this."""
    def read(self, location: str) -> pd.DataFrame: ...
    def write(self, df: pd.DataFrame, location: str) -> None: ...


class LocalFileAdapter:
    """Adapts filesystem operations to DataSource interface."""

    def read(self, location: str) -> pd.DataFrame:
        path = Path(location)
        if path.suffix == ".csv":
            return pd.read_csv(path)
        elif path.suffix == ".parquet":
            return pd.read_parquet(path)
        raise ValueError(f"Unsupported format: {path.suffix}")

    def write(self, df: pd.DataFrame, location: str) -> None:
        path = Path(location)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".csv":
            df.to_csv(path, index=False)
        elif path.suffix == ".parquet":
            df.to_parquet(path, index=False)


class S3Adapter:
    """Adapts boto3 S3 operations to DataSource interface."""

    def __init__(self, bucket: str):
        import boto3
        self._s3 = boto3.client("s3")
        self._bucket = bucket

    def read(self, location: str) -> pd.DataFrame:
        import io
        response = self._s3.get_object(Bucket=self._bucket, Key=location)
        body = response["Body"].read()
        if location.endswith(".csv"):
            return pd.read_csv(io.BytesIO(body))
        elif location.endswith(".parquet"):
            return pd.read_parquet(io.BytesIO(body))
        raise ValueError(f"Unsupported: {location}")

    def write(self, df: pd.DataFrame, location: str) -> None:
        import io
        buffer = io.BytesIO()
        if location.endswith(".csv"):
            df.to_csv(buffer, index=False)
        elif location.endswith(".parquet"):
            df.to_parquet(buffer, index=False)
        buffer.seek(0)
        self._s3.put_object(Bucket=self._bucket, Key=location, Body=buffer.getvalue())


class BigQueryAdapter:
    """Adapts BigQuery client to DataSource interface.
    Note: BigQuery uses SQL queries, not file paths — adapter translates the concept."""

    def __init__(self, project: str):
        from google.cloud import bigquery
        self._client = bigquery.Client(project=project)

    def read(self, location: str) -> pd.DataFrame:
        # 'location' here is a table name like 'dataset.table'
        query = f"SELECT * FROM `{location}`"
        return self._client.query(query).to_dataframe()

    def write(self, df: pd.DataFrame, location: str) -> None:
        job = self._client.load_table_from_dataframe(df, location)
        job.result()  # Wait for completion


# ─── Your ETL pipeline works identically regardless of where data lives ───

class ETLPipeline:
    def __init__(self, source: DataSource, sink: DataSource):
        self.source = source
        self.sink = sink

    def run(self, input_path: str, output_path: str, transform_fn) -> None:
        df = self.source.read(input_path)
        df = transform_fn(df)
        self.sink.write(df, output_path)


# Local development
pipeline = ETLPipeline(
    source=LocalFileAdapter(),
    sink=LocalFileAdapter(),
)
# pipeline.run("data/raw.csv", "data/processed.parquet", my_transform)

# Production
# pipeline = ETLPipeline(
#     source=S3Adapter(bucket="data-lake-raw"),
#     sink=BigQueryAdapter(project="my-gcp-project"),
# )
# pipeline.run("users/2024-01-15/data.parquet", "analytics.clean_users", my_transform)
```

---

## Another Common Use Case: LLM Provider Adapters

```python
from typing import Protocol
from dataclasses import dataclass


@dataclass
class LLMResponse:
    text: str
    tokens_used: int
    model: str


class LLMProvider(Protocol):
    """Your interface — all LLM providers must look like this."""
    def generate(self, prompt: str, max_tokens: int = 500) -> LLMResponse: ...


class OpenAIAdapter:
    """Adapts OpenAI's client to your LLMProvider interface."""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        from openai import OpenAI
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate(self, prompt: str, max_tokens: int = 500) -> LLMResponse:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
        )
        return LLMResponse(
            text=response.choices[0].message.content,
            tokens_used=response.usage.total_tokens,
            model=self._model,
        )


class AnthropicAdapter:
    """Adapts Anthropic's client to your LLMProvider interface."""

    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        from anthropic import Anthropic
        self._client = Anthropic(api_key=api_key)
        self._model = model

    def generate(self, prompt: str, max_tokens: int = 500) -> LLMResponse:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return LLMResponse(
            text=response.content[0].text,
            tokens_used=response.usage.input_tokens + response.usage.output_tokens,
            model=self._model,
        )


class LocalLlamaAdapter:
    """Adapts a local llama.cpp model to your LLMProvider interface."""

    def __init__(self, model_path: str):
        from llama_cpp import Llama
        self._model = Llama(model_path=model_path)

    def generate(self, prompt: str, max_tokens: int = 500) -> LLMResponse:
        output = self._model(prompt, max_tokens=max_tokens)
        return LLMResponse(
            text=output["choices"][0]["text"],
            tokens_used=output["usage"]["total_tokens"],
            model="local-llama",
        )


# Your service doesn't know which provider it's using
class TextSummarizer:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    def summarize(self, text: str) -> str:
        response = self.llm.generate(
            prompt=f"Summarize this in 2 sentences:\n\n{text}",
            max_tokens=100,
        )
        return response.text


# Swap providers without changing TextSummarizer
summarizer = TextSummarizer(llm=OpenAIAdapter(api_key="..."))
summarizer = TextSummarizer(llm=AnthropicAdapter(api_key="..."))
summarizer = TextSummarizer(llm=LocalLlamaAdapter(model_path="./model.gguf"))
```

---

## Summary

```
ADAPTER answers: "How do I make X work with my system when X has a different interface?"

You can't change X (third-party, legacy, different team).
You can't change your system (existing code depends on your interface).
Solution: Write a thin wrapper that TRANSLATES between the two.

                  YOUR CODE                    ADAPTER                   THIRD-PARTY
            ┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
            │                  │       │                  │       │                  │
            │  predict(numpy)  │──────►│  predict(numpy)  │──────►│  forward(tensor) │
            │                  │       │     translates   │       │                  │
            └──────────────────┘       └──────────────────┘       └──────────────────┘
                Calls predict()         Converts numpy→tensor        PyTorch's interface
                                        Calls forward()
                                        Converts tensor→numpy
                                        Returns numpy
```


---

## Working Implementation

The full runnable implementation lives in `design_patterns/adapter/`:

```
adapter/
├── README.md                       # Pattern explanation in context
├── src/
│   ├── __init__.py
│   ├── model_interface.py          # InferenceModel Protocol (target interface)
│   ├── adapters.py                 # SklearnAdapter, DictInputAdapter, BatchAdapter
│   ├── data_source_interface.py    # DataSource Protocol + LocalFileAdapter + InMemoryAdapter
│   └── inference_service.py        # Client service + runnable demo
└── tests/
    ├── __init__.py
    └── test_adapters.py            # 28 tests covering all adapters
```

### Quick Start

```bash
cd design_patterns/adapter
python3 -m venv .venv && source .venv/bin/activate
pip install numpy scikit-learn pytest

# Run the demo
python -m src.inference_service

# Run tests
pytest tests/ -v
```

### What Each Adapter Demonstrates

| Adapter | Incompatibility Solved | Real-World Equivalent |
|---------|----------------------|----------------------|
| `SklearnAdapter` | Adds model_name, uniform error handling | Wrapping any sklearn model for serving |
| `DictInputAdapter` | JSON dict → numpy array translation | API endpoint receiving feature dicts |
| `BatchAdapter` | 1D single sample → 2D batch normalization | Single-request vs batch-request handling |
| `LocalFileAdapter` | File I/O → DataSource protocol | Reading from local disk in ETL |
| `InMemoryAdapter` | In-memory dict → DataSource protocol | Test doubles for data pipelines |
