"""
Create split replenishment purchase orders.

Usage:
  python create_purchase_order_split.py --orders '[{"warehouse":"Main Warehouse","skus":[{"sku":"BATESTSKU-1","quantity":1}]}]'
  python create_purchase_order_split.py --warehouse "Valley View" --sku BATESTSKU-1 --quantity 1
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import oms_client


def parse_warehouse_orders(args, parser):
    if args.orders:
        return json.loads(args.orders)
    if args.warehouse and args.sku and args.quantity is not None:
        return [{"warehouse": args.warehouse, "skus": [{"sku": args.sku, "quantity": args.quantity}]}]
    parser.error("Provide either --orders JSON or --warehouse, --sku and --quantity")


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--orders", default=None, help="JSON array of warehouse orders")
    parser.add_argument("--warehouse", default=None, help="Single warehouse name for PowerShell-friendly input")
    parser.add_argument("--sku", default=None, help="Single SKU for PowerShell-friendly input")
    parser.add_argument("--quantity", type=int, default=None, help="Single SKU quantity for PowerShell-friendly input")
    parser.add_argument("--channel-no", default="C00000568")
    parser.add_argument("--channel-name", default="Walmart-test11")
    parser.add_argument("--data-channel", default="Walmart")
    parser.add_argument("--accounting-code", default="889")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    warehouse_orders = parse_warehouse_orders(args, parser)
    merchant_no = oms_client._env("OMS_MERCHANT_NO")

    results = []
    for idx, order in enumerate(warehouse_orders):
        suffix = str(int(time.time()))[-8:] + str(idx)
        warehouse = order["warehouse"]
        skus = order["skus"]
        body = {
            "merchantNo": merchant_no,
            "orderNo": "P" + suffix,
            "referenceNo": "R" + suffix,
            "source": "CREATED",
            "orderEventType": "CREATE_ORDER",
            "receiptType": "REGULAR_RECEIPT",
            "accountingCode": args.accounting_code,
            "channelNo": args.channel_no,
            "channelName": args.channel_name,
            "dataChannel": args.data_channel,
            "warehouseName": warehouse,
            "itemList": [
                {"poLineNo": str(i + 1), "sku": item["sku"], "qty": item["quantity"], "uom": item.get("uom", "EA")}
                for i, item in enumerate(skus)
            ]
        }
        result = oms_client.post("/api/linker-oms/opc/app-api/purchase-order", body)
        results.append({"warehouse": warehouse, "skus": skus, "result": result})
        print(f"[{warehouse}] {'OK' if result.get('code') == 0 else 'FAILED'}: {result.get('msg', '')}", file=sys.stderr)

    print(json.dumps({"total": len(results), "results": results, "_env": oms_client.get_env_label()}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
