"""
Create a single replenishment purchase order.

Usage:
  python create_purchase_order.py --warehouse "Valley View" --sku BATESTSKU-1 --quantity 1 --confirm-create
  python create_purchase_order.py --warehouse "Valley View" --skus '[{"sku":"BATESTSKU-1","quantity":1}]' --confirm-create
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import oms_client


def parse_items(args, parser):
    if args.skus:
        items = json.loads(args.skus)
    elif args.sku and args.quantity is not None:
        items = [{"sku": args.sku, "quantity": args.quantity}]
    else:
        parser.error("Provide either --skus JSON or --sku plus --quantity.")
    for item in items:
        if not item.get("sku"):
            parser.error("Every item requires sku.")
        if item.get("quantity") is None or float(item.get("quantity")) <= 0:
            parser.error(f"SKU {item.get('sku')} requires a positive quantity.")
    return items


def summarize_po(result, warehouse, items):
    data = result.get("data") or {}
    po_no = data.get("orderNo") or data.get("purchaseOrderNo") or data.get("poNo")
    status = data.get("status") or data.get("statusName")
    return {
        "state": "created" if result.get("code") == 0 and data else "rejected",
        "purchaseOrderNo": po_no,
        "warehouse": warehouse,
        "items": items,
        "status": status,
        "message": (
            "Purchase order was created and submitted to the warehouse flow."
            if result.get("code") == 0 and data
            else result.get("msg") or "OMS rejected the purchase order creation request."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--warehouse", required=True, help="Target warehouse name or number")
    parser.add_argument("--skus", default=None, help='JSON array, e.g. [{"sku":"A","quantity":10}]')
    parser.add_argument("--sku", default=None, help="Single SKU. PowerShell-friendly alternative to --skus.")
    parser.add_argument("--quantity", type=int, default=None, help="Quantity for --sku.")
    parser.add_argument("--channel-no", default="C00000568")
    parser.add_argument("--channel-name", default="Walmart-test11")
    parser.add_argument("--data-channel", default="Walmart")
    parser.add_argument("--accounting-code", default="889")
    parser.add_argument("--confirm-create", action="store_true", help="Required to submit a real purchase-order creation request to OMS.")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    items = parse_items(args, parser)
    suffix = str(int(time.time()))[-8:]
    body = {
        "merchantNo": oms_client._env("OMS_MERCHANT_NO"),
        "orderNo": "P" + suffix,
        "referenceNo": "R" + suffix,
        "source": "CREATED",
        "orderEventType": "CREATE_ORDER",
        "receiptType": "REGULAR_RECEIPT",
        "accountingCode": args.accounting_code,
        "channelNo": args.channel_no,
        "channelName": args.channel_name,
        "dataChannel": args.data_channel,
        "warehouseName": args.warehouse,
        "itemList": [
            {"poLineNo": str(index + 1), "sku": item["sku"], "qty": item["quantity"], "uom": item.get("uom", "EA")}
            for index, item in enumerate(items)
        ],
    }

    if not args.confirm_create:
        print(json.dumps({
            "code": "CONFIRMATION_REQUIRED",
            "_env": oms_client.get_env_label(),
            "_request": {
                "submittedToOms": False,
                "requiredConfirmationFlag": "--confirm-create",
                "operation": "create_purchase_order",
                "warehouse": args.warehouse,
                "items": items,
            },
            "businessSummary": {
                "state": "not_submitted",
                "message": "This is a real OMS purchase-order action. Re-run with --confirm-create only after user second confirmation.",
            },
        }, indent=2, ensure_ascii=False))
        return

    result = oms_client.post("/api/linker-oms/opc/app-api/purchase-order", body)
    result["_env"] = oms_client.get_env_label()
    result["businessSummary"] = summarize_po(result, args.warehouse, items)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
