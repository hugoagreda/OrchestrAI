def generate_media(context):
    print("🎬 Generating media (mock)...")

    script = context.get("script")
    if script:
        context.set("media_assets", ["video_asset_mock.mp4"])