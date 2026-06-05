"""
Suggest a replenishment purchase-order plan from SKU quantities.

Usage:
  python suggest_purchase_order.py --sku BATESTSKU-1 --quantity 10
  python suggest_purchase_order.py --skus '[{"sku":"A","quantity":10},{"sku":"B","quantity":5}]'
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import oms_client


def parse_items(args, parser):
    if args.skus:
        items = json.loads(args.skus)
    elif args.sku and args.quantity is not None:
        items = [{"sku": args.sku, "quantity": args.quantity}]
    else:
        parser.error("Provide either --skus JSON or --sku plus --quantity.")
    normalized = []
    for item in items:
        sku = item.get("sku")
        quantity = item.get("quantity")
        if not sku:
            parser.error("Every item requires sku.")
        if quantity is None or float(quantity) <= 0:
            parser.error(f"SKU {sku} requires a positive quantity.")
        normalized.append({"sku": sku, "quantity": quantity, "uom": item.get("uom", "EA")})
    return normalized


def extract_warehouses(inventory):
    inv_data = inventory.get("data", {})
    inv_items = inv_data if isinstance(inv_data, list) else inv_data.get("list", [])
    warehouse_map = {}
    for item in inv_items or []:
        no = str(item.get("warehouseNo") or item.get("warehouseId") or item.get("omsWarehouseId") or "")
        if not no:
            continue
        name = str(item.get("warehouseName") or item.get("warehouse") or no)
        warehouse_map.setdefault(
            no,
            {
                "warehouseNo": no,
                "warehouseName": name,
                "displayNameConfirmed": name != no,
            },
        )
    return list(warehouse_map.values())


def extract_active_rules(routing):
    routing_rules = routing.get("data", []) if isinstance(routing.get("data"), list) else []
    active = []
    disabled = []
    for page in routing_rules:
        for rule in page.get("ruleItems", []) or []:
            name = rule.get("ruleName") or rule.get("ruleId")
            if rule.get("switchOn"):
                active.append(name)
            else:
                disabled.append(name)
    return routing_rules, active, disabled


def build_plan(items, warehouses, active_rules, requested_warehouse=None):
    if requested_warehouse:
        selected = {
            "warehouseNo": requested_warehouse,
            "warehouseName": requested_warehouse,
            "displayNameConfirmed": True,
            "userSpecified": True,
        }
        reason = "User specified the target warehouse, so the recommendation preserves that constraint."
    elif warehouses:
        selected = warehouses[0]
        reason = (
            "Selected the first and only visible warehouse from inventory availability."
            if len(warehouses) == 1
            else "Selected the first visible warehouse; review alternatives before creating a PO."
        )
    else:
        selected = {
            "warehouseNo": "(select a warehouse)",
            "warehouseName": "(select a warehouse)",
            "displayNameConfirmed": False,
        }
        reason = "No warehouse was returned by inventory/list; user must provide a target warehouse."

    routing_reason = (
        "Routing context has ONE_WAREHOUSE_BACKUP enabled, so a single-warehouse replenishment plan is compatible."
        if "ONE_WAREHOUSE_BACKUP" in active_rules
        else "Routing context was loaded, but no explicit one-warehouse fallback was enabled."
    )
    return {
        "targetWarehouseNo": selected["warehouseNo"],
        "targetWarehouseName": selected["warehouseName"],
        "warehouseDisplayName": (
            f"{selected['warehouseName']} ({selected['warehouseNo']})"
            if selected.get("displayNameConfirmed") and not selected.get("userSpecified")
            else f"{selected['warehouseName']} (user-specified warehouse; confirm it is accepted by OMS before creating a PO)"
            if selected.get("userSpecified")
            else f"{selected['warehouseNo']} (warehouse display name not returned; confirm before creating a PO)"
        ),
        "needsWarehouseNameConfirmation": selected.get("userSpecified") or not selected.get("displayNameConfirmed"),
        "items": items,
        "evidence": [reason, routing_reason],
        "confidence": "medium" if warehouses or requested_warehouse else "low",
    }


def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--skus", default=None, help='JSON array, e.g. [{"sku":"A","quantity":10}]')
    parser.add_argument("--sku", default=None, help="Single SKU. PowerShell-friendly alternative to --skus.")
    parser.add_argument("--quantity", type=int, default=None, help="Quantity for --sku.")
    parser.add_argument("--warehouse", default=None, help="Optional user-specified target warehouse")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    items = parse_items(args, parser)
    merchant_no = oms_client._env("OMS_MERCHANT_NO")
    inventory = oms_client.post("/api/linker-oms/opc/app-api/inventory/list", {"merchantNo": merchant_no})
    routing = oms_client.get("/api/linker-oms/opc/app-api/routing/v2/rules", {"merchantNo": merchant_no})

    warehouses = extract_warehouses(inventory)
    routing_rules, active_rules, disabled_rules = extract_active_rules(routing)
    plan = build_plan(items, warehouses, active_rules, args.warehouse)
    alternatives = [warehouse for warehouse in warehouses if warehouse.get("warehouseNo") != plan.get("targetWarehouseNo")]

    result = {
        "availableWarehouses": warehouses,
        "alternatives": alternatives,
        "routingRules": routing_rules,
        "routingRuleSummary": {
            "pageCount": len(routing_rules),
            "activeRules": active_rules,
            "disabledRules": disabled_rules,
            "note": "Routing rules are replenishment context only; they do not prove why a sales order was allocated to a warehouse.",
        },
        "suggestedPlan": [plan],
        "diagnosis": (
            f"Recommended replenishment to {plan['warehouseDisplayName']} for "
            f"{', '.join(str(item['quantity']) + ' ' + item['uom'] + ' ' + item['sku'] for item in items)}. "
            f"Evidence: {'; '.join(plan['evidence'])}"
        ),
        "recommendedNextStep": (
            "Confirm the warehouse display name and the SKU quantities before creating a purchase order."
            if plan["needsWarehouseNameConfirmation"]
            else "Confirm the suggested plan or adjust the warehouse split before creating a purchase order."
        ),
        "_env": oms_client.get_env_label(),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
