---
name: sales-order
description: OMS 閿€鍞鍗曞叏娴佺▼澶勭悊鎶€鑳姐€傚綋鐢ㄦ埛鎻愬埌閿€鍞鍗曘€佸紓甯歌鍗曘€丱N_HOLD 璁㈠崟銆佹墜鍔ㄥ垎浠撱€佽ˉ璐ч噰璐崟銆侀噴鏀?hold銆侀噸鏂板紑鍚鍗曘€佸彇娑堣鍗曘€佹煡璇㈣鍗曠姸鎬佹椂瑙﹀彂銆傝鐩栦粠璇婃柇鍒版墽琛岀殑瀹屾暣宸ヤ綔娴侊細鏌ヨ 鈫?璇婃柇 鈫?閲婃斁 hold / 鎵嬪姩鍒嗕粨 / 琛ヨ揣閲囪喘鍗?鈫?閲嶆柊寮€鍚?/ 鍙栨秷銆俇se this skill whenever the user mentions sales orders, order exceptions, warehouse allocation, purchase order replenishment, or any OMS order operation.
---

# Sales Order Skill

## Cancel Downstream Guardrail

- If a sales order already has dispatch/WMS records, OMS cancel may publish downstream Kafka work and return `ongoingRespDTOS`.
- Treat `ongoingRespDTOS` as downstream cancellation in progress, not success.
- Re-check order detail and dispatch status before saying cancellation completed.
- Only report completion after both sales order and dispatch are `Cancelled`.
- If downstream rejects, report the rejection and do not mark the cancel successful.

澶勭悊 Linker OMS 閿€鍞鍗曠殑瀹屾暣宸ヤ綔娴併€傛墍鏈夋搷浣滈€氳繃 `scripts/` 鐩綍涓嬬殑 Python 鑴氭湰鎵ц锛屽彧闇€ Python 3 鏍囧噯搴擄紝鏃犻渶瀹夎浠讳綍渚濊禆銆?
## 鐜閰嶇疆

鎵€鏈夎剼鏈緭鍑洪兘鍖呭惈 `_env` 瀛楁锛屾爣娉ㄥ綋鍓嶆搷浣滅殑鏄摢涓幆澧冿紙`staging` 鎴?`production`锛夛紝鏂逛究鍦?agent 鍝嶅簲涓尯鍒嗐€?
### 娴嬭瘯鐜锛坰taging锛?
鍦?Agent 鐨勩€岀幆澧冨彉閲忋€嶉潰鏉夸腑娣诲姞锛?
| KEY | VALUE |
|-----|-------|
| `OMS_ENV` | `staging` |
| `OMS_BASE_URL` | `https://omsv2-staging.item.com` |
| `OMS_TENANT_ID` | `LT` |
| `OMS_MERCHANT_NO` | `LAN0000002` |
| `OMS_USERNAME` | `your_username@item.com` |
| `OMS_PASSWORD` | `your_password` |

### 鐢熶骇鐜锛坧roduction锛?
灏嗕互涓婂彉閲忔浛鎹负鐢熶骇鐜瀵瑰簲鍊硷細

| KEY | VALUE |
|-----|-------|
| `OMS_ENV` | `production` |
| `OMS_BASE_URL` | `https://omsv2.item.com` |
| `OMS_TENANT_ID` | `<鐢熶骇绉熸埛 ID>` |
| `OMS_MERCHANT_NO` | `<鐢熶骇鍟嗘埛鍙?` |
| `OMS_USERNAME` | `<鐢熶骇璐﹀彿>` |
| `OMS_PASSWORD` | `<鐢熶骇瀵嗙爜>` |

### 閫氳繃 API 浼犲弬锛堜笂娓?agent 璋冪敤锛?
```bash
python scripts/query_orders.py \
  --config '{"env":"production","baseUrl":"https://omsv2.item.com","tenantId":"LT","merchantNo":"LAN0000002","username":"x@item.com","password":"xxx"}' \
  --status EXCEPTION
```

