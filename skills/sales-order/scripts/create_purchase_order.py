"""
创建补货采购单（单仓）
用法: python create_purchase_order.py --warehouse "Main Warehouse" --skus '[{"sku":"BATESTSKU-1","quantity":1}]'
"""
import sys, os, json, argparse, time
sys.path.insert(0, os.path.dirname(__file__))
import oms_client

def main():
    parser = argparse.ArgumentParser()
    oms_client.add_config_arg(parser)
    parser.add_argument("--warehouse", required=True, help="目标仓库名称/编号")
    parser.add_argument("--skus", required=True, help='JSON 数组，如 [{"sku":"A","quantity":10}]')
    parser.add_argument("--channel-no", default="C00000568")
    parser.add_argument("--channel-name", default="Walmart-test11")
    parser.add_argument("--data-channel", default="Walmart")
    parser.add_argument("--accounting-code", default="889")
    args = parser.parse_args()
    oms_client.load_config_arg(args)

    items = json.loads(args.skus)
    suffix = str(int(time.time()))[-8:]
    body = {
        "merchantNo": oms_client._env("OMS_MERCHANT_NO"),
        "orderNo": "P" + suffix,
        "referenceNo": "R" + suffix,
        "source": "CREATED",
        "orderEventType": "CREATE_ORDER",
        "receiptType": "REGULAR_RECEIPT",
        "accountingCode": args.accounting_code,
        "channelNo": args.channel_no,
        "channelName": args.channel_name,
        "dataChannel": args.data_channel,
        "warehouseName": args.warehouse,
        "itemList": [
            {"poLineNo": str(index + 1), "sku": item["sku"], "qty": item["quantity"], "uom": item.get("uom", "EA")}
            for index, item in enumerate(items)
        ]
    }

    result = oms_client.post("/api/linker-oms/opc/app-api/purchase-order", body)
    result["_env"] = oms_client.get_env_label()
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
