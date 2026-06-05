"""
Create a test sales order, then return the OMS response.

Usage:
  python create_order.py --channel-order-no CSO-12345 --sku BATESTSKU-1 --qty 1 \
    --ship-name "Test User" --address1 "123 Main St" --city "Los Angeles" --state CA --zip-code 90001 --confirm-create
"""
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(__file__))
import oms_client


def parse_items(args, parser):
    if args.skus:
        items = json.loads(args.skus)
    elif args.sku and args.qty is not None:
        items = [{"sku": args.sku, "qty": args.qty}]
    else:
        parser.error("Provide either --skus JSON or --sku plus --qty.")
    for item in items:
        if not item.get("sku"):
            parser.error("Every item requires sku.")
        if item.get("qty") is None or float(item.get("qty")) <= 0:
            parser.error(f"SKU {item.get('sku')} requires a positive qty.")
    return items


def parse_address(args, parser):
    if args.ship_to:
        return json.loads(args.ship_to)
    if args.ship_name and args.address1 and args.city and args.state and args.zip_code:
        return {
            "name": args.ship_name,
            "address1": args.address1,
            "address2": args.address2,
            "city": args.city,
            "state": args.state,
            "country": args.country,
            "zipCode": args.zip_code,
            "phone": args.phone,
            "email": args.email,
        }
    parser.error("Provide either --ship-to JSON or --ship-name, --address1, --city, --state, and --zip-code.")


def summarize_create(result):
    data = result.get("data") or {}
    return {
        "state": "created" if result.get("code") == 0 and data else "rejected",
        "orderNo": data.get("orderNo"),
        "status": data.get("status"),
        "channelSalesOrderNo": data.get("channelSalesOrderNo"),
        "message": (
            "Sales order was created. Re-read detail if you need latest allocation/dispatch status."
            if result.get("code") == 0 and data
            else result.get("msg") or "OMS rejected sales-order creation."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--channel-order-no", required=True, help="Unique channel sales order number")
    parser.add_argument("--skus", default=None, help='JSON array, e.g. [{"sku":"SKU-A","qty":2}]')
    parser.add_argument("--sku", default=None, help="Single SKU. PowerShell-friendly alternative to --skus.")
    parser.add_argument("--qty", type=int, default=None, help="Quantity for --sku.")
    parser.add_argument("--ship-to", default=None, help="Shipping address JSON")
    parser.add_argument("--ship-name", default=None)
    parser.add_argument("--address1", default=None)
    parser.add_argument("--address2", default="")
    parser.add_argument("--city", default=None)
    parser.add_argument("--state", default=None)
    parser.add_argument("--country", default="US")
    parser.add_argument("--zip-code", default=None)
    parser.add_argument("--phone", default="1")
    parser.add_argument("--email", default="ai-test@example.com")
    parser.add_argument("--bill-to", default=None, help="Billing address JSON; defaults to ship-to")
    parser.add_argument("--reference-no", default=None, help="External reference number")
    parser.add_argument("--remark", default=None, help="Remark")
    parser.add_argument("--confirm-create", action="store_true", help="Required to submit a real sales-order creation request to OMS.")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    raw_items = parse_items(args, parser)
    ship_to = parse_address(args, parser)
    bill_to = json.loads(args.bill_to) if args.bill_to else ship_to

    item_lines = []
    for item in raw_items:
        item_lines.append(
            {
                "sku": item["sku"],
                "productName": item.get("productName", item["sku"]),
                "qty": item["qty"],
                "uom": item.get("uom", "EA"),
                "unitPrice": item.get("unitPrice", 0),
                "price": item.get("price", 0),
                "discount": item.get("discount", 0),
                "discountType": item.get("discountType", "0"),
                "totalAmount": item.get("totalAmount", 0),
            }
        )

    body = {
        "merchantNo": oms_client._env("OMS_MERCHANT_NO"),
        "orderDate": datetime.now(timezone.utc).isoformat(),
        "requiredShippingDate": None,
        "shipToAddress": ship_to,
        "billToAddress": bill_to,
        "itemLines": item_lines,
        "channelSalesOrderNo": args.channel_order_no,
        "purchaseOrderNo": "",
        "referenceNo": args.reference_no or f"AI-REF-{int(time.time())}",
        "carrier": {},
        "taxRate": 0,
        "subtotalAmount": 0,
        "discount": 0,
        "tax": 0,
        "shippingAmount": 0,
        "totalAmount": 0,
        "status": "IMPORTED",
        "source": "CREATED",
    }
    if args.remark:
        body["remark"] = args.remark

    if not args.confirm_create:
        print(json.dumps({
            "code": "CONFIRMATION_REQUIRED",
            "_env": oms_client.get_env_label(),
            "_request": {
                "submittedToOms": False,
                "requiredConfirmationFlag": "--confirm-create",
                "operation": "create_test_sales_order",
                "channelSalesOrderNo": args.channel_order_no,
                "items": raw_items,
            },
            "businessSummary": {
                "state": "not_submitted",
                "message": "This is a real OMS action. Re-run with --confirm-create only after user second confirmation.",
            },
        }, indent=2, ensure_ascii=False))
        return

    result = oms_client.post("/api/linker-oms/opc/app-api/sale-order", body)
    result["_env"] = oms_client.get_env_label()
    result["businessSummary"] = summarize_create(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
