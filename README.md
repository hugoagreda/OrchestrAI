# OrchestrAI — Multi-Agent Identity & Automation Engine 🚀

## 📌 Finalidad del proyecto (explicado simple)

OrchestrAI nace para que cualquier empresa pueda crear y operar agentes de IA de forma fácil, sin tener que construir flujos técnicos complejos a mano.

La idea es simple:

- cada equipo define **qué quiere conseguir**,
- conecta sus APIs/sistemas,
- y OrchestrAI organiza automáticamente la ejecución usando el mejor modelo de IA para cada tarea.

El proyecto está pensado para **integrarse** con los sistemas internos de la empresa, no para sustituirlos por completo.

Además, la plataforma está orientada a un modelo **non-custodial**: por defecto no busca almacenar datos empresariales sensibles, y cada empresa mantiene la responsabilidad sobre sus datos y cumplimiento.

En resumen: OrchestrAI es una capa de orquestación para convertir objetivos de negocio en ejecuciones de IA gobernadas, trazables y escalables.

## 🧠 Visión

OrchestrAI es una infraestructura multiagente diseñada para orquestar modelos de inteligencia artificial, agentes especializados y pipelines automatizados con el objetivo de construir **entidades digitales personalizables** y sistemas autónomos adaptados a empresas.

Este proyecto **no está enfocado únicamente a crear influencers o personajes**, sino a desarrollar un **motor técnico modular** capaz de:

- Orquestar múltiples agentes y modelos IA.
- Construir identidades digitales desde cero (realistas, estilizadas o corporativas).
- Automatizar flujos de contenido y comunicación.
- Adaptarse a diferentes sectores empresariales mediante configuraciones personalizadas.
- Servir como base para soluciones B2C (laboratorio propio) y B2B (infraestructura para empresas).

---

## 🎯 Objetivos del Proyecto

### 1️⃣ Infraestructura Multiagente

Diseñar un sistema distribuido donde distintos agentes colaboren dentro de un flujo estructurado:

- **Strategist Agent** → define objetivos y narrativa.
- **Behavior Agent** → interpreta directrices del usuario o empresa.
- **Media Agent** → genera imagen, vídeo o audio.
- **Editor Agent** → adapta formato y coherencia visual.
- **Publishing Agent** → automatiza acciones y despliegue.
- **Analytics Agent** → analiza métricas y alimenta el feedback loop.

El sistema no impone un tipo de identidad específica: cada usuario o empresa define sus propias reglas.

---

### 2️⃣ Casos de Uso

#### 🔵 Laboratorio interno (B2C)

Espacio experimental para validar:

- pipelines multiagente
- coherencia narrativa
- evolución de identidades digitales

Funciona como prueba pública del motor OrchestrAI.

#### 🟣 Infraestructura empresarial (B2B)

Sistema adaptable que permite a empresas:

- diseñar entidades digitales personalizadas
- definir comportamiento y objetivos
- automatizar comunicación y contenido

El foco no es solo marketing; el sistema busca adaptarse a múltiples industrias.

---

### 3️⃣ Filosofía Técnica

OrchestrAI no pretende reemplazar programadores.

Busca redefinir el rol técnico hacia:

- Arquitectura de sistemas IA
- Orquestación modular
- Supervisión humana constante
- Diseño responsable de identidades digitales

Todo output generado por IA debe pasar por pipelines estructurados y revisables.

---

## ⚙️ Arquitectura (alto nivel)

Orquestador central:

- n8n + API backend modular

Flujo base:

- Entity → Planner → Strategy → Workflow → ExecutionLayer → CapabilityKernel → ExecutionContext

---

## Capability Manifest Schema (v1)

Cada namespace de capacidad debe incluir un archivo `capability.yaml` con este contrato mínimo:

```yaml
namespace: content
version: "1.0.0"
description: "Descripción de la capacidad"

actions:
	action_name:
		description: "Qué hace la acción"
		handler: "module_name.function_name"
		required_payload: []
		provides_context: []

governance:
	isolation_level: "high|medium|low"
	allow_external_calls: true
```

### Reglas validadas por el Kernel

- `namespace` debe ser `string` no vacío.
- `actions` debe ser `map` no vacío.
- Cada acción debe definir `handler` con formato `module.function`.
- `required_payload` debe ser lista.

Si un manifiesto no cumple este contrato, el Kernel falla en boot con excepción de validación.

### Capabilities disponibles actualmente

- `content`
- `media`
- `publishing`
- `analytics`

### Ejecución de pruebas

- Runtime smoke test:
	- `python -m core.test_run`
- Unit tests:
	- `python -m unittest discover -s core/tests -p "test_*.py"`

### Priority 3 Runtime Features

- Handler cache metrics expuestas por Kernel:
	- `hits`, `misses`, `size`
- Ruta async-ready en Execution Layer y Kernel:
	- `ExecutionLayer.execute_async(...)`
	- `CapabilityKernel.execute_async(...)`
- Profiling opcional por ejecución:
	- `enable_profiling=True`
	- métricas: `pipeline_duration_ms`, `avg_step_duration_ms`, `slowest_step`
