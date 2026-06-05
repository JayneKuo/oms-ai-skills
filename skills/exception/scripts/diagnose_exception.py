"""
Diagnose EXCEPTION sales orders with business-friendly cause/action summaries.

Examples:
  python diagnose_exception.py --order SO01373341
  python diagnose_exception.py --orders SO01373341 SO01373322
  python diagnose_exception.py --from-list --size 10
"""
import argparse
import concurrent.futures
import json
import os
import re
import sys
import time
from urllib.error import HTTPError, URLError

sys.path.insert(0, os.path.dirname(__file__))
import oms_client


OUT_OF_STOCK_RE = re.compile(r"Product\s+(.+?)\s+is currently out of stock", re.IGNORECASE)


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


def unwrap_data(response):
    return response.get("data") if isinstance(response, dict) else None


def as_list(value):
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def query_exception_orders(page, size):
    return safe_get(
        "/api/linker-oms/opc/app-api/sale-order/page",
        {
            "pageNo": page,
            "pageSize": size,
            "merchantNo": oms_client._env("OMS_MERCHANT_NO"),
            "statuses": ["EXCEPTION"],
        },
    )


def summarize_items(order_data):
    lines = []
    unallocated = []
    for row in as_list(order_data.get("itemLines") if isinstance(order_data, dict) else []):
        if not isinstance(row, dict):
            continue
        qty = row.get("qty") or 0
        allocated = row.get("allocatedQty") or 0
        try:
            remaining = float(qty or 0) - float(allocated or 0)
        except (TypeError, ValueError):
            remaining = None
        line = {
            "sku": row.get("sku") or row.get("originalSku"),
            "qty": qty,
            "allocatedQty": allocated,
            "remainingQty": remaining,
            "uom": row.get("uom"),
        }
        lines.append(line)
        if remaining is not None and remaining > 0:
            unallocated.append(line)
    return {"lines": lines, "unallocatedLines": unallocated}


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
    rows = []
    if isinstance(data, dict) and isinstance(data.get("itemVOList"), list):
        rows = data.get("itemVOList")
    else:
        rows = as_list(data)
    total = 0
    lines = []
    for row in rows:
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


def fetch_dispatch_explain(order_no):
    return safe_get(
        "/api/linker-oms/opc/public-api/dispatch/dispatch-log/explain",
        {"orderNo": order_no},
    )


def summarize_dispatch_explain(response):
    data = unwrap_data(response)
    rows = as_list(data)
    event_types = []
    event_id = None
    for row in rows:
        if not isinstance(row, dict):
            continue
        event_id = event_id or row.get("eventId")
        if row.get("eventType"):
            event_types.append(row.get("eventType"))
    return {
        "fetchStatus": "failed" if isinstance(response, dict) and response.get("_fetchError") else "ok",
        "eventId": event_id,
        "eventCount": len(rows),
        "eventTypes": event_types,
    }


def extract_out_of_stock_sku(message):
    if not message:
        return None
    match = OUT_OF_STOCK_RE.search(str(message))
    return match.group(1).strip() if match else None


def build_diagnosis(order_no, order_response, allocation_summary, dispatch_summary):
    order_data = unwrap_data(order_response) or {}
    if not order_data or (isinstance(order_response, dict) and order_response.get("code") not in (0, None)):
        return {
            "orderNo": order_no,
            "state": "not_found",
            "status": None,
            "causeConfirmed": False,
            "category": "ORDER_NOT_FOUND_OR_INACCESSIBLE",
            "reason": order_response.get("msg") if isinstance(order_response, dict) else "Order detail was not returned.",
            "solution": "Confirm the order number, merchant, and environment before diagnosing.",
            "nextStep": "Re-query with a valid order number.",
        }

    status = order_data.get("status")
    item_summary = summarize_items(order_data)
    reserve = order_data.get("reserve1") or order_data.get("shipMessage") or order_data.get("notificationMsg")
    out_of_stock_sku = extract_out_of_stock_sku(reserve)
    dispatches = as_list(order_data.get("orderDispatchList"))

    base = {
        "orderNo": order_data.get("orderNo") or order_no,
        "status": status,
        "channelName": order_data.get("channelName"),
        "channelSalesOrderNo": order_data.get("channelSalesOrderNo"),
        "dispatchCount": len(dispatches),
        "items": item_summary.get("lines"),
        "allocationSummary": allocation_summary,
        "dispatchExplainSummary": dispatch_summary,
    }

    if status != "EXCEPTION":
        base.update(
            {
                "state": "status_changed",
                "causeConfirmed": True,
                "category": "STATUS_CHANGED_FROM_EXCEPTION",
                "reason": f"The latest order detail status is {status}, so this is no longer an active EXCEPTION order.",
                "solution": "Do not reopen or allocate based on a stale EXCEPTION list row.",
                "nextStep": "Continue with the skill that matches the latest status.",
            }
        )
        return base

    if out_of_stock_sku:
        base.update(
            {
                "state": "exception",
                "causeConfirmed": True,
                "category": "OUT_OF_STOCK",
                "affectedSkus": [out_of_stock_sku],
                "reason": reserve,
                "solution": f"先为 SKU {out_of_stock_sku} 补货或确认可用库存；库存到位后再重新触发订单处理流程。",
                "nextStep": "交给 replenishment 做补货/采购建议；补货完成后，如业务确认需要重试，再由 allocation 执行 reopen-for-allocation retry。",
            }
        )
        return base

    if item_summary.get("unallocatedLines") and not dispatches:
        skus = [line.get("sku") for line in item_summary.get("unallocatedLines") if line.get("sku")]
        base.update(
            {
                "state": "exception",
                "causeConfirmed": False,
                "category": "UNALLOCATED_WITHOUT_CONFIRMED_CAUSE",
                "affectedSkus": skus,
                "reason": "The order is EXCEPTION, has no dispatch, and item quantities are not allocated, but no explicit exception message was found.",
                "solution": "先补查分仓/路由/库存证据，再决定是补货、分仓还是 reopen。",
                "nextStep": "交给 allocation 查 dispatch/routing evidence；如果确认缺货，再交给 replenishment。",
            }
        )
        return base

    base.update(
        {
            "state": "exception",
            "causeConfirmed": False,
            "category": "UNKNOWN_EXCEPTION_CAUSE",
            "reason": "The order is EXCEPTION, but detail fields do not contain a confirmed cause.",
            "solution": "不要猜原因；需要继续查 dispatch log、allocation evidence 或订单异常日志。",
            "nextStep": "先补充日志证据，再决定是否需要 reopen、分仓或补货。",
        }
    )
    return base