鎺ュ彈鐨勫弬鏁板悕锛歚env`銆乣baseUrl`銆乣tenantId`銆乣merchantNo`銆乣username`銆乣password`

### 鍙橀噺缂哄け鏃剁殑澶勭悊

濡傛灉鑴氭湰 stderr 杈撳嚭 `"error": "missing_env"`锛岃鏄庢煇涓幆澧冨彉閲忔湭璁剧疆銆傛鏃讹細

1. 鍚戠敤鎴疯鏄庣己灏戝摢涓彉閲忥紝鐢ㄥ弸濂借瑷€璇㈤棶锛?   - `OMS_BASE_URL` 鈫?"璇锋彁渚?OMS 鏈嶅姟鍣ㄥ湴鍧€锛堝 https://omsv2-staging.item.com锛?
   - `OMS_USERNAME` / `OMS_PASSWORD` 鈫?"璇锋彁渚涗綘鐨?OMS 鐧诲綍璐﹀彿鍜屽瘑鐮?
   - `OMS_TENANT_ID` 鈫?"璇锋彁渚涚鎴?ID锛堥€氬父鏄?2-3 浣嶅瓧姣嶏紝濡?LT锛?
   - `OMS_MERCHANT_NO` 鈫?"璇锋彁渚涘晢鎴峰彿锛堝 LAN0000002锛?

2. 鐢ㄦ埛鎻愪緵鍚庯紝鐢?`export` 璁剧疆鍒板綋鍓嶄細璇濓紝鐒跺悗閲嶆柊鎵ц鍛戒护锛?   ```bash
   export OMS_BASE_URL=鐢ㄦ埛鎻愪緵鐨勫€?   ```

