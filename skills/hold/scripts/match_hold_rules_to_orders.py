"""
Map ON_HOLD orders to likely hold rules.

OMS exposes active-count by rule but not a hold-record list endpoint in the
available OpenAPI. This script therefore returns candidate matches based on
rule criteria and order fields, and clearly marks them as inferred candidates
unless direct rule execution/log evidence exists.

Examples:
  python match_hold_rules_to_orders.py --size 20
  python match_hold_rules_to_orders.py --orders SO01376525 SO01376524
"""
import argparse
import concurrent.futures
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import oms_client
import hold_rules


def as_list(value):
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def unwrap_data(response):
    return response.get("data") if isinstance(response, dict) else None


def get_order(order_no):
    response = hold_rules.safe_get(f"/api/linker-oms/opc/app-api/sale-order/{order_no}")
    return unwrap_data(response) or {}


def query_on_hold_orders(page, size):
    response = hold_rules.safe_get(
        "/api/linker-oms/opc/app-api/sale-order/page",
        {
            "pageNo": page,
            "pageSize": size,
            "merchantNo": oms_client._env("OMS_MERCHANT_NO"),
            "statuses": ["ON_HOLD"],
        },
    )
    data = unwrap_data(response) or {}
    return [row for row in as_list(data.get("list")) if isinstance(row, dict)]


def get_rules(size):
    args = argparse.Namespace(
        page=1,
        size=size,
        sort_field="priority",
        sort_type="ASC",
        rule_name=None,
        status=None,
    )
    listed = hold_rules.list_rules(args)
    return listed.get("rules") or []


def order_skus(order):
    skus = set()
    if order.get("product"):
        for part in str(order.get("product")).replace(",", " ").split():
            if part.strip():
                skus.add(part.strip().upper())
    for line in as_list(order.get("itemLines")):
        if isinstance(line, dict):
            sku = line.get("sku") or line.get("originalSku")
            if sku:
                skus.add(str(sku).upper())
    return skus


def match_rule(order, rule):
    reasons = []
    blockers = []
    sku_list = {str(sku).upper() for sku in as_list(rule.get("skuList"))}
    if sku_list:
        common = sorted(order_skus(order) & sku_list)
        if common:
            reasons.append(f"SKU matched: {', '.join(common)}")
        else:
            blockers.append("SKU rule did not match order SKUs")

    order_sources = {str(v).upper() for v in as_list(rule.get("orderSource"))}
    if order_sources:
        source_values = {
            str(order.get("source") or "").upper(),
            str(order.get("dataChannel") or "").upper(),
            str(order.get("originalDataChannel") or "").upper(),
        }
        if order_sources & source_values:
            reasons.append(f"orderSource matched: {', '.join(sorted(order_sources & source_values))}")
        else:
            blockers.append("orderSource rule did not match order source/channel")

    channels = {str(v).upper() for v in as_list(rule.get("channels"))}
    if channels:
        channel_values = {
            str(order.get("channelName") or "").upper(),
            str(order.get("channelNo") or "").upper(),
            str(order.get("dataChannel") or "").upper(),
        }
        if channels & channel_values:
            reasons.append(f"channel matched: {', '.join(sorted(channels & channel_values))}")
        else:
            blockers.append("channel rule did not match order channel")

    risk_levels = {str(v).upper() for v in as_list(rule.get("allowedRiskLevels"))}
    if risk_levels:
        reasons.append("risk-level rule exists but order risk evidence was not available in detail/list payload")

    has_conditions = bool(sku_list or order_sources or channels or risk_levels)
    if blockers:
        return None
    if not has_conditions:
        reasons.append("rule has no supported matching criteria in this script; candidate only by enabled/permanent rule scope")
    confidence = "candidate"
    if reasons and not any("not available" in reason for reason in reasons):
        confidence = "likely_candidate"
    return {
        "ruleId": rule.get("id"),
        "ruleName": rule.get("ruleName"),
        "status": rule.get("status"),
        "holdMode": rule.get("holdMode"),
        "priority": rule.get("priority"),
        "confidence": confidence,
        "evidence": reasons,
    }


def summarize_order(order, rules):
    matches = []
    for rule in rules:
        matched = match_rule(order, rule)
        if matched:
            if rule.get("status") == "ENABLED":
                matched["matchType"] = "active_rule_candidate"
            else:
                matched["matchType"] = "disabled_or_historical_rule_candidate"
                matched["evidence"].append(
                    "Rule is currently disabled; it can explain historical holds only if the order was held while the rule was enabled."
                )
            matches.append(matched)
    matches.sort(key=lambda row: row.get("priority") if row.get("priority") is not None else 999999)
    return {
        "orderNo": order.get("orderNo"),
        "status": order.get("status"),
        "channelName": order.get("channelName"),
        "dataChannel": order.get("dataChannel"),
        "source": order.get("source"),
        "skus": sorted(order_skus(order)),
        "candidateRules": matches,
        "matchBasis": "candidate_inference_from_order_fields_and_rule_config",
        "evidenceBoundary": (
            "This is not a direct hold execution log. Confirm exact causality with ORDER_HOLD_OR "
            "execution logs, order event logs, or OMS hold records when available."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--orders", nargs="*", default=[])
    parser.add_argument("--page", type=int, default=1)
    parser.add_argument("--size", type=int, default=20)
    parser.add_argument("--rule-size", type=int, default=100)
    parser.add_argument("--max-workers", type=int, default=4)
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    if args.orders:
        workers = max(1, min(args.max_workers, 8, len(args.orders)))
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            orders = list(executor.map(get_order, args.orders))
    else:
        orders = query_on_hold_orders(args.page, args.size)
    rules = get_rules(args.rule_size)
    results = [summarize_order(order, rules) for order in orders if order]
    output = {
        "_env": oms_client.get_env_label(),
        "summary": {
            "orderCount": len(results),
            "ruleCount": len(rules),
            "ordersWithCandidates": sum(1 for row in results if row.get("candidateRules")),
            "ordersWithActiveRuleCandidates": sum(
                1
                for row in results
                if any(rule.get("matchType") == "active_rule_candidate" for rule in row.get("candidateRules", []))
            ),
            "ordersWithHistoricalCandidates": sum(
                1
                for row in results
                if any(
                    rule.get("matchType") == "disabled_or_historical_rule_candidate"
                    for rule in row.get("candidateRules", [])
                )
            ),
        },
        "results": results,
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
