"""
Explain an order's warehouse assignment with evidence boundaries.

This script intentionally separates confirmed facts from inferred context.
The final warehouse proves where the order is assigned, but it does not by
itself prove why OMS selected that warehouse.

Usage:
  python explain_warehouse_assignment.py --order SO00361770
  python explain_warehouse_assignment.py --order SO00361770 --compare-warehouse "Valley View"
"""
import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError

sys.path.insert(0, os.path.dirname(__file__))
import oms_client

RULE_TRANSLATIONS = {
    "Allow Split Fulfillment": "允许拆单履约",
    "Auto create product": "自动创建商品",
    "Auto create product for PO": "PO 场景自动创建商品",
    "lf the inventory is insufficient, it will be directed to the highest priority warehouse": "库存不足时转到最高优先级仓库",
    "If the inventory is insufficient, it will be directed to the highest priority warehouse": "库存不足时转到最高优先级仓库",
    "Final Summary": "最终分仓结果",
    "Order Routing Rule Check": "路由规则检查",
    "Fulfillment Item": "履约商品检查",
    "Available Warehouse Check": "可用仓库检查",
    "Available Inventory Check": "可用库存检查",
}


def translate_label(value):
    if value is None:
        return None
    return RULE_TRANSLATIONS.get(str(value), str(value))


def unwrap_data(response):
    if isinstance(response, dict):
        return response.get("data")
    return None


def as_list(value):
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def safe_get(path, params=None):
    try:
        return oms_client.get(path, params)
    except HTTPError as exc:
        try:
            body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return {"_fetchError": True, "status": exc.code, "message": str(exc), "body": body}
    except URLError as exc:
        return {"_fetchError": True, "message": str(exc)}


def fetch_dispatch_explain(order_no):
    return safe_get(
        "/api/linker-oms/opc/public-api/dispatch/dispatch-log/explain",
        {"orderNo": order_no},
    )


def find_first(obj, key_names):
    if isinstance(obj, dict):
        for key in key_names:
            if obj.get(key) not in (None, ""):
                return obj.get(key)
        for value in obj.values():
            found = find_first(value, key_names)
            if found not in (None, ""):
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_first(item, key_names)
            if found not in (None, ""):
                return found
    return None


def extract_dispatches(order_data):
    if not isinstance(order_data, dict):
        return []
    candidates = [
        order_data.get("orderDispatchList"),
        order_data.get("dispatchList"),
        order_data.get("dispatchDTOList"),
        order_data.get("dispatches"),
    ]
    for candidate in candidates:
        if isinstance(candidate, list):
            return candidate
    return []


def extract_assignment(order_data):
    dispatches = extract_dispatches(order_data)
    selected = dispatches[0] if dispatches else {}
    source = selected if selected else order_data if isinstance(order_data, dict) else {}

    return {
        "warehouseName": find_first(source, ["warehouseName", "warehouse", "shipFromWarehouseName"]),
        "warehouseCode": find_first(source, ["warehouseCode", "accountingCode", "warehouseId"]),
        "dispatchNo": find_first(source, ["dispatchNo", "dispatchOrderNo", "orderDispatchNo"]),
        "behindOrderNo": find_first(source, ["behindOrderNo", "dnNo", "deliveryNo"]),
        "dispatchStatus": find_first(source, ["dispatchStatus", "statusName", "status"]),
        "sendType": find_first(source, ["sendType"]),
        "dispatchType": find_first(source, ["dispatchType"]),
        "source": "orderDispatchList" if selected else "orderDetail",
        "rawDispatchCount": len(dispatches),
    }


def extract_order_summary(order_data):
    if not isinstance(order_data, dict):
        return {}
    return {
        "orderNo": find_first(order_data, ["orderNo", "salesOrderNo"]),
        "status": find_first(order_data, ["status", "orderStatus"]),
        "channel": find_first(order_data, ["channel", "channelName"]),
        "channelSalesOrderNo": find_first(order_data, ["channelSalesOrderNo"]),
        "merchantNo": find_first(order_data, ["merchantNo"]),
    }


