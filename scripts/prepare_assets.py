"""DVC 스테이지. 로봇(Unitree A1)은 isaaclab_assets 의 USD 를 쓰므로 여기서는 에셋 식별 정보만 고정한다 (dvc.lock → 에셋 hash)."""
import json
from pathlib import Path

Path("assets").mkdir(exist_ok=True)
Path("assets/task.json").write_text(json.dumps({"robot": "isaaclab_assets.UNITREE_A1_CFG", "isaaclab": "2.1.1", "isaacsim": "4.5.0"}, indent=2))
print("assets/task.json")
