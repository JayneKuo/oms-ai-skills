"""
Query sales orders by list filters, status, or keyword.

Usage:
  python query_orders.py --status EXCEPTION --size 20
  python query_orders.py --keyword SO00361770
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import oms_client
from get_order_detail import STATUS_MEANINGS


def looks_like_order_no(value):
    return bool(value) and value.upper().startswith("SO")


def summarize_list(result):
    data = result.get("data") or {}
    rows = data.get("list") or []
    summaries = []
    for row in rows[:20]:
        if not isinstance(row, dict):
            continue
        status = row.get("status")
        summaries.append(
            {
                "orderNo": row.get("orderNo"),
                "status": status,
                "statusName": row.get("statusName"),
                "meaning": STATUS_MEANINGS.get(status, "Status returned by OMS."),
                "channelSalesOrderNo": row.get("channelSalesOrderNo"),
            }
        )
    return {
        "total": data.get("total"),
        "source": data.get("source") or "page_query",
        "returned": len(rows) if isinstance(rows, list) else 0,
        "orders": summaries,
    }


def with_exact_order_fallback(result, keyword):
    data = result.get("data") or {}
    if not looks_like_order_no(keyword):
        return result
    if data.get("total") not in (0, None):
        return result

    detail = oms_client.get(f"/api/linker-oms/opc/app-api/sale-order/{keyword}")
    if detail.get("code") == 0 and detail.get("data"):
        result["data"] = {
            "list": [detail["data"]],
            "total": 1,
            "source": "detail_fallback",
        }
        result["_warning"] = (
            "The page query returned no rows for this order number, so the script used "
            "the exact order-detail endpoint as a fallback."
        )
    return result


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--keyword", default=None)
    parser.add_argument("--status", action="append", dest="statuses")
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--size", type=int, default=20)
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    params = {
        "pageNo": args.page,
        "pageSize": args.size,
        "merchantNo": oms_client._env("OMS_MERCHANT_NO"),
    }
    if args.keyword:
        params["keyword"] = args.keyword
    if args.statuses:
        params["statuses"] = args.statuses

    result = oms_client.get("/api/linker-oms/opc/app-api/sale-order/page", params)
    if args.keyword:
        result = with_exact_order_fallback(result, args.keyword)
    result["_env"] = oms_client.get_env_label()
    result["businessSummary"] = summarize_list(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
