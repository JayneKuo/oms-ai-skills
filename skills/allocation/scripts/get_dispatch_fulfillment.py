"""
Read allocation-owned dispatch and fulfillment state for one sales order.

This is a read-only helper. It does not cancel, release, allocate, or submit
anything to OMS. Use it when the user asks about dispatch, DN, WMS handoff,
warehouse processing, fulfillment progress, or "why it is not shipped yet".

Usage:
  python get_dispatch_fulfillment.py --order SO01405073
"""
import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError

sys.path.insert(0, os.path.dirname(__file__))
import oms_client
import explain_warehouse_assignment as explainer


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


def find_first(obj, key_names):
    return explainer.find_first(obj, key_names)


def unwrap_data(response):
    return explainer.unwrap_data(response)


def extract_order_items(order_data):
    rows = []
    candidates = [
        order_data.get("orderItemList") if isinstance(order_data, dict) else None,
        order_data.get("items") if isinstance(order_data, dict) else None,
        order_data.get("itemList") if isinstance(order_data, dict) else None,
    ]
    for candidate in candidates:
        if isinstance(candidate, list):
            rows = candidate
            break
    result = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        result.append(
            {
                "sku": find_first(row, ["sku", "itemSku", "productSku"]),
                "orderedQty": find_first(row, ["qty", "quantity", "orderedQty", "totalQty"]),
                "uom": find_first(row, ["uom", "unit"]),
                "name": find_first(row, ["name", "productName", "itemName"]),
            }
        )
    return result[:50]


def extract_dispatch_items(dispatch):
    rows = []
    for key in ("dispatchItemList", "itemList", "items", "details"):
        if isinstance(dispatch, dict) and isinstance(dispatch.get(key), list):
            rows = dispatch.get(key)
            break
    result = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        result.append(
            {
                "sku": find_first(row, ["sku", "itemSku", "productSku"]),
                "qty": find_first(row, ["qty", "quantity", "dispatchQty", "allocatedQty"]),
                "uom": find_first(row, ["uom", "unit"]),
                "status": find_first(row, ["statusName", "status"]),
            }
        )
    return result[:50]


def extract_dispatches(order_data):
    dispatches = explainer.extract_dispatches(order_data)
    result = []
    for dispatch in dispatches:
        if not isinstance(dispatch, dict):
            continue
        result.append(
            {
                "dispatchNo": find_first(dispatch, ["dispatchNo", "dispatchOrderNo", "orderDispatchNo"]),
                "behindOrderNo": find_first(dispatch, ["behindOrderNo", "dnNo", "deliveryNo"]),
                "warehouseName": find_first(dispatch, ["warehouseName", "warehouse", "shipFromWarehouseName"]),
                "warehouseCode": find_first(dispatch, ["warehouseCode", "accountingCode", "warehouseId"]),
                "status": find_first(dispatch, ["status", "dispatchStatus"]),
                "statusName": find_first(dispatch, ["statusName", "dispatchStatusName"]),
                "sendType": find_first(dispatch, ["sendType"]),
                "dispatchType": find_first(dispatch, ["dispatchType"]),
                "warehouseVersion": find_first(dispatch, ["warehouseVersion"]),
                "warehouseDataChannel": find_first(dispatch, ["warehouseDataChannel", "dataChannel"]),
                "callbackTime": find_first(dispatch, ["callbackTime", "lastCallbackTime", "updatedAt"]),
                "items": extract_dispatch_items(dispatch),
            }
        )
    return result


def classify_stage(order_summary, dispatches):
    status_text = " ".join(
        str(value or "")
        for value in [
            order_summary.get("status"),
            order_summary.get("statusName"),
            *(item.get("statusName") for item in dispatches),
            *(item.get("status") for item in dispatches),
        ]
    ).lower()
    if not dispatches:
        return {
            "stage": "not_dispatched",
            "businessMeaning": "No dispatch record was found, so warehouse fulfillment has not been handed off from the fetched order detail.",
            "nextStep": "Check allocation eligibility and allocation explain evidence before expecting WMS progress.",
        }
    if "cancel" in status_text:
        return {
            "stage": "cancelled",
            "businessMeaning": "The order or dispatch is cancelled in the fetched state.",
            "nextStep": "No allocation action is needed unless the business wants a new order/retry path.",
        }
    if "ship" in status_text:
        return {
            "stage": "shipped_or_shipping",
            "businessMeaning": "The fetched status indicates shipment progress.",
            "nextStep": "Use tracking/logistics tools if the user needs carrier-level tracking.",
        }
    if "warehouse received" in status_text or "warehouse_processing" in status_text or "warehouse processing" in status_text:
        return {
            "stage": "warehouse_processing",
            "businessMeaning": "OMS has dispatched the order and the warehouse/WMS side has received or is processing it.",
            "nextStep": "Allocation is done. Continue with warehouse/WMS progress checks only if the user asks why fulfillment has not advanced.",
        }
    return {
        "stage": "dispatched_pending_or_unknown",
        "businessMeaning": "A dispatch exists, but the fetched fields do not prove the final warehouse processing/shipping stage.",
        "nextStep": "Check dispatch logs or WMS events for more detailed fulfillment progress.",
    }


