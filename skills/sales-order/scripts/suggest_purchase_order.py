"""
根据库存和路由规则推荐补货方案
用法: python suggest_purchase_order.py --skus '[{"sku":"SKU-A","quantity":10}]'
"""
import sys, os, json, argparse
sys.path.insert(0, os.path.dirname(__file__))
import oms_client

def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--skus", required=True, help='JSON 数组，如 [{"sku":"A","quantity":10}]')
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    items = json.loads(args.skus)
    merchant_no = oms_client._env("OMS_MERCHANT_NO")

    # 并行拉取库存和路由规则
    inventory = oms_client.post("/api/linker-oms/opc/app-api/inventory/list", {"merchantNo": merchant_no})
    routing = oms_client.get("/api/linker-oms/opc/app-api/routing/v2/rules", {"merchantNo": merchant_no})

    inv_data = inventory.get("data", {})
    inv_items = inv_data if isinstance(inv_data, list) else inv_data.get("list", [])

    # 去重仓库列表
    warehouse_map = {}
    for item in inv_items:
        no = str(item.get("warehouseNo") or item.get("warehouseId") or "")
        if no and no not in warehouse_map:
            warehouse_map[no] = {"warehouseNo": no, "warehouseName": str(item.get("warehouseName") or no)}
    available_warehouses = list(warehouse_map.values())

    routing_rules = routing.get("data", []) if isinstance(routing.get("data"), list) else []
    default_warehouse = available_warehouses[0]["warehouseNo"] if available_warehouses else "(select a warehouse)"

    result = {
        "availableWarehouses": available_warehouses,
        "routingRules": routing_rules,
        "suggestedPlan": [{"targetWarehouseNo": default_warehouse, "items": items}],
        "diagnosis": (
            f"Found {len(available_warehouses)} warehouse(s). Routing rules loaded ({len(routing_rules)} page(s)) for context. "
            f"Default plan sends all items to {default_warehouse}. You can split across warehouses or pick a different one."
            if routing_rules else
            f"No routing rules found. Default plan sends all items to {default_warehouse}."
            if available_warehouses else
            "No warehouses found. Please specify a target warehouse manually."
        )
    }
    result["_env"] = oms_client.get_env_label()
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
