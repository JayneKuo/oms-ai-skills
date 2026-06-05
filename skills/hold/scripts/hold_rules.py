"""
Query, inspect, draft, and optionally create OMS hold rules.

Default behavior is read-only/dry-run. Creating a rule requires
`--action create --confirm-create`.

Examples:
  python hold_rules.py --action list
  python hold_rules.py --action list --status ENABLED
  python hold_rules.py --action get --id 2062019635310088193
  python hold_rules.py --action active-count --id 2062019635310088193
  python hold_rules.py --action draft --text "hold imported orders permanently priority 55"
  python hold_rules.py --action create --text "hold imported orders permanently priority 55" --confirm-create
"""
import argparse
import json
import os
import re
import sys
import urllib.error

sys.path.insert(0, os.path.dirname(__file__))
import oms_client


HOLD_MODES = {"PERMANENT", "DATA_RANGE", "RISK_CONTROL"}
RISK_LEVELS = {"LOW", "MEDIUM", "HIGH", "PENDING", "NONE"}
ORDER_SOURCE_ALIASES = {
    "imported": "IMPORTED",
    "导入": "IMPORTED",
    "created": "CREATED",
    "manual": "CREATED",
    "手动": "CREATED",
    "shopify": "SHOPIFY",
    "walmart": "WALMART_MP",
    "walmart_mp": "WALMART_MP",
}


def safe_get(path, params=None):
    try:
        return oms_client.get(path, params)
    except urllib.error.HTTPError as exc:
        return {"_fetchError": True, "status": exc.code, "message": str(exc)}
    except urllib.error.URLError as exc:
        return {"_fetchError": True, "message": str(exc)}


def safe_post(path, body=None):
    try:
        return oms_client.post(path, body)
    except urllib.error.HTTPError as exc:
        return {"_fetchError": True, "status": exc.code, "message": str(exc)}
    except urllib.error.URLError as exc:
        return {"_fetchError": True, "message": str(exc)}


def unwrap_data(response):
    return response.get("data") if isinstance(response, dict) else None


def parse_csv(value):
    if value is None:
        return None
    items = []
    for part in str(value).replace("，", ",").split(","):
        part = part.strip()
        if part:
            items.append(part)
    return items or None


def summarize_rule(rule):
    return {
        "id": rule.get("id"),
        "ruleName": rule.get("ruleName"),
        "status": rule.get("status"),
        "holdMode": rule.get("holdMode"),
        "priority": rule.get("priority"),
        "skuList": rule.get("skuList"),
        "channels": rule.get("channels"),
        "orderSource": rule.get("orderSource"),
        "warehouseNames": rule.get("warehouseNames"),
        "dateRange": rule.get("dateRange"),
        "allowedRiskLevels": rule.get("allowedRiskLevels"),
        "holdDurationHours": rule.get("holdDurationHours"),
    }


def list_rules(args):
    params = {
        "pageNo": args.page,
        "pageSize": args.size,
        "merchantNo": oms_client._env("OMS_MERCHANT_NO"),
        "sortField": args.sort_field,
        "sortType": args.sort_type,
        "ruleName": args.rule_name,
        "status": args.status,
    }
    response = safe_get("/api/linker-oms/opc/app-api/hold-rule-data/page", params)
    data = unwrap_data(response) or {}
    rules = [summarize_rule(row) for row in data.get("list", []) if isinstance(row, dict)]
    return {
        "code": response.get("code") if isinstance(response, dict) else None,
        "message": response.get("msg") if isinstance(response, dict) else None,
        "total": data.get("total"),
        "rules": rules,
    }


def get_rule(args):
    response = safe_get(f"/api/linker-oms/opc/app-api/hold-rule-data/{args.id}")
    data = unwrap_data(response)
    return {
        "code": response.get("code") if isinstance(response, dict) else None,
        "message": response.get("msg") if isinstance(response, dict) else None,
        "rule": summarize_rule(data) if isinstance(data, dict) else data,
        "raw": data,
    }


def active_count(args):
    response = safe_get(
        "/api/linker-oms/opc/app-api/order-hold/active-count",
        {"merchant": oms_client._env("OMS_MERCHANT_NO"), "rule_id": args.id},
    )
    return {
        "code": response.get("code") if isinstance(response, dict) else None,
        "message": response.get("msg") if isinstance(response, dict) else None,
        "ruleId": args.id,
        "activeHoldCount": unwrap_data(response),
    }


