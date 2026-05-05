#!/usr/bin/env python3
"""
将 free_models.json 中支持 tools 的模型生成 AI SDK 配置格式的 JSON。
"""

import json
from pathlib import Path


def has_tools_feature(model: dict) -> bool:
    """检查模型是否支持 tools 功能。"""
    features = model.get("supported_features", [])
    return isinstance(features, list) and "tools" in features


def generate_ai_sdk_config(models: list[dict]) -> dict:
    """生成 AI SDK 配置。"""
    ai_models = {}

    for model in models:
        if not has_tools_feature(model):
            continue

        model_id = model.get("id", "")
        metadata = model.get("metadata", {})
        display_name = metadata.get("display_name", model_id)

        # 普通版本
        ai_models[model_id] = {
            "name": f"{display_name} (Free)",
            "reasoning": False,
        }

        # Reasoning 版本
        ai_models[f"{model_id}-reasoning"] = {
            "name": f"{display_name} Reasoning (Free)",
            "reasoning": True,
        }

    return {
        "poe-custom": {
            "name": "Poe",
            "npm": "@ai-sdk/openai-compatible",
            "options": {
                "baseURL": "https://api.poe.com/v1"
            },
            "models": ai_models,
        }
    }


def main():
    """主函数。"""
    base_dir = Path(__file__).parent
    json_path = base_dir / "free_models.json"
    output_path = base_dir / "free_models_ai_sdk.json"

    if not json_path.exists():
        print(f"错误: 找不到 {json_path}")
        return 1

    with open(json_path, "r", encoding="utf-8") as f:
        models = json.load(f)

    config = generate_ai_sdk_config(models)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    model_count = len(config["poe-custom"]["models"])
    print(f"已生成 AI SDK 配置文件: {output_path}")
    print(f"共 {model_count} 个模型支持 tools")

    return 0


if __name__ == "__main__":
    exit(main())
