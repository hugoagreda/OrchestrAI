# Summary: Implements media actions logic for the OrchestrAI runtime.
"""
Media Capability Actions — Media generation and management
"""


def on_start(step, context):
    print(f"[MEDIA LIFECYCLE] on_start -> {step.action}")


def on_finish(step, context):
    print(f"[MEDIA LIFECYCLE] on_finish -> {step.action}")


def generate_media(step, context):
    """
    Generates media assets.
    
    Expected payload:
    - style: str (optional)
    
    Stores result in context memory:
    - media_asset: str
    """
    print("[MEDIA ACTION] Generating media...")
    
    style = step.payload.get("style", "default")
    
    media = f"Media asset in {style} style (mock)"
    
    # Store in execution context
    context.set("media_asset", media)
    
    print(f"[MEDIA ACTION] Generated: {media}")
