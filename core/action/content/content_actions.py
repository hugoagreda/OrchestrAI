"""
Content Capability Actions — Script generation and refinement
"""


def on_start(step, context):
    print(f"[CONTENT LIFECYCLE] on_start -> {step.action}")


def on_finish(step, context):
    print(f"[CONTENT LIFECYCLE] on_finish -> {step.action}")


def generate_script(step, context):
    """
    Generates a script based on topic and tone.
    
    Expected payload:
    - topic: str
    - tone: str
    
    Stores result in context memory:
    - script_raw: str
    """
    print("[CONTENT ACTION] Generating script...")
    
    topic = step.payload.get("topic", "unknown")
    tone = step.payload.get("tone", "neutral")
    
    script = f"Script about '{topic}' in {tone} tone (mock)"
    
    # Store in execution context
    context.set("script_raw", script)
    
    print(f"[CONTENT ACTION] Generated: {script}")


def refine_hook(step, context):
    """
    Refines the first 3 seconds (hook) of a script.
    
    Expected payload:
    - script_raw: str (from context if not in payload)
    
    Stores result in context memory:
    - optimized_hook: str
    """
    print("[CONTENT ACTION] Refining hook...")
    
    script = step.payload.get("script_raw") or context.get("script_raw", "")
    
    if not script:
        print("[CONTENT ACTION WARNING] No script found")
        return
    
    optimized = f"HOOK: {script[:50]}... (optimized)"
    context.set("optimized_hook", optimized)
    
    print(f"[CONTENT ACTION] Optimized: {optimized}")
