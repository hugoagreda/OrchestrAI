# OrchestrAI — AI Execution Optimization Engine

OrchestrAI is a developer-facing API infrastructure that optimizes AI model execution across providers.

The system acts as an intelligent routing and governance layer between applications and model providers to make AI usage:

- cheaper
- easier to manage
- provider-agnostic
- observable and controllable

## Core Value

OrchestrAI optimizes each execution based on:

- task classification
- deterministic routing policies
- compute budget signals
- provider abstraction via adapters
- structured execution traces

## Supported Providers (initial)

- OpenAI
- Anthropic
- Google
- Mistral
- OpenRouter

Future support:

- local models
- enterprise/private endpoints
- self-hosted models

## Architectural Layers

- Identity
- Behavior
- Strategy
- Workflow
- ExecutionLayer
- CapabilityKernel
- CapabilityNamespace
- ExecutionContext

Routing and execution governance live inside `CapabilityKernel`.

## Minimal Runtime Flow

Application → OrchestrAI API → Task Classifier → Routing Engine → Policy/Budget Evaluation → Model Adapter → Model Provider → Execution Trace

## Development Philosophy

Early versions prioritize:

- simplicity
- modularity
- traceability
- low operational complexity

Avoid over-engineering. Validate value first through automatic model routing and cost optimization.

## Python Environment (venv)

Recommended setup (Windows):

1. Create virtual environment:
  - `py -m venv .venv`

2. Activate it:
  - PowerShell: `.\.venv\Scripts\Activate.ps1`
  - CMD: `.venv\Scripts\activate.bat`

3. Install dependencies:
  - `python -m pip install --upgrade pip`
  - `python -m pip install -r requirements.txt`

4. Deactivate when done:
  - `deactivate`


## Local Execution

- Runtime smoke test:
  - `python -m core.test_run`
- Unit tests:
  - `python -m unittest discover -s core/tests -p "test_*.py"`
