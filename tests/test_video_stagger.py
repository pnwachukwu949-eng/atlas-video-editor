from atlas.rendering.bridge import RenderBridge

def test_stagger_second_use_of_same_video():
    clips = [
        {"beat_id": "B01", "asset_id": "fetched_video_residential_01", "type": "contextual_video", "start": 0, "end": 2},
        {"beat_id": "B02", "asset_id": "card_a", "type": "contextual_photo", "start": 2, "end": 4},
        {"beat_id": "B03", "asset_id": "fetched_video_residential_01", "type": "contextual_video", "start": 4, "end": 6},
    ]
    out = RenderBridge()._stagger_video_inpoints(clips)
    assert out[0].get("video_start_seconds") is None
    assert out[2].get("video_start_seconds") == 2.5
    assert out[1].get("video_start_seconds") is None


def test_explicit_inpoint_not_overwritten():
    clips = [
        {"beat_id": "B01", "asset_id": "vid", "type": "contextual_video", "video_start_seconds": 1.0},
        {"beat_id": "B02", "asset_id": "vid", "type": "contextual_video", "video_start_seconds": 4.0},
    ]
    out = RenderBridge()._stagger_video_inpoints(clips)
    assert out[0]["video_start_seconds"] == 1.0
    assert out[1]["video_start_seconds"] == 4.0
