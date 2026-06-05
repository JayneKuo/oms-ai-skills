"""
Reopen a sales order that is currently in EXCEPTION.

Usage:
  python reopen_order.py --order SO00361770
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import oms_client


def summarize_reopen(order_no, result):
    if result.get("code") == 0 and result.get("data") is not False:
        state = "accepted"
        message = "OMS accepted the reopen request. Re-check order detail before saying the order is fully recovered."
    else:
        state = "rejected"
        message = result.get("msg") or "OMS rejected the reopen request."
    return {"orderNo": order_no, "state": state, "message": message}


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--order", required=True, help="Sales order number")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    result = oms_client.post(f"/api/linker-oms/opc/app-api/sale-order/reopen/{args.order}")
    result["_env"] = oms_client.get_env_label()
    result["businessSummary"] = summarize_reopen(args.order, result)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