def summarize_allocation_items(response):
    data = unwrap_data(response)
    if isinstance(response, dict) and response.get("code") not in (0, None):
        return {
            "fetchStatus": "failed",
            "businessCode": response.get("code"),
            "message": response.get("msg"),
            "lineCount": 0,
            "totalRemainingQty": 0,
            "lines": [],
        }
    if isinstance(data, dict) and isinstance(data.get("itemVOList"), list):
        rows = data.get("itemVOList")
    else:
        rows = as_list(data)
    total_remaining = 0
    lines = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        remaining = row.get("remainingQty")
        if remaining is None:
            remaining = row.get("remainingQuantity")
        if remaining is None:
            remaining = row.get("remainQty")
        if remaining is None:
            remaining = row.get("remaining")
        try:
            remaining_num = float(remaining or 0)
        except (TypeError, ValueError):
            remaining_num = 0
        total_remaining += remaining_num
        lines.append(
            {
                "sku": find_first(row, ["sku", "itemSku", "productSku"]),
                "orderedQty": find_first(row, ["qty", "quantity", "orderedQty", "totalQty"]),
                "remainingQty": remaining,
                "uom": find_first(row, ["uom", "unit"]),
            }
        )
    return {
        "fetchStatus": "failed" if isinstance(response, dict) and response.get("_fetchError") else "ok",
        "lineCount": len(lines),
        "totalRemainingQty": total_remaining,
        "lines": lines[:20],
    }


def summarize_routing_rules(response):
    data = unwrap_data(response)
    rules = as_list(data)
    active = []
    for rule in rules:
        if not isinstance(rule, dict):
            continue
        enabled = rule.get("enabled")
        if enabled is None:
            enabled = rule.get("enable")
        if enabled is False:
            continue
        active.append(
            {
                "name": find_first(rule, ["ruleName", "name", "routingRuleName"]),
                "type": find_first(rule, ["ruleType", "type", "routingType"]),
                "priority": find_first(rule, ["priority", "sort", "sequence"]),
                "status": find_first(rule, ["status"]),
            }
        )
    return {
        "fetchStatus": "failed" if isinstance(response, dict) and response.get("_fetchError") else "ok",
        "activeRuleCount": len(active),
        "activeRules": active[:20],
        "evidenceBoundary": "Routing configuration is context only unless a routing trace/log confirms the rule was applied to this order.",
    }


def try_parse_json(value):
    if not isinstance(value, str):
        return value
    text = value.strip()
    if not text:
        return value
    if not (text.startswith("{") or text.startswith("[")):
        return value
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return value


def summarize_dispatch_explain(response):
    data = unwrap_data(response)
    rows = as_list(data)
    events = []
    selected_rules = []
    available_warehouses = []
    inventory_checks = []
    final_dispatches = []
    event_id = None

    for row in rows:
        if not isinstance(row, dict):
            continue
        event_type = row.get("eventType")
        parsed_summary = try_parse_json(row.get("summary"))
        event_id = event_id or row.get("eventId")
        event = {
            "eventType": event_type,
            "status": row.get("status"),
            "eventId": row.get("eventId"),
            "eventTime": row.get("eventTime"),
            "summary": parsed_summary,
        }
        events.append(event)

        if event_type == "Order Routing Rule Check":
            selected_rules = parsed_summary if isinstance(parsed_summary, list) else []
        elif event_type == "Available Warehouse Check":
            available_warehouses = parsed_summary if isinstance(parsed_summary, list) else []
        elif event_type == "Available Inventory Check":
            inventory_checks = parsed_summary.get("inventoryList", []) if isinstance(parsed_summary, dict) else []
        elif event_type in ("Final Summary",) or (
            isinstance(event_type, str)
            and event_type not in ("Order Routing Rule Check", "Fulfillment Item", "Available Warehouse Check", "Available Inventory Check")
            and isinstance(parsed_summary, list)
        ):
            final_dispatches = parsed_summary if isinstance(parsed_summary, list) else final_dispatches

    return {
        "fetchStatus": "failed" if isinstance(response, dict) and response.get("_fetchError") else "ok",
        "eventId": event_id,
        "eventCount": len(events),
        "events": events,
        "selectedRules": selected_rules,
        "availableWarehouses": available_warehouses,
        "inventoryChecks": inventory_checks,
        "finalDispatches": final_dispatches,
    }


