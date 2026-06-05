"""
Batch high-impact sales order operations.

Operations owns cancel only. Reopen/retry allocation belongs to the allocation skill.

Usage:
  python batch_orders.py --action cancel --orders SO001 SO002 --confirm-execute
"""
import argparse
import concurrent.futures
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import cancel_order
import oms_client


def cancel_many(order_nos, post_check_delay=1.0):
    result = oms_client.post(
        "/api/linker-oms/opc/app-api/sale-order/cancel",
        {"merchantNo": oms_client._env("OMS_MERCHANT_NO"), "orderNos": order_nos},
    )
    summary = cancel_order.summarize_cancel_result(result)
    if post_check_delay > 0:
        time.sleep(min(post_check_delay, 10))
    post_checks = []
    for order_no in order_nos:
        detail = cancel_order.get_detail(order_no)
        data = detail.get("data") if isinstance(detail, dict) else {}
        dispatches = cancel_order.summarize_dispatches(detail)
        sales_status = data.get("status") if isinstance(data, dict) else None
        fully_cancelled = sales_status == "CANCELLED" and (
            not dispatches or all(cancel_order.is_cancelled_dispatch(row) for row in dispatches)
        )
        post_checks.append(
            {
                "orderNo": order_no,
                "ok": fully_cancelled,
                "businessResult": "cancelled" if fully_cancelled else "not_confirmed",
                "salesOrderStatus": sales_status,
                "salesOrderStatusName": data.get("statusName") if isinstance(data, dict) else None,
                "dispatches": dispatches,
            }
        )
    if post_checks and all(row.get("ok") for row in post_checks):
        summary["finalBusinessState"] = "cancelled"
        if summary["state"] == "failed":
            summary["message"] = (
                "The cancel submission was rejected for at least one row, but post-check confirms "
                "the target order(s) are already cancelled."
            )
    elif summary["state"] == "ongoing":
        summary["finalBusinessState"] = "not_confirmed"
    return {
        "rawResult": result,
        "businessSummary": summary,
        "results": post_checks,
    }


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--action", required=True, choices=["cancel"])
    parser.add_argument("--orders", nargs="+", required=True, help="One or more order numbers")
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--post-check-delay", type=float, default=1.0)
    parser.add_argument("--confirm-execute", action="store_true", help="Required to submit real batch cancel requests to OMS.")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    if not args.confirm_execute:
        print(json.dumps({
            "code": "CONFIRMATION_REQUIRED",
            "_env": oms_client.get_env_label(),
            "_request": {
                "submittedToOms": False,
                "requiredConfirmationFlag": "--confirm-execute",
                "operation": "batch_cancel",
                "orders": args.orders,
            },
            "businessSummary": {
                "state": "not_submitted",
                "message": "This is a real OMS batch order action. Re-run with --confirm-execute only after user second confirmation.",
            },
        }, indent=2, ensure_ascii=False))
        return

    if args.action == "cancel":
        batch_result = cancel_many(args.orders, args.post_check_delay)
        results = batch_result["results"]
        success = sum(1 for item in results if item["ok"])
        output = {
            "action": args.action,
            "total": len(results),
            "success": success,
            "failed": len(results) - success,
            **batch_result,
            "_env": oms_client.get_env_label(),
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

if __name__ == "__main__":
    main()
