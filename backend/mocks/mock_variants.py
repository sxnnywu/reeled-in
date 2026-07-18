"""Canned variant list for stubbing generation. Owner: D (Sunny)."""
def mock_variants(test_id: str = "test_demo0001") -> list:
    return [
        {"id": "var_demoA", "test_id": test_id, "label": "A", "media_key": "media/var_demoA.mp4",
         "params": {"script": "Stop scrolling. Reeled In shows you which edit hooks the brain.",
                    "voice_id": "21m00Tcm4TlvDq8ikWAM", "voice_settings": {}},
         "created_at": "2026-07-19T04:20:00Z"},
        {"id": "var_demoB", "test_id": test_id, "label": "B", "media_key": "media/var_demoB.mp4",
         "params": {"script": "Stop scrolling. Reeled In shows you which edit hooks the brain.",
                    "voice_id": "21m00Tcm4TlvDq8ikWAM", "voice_settings": {"speed": 1.15}},
         "created_at": "2026-07-19T04:20:00Z"},
    ]
