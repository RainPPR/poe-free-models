#!/usr/bin/env python3
"""
将 free_models.json 中的模型数据提取为 CSV，只包含 name、id、provider 三列。
"""

import csv
import json
from pathlib import Path


def extract_models_to_csv(json_path: Path, csv_path: Path) -> None:
    """从 JSON 文件提取模型数据并保存为 CSV。"""
    with open(json_path, "r", encoding="utf-8") as f:
        models = json.load(f)

    rows = []
    for model in models:
        model_id = model.get("id", "")
        provider = model.get("owned_by", "")
        metadata = model.get("metadata", {})
        context_length = model.get("context_length", 0)
        name = metadata.get("display_name", model_id)

        rows.append({
            "name": name,
            "id": model_id,
            "provider": provider,
            "context_length": context_length
        })

    # 按 name 排序
    rows.sort(key=lambda x: x["name"].lower())

    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "id", "provider"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"已保存 {len(rows)} 个模型到 {csv_path}")


def main():
    """主函数。"""
    base_dir = Path(__file__).parent
    json_path = base_dir / "free_models.json"
    csv_path = base_dir / "free_models.csv"

    if not json_path.exists():
        print(f"错误: 找不到 {json_path}")
        return 1

    extract_models_to_csv(json_path, csv_path)
    return 0


if __name__ == "__main__":
    exit(main())
