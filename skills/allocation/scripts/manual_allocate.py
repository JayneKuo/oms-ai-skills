"""
Submit a manual/auto dispatch allocation request.

Supported dispatch types:
  HAND_WHOLE_DISPATCH       Assign the whole order to a specified warehouse.
  HAND_SKU_DISPATCH         Assign specific SKU quantities to specified warehouse(s).
  HAND_WHOLE_AUTO_DISPATCH  Let OMS auto-dispatch the whole order.
  HAND_SKU_AUTO_DISPATCH    Let OMS auto-dispatch specific SKU quantities.

Usage:
  python manual_allocate.py --order SO001 --dispatch-type HAND_WHOLE_AUTO_DISPATCH --confirm-allocation
  python manual_allocate.py --order SO001 --dispatch-type HAND_WHOLE_DISPATCH --warehouse "Valley View" --accounting-code 889 --confirm-allocation
  python manual_allocate.py --order SO001 --dispatch-type HAND_SKU_AUTO_DISPATCH --sku SKU-A --qty 2 --confirm-allocation
  python manual_allocate.py --order SO001 --dispatch-type HAND_SKU_DISPATCH --warehouse "Valley View" --sku SKU-A --qty 2 --confirm-allocation
  python manual_allocate.py --order SO001 --warehouse-orders '[{"warehouseName":"Valley View","accountingCode":"889","items":[{"sku":"SKU-A","qty":2}]}]' --confirm-allocation
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import oms_client
import explain_warehouse_assignment as warehouse_explainer

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


def build_allocation_context(order_no, include_eligibility=False):
    order_response = warehouse_explainer.safe_get(
        f"/api/linker-oms/opc/app-api/sale-order/{order_no}"
    )
    order_data = warehouse_explainer.unwrap_data(order_response) or {}
    dispatch_explain_response = warehouse_explainer.fetch_dispatch_explain(order_no)
    allocation_response = warehouse_explainer.safe_get(
        f"/api/linker-oms/opc/app-api/dispatch/hand/item/{order_no}"
    )
    routing_response = warehouse_explainer.safe_get(
        "/api/linker-oms/opc/app-api/routing/v2/rules",
        {"merchantNo": oms_client._env("OMS_MERCHANT_NO")},
    )

    order_summary = warehouse_explainer.extract_order_summary(order_data)
    order_summary["orderNo"] = order_summary.get("orderNo") or order_no
    assignment = warehouse_explainer.extract_assignment(order_data)
    dispatch_explain_summary = warehouse_explainer.summarize_dispatch_explain(dispatch_explain_response)
    allocation_summary = warehouse_explainer.summarize_allocation_items(allocation_response)
    routing_summary = warehouse_explainer.summarize_routing_rules(routing_response)
    dispatch_method = warehouse_explainer.classify_dispatch_method(assignment, dispatch_explain_summary)
    reason = warehouse_explainer.build_reason(
        order_summary,
        assignment,
        allocation_summary,
        routing_summary,
        dispatch_explain_summary,
    )
    result = {
        "orderSummary": order_summary,
        "assignmentResult": assignment,
        "dispatchMethod": dispatch_method,
        "reason": reason,
        "dispatchExplainSummary": dispatch_explain_summary,
        "allocationSummary": allocation_summary,
        "routingRuleSummary": routing_summary,
        "userFacingSummary": warehouse_explainer.build_user_summary(
            order_summary, assignment, dispatch_method, reason
        ),
    }
    if include_eligibility:
        result["manualAllocationEligibility"] = warehouse_explainer.safe_get(
            f"/api/linker-oms/opc/app-api/dispatch/hand/check/{order_no}"
        )
    return result


def build_post_allocation_check(order_no):
    return build_allocation_context(order_no, include_eligibility=False)


def sku_remaining_text(allocation_summary):
    lines = allocation_summary.get("lines") or []
    parts = []
    for line in lines[:10]:
        sku = line.get("sku") or "unknown SKU"
        ordered = line.get("orderedQty")
        remaining = line.get("remainingQty")
        uom = line.get("uom") or ""
        parts.append(f"{sku}: ordered={ordered}, remaining={remaining} {uom}".strip())
    return "; ".join(parts) if parts else "No allocatable item lines were returned."


def should_block_before_submit(precheck):
    order_summary = precheck.get("orderSummary") or {}
    allocation_summary = precheck.get("allocationSummary") or {}
    eligibility = precheck.get("manualAllocationEligibility") or {}

    if order_summary.get("lookupStatus") == "ORDER_NOT_FOUND_OR_INACCESSIBLE":
        return True, "order_not_found"
    if allocation_summary.get("fetchStatus") == "ok" and allocation_summary.get("totalRemainingQty", 0) <= 0:
        return True, "no_remaining_items"
    if isinstance(eligibility, dict) and eligibility.get("code") not in (0, None):
        return True, "manual_allocation_not_supported"
    return False, None


def build_precheck_block_summary(precheck, reason_code):
    order_summary = precheck.get("orderSummary") or {}
    assignment = precheck.get("assignmentResult") or {}
    allocation_summary = precheck.get("allocationSummary") or {}
    eligibility = precheck.get("manualAllocationEligibility") or {}
    warehouse = assignment.get("warehouseName") or "not assigned"
    dispatch_no = assignment.get("dispatchNo") or "no dispatch"
    dispatch_status = assignment.get("dispatchStatus") or "unknown"
    total_remaining = allocation_summary.get("totalRemainingQty")
    sku_text = sku_remaining_text(allocation_summary)

    if reason_code == "order_not_found":
        message = "The order was not found or is not accessible, so no allocation write was submitted."
    elif reason_code == "no_remaining_items":
        message = (
            "The order is already fully allocated. There are no remaining allocatable items, "
            "so no allocation write was submitted."
        )
    else:
        message = (
            "OMS reports this order does not support manual allocation in its current status, "
            "so no allocation write was submitted."
        )

    return (
        f"{message}\n"
        f"Order: {order_summary.get('orderNo')}, status: {order_summary.get('status')}.\n"
        f"Current allocation: warehouse={warehouse}, dispatch={dispatch_no}, dispatchStatus={dispatch_status}.\n"
        f"Items: {sku_text}; totalRemaining={total_remaining}.\n"
        f"OMS eligibility: code={eligibility.get('code')}, msg={eligibility.get('msg')}.\n"
        "User-facing answer should explain the existing allocation details and say there are no allocatable products, "
        "instead of saying allocation execution is required."
    )


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
    parser.add_argument(
        "--force-submit",
        action="store_true",
        help="Submit even if precheck says the order has no remaining quantity or is not eligible.",
    )
    parser.add_argument("--confirm-allocation", action="store_true", help="Required to submit a real allocation request to OMS.")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    body = build_body(args, parser)
    precheck = build_allocation_context(args.order, include_eligibility=True)
    blocked, block_reason = should_block_before_submit(precheck)
    if not args.confirm_allocation:
        result = {
            "code": "CONFIRMATION_REQUIRED",
            "data": None,
            "msg": "confirmation_required",
            "_env": oms_client.get_env_label(),
            "_request": {
                "orderNo": body.get("orderNo"),
                "dispatchType": body.get("dispatchType"),
                "hasWarehouseDTOList": bool(body.get("warehouseDTOList")),
                "hasItemDTOList": bool(body.get("itemDTOList")),
                "submittedToOms": False,
                "requiredConfirmationFlag": "--confirm-allocation",
            },
            "preAllocationCheck": precheck,
            "businessSummary": {
                "state": "not_submitted",
                "reason": "confirmation_required",
                "message": "This is a real OMS allocation action. Re-run with --confirm-allocation only after user second confirmation.",
            },
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    if blocked and not args.force_submit:
        result = {
            "code": "PRECHECK_BLOCKED",
            "data": None,
            "msg": block_reason,
            "_env": oms_client.get_env_label(),
            "_request": {
                "orderNo": body.get("orderNo"),
                "dispatchType": body.get("dispatchType"),
                "hasWarehouseDTOList": bool(body.get("warehouseDTOList")),
                "hasItemDTOList": bool(body.get("itemDTOList")),
                "submittedToOms": False,
            },
            "preAllocationCheck": precheck,
            "businessSummary": {
                "state": "not_submitted",
                "reason": block_reason,
                "message": build_precheck_block_summary(precheck, block_reason),
            },
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    result = oms_client.post("/api/linker-oms/opc/app-api/dispatch/hand", body)
    result["_env"] = oms_client.get_env_label()
    result["_request"] = {
        "orderNo": body.get("orderNo"),
        "dispatchType": body.get("dispatchType"),
        "hasWarehouseDTOList": bool(body.get("warehouseDTOList")),
        "hasItemDTOList": bool(body.get("itemDTOList")),
        "submittedToOms": True,
    }
    result["preAllocationCheck"] = precheck
    if result.get("code") == 0:
        result["postAllocationCheck"] = build_post_allocation_check(args.order)
        result["businessSummary"] = {
            "state": "submitted_and_rechecked",
            "message": (
                "The allocation request was accepted by OMS and the order was re-read. "
                "Use postAllocationCheck.assignmentResult and postAllocationCheck.allocationSummary "
                "in the user-facing response."
            ),
        }
    else:
        result["businessSummary"] = {
            "state": "rejected",
            "message": "OMS rejected the allocation request; do not claim a new allocation result.",
        }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
