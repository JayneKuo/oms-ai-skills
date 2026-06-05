"""
Diagnose ON_HOLD orders and optionally release hold with post-check.

Examples:
  python diagnose_hold.py --order SO01376525
  python diagnose_hold.py --orders SO01376525 SO01376524
  python diagnose_hold.py --order SO01376525 --release
"""
import argparse
import concurrent.futures
import json
import os
import sys
import time
import urllib.error
import urllib.parse

sys.path.insert(0, os.path.dirname(__file__))
import oms_client


def safe_get(path, params=None):
    try:
        return oms_client.get(path, params)
    except urllib.error.HTTPError as exc:
        return {"_fetchError": True, "status": exc.code, "message": str(exc)}
    except urllib.error.URLError as exc:
        return {"_fetchError": True, "message": str(exc)}


def safe_post(path, body=None, extra_headers=None):
    try:
        return oms_client.post(path, body, extra_headers=extra_headers)
    except urllib.error.HTTPError as exc:
        return {"_fetchError": True, "status": exc.code, "message": str(exc)}
    except urllib.error.URLError as exc:
        return {"_fetchError": True, "message": str(exc)}


def unwrap_data(response):
    return response.get("data") if isinstance(response, dict) else None


def as_list(value):
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def build_rule_request(order_no, merchant_no, order_data):
    return {
        "merchantNo": merchant_no,
        "businessKey": order_no,
        "testMode": False,
        "facts": {"order": order_data},
        "variables": {"stopOnFirstMatch": False},
    }


def summarize_items(order_data):
    lines = []
    for row in as_list(order_data.get("itemLines") if isinstance(order_data, dict) else []):
        if not isinstance(row, dict):
            continue
        qty = row.get("qty") or 0
        allocated = row.get("allocatedQty") or 0
        try:
            remaining = float(qty or 0) - float(allocated or 0)
        except (TypeError, ValueError):
            remaining = None
        lines.append(
            {
                "sku": row.get("sku") or row.get("originalSku"),
                "qty": qty,
                "allocatedQty": allocated,
                "remainingQty": remaining,
                "uom": row.get("uom"),
            }
        )
    return lines


def summarize_allocation_items(order_no):
    response = safe_get(f"/api/linker-oms/opc/app-api/dispatch/hand/item/{order_no}")
    data = unwrap_data(response)
    if isinstance(response, dict) and response.get("code") not in (0, None):
        return {
            "fetchStatus": "failed",
            "businessCode": response.get("code"),
            "message": response.get("msg"),
            "totalRemainingQty": None,
            "lines": [],
        }
    rows = data.get("itemVOList") if isinstance(data, dict) else as_list(data)
    total = 0
    lines = []
    for row in as_list(rows):
        if not isinstance(row, dict):
            continue
        remaining = row.get("remaining")
        if remaining is None:
            remaining = row.get("remainingQty") or row.get("remainQty")
        try:
            total += float(remaining or 0)
        except (TypeError, ValueError):
            pass
        lines.append(
            {
                "sku": row.get("sku") or row.get("itemSku"),
                "orderedQty": row.get("totalQty") or row.get("qty"),
                "allocatedQty": row.get("allocated"),
                "remainingQty": remaining,
                "uom": row.get("uom"),
            }
        )
    return {"fetchStatus": "ok", "totalRemainingQty": total, "lines": lines}


def fetch_hold_rule(order_no, order_data):
    if order_data.get("status") != "ON_HOLD":
        return {
            "ruleExecutionStatus": "NOT_APPLICABLE",
            "matched": None,
            "matchedRuleCount": None,
            "matchedRules": [],
            "executedActions": [],
            "executionLogs": [],
            "errors": [],
            "confirmed": ["order_detail", "not_currently_on_hold"],
            "unconfirmed": [],
        }

    response = safe_post(
        "/api/linker-oms/oas/rpc-api/rule/types/ORDER_HOLD_OR/execute",
        build_rule_request(order_no, oms_client._env("OMS_MERCHANT_NO"), order_data),
        extra_headers={"trace": "true", "locale": "zh-CN"},
    )
    if isinstance(response, dict) and response.get("_fetchError"):
        return {
            "ruleExecutionStatus": "UNAVAILABLE",
            "matched": None,
            "matchedRuleCount": None,
            "matchedRules": [],
            "executedActions": [],
            "executionLogs": [],
            "errors": [f"ORDER_HOLD_OR lookup failed: {response.get('status') or response.get('message')}"],
            "confirmed": ["order_detail"],
            "unconfirmed": ["specific_hold_rule_reason"],
        }
    data = unwrap_data(response) or {}
    return {
        "ruleExecutionStatus": data.get("status"),
        "matched": data.get("matched"),
        "matchedRuleCount": data.get("matchedRuleCount"),
        "matchedRules": data.get("matchedRules") or [],
        "executedActions": data.get("executedActions") or [],
        "executionLogs": data.get("executionLogs") or [],
        "errors": data.get("errors") or [],
        "confirmed": ["order_detail"],
        "unconfirmed": [] if data.get("matchedRules") or data.get("executionLogs") else ["specific_hold_rule_reason"],
    }


def release_hold(order_no):
    return safe_post(f"/api/linker-oms/opc/app-api/order-hold/release?orderNo={urllib.parse.quote(order_no)}")