3. 涓婃父绯荤粺鍙兘鐢ㄤ笉鍚屽彉閲忓悕浼犲叆锛堝 `BASE_URL`銆乣TENANT_ID`锛夛紝`oms_client.py` 浼氳嚜鍔ㄨ瘑鍒父瑙佸埆鍚嶏紝鏃犻渶鎵嬪姩鏄犲皠銆?
## 鐢ㄦ埛杈撳嚭纭鍒?
榛樿闈㈠悜涓氬姟杩愯惀杈撳嚭锛岄櫎闈炵敤鎴锋槑纭姹傛妧鏈粏鑺傘€?
鐢ㄦ埛鍙礋璐ｅ喅绛栵紝涓嶈礋璐ｆ帹鐞嗐€俛gent 蹇呴』涓诲姩鍛婅瘔鐢ㄦ埛锛?1. 缁撴灉鏄粈涔?2. 涓轰粈涔堜細杩欐牱
3. 鍙鐨勮В鍐虫柟妗堟槸浠€涔?4. 涓嬩竴姝ュ簲璇ユ€庝箞鍋?
榛樿杈撳嚭椤哄簭锛氱粨鏋?鈫?鍘熷洜 鈫?瑙ｅ喅鏂规 鈫?涓嬩竴姝ャ€?
闄ら潪鐢ㄦ埛鏄庣‘瑕佹眰锛屽惁鍒欎笉瑕佺洿鎺ュ睍绀哄簳灞傚瓧娈垫垨澶ф JSON锛屼緥濡?`data=true/false`銆乣successRespDTOS`銆乣failRespDTOS`銆乣ongoingRespDTOS`銆乨ispatch remark 鍘熸枃銆乺outing rules 鍘熷缁撴瀯銆?
绯荤粺鐘舵€佸繀椤荤炕璇戞垚浜鸿瘽銆備緥濡傦細
- `ALLOCATED` 鈫?宸茶繘鍏ュ垎閰嶉樁娈?- `WAREHOUSE_PROCESSING` 鈫?宸茶繘鍏ヤ粨搴撳鐞嗘祦绋?- `DISPATCHED` 鈫?宸叉彁浜ゅ埌浠撳簱澶勭悊
- `EXCEPTION` 鈫?褰撳墠浠嶅浜庡紓甯哥姸鎬?- `ON_HOLD` 鈫?褰撳墠琚?hold锛屾殏鏃朵笉鑳界户缁祦杞?- `ongoing` 鈫?绯荤粺宸叉帴鏀惰姹傦紝浠嶅湪澶勭悊涓?
濡傛灉褰撳墠鍙兘纭缁撴灉锛屼笉鑳界‘璁ゅ師鍥狅紝蹇呴』鏄庣‘鍛婅瘔鐢ㄦ埛鈥滅幇鍦ㄥ彧鑳界‘璁や粈涔堛€佽繕涓嶈兘纭浠€涔堛€佷笅涓€姝ラ渶瑕佹煡浠€涔堚€濓紝绂佹鎶婃帹娴嬪寘瑁呮垚浜嬪疄銆?
### 閿€鍞鍗曞垎浠撹鏄?
褰撶敤鎴烽棶閿€鍞鍗曞垎鍒板摢涓粨銆佷负浠€涔堝垎鍒拌繖涓粨鏃讹紝蹇呴』灏介噺鍥炵瓟锛?- 鍒嗗埌鍝釜浠?- 鏄郴缁熻嚜鍔ㄥ垎浠撹繕鏄汉宸ユ寚瀹?- 涓轰粈涔堝垎鍒拌繖涓粨
- 褰撳墠鏄惁杩橀渶瑕佺敤鎴峰共棰?
閿€鍞鍗曞垎浠撳師鍥犲繀椤绘潵鑷湡瀹炶瘉鎹紝涓嶅緱闈?agent 鑷鎺ㄦ祴銆備紭鍏堣瘉鎹潵婧愶細
1. 鍒嗕粨鎴愬姛鏃ュ織
2. dispatch 璁板綍
3. route / routing 鐩稿叧璇佹嵁
4. 璁㈠崟璇︽儏涓兘鏄庣‘鏀寔缁撹鐨勫瓧娈?
绂佹浠呭嚟 `warehouseName`銆乣accountingCode`銆乣ALLOCATED`銆乣WAREHOUSE_PROCESSING` 绛夋渶缁堢粨鏋滃瓧娈佃В閲娾€滀负浠€涔堝垎鍒拌繖涓粨鈥濄€傝繖浜涘瓧娈靛彧鑳借瘉鏄庣粨鏋滐紝涓嶈兘鍗曠嫭璇佹槑鍘熷洜銆?
濡傛灉褰撳墠鍙兘纭璁㈠崟宸茬粡鍒嗗埌鏌愪粨锛屼絾娌℃湁鎷垮埌瓒冲鐨勫垎浠撴棩蹇?dispatch 璇佹嵁锛屽氨鍙兘璇存槑缁撴灉锛屼笉鑳借В閲婂師鍥狅紱鍚屾椂瑕佷富鍔ㄥ憡璇夌敤鎴峰彲浠ョ户缁煡瀵瑰簲鏃ュ織銆?
### EXCEPTION 璁㈠崟璇存槑

寮傚父璁㈠崟蹇呴』缁欏嚭鈥滃師鍥犲拰瑙ｅ喅鏂规鈥濓紝涓嶈兘鍙憡璇夌敤鎴疯繖鏄?EXCEPTION銆?
搴斾紭鍏堜粠鐪熷疄鎺ュ彛/璇︽儏杩斿洖涓彁鍙栧師鍥犲拰鏂规锛屼緥濡傦細`diagnosis`銆乣availableActions`銆乣recommendedNextStep`銆乣inventorySummary`銆佹槑纭殑 detail 閿欒銆佺浉鍏?dispatch/log 璇佹嵁銆?
濡傛灉鎺ュ彛宸茬粡缁欏嚭澶勭悊鏂瑰悜锛屽繀椤昏浆鎴愪笟鍔¤瑷€鐩存帴鍛婅瘔鐢ㄦ埛锛屼笉鑳芥妸 diagnosis 鎴?availableActions 鍘熸牱涓㈢粰鐢ㄦ埛鑷繁鐞嗚В銆?
### ON_HOLD 璁㈠崟璇存槑

