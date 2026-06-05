"""
Submit a manual/auto dispatch allocation request.

Supported dispatch types:
  HAND_WHOLE_DISPATCH       Assign the whole order to a specified warehouse.
  HAND_SKU_DISPATCH         Assign specific SKU quantities to specified warehouse(s).
  HAND_WHOLE_AUTO_DISPATCH  Let OMS auto-dispatch the whole order.
  HAND_SKU_AUTO_DISPATCH    Let OMS auto-dispatch specific SKU quantities.

Usage:
  python manual_allocate.py --order SO001 --dispatch-type HAND_WHOLE_AUTO_DISPATCH
  python manual_allocate.py --order SO001 --dispatch-type HAND_WHOLE_DISPATCH --warehouse "Valley View" --accounting-code 889
  python manual_allocate.py --order SO001 --dispatch-type HAND_SKU_AUTO_DISPATCH --sku SKU-A --qty 2
  python manual_allocate.py --order SO001 --dispatch-type HAND_SKU_DISPATCH --warehouse "Valley View" --sku SKU-A --qty 2
  python manual_allocate.py --order SO001 --warehouse-orders '[{"warehouseName":"Valley View","accountingCode":"889","items":[{"sku":"SKU-A","qty":2}]}]'
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import oms_client

DISPATCH_TYPES = [
    "NORMAL_DISPATCH",
    "HAND_WHOLE_DISPATCH",
    "HAND_SKU_DISPATCH",
    "REOPEN_DISPATCH",
    "MERGE_ORDER_DISPATCH",
    "HAND_WHOLE_AUTO_DISPATCH",
    "HAND_SKU_AUTO_DISPATCH",
]


def parse_item_list(args):
    if args.skus:
        return json.loads(args.skus)
    if args.sku and args.qty is not None:
        return [{"sku": args.sku, "qty": args.qty, "uom": args.uom}]
    return []


def infer_dispatch_type(args):
    if args.dispatch_type:
        return args.dispatch_type
    if args.mode == "ORDER":
        return "HAND_WHOLE_DISPATCH" if args.warehouse else "HAND_WHOLE_AUTO_DISPATCH"
    return "HAND_SKU_DISPATCH" if args.warehouse else "HAND_SKU_AUTO_DISPATCH"


def build_warehouse_entry(args, items):
    warehouse_name = args.warehouse_name or args.warehouse
    if not warehouse_name:
        return None
    entry = {"warehouseName": warehouse_name}
    if args.accounting_code:
        entry["accountingCode"] = args.accounting_code
    if items:
        entry["itemDTOList"] = items
    return entry


def normalize_warehouse_orders(raw_orders):
    warehouse_orders = []
    for order in raw_orders:
        warehouse_name = order.get("warehouseName") or order.get("warehouse") or order.get("warehouseCode")
        entry = {"warehouseName": warehouse_name}
        if order.get("accountingCode"):
            entry["accountingCode"] = order["accountingCode"]
        items = order.get("itemDTOList") or order.get("items") or order.get("skus") or []
        if items:
            entry["itemDTOList"] = items
        warehouse_orders.append(entry)
    return warehouse_orders


def build_body(args, parser):
    dispatch_type = infer_dispatch_type(args)
    items = parse_item_list(args)
    body = {
        "orderNo": args.order,
        "dispatchType": dispatch_type,
    }
    if args.remark:
        body["remark"] = args.remark

    if args.warehouse_orders:
        body["warehouseDTOList"] = normalize_warehouse_orders(json.loads(args.warehouse_orders))
        return body

    if dispatch_type in ("HAND_SKU_AUTO_DISPATCH", "REOPEN_DISPATCH") and items:
        body["itemDTOList"] = items
        return body

    if dispatch_type == "HAND_SKU_DISPATCH":
        if not args.warehouse:
            parser.error("--warehouse is required for HAND_SKU_DISPATCH unless --warehouse-orders is provided")
        if not items:
            parser.error("--skus JSON or --sku/--qty is required for HAND_SKU_DISPATCH")
        body["warehouseDTOList"] = [build_warehouse_entry(args, items)]
        return body

    if dispatch_type == "HAND_WHOLE_DISPATCH":
        if not args.warehouse:
            parser.error("--warehouse is required for HAND_WHOLE_DISPATCH")
        body["warehouseDTOList"] = [build_warehouse_entry(args, items)]
        return body

    if dispatch_type == "HAND_WHOLE_AUTO_DISPATCH":
        if items:
            body["itemDTOList"] = items
        return body

    if args.warehouse:
        body["warehouseDTOList"] = [build_warehouse_entry(args, items)]
    elif items:
        body["itemDTOList"] = items
    return body


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--order", required=True, help="Order number")
    parser.add_argument("--dispatch-type", choices=DISPATCH_TYPES, default=None)
    parser.add_argument("--mode", default="SKU", choices=["SKU", "ORDER"], help="Legacy alias used to infer dispatch type")
    parser.add_argument("--warehouse", default=None, help="Warehouse name for specified-warehouse dispatch")
    parser.add_argument("--warehouse-name", default=None, help="Warehouse display name; defaults to --warehouse")
    parser.add_argument("--accounting-code", default=None, help="Warehouse accounting code, if required by OMS")
    parser.add_argument("--warehouse-orders", default=None, help="JSON array for multi-warehouse SKU dispatch")
    parser.add_argument("--skus", default=None, help='JSON array, for example [{"sku":"A","qty":2,"uom":"EA"}]')
    parser.add_argument("--sku", default=None, help="Single SKU for PowerShell-friendly input")
    parser.add_argument("--qty", type=int, default=None, help="Single SKU quantity")
    parser.add_argument("--uom", default="EA")
    parser.add_argument("--remark", default=None)
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    body = build_body(args, parser)
    result = oms_client.post("/api/linker-oms/opc/app-api/dispatch/hand", body)
    result["_env"] = oms_client.get_env_label()
    result["_request"] = {
        "orderNo": body.get("orderNo"),
        "dispatchType": body.get("dispatchType"),
        "hasWarehouseDTOList": bool(body.get("warehouseDTOList")),
        "hasItemDTOList": bool(body.get("itemDTOList")),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
