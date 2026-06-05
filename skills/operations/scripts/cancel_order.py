"""
Cancel sales orders.

The OMS cancel endpoint may return success, fail, or ongoing rows. Ongoing means
the cancellation request has been accepted and downstream processing such as
Kafka/WMS cancellation is still in progress; it is not a completed cancellation.

Usage:
  python cancel_order.py --orders SO001
  python cancel_order.py --orders SO001 SO002 SO003
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import oms_client


def as_list(value):
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def get_detail(order_no):
    try:
        return oms_client.get(f"/api/linker-oms/opc/app-api/sale-order/{order_no}")
    except Exception as exc:
        return {"_fetchError": True, "message": str(exc)}


def summarize_dispatches(order_detail):
    data = order_detail.get("data") if isinstance(order_detail, dict) else {}
    dispatches = []
    for dispatch in as_list(data.get("orderDispatchList") if isinstance(data, dict) else []):
        if not isinstance(dispatch, dict):
            continue
        dispatches.append(
            {
                "dispatchNo": dispatch.get("dispatchNo") or dispatch.get("orderDispatchNo"),
                "status": dispatch.get("status"),
                "statusName": dispatch.get("statusName"),
                "warehouseName": dispatch.get("warehouseName"),
                "wmsStatus": dispatch.get("wmsStatus") or dispatch.get("wmsStatusName"),
            }
        )
    return dispatches


def is_cancelled_dispatch(dispatch):
    status = dispatch.get("status")
    status_name = str(dispatch.get("statusName") or "").upper()
    return status in (8, "8", "CANCELLED", "Cancelled") or status_name == "CANCELLED"


def row_order_no(row):
    if not isinstance(row, dict):
        return None
    return row.get("orderNo") or row.get("salesOrderNo") or row.get("businessNo")


def summarize_cancel_result(result):
    data = result.get("data") or {}
    success_rows = data.get("successRespDTOS") or []
    failed_rows = data.get("failRespDTOS") or []
    ongoing_rows = data.get("ongoingRespDTOS") or []

    if failed_rows:
        state = "failed"
    elif ongoing_rows:
        state = "ongoing"
    elif success_rows:
        state = "completed"
    elif result.get("code") == 0:
        state = "accepted_no_rows"
    else:
        state = "failed"

    return {
        "state": state,
        "successCount": len(success_rows),
        "failedCount": len(failed_rows),
        "ongoingCount": len(ongoing_rows),
        "message": (
            "Cancellation is still being processed downstream; re-check order and dispatch status before calling it successful."
            if state == "ongoing"
            else "Cancellation completed for returned success rows."
            if state == "completed"
            else "Cancellation failed for returned failed rows."
            if state == "failed"
            else "OMS accepted the request but did not return row-level status."
        ),
        "successOrders": [row_order_no(row) for row in success_rows if row_order_no(row)],
        "failedOrders": [row_order_no(row) for row in failed_rows if row_order_no(row)],
        "ongoingOrders": [row_order_no(row) for row in ongoing_rows if row_order_no(row)],
    }


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--orders", nargs="+", required=True, help="One or more order numbers")
    parser.add_argument("--post-check-delay", type=float, default=1.0, help="Seconds to wait before post-cancel detail check")
    parser.add_argument("--skip-post-check", action="store_true")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    body = {
        "merchantNo": oms_client._env("OMS_MERCHANT_NO"),
        "orderNos": args.orders
    }

    result = oms_client.post("/api/linker-oms/opc/app-api/sale-order/cancel", body)
    result["_env"] = oms_client.get_env_label()
    result["businessSummary"] = summarize_cancel_result(result)
    if not args.skip_post_check:
        if args.post_check_delay > 0:
            time.sleep(min(args.post_check_delay, 10))
        post_checks = []
        for order_no in args.orders:
            detail = get_detail(order_no)
            data = detail.get("data") if isinstance(detail, dict) else {}
            dispatches = summarize_dispatches(detail)
            sales_status = data.get("status") if isinstance(data, dict) else None
            fully_cancelled = sales_status == "CANCELLED" and (
                not dispatches or all(is_cancelled_dispatch(row) for row in dispatches)
            )
            post_checks.append(
                {
                    "orderNo": order_no,
                    "fetchOk": isinstance(detail, dict) and not detail.get("_fetchError") and detail.get("code") == 0,
                    "salesOrderStatus": sales_status,
                    "salesOrderStatusName": data.get("statusName") if isinstance(data, dict) else None,
                    "dispatches": dispatches,
                    "fullyCancelled": fully_cancelled,
                    "businessResult": "cancelled" if fully_cancelled else "not_confirmed",
                }
            )
        result["postCancelChecks"] = post_checks
        result["businessSummary"]["postCheck"] = {
            "checked": True,
            "fullyCancelledCount": sum(1 for row in post_checks if row.get("fullyCancelled")),
            "notConfirmedCount": sum(1 for row in post_checks if not row.get("fullyCancelled")),
        }
        if post_checks and all(row.get("fullyCancelled") for row in post_checks):
            result["businessSummary"]["finalBusinessState"] = "cancelled"
            if result["businessSummary"]["state"] == "failed":
                result["businessSummary"]["message"] = (
                    "The cancel submission was rejected for at least one row, but post-check confirms "
                    "the target order(s) are already cancelled."
                )
        elif result["businessSummary"]["state"] == "ongoing":
            result["businessSummary"]["finalBusinessState"] = "not_confirmed"
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
