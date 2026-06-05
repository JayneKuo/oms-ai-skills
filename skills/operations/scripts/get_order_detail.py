"""
Fetch a single sales order detail record before or after an operation.

Usage:
  python get_order_detail.py --order SO00361770
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import oms_client


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--order", required=True, help="Sales order number")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    result = oms_client.get(f"/api/linker-oms/opc/app-api/sale-order/{args.order}")
    result["_env"] = oms_client.get_env_label()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
