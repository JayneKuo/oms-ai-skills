"""
Create a sales order.

Usage:
  python create_order.py --channel-order-no CSO-12345 --skus '[{"sku":"BATESTSKU-1","qty":10}]' --ship-to '{"name":"John","address1":"123 Main St","city":"Los Angeles","state":"CA","zipCode":"90001","country":"US"}'
  python create_order.py --channel-order-no CSO-12345 --sku BATESTSKU-1 --qty 1 --ship-name John --address1 "123 Main St" --city Los Angeles --state CA --zip-code 90001
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
        return json.loads(args.skus)
    if args.sku and args.qty is not None:
        return [{"sku": args.sku, "qty": args.qty}]
    parser.error("Provide either --skus JSON or --sku plus --qty.")


def parse_ship_to(args, parser):
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
            "email": args.email
        }
    parser.error("Provide either --ship-to JSON or --ship-name, --address1, --city, --state, and --zip-code.")


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--channel-order-no", required=True, help="Unique channel order number")
    parser.add_argument("--skus", default=None, help='JSON item array, for example [{"sku":"SKU-A","qty":2}]')
    parser.add_argument("--sku", default=None, help="Single SKU. PowerShell-friendly alternative to --skus.")
    parser.add_argument("--qty", type=int, default=None, help="Quantity for --sku.")
    parser.add_argument("--ship-to", default=None, help="Ship-to address JSON")
    parser.add_argument("--ship-name", default=None)
    parser.add_argument("--address1", default=None)
    parser.add_argument("--address2", default="")
    parser.add_argument("--city", default=None)
    parser.add_argument("--state", default=None)
    parser.add_argument("--country", default="US")
    parser.add_argument("--zip-code", default=None)
    parser.add_argument("--phone", default="1")
    parser.add_argument("--email", default="ai-test@example.com")
    parser.add_argument("--bill-to", default=None, help="Bill-to address JSON; defaults to ship-to")
    parser.add_argument("--reference-no", default=None, help="External reference number")
    parser.add_argument("--remark", default=None, help="Remark")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    merchant_no = oms_client._env("OMS_MERCHANT_NO")
    raw_items = parse_items(args, parser)
    ship_to = parse_ship_to(args, parser)
    bill_to = json.loads(args.bill_to) if args.bill_to else ship_to

    item_lines = []
    for item in raw_items:
        item_lines.append({
            "sku": item["sku"],
            "productName": item.get("productName", item["sku"]),
            "qty": item["qty"],
            "uom": item.get("uom", "EA"),
            "unitPrice": item.get("unitPrice", 0),
            "price": item.get("price", 0),
            "discount": item.get("discount", 0),
            "discountType": item.get("discountType", "0"),
            "totalAmount": item.get("totalAmount", 0)
        })

    body = {
        "merchantNo": merchant_no,
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
        "source": "CREATED"
    }
    if args.remark:
        body["remark"] = args.remark

    result = oms_client.post("/api/linker-oms/opc/app-api/sale-order", body)
    result["_env"] = oms_client.get_env_label()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