def infer_from_text(text):
    lower = (text or "").lower()
    draft = {
        "ruleName": "AI drafted hold rule",
        "status": "DISABLED",
        "holdMode": "PERMANENT",
        "priority": 100,
        "merchantNo": oms_client._env("OMS_MERCHANT_NO"),
        "addressConditions": [],
        "addressMatchLogic": "OR",
        "orderTagMatchLogic": "OR",
    }

    name_match = re.search(
        r"(?:name|rule name|规则名|叫|命名为)\s*[:：]?\s*['\"]?([^'\"，,。；;]+)",
        text or "",
        re.I,
    )
    if name_match:
        draft["ruleName"] = name_match.group(1).strip()

    if "enable" in lower or "启用" in lower:
        draft["status"] = "ENABLED"
    if "disable" in lower or "禁用" in lower:
        draft["status"] = "DISABLED"
    if "temporary" in lower or "date range" in lower or "时间" in lower:
        draft["holdMode"] = "DATA_RANGE"
    if "risk" in lower or "风控" in lower or "风险" in lower:
        draft["holdMode"] = "RISK_CONTROL"

    priority_match = re.search(r"(?:priority|优先级)\s*[:：]?\s*(\d+)", lower)
    if priority_match:
        draft["priority"] = int(priority_match.group(1))

    sku_match = re.search(r"(?:sku|skus|商品)\s*[:：]?\s*([A-Za-z0-9_,，\-\s]+)", text or "", re.I)
    if sku_match:
        draft["skuList"] = [item.upper() for item in parse_csv(sku_match.group(1)) or []]

    sources = []
    for token, source in ORDER_SOURCE_ALIASES.items():
        if re.search(rf"(?<![a-z0-9_]){re.escape(token)}(?![a-z0-9_])", lower):
            sources.append(source)
    sources = list(dict.fromkeys(sources))
    if sources:
        draft["orderSource"] = sources

    risks = [risk for risk in RISK_LEVELS if risk.lower() in lower]
    if risks:
        draft["allowedRiskLevels"] = risks
        draft["holdMode"] = "RISK_CONTROL"

    duration_match = re.search(r"(\d+)\s*(?:hours|hour|小时)", lower)
    if duration_match:
        draft["holdDurationHours"] = int(duration_match.group(1))

    return draft


def build_draft(args):
    if args.json_body:
        draft = json.loads(args.json_body)
    else:
        draft = infer_from_text(args.text or "")
    if args.rule_name:
        draft["ruleName"] = args.rule_name
    if args.status:
        draft["status"] = args.status
    if args.hold_mode:
        draft["holdMode"] = args.hold_mode
    if args.priority is not None:
        draft["priority"] = args.priority
    if args.skus:
        draft["skuList"] = [item.upper() for item in parse_csv(args.skus) or []]
    if args.order_source:
        draft["orderSource"] = parse_csv(args.order_source)
    draft["merchantNo"] = draft.get("merchantNo") or oms_client._env("OMS_MERCHANT_NO")
    draft.setdefault("addressConditions", [])
    draft.setdefault("addressMatchLogic", "OR")
    draft.setdefault("orderTagMatchLogic", "OR")

    warnings = []
    if draft.get("status") == "ENABLED":
        warnings.append("Draft is ENABLED; creating it may immediately hold matching future orders.")
    if not draft.get("ruleName"):
        warnings.append("ruleName is missing.")
    if draft.get("holdMode") not in HOLD_MODES:
        warnings.append("holdMode is unusual; expected PERMANENT, DATA_RANGE, or RISK_CONTROL.")
    return {"draft": draft, "warnings": warnings}


def create_rule(args):
    draft_result = build_draft(args)
    if not args.confirm_create:
        return {
            "state": "dry_run",
            "submittedToOms": False,
            "message": "Creation was not submitted. Add --confirm-create after reviewing the draft.",
            **draft_result,
        }
    response = safe_post("/api/linker-oms/opc/app-api/hold-rule-data/create", draft_result["draft"])
    return {
        "state": "submitted",
        "submittedToOms": True,
        "response": response,
        **draft_result,
    }


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--action", required=True, choices=["list", "get", "active-count", "draft", "create"])
    parser.add_argument("--id", default=None)
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--size", type=int, default=20)
    parser.add_argument("--sort-field", default="priority")
    parser.add_argument("--sort-type", default="ASC")
    parser.add_argument("--rule-name", default=None)
    parser.add_argument("--status", choices=["ENABLED", "DISABLED"], default=None)
    parser.add_argument("--text", default=None)
    parser.add_argument("--json-body", default=None)
    parser.add_argument("--hold-mode", choices=sorted(HOLD_MODES), default=None)
    parser.add_argument("--priority", type=int, default=None)
    parser.add_argument("--skus", default=None)
    parser.add_argument("--order-source", default=None)
    parser.add_argument("--confirm-create", action="store_true")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    if args.action in ("get", "active-count") and not args.id:
        parser.error("--id is required for get/active-count")

    if args.action == "list":
        result = list_rules(args)
    elif args.action == "get":
        result = get_rule(args)
    elif args.action == "active-count":
        result = active_count(args)
    elif args.action == "draft":
        result = build_draft(args)
        result["state"] = "draft"
        result["submittedToOms"] = False
    else:
        result = create_rule(args)

    result["_env"] = oms_client.get_env_label()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
