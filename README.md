<!-- Summary: Provides project overview, setup steps, and usage instructions for OrchestrAI. -->
# OrchestrAI — AI Execution Optimization API

OrchestrAI es una API que reduce automáticamente el coste de usar modelos de inteligencia artificial seleccionando el modelo óptimo para cada petición.

En lugar de utilizar siempre el mismo modelo (y pagar de más), OrchestrAI actúa como una capa intermedia inteligente que decide cómo ejecutar cada solicitud de la forma más eficiente posible.

---

## 🚀 Qué hace OrchestrAI

OrchestrAI se integra en sistemas existentes de IA y:

* reduce el coste de ejecución automáticamente
* selecciona el modelo más adecuado en cada petición
* permite usar múltiples proveedores sin complejidad
* añade trazabilidad y control sobre el uso de IA

Todo esto **sin necesidad de modificar la arquitectura del sistema existente**.

---

## 💡 Problema

Las empresas que usan IA hoy:

* utilizan modelos caros para tareas simples
* no tienen control real sobre el gasto
* dependen de un único proveedor
* no saben si están usando la IA de forma eficiente

Resultado:

**están pagando más de lo necesario sin saberlo.**

---

## ✅ Solución

OrchestrAI introduce una capa de optimización entre la aplicación y los modelos.

Flujo:

Aplicación
→ OrchestrAI
→ Modelo óptimo
→ Respuesta

El sistema decide automáticamente:

* qué modelo utilizar
* cuándo usar uno más barato
* cuándo escalar a uno más potente
* cómo equilibrar coste, latencia y calidad

---

## 🧠 Ejemplo

### Sin OrchestrAI

Aplicación → GPT-4 → respuesta
(Coste alto en todas las peticiones)

---

### Con OrchestrAI

Aplicación → OrchestrAI → modelo óptimo → respuesta

* tareas simples → modelo barato
* tareas complejas → modelo avanzado

Resultado:

**menor coste sin perder calidad.**

---

## ⚙️ Cómo funciona

Cada petición sigue este flujo:

Aplicación
→ API de OrchestrAI
→ Clasificador de tarea
→ Motor de enrutamiento
→ Evaluación de política / presupuesto
→ Adaptador de modelo
→ Proveedor de modelo
→ Traza de ejecución

---

## 🧩 Valor Principal

OrchestrAI optimiza cada ejecución en base a:

* clasificación de tareas
* políticas de enrutamiento deterministas
* señales de presupuesto de cómputo
* abstracción de proveedores mediante adaptadores
* trazas de ejecución estructuradas

---

## 🔌 Proveedores Soportados (inicial)

* OpenAI
* Anthropic
* Google
* Mistral
* OpenRouter

Soporte futuro:

* modelos locales
* endpoints privados / empresariales
* modelos autoalojados

---

## 🏗️ Capas Arquitectónicas

OrchestrAI sigue una arquitectura por capas:

* Identity
* Behavior
* Strategy
* Workflow
* ExecutionLayer
* CapabilityKernel
* CapabilityNamespace
* ExecutionContext

El enrutamiento y la gobernanza de ejecución residen en el `CapabilityKernel`.

---

## 🧪 Uso básico (conceptual)

```python
response = orchestrai.execute(
    input="Resume este texto",
    policy="balanced"
)
```

OrchestrAI decide automáticamente el modelo a utilizar.

---

## 🧠 Filosofía de Desarrollo

Las primeras versiones priorizan:

* simplicidad
* modularidad
* trazabilidad
* baja complejidad operativa

Evita la sobreingeniería.

Primero se valida valor mediante:

* enrutamiento automático
* optimización de costes
* ejecución eficiente

---

## 🧱 Entorno Python (venv)

### Activar entorno

PowerShell:

```
.\.venv\Scripts\Activate.ps1
```

CMD:

```
.venv\Scripts\activate.bat
```

---

### Instalar dependencias

```
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

### Desactivar entorno

```
deactivate
```

---

## ▶️ Ejecución Local

### Prueba rápida

```
python -m core.run_demo_pipeline
```

### Tests

```
python -m unittest discover -s core/tests -p "test_*.py"
```

---

## 🎯 Objetivo

Convertirse en la capa que controla cómo se utiliza la inteligencia artificial en sistemas reales.

En otras palabras:

**Ser el sistema que decide qué IA usar, cuándo y cómo, de forma automática.**
