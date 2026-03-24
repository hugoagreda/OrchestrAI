# Summary: Implements publishing actions logic for the OrchestrAI runtime.
"""
Publishing Capability Actions — Content publication and distribution
"""


def on_start(step, context):
    print(f"[PUBLISHING LIFECYCLE] on_start -> {step.action}")


def on_finish(step, context):
    print(f"[PUBLISHING LIFECYCLE] on_finish -> {step.action}")


def prepare_publish(step, context):
    """
    Prepares content for publication.
    
    Expected payload:
    - platform: str (optional)
    
    Stores result in context memory:
    - publish_ready: bool
    """
    print("[PUBLISHING ACTION] Preparing to publish...")
    
    platform = step.payload.get("platform", "generic")
    
    # Get generated content from context
    script = context.get("script_raw", "No script")
    media = context.get("media_asset", "No media")
    
    print(f"[PUBLISHING ACTION] Publishing to {platform}")
    print(f"  Script: {script[:50]}...")
    print(f"  Media: {media}")
    
    # Mark as ready
    context.set("publish_ready", True)
    
    print(f"[PUBLISHING ACTION] Ready for {platform}")