瀵逛簬 ON_HOLD锛屽繀椤诲尯鍒嗭細
1. hold 鏈韩鐨勯棶棰?2. 鍒嗕粨/搴撳瓨鐨勯棶棰?
澶勭悊椤哄簭锛氬厛纭 hold 鐘舵€侊紝鍐嶅皾璇?release锛涘鏋?release 澶辫触锛屽啀妫€鏌?allocation/remaining锛屽苟鐩存帴鍛婅瘔鐢ㄦ埛褰撳墠鍗＄偣鍒板簳鍦?hold 杩樻槸鍒嗕粨銆?
濡傛灉鎵€鏈夊晢鍝侀兘宸茬粡鍒嗛厤瀹屾垚锛屽繀椤绘槑纭憡璇夌敤鎴凤細褰撳墠涓嶈兘缁х画鎵嬪姩鍒嗕粨锛岄棶棰樹笉鍦ㄥ簱瀛樺垎閰嶏紝鑰屽湪 hold 鏈韩娌℃湁瑙ｉ櫎銆?
### 琛ヨ揣 / 閲囪喘鍗曟帹鑽愯鏄?
鎺ㄨ崘閲囪喘浠撴垨琛ヨ揣鏂规鏃讹紝蹇呴』涓诲姩鍛婅瘔鐢ㄦ埛锛?- 鎺ㄨ崘鍝釜浠?- 涓轰粈涔堟帹鑽愯繖涓粨
- 鏄惁杩樻湁鍏朵粬鍙€夐」
- 褰撳墠鏄惁闇€瑕佺敤鎴风‘璁?
鎺ㄨ崘鍘熷洜蹇呴』灏介噺鏉ヨ嚜鐪熷疄渚濇嵁锛屼緥濡傚綋鍓嶅彲鐢ㄤ粨搴撶粨鏋溿€乺outing 瑙勫垯涓婁笅鏂囥€乫ulfillment/WMS 鍙敤鎬с€乺ank/浼樺厛绾с€佺敤鎴锋寚瀹氭潯浠躲€?
### 楂橀闄╀笌寮傛缁撴灉璇存槑

cancel銆乺eopen銆乥atch release hold / batch reopen銆乫orce allocate 绛夐珮椋庨櫓鍐欐搷浣滈粯璁や笉鐩存帴鎵ц锛屽繀椤诲厛纭鐜銆佹搷浣溿€佸璞″拰椋庨櫓锛屽苟缁欏嚭鏄庣‘纭鐭彞銆?
濡傛灉鎺ュ彛杩斿洖鐨勬槸 submitted / ongoing / 宸茶皟鐢ㄤ絾鐘舵€佹湭鍙橈紝蹇呴』鏄庣‘鍖哄垎鈥滄帴鍙ｅ凡鍙楃悊鈥濆拰鈥滀笟鍔″凡瀹屾垚鈥濓紝涓嶈兘鎶婅姹傚凡鎻愪氦璇存垚鏈€缁堟垚鍔熴€?
## 宸ヤ綔娴?
### 1. 鍒涘缓璁㈠崟

褰撶敤鎴疯鈥滃府鎴戝垱寤鸿鍗曗€濇椂锛屽厛鏀堕泦鏈€灏戝繀瑕佷俊鎭細

- 鍟嗗搧锛歋KU銆佹暟閲?- 鏀惰揣鍦板潃锛氭敹璐т汉銆佸湴鍧€銆佸煄甯傘€佸窞/鐪併€侀偖缂栥€佸浗瀹讹紙鐢佃瘽/閭鍙€変絾寤鸿锛?- 娓犻亾璁㈠崟鍙凤細濡傛灉鐢ㄦ埛鏈彁渚涳紝鑷姩鐢熸垚 `AI-ORDER-<timestamp>`
- 鐜锛氶粯璁や娇鐢ㄥ凡閰嶇疆鐜锛屽苟鍦ㄧ粨鏋滈噷璇存槑 `_env`

