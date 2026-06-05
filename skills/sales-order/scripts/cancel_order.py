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

sys.path.insert(0, os.path.dirname(__file__))
import oms_client


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
        )
    }


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--orders", nargs="+", required=True, help="One or more order numbers")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    body = {
        "merchantNo": oms_client._env("OMS_MERCHANT_NO"),
        "orderNos": args.orders
    }

    result = oms_client.post("/api/linker-oms/opc/app-api/sale-order/cancel", body)
    result["_env"] = oms_client.get_env_label()
    result["businessSummary"] = summarize_cancel_result(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
