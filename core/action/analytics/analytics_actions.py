"""
Analytics Capability Actions — Runtime metrics analysis and summary
"""


def on_start(step, context):
    print(f"[ANALYTICS LIFECYCLE] on_start -> {step.action}")


def on_finish(step, context):
    print(f"[ANALYTICS LIFECYCLE] on_finish -> {step.action}")


def analyze_metrics(step, context):
    """
    Summarizes runtime memory and metrics into a compact report.
    """
    print("[ANALYTICS ACTION] Building analytics summary...")

    metrics = context.metrics()
    summary = {
        "successful_steps": metrics.get("successful_steps", 0),
        "failed_steps": metrics.get("failed_steps", 0),
        "capability_invocations": metrics.get("capability_invocations", {}),
        "memory_keys": list(context.dump().get("state", {}).get("memory", {}).keys()),
    }

    context.set("analytics_summary", summary)
    print(f"[ANALYTICS ACTION] Summary: {summary}")
