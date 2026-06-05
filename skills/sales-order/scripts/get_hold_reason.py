"""
查询订单 Hold 原因（优先使用 ORDER_HOLD_OR 规则执行接口）
用法: python get_hold_reason.py --order SO00361770
"""
import sys, os, json, argparse
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
        "note": "Hold reason is resolved from ORDER_HOLD_OR rule execution when the rule engine returns match/log data."
    }
    result["_env"] = oms_client.get_env_label()
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
