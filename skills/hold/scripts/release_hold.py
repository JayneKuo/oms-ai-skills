"""
Release an ON_HOLD sales order after explicit confirmation.

Usage:
  python release_hold.py --order SO00361770 --confirm-release
"""
import argparse
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(__file__))
import oms_client


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--order", required=True, help="Sales order number")
    parser.add_argument("--confirm-release", action="store_true", help="Required to submit a real hold release request to OMS.")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    if not args.confirm_release:
        print(json.dumps({
            "code": "CONFIRMATION_REQUIRED",
            "_env": oms_client.get_env_label(),
            "_request": {
                "submittedToOms": False,
                "requiredConfirmationFlag": "--confirm-release",
                "operation": "release_hold",
                "orderNo": args.order,
            },
            "businessSummary": {
                "orderNo": args.order,
                "state": "not_submitted",
                "message": "This is a real OMS hold-release action. Re-run with --confirm-release only after user second confirmation.",
            },
        }, indent=2, ensure_ascii=False))
        return

    result = oms_client.post(
        f"/api/linker-oms/opc/app-api/order-hold/release?orderNo={urllib.parse.quote(args.order)}"
    )
    result["_env"] = oms_client.get_env_label()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()