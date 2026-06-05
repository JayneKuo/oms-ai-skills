"""
Batch allocation diagnostics and controlled allocation actions.

The script prefers one concise per-order result over large raw payloads. When
OMS does not provide a batch endpoint, it runs bounded parallel single-order
calls so one slow/failing order does not block the whole batch.

Examples:
  python batch_allocation.py --action explain --orders SO001 SO002
  python batch_allocation.py --action items --orders SO001 SO002
  python batch_allocation.py --action check --orders SO001 SO002
  python batch_allocation.py --action manual_allocate --orders SO001 SO002 --dispatch-type HAND_WHOLE_AUTO_DISPATCH --confirm-allocation
"""
import argparse
import concurrent.futures
import json
import os
import sys
import time
from types import SimpleNamespace
from urllib.error import HTTPError, URLError

sys.path.insert(0, os.path.dirname(__file__))
import oms_client
import explain_warehouse_assignment as explainer
import manual_allocate as manual


def parse_orders(args):
    orders = []
    for value in args.orders or []:
        for part in str(value).replace(",", " ").split():
            if part.strip():
                orders.append(part.strip())
    if args.orders_file:
        with open(args.orders_file, "r", encoding="utf-8") as handle:
            for line in handle:
                value = line.strip()
                if value and not value.startswith("#"):
                    orders.append(value)
    return list(dict.fromkeys(orders))


def summarize_explain(order_no):
    order_response = explainer.safe_get(f"/api/linker-oms/opc/app-api/sale-order/{order_no}")
    order_data = explainer.unwrap_data(order_response) or {}
    dispatch_explain_response = explainer.fetch_dispatch_explain(order_no)
    allocation_response = explainer.safe_get(f"/api/linker-oms/opc/app-api/dispatch/hand/item/{order_no}")
    routing_response = explainer.safe_get(
        "/api/linker-oms/opc/app-api/routing/v2/rules",
        {"merchantNo": oms_client._env("OMS_MERCHANT_NO")},
    )

    order_summary = explainer.extract_order_summary(order_data)
    order_summary["orderNo"] = order_summary.get("orderNo") or order_no
    if not order_data or (isinstance(order_response, dict) and order_response.get("code") not in (0, None)):
        order_summary["lookupStatus"] = "ORDER_NOT_FOUND_OR_INACCESSIBLE"
        order_summary["lookupCode"] = order_response.get("code") if isinstance(order_response, dict) else None
        order_summary["lookupMessage"] = order_response.get("msg") if isinstance(order_response, dict) else None

    assignment = explainer.extract_assignment(order_data)
    dispatch_explain_summary = explainer.summarize_dispatch_explain(dispatch_explain_response)
    allocation_summary = explainer.summarize_allocation_items(allocation_response)
    routing_summary = explainer.summarize_routing_rules(routing_response)
    dispatch_method = explainer.classify_dispatch_method(assignment, dispatch_explain_summary)
    reason = explainer.build_reason(
        order_summary,
        assignment,
        allocation_summary,
        routing_summary,
        dispatch_explain_summary,
    )
    state = "not_found" if order_summary.get("lookupStatus") == "ORDER_NOT_FOUND_OR_INACCESSIBLE" else "ok"
    return {
        "orderNo": order_no,
        "state": state,
        "status": order_summary.get("status"),
        "warehouse": assignment.get("warehouseName"),
        "dispatchNo": assignment.get("dispatchNo"),
        "dispatchStatus": assignment.get("dispatchStatus"),
        "remaining": allocation_summary.get("totalRemainingQty"),
        "reasonConfirmed": reason.get("confirmed"),
        "reason": reason.get("message"),
        "summary": explainer.build_user_summary(order_summary, assignment, dispatch_method, reason),
    }


def summarize_items(order_no):
    response = explainer.safe_get(f"/api/linker-oms/opc/app-api/dispatch/hand/item/{order_no}")
    summary = explainer.summarize_allocation_items(response)
    return {
        "orderNo": order_no,
        "state": "ok" if summary.get("fetchStatus") == "ok" else "failed",
        "remaining": summary.get("totalRemainingQty"),
        "lines": summary.get("lines"),
        "businessCode": summary.get("businessCode"),
        "message": summary.get("message"),
    }


def summarize_check(order_no):
    response = explainer.safe_get(f"/api/linker-oms/opc/app-api/dispatch/hand/check/{order_no}")
    return {
        "orderNo": order_no,
        "state": "eligible" if isinstance(response, dict) and response.get("code") == 0 else "not_eligible",
        "code": response.get("code") if isinstance(response, dict) else None,
        "message": response.get("msg") if isinstance(response, dict) else str(response),
    }


def manual_args_for(order_no, args):
    return SimpleNamespace(
        order=order_no,
        dispatch_type=args.dispatch_type,
        mode=args.mode,
        warehouse=args.warehouse,
        warehouse_name=args.warehouse_name,
        accounting_code=args.accounting_code,
        warehouse_orders=args.warehouse_orders,
        skus=args.skus,
        sku=args.sku,
        qty=args.qty,
        uom=args.uom,
        remark=args.remark,
        force_submit=args.force_submit,
        config=args.config,
    )


class ParserProxy:
    def error(self, message):
        raise ValueError(message)


