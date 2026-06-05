"""
释放 ON_HOLD 订单
用法: python release_hold.py --order SO00361770
"""
import sys, os, json, argparse, urllib.parse
sys.path.insert(0, os.path.dirname(__file__))
import oms_client

def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--order", required=True, help="订单号")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    result = oms_client.post(
        f"/api/linker-oms/opc/app-api/order-hold/release?orderNo={urllib.parse.quote(args.order)}"
    )
    result["_env"] = oms_client.get_env_label()
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