def classify_dispatch_method(assignment, dispatch_explain_summary=None):
    if dispatch_explain_summary and dispatch_explain_summary.get("eventCount"):
        return {
            "value": "confirmed_auto_dispatch",
            "evidence": "Dispatch explain logs exist for this order and include routing rule checks, warehouse checks, inventory checks, and final dispatch result.",
        }
    dispatch_type = assignment.get("dispatchType")
    if dispatch_type:
        if "AUTO" in str(dispatch_type):
            return {
                "value": "confirmed_auto_dispatch",
                "evidence": f"dispatchType={dispatch_type}",
            }
        if "HAND" in str(dispatch_type):
            return {
                "value": "confirmed_manual_dispatch",
                "evidence": f"dispatchType={dispatch_type}",
            }
    return {
        "value": "unknown_from_available_fields",
        "evidence": "No dispatchType/manual/auto field was found in the fetched order detail.",
    }


def build_confirmed_reason_from_dispatch_explain(dispatch_explain_summary, assignment):
    if dispatch_explain_summary.get("fetchStatus") != "ok" or not dispatch_explain_summary.get("eventCount"):
        return None

    final_dispatches = dispatch_explain_summary.get("finalDispatches") or []
    chosen_warehouse = assignment.get("warehouseName")
    if not chosen_warehouse and final_dispatches:
        chosen_warehouse = find_first(final_dispatches, ["warehouseName"])

    rule_events = [
        event for event in dispatch_explain_summary.get("events", [])
        if isinstance(event.get("eventType"), str)
        and event.get("eventType") not in (
            "Order Routing Rule Check",
            "Fulfillment Item",
            "Available Warehouse Check",
            "Available Inventory Check",
            "Final Summary",
        )
    ]
    applied_rule = rule_events[-1]["eventType"] if rule_events else None
    selected_rules = dispatch_explain_summary.get("selectedRules") or []
    available_warehouses = dispatch_explain_summary.get("availableWarehouses") or []
    inventory_checks = dispatch_explain_summary.get("inventoryChecks") or []

    inventory_text = []
    for item in inventory_checks:
        sku = item.get("sku") if isinstance(item, dict) else None
        warehouses = item.get("warehouses", []) if isinstance(item, dict) else []
        if sku and warehouses:
            parts = [
                f"{w.get('warehouseName')}({w.get('accountingCode')}): {w.get('qty')} {w.get('uom')}"
                for w in warehouses
                if isinstance(w, dict)
            ]
            inventory_text.append(f"{sku}: " + ", ".join(parts))

    facts = []
    if selected_rules:
        facts.append("检查过的路由规则: " + ", ".join(translate_label(rule) for rule in selected_rules))
    if available_warehouses:
        facts.append("可用仓库: " + ", ".join(map(str, available_warehouses)))
    if inventory_text:
        facts.append("库存检查: " + " | ".join(inventory_text))
    if applied_rule:
        facts.append(f"命中规则/事件: {translate_label(applied_rule)}")
    if final_dispatches:
        facts.append(f"最终分仓结果: {json.dumps(final_dispatches, ensure_ascii=False)}")

    if not chosen_warehouse:
        return None

    message_parts = [f"根据分仓解释日志，订单被分到 {chosen_warehouse}。"]
    if applied_rule:
        message_parts.append(f"关键命中规则是：{translate_label(applied_rule)}。")
    if inventory_text:
        message_parts.append("库存证据：" + " | ".join(inventory_text))

    return {
        "confirmed": True,
        "message": " ".join(message_parts),
        "confirmedFacts": facts,
        "evidenceSource": "dispatch_log_explain",
        "eventId": dispatch_explain_summary.get("eventId"),
        "evidenceGap": [],
    }


