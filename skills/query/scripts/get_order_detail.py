"""
Fetch a single sales order detail.

Usage:
  python get_order_detail.py --order SO00361770
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import oms_client


STATUS_MEANINGS = {
    "IMPORTED": "Imported and waiting for the next OMS processing step.",
    "ALLOCATED": "Allocated and ready for downstream fulfillment steps.",
    "WAREHOUSE_PROCESSING": "Sent to warehouse processing/fulfillment.",
    "DISPATCHED": "Dispatched to warehouse flow.",
    "ON_HOLD": "Currently held and blocked from normal processing.",
    "EXCEPTION": "Currently in exception and needs diagnosis.",
    "CANCELLED": "Cancelled.",
    "SHIPPED": "Shipped.",
}


def summarize_order(result, order_no):
    data = result.get("data") or {}
    status = data.get("status")
    dispatches = data.get("orderDispatchList") or []
    return {
        "orderNo": data.get("orderNo") or order_no,
        "exists": result.get("code") == 0 and bool(data),
        "status": status,
        "statusName": data.get("statusName"),
        "meaning": STATUS_MEANINGS.get(status, "Status returned by OMS; use a focused skill for deeper diagnosis."),
        "channelSalesOrderNo": data.get("channelSalesOrderNo"),
        "dispatchCount": len(dispatches) if isinstance(dispatches, list) else 0,
        "nextSkill": (
            "hold"
            if status == "ON_HOLD"
            else "exception"
            if status == "EXCEPTION"
            else "allocation"
            if status in ("ALLOCATED", "WAREHOUSE_PROCESSING", "DISPATCHED")
            else None
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--order", required=True, help="Sales order number")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    result = oms_client.get(f"/api/linker-oms/opc/app-api/sale-order/{args.order}")
    result["_env"] = oms_client.get_env_label()
    result["businessSummary"] = summarize_order(result, args.order)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
