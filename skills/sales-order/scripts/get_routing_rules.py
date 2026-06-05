"""
读取当前商户的路由规则列表
用法: python get_routing_rules.py [--config '{"baseUrl":"..."}']
"""
import sys, os, json, argparse
sys.path.insert(0, os.path.dirname(__file__))
import oms_client

def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    merchant_no = oms_client._env("OMS_MERCHANT_NO")
    result = oms_client.get("/api/linker-oms/opc/app-api/routing/v2/rules", {"merchantNo": merchant_no})
    result["_env"] = oms_client.get_env_label()
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
