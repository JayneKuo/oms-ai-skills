"""
查询销售订单列表
用法: python query_orders.py [--keyword KW] [--status EXCEPTION] [--page 1] [--size 20]
"""
import sys, os, json, argparse
sys.path.insert(0, os.path.dirname(__file__))
import oms_client

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
    result["_env"] = oms_client.get_env_label()
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