濡傛灉鐢ㄦ埛璇粹€滃叾浠栭殢渚垮～鈥濓紝鍙娇鐢ㄦ祴璇曢粯璁ゅ湴鍧€锛?
```json
{"name":"1","address1":"1","address2":"1","city":"ABMPS","state":"NY","country":"US","zipCode":"111111","phone":"1","email":"1@qq.com"}
```

鍒涘缓鍛戒护锛?
```bash
python scripts/create_order.py \
  --channel-order-no AI-ORDER-$(date +%s) \
  --skus '[{"sku":"BATESTSKU-1","qty":10}]' \
  --ship-to '{"name":"1","address1":"1","address2":"1","city":"ABMPS","state":"NY","country":"US","zipCode":"111111","phone":"1","email":"1@qq.com"}'
```

鍒涘缓鎴愬姛鍚庤繑鍥烇細璁㈠崟鍙枫€丼KU/鏁伴噺銆佺姸鎬併€佺幆澧冿紝浠ュ強涓嬩竴姝ュ缓璁€?
### 2. 鏌ヨ璁㈠崟

```bash
python scripts/query_orders.py --status EXCEPTION --size 20
python scripts/query_orders.py --keyword SO00361770
```

### 2. 鏌ョ湅璁㈠崟璇︽儏

```bash
python scripts/get_order_detail.py --order SO00361770
```

鎷垮埌璇︽儏鍚庡垽鏂姸鎬侊細
- `EXCEPTION` 鈫?浼樺厛璇诲彇璇︽儏閲岀殑 diagnosis / availableActions / recommendedNextStep / inventorySummary / 鏄庣‘閿欒淇℃伅锛屽悜鐢ㄦ埛璇存槑寮傚父鍘熷洜鍜岃В鍐虫柟妗堬紱鍙湁鍦ㄨ繖浜涗俊鎭笉瓒虫椂锛屾墠缁х画缁撳悎 warehouse銆乮temLines銆乨ispatch/log 璇佹嵁琛ュ厖鍒ゆ柇
- `ON_HOLD` 鈫?鍏堟煡 hold 鍘熷洜锛屽啀灏濊瘯閲婃斁锛涘鏋?release 澶辫触锛屽啀缁撳悎 allocation/remaining 鏄庣‘鍛婅瘔鐢ㄦ埛褰撳墠闂鍦?hold 鏈韩杩樻槸鍒嗕粨/搴撳瓨

### 3. Hold 鍘熷洜鏌ヨ

```bash
python scripts/get_hold_reason.py --order SO00361770
```

娉ㄦ剰锛氬簲浼樺厛閫氳繃 `ORDER_HOLD_OR` 瑙勫垯鎵ц鎺ュ彛鏌ヨ璁㈠崟绾?hold 鍘熷洜銆佸懡涓鍒欏拰鎵ц鏃ュ織锛岃€屼笉鏄彧鐪嬪晢鎴风骇 active hold 鏁伴噺銆傚彧鏈夊湪瑙勫垯鎵ц鎺ュ彛鏃犳硶鎻愪緵瓒冲淇℃伅鏃讹紝鎵嶉€€鍥炲埌 OMS 椤甸潰缁х画浜哄伐鏌ョ湅銆?
### 4. 閲婃斁 Hold锛圤N_HOLD 璁㈠崟锛?
```bash
python scripts/release_hold.py --order SO00361770
```

- 杩斿洖 `data: true` 鈫?鎴愬姛锛岄噸鏂版煡鐪嬭鍗曠姸鎬?- 杩斿洖 `data: false` 鈫?澶辫触锛屾鏌ュ晢鍝佹槸鍚﹀凡鍏ㄩ儴鍒嗛厤锛?
```bash
python scripts/get_allocation_items.py --order SO00361770
```