def build_user_summary(result):
    if result.get("state") == "not_found":
        return (
            f"结论：没有查到订单 {result.get('orderNo')} 的有效详情，暂时不能诊断异常。\n"
            f"原因：{result.get('reason') or '订单详情接口没有返回有效数据'}。\n"
            "下一步：确认订单号、商户和环境后重新查询。"
        )
    if result.get("state") == "status_changed":
        return (
            f"结论：订单 {result.get('orderNo')} 最新状态是 {result.get('status')}，已经不是 EXCEPTION。\n"
            f"原因：{result.get('reason')}\n"
            "下一步：不要按异常单执行 reopen 或分仓，改按最新状态继续处理。"
        )
    confidence = "已确认" if result.get("causeConfirmed") else "未完全确认"
    sku_text = ", ".join(result.get("affectedSkus") or [])
    sku_line = f"\n影响 SKU：{sku_text}" if sku_text else ""
    return (
        f"结论：订单 {result.get('orderNo')} 当前仍是 EXCEPTION，异常原因{confidence}。\n"
        f"原因：{result.get('reason')}{sku_line}\n"
        f"解决方案：{result.get('solution')}\n"
        f"下一步：{result.get('nextStep')}"
    )


def diagnose_one(order_no):
    started = time.perf_counter()
    try:
        order_response = safe_get(f"/api/linker-oms/opc/app-api/sale-order/{order_no}")
        allocation_summary = summarize_allocation_items(order_no)
        dispatch_summary = summarize_dispatch_explain(fetch_dispatch_explain(order_no))
        result = build_diagnosis(order_no, order_response, allocation_summary, dispatch_summary)
        result["userFacingSummary"] = build_user_summary(result)
        result["durationMs"] = int((time.perf_counter() - started) * 1000)
        return result
    except Exception as exc:
        return {
            "orderNo": order_no,
            "state": "error",
            "causeConfirmed": False,
            "category": "SCRIPT_ERROR",
            "reason": str(exc),
            "solution": "Retry or inspect the script/API error.",
            "nextStep": "Do not execute writes until diagnosis succeeds.",
            "durationMs": int((time.perf_counter() - started) * 1000),
        }


def parse_orders(args):
    orders = []
    for value in args.orders or []:
        for part in str(value).replace(",", " ").split():
            if part.strip():
                orders.append(part.strip())
    if args.order:
        orders.insert(0, args.order)
    if args.from_list:
        response = query_exception_orders(args.page, args.size)
        data = unwrap_data(response) or {}
        for row in as_list(data.get("list")):
            if isinstance(row, dict) and row.get("orderNo"):
                orders.append(row.get("orderNo"))
    return list(dict.fromkeys(orders))


def build_batch_summary(results):
    counts = {}
    for result in results:
        state = result.get("state") or "unknown"
        counts[state] = counts.get(state, 0) + 1
    return {
        "total": len(results),
        "counts": counts,
        "confirmedCauseCount": sum(1 for result in results if result.get("causeConfirmed")),
        "actionBuckets": {
            "replenishment": [r.get("orderNo") for r in results if r.get("category") == "OUT_OF_STOCK"],
            "allocationEvidenceNeeded": [
                r.get("orderNo") for r in results if r.get("category") == "UNALLOCATED_WITHOUT_CONFIRMED_CAUSE"
            ],
            "statusChanged": [r.get("orderNo") for r in results if r.get("state") == "status_changed"],
        },
    }


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--order", default=None)
    parser.add_argument("--orders", nargs="*", default=[])
    parser.add_argument("--from-list", action="store_true")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--size", type=int, default=5)
    parser.add_argument("--max-workers", type=int, default=4)
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    orders = parse_orders(args)
    if not orders:
        parser.error("Provide --order, --orders, or --from-list")
    workers = max(1, min(args.max_workers, 8, len(orders)))
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(diagnose_one, order_no) for order_no in orders]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    results.sort(key=lambda row: orders.index(row["orderNo"]) if row.get("orderNo") in orders else len(orders))
    output = {
        "_env": oms_client.get_env_label(),
        "durationMs": int((time.perf_counter() - started) * 1000),
        "batchSummary": build_batch_summary(results),
        "results": results,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
