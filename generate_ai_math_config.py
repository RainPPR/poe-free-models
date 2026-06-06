#!/usr/bin/env python3
"""
将 free_models.json 中的模型生成 AI Math 配置格式的 JSON。
"""

import json
import uuid
from pathlib import Path


def generate_model_uuid(model_id: str) -> str:
    """根据 modelId 生成确定性的 UUID。"""
    # 使用 uuid5（SHA-1 散列）基于固定命名空间和 modelId 生成
    # 确保相同的 modelId 永远生成相同的 UUID
    NAMESPACE = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')  # DNS namespace
    return str(uuid.uuid5(NAMESPACE, model_id))


def has_tools_feature(model: dict) -> bool:
    """检查模型是否支持 tools 功能。"""
    features = model.get("supported_features", [])
    return isinstance(features, list) and "tools" in features


def generate_ai_math_config(models: list[dict]) -> list[dict]:
    """生成 AI Math 配置。"""
    result = []

    for model in models:
        model_id = model.get("id", "")
        if not model_id:
            continue

        metadata = model.get("metadata", {})
        display_name = metadata.get("display_name", model_id)

        result.append({
            "id": generate_model_uuid(model_id),
            "modelId": model_id,
            "enableTools": has_tools_feature(model),
            "disabledTools": [],
            "displayName": f"{display_name} (Poe)",
        })

    return result


def main():
    """主函数。"""
    base_dir = Path(__file__).parent
    json_path = base_dir / "free_models.json"
    output_path = base_dir / "free_models_ai_math.json"

    if not json_path.exists():
        print(f"错误: 找不到 {json_path}")
        return 1

    with open(json_path, "r", encoding="utf-8") as f:
        models = json.load(f)

    config = generate_ai_math_config(models)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    print(f"已生成 AI Math 配置文件: {output_path}")
    print(f"共 {len(config)} 个模型")

    return 0


if __name__ == "__main__":
    exit(main())