濡傛灉鎵€鏈夊晢鍝?`remaining=0`锛屽憡鐭ョ敤鎴凤細鎵€鏈夊晢鍝佸凡鍒嗛厤锛宧old 鐢变笟鍔¤鍒欓攣瀹氾紝闇€鍦?OMS 鎵嬪姩澶勭悊銆?
### 5. 鎵嬪姩鍒嗕粨

鍏堢‘璁ゅ彲鎿嶄綔锛?```bash
python scripts/check_manual_allocation.py --order SO00361770
```

鑾峰彇鍙垎閰嶅晢鍝佽锛?```bash
python scripts/get_allocation_items.py --order SO00361770
```

- `remaining=0` 鈫?鍛婄煡鐢ㄦ埛鏃犻渶鎿嶄綔锛屾墍鏈夊晢鍝佸凡鍒嗛厤
- `remaining>0` 鈫?鎵ц鍒嗕粨锛?
```bash
python scripts/manual_allocate.py \
  --order SO00361770 \
  --warehouse WH-001 \
  --skus '[{"sku":"SKU-A","qty":2}]'
```

寮哄埗鍒嗕粨锛堣烦杩囧簱瀛樻鏌ワ級闇€鐢ㄦ埛鏄庣‘纭椋庨櫓鍚庢墠鎵ц銆?
### 6. 琛ヨ揣閲囪喘鍗?
鍏堣幏鍙栨帹鑽愭柟妗堬細
```bash
python scripts/suggest_purchase_order.py --skus '[{"sku":"SKU-A","quantity":10}]'
```

鐢ㄦ埛纭鍚庡垱寤猴紙鍗曚粨锛夛細
```bash
python scripts/create_purchase_order.py \
  --warehouse WH-001 \
  --skus '[{"sku":"SKU-A","quantity":10}]'
```

澶氫粨鎷嗗崟锛?```bash
python scripts/create_purchase_order_split.py \
  --orders '[{"warehouse":"WH-001","skus":[{"sku":"A","quantity":5}]},{"warehouse":"WH-002","skus":[{"sku":"A","quantity":5}]}]'
```

### 7. 璺敱瑙勫垯

```bash
python scripts/get_routing_rules.py
```

璺敱瑙勫垯鏄ˉ璐у缓璁殑鍙傝€冧笂涓嬫枃锛屼笉绛変簬閿€鍞鍗曞垎浠撳師鍥犮€傚悜鐢ㄦ埛瑙ｉ噴鈥滀负浠€涔堟帹鑽愯繖涓ˉ璐т粨鈥濇椂锛屽彲浠ヤ娇鐢?routing/鍙敤浠?浼樺厛绾ц瘉鎹紱鍚戠敤鎴疯В閲娾€滀负浠€涔堥攢鍞鍗曞垎鍒拌繖涓粨鈥濇椂锛屽繀椤讳紭鍏堟煡鍒嗕粨鏃ュ織銆乨ispatch 鎴栧叾浠栫湡瀹炲垎浠撹瘉鎹€?
### 8. 閲嶆柊寮€鍚?EXCEPTION 璁㈠崟

闇€鐢ㄦ埛纭鍚庢墽琛岋細
```bash
python scripts/reopen_order.py --order SO00361770
```

### 9. 鍙栨秷璁㈠崟锛堟敮鎸佹壒閲忥級

```bash
python scripts/cancel_order.py --orders SO00361770
python scripts/cancel_order.py --orders SO001 SO002 SO003
```

### 10. 鎵归噺 Reopen / Release Hold

```bash
python scripts/batch_orders.py --action reopen --orders SO001 SO002 SO003
python scripts/batch_orders.py --action release_hold --orders SO001 SO002
```

## 鍏抽敭鍘熷垯

