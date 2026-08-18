#!/usr/bin/env python3
"""
获取 POE API 的免费模型列表，并生成 AI Math 格式的 JSON 配置文件。
"""

import json
import uuid
from pathlib import Path

import requests


def generate_model_uuid(model_id: str) -> str:
    """根据 modelId 生成确定性的 UUID。"""
    NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # DNS namespace
    return str(uuid.uuid5(NAMESPACE, model_id))


def fetch_models() -> list[dict]:
    """从 POE API 获取模型列表。"""
    url = "https://api.poe.com/v1/models"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data.get("data", [])


def has_text_modalities(architecture: dict | None) -> bool:
    """检查 input_modalities 和 output_modalities 是否都包含 'text'。"""
    if not isinstance(architecture, dict):
        return False

    input_modalities = architecture.get("input_modalities")
    output_modalities = architecture.get("output_modalities")

    if not isinstance(input_modalities, list) or not isinstance(output_modalities, list):
        return False

    return "text" in input_modalities and "text" in output_modalities


def is_strictly_free(pricing: dict | None) -> bool:
    """检查价格是否严格为 0（原有初始规则）。"""
    if pricing is None or not isinstance(pricing, dict):
        return False

    has_any_price = False
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


def is_free_pricing_dict(pricing: dict | None) -> bool:
    """检查 pricing 字典中除 image 外的所有字段是否均为 0、'0.00...' 或 null。"""
    if pricing is None or not isinstance(pricing, dict):
        return False

    for key, value in pricing.items():
        if key == "image":
            continue
        if value is None:
            continue
        try:
            if float(value) != 0.0:
                return False
        except (ValueError, TypeError):
            return False

    return True


def has_allowed_parameters_for_el(model: dict) -> bool:
    """检查 -el 模型支持的 parameters 是否仅包含 enable_thinking 和 reasoning_effort（或无其他额外参数）。"""
    allowed_param_names = {"enable_thinking", "reasoning_effort"}
    parameters = model.get("parameters") or []
    if not isinstance(parameters, list):
        return True

    for param in parameters:
        if isinstance(param, dict):
            name = param.get("name")
            if name not in allowed_param_names:
                return False

    return True


def is_free_model(model: dict) -> bool:
    """判断模型是否符合免费模型条件：
    1. architecture 的 input_modalities 和 output_modalities 都包含 text
    2. 满足以下条件之一：
       - 最开始的 strictly free 规则（pricing 中有非 null 价格且全为 0，如 gemma-4-31b 等）
       - id 以 -el / -EL 结尾的模型，且 pricing 免费（pricing 为 None，或 pricing 字典中除 image 外全为 0/null），且 parameters 仅可能包含 enable_thinking / reasoning_effort（如 qwen3.8-27b-el, muse-glimmer-30b-el 等）
    """
    if not has_text_modalities(model.get("architecture")):
        return False

    pricing = model.get("pricing")
    model_id = model.get("id", "")
    is_el = model_id.lower().endswith("-el")

    # 条件1：最开始的 strictly free 规则
    if is_strictly_free(pricing):
        return True

    # 条件2：-el / -EL 结尾，pricing 免费且参数仅限 enable_thinking / reasoning_effort
    if is_el and (pricing is None or is_free_pricing_dict(pricing)) and has_allowed_parameters_for_el(model):
        return True

    return False


def extract_reasoning_effort(model: dict) -> str | None:
    """从模型的 parameters 中提取 reasoning_effort 参数值。"""
    parameters = model.get("parameters")
    if not isinstance(parameters, list):
        return None

    for param in parameters:
        if isinstance(param, dict) and param.get("name") == "reasoning_effort":
            schema = param.get("schema")
            if isinstance(schema, dict) and "enum" in schema and isinstance(schema["enum"], list) and len(schema["enum"]) > 0:
                return str(schema["enum"][-1])
            if "default_value" in param and param["default_value"] is not None:
                return str(param["default_value"])

    return None


def generate_ai_math_config(models: list[dict]) -> list[dict]:
    """生成 AI Math 配置。"""
    result = []

    for model in models:
        if not is_free_model(model):
            continue

        model_id = model.get("id", "")
        if not model_id:
            continue

        metadata = model.get("metadata", {})
        display_name = metadata.get("display_name", model_id)

        item = {
            "id": generate_model_uuid(model_id),
            "modelId": model_id,
            "displayName": f"{display_name} (Poe)",
        }

        reasoning_effort = extract_reasoning_effort(model)
        if reasoning_effort is not None:
            item["reasoningEffort"] = reasoning_effort

        result.append(item)

    return result


def main():
    """主函数。"""
    try:
        print("正在获取 POE 模型列表...")
        models = fetch_models()
        print(f"获取到 {len(models)} 个模型")

        config = generate_ai_math_config(models)
        print(f"找到 {len(config)} 个免费 AI Math 模型")

        output_path = Path(__file__).parent / "poe_ai_math.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        print(f"已生成 AI Math 配置文件: {output_path}")

        if config:
            print("\n模型列表:")
            for item in config:
                reasoning = f" [reasoningEffort: {item['reasoningEffort']}]" if "reasoningEffort" in item else ""
                print(f"  - {item['modelId']} ({item['displayName']}){reasoning}")

        return 0

    except Exception as e:
        print(f"发生错误: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