def build_reason(order_summary, assignment, allocation_summary, routing_summary, dispatch_explain_summary=None):
    if dispatch_explain_summary:
        confirmed_reason = build_confirmed_reason_from_dispatch_explain(dispatch_explain_summary, assignment)
        if confirmed_reason:
            return confirmed_reason

    warehouse = assignment.get("warehouseName")
    if not warehouse:
        return {
            "confirmed": False,
            "message": "No assigned warehouse was found in the fetched order detail.",
            "evidenceGap": ["orderDispatchList or warehouse fields are missing."],
        }

    gaps = [
        "Dispatch explain log was unavailable or empty for this order.",
        "Routing rule configuration can explain possible logic, but cannot prove the exact rule path for this order without dispatch explain logs.",
    ]
    if allocation_summary.get("fetchStatus") != "ok":
        gaps.append("Allocation item lookup failed, so remaining quantity evidence is incomplete.")

    return {
        "confirmed": False,
        "message": (
            f"The order is confirmed assigned to {warehouse}, but the exact selection reason is not confirmed "
            "from the available fields. Do not claim closest warehouse, inventory priority, zip-code routing, "
            "or product-specific routing unless a routing trace/log explicitly proves it."
        ),
        "confirmedFacts": [
            f"Order status: {order_summary.get('status') or 'unknown'}",
            f"Assignment source: {assignment.get('source')}",
            f"Dispatch status: {assignment.get('dispatchStatus') or 'unknown'}",
            f"Remaining quantity total: {allocation_summary.get('totalRemainingQty')}",
            f"Active routing rules fetched: {routing_summary.get('activeRuleCount')}",
        ],
        "evidenceGap": gaps,
    }


def same_text(left, right):
    if left is None or right is None:
        return False
    return str(left).strip().lower() == str(right).strip().lower()


def normalize_warehouse_label(value):
    if value is None:
        return ""
    return str(value).split("-")[0].strip().lower()


def build_candidate_answer(compare_warehouse, assignment, dispatch_explain_summary):
    assigned = assignment.get("warehouseName")
    if not compare_warehouse:
        return {
            "comparedWarehouse": None,
            "isSameAsAssignedWarehouse": False,
            "canExplainWhyNotSelected": False,
            "message": None,
        }

    if same_text(compare_warehouse, assigned):
        return {
            "comparedWarehouse": compare_warehouse,
            "isSameAsAssignedWarehouse": True,
            "canExplainWhyNotSelected": False,
            "message": "The compared warehouse is the assigned warehouse, so it is not a rejected candidate.",
        }

    available = dispatch_explain_summary.get("availableWarehouses") if dispatch_explain_summary else []
    available_names = {normalize_warehouse_label(item) for item in available or []}
    compared_name = normalize_warehouse_label(compare_warehouse)
    if available_names and compared_name not in available_names:
        return {
            "comparedWarehouse": compare_warehouse,
            "isSameAsAssignedWarehouse": False,
            "canExplainWhyNotSelected": True,
            "message": f"{compare_warehouse} was not in the available warehouse candidate list returned by dispatch explain logs.",
            "availableWarehouses": available,
        }

    return {
        "comparedWarehouse": compare_warehouse,
        "isSameAsAssignedWarehouse": False,
        "canExplainWhyNotSelected": False,
        "message": (
            "A non-selected warehouse can only be explained with candidate evaluation evidence, "
            "such as routing trace, inventory candidate list, or explicit rejection reason."
        ),
        "availableWarehouses": available,
    }


