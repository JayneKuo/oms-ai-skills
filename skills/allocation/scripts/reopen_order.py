"""
Reopen an EXCEPTION sales order so it can re-enter allocation/dispatch processing.

Ownership note:
  Reopen is treated as an allocation workflow because the business purpose is to
  let an exception order retry allocation/dispatch after the blocker is resolved.

Usage:
  python reopen_order.py --order SO00361770 --confirm-reopen
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import oms_client
import explain_warehouse_assignment as warehouse_explainer


def get_detail(order_no):
    try:
        return oms_client.get(f"/api/linker-oms/opc/app-api/sale-order/{order_no}")
    except Exception as exc:
        return {"_fetchError": True, "message": str(exc)}


def summarize_reopen(order_no, result):
    if result.get("code") == 0 and result.get("data") is not False:
        state = "accepted"
        message = (
            "OMS accepted the reopen request. Re-check order detail and allocation evidence "
            "before saying allocation/dispatch has recovered."
        )
    else:
        state = "rejected"
        message = result.get("msg") or "OMS rejected the reopen request."
    return {"orderNo": order_no, "state": state, "message": message}


def post_reopen_check(order_no):
    detail = get_detail(order_no)
    data = detail.get("data") if isinstance(detail, dict) else {}
    allocation_response = warehouse_explainer.safe_get(
        f"/api/linker-oms/opc/app-api/dispatch/hand/item/{order_no}"
    )
    return {
        "fetchOk": isinstance(detail, dict) and not detail.get("_fetchError") and detail.get("code") == 0,
        "status": data.get("status") if isinstance(data, dict) else None,
        "statusName": data.get("statusName") if isinstance(data, dict) else None,
        "dispatchCount": len(data.get("orderDispatchList") or []) if isinstance(data, dict) else 0,
        "allocationSummary": warehouse_explainer.summarize_allocation_items(allocation_response),
    }


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--order", required=True, help="Sales order number")
    parser.add_argument("--confirm-reopen", action="store_true", help="Required to submit a real reopen request to OMS.")
    parser.add_argument("--post-check-delay", type=float, default=1.0)
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    if not args.confirm_reopen:
        print(json.dumps({
            "code": "CONFIRMATION_REQUIRED",
            "_env": oms_client.get_env_label(),
            "_request": {
                "submittedToOms": False,
                "requiredConfirmationFlag": "--confirm-reopen",
                "operation": "reopen_for_allocation_retry",
                "orderNo": args.order,
            },
            "businessSummary": {
                "orderNo": args.order,
                "state": "not_submitted",
                "message": "This is a real OMS allocation retry action. Re-run with --confirm-reopen only after user second confirmation.",
            },
        }, indent=2, ensure_ascii=False))
        return

    result = oms_client.post(f"/api/linker-oms/opc/app-api/sale-order/reopen/{args.order}")
    result["_env"] = oms_client.get_env_label()
    result["_request"] = {
        "submittedToOms": True,
        "operation": "reopen_for_allocation_retry",
        "orderNo": args.order,
    }
    result["businessSummary"] = summarize_reopen(args.order, result)
    if args.post_check_delay > 0:
        time.sleep(min(args.post_check_delay, 10))
    result["postReopenCheck"] = post_reopen_check(args.order)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