def summarize_manual_allocate(order_no, args):
    single_args = manual_args_for(order_no, args)
    body = manual.build_body(single_args, ParserProxy())
    precheck = manual.build_allocation_context(order_no, include_eligibility=True)
    blocked, block_reason = manual.should_block_before_submit(precheck)
    if blocked and not args.force_submit:
        return {
            "orderNo": order_no,
            "state": "not_submitted",
            "reason": block_reason,
            "submittedToOms": False,
            "warehouse": (precheck.get("assignmentResult") or {}).get("warehouseName"),
            "dispatchNo": (precheck.get("assignmentResult") or {}).get("dispatchNo"),
            "dispatchStatus": (precheck.get("assignmentResult") or {}).get("dispatchStatus"),
            "remaining": (precheck.get("allocationSummary") or {}).get("totalRemainingQty"),
            "message": manual.build_precheck_block_summary(precheck, block_reason),
        }

    response = oms_client.post("/api/linker-oms/opc/app-api/dispatch/hand", body)
    accepted = isinstance(response, dict) and response.get("code") == 0
    result = {
        "orderNo": order_no,
        "state": "submitted_and_rechecked" if accepted else "rejected",
        "submittedToOms": True,
        "code": response.get("code") if isinstance(response, dict) else None,
        "message": response.get("msg") if isinstance(response, dict) else str(response),
    }
    if accepted:
        post = manual.build_post_allocation_check(order_no)
        assignment = post.get("assignmentResult") or {}
        allocation = post.get("allocationSummary") or {}
        result.update(
            {
                "warehouse": assignment.get("warehouseName"),
                "dispatchNo": assignment.get("dispatchNo"),
                "dispatchStatus": assignment.get("dispatchStatus"),
                "remaining": allocation.get("totalRemainingQty"),
                "postSummary": post.get("userFacingSummary"),
            }
        )
    return result


def run_one(order_no, args):
    started = time.perf_counter()
    try:
        if args.action == "explain":
            result = summarize_explain(order_no)
        elif args.action == "items":
            result = summarize_items(order_no)
        elif args.action == "check":
            result = summarize_check(order_no)
        elif args.action == "manual_allocate":
            result = summarize_manual_allocate(order_no, args)
        else:
            raise ValueError(f"Unsupported action: {args.action}")
        result["durationMs"] = int((time.perf_counter() - started) * 1000)
        return result
    except (HTTPError, URLError, ValueError, RuntimeError) as exc:
        return {
            "orderNo": order_no,
            "state": "error",
            "message": str(exc),
            "durationMs": int((time.perf_counter() - started) * 1000),
        }


def build_batch_summary(results):
    counts = {}
    for row in results:
        state = row.get("state") or "unknown"
        counts[state] = counts.get(state, 0) + 1
    return {
        "total": len(results),
        "counts": counts,
        "slowestMs": max([row.get("durationMs", 0) for row in results] or [0]),
    }


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--action", required=True, choices=["explain", "items", "check", "manual_allocate"])
    parser.add_argument("--orders", nargs="*", default=[])
    parser.add_argument("--orders-file", default=None)
    parser.add_argument("--max-workers", type=int, default=4)
    parser.add_argument("--dispatch-type", default=None)
    parser.add_argument("--mode", default="SKU", choices=["SKU", "ORDER"])
    parser.add_argument("--warehouse", default=None)
    parser.add_argument("--warehouse-name", default=None)
    parser.add_argument("--accounting-code", default=None)
    parser.add_argument("--warehouse-orders", default=None)
    parser.add_argument("--skus", default=None)
    parser.add_argument("--sku", default=None)
    parser.add_argument("--qty", type=int, default=None)
    parser.add_argument("--uom", default="EA")
    parser.add_argument("--remark", default=None)
    parser.add_argument("--force-submit", action="store_true")
    parser.add_argument("--confirm-allocation", action="store_true", help="Required to submit real batch allocation requests to OMS.")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    orders = parse_orders(args)
    if not orders:
        parser.error("--orders or --orders-file is required")
    if args.action == "manual_allocate" and not args.confirm_allocation:
        print(json.dumps({
            "code": "CONFIRMATION_REQUIRED",
            "_env": oms_client.get_env_label(),
            "action": args.action,
            "_request": {
                "submittedToOms": False,
                "requiredConfirmationFlag": "--confirm-allocation",
                "operation": "batch_allocation",
                "orders": orders,
                "dispatchType": args.dispatch_type,
                "warehouse": args.warehouse,
                "sku": args.sku,
                "qty": args.qty,
            },
            "businessSummary": {
                "state": "not_submitted",
                "message": "This is a real OMS batch allocation action. Re-run with --confirm-allocation only after user second confirmation.",
            },
        }, indent=2, ensure_ascii=False))
        return

    worker_count = max(1, min(args.max_workers, 8, len(orders)))
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(run_one, order_no, args) for order_no in orders]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    results.sort(key=lambda row: orders.index(row["orderNo"]) if row.get("orderNo") in orders else len(orders))

    output = {
        "_env": oms_client.get_env_label(),
        "action": args.action,
        "submittedToOms": args.action == "manual_allocate" and any(row.get("submittedToOms") for row in results),
        "durationMs": int((time.perf_counter() - started) * 1000),
        "batchSummary": build_batch_summary(results),
        "results": results,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