def build_user_summary(order_summary, assignment, dispatch_method, reason, compare_warehouse=None, candidate_answer=None):
    if order_summary.get("lookupStatus") == "ORDER_NOT_FOUND_OR_INACCESSIBLE":
        return (
            f"结论：没有查到订单 {order_summary.get('orderNo')} 的有效详情，暂时不能判断分仓结果。\n"
            f"原因：订单详情接口未返回有效订单数据（{order_summary.get('lookupMessage') or 'no detail data'}）。\n"
            "下一步：请确认订单号、商户/环境是否正确，再重新查询。"
        )
    warehouse = assignment.get("warehouseName") or "未找到已分配仓库"
    status = order_summary.get("status")
    dispatch_status = assignment.get("dispatchStatus")
    is_cancelled = same_text(status, "CANCELLED") or same_text(dispatch_status, "Cancelled")
    result_wording = "历史分仓/取消前的 dispatch 结果" if is_cancelled else "当前分仓结果"
    method_labels = {
        "confirmed_auto_dispatch": "系统自动分仓",
        "confirmed_manual_dispatch": "人工/手动分仓",
        "unknown_from_available_fields": "当前详情字段未标明自动或手动",
    }
    method_label = method_labels.get(dispatch_method["value"], dispatch_method["value"])
    lines = [
        f"结论：订单 {order_summary.get('orderNo') or ''} {result_wording}是 {warehouse}。",
        f"分仓方式：{method_label}（证据：{dispatch_method['evidence']}）。",
    ]
    if reason.get("confirmed"):
        lines.append(f"原因：{reason.get('message')}")
        facts = reason.get("confirmedFacts") or []
        if facts:
            lines.append("关键证据：" + "；".join(map(str, facts[:4])) + "。")
    else:
        lines.append(
            "原因：当前接口只能确认分仓结果，不能确认具体为什么选择该仓；需要 routing trace、dispatch log 或规则执行明细后才能下结论。"
        )
    candidate_answer = candidate_answer or {}
    if compare_warehouse and same_text(compare_warehouse, warehouse):
        lines.append(f"你提到的 {compare_warehouse} 与已确认仓库一致，不属于未选中仓库。")
    elif compare_warehouse and candidate_answer.get("canExplainWhyNotSelected"):
        lines.append(
            f"关于为什么不是 {compare_warehouse}：分仓解释日志中的可用仓候选列表是 "
            f"{', '.join(map(str, candidate_answer.get('availableWarehouses') or []))}，"
            f"{compare_warehouse} 没有进入这次自动分仓的可用仓候选列表。"
        )
    elif compare_warehouse:
        lines.append(
            f"关于为什么不是 {compare_warehouse}：当前证据不足，不能凭最终仓库反推其他仓被淘汰的原因。"
        )
    if reason.get("confirmed"):
        lines.append("下一步：分仓原因已由 dispatch explain 日志确认；如要继续处理，应查看 WMS/仓库处理进度。")
    else:
        lines.append("建议：如用户追问原因，请先补查路由执行日志/dispatch 日志，再解释具体规则命中。")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--order", required=True, help="Sales order number")
    parser.add_argument("--compare-warehouse", default=None, help="Optional warehouse the user expected")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    order_response = safe_get(f"/api/linker-oms/opc/app-api/sale-order/{args.order}")
    order_data = unwrap_data(order_response) or {}
    dispatch_explain_response = fetch_dispatch_explain(args.order)
    allocation_response = safe_get(f"/api/linker-oms/opc/app-api/dispatch/hand/item/{args.order}")
    routing_response = safe_get(
        "/api/linker-oms/opc/app-api/routing/v2/rules",
        {"merchantNo": oms_client._env("OMS_MERCHANT_NO")},
    )

    order_summary = extract_order_summary(order_data)
    order_summary["orderNo"] = order_summary.get("orderNo") or args.order
    if not order_data or (isinstance(order_response, dict) and order_response.get("code") not in (0, None)):
        order_summary["lookupStatus"] = "ORDER_NOT_FOUND_OR_INACCESSIBLE"
        order_summary["lookupCode"] = order_response.get("code") if isinstance(order_response, dict) else None
        order_summary["lookupMessage"] = order_response.get("msg") if isinstance(order_response, dict) else None
    assignment = extract_assignment(order_data)
    dispatch_explain_summary = summarize_dispatch_explain(dispatch_explain_response)
    allocation_summary = summarize_allocation_items(allocation_response)
    routing_summary = summarize_routing_rules(routing_response)
    dispatch_method = classify_dispatch_method(assignment, dispatch_explain_summary)
    reason = build_reason(
        order_summary,
        assignment,
        allocation_summary,
        routing_summary,
        dispatch_explain_summary,
    )

    result = {
        "orderSummary": order_summary,
        "assignmentResult": assignment,
        "dispatchMethod": dispatch_method,
        "reason": reason,
        "dispatchExplainSummary": dispatch_explain_summary,
        "allocationSummary": allocation_summary,
        "routingRuleSummary": routing_summary,
        "candidateWarehouseAnswer": build_candidate_answer(
            args.compare_warehouse,
            assignment,
            dispatch_explain_summary,
        ),
        "userFacingSummary": build_user_summary(
            order_summary,
            assignment,
            dispatch_method,
            reason,
            args.compare_warehouse,
            build_candidate_answer(args.compare_warehouse, assignment, dispatch_explain_summary),
        ),
        "_env": oms_client.get_env_label(),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