- 榛樿闈㈠悜涓氬姟杩愯惀杈撳嚭锛屽厛璇寸粨鏋滐紝鍐嶈鍘熷洜銆佽В鍐虫柟妗堝拰涓嬩竴姝?- 鐢ㄦ埛鍙礋璐ｅ喅绛栵紝涓嶈礋璐ｆ帹鐞嗭紱绂佹鎶婄姸鎬佸瓧娈垫垨涓棿缁撴灉涓㈢粰鐢ㄦ埛鑷繁鎬濊€?- 閲婃斁 hold 澶辫触鏃讹紝鍏堟鏌?`remaining`锛屽啀鏄庣‘鍛婅瘔鐢ㄦ埛褰撳墠鍗＄偣鍦?hold 杩樻槸鍒嗕粨
- 鎵嬪姩鍒嗕粨鍓嶅繀椤绘鏌?`remaining`锛屼负 0 鏃舵槑纭憡鐭ョ敤鎴锋棤闇€鎿嶄綔
- 閿€鍞鍗曞垎浠撳師鍥犲繀椤绘煡鐪熷疄鏃ュ織/dispatch/route 璇佹嵁锛屼笉鑳介潬鏈€缁堢姸鎬佸瓧娈垫帹娴?- EXCEPTION 璁㈠崟蹇呴』缁欏嚭鍘熷洜鍜岃В鍐虫柟妗堬紝浼樺厛浣跨敤璇︽儏鎺ュ彛涓殑 diagnosis / availableActions / recommendedNextStep 绛夌湡瀹炰俊鎭?- 琛ヨ揣/閲囪喘浠撴帹鑽愬繀椤昏鏄庢帹鑽愮粨鏋滃拰鎺ㄨ崘鍘熷洜锛屼笉鑳藉彧鎶ヤ粨搴撳悕
- 寮哄埗鍒嗕粨蹇呴』瑕佹眰鐢ㄦ埛纭锛岃鏄庨闄?- 鎵€鏈夊啓鎿嶄綔鎵ц鍚庨兘瑕佽鏄庘€滅粨鏋滄剰鍛崇潃浠€涔堚€濆拰鈥滀笅涓€姝ユ€庝箞鍋氣€?- 寮傛缁撴灉涓嶈兘璇存弧锛涘鏋滃彧鏄彈鐞?澶勭悊涓紝蹇呴』鏄庣‘鍛婅瘔鐢ㄦ埛杩樻湭鏈€缁堢‘璁ゆ垚鍔?
## 鑴氭湰鍒楄〃

| 鑴氭湰 | 鍔熻兘 |
|------|------|
| `create_order.py` | 鎵嬪姩鍒涘缓閿€鍞鍗曪紙闇€ order creator 鏉冮檺锛?|
| `query_orders.py` | 鏌ヨ璁㈠崟鍒楄〃 |
| `get_order_detail.py` | 鑾峰彇璁㈠崟璇︽儏 |
| `get_hold_reason.py` | 鏌ヨ璁㈠崟绾?hold 鍘熷洜銆佸懡涓鍒欏拰鎵ц鏃ュ織 |
| `release_hold.py` | 閲婃斁 ON_HOLD 璁㈠崟 |
| `check_manual_allocation.py` | 妫€鏌ユ槸鍚﹀彲鎵嬪姩鍒嗛厤 |
| `get_allocation_items.py` | 鑾峰彇鍙垎閰嶅晢鍝佽 |
| `manual_allocate.py` | 鎻愪氦鎵嬪姩鍒嗛厤 |
| `suggest_purchase_order.py` | 鎺ㄨ崘琛ヨ揣鏂规 |
| `create_purchase_order.py` | 鍒涘缓琛ヨ揣閲囪喘鍗曪紙鍗曚粨锛?|
| `create_purchase_order_split.py` | 鍒涘缓琛ヨ揣閲囪喘鍗曪紙澶氫粨鎷嗗崟锛?|
| `get_routing_rules.py` | 璇诲彇璺敱瑙勫垯 |
| `reopen_order.py` | 閲嶆柊寮€鍚鍗?|
| `cancel_order.py` | 鍙栨秷璁㈠崟锛堟敮鎸佹壒閲忥級 |
| `batch_orders.py` | 鎵归噺 reopen / release hold |
| `oms_client.py` | 鍏变韩 auth + HTTP 瀹㈡埛绔?|

