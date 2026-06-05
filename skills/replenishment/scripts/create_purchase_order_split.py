"""
Create split replenishment purchase orders.

Usage:
  python create_purchase_order_split.py --orders '[{"warehouse":"Main Warehouse","skus":[{"sku":"BATESTSKU-1","quantity":1}]}]' --confirm-create
  python create_purchase_order_split.py --warehouse "Valley View" --sku BATESTSKU-1 --quantity 1 --confirm-create
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


def validate_warehouse_orders(warehouse_orders, parser):
    for order in warehouse_orders:
        if not order.get("warehouse"):
            parser.error("Every split order requires warehouse.")
        skus = order.get("skus") or []
        if not skus:
            parser.error(f"Warehouse {order.get('warehouse')} requires at least one SKU.")
        for item in skus:
            if not item.get("sku"):
                parser.error(f"Warehouse {order.get('warehouse')} has an item without sku.")
            if item.get("quantity") is None or float(item.get("quantity")) <= 0:
                parser.error(f"SKU {item.get('sku')} requires a positive quantity.")


def summarize_po(result, warehouse, skus):
    data = result.get("data") or {}
    po_no = data.get("orderNo") or data.get("purchaseOrderNo") or data.get("poNo")
    return {
        "state": "created" if result.get("code") == 0 and data else "rejected",
        "purchaseOrderNo": po_no,
        "warehouse": warehouse,
        "items": skus,
        "status": data.get("status") or data.get("statusName"),
        "message": (
            "Purchase order was created for this warehouse."
            if result.get("code") == 0 and data
            else result.get("msg") or "OMS rejected this warehouse purchase order."
        ),
    }


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
    parser.add_argument("--confirm-create", action="store_true", help="Required to submit real split purchase-order creation requests to OMS.")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    warehouse_orders = parse_warehouse_orders(args, parser)
    validate_warehouse_orders(warehouse_orders, parser)
    merchant_no = oms_client._env("OMS_MERCHANT_NO")

    if not args.confirm_create:
        print(json.dumps({
            "code": "CONFIRMATION_REQUIRED",
            "_env": oms_client.get_env_label(),
            "_request": {
                "submittedToOms": False,
                "requiredConfirmationFlag": "--confirm-create",
                "operation": "create_split_purchase_orders",
                "warehouseOrders": warehouse_orders,
            },
            "businessSummary": {
                "state": "not_submitted",
                "message": "This is a real OMS split purchase-order action. Re-run with --confirm-create only after user second confirmation.",
            },
        }, indent=2, ensure_ascii=False))
        return

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
        results.append(
            {
                "warehouse": warehouse,
                "skus": skus,
                "result": result,
                "businessSummary": summarize_po(result, warehouse, skus),
            }
        )
        print(f"[{warehouse}] {'OK' if result.get('code') == 0 else 'FAILED'}: {result.get('msg', '')}", file=sys.stderr)

    print(
        json.dumps(
            {
                "total": len(results),
                "created": sum(1 for row in results if row["businessSummary"]["state"] == "created"),
                "failed": sum(1 for row in results if row["businessSummary"]["state"] != "created"),
                "results": results,
                "_env": oms_client.get_env_label(),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
