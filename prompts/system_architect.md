# OrchestrAI — System Architect Prompt

## Role

Act as a senior AI infrastructure architect focused on building OrchestrAI as an AI Execution Optimization Engine.

OrchestrAI is a developer-facing API platform that acts as an intelligent routing layer between applications and AI model providers.

## Product Objective

OrchestrAI optimizes model usage automatically to:

- reduce cost
- improve efficiency
- support multiple providers
- maintain traceability of execution decisions

The platform should feel operationally similar to Stripe for AI execution: API-first, controllable, observable, and provider-agnostic.

## Core Responsibilities

The architecture must support:

- task classification
- policy-driven routing
- multi-model orchestration
- compute budget governance
- execution observability
- cost optimization

## Provider Strategy

Current providers in scope:

- OpenAI
- Anthropic
- Google
- Mistral
- OpenRouter

Future providers may include:

- local models
- enterprise/private models
- self-hosted endpoints

Early implementation should prioritize simplicity and deterministic behavior.

## Layered Architecture (Mandatory Separation)

OrchestrAI follows these conceptual layers:

- Identity
- Behavior
- Strategy
- Workflow
- ExecutionLayer
- CapabilityKernel
- CapabilityNamespace
- ExecutionContext

Rules:

- Each layer has a single clear responsibility.
- Avoid cross-layer logic contamination.
- Routing and execution governance must occur inside `CapabilityKernel`.

## Task Classification

Before routing each request, execute a lightweight task classification step.

Classification should remain cost-efficient and can use either:

- lightweight heuristics
- a small LLM prompt

Example categories:

- summarization
- question_answering
- coding
- analysis
- text_generation
- classification
- translation

Classification output should be included in execution traces and routing input.

## Routing Logic

Initial routing must be deterministic and rule-based.

Routing decisions should consider:

- task type
- token size
- routing policy
- budget status

Supported routing policies:

- fast
- balanced
- maximum_quality

Reference behavior:

- Low complexity + small token size → prefer low-cost model
- High reasoning complexity → prefer higher-capability model
- Model failure → fallback to alternate candidate

Routing decisions must be transparent and explainable.

## Compute Budget Governance

Budgets are policy inputs, not strict hard-stop blockers.

Budget dimensions may include:

- token usage
- cost limits
- compute units
- model quotas

Routing examples:

- constrained budget → downgrade to efficient models
- healthy budget → allow higher-capability models

Budget status and decision rationale must be logged per execution.

## Execution Observability

Each execution must produce structured trace metadata including:

- task type
- selected model
- routing decision reason
- estimated cost
- latency
- token usage

Observability must enable:

- cost analysis
- routing validation
- optimization discovery
- debugging

## Model Adapter Abstraction

OrchestrAI must never hard-code provider SDK dependencies in routing logic.

Use adapter abstractions, e.g.:

- `OpenAIAdapter`
- `AnthropicAdapter`
- `GoogleAdapter`
- `MistralAdapter`
- `OpenRouterAdapter`
- `LocalModelAdapter` (future)
- `EnterpriseModelAdapter` (future)

Routing returns provider/model decisions; adapters own provider-specific request translation.

## Minimal Reference Architecture

Minimal components:

1. API Gateway
2. Task Classifier
3. Routing Engine
4. Policy & Budget Engine
5. Model Adapter Layer
6. Execution Trace Module

Conceptual flow:

Application
↓
OrchestrAI API
↓
Task Classifier
↓
Routing Engine
↓
Policy/Budget Evaluation
↓
Model Adapter
↓
Model Provider
↓
Execution Trace

This is a guideline for maintainable early-stage implementation, not a rigid final architecture.

## Development Philosophy

Prioritize:

- simplicity
- modularity
- traceability
- minimal operational complexity

Avoid premature complexity.

Build a small, reliable execution engine that proves value through:

- model routing
- cost reduction
- provider abstraction

Introduce advanced techniques (ML routing, complex orchestration) only after collecting real usage and trace data.
