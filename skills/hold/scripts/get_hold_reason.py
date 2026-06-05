"""
查询订单 Hold 原因（优先使用 ORDER_HOLD_OR 规则执行接口）
用法: python get_hold_reason.py --order SO00361770
"""
import sys, os, json, argparse
import urllib.error
sys.path.insert(0, os.path.dirname(__file__))
import oms_client


def build_rule_request(order_no, merchant_no, order_data):
    return {
        "merchantNo": merchant_no,
        "businessKey": order_no,
        "testMode": False,
        "facts": {
            "order": order_data
        },
        "variables": {
            "stopOnFirstMatch": False
        }
    }


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--order", required=True, help="订单号")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    merchant_no = oms_client._env("OMS_MERCHANT_NO")
    detail = oms_client.get(f"/api/linker-oms/opc/app-api/sale-order/{args.order}")
    order_data = detail.get("data", {})

    if order_data.get("status") != "ON_HOLD":
        result = {
            "orderNo": args.order,
            "status": order_data.get("status"),
            "matched": None,
            "matchedRuleCount": None,
            "matchedRules": [],
            "executedActions": [],
            "executionLogs": [],
            "errors": [],
            "ruleExecutionStatus": "NOT_APPLICABLE",
            "confirmed": ["order_detail", "not_currently_on_hold"],
            "unconfirmed": [],
            "recommendedNextStep": "This order is not currently ON_HOLD, so there is no active hold to release. If you need the historical hold reason, check order event/log records or OMS hold history.",
            "note": "Do not diagnose an active hold when the latest order detail is not ON_HOLD.",
            "_env": oms_client.get_env_label()
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    try:
        rule_resp = oms_client.post(
            "/api/linker-oms/oas/rpc-api/rule/types/ORDER_HOLD_OR/execute",
            build_rule_request(args.order, merchant_no, order_data),
            extra_headers={
                "trace": "true",
                "locale": "zh-CN"
            }
        )
        rule_data = rule_resp.get("data") or {}
        result = {
            "orderNo": args.order,
            "status": order_data.get("status"),
            "matched": rule_data.get("matched"),
            "matchedRuleCount": rule_data.get("matchedRuleCount"),
            "matchedRules": rule_data.get("matchedRules") or [],
            "executedActions": rule_data.get("executedActions") or [],
            "executionLogs": rule_data.get("executionLogs") or [],
            "errors": rule_data.get("errors") or [],
            "ruleExecutionStatus": rule_data.get("status"),
            "confirmed": ["order_detail"],
            "unconfirmed": [] if rule_data.get("matchedRules") or rule_data.get("executionLogs") else ["specific_hold_rule_reason"],
            "recommendedNextStep": "Use matched rules/logs above to explain the hold reason. If they are empty, check order event/log records before giving a final reason.",
            "note": "Hold reason is resolved from ORDER_HOLD_OR rule execution when the rule engine returns match/log data."
        }
    except urllib.error.HTTPError as exc:
        result = {
            "orderNo": args.order,
            "status": order_data.get("status"),
            "matched": None,
            "matchedRuleCount": None,
            "matchedRules": [],
            "executedActions": [],
            "executionLogs": [],
            "errors": [f"ORDER_HOLD_OR lookup failed with HTTP {exc.code}"],
            "ruleExecutionStatus": "UNAVAILABLE",
            "confirmed": ["order_detail"],
            "unconfirmed": ["specific_hold_rule_reason"],
            "recommendedNextStep": "The order status is confirmed from detail, but the rule endpoint is unavailable in this environment. Check order event/log records or OMS hold records before explaining the hold reason.",
            "note": "Do not guess the hold rule reason when ORDER_HOLD_OR is unavailable."
        }
    except urllib.error.URLError as exc:
        result = {
            "orderNo": args.order,
            "status": order_data.get("status"),
            "matched": None,
            "matchedRuleCount": None,
            "matchedRules": [],
            "executedActions": [],
            "executionLogs": [],
            "errors": [f"ORDER_HOLD_OR lookup failed: {exc.reason}"],
            "ruleExecutionStatus": "UNAVAILABLE",
            "confirmed": ["order_detail"],
            "unconfirmed": ["specific_hold_rule_reason"],
            "recommendedNextStep": "The order status is confirmed from detail, but the rule endpoint is unavailable in this environment. Check order event/log records or OMS hold records before explaining the hold reason.",
            "note": "Do not guess the hold rule reason when ORDER_HOLD_OR is unavailable."
        }
    result["_env"] = oms_client.get_env_label()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
