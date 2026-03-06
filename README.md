# OrchestrAI — Motor de Optimización de Ejecución de IA

OrchestrAI es una infraestructura API orientada a desarrolladores que optimiza la ejecución de modelos de IA entre múltiples proveedores.

El sistema actúa como una capa inteligente de enrutamiento y gobernanza entre aplicaciones y proveedores de modelos para que el uso de IA sea:

- más barato
- más fácil de gestionar
- agnóstico al proveedor
- observable y controlable

## Valor Principal

OrchestrAI optimiza cada ejecución en base a:

- clasificación de tareas
- políticas de enrutamiento deterministas
- señales de presupuesto de cómputo
- abstracción de proveedores mediante adaptadores
- trazas de ejecución estructuradas

## Proveedores Soportados (inicial)

- OpenAI
- Anthropic
- Google
- Mistral
- OpenRouter

Soporte futuro:

- modelos locales
- endpoints privados/empresariales
- modelos autoalojados

## Capas Arquitectónicas

- Identity
- Behavior
- Strategy
- Workflow
- ExecutionLayer
- CapabilityKernel
- CapabilityNamespace
- ExecutionContext

El enrutamiento y la gobernanza de ejecución viven dentro de `CapabilityKernel`.

## Flujo Mínimo de Runtime

Aplicación → API de OrchestrAI → Clasificador de Tarea → Motor de Enrutamiento → Evaluación de Política/Presupuesto → Adaptador de Modelo → Proveedor de Modelo → Traza de Ejecución

## Filosofía de Desarrollo

Las primeras versiones priorizan:

- simplicidad
- modularidad
- trazabilidad
- baja complejidad operativa

Evita la sobreingeniería. Primero valida valor con enrutamiento automático de modelos y optimización de costos.

## Entorno Python (venv)

1. Activar el venv:
  - PowerShell: `.\.venv\Scripts\Activate.ps1`
  - CMD: `.venv\Scripts\activate.bat`

2. Instalar dependencias:
  - `python -m pip install --upgrade pip`
  - `python -m pip install -r requirements.txt`

3. Desactivar al terminar:
  - `deactivate`

## Ejecución Local

- Prueba rápida de runtime:
  - `python -m core.test_run`
- Pruebas unitarias:
  - `python -m unittest discover -s core/tests -p "test_*.py"`