def build_user_summary(result):
    order_no = result.get("orderNo")
    status = result.get("status")
    rule = result.get("holdRuleSummary") or {}
    allocation = result.get("allocationSummary") or {}
    release = result.get("releaseResult")

    if result.get("state") == "not_found":
        return (
            f"结论：没有查到订单 {order_no} 的有效详情，暂时不能判断 hold 状态。\n"
            f"原因：{result.get('reason')}\n"
            "下一步：确认订单号、商户和环境后重新查询。"
        )
    if status != "ON_HOLD":
        lines = [
            f"结论：订单 {order_no} 最新状态是 {status}，当前不是 ON_HOLD。\n"
            "原因：订单详情已确认没有 active hold；因此不需要 release hold。\n"
            "下一步：如果要查历史 hold 原因，需要看订单 event/log 或 OMS hold 历史记录。"
        ]
        if release:
            lines.append(
                f"Release 处理：{release.get('businessResult')}；submittedToOms={release.get('submittedToOms')}。"
            )
        return "\n".join(lines)

    if rule.get("unconfirmed"):
        reason_text = "当前只能确认订单处于 ON_HOLD，但 staging 的 ORDER_HOLD_OR 规则接口不可用/无命中记录，具体 hold 规则原因未确认。"
    else:
        reason_text = f"命中 hold 规则/日志：{rule.get('matchedRules') or rule.get('executionLogs')}"
    remaining = allocation.get("totalRemainingQty")
    alloc_text = f"allocation remaining={remaining}，这用于区分是否还存在未分仓商品。"
    lines = [
        f"结论：订单 {order_no} 当前是 ON_HOLD。",
        f"原因：{reason_text}",
        f"分仓状态：{alloc_text}",
    ]
    if release:
        business = release.get("businessResult")
        post = release.get("postCheck") or {}
        lines.append(
            f"Release 结果：{business}；接口 code={release.get('code')}，data={release.get('data')}，复查状态={post.get('status')}。"
        )
        if business == "released":
            lines.append("下一步：按复查后的最新状态继续处理，不要只凭提交结果判断流程完成。")
        else:
            lines.append("下一步：不要把本次 release 说成成功；需要继续查 hold 规则/OMS hold 记录或人工处理。")
    else:
        lines.append("下一步：如要 release hold，需要用户明确确认；执行后必须复查订单状态。")
    return "\n".join(lines)


def diagnose_one(order_no, do_release=False):
    started = time.perf_counter()
    order_response = safe_get(f"/api/linker-oms/opc/app-api/sale-order/{order_no}")
    order_data = unwrap_data(order_response) or {}
    if not order_data or (isinstance(order_response, dict) and order_response.get("code") not in (0, None)):
        result = {
            "orderNo": order_no,
            "state": "not_found",
            "status": None,
            "reason": order_response.get("msg") if isinstance(order_response, dict) else "Order detail was not returned.",
        }
        result["userFacingSummary"] = build_user_summary(result)
        result["durationMs"] = int((time.perf_counter() - started) * 1000)
        return result

    status = order_data.get("status")
    result = {
        "orderNo": order_data.get("orderNo") or order_no,
        "state": "on_hold" if status == "ON_HOLD" else "not_on_hold",
        "status": status,
        "channelName": order_data.get("channelName"),
        "channelSalesOrderNo": order_data.get("channelSalesOrderNo"),
        "financialStatus": order_data.get("financialStatus"),
        "items": summarize_items(order_data),
        "holdRuleSummary": fetch_hold_rule(order_no, order_data),
        "allocationSummary": summarize_allocation_items(order_no),
    }

    if do_release and status != "ON_HOLD":
        result["releaseResult"] = {
            "businessResult": "not_submitted",
            "submittedToOms": False,
            "reason": "latest_status_is_not_on_hold",
            "postCheck": {
                "status": status,
                "statusName": order_data.get("statusName"),
            },
        }
    elif do_release:
        release_response = release_hold(order_no)
        post_response = safe_get(f"/api/linker-oms/opc/app-api/sale-order/{order_no}")
        post_data = unwrap_data(post_response) or {}
        business_result = "released" if release_response.get("code") == 0 and release_response.get("data") is True else "not_released"
        if business_result == "released" and post_data.get("status") == "ON_HOLD":
            business_result = "submitted_but_still_on_hold"
        result["releaseResult"] = {
            "code": release_response.get("code"),
            "data": release_response.get("data"),
            "msg": release_response.get("msg"),
            "businessResult": business_result,
            "submittedToOms": True,
            "postCheck": {
                "status": post_data.get("status"),
                "statusName": post_data.get("statusName"),
            },
        }

    result["userFacingSummary"] = build_user_summary(result)
    result["durationMs"] = int((time.perf_counter() - started) * 1000)
    return result


def parse_orders(args):
    orders = []
    if args.order:
        orders.append(args.order)
    for value in args.orders or []:
        for part in str(value).replace(",", " ").split():
            if part.strip():
                orders.append(part.strip())
    return list(dict.fromkeys(orders))


def build_batch_summary(results):
    counts = {}
    for result in results:
        state = result.get("state") or "unknown"
        counts[state] = counts.get(state, 0) + 1
    release_counts = {}
    for result in results:
        release = result.get("releaseResult")
        if release:
            key = release.get("businessResult") or "unknown"
            release_counts[key] = release_counts.get(key, 0) + 1
    return {"total": len(results), "counts": counts, "releaseCounts": release_counts}


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--order", default=None)
    parser.add_argument("--orders", nargs="*", default=[])
    parser.add_argument("--release", action="store_true")
    parser.add_argument("--max-workers", type=int, default=4)
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    orders = parse_orders(args)
    if not orders:
        parser.error("Provide --order or --orders")

    started = time.perf_counter()
    workers = max(1, min(args.max_workers, 8, len(orders)))
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(diagnose_one, order_no, args.release) for order_no in orders]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    results.sort(key=lambda row: orders.index(row["orderNo"]) if row.get("orderNo") in orders else len(orders))

    print(
        json.dumps(
            {
                "_env": oms_client.get_env_label(),
                "durationMs": int((time.perf_counter() - started) * 1000),
                "batchSummary": build_batch_summary(results),
                "results": results,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