def build_user_summary(order_summary, dispatches, allocation_summary, explain_summary, stage):
    order_no = order_summary.get("orderNo") or "unknown"
    status = order_summary.get("statusName") or order_summary.get("status") or "unknown"
    if not dispatches:
        return (
            f"Result: order {order_no} is {status}, but no dispatch/DN was found in the fetched detail.\n"
            f"Allocation remaining qty: {allocation_summary.get('totalRemainingQty')}.\n"
            f"Business meaning: {stage['businessMeaning']}\n"
            f"Next step: {stage['nextStep']}"
        )
    parts = []
    for row in dispatches:
        parts.append(
            f"{row.get('dispatchNo') or 'no-dispatch-no'} / DN {row.get('behindOrderNo') or 'not found'} / "
            f"{row.get('warehouseName') or 'unknown warehouse'} / "
            f"{row.get('statusName') or row.get('status') or 'unknown status'}"
        )
    explain_count = explain_summary.get("eventCount") if isinstance(explain_summary, dict) else 0
    explain_text = (
        f"Dispatch explain events: {explain_count}."
        if explain_count
        else "Dispatch explain events were not found or did not return evidence."
    )
    return (
        f"Result: order {order_no} is {status}; dispatch/fulfillment state is {stage['stage']}.\n"
        f"Dispatches: {'; '.join(parts)}.\n"
        f"Allocation remaining qty: {allocation_summary.get('totalRemainingQty')}.\n"
        f"Evidence: order detail dispatch records; {explain_text}\n"
        f"Business meaning: {stage['businessMeaning']}\n"
        f"Next step: {stage['nextStep']}"
    )


def summarize_dispatch_fulfillment(order_no):
    order_response = safe_get(f"/api/linker-oms/opc/app-api/sale-order/{order_no}")
    order_data = unwrap_data(order_response) or {}
    allocation_response = safe_get(f"/api/linker-oms/opc/app-api/dispatch/hand/item/{order_no}")
    dispatch_explain_response = explainer.fetch_dispatch_explain(order_no)

    order_summary = explainer.extract_order_summary(order_data)
    order_summary["orderNo"] = order_summary.get("orderNo") or order_no
    order_summary["statusName"] = find_first(order_data, ["statusName", "orderStatusName"])
    if not order_data or (isinstance(order_response, dict) and order_response.get("code") not in (0, None)):
        order_summary["lookupStatus"] = "ORDER_NOT_FOUND_OR_INACCESSIBLE"
        order_summary["lookupCode"] = order_response.get("code") if isinstance(order_response, dict) else None
        order_summary["lookupMessage"] = order_response.get("msg") if isinstance(order_response, dict) else None

    dispatches = extract_dispatches(order_data)
    allocation_summary = explainer.summarize_allocation_items(allocation_response)
    explain_summary = explainer.summarize_dispatch_explain(dispatch_explain_response)
    stage = classify_stage(order_summary, dispatches)
    return {
        "orderSummary": order_summary,
        "fulfillmentStage": stage,
        "dispatches": dispatches,
        "orderItems": extract_order_items(order_data),
        "allocationSummary": allocation_summary,
        "dispatchExplainSummary": {
            "fetchStatus": explain_summary.get("fetchStatus"),
            "eventId": explain_summary.get("eventId"),
            "eventCount": explain_summary.get("eventCount"),
            "finalDispatches": explain_summary.get("finalDispatches"),
        },
        "userFacingSummary": build_user_summary(order_summary, dispatches, allocation_summary, explain_summary, stage),
        "_env": oms_client.get_env_label(),
    }


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--order", required=True, help="Sales order number")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    print(json.dumps(summarize_dispatch_fulfillment(args.order), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
