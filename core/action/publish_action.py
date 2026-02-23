def prepare_publish(context):
    print("🚀 Preparing publish (mock)...")

    media = context.get("media_assets")
    if media:
        context.set("publish_ready", True)