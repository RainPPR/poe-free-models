#!/usr/bin/env python3
"""
获取 POE API 的模型列表，并筛选出所有价格严格为 0 的免费模型保存到 JSON 文件。
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import requests


def fetch_models() -> list[dict]:
    """从 POE API 获取模型列表（无需认证）。"""
    url = "https://api.poe.com/v1/models"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    data = response.json()
    return data.get("data", [])


def is_strictly_free(pricing: dict | None) -> bool:
    """检查价格是否严格为 0（免费）。"""
    if pricing is None:
        return False

    if not isinstance(pricing, dict):
        return False

    has_any_price = False

    # 遍历 pricing 中所有非 null 的值
    for key, value in pricing.items():
        if value is None:
            continue

        has_any_price = True

        try:
            if float(value) != 0:
                return False
        except (ValueError, TypeError):
            return False

    return has_any_price


def extract_free_models(models: list[dict]) -> list[dict]:
    """提取所有价格严格为 0 的模型。"""
    free_models = []

    for model in models:
        pricing = model.get("pricing")

        if is_strictly_free(pricing):
            # 保留完整的模型数据，只添加更新时间
            free_model = model.copy()
            free_model["updated_at"] = datetime.now(timezone.utc).isoformat()
            free_models.append(free_model)

    return free_models


def save_to_json(models: list[dict], output_path: Path) -> None:
    """将模型列表保存为 JSON 文件。"""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(models, f, ensure_ascii=False, indent=2)

    print(f"已保存 {len(models)} 个免费模型到 {output_path}")


def main():
    """主函数。"""
    try:
        print("正在获取 POE 模型列表...")

        models = fetch_models()
        print(f"获取到 {len(models)} 个模型")

        free_models = extract_free_models(models)
        print(f"找到 {len(free_models)} 个价格严格为 0 的模型")

        # 保存到项目根目录
        output_path = Path(__file__).parent / "free_models.json"
        save_to_json(free_models, output_path)

        # 打印模型列表
        if free_models:
            print("\n免费模型列表:")
            for model in free_models:
                metadata = model.get("metadata", {})
                name = metadata.get("display_name", model.get("id"))
                print(f"  - {model['id']} ({name})")
        else:
            print("\n没有找到价格严格为 0 的模型")

        return 0

    except requests.exceptions.RequestException as e:
        print(f"API 请求失败: {e}")
        return 1
    except Exception as e:
        print(f"发生错误: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
