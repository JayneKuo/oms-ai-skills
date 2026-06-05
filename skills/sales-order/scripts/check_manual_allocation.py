"""
检查订单是否可以手动分配
用法: python check_manual_allocation.py --order SO00361770
"""
import sys, os, json, argparse
sys.path.insert(0, os.path.dirname(__file__))
import oms_client

def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--order", required=True, help="订单号")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    result = oms_client.get(f"/api/linker-oms/opc/app-api/dispatch/hand/check/{args.order}")
    result["_env"] = oms_client.get_env_label()
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
