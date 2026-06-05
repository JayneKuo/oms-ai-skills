"""
Batch order operations: reopen or release hold.

Usage:
  python batch_orders.py --action reopen --orders SO001 SO002 SO003
  python batch_orders.py --action release_hold --orders SO001 SO002
"""
import argparse
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(__file__))
import oms_client


def reopen(order_no):
    return oms_client.post(f"/api/linker-oms/opc/app-api/sale-order/reopen/{order_no}")


def release_hold(order_no):
    return oms_client.post(
        f"/api/linker-oms/opc/app-api/order-hold/release?orderNo={urllib.parse.quote(order_no)}"
    )


def is_success(action, result):
    if result.get("code") != 0:
        return False
    if action == "release_hold":
        return result.get("data") is True
    return True


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--action", required=True, choices=["reopen", "release_hold"])
    parser.add_argument("--orders", nargs="+", required=True, help="One or more order numbers")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    results = []
    for order_no in args.orders:
        try:
            result = reopen(order_no) if args.action == "reopen" else release_hold(order_no)
            ok = is_success(args.action, result)
            item = {"orderNo": order_no, "ok": ok, "result": result}
            if args.action == "release_hold":
                item["businessResult"] = "released" if result.get("data") is True else "not_released"
            results.append(item)
            print(f"[{order_no}] {'OK' if ok else 'FAILED'}: {result.get('msg', '')}", file=sys.stderr)
        except Exception as exc:
            results.append({"orderNo": order_no, "ok": False, "error": str(exc)})
            print(f"[{order_no}] ERROR: {exc}", file=sys.stderr)

    success = sum(1 for item in results if item["ok"])
    print(json.dumps({
        "action": args.action,
        "total": len(results),
        "success": success,
        "failed": len(results) - success,
        "results": results,
        "_env": oms_client.get_env_label()
    }, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
