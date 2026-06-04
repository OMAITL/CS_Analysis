# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

> For user-friendly release highlights, see the [GitHub Releases](https://github.com/ZhuLinsen/daily_stock_analysis/releases) page.

## [Unreleased]

- [文档] 重写 README、文档中心、CS 使用指南、FAQ、部署指南；股票长文档标注为遗留，默认文档路径改为 CS 饰品分析。
- [改进] CS 首页正式替换为 Agent 工作台 UI（左任务下发 / 右分析报告）；`/preview` 重定向至 `/`；组件见 `components/v2/cs/`。
- [改进] 饰品助手 v2 预览改为左右分栏：左侧任务下发、右侧分析报告；移除流水线动画；空报告区展示示例与最近分析。
- [改进] 饰品助手 v2 预览首页改为 Agent 工作台：左侧流水线/数据源/Skill，右侧任务下发；与问股聊天式预览区分。
- [新功能] 饰品投资助手 UI v2 预览：`/preview`（分层结果页 + 折叠历史卡片）、`/preview/chat`（ChatGPT 风格问股）；组件见 `apps/dsa-web/src/components/v2/cs/`，说明见 `docs/ui-v2-preview.md`；正式 `/` 与 `/chat` 未改动。
- [改进] CS 首页布局与股票分析页对齐：`lg:max-w-6xl` 居中容器、左侧历史栏、主内容 `max-w-4xl`，避免全屏过宽。
- [新功能] CS 首页搜索联想：`GET /api/v1/cs/items/search` 对接 CSQAQ `get_good_id`；多结果时须从下拉选择具体饰品再分析。
- [改进] CS 结果页移除 K 线量价图；完整 Markdown 报告改为默认折叠，标题改为「完整分析报告」。
- [改进] CS 饰品分析结果页对齐股票仪表盘：核心洞察、操作建议、趋势预测、板块联动（所属武器箱）、运行诊断、策略点位、资讯动态；API 新增结构化 `report` 字段。
- [修复] Web CS 分析请求超时由 120s 增至 300s，并区分「前端等待超时」与「上游依赖超时」提示。
- [修复] `CSItemService.analyze_item` 补全 `active_skills = normalize_cs_skill_ids(skills)`，修复 CS 分析 500（`name 'active_skills' is not defined`）。
- [改进] Web 首页改为 CS 饰品分析仪表盘（方案 A 默认）；原股票分析迁至 `/stocks`；`/cs` 重定向至首页。
- [改进] CS 饰品 skill 介入点与股票对齐：经 `GeminiAnalyzer.analyze()` 输出 JSON 决策仪表盘后再渲染 Markdown，不再仅在 `generate_text` 写报告阶段注入。
- [新功能] CS 饰品分析复用 13 个交易 skill：`skills` 请求参数、`GET /api/v1/cs/items/skills`、CS 适配 YAML 见 `strategies/cs/`。
- [改进] CS 事件情报：从 CSQAQ `container` 读取所属武器箱，新增「所属武器箱」搜索维度与「武器箱相关」分组；搜不到本品新闻属正常。
- [改进] CS 事件情报按饰品关键词打分：过滤 HLTV 纯战队八卦，优先「本品相关」与「市场要闻」分组展示；新增「本品聚焦」搜索维度。
- [改进] CS 事件情报：HLTV/Major 查询改为 `site:hltv.org`，按域名与 CS 关键词过滤无关结果（体育博彩、无关贴吧等）；优先 SerpAPI/Brave 执行站点搜索。
- [新功能] CS 饰品分析接入事件情报：分析时搜索官方 Blog、Major/贴纸、新箱、HLTV、贴吧（复用股票搜索 API），写入报告「事件与舆论影响」并在 Web `/cs` 展示快照列表。
- [改进] CS 饰品分析默认在每次查询前轻量重爬当天 K 线（`refresh_today`），历史日期仍读爬虫库；全量刷新仍用 `refresh_crawl`。
- [修复] CS Web/API 响应序列化加固（NaN/整数快照）；Vite 代理后端未启动时提示启动 `uvicorn` 而非笼统 500。
- [新功能] 新增 `tools/export_csqaq_volume.py` 与 `market_provider/csqaq/volume_export.py`，支持导出饰品指数日成交量和单个或批量饰品的每日成交量 CSV。
- [修复] CSQAQ K 线/成交量日期按 `Asia/Shanghai` 解析，修复相对网站整体偏移 1 天的问题。
- [新功能] Phase 2 数据融合：`ItemOhlcvBuilder` 合并开放 API 与爬虫 K 线，新增 `tools/build_cs_item_ohlcv.py`、`tools/analyze_cs_item.py`，结果写入 `CS_ANALYSIS_DB`。
- [新功能] Phase 2.3 CS 饰品 LLM Markdown 报告：`tools/report_cs_item.py`（LLM 不可用时降级模板）。
- [新功能] Web 端 CS 饰品分析页 `/cs`：`POST /api/v1/cs/items/analyze` + K 线图 / 技术面 / Markdown 报告展示。
<!-- 鏂版潯鐩牸寮忥細- [绫诲瀷] 鎻忚堪锛堢被鍨嬪彇鍊硷細鏂板姛鑳?鏀硅繘/淇/鏂囨。/娴嬭瘯/chore锛?->
<!-- 姣忔潯鐙珛涓€琛岃拷鍔犲埌鏈鏈熬锛屾棤闇€鍒嗙被鏍囬锛屽悎骞舵椂鍐茬獊鏈€灏?-->
- [鏂板姛鑳絔 鏂板 `market_provider/csqaq` Phase 1锛欳SQAQ 瀹㈡埛绔紙1 req/s 棰戞帶 + SQLite 缂撳瓨閽╁瓙锛夈€佸浘琛?鎸囨暟 K 绾?OHLCV 閫傞厤鍣ㄤ笌 `tools/test_cs_pipeline.py` 绔埌绔獙璇佽剼鏈€?- [chore] 绉婚櫎 `market_provider/steamdt` 鍙婄浉鍏宠剼鏈€佹枃妗ｄ笌鏍蜂緥鏁版嵁銆?- [鏀硅繘] CSQAQ 榛樿浠锋牸/鎴愪氦閲忓钩鍙版敼涓烘偁鎮犳湁鍝?(YYYP)锛屽彲閫氳繃 `CSQAQ_PRICE_PLATFORM` 瑕嗙洊锛坆uff/yyyp/steam锛夈€?- [淇] CSQAQ chart 鏃?K 鑱氬悎鏀逛负鍖椾含鏃堕棿鍒囨棩锛屽苟鎸夋椂闂村簭鍙?open/close锛涘湪鍞暟閲?volume 鏀逛负鏃ユ湯蹇収鑰岄潪鏃ュ唴绱姞銆?- [鏀硅繘] `scripts/fetch_tushare_stock_list.py` 鍙 A 鑲′腑甯?`XD`/`XR`/`DR`/`N`/`C` 鍓嶇紑鐨勫悕绉拌繘琛屽洖濉慨姝ｏ紝渚涜嚜鍔ㄨˉ鍏ㄥ埛鏂版祦绋嬮粯璁や娇鐢ㄣ€?- [淇] 鑲＄エ鑷姩琛ュ叏绱㈠紩鐢熸垚缂哄皯 `pypinyin` 鏃舵敼涓虹洿鎺ュけ璐ワ紝閬垮厤鍐欏嚭缂哄け鎷奸煶瀛楁鐨勯檷绾х储寮曘€?- [淇] 褰掍竴鑵捐瀹炴椂琛屾儏鎴愪氦閲忎负鑲″彛寰勶紝閬垮厤閲忚兘鍙樺寲鍊嶆暟琚斁澶у苟璇鍒嗘瀽鎶ュ憡銆?- [鏂囨。] 鏂板 #1391 Phase 0 杩愯璇婃柇濂戠害鏂囨。锛屾槑纭?trace_id銆佽瘖鏂憳瑕併€佸叧閿摼璺寖鍥翠笌鑴辨晱/fail-open/retention 杈圭晫銆?- [鏂板姛鑳絔 钀藉湴 #1391 Phase 1 杩愯璇婃柇鏈€灏忛摼璺細浠诲姟/SSE 杩藉姞 trace_id锛屽苟璁板綍鏃ョ嚎涓庡疄鏃惰鎯?ProviderRun 蹇収銆?- [鏀硅繘] Web 璺敱椤甸潰鏀逛负鎸夐渶鍔犺浇锛岄檷浣庨鍖呬綋绉苟澧炲姞璺敱鍔犺浇澶辫触鎭㈠鎻愮ず銆?- [淇] Docker 榛樿閮ㄧ讲绉婚櫎 `.env` 鍗曟枃浠舵寕杞斤紝閬垮厤 WebUI 淇濆瓨閰嶇疆鏃跺洜 `os.replace` 鏇存柊鎸傝浇鐐硅Е鍙?`Device or resource busy`銆?- [淇] 鏀舵暃 #1391 Phase 0 A 鑲′唬鐮佸綊灞炶竟鐣岋細琛ラ綈 `SH`/`SZ` 鍓嶇紑鍦烘櫙鐨勫綊灞炰竴鑷存€э紝鏄庣‘ `data_provider/baostock_fetcher.py`銆乣data_provider/pytdx_fetcher.py`銆乣data_provider/tushare_fetcher.py` 鐨勬湰杞慨澶嶈寖鍥淬€?- [鏀硅繘] Web 瀹屾暣鎶ュ憡 Markdown 鎶藉眽鏀逛负鎸夐渶鍔犺浇銆?- [鏀硅繘] 鏂板甯傚満闃舵鎺ㄦ柇鍩虹嚎骞舵槑纭洏鍓嶃€佺洏涓€佸崍浼戙€佷复杩戞敹鐩樸€佺洏鍚庡拰闈炰氦鏄撴棩璇箟銆?- [鏂板姛鑳絔 鍛婅涓績鏂板 P7 澶х洏绾㈢豢鐏粨鏋勫寲瑙勫垯锛屾敮鎸?`market_light_status` 涓?`market_light_score_drop` 骞跺鐢ㄧ幇鏈?worker銆佽Е鍙戝巻鍙层€侀€氱煡鍜屽喎鍗撮摼璺€?- [淇] 淇 `STOCK_LIST` 浣跨敤瑁?A 鑲′唬鐮佹椂 Baostock 绛夋暟鎹簮 fallback 鐨勫唴閮ㄦ牸寮忚浆鎹紝淇濇寔鐢ㄦ埛閰嶇疆缁х画浣跨敤 6 浣嶈偂绁ㄧ紪鍙枫€?- [鏂囨。] 琛ラ綈鍛婅涓績 P8 鏂囨。涓庨厤缃敹鍙ｈ鏄庯紝鏄庣‘ legacy JSON銆侀珮绾ц鍒欍€乄eb/API銆丏ocker銆丟itHub Actions 涓?Desktop 杈圭晫銆?- [淇] Windows 妗岄潰绔嚜鍔ㄦ洿鏂板湪鐢ㄦ埛纭閲嶅惎瀹夎鍚庢敼涓洪潤榛樻墽琛屽畨瑁呭櫒锛屽苟鍦ㄥ仠姝㈠唴缃悗绔悗娓呯悊杩涚▼寮曠敤锛岄檷浣庡畨瑁呭櫒鎻愮ず鈥滄瘡鏃ヨ偂绁ㄥ垎鏋愭棤娉曞叧闂€濈殑姒傜巼銆?- [鏂囨。] 璇存槑鏈妗岄潰淇浠呰鐩?Windows NSIS 鏇存柊瀹夎閾捐矾涓庡悗绔繘绋嬬敓鍛藉懆鏈熸竻鐞嗭紱鏈敼鍔ㄨ缃」淇濆瓨/妯″瀷杩愯鏃舵竻鐞嗚涔夈€傜Щ闄ゆ鍓嶈鍏ョ殑 `docker/Dockerfile` `npm registry` 鍙樻洿锛屾仮澶嶉儴缃叉瀯寤轰笌鏇存柊淇鐨勮亴璐ｉ殧绂汇€?- [淇] macOS 妗岄潰绔皢杩愯鏃堕厤缃縼绉诲埌鐢ㄦ埛鏁版嵁鐩綍锛屽苟鍦ㄦ棫 `.app` 鍖呭唴鏂囦欢浠嶅彲璁块棶鏃惰縼绉?`.env`銆佹暟鎹簱鍜屾棩蹇楋紝閬垮厤鍚庣画鏇挎崲鍗囩骇鍚庨噸鏂伴厤缃€?- [鏀硅繘] 鏂板杩愯鎬佸競鍦洪樁娈典笂涓嬫枃鏋勯€犱笌闄嶇骇娴嬭瘯銆?- [鏂囨。] 鏂板 AnalysisContextPack P0 涓婁笅鏂囩洏鐐癸紝鏄庣‘瀛楁璐ㄩ噺鐘舵€併€佺幇鏈夌姸鎬佹槧灏勫拰棣栫増 pack 杈圭晫銆?- [鏂板姛鑳絔 钀藉湴 #1391 Phase 2 杩愯璇婃柇鎽樿锛氱敓鎴愮敤鎴峰彲璇?RunDiagnosticSummary锛屾彁渚涘巻鍙叉姤鍛婅瘖鏂?API 涓庤劚鏁忓鍒舵枃鏈€?- [鏂囨。] 鏄庣‘ #1391 Phase 2 鐨勭粨鏋勫寲妫€娴嬪憡璀︿负闈為厤缃縼绉讳俊鍙凤細`agent_max_steps`/`agent_orchestrator_timeout_s` 闈炴硶鍊间細 fallback 鑷抽粯璁ゅ苟浜х敓鏃ュ織鍛婅锛屾柊澧炶瘖鏂摼璺粎鏂板 `context_snapshot`/`RunDiagnosticSummary` 璇诲啓瀛楁锛屼笉鏀瑰啓 `litellm_model`銆乣agent_litellm_model`銆乣openai_base_url`銆丩LM channel 璺敱鎴栭厤缃縼绉昏涔夈€?- [鏂板姛鑳絔 钀藉湴 #1391 Phase 3 杩愯璇婃柇鍙鎬э細鎶ュ憡璇︽儏鍜屼换鍔￠潰鏉块粯璁ゆ姌鍙犲睍绀鸿繍琛岀姸鎬併€乼race 涓庡彲澶嶅埗鎺掗殰淇℃伅锛涘悗绔€氳繃 `api/v1/history/{record_id}/diagnostics` 涓?`context_snapshot.diagnostics` 鎻愪緵鍘嗗彶閾捐矾鍥炲～銆?- [鏂囨。] 琛ュ厖 #1391 Phase 3 鍏煎鎬ц鏄庯細璁板綍鍚庣璇婃柇鎸佷箙鍖栥€佸巻鍙叉煡璇笌閫氱煡鍥炲啓閾捐矾鍙樻洿杈圭晫涓庡洖婊氱瓥鐣ワ紝骞惰ˉ榻愬悗绔棬绂佺骇楠岃瘉瑕佹眰銆?- [娴嬭瘯] 鏀舵暃 #1391 Phase 3 鍚庣/API 涓?Web 鍥炲綊妫€鏌ワ細`./scripts/ci_gate.sh`銆乣test_pipeline_market_phase_context.py`銆乣test_analysis_api_contract.py`銆乣test_analysis_history.py`銆乣npm run lint`銆乣npm run build`銆?- [鏂板姛鑳絔 鏂板 AnalysisContextPack P1 鍐呴儴濂戠害涓庤劚鏁忓簭鍒楀寲娴嬭瘯銆?- [淇] 鎭㈠ Agent/鍘嗗彶鍏煎蹇収涓殑鍏宠仈鏉垮潡涓庢澘鍧楄仈鍔ㄥ瓧娈垫彁鍙栵紝淇鏂扮増棣栭〉鎶ュ憡缂哄皯鈥滄澘鍧楄仈鍔ㄢ€濈殑鍥炲綊闂銆?- [鏀硅繘] 璁剧疆椤甸厤缃府鍔╅樁娈垫€цˉ榻?Web 璁剧疆椤靛疄闄呭睍绀?鍙厤缃瓧娈电殑涓嫳鍙岃鏂囨锛岃鐩?Agent銆佸洖娴嬨€佹姤鍛娿€侀€氱煡璺敱銆佺郴缁熻繍琛屾椂銆丄I legacy銆佹暟鎹簮鍜岄€氱煡楂樼骇閰嶇疆銆?- [淇] 淇 Web 璁剧疆甯姪涓?legacy 鍛婅 JSON 瀛楁鍚嶄笌闈欓粯鏃舵鎶曢€掕涔夎鏄庛€?- [淇] 淇 Web 涓枃璁剧疆椤靛湪鏁版嵁婧愩€侀€氱煡銆佺郴缁熶笌 Agent 鍖哄煙鐨勯厤缃爣棰樸€佽鏄庡拰鍏抽敭涓嬫媺閫夐」婕忕炕闂銆?- [淇] 淇闂偂浼氳瘽鍒囨崲鍜岄椤典换鍔￠噸杩炲悗鍙兘娈嬬暀 Agent/鍒嗘瀽浠诲姟杩涜涓姸鎬佺殑闂銆?- [鏂板姛鑳絔 闂偂鏂板榛樿鍏抽棴鐨勫彲瑙佸璇濅笂涓嬫枃鍘嬬缉锛屾敮鎸?Web 寮€鍏炽€丄gent 楂樼骇 preset銆佹粴鍔ㄦ憳瑕佸拰鏈€杩戣疆娆″師鏂囦繚鎶わ紝闄嶄綆闀夸細璇?token 娑堣€椼€?- [鏀硅繘] P2-min锛歀LM Prompt 娉ㄥ叆甯傚満闃舵涓婁笅鏂囥€?
## [3.18.0] - 2026-05-21

### 鍙戝竷浜偣

- feat: 鍛婅涓績鎵╁睍鍒?P2-P6锛岃ˉ榻愬悗鍙拌瘎浼般€佺湡瀹為€氱煡缁撴灉銆佷笟鍔″喎鍗淬€佹妧鏈寚鏍囪鍒欙紝浠ュ強鑷€夎偂 / 鎸佷粨 / 璐︽埛鑱斿姩瑙勫垯銆?- feat: 涓偂鍒嗘瀽鏀寔绛栫暐閫夋嫨锛屾柊澧炵儹鐐归鏉愩€佷簨浠堕┍鍔ㄣ€佹垚闀胯川閲忓拰棰勬湡閲嶄及绛栫暐锛屽苟涓?HK/US 鎶ュ憡琛ュ厖鍩烘湰闈€佽储鍔℃憳瑕併€佽偂涓滃洖鎶ュ拰鍏宠仈鏉垮潡銆?- feat: 鏂板 Finnhub / AlphaVantage 缇庤偂鏁版嵁婧愰€傞厤鍣紝鎵╁睍缇庤偂鏃ョ嚎 failover 閾撅紝鎻愬崌缇庤偂琛屾儏鑾峰彇闊ф€с€?- fix: 淇妗岄潰绔彂甯冩墦鍖呫€佸垎鏋愮姸鎬佹帴鍙ｃ€丄lphaVantage 娑ㄨ穼骞呫€佹寔浠撳疄鏃朵及鍊笺€佸憡璀﹀巻鍙插幓閲嶃€佹暟鎹簱鍐峰惎鍔ㄥ拰 fallback pricing 娉ㄥ唽绛夌ǔ瀹氭€ч棶棰樸€?
### What's Changed

- feat: Add alert-center P2-P6, Web strategy selection, HK/US fundamental context, static-report financial sections, and Finnhub / AlphaVantage US-market fallback.
- improve: Refine LiteLLM parameter recovery, yfinance currency/dividend handling, RSI calculation, market-review presentation, stock-news relevance ranking, and report table rendering.
- fix: Harden desktop packaging/update assets, completed analysis-status responses, AlphaVantage pct_chg routing, portfolio realtime snapshots, alert trigger dedupe, DatabaseManager cold start, and fallback pricing registration.
- docs/tests: Add beginner setup and settings-help docs, document compatibility/rollback boundaries, and extend regression coverage for API, alert, packaging, and release paths.

## [3.17.1] - 2026-05-16

### 鍙戝竷浜偣

- fix: 妗岄潰绔?Windows / macOS 鎵撳寘鑴氭湰鏄惧紡鍏抽棴 electron-builder 鑷姩鍙戝竷锛岄伩鍏?tag 鏋勫缓鏃跺洜缂哄皯 `GH_TOKEN` 鍦ㄦ湰鍦版墦鍖呭畬鎴愬悗澶辫触锛汻elease workflow 缁х画璐熻矗涓婁紶鍜屽彂甯冧骇鐗┿€?
### What's Changed

- fix: Add `--publish never` to the Windows and macOS Electron packaging scripts so tag builds only create local artifacts and GitHub Actions handles release upload/publish.

## [3.17.0] - 2026-05-16

### 鍙戝竷浜偣

- feat: 鏂板 Alert API MVP锛屾敮鎸佸憡璀﹁鍒?CRUD銆佸惎鍋溿€佷竴娆℃€ф祴璇曚互鍙婅Е鍙?閫氱煡缁撴灉鏌ヨ锛岄鐗堣鐩?`price_cross` / `price_change_percent` / `volume_spike` 骞朵繚鎸?legacy 閰嶇疆鍏煎銆?- feat: 閫氱煡缃戝叧鏂板 ntfy 涓?Gotify 涓€绛夋笭閬擄紝骞惰ˉ榻愰€氱煡闄嶅櫔銆侀潤鎬佹笭閬撻殧绂汇€佽瘖鏂€乄eb 娴嬭瘯鍜?GitHub Actions env 瀵圭収鏍￠獙銆?- feat: Windows 妗岄潰瀹夎鐗堟帴鍏ヨ嚜鍔ㄦ洿鏂板畨瑁呴摼璺紝鏀寔鍚庡彴涓嬭浇銆佺‘璁ら噸鍚畨瑁呫€佽繍琛屾椂鏂囦欢澶囦唤/鎭㈠鍜屽彂甯冧骇鐗╁厓鏁版嵁鏍￠獙銆?- improve: 澶х洏澶嶇洏鏂板姒傚康鎺掕銆佷汉姘旇偂銆佹定鍋滄睜绛夊簳灞傛暟鎹簮锛屾敮鎸佹寚鏁版定璺岄鑹茶涔夐厤缃紝骞跺皢澶嶇洏缁撴灉鍐欏叆鍘嗗彶璁板綍銆?- improve: Web 璁剧疆椤垫敮鎸?`.env` 閰嶇疆澶囦唤瀵煎叆/瀵煎嚭鍜岄€氱煡/Agent 鍖哄煙灞€閮ㄩ敊璇厹搴曪紱鎶ュ憡鏂板 `REPORT_SHOW_LLM_MODEL` 寮€鍏虫帶鍒舵ā鍨嬩俊鎭睍绀恒€?- improve: Docker 鍚姩鍏ュ彛鑷姩淇鎸傝浇鐩綍鏉冮檺骞跺湪鏃ュ織鐩綍涓嶅彲鍐欐椂闄嶇骇鍒版帶鍒跺彴锛屽噺灏戞櫘閫氶儴缃茬殑鎵嬪姩淇姝ラ銆?- fix: 鏁版嵁婧愮己鍑嵁鎴栬繛鎺ュけ璐ユ椂鏇存俯鍜岄檷绾э紝Longbridge / Pytdx 鍔犲叆鍐峰嵈锛岃祫閲戞祦缂哄け鏃堕伩鍏嶈緭鍑洪珮缃俊涔板叆缁撹銆?- fix: 鍒嗘瀽涓庢姤鍛婇摼璺吋瀹?OpenAI-compatible `content_blocks` 鍝嶅簲锛屽綊涓€绛栫暐浠锋牸瀛楁锛屽苟淇澶х洏澶嶇洏婊氬姩鍜屽巻鍙茶褰曚涪澶遍棶棰樸€?- docs: 琛ラ綈閫氱煡銆佸憡璀︿腑蹇冦€佹闈㈡墦鍖呫€丷EADME / 鎸囧崡鍜?PR title 娌荤悊璇存槑锛屾槑纭澶勯厤缃吋瀹硅竟鐣屼笌鍥炴粴璺緞銆?- test: 澧炲姞 Alert API銆侀€氱煡闄嶅櫔/璺敱銆丏ocker entrypoint銆佹暟鎹簮棰勫彇銆佹闈㈡洿鏂伴摼璺拰鍒嗘瀽鍘嗗彶绛夊洖褰掕鐩栥€?
### What's Changed

- feat: Add an Alert API MVP with rule CRUD, enable/disable, one-shot testing, trigger history, notification results, and legacy config compatibility.
- feat: Promote ntfy and Gotify to first-class notification channels with Web tests, routing, Actions integration, diagnostics, and noise control.
- feat: Add the Windows desktop auto-update install flow with runtime state backup/restore and release artifact metadata verification.
- improve: Extend market review data sources, add configurable index color semantics, and persist market review results into analysis history.
- improve: Add Web `.env` backup import/export, local settings panel error boundaries, and a report model visibility toggle.
- improve: Harden Docker startup by repairing mounted directory permissions and falling back to console logging when mounted logs are not writable.
- fix: Cool down unavailable optional fetchers, reduce noisy Longbridge/Pytdx retries, and downgrade buy advice when capital flow data is missing.
- fix: Handle OpenAI-compatible `content_blocks`, normalize strategy price fields, and recover market review scrolling/history behavior.
- docs/tests: Update notification, alert, desktop packaging, README/guide, and governance docs; add focused regression coverage for the new release paths.

## [3.16.0] - 2026-05-10

### 鍙戝竷浜偣

- feat: Web 棣栭〉鏂板鈥滃ぇ鐩樺鐩樷€濊Е鍙戝叆鍙ｃ€佷换鍔¤疆璇笌瀹屾垚鍚庢姤鍛婄洿鍑猴紱棣栨鍚姩閰嶇疆鐘舵€佸彲鎻愮ず缂哄彛骞跺紩瀵煎埌绯荤粺璁剧疆銆?- feat: 鏂板閫氱煡璺敱绛栫暐锛屾敮鎸佹寜 report銆乤lert銆乻ystem_error 灏嗛€氱煡鏀剁獎鍒版寚瀹氭笭閬擄紱Web 璁剧疆椤垫敮鎸侀€氱煡娓犻亾涓€閿祴璇曘€?- feat: 绯荤粺璁剧疆椤垫柊澧為厤缃」甯姪鍏ュ彛涓庡璇█甯姪鏂囨鍩虹璁炬柦锛岄鎵硅鐩栬嚜閫夎偂銆丩LM 涓绘ā鍨嬨€丩LM 娓犻亾銆侀涔?Webhook 涓?WebUI 鐩戝惉鍦板潃銆?- improve: 澶х洏澶嶇洏 API銆丆LI銆丅ot 鍏辩敤 `build_market_review_runtime` 瑁呴厤璺緞锛岃ˉ榻?`litellm_model` / `llm_model_list` 涓?legacy key 鍥為€€璇存槑銆?- improve: 涓偂鎶ュ憡鎿嶄綔寤鸿缁撳悎鏀拺/鍘嬪姏銆侀噺鑳姐€佺鐮佷笌涓诲姏璧勯噾娴佹牎鍑嗭紝鍑忓皯涔板叆/鍗栧嚭鍓х儓鍒囨崲锛屽苟琛ュ己 Agent 鍐崇瓥鍏滃簳銆?- improve: Docker 闀滃儚鏀寔闈?root 鐢ㄦ埛杩愯锛孡iteLLM 渚濊禆绾︽潫鏀惧鍒板悗缁畨鍏?1.x 淇鐗堟湰銆?- fix: 淇 LLM 娓犻亾娴嬭瘯涓?`Model disabled`銆乸rovider blocked 绛夐敊璇垎绫伙紝閬垮厤琚鎶ヤ负缃戠粶寮傚父銆?- fix: 娓偂鏃ョ嚎璺宠繃涓嶆敮鎸佹腐鑲＄殑鍐呯疆鍘嗗彶鏁版嵁婧愶紱鍖椾氦鎵€ `BJ` 鍓嶇紑涓?`.BJ` 鍚庣紑浠ｇ爜鏍￠獙淇濇寔涓€鑷淬€?- fix: Web 澶х洏澶嶇洏鎸夐挳鍙娴嬫€с€乄indows fallback 閿佽繘绋嬫帰娴嬪拰鍌寲绾跨储灞曠ず鏇寸ǔ鍋ャ€?- docs: 鏂板鏂囨。涓績涓庨厤缃府鍔╃淮鎶よ鏄庯紝娓呯悊 README銆佸畬鏁存寚鍗椾笌閰嶇疆鎸囧崡涓殑涓存椂 PR/鏂囨。鍚屾璇存槑銆?
### What's Changed

- feat: Add a Web home market-review trigger with task polling and inline report display; setup status now points users to missing configuration.
- feat: Add notification routing by report, alert, and system_error; add one-click notification channel testing in Web settings.
- feat: Add settings field help infrastructure with multilingual help text for the first batch of core configuration fields.
- improve: Share `build_market_review_runtime` across API, CLI, and Bot market review paths; document `litellm_model` / `llm_model_list` and legacy key fallback behavior.
- improve: Calibrate stock advice with support/resistance, volume, chips, and main-force capital flow; strengthen Agent decision fallback behavior.
- improve: Run Docker images as a non-root user and relax LiteLLM constraints to allow safe future 1.x fixes.
- fix: Classify `Model disabled`, provider blocked, and related LLM channel test errors more accurately instead of reporting them as generic network failures.
- fix: Avoid unsupported built-in historical providers for Hong Kong daily data; align Beijing Stock Exchange `BJ` prefix and `.BJ` suffix validation.
- fix: Improve Web market-review observability, Windows fallback lock probing, and market catalyst snippet rendering.
- docs: Add the documentation index and settings-help maintenance guide; remove temporary PR/doc-sync notes from README and user-facing guides.

## [3.15.0] - 2026-05-05

### 鍙戝竷浜偣

- LLM 娓犻亾閰嶇疆浣撻獙缁х画鍗囩骇锛氭柊澧?Anspire OpenAI-compatible 缃戝叧鎺ュ叆锛屽苟琛ラ綈甯哥敤鏈嶅姟鍟嗛璁俱€佸畼鏂规潵婧愩€佽兘鍔涙爣绛俱€侀厤缃敞鎰忎簨椤瑰拰 GitHub Actions 鏄惧紡鏄犲皠銆?- Web LLM 閰嶇疆妫€娴嬫洿鍙瘖鏂細缁嗗垎閿欒 reason锛屽苟鏀寔鐢ㄦ埛鏄惧紡瑙﹀彂 JSON銆乼ools銆乿ision銆乻tream 杩愯鏃?smoke銆?- LLM 杩愯鏃堕厤缃竻鐞嗘洿绋冲仴锛氬彧娓呯悊鎵樼 provider 鐨勫け鏁堣繍琛屾椂閫夋嫨锛屽苟淇濈暀 `cohere/*`銆乣google/*`銆乣xai/*` 绛夌洿杩?provider 鍏煎璇箟銆?- 閫氱煡涓?Bot 鐘舵€佸彲瑙傛祴鎬у寮猴細鑷畾涔?Webhook 鏀寔 JSON body 妯℃澘锛孊ot `/status` 灞曠ず鏇村畬鏁寸殑 LLM銆丄gent 涓庨€氱煡娓犻亾鐘舵€併€?- 澶х洏澶嶇洏銆佸疄鏃跺憡璀︺€丄gent weak 鍏滃簳鍜屾寔浠撲及鍊肩户缁ˉ寮猴紝闄嶄綆榛樿鍊艰鐩栥€佺己浠锋薄鏌撳拰閰嶇疆鎺掗殰鎴愭湰銆?
### 鏂板姛鑳?
- 鏀寔 `ANSPIRE_API_KEYS` 榛樿鎺ュ叆 Anspire OpenAI-compatible 澶фā鍨嬬綉鍏筹紝骞跺湪 LLM 娓犻亾缂栬緫鍣ㄨˉ鍏?Anspire Open 棰勮銆?- 鑷畾涔?Webhook 鏀寔 `CUSTOM_WEBHOOK_BODY_TEMPLATE` JSON body 妯℃澘锛屼究浜庨€傞厤 AstrBot銆丯apCat 鍜岃嚜寤烘帹閫佹湇鍔°€?- 澶х洏澶嶇洏缁撴瀯鍖栧尯鍧楁柊澧炲ぇ鐩樼孩缁跨伅缁撹锛屽熀浜庣洏闈㈡俯搴﹁緭鍑?green/yellow/red銆佹牳蹇冨師鍥犲拰鎿嶄綔寤鸿銆?- EventMonitor 鏀寔 `price_change_percent` 娑ㄨ穼骞呴槇鍊艰鍒欙紝鍙寜涓婃定鎴栦笅璺屾柟鍚戣Е鍙戝疄鏃跺憡璀︺€?- Web LLM 娓犻亾缂栬緫鍣ㄦ柊澧炲父鐢ㄦ湇鍔″晢閰嶇疆妯℃澘涓庨璁撅紝瑕嗙洊 MiniMax銆佺伀灞辨柟鑸熴€丱penAI銆丆laude銆丟emini銆並imi銆丵wen銆丟LM銆佽眴鍖呯瓑鍏ュ彛銆?
### 鏀硅繘

- Web LLM 閰嶇疆妫€娴嬭ˉ鍏呯粏鍒嗛敊璇垎绫伙紝骞舵柊澧炴樉寮忚Е鍙戠殑 JSON/tools/vision/stream 杩愯鏃?smoke锛涢粯璁ゆ祴璇曞拰淇濆瓨娴佺▼涓嶅彉锛屾娴嬬粨鏋滀粎浣滀负褰撳墠閰嶇疆鐨勪竴娆?best-effort 璇婃柇銆?- Bot `/status` 灞曠ず缁熶竴 LLM 涓绘ā鍨嬨€丄gent 妯″瀷銆佹笭閬撴ā寮忋€乊AML 閰嶇疆鍜屾洿澶氶€氱煡娓犻亾鐘舵€併€?- Web LLM 娓犻亾缂栬緫鍣ㄥ睍绀?provider 鑳藉姏鏍囩銆佸畼鏂规潵婧愰摼鎺ュ拰閰嶇疆娉ㄦ剰浜嬮」鎻愮ず锛涜繖浜涙爣绛句粎鐢ㄤ簬閰嶇疆鍙傝€冿紝涓嶄唬琛ㄨ繍琛屾椂鑳藉姏宸查獙璇侀€氳繃銆?- 鎶藉嚭 Web LLM provider preset 鍗曚竴妯℃澘鏁版嵁婧愶紝淇濇寔鐜版湁閰嶇疆淇濆瓨璇箟涓嶅彉銆?- 琛ラ綈 LLM provider channel 鍦?GitHub Actions 涓殑鏄惧紡鏄犲皠锛屽苟鍚屾 `.env` 绀轰緥涓庨厤缃枃妗ｃ€?
### 淇

- Agent weak 瀹屾暣鎬у厹搴曞湪妯″瀷缂哄皯璇勫垎銆佽秼鍔裤€佹搷浣滃缓璁垨 dashboard 鍏抽敭鍧楁椂浼樺厛淇濈暀鏈湴瓒嬪娍鍒嗘瀽缁撴灉锛屽苟鍙ˉ榻愮湡姝ｇ己澶辩殑浠〃鐩樺瓧娈碉紝閬垮厤棣栭〉璇勫垎琚粯璁?50 瑕嗙洊銆?- 缁熶竴鎸佷粨蹇収杈撳嚭鐜颁环銆佸競鍊笺€佹诞鐩堜簭銆佹敹鐩婄巼涓庝环鏍煎厓淇℃伅锛岄伩鍏嶇己浠锋垨 stale 浠锋牸姹℃煋鎸佷粨浼板€笺€?- LLM 娓犻亾娴嬭瘯琛ュ厖缁撴瀯鍖栬瘖鏂笌璁剧疆椤垫帓闅滄彁绀猴紝渚夸簬瀹氫綅 provider銆佹ā鍨嬨€丅ase URL 鍜岄壌鏉冮厤缃棶棰樸€?- 鏄庣‘ runtime 娓呯悊鍏煎杈圭晫锛氫粎瀵规墭绠?provider锛坄gemini`銆乣vertex_ai`銆乣anthropic`銆乣openai`銆乣deepseek`锛夎Е鍙戜繚瀛樺墠澶辨晥鍊兼竻鐞嗭紝`cohere/*`銆乣google/*`銆乣xai/*` 鐩磋繛鍊兼寜 legacy 鍏煎璺緞淇濈暀锛屼笉鍋氭棤鎻愮ず杩佺Щ鎴栬鍐欍€?- 灏?MiniMax 棰勮璋冩暣涓哄畼鏂?OpenAI-compatible Base URL 鍜屽綋鍓嶆ā鍨嬬ず渚嬶紝骞惰ˉ鍏?MiniMax銆佺伀灞辨柟鑸熴€丩iteLLM 鍏煎鏉ユ簮涓庡洖閫€璇存槑銆?- 绉婚櫎鎴浘璇嗗埆瀵?Gemini 3 Vision 妯″瀷鐨勮繃鏃堕檷绾ч€昏緫锛岄粯璁ゆ帹鏂敼鐢ㄥ綋鍓?Gemini 妯″瀷閰嶇疆銆?
### 鏂囨。

- 瀹屽杽 LLM provider 閰嶇疆鏂囨。锛岃ˉ鍏呴厤缃柟寮忛€夋嫨銆丄ctions 鍙橀噺瀵圭収銆佽繍琛屾椂妫€娴嬭竟鐣屻€侀敊璇?reason 鎺掗殰鍜屽洖婊氳矾寰勶紙#1180锛夈€?- 琛ュ厖 LLM 娓犻亾缂栬緫鍣ㄧ殑瀹樻柟鏉ユ簮銆佷緷璧栧吋瀹圭獥鍙ｃ€佷繚瀛樻椂鐨勮繍琛屾椂妯″瀷娓呯悊瑙勫垯锛屼互鍙婃棫閰嶇疆鍥為€€璺緞璇存槑銆?- 涓?`cohere/*`銆乣google/*`銆乣xai/*` 鐩磋繛璇箟琛ュ厖瀹樻柟 provider/model 璇存槑銆乣litellm>=1.80.10,<1.82.7` 鍏煎渚濇嵁寮曠敤锛屽苟鏄庣‘绀轰緥妯″瀷鍚嶄粎涓洪厤缃繚鐣欒涓鸿鏄庤€岄潪鍙敤鎬ц儗涔︺€?- 鏄庣‘ `price_change_percent` 浜嬩欢鍛婅浠呬负閰嶇疆涓庤繍琛屾椂瑙勫垯鎵╁睍锛屾湭鍙樻洿妯″瀷/provider/base URL/LiteLLM 鍏煎璇箟锛涘洖閫€璺緞涓哄叧闂?绉婚櫎 Event Monitor 閰嶇疆銆?- 鍚屾 README銆丏EPLOY銆乫ull-guide銆丄nspire銆丄IHubMix 涓?SerpAPI 鐩稿叧璇存槑锛岀粺涓€澶栭摼銆侀厤缃彛寰勫拰璇勫涓€鑷存€ц鏄庛€?
### 娴嬭瘯

- 琛ラ綈 AI 閰嶇疆椤典笌 `task_queue` 鐨?LLM 杩愯鏃舵竻鐞?鍚屾鍥炲綊璇佹嵁锛氭仮澶嶆笭閬撴ā鍨嬫椂淇濈暀 fallback銆佺紪杈戞ā鍨嬪垪琛ㄦ湡闂翠笉闈欓粯娓呯┖杩愯鏃堕€夋嫨锛屾笭閬撴棤鍙敤妯″瀷鏃舵竻鐞嗗け鏁?runtime 寮曠敤锛屽苟瑕嗙洊 legacy key 涓?`cohere/*`銆乣google/*`銆乣xai/*` 鐩磋繛 provider 淇濈暀璇箟銆?- 瑕嗙洊 Web LLM 閰嶇疆妫€娴嬬殑缁嗗垎閿欒鍒嗙被锛屼互鍙?JSON銆乼ools銆乿ision銆乻tream 杩愯鏃?smoke 鐨勬樉寮忚Е鍙戣矾寰勩€?
## [3.14.2] - 2026-04-30

### 鍙戝竷浜偣

- 澶х洏澶嶇洏鎵╁睍鍒版腐鑲★紝骞惰 Bot `/market` 涓?CLI/璋冨害鍏ュ彛浣跨敤涓€鑷寸殑浜ゆ槗鏃ヨ繃婊よ涔夈€?- 闂偂涓?Agent 閾捐矾澧炲己閰嶇疆缂哄け銆佸喅绛?fallback 鍜屽绛栫暐閫夋嫨浣撻獙銆?- LLM 涓庡垎鏋愭姤鍛婇摼璺彁鍗囩ǔ瀹氭€э細闈炴硶 JSON 鍝嶅簲浼氱户缁皾璇曞鐢ㄦā鍨嬶紝LiteLLM DEBUG 鏃ュ織榛樿闄嶅櫔銆?- 鏂板鍙棣栨鍚姩閰嶇疆鐘舵€佹帴鍙ｏ紝涓哄悗缁厤缃悜瀵煎拰 smoke run 濂犲畾鍩虹銆?
### 鏂板姛鑳?
- 澶х洏澶嶇洏鏀寔娓偂甯傚満锛歚MARKET_REVIEW_REGION` 鏂板 `hk` 閫夐」锛沗both` 鎵╁睍涓?A鑲?娓偂+缇庤偂锛屽苟鏂板娓偂鎸囨暟锛圚SI/HSTECH/HSCEI锛夊鐩橀摼璺€?- 鏂板鍙棣栨鍚姩閰嶇疆鐘舵€佹帴鍙?`GET /api/v1/system/config/setup/status`锛岀敤浜庤瘑鍒?LLM銆丄gent銆佽嚜閫夎偂銆侀€氱煡鍜屾湰鍦板瓨鍌ㄩ厤缃己鍙ｏ紱璇ユ帴鍙ｄ笉浼氶噸杞借繍琛屾椂銆佸啓鍏?`.env` 鎴栧垱寤烘暟鎹簱鏂囦欢銆?
### 鏀硅繘

- 闂偂椤甸潰鏀寔缁勫悎閫夋嫨澶氫釜 Agent 绛栫暐銆?
### 淇

- Bot `/market` 鍛戒护澶嶇敤 `get_open_markets_today()` / `compute_effective_region()` 鍋氫氦鏄撴棩杩囨护锛氱粨鏋滀綔涓?`override_region` 閫忎紶缁?`run_market_review`锛涜嫢缁撴灉涓虹┖瀛楃涓插垯璺宠繃澶嶇洏骞舵帹閫佲€滀粖鏃ョ浉鍏冲競鍦轰紤甯傗€濓紝涓?CLI/璋冨害鍏ュ彛琛屼负涓€鑷淬€?- 闂偂 Agent 鍦ㄦ湭閰嶇疆鍙敤 LLM 鏃朵繚鐣欏悗绔湡瀹為敊璇師鍥犲苟缁存寔 `done.success=false` 澶辫触璇箟锛岄伩鍏嶅墠绔妸閰嶇疆缂哄け璇綋鎴愭垚鍔熷洖绛斻€?- Agent 妯″紡鏈敓鎴愭湁鏁堝喅绛栦华琛ㄧ洏鏃朵繚鐣欐湰鍦拌秼鍔垮垎鏋愮殑璇勫垎銆佽秼鍔垮拰鎿嶄綔寤鸿锛屽苟灏嗗己涔?寮哄崠 fallback 褰掍竴鍒板吋瀹圭殑 `buy`/`sell` 鍐崇瓥绫诲瀷锛岄伩鍏嶉椤电粨鏋滆 `50 / 瑙傛湜 / 鏈煡` 缂虹渷鍊艰鐩栥€?- 鎸佷粨蹇収鐜颁环缂哄け鏃朵笉鍐嶉潤榛樺洖閫€涓烘寔浠撴垚鏈紱褰撳ぉ蹇収浼樺厛浣跨敤鍘嗗彶鏀剁洏浠凤紝浠呭湪缂哄け鏃朵娇鐢ㄥ疄鏃朵环 fallback锛岀己浠锋寔浠撲笉鍐嶆薄鏌撳競鍊间笌鏈疄鐜扮泩浜忔眹鎬伙紝骞朵负鎸佷粨鏄庣粏杩斿洖浠锋牸鏉ユ簮銆佹棩鏈熴€乻tale 涓庣己浠风姸鎬併€?- 鍒嗘瀽 Prompt 鍦ㄦ敞鍏?`trend_analysis` 鍓嶆寜鏈€缁?`trend_status` / `ma_alignment` 娓呮礂浜掓枼鐞嗙敱锛氱┖澶寸粨鏋勭Щ闄ょ湅澶氱悊鐢便€佸澶寸粨鏋勭Щ闄ょ┖澶寸粨鏋勯闄╋紝骞跺湪浜嬩欢/鎶€鏈啿绐佷笌寮傚父鏀鹃噺锛?10 鍊嶏級鏃跺己鍒舵彁绀衡€滀簨浠跺厛琛屻€佹妧鏈緟纭鈥濅笌閲忚兘闄嶆潈銆?- LLM 杩斿洖闈?JSON 鍝嶅簲鏃跺悓鏍疯Е鍙戝鐢ㄦā鍨嬪垏鎹細涓绘ā鍨嬫垚鍔熻繑鍥炰絾鏃犳硶瑙ｆ瀽 JSON 鏃讹紝涓嶅啀绔嬪嵆闄嶇骇涓虹函鏂囨湰 fallback锛岃€屾槸渚濇灏濊瘯 `LITELLM_FALLBACK_MODELS` 涓殑澶囩敤妯″瀷锛涙墍鏈夋ā鍨嬪潎鏃犳硶杩斿洖鍚堟硶 JSON 鏃讹紝鍐嶉檷绾т负鏂囨湰 fallback銆?- LiteLLM 鍐呴儴 DEBUG 鏃ュ織榛樿鍘嬩綆鍒?WARNING锛岄伩鍏嶆祦寮忕敓鎴愭椂 token 绾ф棩蹇楁薄鏌?`stock_analysis_debug_*.log`锛涘闇€鎺掓煡 LiteLLM 鍐呴儴缁嗚妭锛屽彲涓存椂璁剧疆 `LITELLM_LOG_LEVEL=DEBUG`锛團ixes #1156锛夈€?
### 鏂囨。

- 琛ュ厖 LLM 閰嶇疆鎸囧崡涓?FAQ锛屾槑纭棶鑲?Agent 瀵?`LITELLM_CONFIG` / `LLM_CHANNELS` / legacy `GEMINI_*` `OPENAI_*` `ANTHROPIC_*` 鐨勫吋瀹逛紭鍏堢骇銆佸洖閫€璺緞涓庘€滀笉闈欓粯杩佺Щ鏃ч厤缃€濈殑缁撹銆?
### 娴嬭瘯

- 鏂板 `tests/test_bot_market_command.py`锛岃鐩?`MARKET_REVIEW_REGION=both` + open markets `{"cn","us"}` / `{"cn","hk"}` 鐨?`override_region` 閫忎紶鏂█锛屽苟瑕嗙洊鍏ㄥ競鍦轰紤甯傝烦杩囦笌鍏抽棴浜ゆ槗鏃ユ鏌ヨ矾寰勶紱鏂板 `tests/test_yfinance_hk_indices.py` 瑕嗙洊娓偂鎸囨暟绗﹀彿鏄犲皠涓庨儴鍒?鍏ㄩ儴澶辫触闄嶇骇璺緞銆?- 琛ラ綈 `task_queue` 杞婚噺瀵煎叆 stub 鐨勮偂绁ㄤ唬鐮佽鑼冨寲鍑芥暟锛屾仮澶?`tests/test_task_queue_config_sync.py` 鏀堕泦涓庤繍琛屻€?
## [3.14.1] - 2026-04-26
- [娴嬭瘯] 淇澶х洏澶嶇洏 prompt 娴嬭瘯瀵光€滄槑鏃ヤ氦鏄撹鍒掆€濇爣棰樼殑鏂█锛屽苟鍚屾妗岄潰绔増鏈彿锛屾仮澶嶅彂甯?gate銆?
## [3.14.0] - 2026-04-26

### 鍙戝竷浜偣

- 馃搳 **澶х洏澶嶇洏鍗囩骇涓虹洏鍚庡伐浣滃彴寮忕粨鏋?* 鈥?A 鑲″鐩樺浐瀹氳緭鍑虹洏闈㈡俯搴︺€佹寚鏁版槑缁嗐€佹澘鍧?Top 琛ㄣ€佹柊闂诲偓鍖栥€佹槑鏃ヤ氦鏄撹鍒掑拰椋庨櫓鎻愮ず锛屽噺灏戠函鏂囧瓧澶嶇洏鐨勯噸澶嶄笌绌烘硾銆?- 馃枼锔?**妗岄潰绔柊澧?GitHub Release 鏇存柊鎻愰啋** 鈥?Windows/macOS 妗岄潰绔惎鍔ㄥ悗鑷姩妫€娴嬫柊鐗堟湰锛屼篃鍙粠璁剧疆椤垫墜鍔ㄦ鏌ュ苟璺宠浆涓嬭浇椤点€?- 馃 **Pipeline Agent 鏁版嵁鍔犺浇澶у箙闄嶅櫔** 鈥?K 绾垮伐鍏锋敼涓?DB-first 骞堕鐑?240 澶╁巻鍙叉暟鎹紝閬垮厤鍚屼竴鍙偂绁ㄩ噸澶?HTTP 璇锋眰銆?- 馃惓 **Docker 鍙戝竷閾捐矾鏁寸悊** 鈥?鍙戝竷宸ヤ綔娴佹敹鏁涗负姝ｅ紡鍙戝竷涓庢墜鍔ㄨˉ鍙戜袱鏉¤矾寰勶紝瀹樻柟 Docker Hub 闀滃儚鍚嶇粺涓€涓?`zhulinsen/daily_stock_analysis`銆?- 馃敡 **LLM 娓犻亾涓?DeepSeek V4 閰嶇疆琛ュ己** 鈥?GitHub Actions 瀹氭椂鍒嗘瀽琛ラ綈澶氭笭閬撳彉閲忛€忎紶锛孌eepSeek 瀹樻柟娓犻亾棰勮涓庣ず渚嬪悓姝ュ埌 V4銆?- 馃З **妗岄潰绔潤鎬佽祫婧愪竴鑷存€ф牎楠?* 鈥?鎵撳寘閾捐矾鍜岃繍琛屾椂閮借兘鏇存棭鍙戠幇闈欐€佽祫婧愰敊閰嶏紝闄嶄綆 Release 鍖呯櫧灞忔帓鏌ユ垚鏈€?
### 鏂板姛鑳?
- 馃彔 **Web 棣栭〉鍘嗗彶鎶ュ憡鍖烘柊澧為噸鏂板垎鏋愬叆鍙?* 鈥?鏀寔鍩轰簬鍘熷 prompt 閲嶅仛鍚屼竴鍙偂绁ㄥ悓鏃ユ湡鐨勫垎鏋愩€?- 馃枼锔?**Windows/macOS 妗岄潰绔柊澧?GitHub Release 鏇存柊鎻愰啋** 鈥?鍚姩鍚庤嚜鍔ㄦ娴嬫柊鐗堟湰锛屽苟鏀寔浠庤缃〉鎵嬪姩妫€鏌ュ悗璺宠浆涓嬭浇椤点€?
### 鏀硅繘

- 馃搳 **A 鑲″ぇ鐩樺鐩樻姤鍛婃敼涓虹粨鏋勫寲鐩樺悗宸ヤ綔鍙扮増寮?* 鈥?鍥哄畾杈撳嚭鐩橀潰娓╁害銆佹寚鏁版槑缁嗐€佹澘鍧?Top 琛ㄣ€佹柊闂诲偓鍖栧拰鏄庢棩浜ゆ槗璁″垝銆?- 馃惓 **Docker 鍙戝竷宸ヤ綔娴佹敹鏁?* 鈥?鏇存竻鏅板湴鍖哄垎姝ｅ紡鍙戝竷涓庢墜鍔ㄨˉ鍙戦摼璺紝骞剁粺涓€瀹樻柟 Docker Hub 闀滃儚鍚嶄负 `zhulinsen/daily_stock_analysis`銆?- 馃 **Agent 鏃ョ嚎宸ュ叿浼樺厛澶嶇敤鏈湴缂撳瓨** 鈥?鍚屾椂鎸佷箙鍖栨柊鑾峰彇鐨勬棩绾夸笌鏂伴椈鎯呮姤锛屽噺灏戦噸澶嶆暟鎹簮璋冪敤銆?
### 淇

- 馃 **Pipeline Agent K 绾垮伐鍏?DB-first 鍔犺浇** 鈥?`get_daily_history` / `analyze_trend` / `calculate_ma` / `get_volume_analysis` / `analyze_pattern` 鏀逛负浼樺厛璇诲彇鏈湴 DB锛屾秷闄ゅ悓涓€鍙偂绁?9x5=45 娆￠噸澶?HTTP 璇锋眰锛團ixes #1066锛夈€?- 馃 **Pipeline Agent 鎵ц鍓嶆寜闇€棰勭儹 240 澶?K 绾垮巻鍙插埌 DB** 鈥?姝ｅ父鎯呭喌涓?K 绾垮伐鍏疯皟鐢ㄦ棤闇€閲嶅缃戠粶璇锋眰銆?- 馃晵 **鍐荤粨 `target_date` 骞堕€氳繃 ContextVar 閫忎紶鍒?Pipeline Agent K 绾垮伐鍏风嚎绋?* 鈥?娑堥櫎璺ㄦ敹鐩樿竟鐣屾椂闂存紓绉汇€?- 馃獰 **Windows 妗岄潰绔悗绔棩蹇楄浆鎶勭紪鐮佷慨澶?* 鈥?杞妱 stdout/stderr 鏃朵紭鍏堜娇鐢?UTF-8锛屽苟鍏煎鏈湴浠ｇ爜椤靛洖閫€锛岄伩鍏嶄腑鏂囨棩蹇椾贡鐮併€?- 鈿欙笍 **GitHub Actions 姣忔棩鍒嗘瀽宸ヤ綔娴佽ˉ榻?LLM 娓犻亾鍙橀噺閫忎紶** 鈥?鏀寔 `LLM_CHANNELS`銆佸 Key 涓庡父鐢?`LLM_<NAME>_*`锛岄伩鍏嶆湰鍦板彲鐢ㄧ殑澶氭ā鍨嬮厤缃湪浜戠瀹氭椂浠诲姟涓け鏁堬紙Fixes #1063, #872锛夈€?- 馃搱 **鍘嗗彶鎶ュ憡璇︽儏鎺ュ彛淇 `change_pct` 鍙栧€?* 鈥?浣跨敤 `is None` 鍒ゆ柇閬垮厤鎶?0.0锛堝钩鐩橈級褰撲綔缂哄け鍊间涪寮冿紝绉婚櫎閿欒鐨?`change_60d` 鍏滃簳锛屽苟鍦ㄧ己澶辨椂鍥為€€鍒板師濮嬪疄鏃惰鎯呭瓧娈碉紙Fixes #1084锛夈€?- 馃敡 **DeepSeek 瀹樻柟娓犻亾棰勮涓庣ず渚嬮厤缃悓姝ュ埌 V4** 鈥?淇濈暀 legacy `deepseek-chat` 榛樿鍊煎苟澧炲姞搴熷純鎻愮ず锛屽悓鏃朵慨姝ｆā鍨嬪彂鐜板悗鏃ц繍琛屾椂閫夋嫨瀵艰嚧淇濆瓨澶辫触鐨勯棶棰橈紙Fixes #1108, #1109锛夈€?- 馃З **妗岄潰绔墦鍖呴摼璺柊澧為潤鎬佽祫婧愪竴鑷存€ф鏌?* 鈥?`scripts/check_static_assets.py` 浼氬湪婧?`static/` 涓?PyInstaller 浜х墿涓牎楠?`index.html` 寮曠敤鐨勮祫婧愭槸鍚︾湡瀹炲瓨鍦紝杩愯鏃朵篃浼氬湪閿欓厤鏃跺啓鍏ユ槑纭棩蹇楋紝閬垮厤閲嶇幇 Release 鍖呮墦寮€鍚庣櫧灞忥紙Refs #1064 / #1065 / #1050锛夈€?- 馃З **鍚庣 `/assets/*` 鏀逛负鏄惧紡璺敱鎵樼** 鈥?璧勬簮缂哄け鏃惰繑鍥炰笌璇锋眰鎵╁睍鍚嶅尮閰嶇殑 `text/javascript` / `text/css` 404锛屽噺灏戦粯璁?JSON 閿欒鍝嶅簲甯︽潵鐨勬帓鏌ヨ瀵硷紙Refs #1064锛夈€?- 馃寵 **`kimi-k2.6` 鑷姩浣跨敤鍥哄畾娓╁害** 鈥?涓诲垎鏋愩€佸ぇ鐩樺鐩樺拰 Agent 璋冪敤璇ユā鍨嬫椂鑷姩浣跨敤 `temperature=1.0`锛岄伩鍏嶆ā鍨嬫嫆缁濋粯璁ゆ俯搴﹁姹傦紙Fixes #1102锛夈€?
### 鏂囨。

- 馃惓 **琛ュ厖瀹樻柟 Docker 闀滃儚浣跨敤璇存槑** 鈥?澧炲姞闀滃儚鎷夊彇銆乣docker run` 鐢ㄦ硶涓?`.env` / 鏁版嵁鐩綍鏄犲皠璇存槑锛屼笉鍐嶅彧瑕嗙洊 Compose 閮ㄧ讲璺緞銆?- 馃摠 **淇椋炰功鑷畾涔夋満鍣ㄤ汉 Webhook 绀轰緥** 鈥?`feishu_sender.py` 涓殑绀轰緥鏀逛负 interactive card JSON锛屽苟琛ュ厖椋炰功鑷姩鍖?Webhook 瑙﹀彂鍣ㄩ厤缃暀绋嬨€?- 馃摎 **浼樺寲鏍?README 缁撴瀯** 鈥?淇濈暀棣栭〉绾у姛鑳界壒鎬с€佹妧鏈爤銆佸揩閫熷紑濮嬨€佹帹閫佹晥鏋溿€乄eb銆丄gent銆佽禐鍔╁晢鍜屾柊闂绘簮鍏ュ彛锛屽皢缁嗛厤缃€佷氦鏄撶邯寰嬪拰鍩烘湰闈㈣涔夋敹鍙ｅ埌瀹屾暣鎸囧崡锛屽苟灏?Docker 寰界珷鎸囧悜瀹樻柟闀滃儚椤点€?- 馃寪 **鍚屾鑻辨枃涓庣箒涓?README 鐨勭簿绠€鍏ュ彛缁撴瀯** 鈥?鍚屾椂琛ラ綈瀹屾暣鎸囧崡涓殑 LLM 鐢ㄩ噺 API 涓庢寔浠撶鐞嗚鏄庛€?- 馃 **璋冩暣 AI 鍗忎綔涓?PR 妯℃澘涓殑 README 缁存姢瑙勫垯** 鈥?鏄庣‘ README 闈炲繀瑕佷笉鏇存柊锛岀粏鑺備紭鍏堣繘鍏ヤ笓棰樻枃妗ｃ€?
### 娴嬭瘯

- 馃И **绋冲畾甯傚満澶嶇洏鐩稿叧娴嬭瘯鐨?LiteLLM stub 琛屼负** 鈥?閬垮厤鏈満瀹夎鐨?LiteLLM 鍦ㄦ祴璇曟敹闆嗛『搴忓彉鍖栨椂褰卞搷甯傚満澶嶇洏鍗曞厓娴嬭瘯銆?- 馃И **pytest 榛樿璺宠繃鍓嶇渚濊禆鐩綍** 鈥?鏈湴瀛樺湪 `apps/dsa-web/node_modules` 鏃朵笉鍐嶈鍚庣娴嬭瘯閫掑綊鎵弿锛岄伩鍏嶅彂甯冨墠 gate 琚棤鍏崇洰褰曟嫋鎱€?
## [3.13.0] - 2026-04-21

### 鍙戝竷浜偣

- 馃寜 **闀挎ˉ OpenAPI 鏁版嵁婧愭帴鍏?* 鈥?缇庤偂/娓偂琛屾儏浼樺厛浣跨敤 Longbridge锛孻Finance / AkShare 鑷姩鍏滃簳锛涙湭閰嶇疆鏃惰涓轰笉鍙樸€?- 馃搱 **Tushare 娓偂鍏ㄩ摼璺墿灞?* 鈥?娓偂鏃ョ嚎閫氳繃 `hk_daily` 鑾峰彇锛涚鐮佸垎甯冨娓偂杩斿洖 `None`锛涙崲绠楀崟浣嶈窡闅忔腐鑲″彛寰勶紝涓嶅啀濂楃敤 A 鑲℃墜/鍗冨厓瑙勫垯銆?- 馃攳 **Anspire Search 璇箟鎼滅储鎺ュ叆** 鈥?閰嶇疆 `ANSPIRE_*` 鍚庡嵆鍙娇鐢?Anspire Search 鑾峰彇瀹炴椂琛屾儏鍙婅祫璁紝鏈厤缃椂瀹屽叏閫忔槑銆?- 馃殌 **鏅€氬垎鏋愰摼璺敮鎸?LLM 娴佸紡鐢熸垚** 鈥?棣栭〉浠诲姟 SSE 鏂板 `task_progress` 浜嬩欢锛岃繘搴︽洿缁嗗寲锛涗笉鏀寔娴佸紡鐨?provider 鑷姩鍥為€€鍒伴潪娴佸紡璋冪敤銆?- 馃 **Web 娓犻亾缂栬緫鍣ㄦ敮鎸佹寜闇€鎷夊彇鍙敤妯″瀷鍒楄〃** 鈥?`/v1/models` 缁熶竴妯″瀷鍙戠幇鍏ュ彛锛屽閫夊啓鍥?`LLM_{CHANNEL}_MODELS`锛屾媺鍙栧け璐ユ椂淇濈暀鎵嬪姩杈撳叆闄嶇骇銆?- 馃洝锔?**Agent 绋冲畾鎬т笌棰勭畻鎶ゆ爮鍏ㄩ潰琛ュ己** 鈥?`AGENT_MAX_STEPS` 璇箟缁熶竴銆佹妧鑳介檷绾т笉涓柇绠＄嚎銆丼SE 寮傚父閫忎紶銆佹妧鑳藉姞杞?warning 鏃ュ織琛ラ綈銆?- 馃洜锔?**SQLite 鍐欏叆閾捐矾鍘熷瓙鍖?* 鈥?鎵归噺鍘熷瓙 upsert + WAL + `busy_timeout` + 鏈夐檺鍐欏叆閲嶈瘯锛屾樉钁楅檷浣庢壒閲忓垎鏋愬苟鍙戦攣绔炰簤銆?
### 鏂板姛鑳?
- 馃寜 **闆嗘垚 Longbridge OpenAPI 浣滀负缇庤偂/娓偂鍙€夋暟鎹簮**锛坒ixes #981锛夆€?閰嶇疆 `LONGBRIDGE_*` 鍚庝紭鍏堜娇鐢ㄩ暱妗ヨ幏鍙栨棩绾夸笌瀹炴椂琛屾儏锛孻Finance / AkShare 鍏滃簳锛涙湭閰嶇疆鏃惰涓轰笌姝ゅ墠涓€鑷淬€傝仈璋冧娇鐢?`tests/longbridge_live_smoke.py`锛堟墜鍔ㄨ剼鏈紝涓嶅弬涓?pytest 鏀堕泦锛夈€?- 馃搱 **Tushare 鏀寔娓偂鏃ョ嚎鏌ヨ** 鈥?閰嶇疆 Tushare 鍑瘉鍚庤皟鐢?`hk_daily` 鎺ュ彛鑾峰彇娓偂鏁版嵁锛涙潈闄愪笉瓒虫椂鎶涘嚭寮傚父锛屼笌鍘熸祦绋嬩竴鑷淬€?- 馃攳 **闆嗘垚 Anspire Search 鍙€夎涔夋悳绱㈠悗绔?* 鈥?閰嶇疆 `ANSPIRE_*` 鍙娇鐢?Anspire Search 鑾峰彇瀹炴椂琛屾儏鍙婃柊闂昏祫璁紱鏈厤缃椂琛屼负涓庢鍓嶄竴鑷淬€傝仈璋冧娇鐢?`tests/test_anspire_search.py`锛堟墜鍔ㄨ剼鏈級銆?- 馃殌 **鏅€氬垎鏋愰摼璺敮鎸?LiteLLM 娴佸紡鐢熸垚涓庢洿缁嗕换鍔¤繘搴?* 鈥?鑲＄エ鍒嗘瀽鍦?LLM 闃舵浼樺厛灏濊瘯 `stream=True` 骞跺湪鏈嶅姟绔疮绉?chunk锛岄椤典换鍔?SSE 鏂板 `task_progress` 浜嬩欢涓庢洿缁嗙殑 `message/progress` 鏇存柊锛涗粎鍦ㄦ渶缁?JSON 瑙ｆ瀽鎴愬姛鍚庢寔涔呭寲鍘嗗彶鎶ュ憡锛涗笉鏀寔娴佸紡鐨?provider 鑷姩鍥為€€鍒伴潪娴佸紡璋冪敤銆?- 馃 **Web AI 妯″瀷閰嶇疆鏀寔鎸夋笭閬撹幏鍙栧彲鐢ㄦā鍨嬪垪琛?* 鈥?娓犻亾缂栬緫鍣ㄦ敮鎸佽皟鐢?`/v1/models` 鎷夊彇鍙敤妯″瀷锛屽苟浠ュ閫夋柟寮忓啓鍥?`LLM_{CHANNEL}_MODELS`锛涙媺鍙栧け璐ユ椂淇濈暀鎵嬪姩杈撳叆浣滀负闄嶇骇璺緞銆?
### 鏀硅繘

- 馃攷 **SerpAPI 姝ｆ枃琛ユ姄鑼冨洿鏀舵暃** 鈥?鑷劧鎼滅储缁撴灉涓嶅啀閫愭潯鍚屾鎶撳彇缃戦〉姝ｆ枃锛涗粎瀵规瀬灏戞暟楂樹綅涓旀憳瑕佷笉瓒崇殑缁撴灉鍋氬欢杩熻ˉ鎶擄紝浼樺厛澶嶇敤 SerpAPI 宸茶繑鍥炵殑缁撴瀯鍖栨憳瑕侊紝闄嶄綆鎼滅储閾捐矾灏惧欢杩熶笌鎱㈢珯鐐规斁澶ч闄┿€?- 馃 **LLM 鎺ュ叆浣撻獙绠€鍖?* 鈥?闈㈠悜鐢ㄦ埛鐨?AI 妯″瀷鎺ュ叆鏂囨缁熶竴涓?涓绘ā鍨?/ Agent 涓绘ā鍨?/ 澶囬€夋ā鍨?/ 妯″瀷娓犻亾"锛屼笉鍐嶆妸 LiteLLM 褰撲綔鏅€氱敤鎴峰繀瀛︽蹇碉紝鐜版湁 `LITELLM_*` / `LLM_CHANNELS` 閰嶇疆閿繚鎸佸吋瀹广€?- 馃 **IntelAgent 鏂板鍏徃鍏憡鎼滅储涓庝富鍔涜祫閲戞祦宸ュ叿** 鈥?澧炲姞涓婁氦鎵€/娣变氦鎵€/cninfo 鍏憡鎼滅储缁村害涓?`get_capital_flow` 宸ュ叿锛屼慨澶?Agent 妯″紡涓嬪叕鍛婂拰璧勯噾娴佹暟鎹粡甯哥己澶辩殑闂銆?- 馃摝 **鍚庣鑲＄エ鍚嶇О瑙ｆ瀽浼樺厛澶嶇敤 `stocks.index.json`** 鈥?鎳掑姞杞界紦瀛樺墠绔潤鎬佺储寮曪紝绾悗绔?缂哄け闈欐€佽祫婧愬満鏅潤榛橀檷绾у洖 `STOCK_NAME_MAP` 涓庡師鏈夋暟鎹簮鍥為€€閾捐矾銆?- 馃搳 **TushareFetcher 娓偂鍗曚綅閫傞厤** 鈥?`get_chip_distribution` 瀵规腐鑲＄洿鎺ヨ繑鍥?`None`锛堟腐鑲℃殏涓嶆敮鎸佺鐮佸垎甯冿級锛沗_normalize_data` 瀵规腐鑲★紙`hk_daily`锛変笉鍐嶅仛 A 鑲℃墜鈫掕偂銆佸崈鍏冣啋鍏冪殑缂╂斁锛屼笌 Tushare 娓偂瀛楁璇箟涓€鑷淬€?- 鈴憋笍 **Agent 瓒呮鏁伴敊璇鍔?`AGENT_MAX_STEPS` 璋冩暣鎻愮ず** 鈥?甯姪鐢ㄦ埛鑷姪鎺掓煡姝ユ暟闄愬埗闂銆?- 鈿欙笍 **GitHub Actions 鍒嗘瀽浠诲姟瓒呮椂鏀寔 `vars` 閰嶇疆** 鈥?`daily_analysis.yml` 浠诲姟瓒呮椂浠?repository variables 璇诲彇锛屾棤闇€淇敼浠ｇ爜鍗冲彲璋冩暣杩愯瓒呮椂涓婇檺锛坒ixes #1014锛夈€?
### 淇

- 馃摚 **澶х洏澶嶇洏閾捐矾鎺ュ叆 `REPORT_LANGUAGE`** 鈥?`REPORT_LANGUAGE=en` 鏃讹紝A 鑲?鍚堝苟澶嶇洏鐨?Prompt銆佺珷鑺傛爣棰樸€佹ā鏉垮厹搴曟枃妗堜笌閫氱煡鍖呰鏍囬缁熶竴杈撳嚭鑻辨枃锛岄伩鍏嶈嫳鏂囨鏂囨惌閰嶄腑鏂囨爣棰樼殑娣锋帓闂銆?- 馃搱 **EfinanceFetcher 鎸囨暟寮€鐩樹环鏄犲皠鍏煎**锛坒ixes #1043锛夆€?`get_main_indices()` 鐨勫紑鐩樹环鏄犲皠鏀逛负鍏煎 `浠婂紑 鈫?寮€鐩?鈫?open`锛屼慨澶嶉儴鍒?efinance 鐗堟湰涓嬫寚鏁板紑鐩樹环琚鎴愮己澶卞€肩殑闂銆?- 馃 **AGENT_MAX_STEPS 璇箟缁熶竴**锛坒ixes #1026锛夆€?鍦?orchestrator 澶?Agent 妯″紡涓嬫槑纭负"鍚勫瓙 Agent 姝ユ暟涓婇檺鑰岄潪纭鐩?锛汿echnicalAgent 绛夐珮榛樿鍊?Agent 浼氳灏侀《锛屼綆榛樿鍊?Agent 淇濇寔鍘熷€硷紱鐢ㄦ埛涓诲姩璋冮珮锛?10锛夋椂缁熶竴瑕嗙洊鎵€鏈夊瓙 Agent銆備慨澶嶄簡鐢ㄦ埛璁剧疆 12 浣?TechnicalAgent 浠嶄互榛樿 6 姝ヨ繍琛屽苟鎶?"Agent exceeded max steps" 鐨勯棶棰樸€?- 馃洝锔?**Specialist锛圫kill锛堿gent 澶辫触鏀逛负浼橀泤闄嶇骇** 鈥?鎶€鑳?Agent 澶辫触涓嶅啀涓柇鏁翠釜鍒嗘瀽绠＄嚎锛屼笌 intel/risk 淇濇寔鐩稿悓鐨勯檷绾х瓥鐣ャ€?- 馃敡 **MiniMax-M2.7 杩炴帴娴嬭瘯淇** 鈥?淇 LLM 閫氶亾杩炴帴娴嬭瘯鍦?MiniMax-M2.7 涓嬭繑鍥?"Empty response" 鐨勯棶棰橈紱灏?`max_tokens` 涓婇檺浠?8 鎻愬崌鑷?256 浠ュ绾虫€濊€冭繃绋嬶紝骞舵坊鍔?`content_blocks` 鏍煎紡瑙ｆ瀽閫昏緫銆?- 馃搳 **绉婚櫎 `sentiment_score` 鑼冨洿绾︽潫**锛坒ixes #942锛夆€?绉婚櫎 `HistoryItem` 涓?`ReportSummary` 鍝嶅簲 Schema 涓?`sentiment_score` 鐨?`ge=0/le=100` 绾︽潫锛屽巻鍙插簱涓瓨鍌ㄧ殑瓒呰寖鍥村€间笉鍐嶈Е鍙?Pydantic ValidationError銆?- 馃枼锔?**WebUI 鍓嶇璧勬簮缂哄け鏃跺彂鍑烘槑纭鍛?* 鈥?`webui_frontend.py` 鍦?`static/index.html` 瀛樺湪浣?`static/assets/` 缂哄け鏃跺彂鍑?warning锛岄伩鍏?CSS/JS 璧勬簮缂哄け瀵艰嚧椤甸潰寮傚父鍙樺ぇ鍗存棤浠庢帓鏌ワ紙fixes #944锛夈€?- 馃敆 **鍒嗘瀽绠＄嚎鍙€夋湇鍔￠檷绾у垵濮嬪寲** 鈥?`StockAnalysisPipeline` 鎼滅储鏈嶅姟涓庣ぞ浜よ垎鎯呮湇鍔′换涓€鍒濆鍖栧紓甯告椂锛岃褰?warning 骞朵互绂佺敤鐘舵€佺户缁繍琛岋紝閬垮厤澶栭儴渚濊禆鎶栧姩闃诲涓诲垎鏋愰摼璺€?- 馃枼锔?**妗岄潰绔増鏈睍绀虹粺涓€璇诲彇 `package.json`** 鈥?缁熶竴璇诲彇 `apps/dsa-desktop/package.json`锛岀Щ闄?preload 涓‖缂栫爜鐨?`0.1.0`锛岃缃〉灞曠ず鐪熷疄妗岄潰绔増鏈紱淇鐗堟湰鍙锋樉绀洪敊璇紙fixes #1048锛夈€?- 馃悑 **娓偂鍚嶇О鑾峰彇澶辫触淇**锛坒ixes #940锛夆€?淇涓绘暟鎹簮瀛楁缂哄け鏃舵棤娉曟纭洖閫€鍒板鐢ㄥ瓧娈佃幏鍙栨腐鑲″悕绉扮殑闂銆?- 馃攧 **SSE 浠诲姟娴佹柇寮€鏃?`CancelledError` 姝ｇ‘ re-raise**锛坒ixes #967锛夆€?淇 SSE 娴佷腑鏂椂寮傚父琚潤榛樺悶鎺夊鑷存晠闅滄棤鏃ュ織鍙煡鐨勯棶棰樸€?- 馃攧 **Agent SSE 娓呯悊闃舵鍚庡彴浠诲姟寮傚父姝ｇ‘涓婃姤**锛坒ixes #969锛夆€?娴佺粨鏉熸椂鍚庡彴鎵ц鍣ㄥ紓甯哥幇鍦ㄦ纭褰曞苟涓婃姤锛岄伩鍏嶉敊璇棤娉曟劅鐭ャ€?- 馃攪 **鎶€鑳藉姞杞藉紓甯歌ˉ鍏?`logger.warning` 鏃ュ織**锛坒ixes #970锛夆€?鍦?`ask.py`銆乣skills/aggregator.py`銆乣skills/router.py` 鐨勯潤榛?except 鍧楄ˉ鍏呮棩蹇楋紝纭繚鎶€鑳藉垪琛ㄤ负绌烘椂鏈夋棩蹇楀彲鏌ャ€?- 馃洜锔?**SQLite 鍐欏叆閾捐矾鍘熷瓙鍖?*锛坒ixes #878锛夆€?`stock_daily(code,date)` 浣跨敤鎵归噺鍘熷瓙 upsert锛涙枃浠跺瀷 SQLite 杩炴帴榛樿鍚敤 WAL + `busy_timeout` + 鏈夐檺鍐欏叆閲嶈瘯锛?鏂板鏁?鏀规寜鏈鐪熸鎻掑叆绐楀彛璁＄畻銆?- 馃挵 **澶?Agent / 鍗?Agent 棰勭畻鎶ゆ爮璇箟缁熶竴** 鈥?鍓╀綑棰勭畻浣庝簬鏈€灏忛槇鍊兼椂涓诲姩璺宠繃骞堕檷绾э紱宸插畬鎴愰樁娈靛彲鏋勫缓闄嶇骇鎶ュ憡鏃惰繑鍥?`success=True` 骞舵惡甯﹂潪绌哄唴瀹癸紝鍚﹀垯杩斿洖 `success=False`銆?- 鈿欙笍 **GitHub Actions `daily_analysis.yml` 琛ラ綈 `REPORT_LANGUAGE` 娉ㄥ叆**锛坒ixes #1013锛夆€?淇鐢ㄦ埛鍦?Secrets/Variables 涓厤缃?`REPORT_LANGUAGE` 鍚庝笉鐢熸晥鐨勯棶棰樸€?- 馃搳 **浠诲姟鐘舵€?API 琛ラ綈瀹炴椂浠锋牸瀛楁**锛坒ixes #983锛夆€?`GET /api/v1/analysis/status/{task_id}` 浠庢暟鎹簱鍥炲～宸插畬鎴愪换鍔℃椂琛ラ綈 `current_price` / `change_pct`锛屼慨澶嶉椤垫姤鍛婅偂绁ㄥ悕鏃佷笉鏄剧ず瀹炴椂浠锋牸鐨勯棶棰樸€?- 馃搮 **闈炰氦鏄撴棩鏁版嵁杩斿洖鏈€杩戜氦鏄撴棩**锛坒ixes #1009锛夆€?淇闈炰氦鏄撴棩锛堝懆鏈?鑺傚亣鏃ワ級绛圭爜鍒嗗竷涓庢澘鍧楁帓琛岃繑鍥炲€掓暟绗簩涓氦鏄撴棩鏁版嵁鐨勯棶棰橈紝鐜板湪姝ｅ父杩斿洖鏈€杩戜氦鏄撴棩鏁版嵁銆?- 馃攳 **A 鑲¤祫璁悳绱㈡仮澶嶄腑鏂囦紭鍏?* 鈥?`search_stock_news()` 鍦ㄩ涓?provider 涓昏杩斿洖鑻辨枃璧勮鏃剁户缁皾璇曞悗缁紩鎿庯紝骞跺皢鍚屾壒缁撴灉涓殑涓枃璧勮鎺掑埌鍓嶉潰锛涢潪缇庤偂鏌ヨ涓嶅啀榛樿娌跨敤 Brave 鐨?`en/US` 鍖哄煙璇█鍋忓ソ銆?- 馃摠 **椋炰功缇ゆ満鍣ㄤ汉閫氱煡鏀寔绛惧悕鏍￠獙** 鈥?椋炰功閫氱煡鐜板湪鏀寔 `FEISHU_WEBHOOK_SECRET` / `FEISHU_WEBHOOK_KEYWORD`锛沇eb 璁剧疆涓庢枃妗ｆ槑纭尯鍒?Webhook 鎺ㄩ€佹ā寮忓拰 `FEISHU_APP_ID` / `FEISHU_APP_SECRET` 搴旂敤妯″紡锛岄檷浣庤閰嶉闄┿€?- 鈿?**LLM 閫傞厤灞傛柊澧?`RateLimitError` 鍜?`ContextWindowExceeded` 妫€娴?* 鈥?璇嗗埆骞跺鐞嗛€熺巼闄愬埗涓庝笂涓嬫枃绐楀彛瓒呭嚭閿欒锛屾彁鍗囧垎鏋愰摼璺湪楂樿礋杞芥垨闀挎枃鏈満鏅笅鐨勫仴澹€э紙fixes #1002锛夈€?
### 娴嬭瘯

- 馃И **TushareFetcher 娓偂鐩稿叧鍗曞厓娴嬭瘯** 鈥?鏂板 `get_chip_distribution` 绛圭爜鍒嗗竷鑾峰彇涓?`_normalize_data` 娓偂/A 鑲?ETF 鍗曚綅澶勭悊鐨勫崟鍏冩祴璇曪紝瑕嗙洊娓偂鐗规畩璺緞銆?
### 鏂囨。

- 馃摌 **DEPLOY.md 琛ュ厖 UI 鍏冪礌寮傚父鍙樺ぇ鎺掓煡姝ラ** 鈥?鏂板閲嶅缓 Docker 闀滃儚鎴栨墜鍔ㄦ墽琛?`npm run build` 鐨勬帓鏌ユ寚鍗楋紱`deploy-webui-cloud.md` 鍚屾鏇存柊銆?- 馃摠 **椋炰功 Webhook 閰嶇疆璇存槑琛ュ叏** 鈥?寮鸿皟 `FEISHU_WEBHOOK_URL` 鏄兢閫氱煡蹇呭～椤广€佺鍚嶆牎楠岄』涓ょ鍚屾椂鍚敤鎴栧叧闂€乣FEISHU_APP_SECRET` 浠呯敤浜庡簲鐢?Stream Bot 妯″紡锛沗.env.example` 琛ュ厖鍐呰仈娉ㄩ噴锛涘悓姝ヨ嫳鏂囨寚鍗椼€?- 馃 **FAQ 琛ュ厖 Ollama 杩炴帴澶辫触鎺掗殰鏉＄洰锛圦12c锛?* 鈥?瑕嗙洊鏈嶅姟鏈惎鍔ㄣ€乁RL 閰嶇疆閿欒銆佹ā鍨嬪墠缂€缂哄け銆佹ā鍨嬫湭涓嬭浇銆佽繙绋嬮槻鐏绛?5 涓鏌ョ偣锛坒ixes #854锛夈€?- 馃寜 **README 琛ュ厖闀挎ˉ鏁版嵁婧愪娇鐢ㄨ鏄?* 鈥?涓?鑻?绻?README 鏄庣‘闀挎ˉ"棣栭€?/ 鍏滃簳 / 鏈厤缃笉璋冪敤"杈圭晫锛沗docs/` 鍐呯浉瀵硅矾寰勯摼鎺ヤ慨澶嶏紱`LONGBRIDGE_PRINT_QUOTE_PACKAGES` 閰嶇疆涓庝唬鐮佸強 `.env.example` 瀵归綈銆?- 馃悑 **Docker 瀹夎鍦烘櫙鐗堟湰璇存槑** 鈥?琛ュ厖鏈€灏忓寲鏂囨。锛屾槑纭?Docker 瀹夎鍦烘櫙涓嬪簲浠?Git tag / 闀滃儚 tag 鍒ゆ柇鐗堟湰锛坒ixes #1091锛夈€?
## [3.12.0] - 2026-04-01

### 鍙戝竷浜偣

- 馃搳 **鍥炴祴椤垫柊澧?娆℃棩楠岃瘉"瑙嗗浘** 鈥?鍙寜鑲＄エ涓庢棩鏈熻寖鍥存煡鐪?AI 棰勬祴 vs 娆℃棩瀹為檯娑ㄨ穼锛屽鐢ㄥ巻鍙插垎鏋愪笌 1 鏃ュ洖娴嬬粨鏋滐紝蹇€熼獙璇佸垎鏋愬噯纭巼銆?- 馃敡 **LLM 鎺ュ叆浣撻獙绠€鍖?* 鈥?鐢ㄦ埛渚ф枃妗堢粺涓€鏀跺彛涓?涓绘ā鍨?/ 澶囬€夋ā鍨?/ 妯″瀷娓犻亾"锛屼笉鍐嶆妸 LiteLLM 褰撲綔鏅€氱敤鎴峰繀瀛︽蹇碉紝鐜版湁閰嶇疆閿繚鎸佸吋瀹广€?- 馃惓 **Docker / WebUI 杩愯鏃剁ǔ鎬佽ˉ寮?* 鈥?淇绯荤粺璁剧疆淇濆瓨鍚庨厤缃笉鐢熸晥銆佸惎鍔ㄦ棭鏈熸棩蹇楃己澶便€侀鏋勫缓闈欐€佽祫婧愬鐢ㄧ瓑闂锛岄檷浣庡鍣ㄥ寲閮ㄧ讲鐨勮繍缁存懇鎿︺€?- 馃敀 **瀹夊叏涓庡苟鍙戠ǔ瀹氭€у悓姝ュ寮?* 鈥?Discord 鍏ョ珯 Webhook 琛ラ綈 Ed25519 楠岀锛屼慨澶嶅苟鍙戞墽琛屾椂鍏变韩鐘舵€佹湭鍔犻攣銆佸崟鑲℃帹閫佹ā寮忛€氱煡骞跺彂澶嶇敤绛夐棶棰樸€?- 馃枼锔?**妗岄潰绔笌瀹氭椂浠诲姟缁嗚妭鎵撶（** 鈥?Windows 瀹夎鍣ㄦ敮鎸佽嚜閫夊畨瑁呯洰褰曪紝鍐呯疆瀹氭椂璋冨害鍣ㄦ劅鐭ヨ繍琛屼腑 SCHEDULE_TIME 鍙樻洿锛屾柇鐐圭画浼犳敼鎸夊競鍦烘椂鍖哄垽鏂€?
### 鏂板姛鑳?
- 馃搳 **鍥炴祴椤垫柊澧?娆℃棩楠岃瘉 / 1 鏃ョ獥鍙?瑙嗗浘** 鈥?鍙寜鑲＄エ浠ｇ爜涓庡垎鏋愭棩鏈熻寖鍥存煡鐪?AI 棰勬祴銆佹鏃ュ疄闄呮定璺屽強绛涢€夊尯闂村噯纭巼锛屽鐢ㄥ巻鍙插垎鏋愪笌 1 鏃ュ洖娴嬬粨鏋滃疄鐜般€?- 馃彿锔?**Web 璁剧疆椤垫柊澧炵増鏈俊鎭崱鐗?* 鈥?`apps/dsa-web` 鐜板湪浼氬湪鏋勫缓鏃舵敞鍏ュ墠绔寘鐗堟湰涓庢瀯寤烘椂闂达紝绯荤粺璁剧疆椤垫柊澧炲彧璇?鐗堟湰淇℃伅"鍖哄潡锛屽睍绀?`WebUI 鐗堟湰 / 鏋勫缓鏍囪瘑 / 鏋勫缓鏃堕棿`锛涘綋 `package.json` 浠嶄负鍗犱綅鐗堟湰 `0.0.0` 鏃讹紝浼氳嚜鍔ㄥ洖閫€涓烘瀯寤烘爣璇嗭紝鏂逛究 Docker 閲嶅缓鍚庡揩閫熺‘璁ゅ綋鍓嶉潤鎬佽祫婧愭槸鍚﹀凡缁忕敓鏁堛€?- 馃獰 **Windows 妗岄潰瀹夎鍣ㄦ敮鎸佽嚜閫夊畨瑁呯洰褰?* 鈥?瀹夎鍣ㄦ敼涓烘敮鎸佸湪瀹夎鍚戝涓嚜瀹氫箟瀹夎鐩綍锛屽畨瑁呭埌闈為粯璁ょ洏绗﹀悗浠嶆部鐢ㄧ幇鏈夋墦鍖呮€佺洰褰曢€昏緫鍦ㄥ畨瑁呯洰褰曟梺璇诲啓 `.env`銆乣data/stock_analysis.db` 鍜?`logs/desktop.log`锛屽悓鏃朵繚鐣?`win-unpacked` 鍏嶅畨瑁呭垎鍙戞柟寮忋€傚畨瑁呭櫒浠呮敮鎸佸綋鍓嶇敤鎴峰畨瑁呫€佸凡绂佺敤绠＄悊鍛樻彁鏉冿紙`allowElevation: false`锛夛紝骞堕€氳繃 NSIS `.onVerifyInstDir` 闃绘閫夋嫨绯荤粺淇濇姢鐩綍銆?
### 鏀硅繘

- 馃攷 **SerpAPI 姝ｆ枃琛ユ姄鑼冨洿鏀舵暃** 鈥?鑷劧鎼滅储缁撴灉涓嶅啀閫愭潯鍚屾鎶撳彇缃戦〉姝ｆ枃锛涚幇鍦ㄤ粎瀵规瀬灏戞暟楂樹綅涓旀憳瑕佹槑鏄句笉瓒崇殑缁撴灉锛屽湪鏇寸煭瓒呮椂棰勭畻鍐呭仛寤惰繜琛ユ姄锛屽苟浼樺厛澶嶇敤 SerpAPI 宸茶繑鍥炵殑缁撴瀯鍖栨憳瑕侊紝闄嶄綆鎼滅储閾捐矾灏惧欢杩熶笌鎱㈢珯鐐规斁澶ч闄┿€?- 馃 **LLM 鎺ュ叆浣撻獙绠€鍖?* 鈥?闈㈠悜鐢ㄦ埛鐨?AI 妯″瀷鎺ュ叆鏂囨宸茬粺涓€鏀跺彛涓?涓绘ā鍨?/ Agent 涓绘ā鍨?/ 澶囬€夋ā鍨?/ 妯″瀷娓犻亾 / 楂樼骇妯″瀷璺敱閰嶇疆"锛沇eb 璁剧疆椤点€侀厤缃厓鏁版嵁銆佹牎楠屾彁绀轰笌涓嫳鏂囨枃妗ｄ笉鍐嶆妸 LiteLLM 褰撲綔鏅€氱敤鎴烽粯璁ゅ繀瀛︽蹇碉紝鐜版湁 `LITELLM_*` / `LLM_CHANNELS` 閰嶇疆閿粛淇濇寔鍏煎銆?
### 淇

- 馃殌 **鍚姩鏃╂湡澶辫触鏃舵毚闇茬湡瀹炴牴鍥?* 鈥?`python main.py` 鐜板湪閫氳繃 stderr 鏆撮湶鐪熷疄鏍瑰洜锛宐ootstrap 闃舵涓嶅啀鍚戠‖缂栫爜 `logs/` 鐩綍鍐欏叆鏂囦欢鏃ュ織锛屾枃浠舵棩蹇楁帹杩熷埌 `config.log_dir` 鍙敤鍚庡垱寤猴紝閬垮厤鍋ュ悍鍚姩鍦ㄩ潪棰勬湡璺緞娈嬬暀鏃ュ織鏂囦欢銆?- 馃惓 **Docker WebUI 杩愯鏃朵紭鍏堝鐢ㄩ鏋勫缓闈欐€佽祫婧?* 鈥?`prepare_webui_frontend_assets()` 鐜板湪浼氬厛妫€鏌ラ暅鍍忓唴宸叉湁鐨?`static/index.html` 鏄惁鍙洿鎺ュ鐢紱褰撳鍣ㄨ繍琛屾椂涓嶅寘鍚?`apps/dsa-web` 婧愮爜鐩綍涓旀湭瀹夎 `npm` 鏃讹紝涔熶笉浼氳鎶?鏈壘鍒板墠绔」鐩紝鏃犳硶鑷姩鏋勫缓"锛屼粠鑰屾仮澶?Docker 閮ㄧ讲鍚庣殑 WebUI 鎵撳紑鑳藉姏銆?- 馃惓 **Docker WebUI 绯荤粺璁剧疆淇濆瓨鍚庨厤缃敓鏁?* 鈥?Docker 鍦烘櫙涓?WebUI 淇濆瓨 `STOCK_LIST`銆乣SCHEDULE_ENABLED`銆乣SCHEDULE_TIME`銆乣SCHEDULE_RUN_IMMEDIATELY`銆乣RUN_IMMEDIATELY` 鍚庯紝`Config` 浼氫紭鍏堣鍙栨寔涔呭寲 `.env` 涓殑鏂板€硷紝閬垮厤琚鍣ㄥ垱寤烘椂娉ㄥ叆鐨勬棫鐜鍙橀噺瑕嗙洊銆?- 馃搱 **甯傚満澶嶇洏 LLM max_tokens 鎻愬崌** 鈥?甯傚満澶嶇洏鐢熸垚閾捐矾灏?LLM `max_tokens` 浠?`2048` 鎻愬崌鍒?`8192`锛岄檷浣庨暱澶嶇洏杈撳嚭鍥?`MAX_TOKENS` 鎻愬墠鎴柇瀵艰嚧鍐呭鏈畬鎴愮殑姒傜巼銆?- 鈴?**鍐呯疆瀹氭椂璋冨害鍣ㄦ劅鐭?SCHEDULE_TIME 杩愯鏃跺彉鏇?* 鈥?璋冨害鍣ㄧ幇鍦ㄤ細鍦ㄨ繍琛屼腑鎰熺煡 WebUI 淇濆瓨鍚庣殑 `SCHEDULE_TIME` 鍙樺寲锛屽苟鍦ㄤ笅涓€杞鏌ユ椂閲嶇粦 daily job銆?- 馃獰 **Windows Release 娓犻亾缂栬緫鍣ㄤ繚鐣?MiniMax 妯″瀷鍓嶇紑** 鈥?娓犻亾妯″紡涓嬪～鍐?`minimax/<妯″瀷鍚?` 鏃讹紝鍚庣褰掍竴鍖栦笌 Web 璁剧疆椤佃繍琛屾椂妯″瀷鍒楄〃閮戒細淇濈暀璇ュ€煎師鏍凤紝涓嶅啀璇敼鍐欐垚 `openai/minimax/<妯″瀷鍚?`銆?- 馃 **Discord 鍏ョ珯 Webhook 琛ラ綈 Ed25519 楠岀** 鈥?`DiscordPlatform` 鐜板湪浼氬熀浜?`X-Signature-Ed25519`銆乣X-Signature-Timestamp` 鍜屽師濮嬭姹備綋鏍￠獙 Discord Interaction 绛惧悕锛涚己澶辩鍚嶅ご銆佸叕閽ユ牸寮忛潪娉曟垨绛惧悕涓嶅尮閰嶆椂鐩存帴鎷掔粷璇锋眰锛屽悓鏃跺 timestamp 鍋?卤5 鍒嗛挓鏃舵晥绐楀彛鏍￠獙浠ラ槻寰￠噸鏀炬敾鍑汇€?- 鈿欙笍 **STOCK_GROUP_N / EMAIL_GROUP_N 閰嶇疆鍏崇郴鏄庣‘鍖?* 鈥?鏄庣‘涓?`STOCK_LIST` 鐨勫叧绯伙紝骞跺湪閰嶇疆鏍￠獙涓瓒呭嚭 `STOCK_LIST` 鐨勯偖浠跺垎缁勭粰鍑?warning銆?- 馃棑锔?**鏂偣缁紶鏀规寜甯傚満鏃跺尯鍜屼氦鏄撴棩鍘嗗垽鏂?*锛坒ixes #880锛夆€?鑲＄エ鏁版嵁瀛樺湪鎬ф鏌ヤ笉鍐嶇洿鎺ヤ娇鐢ㄦ湇鍔″櫒鑷劧鏃ワ紝鑰屾槸鎸?A 鑲?/ 娓偂 / 缇庤偂鍚勮嚜甯傚満鏃跺尯瑙ｆ瀽"鏈€鏂板彲澶嶇敤浜ゆ槗鏃?銆?- 馃摠 **鍗曡偂鎺ㄩ€佹ā寮忎笉鍐嶅苟鍙戝鐢ㄥ叡浜€氱煡瀹炰緥** 鈥?`StockAnalysisPipeline.run()` 鐜板湪浼氫繚鐣欎釜鑲″垎鏋愬苟鍙戯紝浣嗘妸 `SINGLE_STOCK_NOTIFY=true` 涓嬬殑鍗虫椂閫氱煡鎸埌缁撴灉鏀堕泦渚т覆琛屽彂閫併€?- 馃攪 **瀹炴椂琛屾儏闄嶇骇鎻愮ず鏀跺彛涓哄崟娆″憡璀?* 鈥?鍒嗘瀽涓绘祦绋嬭幏鍙栬偂绁ㄥ悕绉版椂涓嶅啀鎻愬墠瑙﹀彂涓€娆″疄鏃惰鎯呮煡璇紝鍙湁鍦ㄥ叏閮ㄦ暟鎹簮閮戒笉鍙敤鏃舵墠鎻愮ず宸查檷绾т负鍘嗗彶鏀剁洏浠风户缁垎鏋愩€?- 馃攳 **A 鑲′腑鏂囪祫璁悳绱㈡仮澶嶄腑鏂囦紭鍏?* 鈥?`search_stock_news()` 鐜板湪浼氬湪棣栦釜 provider 涓昏杩斿洖鑻辨枃璧勮鏃剁户缁皾璇曞悗缁紩鎿庯紝骞跺皢鍚屾壒缁撴灉涓殑涓枃璧勮鎺掑埌鍓嶉潰銆?- 馃敀 **骞跺彂鎵ц鏃跺叡浜姸鎬佽ˉ榻愮粺涓€鍔犻攣** 鈥?淇骞跺彂鎵ц鏃跺叡浜姸鎬佺己灏戠粺涓€鍔犻攣鐨勯棶棰橈紝閬垮厤澶氱嚎绋嬪満鏅笅鐨勬暟鎹珵浜夈€?
### 娴嬭瘯

- 馃И **琛ュ厖璁剧疆椤电増鏈俊鎭洖褰掓祴璇?* 鈥?鏂板 Web 璁剧疆椤电増鏈俊鎭覆鏌撴柇瑷€锛屽苟瑕嗙洊鍗犱綅鐗堟湰 `0.0.0` 鑷姩鍥為€€涓烘瀯寤烘爣璇嗙殑閫昏緫銆?- 馃И **UI 娌荤悊涓庡叧閿矾寰勫洖褰掕ˉ寮?* 鈥?琛ュ厖 `SidebarNav`銆乣ChatPage`銆乣BacktestPage` 绛夌粍浠舵祴璇曪紝骞舵柊澧?UI governance 瀹堝崼锛屾寔缁槻姝氦浜掑厓绱犻噸鏂板紩鍏ュ師鐢?`title` 灞炴€ф垨鏃?`input-terminal` 鏍峰紡鍥炴祦銆傚悓姝ユ洿鏂?smoke / markdown drawer 鐩稿叧楠岃瘉锛岃鐩栦富棰樺崌绾у悗鐨勫叧閿富閾捐矾銆?
## [3.11.0] - 2026-03-27

### 鍙戝竷浜偣

- 馃帹 **Web 宸ヤ綔鍙板畬鎴愪竴杞?UI 缁熶竴涓庡弻涓婚鍗囩骇** 鈥?棣栭〉銆侀棶鑲°€佸洖娴嬨€佹寔浠撳拰璁剧疆椤佃繘涓€姝ユ敹鍙ｅ埌缁熶竴璁捐 token銆佽緭鍏ヨ〃闈㈠拰鐘舵€佽〃杈撅紱鏂板瀹屾暣娴呰壊涓婚锛屽苟鏀寔娴呰壊 / 娣辫壊涓€閿垏鎹笌鎸佷箙鍖栦繚瀛樸€?- 馃 **Bot / Agent 鑳藉姏閲嶆柊琛ュ洖涓诲垎鏀?* 鈥?鎭㈠ `/history`銆乣/strategies`銆乣/research` 绛夊懡浠わ紝`/ask` 缁х画鏀寔澶氳偂瀵规瘮涓庣粍鍚堣瑙掞紱Deep Research銆佷簨浠剁洃鎺т笌 schedule 杞閾捐矾閲嶆柊鎺ュ洖涓荤嚎鑳藉姏銆?- 馃敀 **瀹夊叏鎬т笌杩愯绋虫€佸悓姝ヨˉ寮?* 鈥?淇 `X-Forwarded-For` 闄愭祦缁曡繃椋庨櫓锛屾仮澶?LiteLLM 瀹樻柟 PyPI 瀹夎璺緞锛孴ushare 鍒濆鍖栦笉鍐嶄緷璧栨湰鍦?SDK锛岄檷浣?Docker銆佹闈㈡墦鍖呭拰鐜閲嶅缓鏃剁殑鑴嗗急鐐广€?- 馃枼锔?**鏃ュ父浣跨敤缁嗚妭缁х画鎵撶（** 鈥?淇棣栭〉娓偂鑷姩琛ュ叏鎻愪氦銆佺櫥褰曢〉棣栧睆涓婚闂儊銆佸巻鍙查暱鑲＄エ鍚嶉噸鍙狅紝浠ュ強 Telegram Markdown 瑙ｆ瀽澶辫触鏃舵暣鏉￠€氱煡鍙戦€佷腑鏂瓑闂銆?
### 鏂板姛鑳?
- 馃帹 **鍏ㄦ柊娴呰壊涓婚涓庡弻涓婚鍒囨崲涓婄嚎** 鈥?Web 宸ヤ綔鍙版柊澧炲畬鏁存祬鑹蹭富棰橈紝骞舵敮鎸佸湪渚ц竟鏍忎腑涓€閿垏鎹㈡祬鑹?/ 娣辫壊妯″紡锛涗富棰橀€夋嫨浼氭寔涔呭寲淇濆瓨锛屽埛鏂伴〉闈㈠悗浠嶄繚鎸佸綋鍓嶅亸濂姐€傛娆″崌绾т笉鏄眬閮ㄩ厤鑹插井璋冿紝鑰屾槸瀵瑰崱鐗囧眰绾с€佽竟鐣屽姣斻€佽緭鍏ヨ〃闈€佺姸鎬佹彁绀哄拰椤甸潰鑳屾櫙鍋氫簡涓€鏁村 light theme 閲嶇粯銆?- 馃 **琛ュ洖涓诲垎鏀己澶辩殑 Agent / Bot 鑳藉姏** 鈥?`#648` / `#649` 宸查噸鏂拌ˉ鍥?`main`锛欱ot 鎭㈠ `/history`銆乣/strategies`銆乣/research`锛宍/ask` 淇濈暀澶氳偂瀵规瘮涓庣粍鍚堣瑙掞紱Deep Research 涓?Event Monitor 鐨勯厤缃噸鏂板湪 Web 璁剧疆椤靛彲瑙佸苟鍙紪杈戯紝schedule 妯″紡涔熼噸鏂版帴鍏ヤ簨浠跺憡璀﹁疆璇€?
### 鏀硅繘

- 馃枼锔?**鏍稿績椤甸潰缁熶竴鍒板悓涓€濂楀伐浣滃彴瑙嗚璇█** 鈥?`Home / Chat / Backtest / Portfolio / Settings` 杩涗竴姝ユ敹鍙ｅ埌鍏变韩璁捐 token銆乣input-surface` 杈撳叆浣撶郴銆佺┖鎬?閿欒鎬佽〃杈惧拰鎶藉眽閬僵璇箟锛屽噺灏戦〉闈箣闂寸殑瑙嗚鍓茶涓庡眬閮ㄧ鏈夋牱寮忔紓绉汇€?- 馃挰 **闂偂浜や簰鍙揪鎬т笌鍙嶉澧炲己** 鈥?闂偂椤佃ˉ寮轰簡浼氳瘽瀵煎嚭銆侀€氱煡鍙戦€併€佹秷鎭鍒躲€佸巻鍙插垹闄や笌杩介棶涓婁笅鏂囨彁绀猴紱AI 鍥炲鎿嶄綔涓嶅啀杩囧害渚濊禆 hover锛岃Е灞忚澶囧拰灏忓睆鍦烘櫙涓嬩篃鑳界洿鎺ヨЕ杈惧叧閿寜閽€?- 馃搳 **鍥炴祴涓庢寔浠撻〉琛ㄩ潰鍜岀姸鎬佽〃杈剧户缁爣鍑嗗寲** 鈥?鍥炴祴椤电瓫閫夋帶浠躲€佸竷灏旂姸鎬併€佺粨鏋滆〃鏍间笌姹囨€诲崱鐗囩粺涓€鍒板叡浜緭鍏?鐘舵€佸師璇紱鎸佷粨椤电殑瀵煎叆鍙嶉銆佹眹鐜囧埛鏂版彁绀恒€佺┖鎬佷笌璀︾ず淇℃伅杩涗竴姝ュ綊鍙ｅ埌鍏变韩缁勪欢锛屽噺灏戦〉闈㈢骇閲嶅瀹炵幇銆?- 馃Л **瀵艰埅涓庨〉闈㈠３灞傚崗鍚屼紭鍖?* 鈥?渚ц竟鏍忎富棰樺垏鎹€侀棶鑲″畬鎴愯鏍囥€佺Щ鍔ㄧ鎶藉眽閬僵鍜屼富鍐呭婊氬姩濂戠害杩涗竴姝ョ粺涓€锛岄椤点€侀棶鑲″拰鍥炴祴鍦ㄦ闈㈢涓庣Щ鍔ㄧ鐨勫垏椤典綋楠屾洿绋冲畾銆?
### 娴嬭瘯

- 馃И **UI 娌荤悊涓庡叧閿矾寰勫洖褰掕ˉ寮?* 鈥?琛ュ厖 `SidebarNav`銆乣ChatPage`銆乣BacktestPage` 绛夌粍浠舵祴璇曪紝骞舵柊澧?UI governance 瀹堝崼锛屾寔缁槻姝氦浜掑厓绱犻噸鏂板紩鍏ュ師鐢?`title` 灞炴€ф垨鏃?`input-terminal` 鏍峰紡鍥炴祦銆傚悓姝ユ洿鏂?smoke / markdown drawer 鐩稿叧楠岃瘉锛岃鐩栦富棰樺崌绾у悗鐨勫叧閿富閾捐矾銆?
### 淇

- 馃寳 **Web 棣栧睆榛樿涓婚棰勮涓烘繁鑹?* 鈥?`apps/dsa-web/index.html` 鐜板湪浼氬湪 React 鎸傝浇鍓嶈鍙栨湰鍦颁繚瀛樼殑涓婚鍋忓ソ锛涜嫢娌℃湁宸蹭繚瀛樺€硷紝鍒欑珛鍗崇粰 `<html>` 棰勮 `dark` 骞跺悓姝?`color-scheme`锛岄伩鍏嶉椤靛拰鐧诲綍椤甸灞忓厛闂嚭娴呰壊涓婚銆?- 馃攼 **鐧诲綍椤电嫭绔嬩富棰樺眰鏀跺彛** 鈥?鐧诲綍椤佃緭鍏ユ銆佹爣绛俱€佸垏鎹㈡寜閽拰鎸夐挳鏂囨鐜板湪浣跨敤鐙珛鐨?`--login-*` 瑙嗚 token锛屼笉鍐嶇户鎵垮叏灞€娴?娣变富棰樻枃瀛楄壊锛涘嵆浣挎祻瑙堝櫒缂撳瓨浜嗘祬鑹蹭富棰橈紝鐧诲綍椤典粛淇濇寔绋冲畾鐨勬繁鑹茶瑙変笌闈掕壊瀵嗙爜杈撳叆琛ㄧ幇锛岄伩鍏嶅瘑鐮佸渾鐐瑰拰鏂囨钀芥垚榛戣壊銆?- 馃枼锔?**棣栭〉娓偂浠ｇ爜杈撳叆淇** 鈥?Web 棣栭〉鍒嗘瀽杈撳叆妗嗙幇鍦ㄥ彲姝ｇ‘鎺ュ彈娓偂浠ｇ爜涓庤嚜鍔ㄥ畬鎴愰€変腑鐨勬腐鑲￠」锛岃ˉ榻?`00700.HK` / `HK00700` 绛夋牸寮忚瘑鍒紝閬垮厤鎻愪氦鏃惰鎶モ€滆杈撳叆鏈夋晥鐨勮偂绁ㄤ唬鐮佹垨鑲＄エ鍚嶇О鈥濄€?
- 馃敀 **璁よ瘉闄愭祦 X-Forwarded-For 鍙栧€间慨澶嶏紙CWE-345锛?*锛?841 / #842锛夆€?`get_client_ip()` 浠庡彇 `X-Forwarded-For` 鏈€宸﹀€兼敼涓烘渶鍙冲€硷紝闃叉鏀诲嚮鑰呴€氳繃浼€犻閮ㄦ棆杞檺娴佹《缁曡繃鏆村姏鐮磋В淇濇姢锛涗粎褰卞搷 `TRUST_X_FORWARDED_FOR=true` 涓斿崟灞傚彲淇″弽鍚戜唬鐞嗙殑閮ㄧ讲鍦烘櫙锛屽绾т唬鐞嗙幆澧冮渶鎸夐儴缃叉枃妗ｈ瘎浼伴厤缃€?- 馃摝 **鎭㈠ LiteLLM 瀹樻柟 PyPI 瀹夎骞堕攣瀹氬畨鍏ㄤ笂闄?* 鈥?`requirements.txt` 閲嶆柊浣跨敤 `pip install litellm` 鐨勫畼鏂?PyPI 瀹夎璺緞锛屽苟鍦ㄤ繚鐣欏巻鍙叉渶浣庤姹?`>=1.80.10` 鐨勫悓鏃跺鍔?`<1.82.7` 鐨勫畨鍏ㄤ笂闄愶紝閬垮厤璇宸茶绉婚櫎鐨?`1.82.7` / `1.82.8` 椋庨櫓鐗堟湰锛沇indows 妗岄潰鎵撳寘鑴氭湰涔熷悓姝ュ洖閫€鍒版爣鍑?`pip install -r requirements.txt` 閾捐矾锛屽噺灏戠壒娈婁笅杞藉垎鏀甫鏉ョ殑缁存姢鎴愭湰銆?- 馃摠 **Telegram Markdown 瑙ｆ瀽澶辫触鍥為€€绾枃鏈?*锛坒ixes #850锛夆€?`src/notification_sender/telegram_sender.py` 鐜板湪浼氬湪 Telegram 杩斿洖 `HTTP 400` 涓斿寘鍚?`can't parse entities` / Markdown 瑙ｆ瀽閿欒鏃讹紝鑷姩鍘绘帀 `parse_mode` 鍚庨噸璇曠函鏂囨湰鍙戦€侊紝閬垮厤 `*ST` 绛夋鏂囧唴瀹圭洿鎺ュ鑷存暣鏉￠€氱煡澶辫触銆?- 馃敘 **A 鑲″悓鐮佸疄鏃惰鎯呬繚鐣欎氦鏄撴墍鎻愮ず**锛坒ixes #852锛夆€?`DataFetcherManager` 涓?`TushareFetcher` 鐜板湪浼氫繚鐣?`SZ000001` / `000001.SZ` 杩欑被鏄惧紡娌繁鎻愮ず锛屾棫鐗?Tushare 瀹炴椂琛屾儏闄嶇骇鍒嗘敮涓嶅啀鎶婃繁甯?`000001` 璇垽鎴?`sh000001` 涓婅瘉鎸囨暟銆?- 馃幆 **澶?Agent 娆′紭涔扮偣涓嶅啀鐩茬洰澶嶅埗鐞嗘兂涔扮偣**锛坒ixes #851锛夆€?褰撳鏅鸿兘浣撶粨鏋滅己灏戠嫭绔?`secondary_buy` 鏃讹紝浠〃鐩樼幇鍦ㄤ紭鍏堝睍绀?`N/A` 鑰屼笉鏄妸 fallback 鍊肩‖鎷疯礉鎴愪笌 `ideal_buy` 瀹屽叏鐩稿悓锛屽噺灏戣瀵兼€х殑鍙屼拱鐐瑰睍绀恒€?- 馃З **Tushare 鍒濆鍖栦笉鍐嶅己渚濊禆鏈湴 SDK 鍖?* 鈥?`TushareFetcher` 鐜板湪鐩存帴浣跨敤鍐呯疆 HTTP client 璁块棶 Tushare Pro锛屼笉鍐嶅湪鍚姩闃舵鍏?`import tushare` 鎵嶈兘鍒濆鍖栵紱淇浜?Docker銆佹闈㈡墦鍖呮垨鐜閲嶅缓鍚庡洜缂哄皯 `tushare` 鍖呰€屾彁鍓嶆姤 `No module named 'tushare'` 鐨勯棶棰橈紝骞惰ˉ鍏呭搴斿洖褰掓祴璇曘€?- 鈿欙笍 **`daily_analysis` 宸ヤ綔娴佽ˉ榻?`DEEPSEEK_API_KEY` 鏄犲皠** 鈥?GitHub Actions 姣忔棩鍒嗘瀽宸ヤ綔娴佺幇鍦ㄤ細姝ｇ‘閫忎紶 `DEEPSEEK_API_KEY`锛岄伩鍏嶄簯绔换鍔￠厤缃簡瀵嗛挜鍗村湪杩愯鏃舵嬁涓嶅埌瀵瑰簲鐜鍙橀噺銆?- 馃枼锔?**鍘嗗彶鍒楄〃杩囬暱鑲＄エ鍚嶇О鎴柇涓庢偓鍋滃睍绀?*锛坒ixes #815锛夆€?鍘嗗彶鍒楄〃涓繃闀跨殑鑲＄エ鍚嶇О, 鐜板湪浼氭寜瀛楃绫诲瀷鑷姩鎴柇锛堣嫳鏂?5/涓枃8/娣峰悎10瀛楃锛夛紝榛樿鏄剧ず鎴柇缁撴灉锛屾偓鍋滄椂灞曠ず瀹屾暣鍚嶇О锛涜В鍐?1920x1080 鍒嗚鲸鐜囦笅鑲＄エ鍚嶇О涓庡彸渚х姸鎬佹爣绛炬枃瀛楅噸鍙犵殑闂銆傛柊澧?`stockName.ts` 宸ュ叿鍑芥暟骞惰ˉ鍏呭搴旀祴璇曘€?
### 鏂囨。

- 馃Ь **README 鎹愯禒鍏ュ彛鏇存柊涓哄皬绾功浜岀淮鐮?* 鈥?README 鍙婁腑鑻辨枃璇存槑涓殑璧炲姪鍏ュ彛鏇存柊涓哄皬绾功浜岀淮鐮佺礌鏉愶紝淇濇寔灞曠ず鍙ｅ緞涓€鑷淬€?
## [3.10.1] - 2026-03-24

### 鏂板姛鑳?
- 馃敂 **Web 绔垎鏋愭帹閫侀€氱煡寮€鍏?*锛?808锛夆€?棣栭〉鍒嗘瀽鎸夐挳鏃佹柊澧炪€屾帹閫侀€氱煡銆嶅閫夋锛岄粯璁ゅ嬀閫夛紱鍙栨秷鍕鹃€夋椂鏈鍒嗘瀽涓嶅彂閫?Telegram/浼佷笟寰俊绛夋帹閫併€侫PI `POST /api/v1/analysis/analyze` 鏂板 `notify` 瀛楁锛坄bool`锛岄粯璁?`true`锛夛紝涓嶄紶鏃惰涓轰笌淇敼鍓嶄竴鑷达紝Bot 鍜屽畾鏃朵换鍔′笉鍙楀奖鍝嶃€?
### 鏀硅繘

- 馃枼锔?**闂偂 / 鍥炴祴椤甸潰甯冨眬涓庡３灞傚崗鍚屼紭鍖?* 鈥?缁熶竴 Chat / Backtest 椤甸潰瀹瑰櫒銆佸叡浜?UI 鐘舵€佸拰璺熼殢闂瓟浜や簰璺緞锛岀Щ闄ら儴鍒嗙‖缂栫爜楂樺害闄愬埗锛岃瀵艰埅妗嗘灦鍐呯殑濉厖涓庢粴鍔ㄨ涓烘洿杩炶疮銆?- 馃帹 **鍏ㄥ眬瑙嗚涓庡叡浜粍浠剁户缁敹鏁?* 鈥?Light theme 寮曞叆鍔ㄦ€?HSL 闃村奖浣撶郴锛岀粺涓€渚ц竟鏍忔縺娲绘€併€佸憡璀︾粍浠跺姣斿害鍜岃亰澶╂皵娉℃牱寮忥紝骞舵妸閮ㄥ垎闆舵暎鍐呰仈鏍峰紡鏀跺彛涓鸿涔夊寲 CSS 鍙橀噺锛屾彁鍗囦竴鑷存€т笌鍙淮鎶ゆ€с€?
### 淇

- 馃柤锔?**绯荤粺璁剧疆鏅鸿兘瀵煎叆鏂囦欢閫夋嫨鎭㈠** 鈥?淇浜嗏€滅郴缁熻缃?> 鍩虹璁剧疆 > 鏅鸿兘瀵煎叆鈥濇ā鍧椾腑 鈥滈€夋嫨鍥剧墖 / 閫夋嫨鏂囦欢鈥?涓や釜鎸夐挳鐐瑰嚮鏃犲搷搴旂殑闂銆?- 馃枼锔?**绉诲姩绔粴鍔ㄤ笌浜や簰灞傜骇淇** 鈥?瑙ｅ喅涓婚鍒囨崲鑿滃崟鍦ㄧЩ鍔ㄧ琚富鍐呭閬尅鐨?z-index 鍐茬獊锛屽苟鎭㈠棣栭〉闀挎姤鍛婂満鏅笅鐨勬甯哥旱鍚戞粴鍔紝涓嶅奖鍝嶅叾浠栭〉闈㈢幇鏈夋粴鍔ㄨ涓恒€?- 馃Ь **Markdown 绾枃鏈鍒舵竻娲楀寮?* 鈥?鏀硅繘绾枃鏈鍑虹畻娉曪紝澶嶅埗鍒嗘瀽鎶ュ憡鏃朵細鏇寸ǔ瀹氬湴娓呴櫎琛ㄦ牸鍒嗛殧绗︾瓑 Markdown 鐥曡抗锛屾彁鍗囧垎浜拰褰掓。鍐呭鐨勭函鍑€搴︺€?- 馃 **Trading philosophy injection 瑕嗙洊 legacy + Agent 鍏ㄩ摼璺?*锛?810锛夆€?`GeminiAnalyzer`銆佸崟 Agent 妯″紡鍜?skill-aware Prompt 鐜板湪鍏变韩鍚屼竴濂楃瓥鐣ユ敞鍏ョ姸鎬侊紱鍙湁闅愬紡鍥炶惤鍒板唴缃粯璁?`bull_trend` 鏃舵墠淇濈暀鏃х殑瓒嬪娍鍨嬫彁绀猴紝鏄惧紡绛栫暐閫夋嫨鎴栬嚜瀹氫箟榛樿 skill 涓嶅啀琚伔鍋峰彔鍔?`MA5>MA10>MA20` 澶氬ご鍩虹嚎銆?- 馃洜锔?**鍚庣 CI 渚濊禆瀹夎閾捐矾绋虫€佸寲**锛?835锛夆€?鎷嗗垎 backend gate 闃舵銆佷负渚濊禆瀹夎澧炲姞閲嶈瘯锛屽苟鎶?CI 鐢ㄧ殑 `litellm` 瀹夎鏉ユ簮璋冩暣涓烘洿绋冲畾鐨?GitHub 婧愶紝闄嶄綆渚濊禆瑙ｆ瀽鎶栧姩瀵艰嚧鐨?backend gate 鍋跺彂澶辫触銆?- 馃獰 **Windows 妗岄潰鍙戠増鏋勫缓鎭㈠ LiteLLM 瀹夎鍏煎鎬?* 鈥?`scripts/build-backend.ps1` 鐜板湪浼氬厛杩囨护 `requirements.txt` 涓殑 LiteLLM GitHub 婧愬寘锛屽啀涓嬭浇瀵瑰簲 tag 鐨?zipball 鍒版湰鍦扮Щ闄や笂娓稿彲閫?`enterprise/` 鐩綍鍚庡畨瑁咃紝缁曡繃 Windows runner 涓?Poetry 鏋勫缓 wheel 鏃舵妸鐩綍璇綋鏂囦欢鎵撳寘瀵艰嚧鐨勫け璐ワ紱鍚屾椂琛ヤ笂 `pip install` 閫€鍑虹爜妫€鏌ワ紝閬垮厤渚濊禆瀹夎澶辫触鍚庡彧鍦ㄥ悗缁?`python-multipart` 鏍￠獙闃舵鎵嶆毚闇叉垚娆＄敓鎶ラ敊銆?
### 娴嬭瘯

- 馃И **闂偂 / 鍥炴祴 / 鏅鸿兘瀵煎叆鍥炲綊瑕嗙洊琛ラ綈** 鈥?鍚屾鏇存柊 E2E 鍐掔儫鏈熸湜锛岃ˉ鍏?`DashboardStateBlock`銆丆hat 椤点€佹櫤鑳藉鍏ユ枃浠堕€夋嫨涓庣浉鍏充氦浜掑洖褰掓柇瑷€锛岀‘淇濊繎鏈?UI 璋冩暣鍚庣殑鍏抽敭璺緞浠嶅彲绋冲畾閫氳繃銆?
## [3.10.0] - 2026-03-24

### 鍙戝竷浜偣

- 馃攷 **鑷姩琛ュ叏涓庣储寮曞伐鍏锋墿灞曞埌涓夊競鍦?* 鈥?琛ュ叏绱㈠紩鐢熸垚閾捐矾鐜板湪鍚屾椂瑕嗙洊 A 鑲°€佹腐鑲°€佺編鑲★紝閰嶅鏂板 Tushare 鑲＄エ鍒楄〃鎶撳彇宸ュ叿涓庢洿瀹屾暣鐨勯潤鎬佺储寮曟暟鎹紝璁╅椤垫悳绱㈠叆鍙ｄ粠鈥滆兘鐢ㄢ€濊蛋鍚戔€滄洿鍏ㄣ€佹洿绋斥€濄€?- 馃枼锔?**Dashboard 涓庢姤鍛婃煡鐪嬩綋楠岀户缁敹鍙?* 鈥?棣栭〉 Dashboard 闈㈡澘銆佺姸鎬佽竟鐣屻€佸瓧浣撳眰绾у拰瀹屾暣鎶ュ憡琛ㄦ牸瀵嗗害瀹屾垚涓€杞粺涓€锛涙姤鍛婅鎯呬篃琛ラ綈浜?Markdown/绾枃鏈鍒朵笌鏇村彲闈犵殑鎸夐挳浜や簰锛屽噺灏戝巻鍙叉姤鍛婃煡鐪嬩笌鍒嗕韩鏃剁殑鎽╂摝銆?- 馃 **Agent skill 涓庡競鍦鸿涔夎竟鐣屾洿娓呮櫚** 鈥?skill bundle銆侀粯璁ょ瓥鐣ャ€佸洖娴嬫眹鎬昏涔夊拰鍏煎鎺ュ彛杩涗竴姝ユ敹鏁涳紱鍚屾椂鍒嗘瀽 Prompt 涓嶅啀榛樿鍐欐 A 鑲′笂涓嬫枃锛岀編鑲″拰娓偂鍒嗘瀽涔熻兘鎸夊悇鑷競鍦鸿鍒欑敓鎴愭洿璐村垏鐨勫唴瀹广€?- 鈴?**瀹氭椂涓庢闈㈤厤缃兘鍔涙洿璐磋繎鐪熷疄浣跨敤鍦烘櫙** 鈥?妗岄潰绔敮鎸?`.env` 瀵煎叆瀵煎嚭锛沗python main.py --schedule --stocks ...` 涔熶笉鍐嶆妸鍚姩鏃惰偂绁ㄥ揩鐓ч敊璇甫鍏ュ悗缁鍒掓墽琛岋紝瀹氭椂浠诲姟浼氳窡闅忔渶鏂颁繚瀛樼殑 `STOCK_LIST`銆?### 鏂板姛鑳?
- 馃捑 **妗岄潰绔?`.env` 澶囦唤/鎭㈠鍏ュ彛**锛?754锛夆€?妗岄潰妯″紡涓嬬殑绯荤粺璁剧疆椤垫柊澧?`瀵煎嚭 .env` / `瀵煎叆 .env` 鎸夐挳锛屽彲鐩存帴澶囦唤褰撳墠宸蹭繚瀛橀厤缃紝鎴栨妸澶囦唤鏂囦欢涓殑閿€煎悎骞舵仮澶嶅埌褰撳墠妗岄潰绔?`.env`锛涘鍏ユ部鐢ㄧ幇鏈?`config_version` 鍐茬獊淇濇姢涓庤繍琛屾椂閲嶈浇閾捐矾锛屼笉鏀瑰彉鐜版湁妗岄潰绔究鎼烘ā寮忚矾寰勩€?- 馃搳 **Tushare 鑲＄エ鍒楄〃鑾峰彇宸ュ叿** 鈥?鏂板 `scripts/fetch_tushare_stock_list.py`锛屾敮鎸佷粠 Tushare Pro 鑾峰彇 A鑲°€佹腐鑲°€佺編鑲″垪琛ㄤ俊鎭苟淇濆瓨涓?CSV锛岄厤鏈夊垎椤佃鍙栥€佹櫤鑳介檺娴併€侀敊璇鐞嗗拰杩涘害鎻愮ず锛涙柊澧炲搴斾娇鐢ㄦ枃妗?`docs/TUSHARE_STOCK_LIST_GUIDE.md`銆?- 馃攷 **绱㈠紩鐢熸垚鑴氭湰澶氬競鍦烘敮鎸?* 鈥?`generate_index_from_csv.py` 閲嶆瀯涓烘敮鎸?Tushare 鍜?AkShare 鍙屾暟鎹簮锛屽悓鏃惰鐩?A鑲°€佹腐鑲°€佺編鑲′笁涓競鍦猴紱鏂板鎸夊競鍦哄垎绫荤殑鍒悕鏄犲皠锛圓鑲°€佹腐鑲″父瑙佸埆鍚嶏紝缇庤偂甯哥敤鑲＄エ鑻辨枃缂╁啓锛夛紱娣诲姞 `--source` 鍙傛暟鍒囨崲鏁版嵁婧愩€乣--test` 鍙傛暟楠岃瘉妯″紡锛涗弗鏍艰繃婊ょ編鑲?DUMMY 璁板綍銆?- 馃攷 **绱㈠紩鐢熸垚鑴氭湰澧炲己** 鈥?`generate_stock_index.py` 鏂板 `--test`/`-t` 娴嬭瘯妯″紡鍜?`--verbose`/`-v` 璇︾粏杈撳嚭妯″紡锛屾坊鍔犲競鍦哄垎甯冪粺璁★紝浼樺寲 JSON 杈撳嚭鏍煎紡銆?- 馃搵 **棣栭〉瀹屾暣鎶ュ憡鏀寔鍙屾ā寮忓鍒?* 鈥?鍘嗗彶鎶ュ憡璇︽儏澶撮儴鏂板鈥滃鍒?Markdown 婧愮爜鈥濆拰鈥滃鍒剁函鏂囨湰鈥濆伐鍏锋寜閽紱鍓嶈€呬繚鐣欏師濮?Markdown 缁撴瀯锛屽悗鑰呭幓闄ゅ父瑙?Markdown 鏍煎紡绗﹀彿锛屾柟渚垮垎浜€佸綊妗ｅ拰璺ㄦ姤鍛婃瘮瀵广€傚鍒舵寜閽枃妗堜細璺熼殢 `REPORT_LANGUAGE` 淇濇寔涓嫳鏂囦竴鑷达紝閬垮厤鑻辨枃鎶ュ憡椤靛嚭鐜颁腑鏂囧浐瀹氭枃妗堛€?- 馃З **涓偂鍒嗘瀽椤佃ˉ榻愬叧鑱旀澘鍧楀睍绀?*锛?669锛夆€?A 鑲″垎鏋愬啓璺緞鐜板湪浼氭妸 `belong_boards` 涓€娆℃€у啓鍏?`fundamental_context` / `fundamental_snapshot`锛岀粨鏋勫寲鎶ュ憡璇︽儏鍚屾鏂板 `belong_boards` 涓?`sector_rankings` 瀛楁锛學eb 涓偂鍒嗘瀽椤甸灞忓彲鐩存帴灞曠ず鎵€灞炴澘鍧楀強鍏舵槸鍚﹀懡涓綋鏃ユ澘鍧楁定璺屾锛涙棤鏁版嵁鏃朵繚鎸?fail-open 闅愯棌锛屼笉褰卞搷鐜版湁鍒嗘瀽涓绘祦绋嬨€?
### 鏀硅繘

- 馃枼锔?**Dashboard 闈㈡澘缁熶竴鍖栵紙PR7-2锛?* 鈥?鏂板 `DashboardPanelHeader` 鍜?`DashboardStateBlock` 浣滀负鍘嗗彶銆佹姤鍛娿€佽祫璁€佷换鍔″拰閫忔槑搴︾瓑闈㈡澘鐨勯€氱敤缁勪欢锛涚粺涓€浜嗗悇闈㈡澘鏍囬灞傜骇銆佸姞杞?绌烘€?閿欒鎬佸拰 CSS 鍙橀噺 token銆?- 馃枼锔?**HomePage 鐘舵€佽竟鐣屾敹鍙ｏ紙PR7-2锛?* 鈥?寮曞叆 `useHomeDashboardState` hook锛岄泦涓?`stockPoolStore` 鐘舵€侀€夊彇閫昏緫锛岀Щ闄?`HomePage` 涓噸澶嶇殑鏈湴鐘舵€佹淳鐢熷拰鍥炶皟瀹氫箟銆?- 馃Л **Agent skill 缁熶竴鍒板崟涓€閰嶇疆璇箟** 鈥?Multi-Agent runtime銆丄PI銆乄eb chat 鍜岄厤缃厓鏁版嵁缁熶竴鍥寸粫 `skill` 姒傚康鏀舵暃锛沗/api/v1/agent/skills` 鎴愪负涓诲彂鐜板叆鍙ｏ紝`AGENT_SKILL_*` 鎴愪负涓婚厤缃潰锛屽唴缃?skill 鍏冩暟鎹篃寮€濮嬪０鏄庨粯璁ゅ惎鐢ㄣ€佹帓搴忎紭鍏堢骇銆乵arket regime tag 绛変俊鎭紝鍑忓皯榛樿绛栫暐鏁ｈ惤鍦ㄤ唬鐮侀噷鐨勯殣寮忚€﹀悎銆?- 馃攷 **鑷姩琛ュ叏绱㈠紩鏁版嵁鏇存柊** 鈥?閲嶆柊鐢熸垚 `stocks.index.json`锛屾兜鐩?A鑲°€佹腐鑲°€佺編鑲′笁涓競鍦猴紝鎻愬崌鑷姩琛ュ叏瑕嗙洊鐜囥€?- 馃Ь **Dashboard 瀛椾綋涓庡畬鏁存姤鍛婅〃鏍煎瘑搴﹀井璋?* 鈥?鏀舵暃棣栭〉渚ф爮銆佺┖鐘舵€併€佸巻鍙叉搷浣滃尯鐨勫瓧浣撳眰绾э紝骞跺皢瀹屾暣 Markdown 鎶ュ憡琛ㄦ牸 `th/td` 鐨勫唴杈硅窛璋冩暣鍒版洿绱у噾鐨?4-6px 鍖洪棿锛岃淇℃伅瀵嗗害涓庣幇鏈?Dashboard 瑙嗚鑺傚鏇翠竴鑷淬€?
### 淇

- 鈴?**瀹氭椂妯″紡涓嶅啀閿佸畾鍚姩鏃?CLI 鑲＄エ蹇収** 鈥?`python main.py --schedule --stocks ...` 鐜板湪涓嶄細璁╁悗缁鍒掓墽琛屾部鐢ㄥ惎鍔ㄦ椂鐨勬棫鑲＄エ鍒楄〃锛涘畾鏃朵换鍔℃瘡娆¤Е鍙戝墠閮戒細閲嶆柊璇诲彇鏈€鏂颁繚瀛樼殑 `STOCK_LIST`锛岀‘淇?WebUI 鎴?`.env` 鏇存柊鍚庣殑鑷€夎偂閰嶇疆鑳藉弬涓庡悗缁帹閫併€?- 馃實 **LLM Prompt 鎸夎偂绁ㄥ競鍦哄姩鎬佹敞鍏ヤ笂涓嬫枃** 鈥?鍒嗘瀽閾捐矾涓嶅啀鎶婂競鍦鸿鍒欏啓姝绘垚 A 鑲★紱绯荤粺 Prompt 浼氭牴鎹偂绁ㄤ唬鐮佽瘑鍒?A 鑲°€佹腐鑲℃垨缇庤偂锛屽苟娉ㄥ叆瀵瑰簲鐨勮鑹叉弿杩颁笌浜ゆ槗瑙勫垯鎻愮ず锛屽噺灏戣法甯傚満鍒嗘瀽鍑虹幇鍙ｅ緞閿欎綅鎴栫粨璁哄け鐪熺殑闂銆?- 馃攷 **缇庤偂鑷姩琛ュ叏澶嶇敤 ticker 鍘婚噸** 鈥?`generate_index_from_csv.py` 鍦ㄥ鍏?Tushare `us_basic` CSV 鏃朵細鍏堟寜 `ts_code` 鎶樺彔澶嶇敤鐨勭編鑲?ticker锛屼紭鍏堜繚鐣欐洿鍙兘浠嶅湪浣跨敤鐨勮褰曪紝閬垮厤 `stocks.index.json` 鍑虹幇閲嶅 `canonicalCode` 鍚庤 Web 鑷姩琛ュ叏灞曠ず鍘嗗彶鍚嶇О鎴栨彁浜ゆ涔変唬鐮併€?- 馃Ь **Web 鎶ュ憡璇︽儏澶嶅埗浜や簰绋冲畾鎬т慨澶?*锛?749锛夆€?`ReportDetails` 涓€滃師濮嬪垎鏋愮粨鏋?/ 鍒嗘瀽蹇収鈥濈殑澶嶅埗鎸夐挳琛ラ綈鍙偣鍑诲眰绾э紝閬垮厤琚笅鏂?JSON 鍐呭瑕嗙洊锛涗袱涓潰鏉跨殑澶嶅埗鎻愮ず涔熸敼涓哄悇鑷嫭绔嬶紝涓嶅啀鍑虹幇澶嶅埗涓€涓悗涓や釜鎸夐挳鍚屾椂鏄剧ず鈥滃凡澶嶅埗鈥濈殑璇鍙嶉銆?- 馃搳 **Agent skill 鍥炴祴涓庡吋瀹规帴鍙ｈ涔夋敹鏁?* 鈥?`get_skill_backtest_summary` 鐜板湪瑕佹眰鏄惧紡浼犲叆 `skill_id`锛岀己澶辨椂杩斿洖鏄庣‘鏍￠獙鎻愮ず锛涗粨搴撳皻鏈寔涔呭寲鐪熷疄 skill 绾ф眹鎬绘椂浼氳繑鍥炴槑纭殑 unsupported/info 鍝嶅簲锛屽苟淇濈暀 `normalized` 涓?`*_pct` 鍏煎瀛楁锛岄伩鍏嶆部鐢?overall 鎸囨爣璇 Agent 鎴栫敤鎴枫€?- 馃敡 **Skill 榛樿閫夋嫨涓庡吋瀹瑰眰琛屼负鍔犲浐** 鈥?`allowed-tools` 浼氱户缁粎浣滀负 `SKILL.md` bundle 鍏冩暟鎹繚鐣欙紝涓嶅啀娉勯湶鍒拌繍琛屾椂宸ュ叿閫夋嫨锛沗/api/v1/agent/strategies` 鎭㈠鏃?payload 褰㈢姸锛涙樉寮忎紶鍏?`skills: []` 鏃朵細娓呯┖闄堟棫涓婁笅鏂囷紱褰撶敤鎴锋槑纭€夋嫨绛栫暐 skill 鏃朵笉鍐嶅伔鍋峰彔鍔犻粯璁?bull-trend锛岃€屽湪 `AGENT_SKILLS` 涓虹┖鏃跺垯缁熶竴鍙洖钀藉埌鍗曚竴涓婚粯璁?skill銆?
### 娴嬭瘯

- 馃И **Dashboard 缁勪欢娴嬭瘯瑕嗙洊鐜囨墿灞曪紙PR7-2锛?* 鈥?鏂板 `ReportNews` 鍜?`TaskPanel` 娴嬭瘯锛涘 `HistoryList`銆乣ReportDetails`銆乣HomePage`銆乣useDashboardLifecycle` 鍜?`stockPoolStore` 澧炲己浜嗘柇瑷€瑕嗙洊锛屽寘鎷垹闄ゅ洖閫€銆佺Щ鍔ㄧ鎶藉眽鍜屼换鍔＄敓鍛藉懆鏈熺瓑鍦烘櫙銆?- 馃И **澶氬競鍦虹储寮曠敓鎴愭祴璇曡ˉ榻?* 鈥?鏂板 `tests/test_generate_index_from_csv.py`锛岃鐩?Tushare/AkShare 鍙屾暟鎹簮瑙ｆ瀽銆佸甯傚満鍒ゆ柇銆佺編鑲?DUMMY 杩囨护涓庨噸澶?ticker 鍘婚噸绛夋牳蹇冭矾寰勩€?- 馃И **鍏宠仈鏉垮潡鍐欏叆涓?API 濂戠害鍥炲綊** 鈥?鏂板 `tests/test_pipeline_related_boards.py`锛屽苟琛ュ厖鍒嗘瀽鍘嗗彶涓庡垎鏋愭帴鍙ｅ绾︽祴璇曪紝纭繚 `belong_boards` / `sector_rankings` 鍙仛澧為噺鎵╁睍涓斾繚鎸?fail-open銆?- 馃И **瀹氭椂妯″紡鑲＄エ鍒楄〃璇箟鍥炲綊娴嬭瘯** 鈥?鏂板 `tests/test_main_schedule_mode.py`锛岃鐩栧畾鏃舵ā寮忓拷鐣ュ惎鍔ㄦ椂 `--stocks` 蹇収銆佸崟娆¤繍琛屼粛淇濈暀 CLI 鑲＄エ瑕嗙洊鐨勮竟鐣屽満鏅€?
### 鏂囨。

- 馃摌 **鏂板 Tushare 鑲＄エ鍒楄〃宸ュ叿鏂囨。** 鈥?鏂板 `docs/TUSHARE_STOCK_LIST_GUIDE.md`锛岃鏄庤偂绁ㄥ垪琛ㄦ姄鍙栧伐鍏风殑浣跨敤鏂规硶銆佹暟鎹牸寮忓拰甯歌闂銆?- 馃實 **琛ラ綈瀹氭椂妯″紡涓庡叧鑱旀澘鍧楃殑鍙岃璇存槑** 鈥?`docs/full-guide.md` / `docs/full-guide_EN.md` 鐜板湪鏄庣‘璇存槑 scheduled mode 浼氬湪姣忔鎵ц鍓嶉噸鏂拌鍙?`STOCK_LIST`锛屽苟鍚屾琛ュ厖涓偂鍏宠仈鏉垮潡灞曠ず鑳藉姏璇存槑锛屽噺灏戦厤缃鏈熷亸宸€?- 馃Л **璋冩暣 Agent 鏈鍏煎鏂囨** 鈥?README銆佸弻璇枃妗ｃ€佽缃〉涓庨棶鑲＄晫闈㈢户缁互鈥滅瓥鐣モ€濅綔涓虹敤鎴峰叆鍙ｄ富绉板懠锛屽悓鏃惰ˉ鍏?`skill` 浣滀负鍐呴儴缁熶竴鍛藉悕锛岄檷浣庤縼绉绘湡鐞嗚В鎴愭湰銆?
## [3.9.0] - 2026-03-20

### 鍙戝竷浜偣

- 馃 **妯″瀷閾捐矾涓庢姤鍛婅瑷€鏇寸伒娲?* 鈥?Agent 鐜板湪鍙互閫氳繃 `AGENT_LITELLM_MODEL` 鐙珛閫夋嫨妯″瀷閾捐矾锛屾櫘閫氬垎鏋愪笌 Agent 鎶ュ憡涔熷彲閫氳繃 `REPORT_LANGUAGE=zh|en` 杈撳嚭缁熶竴璇█锛屽噺灏戔€滆嫳鏂囧唴瀹?+ 涓枃澹冲瓙鈥濊繖绫绘贩鎺掗棶棰橈紝骞跺厑璁稿洟闃熷垎鍒潈琛′富鍒嗘瀽涓?Agent 鐨勬垚鏈€侀€熷害鍜岃兘鍔涖€?- 馃攷 **棣栭〉鍒嗘瀽浣撻獙瀹屾垚涓€杞棴鐜紭鍖?* 鈥?棣栭〉鏂板 A 鑲¤嚜鍔ㄨˉ鍏紝鏀寔浠ｇ爜銆佷腑鏂囧悕銆佹嫾闊冲拰鍒悕妫€绱紱鍚屾椂 Dashboard 鐘舵€佹敹鍙ｅ埌缁熶竴 store锛屽巻鍙层€佹姤鍛娿€佹柊闂讳笌 Markdown 鎶藉眽鐨勪氦浜掓洿绋冲畾锛屸€淎sk AI鈥?杩介棶涔熶細浼樺厛鎼哄甫褰撳墠鎶ュ憡涓婁笅鏂囥€?- 馃挰 **閫氱煡涓庢绱㈣兘鍔涚户缁鎵?* 鈥?鏂板 Slack 涓€绛夐€氱煡娓犻亾锛汼earXNG 鍦ㄦ湭閰嶇疆鑷缓瀹炰緥鏃跺彲浠ヨ嚜鍔ㄥ彂鐜板叕鍏卞疄渚嬪苟鎸夊彈鎺ц疆璇㈤檷绾э紱Tavily 鏃舵晥鏂伴椈閾捐矾淇鍚庯紝涓ユ牸鏃舵晥杩囨护涓嶅啀閿欒涓㈠厜鏈夋晥缁撴灉銆?- 馃捈 **鎸佷粨涓庡競鍦哄鐩橀摼璺洿绋?* 鈥?A 鑲?market review 鍙€夋帴鍏?TickFlow 寮哄寲鎸囨暟涓庢定璺岀粺璁★紱鎸佷粨璐︽湰鍐欏叆鏀逛负涓茶鍖栦互缂╁皬骞跺彂瓒呭崠绐楀彛锛涙眹鐜囧埛鏂板叆鍙ｅ拰绂佺敤鎬佹彁绀轰篃鏇村姞娓呮櫚锛屽噺灏戠敤鎴疯鍒ゃ€?
### 鏂板姛鑳?
- 馃攷 **Web 鑲＄エ鑷姩琛ュ叏 MVP** 鈥?棣栭〉鍒嗘瀽杈撳叆妗嗘柊澧炴湰鍦扮储寮曢┍鍔ㄧ殑鑷姩琛ュ叏锛屾敮鎸佽偂绁ㄤ唬鐮併€佷腑鏂囧悕銆佹嫾闊冲拰鍒悕鍖归厤锛涢€変腑鍊欓€夊悗浼氭彁浜?canonical code锛屽苟閫忎紶 `stock_name`銆乣original_query`銆乣selection_source` 鍒板垎鏋愯姹傘€佷换鍔＄姸鎬佸拰 SSE 浜嬩欢锛涚储寮曞姞杞藉け璐ユ椂鑷姩閫€鍥炴棫杈撳叆妯″紡锛屼笉闃绘柇鍘熸湁鎻愪氦娴佺▼銆傚悓姝ヨˉ鍏呬簡闈欐€佺储寮曞姞杞藉櫒銆佺储寮曠敓鎴愯剼鏈拰鍓嶅悗绔绾︽祴璇曘€傚垎闃舵杩涜寮€鍙戯紝绗竴闃舵浠呮敮鎸?A 鑲°€?- 馃挰 **Slack 涓€绛夐€氱煡娓犻亾** 鈥?鏂板 Slack 鍘熺敓閫氱煡鏀寔锛屽悓鏃舵敮鎸?Bot Token 鍜?Incoming Webhook 涓ょ鎺ュ叆鏂瑰紡锛涘悓鏃堕厤缃椂浼樺厛浣跨敤 Bot API锛岀‘淇濇枃鏈笌鍥剧墖鍙戦€佸埌鍚屼竴棰戦亾锛汢ot Token 妯″紡鏀寔鍥剧墖涓婁紶锛坮aw body POST锛屼笉浣跨敤 multipart锛夛紱鏂板 `SLACK_BOT_TOKEN`銆乣SLACK_CHANNEL_ID`銆乣SLACK_WEBHOOK_URL` 閰嶇疆椤癸紝GitHub Actions 宸ヤ綔娴佸悓姝ヨˉ榻愬搴?Secrets 浼犻€掋€?- 馃實 **鎶ュ憡杈撳嚭璇█鍙厤缃?*锛圛ssue #758锛夆€?鏂板 `REPORT_LANGUAGE=zh|en`锛岄粯璁?`zh`锛涜瑷€璁剧疆浼氬悓姝ユ敞鍏ユ櫘閫氬垎鏋愪笌 Agent Prompt锛屽苟瑕嗙洊 Markdown/Jinja 妯℃澘銆侀€氱煡 fallback銆佸巻鍙?API `report_language` 鍏冩暟鎹強 Web 鎶ュ憡椤靛浐瀹氭枃妗堬紝閬垮厤鈥滆嫳鏂囧唴瀹?+ 涓枃澹冲瓙鈥濈殑娣峰悎杈撳嚭銆?- 馃殌 **Agent 涓庢櫘閫氬垎鏋愭ā鍨嬭В鑰?*锛圛ssue #692锛夆€?鏂板 `AGENT_LITELLM_MODEL`锛堢暀绌虹户鎵?`LITELLM_MODEL`锛屾棤鍓嶇紑鎸?`openai/<model>` 褰掍竴锛夛紱Agent 鎵ц閾捐矾涓?`/api/v1/agent/models` 鐨?`is_primary/is_fallback` 鏍囪鏀逛负鍩轰簬 Agent 瀹為檯妯″瀷閾捐矾锛涚郴缁熼厤缃笌鍚姩鏈熸牎楠岃ˉ榻?`AGENT_LITELLM_MODEL` 鐨?`unknown_model/missing_runtime_source` 妫€鏌ワ紱Web 璁剧疆椤垫柊澧?Agent 涓绘ā鍨嬮€夋嫨骞朵笌娓犻亾妯″紡杩愯鏃堕厤缃悓姝ャ€?- 馃攷 **SearXNG 鍏叡瀹炰緥鑷姩鍙戠幇涓庡彈鎺ц疆璇?*锛?752锛夆€?鏂板 `SEARXNG_PUBLIC_INSTANCES_ENABLED`锛屽湪鏈厤缃?`SEARXNG_BASE_URLS` 鏃堕粯璁や粠 `searx.space` 鎷夊彇鍏叡瀹炰緥鍒楄〃锛屽苟鎸夊彈鎺ц疆璇㈤『搴忛€夋嫨瀹炰緥锛涘悓娆¤姹傚唴閬囧埌瓒呮椂銆佽繛鎺ラ敊璇€丠TTP 闈?200 鎴栨棤鏁?JSON 浼氳嚜鍔ㄥ垏鎹㈠埌涓嬩竴涓疄渚嬨€傚凡閰嶇疆鑷缓瀹炰緥鐨勭敤鎴蜂繚鎸佸師鏈変紭鍏堢骇涓庤涔変笉鍙橈紱`daily_analysis` GitHub Actions 宸ヤ綔娴佷篃宸叉敮鎸佹樉寮忛€忎紶璇ュ紑鍏冲苟鍦ㄥ惎鍔ㄦ棩蹇椾腑灞曠ず褰撳墠鐘舵€併€?- 馃搱 **TickFlow market review enhancement** (#632) 鈥?鏂板鍙€?`TICKFLOW_API_KEY`锛涢厤缃悗锛孉 鑲″ぇ鐩樺鐩樼殑涓昏鎸囨暟琛屾儏浼樺厛灏濊瘯 TickFlow锛涜嫢褰撳墠 TickFlow 濂楅鏀寔鏍囩殑姹犳煡璇紝甯傚満娑ㄨ穼缁熻涔熶細浼樺厛灏濊瘯 TickFlow銆傚け璐ユ垨鏉冮檺涓嶈冻鏃剁珛鍗冲洖閫€鍒扮幇鏈?`AkShare / Tushare / efinance` 閾捐矾锛涙澘鍧楁定璺屾鍥為€€椤哄簭淇濇寔涓嶅彉銆傛帴鍏ュ眰鍚屾椂閫傞厤浜嗙湡瀹?SDK 濂戠害锛氫富鎸囨暟鏌ヨ鎸夊崟娆¤姹備笂闄愬垎鎵规媺鍙栵紝骞跺皢 TickFlow 杩斿洖鐨勬瘮渚嬪瀷 `change_pct` / `amplitude` 缁熶竴杞崲涓洪」鐩唴閮ㄧ殑鐧惧垎姣斿彛寰勩€?
### 鏀硅繘

- **Dashboard state slice and workspace closure** 鈥?moved Home / Dashboard state into `stockPoolStore`, consolidated history selection, report loading, task syncing, polling refresh, and markdown drawer handling under a single state slice.
- **Dashboard panel standardization** 鈥?kept the current dashboard layout contract stable while unifying history, report, news, and markdown presentation with shared tokens, standardized states, and bounded in-panel scrolling for the history list.
- **Dashboard-to-chat follow-up bridge** 鈥?routed 鈥淎sk AI鈥?follow-ups through report-context hydration instead of direct cross-page state coupling, while keeping chat sends usable when enriched history context is still loading.
- 馃捈 **鎸佷粨璐︽湰骞跺彂鍐欏叆涓茶鍖?*锛?742锛夆€?鎸佷粨婧愪簨浠跺啓鍏?鍒犻櫎鐜板湪浼氬湪 SQLite 涓嬪厛鑾峰彇涓茶鍖栧啓閿侊紝鍑忓皯骞跺彂鍗栧嚭鎶婅秴鍞祦姘村啓鍏ヨ处鏈殑绐楀彛锛涚洿鎺ユ寔浠撳啓鎺ュ彛鍦ㄩ攣绔炰簤鏃惰繑鍥?`409 portfolio_busy`锛孋SV 瀵煎叆淇濇寔閫愭潯鎻愪氦骞舵妸 busy 璁″叆 `failed_count`銆?- 馃挶 **鎸佷粨椤垫眹鐜囨墜鍔ㄥ埛鏂板叆鍙ｈˉ榻?*锛?748锛夆€?Web `/portfolio` 椤甸潰鐜板湪浼氬湪鈥滄眹鐜囩姸鎬佲€濆崱鐗囦腑灞曠ず鈥滃埛鏂版眹鐜団€濇寜閽紝鐩存帴璋冪敤鐜版湁 `POST /api/v1/portfolio/fx/refresh` 鎺ュ彛锛涘埛鏂板悗浼氫粎閲嶈浇蹇収涓庨闄╂暟鎹紝骞朵互鍐呰仈鎽樿鍙嶉鈥滃凡鏇存柊 / 浠?stale / 鍒锋柊澶辫触鈥濈殑缁撴灉锛屽噺灏戠敤鎴峰 `fxStale` 闀挎椂闂村仠鐣欑殑璇В銆?
### 淇

- 馃攷 **Web 鑷姩琛ュ叏 Enter 鎻愪氦璇箟淇** 鈥?鑲＄エ鑷姩琛ュ叏鍦ㄦ悳绱㈠懡涓€欓€夋椂涓嶅啀榛樿楂樹寒绗竴椤癸紱鍊欓€夊垪琛ㄥ睍寮€浣嗙敤鎴峰皻鏈敤鏂瑰悜閿垨榧犳爣鏄庣‘閫変腑鏃讹紝鎸?Enter 浼氱户缁彁浜ゅ師濮嬭緭鍏ワ紝閬垮厤鎵嬪姩杈撳叆琚涓€鏉″€欓€夐潤榛樿鐩栥€?- 馃實 **琛ラ綈 `REPORT_LANGUAGE` 鍚姩瑙ｆ瀽涓庡巻鍙插睍绀烘湰鍦板寲杈圭晫** 鈥?`Config` 鍦ㄥ惎鍔ㄦ椂缁х画閬靛惊鈥滅湡瀹炵幆澧冨彉閲忎紭鍏堛€乣.env` 鍏滃簳鈥濈殑鏃㈡湁璇箟锛屽苟鍦ㄤ袱鑰呭啿绐佹椂杈撳嚭鏄惧紡鍛婅锛屽噺灏?`REPORT_LANGUAGE` 鏉ユ簮涓嶆竻甯︽潵鐨勮鍒わ紱鍚屾椂 `/api/v1/history/{id}` 鑻辨枃璇︽儏鍝嶅簲浼氬悓姝ユ湰鍦板寲 `sentiment_label`锛屽巻鍙?Markdown 涔熶細姝ｇ‘璇嗗埆鑻辨枃 `bias_status` 鐨勯闄╃瓑绾?emoji锛岄伩鍏嶅嚭鐜?`涔愯` 鎴?`馃毃Safe` 杩欑被涓嫳娣锋帓/璇姤灞曠ず銆?- 馃摪 **Tavily 鏃舵晥鏂伴椈妫€绱㈠彂甯冩椂闂存槧灏勪慨澶?*锛?782锛夆€?Tavily 鍦ㄨ偂绁ㄦ柊闂诲拰涓ユ牸鏃舵晥鐨勬儏鎶ョ淮搴︿腑鐜板湪浼氭樉寮忎娇鐢?`topic="news"`锛屽苟鍏煎 `published_date` / `publishedDate` 涓ょ鍙戝竷鏃堕棿瀛楁锛涗慨澶嶄簡 Tavily 鏄庢槑杩斿洖缁撴灉鍗村湪鍚庣画纭繃婊ら樁娈佃鍏ㄩ儴璁颁负 `drop_unknown` 涓㈠純鐨勯棶棰橈紝鍚屾椂灏嗘満鏋勫垎鏋愩€佷笟缁╅鏈熴€佽涓氬垎鏋愮瓑鍒嗘瀽鍨嬬淮搴︽仮澶嶄负瀹芥簮鎼滅储锛屼笉鍐嶈缁熶竴鍘嬬缉鎴愭柊闂绘ā寮忋€?- 馃挶 **鎸佷粨椤垫眹鐜囧埛鏂扮鐢ㄨ涔変慨姝?*锛?772锛夆€?褰?`PORTFOLIO_FX_UPDATE_ENABLED=false` 鏃讹紝`POST /api/v1/portfolio/fx/refresh` 鐜板湪浼氳繑鍥炴樉寮?`refresh_enabled=false` 涓?`disabled_reason`锛學eb `/portfolio` 椤甸潰浼氭槑纭彁绀衡€滄眹鐜囧湪绾垮埛鏂板凡琚鐢ㄢ€濓紝涓嶅啀璇姤鈥滃綋鍓嶈寖鍥存棤鍙埛鏂扮殑姹囩巼瀵光€濄€?- 馃 **Agent timeout and config hardening** 鈥?`AGENT_ORCHESTRATOR_TIMEOUT_S` now also protects the legacy single-agent ReAct loop, parallel tool batches stop waiting once the remaining budget is exhausted, and invalid numeric `.env` values fall back to safe defaults with warnings instead of crashing startup.
- 馃寪 **CORS wildcard + credentials compatibility** 鈥?`CORS_ALLOW_ALL=true` no longer combines `allow_origins=["*"]` with credentialed requests, avoiding browser-side cross-origin failures in demo/development setups.
- 馃Л **Unavailable Agent settings hidden from Web UI** 鈥?Deep Research / Event Monitor controls are now treated as compatibility-only metadata in the current branch and are removed from the Settings page to avoid exposing non-functional toggles.

### 鏂囨。

- 鏂板 Ollama 鏈湴妯″瀷閰嶇疆璇存槑锛屽悓姝ユ洿鏂?`README.md` 涓?`docs/README_EN.md`锛團ixes #690锛?- 瀹屽杽 Ollama 閰嶇疆璇存槑锛歚docs/full-guide.md` / `docs/full-guide_EN.md` 鐜鍙橀噺琛ㄤ笌 Note 琛ュ厖 `OLLAMA_API_BASE`锛岄伩鍏嶈嫳鏂囩敤鎴疯浠ヤ负 Ollama 涓嶈兘浣滀负鐙珛閰嶇疆鍏ュ彛锛涘悎骞堕噸澶嶇殑 `OLLAMA_API_BASE` 鏉＄洰涓哄崟涓€鏉＄洰
- 鏄庣‘鏂囨。鍚屾娌荤悊杈圭晫锛氳ˉ鍏?`README.md`銆佷笓棰樻枃妗ｃ€佸弻璇枃妗ｄ笌浜や粯璇存槑涔嬮棿鐨勯粯璁ゅ悓姝ヨ鍒欙紝鍑忓皯鍚庣画鏂囨。婕傜Щ

## [3.8.0] - 2026-03-17

### 鍙戝竷浜偣

- 馃帹 **Web 鐣岄潰瀹屾垚涓€杞鏋跺崌绾?* 鈥?鏂扮殑 App Shell銆佷晶杈瑰鑸€佷富棰樿兘鍔涖€佺櫥褰曚笌绯荤粺璁剧疆娴佺▼宸茬粡涓叉垚缁熶竴浣撻獙锛屾闈㈢鍔犺浇鑳屾櫙涔熷畬鎴愬榻愩€?- 馃搱 **鍒嗘瀽涓婁笅鏂囩户缁ˉ寮?* 鈥?缇庤偂鏂板绀句氦鑸嗘儏鎯呮姤锛孉 鑲¤ˉ榻愯储鎶ヤ笌鍒嗙孩缁撴瀯鍖栦笂涓嬫枃锛孴ushare 鏂版帴鍏ョ鐮佸垎甯冨拰琛屼笟鏉垮潡娑ㄨ穼鏁版嵁銆?- 馃敀 **杩愯绋冲畾鎬т笌閰嶇疆鍏煎鎬ф彁鍗?* 鈥?閫€鍑虹櫥褰曚細绔嬪嵆璁╂棫浼氳瘽澶辨晥锛屽畾鏃跺惎鍔ㄥ吋瀹规棫閰嶇疆锛岃繍琛屼腑鐨?`MAX_WORKERS` 璋冩暣鍜屾柊闂绘椂鏁堢獥鍙ｅ弽棣堟洿娓呮櫚銆?- 馃捈 **鎸佷粨绾犻敊閾捐矾鏇村畬鏁?* 鈥?瓒呭敭浼氳鍓嶇疆鎷︽埅锛岄敊璇氦鏄?璧勯噾娴佹按/鍏徃琛屼负鍙互鐩存帴鍒犻櫎鍥炴粴锛屼究浜庝慨澶嶈剰鏁版嵁銆?
### 鏂板姛鑳?
- 馃摫 **缇庤偂绀句氦鑸嗘儏鎯呮姤** 鈥?鏂板 Reddit / X / Polymarket 绀句氦濯掍綋鎯呯华鏁版嵁婧愶紝涓虹編鑲″垎鏋愭彁渚涘疄鏃剁ぞ浜ょ儹搴︺€佹儏缁瘎鍒嗗拰鎻愬強閲忕瓑琛ュ厖鎸囨爣锛涘畬鍏ㄥ彲閫夛紝浠呭湪閰嶇疆 `SOCIAL_SENTIMENT_API_KEY` 鍚庡缇庤偂鐢熸晥銆?- 馃搳 **A 鑲¤储鎶ヤ笌鍒嗙孩缁撴瀯鍖栧寮?*锛圛ssue #710锛夆€?`fundamental_context.earnings.data` 鏂板 `financial_report` 涓?`dividend` 瀛楁锛涘垎绾㈢粺涓€鎸夆€滀粎鐜伴噾鍒嗙孩銆佺◣鍓嶅彛寰勨€濊绠楋紝骞惰ˉ鍏?`ttm_cash_dividend_per_share` 涓?`ttm_dividend_yield_pct`锛涘垎鏋?鍘嗗彶 API 鐨?`details` 杩藉姞 `financial_report`銆乣dividend_metrics` 鍙€夊瓧娈碉紝淇濇寔 fail-open 涓庡悜鍚庡吋瀹广€?- 馃攳 **鎺ュ叆 Tushare 绛圭爜涓庤涓氭澘鍧楁帴鍙?* 鈥?鏂板绛圭爜鍒嗗竷銆佽涓氭澘鍧楁定璺屾暟鎹幏鍙栬兘鍔涳紝骞剁粺涓€绾冲叆閰嶇疆鍖栨暟鎹簮浼樺厛绾э紱榛樿鎸変笂娴锋椂闂村尯鍒嗙洏涓?鐩樺悗浜ゆ槗鏃ュ彇鏁帮紝浼樺厛浣跨敤 Tushare 鍚岃姳椤烘帴鍙ｏ紝蹇呰鏃堕檷绾у埌涓滆储銆?- 馃П **Web UI 鍩虹楠ㄦ灦鍗囩骇** 鈥?閲嶅缓鍏变韩璁捐浠ょ墝涓庨€氱敤缁勪欢锛屾柊澧?App Shell銆乀heme Provider銆佷晶杈瑰鑸紝骞跺悓姝ヨ皟鏁?Electron 鍔犺浇鑳屾櫙锛屼负 Web / Desktop 鐨勭粺涓€浣撻獙鎵撳簳銆?- 馃攼 **鐧诲綍涓庣郴缁熻缃祦绋嬮噸鍋?* 鈥?閲嶆瀯 Login銆丼ettings 涓?Auth 绠＄悊娴佺▼锛岃ˉ涓婃樉寮忕殑璁よ瘉 setup-state 澶勭悊锛屽苟璁?Web 绔笌杩愯鏃惰璇侀厤缃?API 琛屼负瀵归綈銆?- 馃И **鍓嶇鍥炲綊涓庡啋鐑熻鐩栬ˉ寮?* 鈥?鏂板骞舵墿灞曠櫥褰曘€侀椤点€佽亰澶┿€佺Щ鍔ㄧ Shell銆佽缃〉銆佸洖娴嬪叆鍙ｇ瓑鍏抽敭璺緞鐨勭粍浠舵祴璇曚笌 Playwright smoke coverage銆?
### 鍙樻洿

- 馃Л **椤甸潰鎺ュ叆鏂?Shell 甯冨眬濂戠害** 鈥?Home銆丆hat銆丼ettings銆丅acktest 宸茬粺涓€鎺ュ叆鏂扮殑椤甸潰瀹瑰櫒銆佹娊灞夊拰婊氬姩绾﹀畾锛岄檷浣?UI 杩佺Щ鏈熼棿鐨勯〉闈㈣涓轰笉涓€鑷淬€?- 馃捑 **璁剧疆椤电姸鎬佸悓姝ユ洿绋?* 鈥?浼樺寲鑽夌淇濈暀銆佺洿鎺ヤ繚瀛樺悓姝ヤ笌鍐茬獊澶勭悊锛屽噺灏戞ā鍧楃骇淇濆瓨鍚庡墠鍚庣閰嶇疆鐘舵€佷笉涓€鑷寸殑闂銆?- 馃幁 **鐧诲綍椤佃瑙夊熀绾垮洖褰?* 鈥?鐧诲綍椤垫仮澶嶅埌鏃㈡湁 `006` 鍒嗘敮鐨勮瑙夊熀绾匡紝鍚屾椂淇濈暀鏂扮殑璁よ瘉鐘舵€侀€昏緫鍜岀粺涓€琛ㄥ崟浜や簰妯″瀷銆?- 馃彌锔?**AI 鍗忎綔娌荤悊璧勪骇鍔犲浐** 鈥?鏀舵暃骞跺姞寮?`AGENTS.md`銆乣CLAUDE.md`銆丆opilot 鎸囦护鍜屾牎楠岃剼鏈殑涓€鑷存€х害鏉燂紝闄嶄綆娌荤悊璧勪骇闀挎湡婕傜Щ椋庨櫓銆?
### Added

- **Web UI foundation refresh** 鈥?rebuilt shared design tokens and common primitives, introduced the app shell, theme provider, sidebar navigation, and Electron loading background alignment for the upgraded desktop/web experience
- **Settings and auth workflow overhaul** 鈥?rebuilt the Login, Settings, and Auth management flows, added explicit auth setup-state handling, and aligned the Web UI with the runtime auth configuration APIs
- **UI regression coverage and smoke checks** 鈥?expanded targeted frontend tests and added Playwright smoke coverage for login, home, chat, mobile shell, settings, and backtest entry flows

### Changed

- **Shell-driven page integration** 鈥?aligned Home, Chat, Settings, and Backtest with the new shell layout contract so routing, drawer behavior, and page-level scrolling are consistent during the UI migration
- **Settings state consistency** 鈥?refined draft preservation, direct-save synchronization, and conflict handling so module-level saves no longer leave the page out of sync with backend config state
- **Login visual baseline** 鈥?restored the login page visual treatment to the established `006` branch baseline while keeping the newer auth-state logic and unified form interaction model

### 淇

- 鈴?**瀹氭椂鍚姩绔嬪嵆鎵ц鍏煎鏃ч厤缃?*锛圛ssue #726锛夆€?`SCHEDULE_RUN_IMMEDIATELY` 鏈缃椂浼氬洖閫€璇诲彇 `RUN_IMMEDIATELY`锛屼慨澶嶅崌绾у悗鏃?`.env` 鍦ㄥ畾鏃舵ā寮忎笅鐨勫吋瀹规€ч棶棰橈紱鍚屾椂婢勬竻 `.env.example` / README 涓袱涓厤缃」鐨勯€傜敤鑼冨洿锛屽苟娉ㄦ槑 Outlook / Exchange 寮哄埗 OAuth2 鏆備笉鏀寔銆?- 馃У **杩愯鏈?`MAX_WORKERS` 閰嶇疆鐢熸晥涓庡彲瑙ｉ噴鎬у寮?*锛?633锛夆€?淇寮傛鍒嗘瀽闃熷垪鏈寜 `MAX_WORKERS` 鍚屾鐨勯棶棰橈紱鏂板浠诲姟闃熷垪骞跺彂 in-place 鍚屾鏈哄埗锛堢┖闂插嵆鏃剁敓鏁堛€佺箒蹇欏欢鍚庯級锛屽苟鍦ㄨ缃繚瀛樺弽棣堜笌杩愯鏃ュ織涓槑纭緭鍑?`profile/max/effective`锛屽噺灏戔€滃弬鏁版湭鐢熸晥鈥濊瑙ｃ€?- 馃攼 **閫€鍑虹櫥褰曠珛鍗冲け鏁堢幇鏈変細璇?* 鈥?`POST /api/v1/auth/logout` 鐜板湪浼氳疆鎹?session secret锛岄伩鍏嶆棫 cookie 鍦ㄩ€€鍑哄悗浠嶅彲缁х画璁块棶鍙椾繚鎶ゆ帴鍙ｏ紱鍚屾祻瑙堝櫒鏍囩椤靛拰骞跺彂椤甸潰浼氳鍚屾鐧诲嚭銆傝璇佸紑鍚椂锛岃鎺ュ彛涔熶笉鍐嶅睘浜庡尶鍚嶇櫧鍚嶅崟锛屾湭鐧诲綍璇锋眰浼氳繑鍥?`401`锛岄伩鍏嶅尶鍚嶈姹傝Е鍙戝叏灞€ session 澶辨晥銆?- 馃М **Tushare 鏉垮潡/绛圭爜璋冪敤闄愭祦涓庤法鏃ョ紦瀛樹慨澶?* 鈥?鏂板鐨?`trade_cal`銆佽涓氭澘鍧楁帓琛屻€佺鐮佸垎甯冮摼璺粺涓€鎺ュ叆 `_check_rate_limit()`锛涗氦鏄撴棩鍘嗙紦瀛樻敼涓烘寜鑷劧鏃ュ埛鏂帮紝閬垮厤鏈嶅姟璺ㄥぉ杩愯鍚庣户缁部鐢ㄦ棫浜ゆ槗鏃ュ垽鏂彇鏁版棩鏈熴€?- 馃捈 **鎸佷粨瓒呭敭鎷︽埅涓庨敊璇祦姘存仮澶?*锛?718锛夆€?`POST /api/v1/portfolio/trades` 鐜板湪浼氬湪鍐欏叆鍓嶆牎楠屽彲鍗栨暟閲忥紝瓒呭敭杩斿洖 `409 portfolio_oversell`锛涙寔浠撻〉鏂板浜ゆ槗 / 璧勯噾娴佹按 / 鍏徃琛屼负鍒犻櫎鑳藉姏锛屽垹闄ゅ悗浼氬悓姝ュけ鏁堜粨浣嶇紦瀛樹笌鏈潵蹇収锛屼究浜庝粠閿欒娴佹按涓洿鎺ユ仮澶嶃€?- 馃摟 **閭欢涓枃鍙戜欢浜哄悕缂栫爜**锛?708锛夆€?閭欢閫氱煡鐜板湪浼氬鍖呭惈涓枃鐨?`EMAIL_SENDER_NAME` 鑷姩鍋?RFC 2047 缂栫爜锛屽苟鍦ㄥ紓甯歌矾寰勮ˉ鍏?SMTP 杩炴帴娓呯悊锛屼慨澶?GitHub Actions / QQ SMTP 涓?`'ascii' codec can't encode characters` 瀵艰嚧鐨勫彂閫佸け璐ャ€?- 馃悰 **娓偂 Agent 瀹炴椂琛屾儏鍘婚噸涓庡揩閫熻矾鐢?* 鈥?缁熶竴 `HK01810` / `1810.HK` / `01810` 绛夋腐鑲′唬鐮佸綊涓€瑙勫垯锛涙腐鑲″疄鏃惰鎯呮敼涓虹洿鎺ヨ蛋鍗曟 `akshare_hk` 璺緞锛岄伩鍏嶆寜 A 鑲?source priority 閲嶅瑙﹀彂鍚屼竴澶辫触鎺ュ彛锛汚gent 杩愯鏈熷鏄惧紡 `retriable=false` 鐨勫伐鍏峰け璐ュ鍔犵煭璺紦瀛橈紝鍑忓皯鍚岃疆鍒嗘瀽涓殑閲嶅澶辫触璋冪敤銆?- 馃摪 **鏂伴椈鏃舵晥纭繃婊や笌绛栫暐鍒嗙獥**锛?697锛夆€?鏂板 `NEWS_STRATEGY_PROFILE`锛坄ultra_short/short/medium/long`锛夊苟涓?`NEWS_MAX_AGE_DAYS` 缁熶竴璁＄畻鏈夋晥绐楀彛锛涙悳绱㈢粨鏋滃湪杩斿洖鍚庢墽琛屽彂甯冩椂闂寸‖杩囨护锛堟椂闂存湭鐭ュ墧闄ゃ€佽秴绐楀墧闄ゃ€佹湭鏉ヤ粎瀹瑰繊 1 澶╋級锛屽苟鍦ㄥ巻鍙?fallback 閾捐矾杩藉姞鐩稿悓绾︽潫锛岄伩鍏嶆棫闂诲啀娆¤繘鍏モ€滄渶鏂板姩鎬?椋庨櫓璀︽姤鈥濄€?
### 鏂囨。

- 鈽侊笍 **鏂板浜戞湇鍔″櫒 Web 鐣岄潰閮ㄧ讲涓庤闂暀绋?*锛團ixes #686锛夆€?琛ュ厖浠庝簯绔儴缃插埌澶栭儴璁块棶鐨勮惤鍦拌鏄庯紝闄嶄綆杩滅▼鑷墭绠￠棬妲涖€?- 馃實 **琛ラ綈鑻辨枃鏂囨。绱㈠紩涓庡崗浣滄枃妗?* 鈥?鏂板鑻辨枃鏂囨。绱㈠紩銆佽础鐚寚鍗椼€丅ot 鍛戒护鏂囨。锛屽苟琛ュ厖涓嫳鍙岃 issue / PR 妯℃澘锛屾柟渚夸腑鑻辨枃鍗忎綔涓庡閮ㄨ础鐚€呯悊瑙ｉ」鐩叆鍙ｃ€?- 馃彿锔?**鏈湴鍖?README 琛ュ厖 Trendshift badge** 鈥?鍦ㄥ璇█ README 涓悓姝ヨˉ涓婃柊鐗堣兘鍔涘叆鍙ｆ爣璇嗭紝鍑忓皯涓嫳鏂囪鏄庨潰涓嶄竴鑷淬€?
## [3.7.0] - 2026-03-15

### 鏂板姛鑳?
- 馃捈 **鎸佷粨绠＄悊 P0 鍏ㄥ姛鑳戒笂绾?*锛?677锛屽搴?Issue #627锛?  - **鏍稿績璐︽湰涓庡揩鐓ч棴鐜?*锛氭柊澧炶处鎴枫€佷氦鏄撱€佺幇閲戞祦姘淬€佷紒涓氳涓恒€佹寔浠撶紦瀛樸€佹瘡鏃ュ揩鐓х瓑鏍稿績鏁版嵁妯″瀷涓?API 绔偣锛涙敮鎸?FIFO / AVG 鍙屾垚鏈硶鍥炴斁锛涘悓鏃ヤ簨浠堕『搴忓浐瀹氫负 `鐜伴噾 鈫?浼佷笟琛屼负 鈫?浜ゆ槗`锛涙寔浠撳揩鐓у啓鍏ラ噰鐢ㄥ師瀛愪簨鍔°€?  - **鍒稿晢 CSV 瀵煎叆**锛氭敮鎸佸崕娉?/ 涓俊 / 鎷涘晢棣栨壒閫傞厤锛屽惈鍒楀悕鍒悕鍏煎锛涗袱闃舵鎺ュ彛锛堣В鏋愰瑙?+ 纭鎻愪氦锛夛紱`trade_uid` 浼樺厛銆乲ey-field hash 鍏滃簳鐨勫箓绛夊幓閲嶏紱鍓嶅闆惰偂绁ㄤ唬鐮佸畬鏁翠繚鐣欍€?  - **缁勫悎椋庨櫓鎶ュ憡**锛氶泦涓害椋庨櫓锛圱op Positions + A 鑲℃澘鍧楀彛寰勶級銆佸巻鍙插洖鎾ょ洃鎺э紙鏀寔鍥炲～缂哄け蹇収锛夈€佹鎹熸帴杩戦璀︼紱澶氬竵绉嶇粺涓€鎹㈢畻 CNY 鍙ｅ緞锛涙辈鍙栧け璐ユ椂鍥為€€鏈€杩戞垚鍔熸眹鐜囧苟鏍囪 stale銆?  - **Web 鎸佷粨椤?*锛坄/portfolio`锛夛細缁勫悎鎬昏銆佹寔浠撴槑缁嗐€侀泦涓害楗煎浘銆侀闄╂憳瑕併€佸叏缁勫悎 / 鍗曡处鎴峰垏鎹紱鎵嬪伐褰曞叆浜ゆ槗 / 璧勯噾娴佹按 / 浼佷笟琛屼负锛涘唴宓岃处鎴峰垱寤哄叆鍙ｏ紱CSV 瑙ｆ瀽 + 鎻愪氦闂幆涓庡埜鍟嗛€夋嫨鍣ㄣ€?  - **Agent 鎸佷粨宸ュ叿**锛氭柊澧?`get_portfolio_snapshot` 鏁版嵁宸ュ叿锛岄粯璁ょ揣鍑戞憳瑕侊紝鍙€夋寔浠撴槑缁嗕笌椋庨櫓鏁版嵁銆?  - **浜嬩欢鏌ヨ API**锛氭柊澧?`GET /portfolio/trades`銆乣GET /portfolio/cash-ledger`銆乣GET /portfolio/corporate-actions`锛屾敮鎸佹棩鏈熻繃婊や笌鍒嗛〉銆?  - **鍙墿灞?Parser Registry**锛氬簲鐢ㄧ骇鍏变韩娉ㄥ唽锛屾敮鎸佽繍琛屾椂娉ㄥ唽鏂板埜鍟嗭紱鏂板 `GET /portfolio/imports/csv/brokers` 鍙戠幇鎺ュ彛銆?
- 馃帹 **鍓嶇璁捐绯荤粺涓庡師瀛愮粍浠跺簱**锛?662锛?  - 寮曞叆娓愯繘寮忓弻涓婚鏋舵瀯锛圚SL 鍙橀噺鍖栬璁′护鐗岋級锛屾竻鐞嗗巻鍙?Legacy CSS锛涢噸鏋?Button / Card / Badge / Collapsible / Input / Select 绛?20+ 鏍稿績缁勪欢锛涙柊澧?`clsx` + `tailwind-merge` 绫诲悕鍚堝苟宸ュ叿锛涙彁鍗囧巻鍙茶褰曘€丩LM 閰嶇疆绛夐〉闈㈠彲璇绘€с€?
- 鈿?**鍒嗘瀽 API 寮傛濂戠害涓庡惎鍔ㄤ紭鍖?*锛?656锛?  - 瑙勮寖 `POST /api/v1/analysis/analyze` 寮傛璇锋眰鐨勮繑鍥炲绾︼紱浼樺寲鏈嶅姟鍚姩杈呭姪閫昏緫锛涗慨澶嶅墠绔姤鍛婄被鍨嬭仈鍚堝畾涔変笌鍚庣鍝嶅簲瀵归綈闂銆?
### 淇

- 馃敂 **Discord 鐜鍙橀噺鍚戝悗鍏煎**锛?659锛夛細杩愯鏃舵柊澧?`DISCORD_CHANNEL_ID` 鈫?`DISCORD_MAIN_CHANNEL_ID` 鐨?fallback 璇诲彇锛涘巻鍙查厤缃敤鎴锋棤闇€淇敼鍗冲彲鎭㈠ Discord Bot 閫氱煡锛涘叏閮ㄧ浉鍏虫枃妗ｄ笌 `.env.example` 瀵归綈銆?- 馃敡 **GitHub Actions Node 24 鍗囩骇**锛?665锛夛細灏嗘墍鏈?GitHub 瀹樻柟 actions 鍗囩骇鑷?Node 24 鍏煎鐗堟湰锛屾秷闄?CI 鏃ュ織涓殑 Node.js 20 deprecation warning锛堝奖鍝?2026-06-02 寮哄埗鍗囩骇绐楀彛锛夈€?- 馃搮 **鎸佷粨椤甸粯璁ゆ棩鏈熸湰鍦板寲**锛氭墜宸ュ綍鍏ヨ〃鍗曢粯璁ゆ棩鏈熸敼鐢ㄦ湰鍦版椂闂达紙`getFullYear/Month/Date`锛夛紝淇 UTC-N 鏃跺尯鐢ㄦ埛鍦ㄥ綋澶╂櫄闂村嚭鐜版棩鏈熷亸绉荤殑闂銆?- 馃攣 **CSV 瀵煎叆鍘婚噸閫昏緫鍔犲浐**锛歞edup hash 绾冲叆琛屽簭鍙蜂綔涓哄尯鍒嗗洜瀛愶紝纭繚鍚屽瓧娈靛悎娉曞垎绗旀垚浜や笉琚鎶樺彔锛涘悓鏃跺湪 `trade_uid` 瀛樺湪鏃朵篃鎸佷箙鍖?hash锛岄槻姝㈡贩鍚堟潵婧愰噸澶嶅啓鍏ャ€?
### 鍙樻洿

- `POST /api/v1/portfolio/trades` 鍦ㄥ悓璐︽埛鍐?`trade_uid` 鍐茬獊鏃惰繑鍥?`409`銆?- 鎸佷粨椋庨櫓鍝嶅簲鏂板 `sector_concentration` 瀛楁锛堝閲忔墿灞曪級锛屽師鏈?`concentration` 瀛楁淇濇寔涓嶅彉銆?- 鍒嗘瀽 API `analyze` 鎺ュ彛寮傛琛屼负濂戠害鏂囨。鍖栵紱鍓嶇鎶ュ憡绫诲瀷鑱斿悎鏇存柊銆?
### 娴嬭瘯

- 鏂板鎸佷粨鏍稿績鏈嶅姟娴嬭瘯锛團IFO / AVG 閮ㄥ垎鍗栧嚭銆佸悓鏃ヤ簨浠堕『搴忋€侀噸澶?`trade_uid` 杩斿洖 409銆佸揩鐓?API 濂戠害锛夈€?- 鏂板 CSV 瀵煎叆骞傜瓑鎬с€佸悎娉曞垎绗旀垚浜や笉璇幓閲嶃€佸幓閲嶈竟鐣屻€侀闄╅槇鍊艰竟鐣屻€佹眹鐜囬檷绾ц涓烘祴璇曘€?- 鏂板 Agent `get_portfolio_snapshot` 宸ュ叿璋冪敤娴嬭瘯銆?- 鏂板鍒嗘瀽 API 寮傛濂戠害鍥炲綊娴嬭瘯銆?
## [3.6.0] - 2026-03-14

### Added
- 馃搳 **Web UI Design System** 鈥?implemented dual-theme architecture and terminal-inspired atomic UI components
- 馃搳 **UI Components Refactoring** 鈥?integrated `clsx` and `tailwind-merge` for robust class composition across Web UI

- 馃棏锔?**History batch deletion** 鈥?Web UI now supports multi-selection and batch deletion of analysis history; added `POST /api/v1/history/batch-delete` endpoint and `ConfirmDialog` component.
- 馃攼 **Auth settings API** 鈥?new `POST /api/v1/auth/settings` endpoint to enable or disable Web authentication at runtime and set the initial admin password when needed
- openclaw Skill 闆嗘垚鎸囧崡 鈥?鏂板 [docs/openclaw-skill-integration.md](openclaw-skill-integration.md)锛岃鏄庡浣曢€氳繃 openclaw Skill 璋冪敤 DSA API
- 鈿欙笍 **LLM channel protocol/test UX** 鈥?`.env` and Web settings now share the same channel shape (`LLM_CHANNELS` + `LLM_<NAME>_PROTOCOL/BASE_URL/API_KEY/MODELS/ENABLED`); settings page adds per-channel connection testing, primary/fallback/vision model selection, and protocol-aware model prefixing
- 馃 **Agent architecture Phase 0+1** 鈥?shared protocols (`AgentContext`, `AgentOpinion`, `StageResult`), extracted `run_agent_loop()` runner, `AGENT_ARCH` switch (`single`/`multi`), config registry entries
- 馃攳 **Bot NL routing** 鈥?two-layer natural-language routing: cheap regex pre-filter (stock codes + finance keywords) 鈫?lightweight LLM intent parsing; controlled by `AGENT_NL_ROUTING=true`; supports multi-stock and strategy extraction
- 馃挰 **`/ask` multi-stock analysis** 鈥?comma or `vs` separated codes (max 5), parallel thread execution with 150s timeout (preserves partial results), Markdown comparison summary table at top
- 馃搵 **`/history` command** 鈥?per-user session isolation via `{platform}_{user_id}:{scope}` format (colon delimiter prevents prefix collision); lists both `/chat` and `/ask` sessions; view detail or clear
- 馃搳 **`/strategies` command** 鈥?lists available strategy YAML files grouped by category (瓒嬪娍/褰㈡€?鍙嶈浆/妗嗘灦) with 鉁?猬?activation status
- 馃敡 **Backtest summary tools** 鈥?`get_strategy_backtest_summary` and `get_stock_backtest_summary` registered as read-only Agent tools
- 鈿欙笍 **Agent auto-detection** 鈥?`is_agent_available()` auto-detects from `LITELLM_MODEL`; explicit `AGENT_MODE=true/false` takes full precedence
- 馃彈锔?**Multi-Agent orchestrator (Phase 2)** 鈥?`AgentOrchestrator` with 4 modes (`quick`/`standard`/`full`/`strategy`); drop-in replacement for `AgentExecutor` via `AGENT_ARCH=multi`; `BaseAgent` ABC with tool subset filtering, cached data injection, and structured `AgentOpinion` output
- 馃З **Specialised agents (Phase 2-4)** 鈥?`TechnicalAgent` (8 tools, trend/MA/MACD/volume/pattern analysis), `IntelAgent` (news & sentiment, risk flag propagation), `DecisionAgent` (synthesis into Decision Dashboard JSON), `RiskAgent` (7 risk categories, two-level severity with soft/hard override)
- 馃搱 **Strategy system (Phase 3)** 鈥?`StrategyAgent` (per-strategy evaluation from YAML skills), `StrategyRouter` (rule-based regime detection 鈫?strategy selection), `StrategyAggregator` (weighted consensus with backtest performance factor)
- 馃敩 **Deep Research agent (Phase 5)** 鈥?`ResearchAgent` with 3-phase approach (decompose 鈫?research sub-questions 鈫?synthesise report); token budget tracking; new `/research` bot command with aliases (`/娣辩爺`, `/deepsearch`)
- 馃 **Memory & calibration (Phase 6)** 鈥?`AgentMemory` with prediction accuracy tracking, confidence calibration (activates after minimum sample threshold), strategy auto-weighting based on historical win rate
- 馃搳 **Portfolio Agent (Phase 7)** 鈥?`PortfolioAgent` for multi-stock portfolio analysis (position sizing, sector concentration, correlation risk, cross-market linkage, rebalance suggestions)
- 馃敂 **Event-driven alerts (Phase 7)** 鈥?`EventMonitor` with `PriceAlert`, `VolumeAlert`, `SentimentAlert` rules; async checking, callback notifications, serializable persistence
- 鈿欙笍 **New config entries** 鈥?`AGENT_ORCHESTRATOR_MODE`, `AGENT_RISK_OVERRIDE`, `AGENT_DEEP_RESEARCH_BUDGET`, `AGENT_MEMORY_ENABLED`, `AGENT_STRATEGY_AUTOWEIGHT`, `AGENT_STRATEGY_ROUTING` 鈥?all registered in `config.py` + `config_registry.py` (WebUI-configurable)

### Changed
- 馃攼 **Auth password state semantics** 鈥?stored password existence is now tracked independently from auth enablement; when auth is disabled, `/api/v1/auth/status` returns `passwordSet=false` while preserving the saved password for future re-enable
- 馃攼 **Auth settings re-enable hardening** 鈥?re-enabling auth with a stored password now requires `currentPassword`, and failed session creation rolls back the auth toggle to avoid lockout
- 鈾伙笍 **AgentExecutor refactored** 鈥?`_run_loop` delegates to shared `runner.run_agent_loop()`; removed duplicated serialization/parsing/thinking-label code
- 鈾伙笍 **Unified agent switch** 鈥?Bot, API, and Pipeline all use `config.is_agent_available()` instead of divergent `config.agent_mode` checks
- 馃摉 **README.md** 鈥?expanded Bot commands section (ask/chat/strategies/history), added NL routing note, updated agent mode description
- 馃摉 **.env.example** 鈥?added `AGENT_ARCH` and `AGENT_NL_ROUTING` configuration documentation
- 馃攲 **Analysis API async contract** 鈥?`POST /api/v1/analysis/analyze` now documents distinct async `202` payloads for single-stock vs batch requests, and `report_type=full` is treated consistently with the existing full-report behavior

### Fixed
- 馃悰 **Analysis API blank-code guardrails** 鈥?`POST /api/v1/analysis/analyze` now drops whitespace-only entries before batch enqueue and returns `400` when no valid stock code remains
- 馃悰 **Bare `/api` SPA fallback** 鈥?unknown API paths now return JSON `404` consistently for both `/api/...` and the exact `/api` path
- 馃幃 **Discord channel env compatibility** 鈥?runtime now accepts legacy `DISCORD_CHANNEL_ID` as a fallback for `DISCORD_MAIN_CHANNEL_ID`, and the docs/examples now use the same variable name as the actual workflow/config implementation
- 馃悰 **Session secret rotation on Windows** 鈥?use atomic replace so auth toggles invalidate existing sessions even when `.session_secret` already exists
- 馃悰 **Auth toggle atomicity** 鈥?persist `ADMIN_AUTH_ENABLED` before rotating session secret; on rotation failure, roll back to the previous auth state
- 馃敡 **LLM runtime selection guardrails** 鈥?YAML 妯″紡涓嬫笭閬撶紪杈戝櫒涓嶅啀瑕嗙洊 `LITELLM_MODEL` / fallback / Vision锛涚郴缁熼厤缃牎楠岃ˉ涓婂叏閮ㄦ笭閬撶鐢ㄥ悗鐨勮繍琛屾椂鏉ユ簮妫€鏌ワ紝骞朵慨澶?`vertexai/...` 杩欑被鍗忚鍒悕妯″瀷琚噸澶嶅姞鍓嶇紑鐨勯棶棰?- 馃悰 **Multi-stock `/ask` follow-up regressions** 鈥?portfolio overlay now shares the same timeout budget as the per-stock phase and is skipped on timeout instead of blocking the bot reply; `/history` now stores the readable per-stock summary instead of raw dashboard JSON; condensed multi-stock output now renders numeric `sniper_points` values
- 馃悰 **Decision dashboard enum compatibility** 鈥?multi-agent `DecisionAgent` now keeps `decision_type` within the legacy `buy|hold|sell` contract and normalizes stray `strong_*` outputs before risk override, pipeline conversion, and downstream缁熻/閫氱煡姹囨€?- 馃洘 **Multi-Agent partial-result fallback** 鈥?`IntelAgent` now caches parsed intel for downstream reuse, shared JSON parsing tolerates lightly malformed model output, and the orchestrator preserves/synthesizes a minimal dashboard on timeout or mid-pipeline parse failure instead of always collapsing to `50/瑙傛湜/鏈煡`
- 馃悰 **Shared LiteLLM routing restored** 鈥?bot NL intent parsing and `ResearchAgent` planning/synthesis now reuse the same LiteLLM adapter / Router / fallback / `api_base` injection path as the main Agent flow, so `LLM_CHANNELS` / `LITELLM_CONFIG` / OpenAI-compatible deployments behave consistently
- 馃悰 **Bot chat session backward compatibility** 鈥?`/chat` now keeps using the legacy `{platform}_{user_id}` session id when old history already exists, and `/history` can still list / view / clear those pre-migration sessions alongside the new `{platform}_{user_id}:chat` format
- 馃悰 **EventMonitor unsupported rule rejection** 鈥?config validation/runtime loading now reject or skip alert types the monitor cannot actually evaluate yet, so schedule mode no longer silently accepts permanent no-op rules
- 馃悰 **P0 鍩烘湰闈㈣仛鍚堢ǔ瀹氭€т慨澶?* (#614) 鈥?淇 `get_stock_info` 鏉垮潡璇箟鍥炲綊锛堟柊澧?`belong_boards` 骞朵繚鐣?`boards` 鍏煎鍒悕锛夈€佸紩鍏ュ熀鏈潰涓婁笅鏂囩簿绠€杩斿洖浠ユ帶鍒?token銆佷负鍩烘湰闈㈢紦瀛樺鍔犳渶澶ф潯鐩窐姹帮紝骞惰ˉ榻?ETF 鎬讳綋鐘舵€佽仛鍚堜笌 NaN 鏉垮潡瀛楁杩囨护锛屼繚璇?fail-open 涓庢渶灏忓叆渚点€?- 馃敡 **GitHub Actions 鎼滅储寮曟搸鐜鍙橀噺琛ュ厖** 鈥?宸ヤ綔娴佹柊澧?`MINIMAX_API_KEYS`銆乣BRAVE_API_KEYS`銆乣SEARXNG_BASE_URLS` 鐜鍙橀噺鏄犲皠锛屼娇 GitHub Actions 鐢ㄦ埛鍙厤缃?MiniMax銆丅rave銆丼earXNG 鎼滅储鏈嶅姟锛堟鍓?v3.5.0 宸叉坊鍔?provider 瀹炵幇浣嗙己灏戝伐浣滄祦閰嶇疆锛?- 馃 **Multi-Agent runtime consistency** 鈥?`AGENT_MAX_STEPS` now propagates to each orchestrated sub-agent; added cooperative `AGENT_ORCHESTRATOR_TIMEOUT_S` budget to stop overlong pipelines before they cascade further
- 馃攲 **Multi-Agent feature wiring** 鈥?`AGENT_RISK_OVERRIDE` now actively downgrades final dashboards on hard risk findings; `AGENT_MEMORY_ENABLED` now injects recent analysis memory + confidence calibration into specialised agents; multi-stock `/ask` now runs `PortfolioAgent` to add portfolio-level allocation and concentration guidance
- 馃敂 **EventMonitor runtime wiring** 鈥?schedule mode can now load alert rules from `AGENT_EVENT_ALERT_RULES_JSON`, poll them at `AGENT_EVENT_MONITOR_INTERVAL_MINUTES`, and send triggered alerts through the existing notification service
- 馃洜锔?**Follow-up stability fixes** 鈥?multi-stock `/ask` now falls back to usable text output when dashboard JSON parsing fails; EventMonitor skips semantically invalid rules instead of aborting schedule startup; background alert polling now runs independently of the main scheduled analysis loop
- 馃И **Multi-Agent regression coverage** 鈥?added orchestrator execution tests for `run()`, `chat()`, critical-stage failure, graceful degradation, and timeout handling
- 馃Ч **PortfolioAgent cleanup** 鈥?`post_process()` now reuses shared JSON parsing and removed stale unused imports
- 馃殾 **Bot async dispatch** 鈥?`CommandDispatcher` now exposes `dispatch_async()`; NL intent parsing and default command execution are offloaded from the event loop, DingTalk stream awaits async handlers directly, and Feishu stream processing is moved off the SDK callback thread
- 馃寪 **Async webhook handler** 鈥?new `handle_webhook_async()` function in `bot/handler.py` for use from async contexts (e.g. FastAPI); calls `dispatch_async()` directly without thread bridging
- 馃У **Feishu stream ThreadPoolExecutor** 鈥?replaced unbounded per-message `Thread` spawning with a capped `ThreadPoolExecutor(max_workers=8)` to prevent thread explosion under message bursts
- 馃敀 **EventMonitor safety** 鈥?`_check_volume()` now safely handles `get_daily_data` returning `None` (no tuple-unpacking crash); `on_trigger` callbacks support both sync and async callables via `asyncio.to_thread`/`await`
- 馃Ч **ResearchAgent dedup** 鈥?`_filtered_registry()` now delegates to `BaseAgent._filtered_registry()` instead of duplicating the filtering logic
- 馃Ч **Bot trailing whitespace cleanup** 鈥?removed W291/W293 whitespace issues across `bot/handler.py`, `bot/dispatcher.py`, `bot/commands/base.py`, `bot/platforms/feishu_stream.py`, `bot/platforms/dingtalk_stream.py`
- 馃悰 **Dispatcher `_parse_intent_via_llm` safety** 鈥?replaced fragile `'raw' in dir()` with `'raw' in locals()` for undefined-variable guard in `JSONDecodeError` handler
- 馃悰 **绛圭爜缁撴瀯 LLM 鏈～鍐欐椂鍏滃簳琛ュ叏** (#589) 鈥?DeepSeek 绛夋ā鍨嬫湭姝ｇ‘濉啓 `chip_structure` 鏃讹紝鑷姩鐢ㄦ暟鎹簮宸茶幏鍙栫殑绛圭爜鏁版嵁琛ュ叏锛屼繚璇佸悇妯″瀷灞曠ず涓€鑷达紱鏅€氬垎鏋愪笌 Agent 妯″紡鍧囩敓鏁?- 馃悰 **鍘嗗彶鎶ュ憡鐙欏嚮鐐逛綅鏄剧ず鍘熷鏂囨湰** (#452) 鈥?鍘嗗彶璇︽儏椤电幇浼樺厛灞曠ず `raw_result.dashboard.battle_plan.sniper_points` 涓殑鍘熷瀛楃涓诧紝閬垮厤 `analysis_history` 鏁板€煎垪鎶婂尯闂淬€佽鏄庢枃瀛楁垨澶嶆潅鐐逛綅鍘嬬缉鎴愬崟涓暟瀛楋紱淇濈暀鍘熸湁鏁板€煎垪浣滀负鍥為€€
- 馃悰 **Session prefix collision** 鈥?user ID `123` could see sessions of user `1234` via `startswith`; fixed with colon delimiter in session_id format
- 馃悰 **NL pre-filter false positives** 鈥?`re.IGNORECASE` caused `[A-Z]{2,5}` to match common English words like "hello"; removed global flag, use inline `(?i:...)` only for English finance keywords
- 馃悰 **Dotted ticker in strategy args** 鈥?`_get_strategy_args()` didn't recognize `BRK.B` as a stock code, leaving it in strategy text; now accepts `TICKER.CLASS` format
- 鈴憋笍 **efinance 闀胯皟鐢ㄦ寕璧蜂慨澶?* (#660) 鈥?涓烘墍鏈?efinance API 璋冪敤寮曞叆 `_ef_call_with_timeout()` 鍖呰锛堥粯璁?30 绉掞紝鍙€氳繃 `EFINANCE_CALL_TIMEOUT` 閰嶇疆锛夛紱浣跨敤 `executor.shutdown(wait=False)` 纭繚瓒呮椂鍚庝笉鍐嶉樆濉炰富绾跨▼锛屽交搴曟秷闄?81 鍒嗛挓鎸傝捣闂
- 馃洝锔?**绫诲瀷瀹夊叏鍐呭瀹屾暣鎬ф鏌?* (#660) 鈥?`check_content_integrity()` 鐜板湪灏嗛潪瀛楃涓茬被鍨嬬殑 `operation_advice` / `analysis_summary` 瑙嗕负缂哄け瀛楁锛岄伩鍏嶄笅娓?`get_emoji()` 鍥?`dict.strip()` 宕╂簝
- 馃搫 **鎶ュ憡淇濆瓨涓庨€氱煡瑙ｈ€?* (#660) 鈥?`_save_local_report()` 涓嶅啀渚濊禆 `send_notification` 鏍囧織瑙﹀彂锛宍--no-notify` 妯″紡涓嬫湰鍦版姤鍛婄収甯镐繚瀛?- 馃攧 **operation_advice 瀛楀吀褰掍竴鍖?* (#660) 鈥?Pipeline 鍜?BacktestEngine 鐜板湪灏?LLM 杩斿洖鐨?`dict` 鏍煎紡 `operation_advice` 閫氳繃 `decision_type`锛堜笉鍖哄垎澶у皬鍐欙級鏄犲皠涓烘爣鍑嗗瓧绗︿覆锛岄槻姝㈠洜妯″瀷杈撳嚭鏍煎紡鍙樺寲瀵艰嚧宕╂簝
- 馃洝锔?**runner.py usage None 闃叉姢** (#660) 鈥?`response.usage` 涓?`None` 鏃朵笉鍐嶆姏鍑?`AttributeError`锛屽洖閫€涓?0 token 璁℃暟
- 馃搵 **orchestrator 闈欓粯澶辫触鏀逛负鏃ュ織璀﹀憡** (#660) 鈥?`IntelAgent` / `RiskAgent` 闃舵澶辫触鐜板湪璁板綍 `WARNING` 鑰岄潪闈欓粯璺宠繃锛屼究浜庤瘖鏂?
### Notes
- 鈿狅笍 **Multi-worker auth toggles** 鈥?runtime auth updates are process-local; multi-worker deployments must restart/roll workers to keep auth state consistent

## [3.5.0] - 2026-03-12

### Added
- 馃搳 **Web UI full report drawer** (Fixes #214) 鈥?history page adds "Full Report" button to display the complete Markdown analysis report in a side drawer; new `GET /api/v1/history/{record_id}/markdown` endpoint
- 馃搳 **LLM cost tracking** 鈥?all LLM calls (analysis, agent, market review) recorded in `llm_usage` table; new `GET /api/v1/usage/summary?period=today|month|all` endpoint returns aggregated token usage by call type and model
- 馃攳 **SearXNG search provider** (Fixes #550) 鈥?quota-free self-hosted search fallback; priority: Bocha > Tavily > Brave > SerpAPI > MiniMax > SearXNG
- 馃攳 **MiniMax web search provider** 鈥?`MiniMaxSearchProvider` with circuit breaker (3 failures 鈫?300s cooldown) and dual time-filtering; configured via `MINIMAX_API_KEYS`
- 馃 **Agent models discovery API** 鈥?`GET /api/v1/agent/models` returns available model deployments (primary/fallback/source/api_base) for Web UI model selector
- 馃 **Agent chat export & send** (#495) 鈥?export conversation to .md file; send to configured notification channels; new `POST /api/v1/agent/chat/send`
- 馃 **Agent background execution** (#495) 鈥?analysis continues when switching pages; badge notification on completion; auto-cancel in-progress stream on session switch
- 馃摑 **Report Engine P0** 鈥?Pydantic schema validation for LLM JSON; Jinja2 templates (markdown/wechat/brief) with legacy fallback; content integrity checks with retry; brief mode (`REPORT_TYPE=brief`); history signal comparison
- 馃摝 **Smart import** 鈥?multi-source import from image/CSV/Excel/clipboard; Vision LLM extracts code+name+confidence; name鈫抍ode resolver (local map + pinyin + AkShare); confidence-tiered confirmation
- 鈿欙笍 **GitHub Actions LiteLLM config** 鈥?workflow supports `LITELLM_CONFIG`/`LITELLM_CONFIG_YAML` for flexible AI provider configuration
- 鈿欙笍 **Config engine refactor & system API** (#602) 鈥?unified config registry, validation and API exposure
- 馃摉 **LLM configuration guide** 鈥?new `docs/LLM_CONFIG_GUIDE.md` covering 3-tier config, quick start, Vision/Agent/troubleshooting

### Fixed
- 馃悰 **analyze_trend always reports No historical data** (#600) 鈥?now fetches from DB/DataFetcher instead of broken `get_analysis_context`
- 馃悰 **Chip structure fallback when LLM omits it** (#589) 鈥?auto-fills from data source chip data for consistent display across models
- 馃悰 **History sniper points show raw text** (#452) 鈥?prioritizes original strings over compressed numeric values
- 馃悰 **GitHub Actions ENABLE_CHIP_DISTRIBUTION configurable** (#617) 鈥?no longer hardcoded, supports vars/secrets override
- 馃悰 **`.env` save preserves comments and blank lines** 鈥?Web settings no longer destroys `.env` formatting
- 馃悰 **Agent model discovery fixes** 鈥?legacy mode includes LiteLLM-native providers; source detection aligned with runtime; fallback deployments no longer expanded per-key
- 馃悰 **Stooq US stock previous close semantics** 鈥?no longer misuses open price as previous close
- 馃悰 **Stock name prefetch regression** 鈥?prioritizes local `STOCK_NAME_MAP` before remote queries
- 馃悰 **AkShare limit-up/down calculation** (#555) 鈥?fixed market analysis statistics
- 馃悰 **AkShare Tencent source field index & ETF quote mapping** (#579)
- 馃悰 **Pytdx stock name cache pagination** (#573) 鈥?prevents cache overflow
- 馃悰 **PushPlus oversized report chunking** (#489) 鈥?auto-segments long content
- 馃悰 **Agent chat cancel & switch** (#495) 鈥?cancel no longer misreports as failure; fast switch no longer overwrites stream state
- 馃悰 **MiniMax search status in `/status` command** (#587)
- 馃悰 **config_registry duplicate BOCHA_API_KEYS** 鈥?removed duplicate dict entry that silently overwrote config

### Changed
- 馃攷 **Fetcher failure observability** 鈥?logs record start/success/failure with elapsed time, failover transitions; Efinance/Akshare include upstream endpoint and classified failure categories
- 鈾伙笍 **Data source resilience & cleanup** (#602) 鈥?fallback chain optimization
- 鈾伙笍 **Image extract API response extension** 鈥?new `items` field (code/name/confidence); `codes` preserved for backward compatibility
- 鈾伙笍 **Import parse error messages** 鈥?specific failure reasons for Excel/CSV; improved logging with file type and size

### Docs
- 馃摉 LLM config guide refactored for clarity (#583)
- 馃摉 `image-extract-prompt.md` with full prompt documentation
- 馃摉 AkShare fallback cache TTL documentation
## [3.4.10] - 2026-03-07

### Fixed
- 馃悰 **EfinanceFetcher ETF OHLCV data** (#541, #527) 鈥?switch `_fetch_etf_data` from `ef.fund.get_quote_history` (NAV-only, no OHLCV, no `beg`/`end` params) to `ef.stock.get_quote_history`; ETFs now return proper open/high/low/close/volume/amount instead of zeros; remove obsolete NAV column mappings from `_normalize_data`
- 馃悰 **tiktoken 0.12.0 `Unknown encoding cl100k_base`** (#537) 鈥?pin `tiktoken>=0.8.0,<0.12.0` in requirements.txt to avoid plugin-registration regression introduced in 0.12.0
- 馃悰 **Web UI API error classification** (#540) 鈥?frontend no longer treats every HTTP 400 as the same "server/network" failure; now distinguishes Agent disabled / missing params / model-tool incompatibility / upstream LLM errors / local connection failures
- 馃悰 **鍖椾氦鎵€浠ｇ爜璇嗗埆澶辫触** (#491, #533) 鈥?8/4/92 寮€澶寸殑 6 浣嶄唬鐮佺幇姝ｇ‘璇嗗埆涓哄寳浜ゆ墍锛汿ushare/Akshare/Yfinance 绛夋暟鎹簮鏀寔 .BJ 鎴?bj 鍓嶇紑锛汢aostock/Pytdx 瀵瑰寳浜ゆ墍浠ｇ爜鏄惧紡鍒囨崲鏁版嵁婧愶紱閬垮厤璇垽涓婃捣 B 鑲?900xxx
- 馃悰 **鐙欏嚮鐐逛綅瑙ｆ瀽閿欒** (#488, #532) 鈥?鐞嗘兂涔板叆/浜屾涔板叆绛夊瓧娈靛湪鏃犮€屽厓銆嶅瓧鏃惰鎻愬彇鎷彿鍐呮妧鏈寚鏍囨暟瀛楋紱鐜板厛鎴幓绗竴涓嫭鍙峰悗鍐呭鍐嶆彁鍙?
### Added
- **Markdown-to-image for dashboard report** (#455, #535) 鈥?涓偂鏃ユ姤姹囨€绘敮鎸?markdown 杞浘鐗囨帹閫侊紙Telegram銆乄eChat銆丆ustom銆丒mail锛夛紝涓庡ぇ鐩樺鐩樿涓轰竴鑷?- **markdown-to-file engine** (#455) 鈥?`MD2IMG_ENGINE=markdown-to-file` 鍙€夛紝瀵?emoji 鏀寔鏇村ソ锛岄渶 `npm i -g markdown-to-file`
- **PREFETCH_REALTIME_QUOTES** (#455) 鈥?璁句负 `false` 鍙鐢ㄥ疄鏃惰鎯呴鍙栵紝閬垮厤 efinance/akshare_em 鍏ㄥ競鍦烘媺鍙?- **Stock name prefetch** (#455) 鈥?鍒嗘瀽鍓嶉鍙栬偂绁ㄥ悕绉帮紝鍑忓皯鎶ュ憡涓€岃偂绁▁xxxx銆嶅崰浣嶇
- 馃搳 **鍒嗘瀽鎶ュ憡妯″瀷鏍囪** (#528, #534) 鈥?鍦ㄥ垎鏋愭姤鍛?meta銆佹姤鍛婃湯灏俱€佹帹閫佸唴瀹逛腑灞曠ず `model_used`锛堝畬鏁?LLM 妯″瀷鍚嶏級锛汚gent 澶氳疆璋冪敤鏃惰褰曞苟灞曠ず姣忚疆瀹為檯浣跨敤鐨勬ā鍨嬶紙鏀寔 fallback 鍒囨崲锛?
### Changed
- **Enhanced markdown-to-image failure warning** (#455) 鈥?杞浘澶辫触鏃舵彁绀哄叿浣撲緷璧栵紙wkhtmltopdf 鎴?m2f锛?- **WeChat-only image routing optimization** (#455) 鈥?浠呴厤缃紒涓氬井淇″浘鐗囨椂锛屼笉鍐嶅瀹屾暣鎶ュ憡鍋氬啑浣欒浆鍥撅紝閬垮厤璇鎬уけ璐ユ棩蹇?- **Stock name prefetch lightweight mode** (#455) 鈥?鍚嶇О棰勫彇闃舵璺宠繃 realtime quote 鏌ヨ锛屽噺灏戦澶栫綉缁滃紑閿€

## [3.4.9] - 2026-03-06

### Added
- 馃 **Structured config validation** 鈥?`ConfigIssue` dataclass and `validate_structured()` with severity-aware logging; `CONFIG_VALIDATE_MODE=strict` aborts startup on errors
- 馃柤锔?**Vision model config** 鈥?`VISION_MODEL` and `VISION_PROVIDER_PRIORITY` for image stock extraction; provider fallback (Gemini 鈫?Anthropic 鈫?OpenAI 鈫?DeepSeek) when primary fails
- 馃殌 **CLI init wizard** 鈥?`python -m dsa init` 3-step interactive bootstrap (model 鈫?data source 鈫?notification), 9 provider presets, incremental merge by default
- 馃敡 **Multi-channel LLM support** with visual channel editor (#494)

### Changed
- 鈾伙笍 **Vision extraction** 鈥?migrated from gemini-3 hardcode to `litellm.completion()` with configurable model and provider fallback; `OPENAI_VISION_MODEL` deprecated in favor of `VISION_MODEL`
- 鈾伙笍 **Market analyzer** 鈥?uses `Analyzer.generate_text()` for LLM calls; fixes bypass and Anthropic `AttributeError` when using non-Router path
- 鈾伙笍 **Config validation refinements** 鈥?test_env output format syncs with `validate_structured` (severity-aware 鉁?鉁?鈿?路); Vision key warning when `VISION_MODEL` set but no provider API key; market_analyzer test covers `generate_market_review` fallback when `generate_text` returns None
- 鈿欙笍 **Auto-tag workflow defaults to NO tag** 鈥?only tags when commit message explicitly contains `#patch`, `#minor`, or `#major`
- 鈾伙笍 **Formatter and notification refactor** (#516)

### Fixed
- 馃悰 **STOCK_LIST not refreshed on scheduled runs** 鈥?`.env` or WebUI changes to `STOCK_LIST` now hot-reload before each scheduled analysis (#529)
- 馃悰 **WebUI fails to load with MIME type error** 鈥?SPA fallback route now resolves correct `Content-Type` for JS/CSS files (#520)
- 馃悰 **AstrBot sender docstring misplaced** 鈥?`import time` placed before docstring in `_send_astrbot`, causing it to become dead code
- 馃悰 **Telegram Markdown link escaping** 鈥?`_convert_to_telegram_markdown` escaped `[]()` characters, breaking all Markdown links in reports
- 馃悰 **Duplicate `discord_bot_status` field** in Config dataclass 鈥?second declaration silently shadowed the first
- 馃Ч **Unused imports** 鈥?removed `shutil`/`subprocess` from `main.py`
- 馃敡 **Config validation and Vision key check** (#525)

### Docs
- 馃摑 Clarified GitHub Actions non-trading-day manual run controls (`TRADING_DAY_CHECK_ENABLED` + `force_run`) for Issue #461 / PR #466

## [3.4.8] - 2026-03-02

### Fixed
- 馃悰 **Desktop exe crashes on startup with `FileNotFoundError`** 鈥?PyInstaller build was missing litellm's JSON data files (e.g. `model_prices_and_context_window_backup.json`). Added `--collect-data litellm` to both Windows and macOS build scripts so the files are correctly bundled in the executable.

### CI
- 馃敡 Cache Electron binaries on macOS CI runners to prevent intermittent EOF download failures when fetching `electron-vX.Y.Z-darwin-*.zip` from GitHub CDN
- 馃敡 Fix macOS DMG `hdiutil Resource busy` error during desktop packaging

### Docs
- 馃摑 Clarify non-trading-day manual run controls for GitHub Actions (`TRADING_DAY_CHECK_ENABLED` + `force_run`) (#474)

## [3.4.7] - 2026-02-28

### Added
- 馃 **CN/US Market Strategy Blueprint System** (#395) 鈥?market review prompt injects region-specific strategy blueprints with position sizing and risk trigger recommendations

### Fixed
- 馃悰 **`TRADING_DAY_CHECK_ENABLED` env var and `--force-run` for GitHub Actions** (#466)
- 馃悰 **Agent pipeline preserved resolved stock names** (#464) 鈥?placeholder names no longer leak into reports
- 馃悰 **Code cleanup** (#462, Fixes #422)
- 馃悰 **WebUI auto-build on startup** (#460)
- 馃悰 **ARCH_ARGS unbound variable** (#458)
- 馃悰 **Time zone inconsistency & right panel flash** (#439)

### Docs
- 馃摑 Clarify potential ambiguities in code (#343)
- 馃摑 ENABLE_EASTMONEY_PATCH guidance for Issue #453 (#456)

## [3.4.0] - 2026-02-27

### Added
- 馃摗 **LiteLLM Direct Integration + Multi API Key Support** (#454, Fixes #421 #428)
  - Removed native SDKs (google-generativeai, google-genai, anthropic); unified through `litellm>=1.80.10`
  - New config: `LITELLM_MODEL`, `LITELLM_FALLBACK_MODELS`, `GEMINI_API_KEYS`, `ANTHROPIC_API_KEYS`, `OPENAI_API_KEYS`
  - Multi-key auto-builds LiteLLM Router (simple-shuffle) with 429 cooldown
  - **Breaking**: `.env` `GEMINI_MODEL` (no prefix) only for fallback; explicit config must include provider prefix

### Changed
- 鈾伙笍 **Notification Refactoring** (#435) 鈥?extracted 10 sender classes into `src/notification_sender/`

### Fixed
- 馃悰 LLM NoneType crash, history API 422, sniper points extraction
- 馃悰 Auto-build frontend on WebUI startup 鈥?`WEBUI_AUTO_BUILD` env var (default `true`)
- 馃悰 Docker explicit project name (#448)
- 馃悰 Bocha search SSL retry (#445, #446) 鈥?transient errors retry up to 3 times
- 馃悰 Gemini google-genai SDK migration (Fixes #440, #444)
- 馃悰 Mobile home page scrolling (Fixes #419, #433)
- 馃悰 History list scroll reset (#431)
- 馃悰 Settings save button false positive (fixes #417, #430)

## [3.3.22] - 2026-02-26

### Added
- 馃挰 **Chat History Persistence** (Fixes #400, #414) 鈥?`/chat` page survives refresh, sidebar session list
- 馃帹 Project VI Assets 鈥?logo icon set, PSD, vector, banner (#425)
- 馃殌 Desktop CI Auto-Release (#426) 鈥?Windows + macOS parallel builds

### Fixed
- 馃悰 Agent Reasoning 400 & LiteLLM Proxy (fixes #409, #427)
- 馃悰 Discord chunked sending (#413) 鈥?`DISCORD_MAX_WORDS` config
- 馃悰 yfinance shared DataFrame (#412)
- 馃悰 sniper_points parsing (#408)
- 馃悰 Agent framework category missing (#406)
- 馃悰 Date inconsistency & query id (fixes #322, #363)

## [3.3.12] - 2026-02-24

### Added
- 馃搱 **Intraday Realtime Technical Indicators** (Issue #234, #397) 鈥?MA calculated from realtime price, config: `ENABLE_REALTIME_TECHNICAL_INDICATORS`
- 馃 **Agent Strategy Chat** (#367) 鈥?full ReAct pipeline, 11 YAML strategies, SSE streaming, multi-turn chat
- 馃摙 PushPlus Group Push 鈥?`PUSHPLUS_TOPIC` (#402)
- 馃搮 Trading Day Check (Issue #373, #375) 鈥?`TRADING_DAY_CHECK_ENABLED`, `--force-run`

### Fixed
- 馃悰 DeepSeek reasoning mode (Issue #379, #386)
- 馃悰 Agent news intel persistence (Fixes #396, #405)
- 馃悰 Bare except clauses replaced with `except Exception` (#398)
- 馃悰 UUID fallback for HTTP non-secure context (fixes #377, #381)
- 馃悰 Docker DNS resolution (Fixes #372, #374)
- 馃悰 Agent session/strategy bugs 鈥?multiple follow-up fixes for #367
- 馃悰 yfinance parallel download data filtering

### Changed
- Market review strategy consistency 鈥?unified cn/us template
- Agent test assertions updated (`6 -> 11`)


## [3.2.11] - 2026-02-23

### 淇锛?patch锛?- 馃悰 **StockTrendAnalyzer 浠庢湭鎵ц** (Issue #357)
  - 鏍瑰洜锛歚get_analysis_context` 浠呰繑鍥?2 澶╂暟鎹笖鏃?`raw_data`锛宲ipeline 涓?`raw_data in context` 濮嬬粓涓?False
  - 淇锛歋tep 3 鐩存帴璋冪敤 `get_data_range` 鑾峰彇 90 鏃ュ巻澶╋紙绾?60 浜ゆ槗鏃ワ級鍘嗗彶鏁版嵁鐢ㄤ簬瓒嬪娍鍒嗘瀽
  - 鏀瑰杽锛氳秼鍔垮垎鏋愬け璐ユ椂鐢?`logger.warning(..., exc_info=True)` 璁板綍瀹屾暣 traceback

## [3.2.10] - 2026-02-22

### 鏂板
- 鈿欙笍 鏀寔 `RUN_IMMEDIATELY` 閰嶇疆椤癸紝璁句负 `true` 鏃跺畾鏃朵换鍔¤Е鍙戝悗绔嬪嵆鎵ц涓€娆″垎鏋愶紝鏃犻渶绛夊緟棣栦釜瀹氭椂鐐?
### 淇
- 馃悰 淇 Web UI 椤甸潰灞呬腑闂
- 馃悰 淇 Settings 杩斿洖 500 閿欒

## [3.2.9] - 2026-02-22

### 淇
- 馃悰 **ETF 鍒嗘瀽浠呭叧娉ㄦ寚鏁拌蛋鍔?*锛圛ssue #274锛?  - 缇庤偂/娓偂 ETF锛堝 VOO銆丵QQ锛変笌 A 鑲?ETF 涓嶅啀绾冲叆鍩洪噾鍏徃灞傞潰椋庨櫓锛堣瘔璁笺€佸０瑾夌瓑锛?  - 鎼滅储缁村害锛欵TF/鎸囨暟涓撶敤 risk_check銆乪arnings銆乮ndustry 鏌ヨ锛岄伩鍏嶅懡涓熀閲戠鐞嗕汉鏂伴椈
  - AI 鎻愮ず锛氭寚鏁板瀷鏍囩殑鍒嗘瀽绾︽潫锛宍risk_alerts` 涓嶅緱鍑虹幇鍩洪噾绠＄悊浜哄叕鍙哥粡钀ラ闄?
## [3.2.8] - 2026-02-21

### 淇
- 馃悰 **BOT 涓?WEB UI 鑲＄エ浠ｇ爜澶у皬鍐欑粺涓€**锛圛ssue #355锛?  - BOT `/analyze` 涓?WEB UI 瑙﹀彂鍒嗘瀽鐨勮偂绁ㄤ唬鐮佺粺涓€涓哄ぇ鍐欙紙濡?`aapl` 鈫?`AAPL`锛?  - 鏂板 `canonical_stock_code()`锛屽湪 BOT銆丄PI銆丆onfig銆丆LI銆乼ask_queue 鍏ュ彛澶勮鑼冨寲
  - 鍘嗗彶璁板綍涓庝换鍔″幓閲嶉€昏緫鍙纭瘑鍒悓涓€鑲＄エ锛堝ぇ灏忓啓涓嶅啀褰卞搷锛?
## [3.2.7] - 2026-02-20

### 鏂板
- 馃攼 **Web 椤甸潰瀵嗙爜楠岃瘉**锛圛ssue #320, #349锛?  - 鏀寔 `ADMIN_AUTH_ENABLED=true` 鍚敤 Web 鐧诲綍淇濇姢
  - 棣栨璁块棶鍦ㄧ綉椤佃缃垵濮嬪瘑鐮侊紱鏀寔銆岀郴缁熻缃?> 淇敼瀵嗙爜銆嶅拰 CLI `python -m src.auth reset_password` 閲嶇疆

## [3.2.6] - 2026-02-20
### 鈿狅笍 鐮村潖鎬у彉鏇达紙Breaking Changes锛?
- **鍘嗗彶璁板綍 API 鍙樻洿 (Issue #322)**
  - 璺敱鍙樻洿锛歚GET /api/v1/history/{query_id}` 鈫?`GET /api/v1/history/{record_id}`
  - 鍙傛暟鍙樻洿锛歚query_id` (瀛楃涓? 鈫?`record_id` (鏁存暟)
  - 鏂伴椈鎺ュ彛鍙樻洿锛歚GET /api/v1/history/{query_id}/news` 鈫?`GET /api/v1/history/{record_id}/news`
  - 鍘熷洜锛歚query_id` 鍦ㄦ壒閲忓垎鏋愭椂鍙兘閲嶅锛屾棤娉曞敮涓€鏍囪瘑鍗曟潯鍘嗗彶璁板綍銆傛敼鐢ㄦ暟鎹簱涓婚敭 `id` 纭繚鍞竴鎬?  - 褰卞搷鑼冨洿锛氫娇鐢ㄦ棫鐗堝巻鍙茶鎯?API 鐨勬墍鏈夊鎴风闇€鍚屾鏇存柊

### 淇
- 淇缇庤偂锛堝 ADBE锛夋妧鏈寚鏍囩煕鐩撅細akshare 缇庤偂澶嶆潈鏁版嵁寮傚父锛岀粺涓€缇庤偂鍘嗗彶鏁版嵁婧愪负 YFinance锛圛ssue #311锛?- 馃悰 **鍘嗗彶璁板綍鏌ヨ鍜屾樉绀洪棶棰?(Issue #322)**
  - 淇鍘嗗彶璁板綍鍒楄〃鏌ヨ涓棩鏈熶笉涓€鑷撮棶棰橈細浣跨敤鏄庡ぉ浣滀负 endDate锛岀‘淇濆寘鍚粖澶╁叏澶╃殑鏁版嵁
  - 淇鏈嶅姟鍣?UI 鎶ュ憡閫夋嫨闂锛氬師鍥犳槸澶氭潯璁板綍鍏变韩鍚屼竴 `query_id`锛屽鑷存€绘槸鏄剧ず绗竴鏉°€傜幇鏀圭敤 `analysis_history.id` 浣滀负鍞竴鏍囪瘑
  - 鍘嗗彶璇︽儏銆佹柊闂绘帴鍙ｅ強鍓嶇缁勪欢宸插叏闈㈤€傞厤 `record_id`
  - 鏂板鍚庡彴杞锛堟瘡 30s锛変笌椤甸潰鍙鎬у彉鏇存椂闈欓粯鍒锋柊鍘嗗彶鍒楄〃锛岀‘淇?CLI 鍙戣捣鐨勫垎鏋愬畬鎴愬悗鍓嶇鑳藉強鏃跺悓姝ワ紝浣跨敤 `silent` 妯″紡閬垮厤瑙﹀彂 loading 鐘舵€?- 馃悰 **缇庤偂鎸囨暟瀹炴椂琛屾儏涓庢棩绾挎暟鎹?* (Issue #273)
  - 淇 SPX銆丏JI銆両XIC銆丯DX銆乂IX銆丷UT 绛夌編鑲℃寚鏁版棤娉曡幏鍙栧疄鏃惰鎯呯殑闂
  - 鏂板 `us_index_mapping` 妯″潡锛屽皢鐢ㄦ埛杈撳叆锛堝 SPX锛夋槧灏勪负 Yahoo Finance 绗﹀彿锛堝 ^GSPC锛?  - 缇庤偂鎸囨暟涓庣編鑲¤偂绁ㄦ棩绾挎暟鎹洿鎺ヨ矾鐢辫嚦 YfinanceFetcher锛岄伩鍏嶉亶鍘嗕笉鏀寔鐨勬暟鎹簮
  - 娑堥櫎閲嶅鐨勭編鑲¤瘑鍒€昏緫锛岀粺涓€浣跨敤 `is_us_stock_code()` 鍑芥暟

### 浼樺寲
- 馃帹 **棣栭〉杈撳叆鏍忎笌 Market Sentiment 甯冨眬瀵归綈浼樺寲**
  - 鑲＄エ浠ｇ爜杈撳叆妗嗗乏缂樹笌鍘嗗彶璁板綍 glass-card 妗嗗乏瀵归綈
  - 鍒嗘瀽鎸夐挳鍙崇紭涓?Market Sentiment 澶栨鍙冲榻?  - Market Sentiment 鍗＄墖鍚戜笅鎷変几濉弧鏍煎瓙锛屾秷闄や笌 STRATEGY POINTS 涔嬮棿鐨勭┖闅?  - 绐勫睆鏃惰緭鍏ユ爮濉弧瀹藉害锛屽搷搴斿紡瀵归綈淇濇寔涓€鑷?
## [3.2.5] - 2026-02-19

### 鏂板
- 馃實 **澶х洏澶嶇洏鍙€夊尯鍩?*锛圛ssue #299锛?  - 鏀寔 `MARKET_REVIEW_REGION` 鐜鍙橀噺锛歚cn`锛圓鑲★級銆乣us`锛堢編鑲★級銆乣both`锛堜袱鑰咃級
  - us 妯″紡浣跨敤 SPX/绾虫柉杈惧厠/閬撴寚/VIX 绛夋寚鏁帮紱both 妯″紡鍙悓鏃跺鐩?A 鑲′笌缇庤偂
  - 榛樿 `cn`锛屼繚鎸佸悜鍚庡吋瀹?
## [3.2.4] - 2026-02-18

### 淇
- 馃悰 **缁熶竴缇庤偂鏁版嵁婧愪负 YFinance**锛圛ssue #311锛?  - akshare 缇庤偂澶嶆潈鏁版嵁寮傚父锛岀粺涓€缇庤偂鍘嗗彶鏁版嵁婧愪负 YFinance
  - 淇 ADBE 绛夌編鑲¤偂绁ㄦ妧鏈寚鏍囩煕鐩鹃棶棰?
## [3.2.3] - 2026-02-18

### 淇
- 馃悰 **鏍囨櫘500瀹炴椂鏁版嵁缂哄け**锛圛ssue #273锛?  - 淇 SPX銆丏JI銆両XIC銆丯DX銆乂IX銆丷UT 绛夌編鑲℃寚鏁版棤娉曡幏鍙栧疄鏃惰鎯呯殑闂
  - 鏂板 `us_index_mapping` 妯″潡锛屽皢鐢ㄦ埛杈撳叆锛堝 SPX锛夋槧灏勪负 Yahoo Finance 绗﹀彿锛堝 `^GSPC`锛?  - 缇庤偂鎸囨暟涓庣編鑲¤偂绁ㄦ棩绾挎暟鎹洿鎺ヨ矾鐢辫嚦 YfinanceFetcher锛岄伩鍏嶉亶鍘嗕笉鏀寔鐨勬暟鎹簮

## [3.2.2] - 2026-02-16

### 鏂板
- 馃搳 **PE 鎸囨爣鏀寔**锛圛ssue #296锛?  - AI System Prompt 澧炲姞 PE 浼板€煎叧娉?- 馃摪 **鏂伴椈鏃舵晥鎬х瓫鏌?*锛圛ssue #296锛?  - `NEWS_MAX_AGE_DAYS`锛氭柊闂绘渶澶ф椂鏁堬紙澶╋級锛岄粯璁?3锛岄伩鍏嶄娇鐢ㄨ繃鏃朵俊鎭?- 馃搱 **寮哄娍瓒嬪娍鑲′箹绂荤巼鏀惧**锛圛ssue #296锛?  - `BIAS_THRESHOLD`锛氫箹绂荤巼闃堝€硷紙%锛夛紝榛樿 5.0锛屽彲閰嶇疆
  - 寮哄娍瓒嬪娍鑲★紙澶氬ご鎺掑垪涓旇秼鍔垮己搴?鈮?0锛夎嚜鍔ㄦ斁瀹戒箹绂荤巼鍒?1.5 鍊?
## [3.2.1] - 2026-02-16

### 鏂板
- 馃敡 **涓滆储鎺ュ彛琛ヤ竵鍙厤缃紑鍏?*
  - 鏀寔 `EFINANCE_PATCH_ENABLED` 鐜鍙橀噺寮€鍏充笢璐㈡帴鍙ｈˉ涓侊紙榛樿 `true`锛?  - 琛ヤ竵涓嶅彲鐢ㄦ椂鍙檷绾у叧闂紝閬垮厤褰卞搷涓绘祦绋?
## [3.2.0] - 2026-02-15

### 鏂板
- 馃敀 **CI 闂ㄧ缁熶竴锛圥0锛?*
  - 鏂板 `scripts/ci_gate.sh` 浣滀负鍚庣闂ㄧ鍗曚竴鍏ュ彛
  - 涓?CI 鏀逛负 `backend-gate`銆乣docker-build`銆乣web-gate` 涓夋寮?  - CI 瑙﹀彂鏀逛负鎵€鏈?PR锛岄伩鍏?Required Checks 鍥犺矾寰勮繃婊ょ己澶辫€屽崱浣忓悎骞?  - `web-gate` 鏀寔鍓嶇璺緞鍙樻洿鎸夐渶瑙﹀彂
  - 鏂板 `network-smoke` 宸ヤ綔娴佹壙杞介潪闃绘柇缃戠粶鍦烘櫙鍥炲綊
- 馃摝 **鍙戝竷閾捐矾鏀舵暃锛圥0锛?*
  - `docker-publish` 璋冩暣涓?tag 涓昏Е鍙戯紝骞跺鍔犲彂甯冨墠闂ㄧ鏍￠獙
  - 鎵嬪姩鍙戝竷澧炲姞 `release_tag` 杈撳叆涓?semver/changelog 寮烘牎楠?  - 鍙戝竷鍓嶆柊澧?Docker smoke锛堝叧閿ā鍧楀鍏ワ級
- 馃摑 **PR 妯℃澘鍗囩骇锛圥0锛?*
  - 澧炲姞鑳屾櫙銆佽寖鍥淬€侀獙璇佸懡浠や笌缁撴灉銆佸洖婊氭柟妗堛€両ssue 鍏宠仈绛夊繀濉」
- 馃 **AI 瀹℃煡瑕嗙洊澧炲己锛圥0锛?*
  - `pr-review` 绾冲叆 `.github/workflows/**` 鑼冨洿
  - 鏂板 `AI_REVIEW_STRICT` 寮€鍏筹紝鍙€夊皢 AI 瀹℃煡澶辫触鍗囩骇涓洪樆鏂?
## [3.1.13] - 2026-02-15

### 鏂板
- 馃搳 **浠呭垎鏋愮粨鏋滄憳瑕?*锛圛ssue #262锛?  - 鏀寔 `REPORT_SUMMARY_ONLY` 鐜鍙橀噺锛岃涓?`true` 鏃跺彧鎺ㄩ€佹眹鎬伙紝涓嶅惈涓偂璇︽儏
  - 榛樿 `false`锛屽鑲℃椂閫傚悎蹇€熸祻瑙?
## [3.1.12] - 2026-02-15

### 鏂板
- 馃摟 **涓偂涓庡ぇ鐩樺鐩樺悎骞舵帹閫?*锛圛ssue #190锛?  - 鏀寔 `MERGE_EMAIL_NOTIFICATION` 鐜鍙橀噺锛岃涓?`true` 鏃跺皢涓偂鍒嗘瀽涓庡ぇ鐩樺鐩樺悎骞朵负涓€娆℃帹閫?  - 榛樿 `false`锛屽噺灏戦偖浠舵暟閲忋€侀檷浣庤璇嗗埆涓哄瀮鍦鹃偖浠剁殑椋庨櫓

## [3.1.11] - 2026-02-15

### 鏂板
- 馃 **Anthropic Claude API 鏀寔**锛圛ssue #257锛?  - 鏀寔 `ANTHROPIC_API_KEY`銆乣ANTHROPIC_MODEL`銆乣ANTHROPIC_TEMPERATURE`銆乣ANTHROPIC_MAX_TOKENS`
  - AI 鍒嗘瀽浼樺厛绾э細Gemini > Anthropic > OpenAI
- 馃摲 **浠庡浘鐗囪瘑鍒偂绁ㄤ唬鐮?*锛圛ssue #257锛?  - 涓婁紶鑷€夎偂鎴浘锛岄€氳繃 Vision LLM 鑷姩鎻愬彇鑲＄エ浠ｇ爜
  - API: `POST /api/v1/stocks/extract-from-image`锛涙敮鎸?JPEG/PNG/WebP/GIF锛屾渶澶?5MB
  - 鏀寔 `OPENAI_VISION_MODEL` 鍗曠嫭閰嶇疆鍥剧墖璇嗗埆妯″瀷
- 鈿欙笍 **閫氳揪淇℃暟鎹簮鎵嬪姩閰嶇疆**锛圛ssue #257锛?  - 鏀寔 `PYTDX_HOST`銆乣PYTDX_PORT` 鎴?`PYTDX_SERVERS` 閰嶇疆鑷缓閫氳揪淇℃湇鍔″櫒

## [3.1.10] - 2026-02-15

### 鏂板
- 鈿欙笍 **绔嬪嵆杩愯閰嶇疆**锛圛ssue #332锛?  - 鏀寔 `RUN_IMMEDIATELY` 鐜鍙橀噺锛宍true` 鏃跺畾鏃朵换鍔″惎鍔ㄥ悗绔嬪嵆鎵ц涓€娆?- 馃悰 淇 Docker 鏋勫缓闂

## [3.1.9] - 2026-02-14

### 鏂板
- 馃攲 **涓滆储鎺ュ彛琛ヤ竵鏈哄埗**
  - 鏂板 `patch/eastmoney_patch.py` 淇 efinance 涓婃父鎺ュ彛鍙樻洿
  - 涓嶅奖鍝嶅叾浠栨暟鎹簮鐨勬甯歌繍琛?
## [3.1.8] - 2026-02-14

### 鏂板
- 馃攼 **Webhook 璇佷功鏍￠獙寮€鍏?*锛圛ssue #265锛?  - 鏀寔 `WEBHOOK_VERIFY_SSL` 鐜鍙橀噺锛屽彲鍏抽棴 HTTPS 璇佷功鏍￠獙浠ユ敮鎸佽嚜绛惧悕璇佷功
  - 榛樿淇濇寔鏍￠獙锛屽叧闂瓨鍦?MITM 椋庨櫓锛屼粎寤鸿鍦ㄥ彲淇″唴缃戜娇鐢?
## [3.1.7] - 2026-02-14

### 淇
- 馃悰 淇鍖呭鍏ラ敊璇紙package import error锛?
## [3.1.6] - 2026-02-13

### 淇
- 馃悰 淇 `news_intel` 涓?`query_id` 涓嶄竴鑷撮棶棰?
## [3.1.5] - 2026-02-13

### 鏂板
- 馃摲 **Markdown 杞浘鐗囬€氱煡**锛圛ssue #289锛?  - 鏀寔 `MARKDOWN_TO_IMAGE_CHANNELS` 閰嶇疆锛屽 Telegram銆佷紒涓氬井淇°€佽嚜瀹氫箟 Webhook锛圖iscord锛夈€侀偖浠跺彂閫佸浘鐗囨牸寮忔姤鍛?  - 閭欢涓哄唴鑱旈檮浠讹紝澧炲己瀵逛笉鏀寔 HTML 瀹㈡埛绔殑鍏煎鎬?  - 闇€瀹夎 `wkhtmltopdf` 鍜?`imgkit`

## [3.1.4] - 2026-02-12

### 鏂板
- 馃摟 **鑲＄エ鍒嗙粍鍙戝線涓嶅悓閭**锛圛ssue #268锛?  - 鏀寔 `STOCK_GROUP_N` + `EMAIL_GROUP_N` 閰嶇疆锛屼笉鍚岃偂绁ㄧ粍鎶ュ憡鍙戦€佸埌瀵瑰簲閭
  - 澶х洏澶嶇洏鍙戝線鎵€鏈夐厤缃殑閭

## [3.1.3] - 2026-02-12

### 淇
- 馃悰 淇 Docker 鍐呰繍琛屾椂閫氳繃椤甸潰淇敼閰嶇疆鎶ラ敊 `[Errno 16] Device or resource busy` 鐨勯棶棰?
## [3.1.2] - 2026-02-11

### 淇
- 馃悰 淇 Docker 涓€鑷存€ч棶棰橈紝瑙ｅ喅鍏抽敭鎵规澶勭悊涓庨€氱煡 Bug

## [3.1.1] - 2026-02-11

### 鍙樻洿
- 鈾伙笍 `API_HOST` 鈫?`WEBUI_HOST`锛欴ocker Compose 閰嶇疆椤圭粺涓€

## [3.1.0] - 2026-02-11

### 鏂板
- 馃搳 **ETF 鏀寔澧炲己涓庝唬鐮佽鑼冨寲**
  - 缁熶竴鍚勬暟鎹簮 ETF 浠ｇ爜澶勭悊閫昏緫
  - 鏂板 `canonical_stock_code()` 缁熶竴浠ｇ爜鏍煎紡锛岀‘淇濇暟鎹簮璺敱姝ｇ‘

## [3.0.5] - 2026-02-08

### 淇
- 馃悰 淇淇″彿 emoji 涓庡缓璁笉涓€鑷寸殑闂锛堝鍚堝缓璁"鍗栧嚭/瑙傛湜"鏈纭槧灏勶級
- 馃悰 淇 `*ST` 鑲＄エ鍚嶅湪寰俊/Dashboard 涓?markdown 杞箟闂
- 馃悰 淇 `idx.amount` 涓?None 鏃跺ぇ鐩樺鐩?TypeError
- 馃悰 淇鍒嗘瀽 API 杩斿洖 `report=None` 鍙?ReportStrategy 绫诲瀷涓嶄竴鑷撮棶棰?- 馃悰 淇 Tushare 杩斿洖绫诲瀷閿欒锛坉ict 鈫?UnifiedRealtimeQuote锛夊強 API 绔偣鎸囧悜

### 鏂板
- 馃搳 澶х洏澶嶇洏鎶ュ憡娉ㄥ叆缁撴瀯鍖栨暟鎹紙娑ㄨ穼缁熻銆佹寚鏁拌〃鏍笺€佹澘鍧楁帓鍚嶏級
- 馃攳 鎼滅储缁撴灉 TTL 缂撳瓨锛?00 鏉′笂闄愶紝FIFO 娣樻卑锛?- 馃敡 Tushare Token 瀛樺湪鏃惰嚜鍔ㄦ敞鍏ュ疄鏃惰鎯呬紭鍏堢骇
- 馃摪 鏂伴椈鎽樿鎴柇闀垮害 50鈫?00 瀛?
### 浼樺寲
- 鈿?琛ュ厖琛屾儏瀛楁璇锋眰闄愬埗涓烘渶澶?1 娆★紝鍑忓皯鏃犳晥璇锋眰

## [3.0.4] - 2026-02-07

### 鏂板
- 馃搱 **鍥炴祴寮曟搸** (PR #269)
  - 鏂板鍩轰簬鍘嗗彶鍒嗘瀽璁板綍鐨勫洖娴嬬郴缁燂紝鏀寔鏀剁泭鐜囥€佽儨鐜囥€佹渶澶у洖鎾ょ瓑鎸囨爣璇勪及
  - WebUI 闆嗘垚鍥炴祴缁撴灉灞曠ず

## [3.0.3] - 2026-02-07

### 淇
- 馃悰 淇鐙欏嚮鐐逛綅鏁版嵁瑙ｆ瀽閿欒闂 (PR #271)

## [3.0.2] - 2026-02-06

### 鏂板
- 鉁夛笍 鍙厤缃偖浠跺彂閫佽€呭悕绉?(PR #272)
- 馃寪 澶栧浗鑲＄エ鏀寔鑻辨枃鍏抽敭璇嶆悳绱?
## [3.0.1] - 2026-02-06

### 淇
- 馃悰 淇 ETF 瀹炴椂琛屾儏鑾峰彇銆佸競鍦烘暟鎹洖閫€銆佷紒涓氬井淇℃秷鎭垎鍧楅棶棰?- 馃敡 CI 娴佺▼绠€鍖?
## [3.0.0] - 2026-02-06

### 绉婚櫎
- 馃棏锔?**绉婚櫎鏃х増 WebUI**
  - 鍒犻櫎鍩轰簬 `http.server.ThreadingHTTPServer` 鐨勬棫鐗?WebUI锛坄web/` 鍖咃級
  - 鏃х増 WebUI 鐨勫姛鑳藉凡瀹屽叏琚?FastAPI锛坄api/`锛? React 鍓嶇鏇夸唬
  - `--webui` / `--webui-only` 鍛戒护琛屽弬鏁版爣璁颁负寮冪敤锛岃嚜鍔ㄩ噸瀹氬悜鍒?`--serve` / `--serve-only`
  - `WEBUI_ENABLED` / `WEBUI_HOST` / `WEBUI_PORT` 鐜鍙橀噺淇濇寔鍏煎锛岃嚜鍔ㄨ浆鍙戝埌 FastAPI 鏈嶅姟
  - `webui.py` 淇濈暀涓哄吋瀹瑰叆鍙ｏ紝鍚姩鏃剁洿鎺ヨ皟鐢?FastAPI 鍚庣
  - Docker Compose 涓Щ闄?`webui` 鏈嶅姟瀹氫箟锛岀粺涓€浣跨敤 `server` 鏈嶅姟

### 鍙樻洿
- 鈾伙笍 **鏈嶅姟灞傞噸鏋?*
  - 灏?`web/services.py` 涓殑寮傛浠诲姟鏈嶅姟杩佺Щ鑷?`src/services/task_service.py`
  - Bot 鍒嗘瀽鍛戒护锛坄bot/commands/analyze.py`锛夋敼涓轰娇鐢?`src.services.task_service`
  - Docker 鐜鍙橀噺 `WEBUI_HOST`/`WEBUI_PORT` 鏇村悕涓?`API_HOST`/`API_PORT`锛堟棫鍚嶄粛鍏煎锛?
## [2.3.0] - 2026-02-01

### 鏂板
- 馃嚭馃嚫 **澧炲己缇庤偂鏀寔** (Issue #153)
  - 瀹炵幇鍩轰簬 Akshare 鐨勭編鑲″巻鍙叉暟鎹幏鍙?(`ak.stock_us_daily()`)
  - 瀹炵幇鍩轰簬 Yfinance 鐨勭編鑲″疄鏃惰鎯呰幏鍙栵紙浼樺厛绛栫暐锛?  - 澧炲姞瀵逛笉鏀寔鏁版嵁婧愶紙Tushare/Baostock/Pytdx/Efinance锛夌殑缇庤偂浠ｇ爜杩囨护鍜屽揩閫熼檷绾?
### 淇
- 馃悰 淇 AMD 绛夌編鑲′唬鐮佽璇瘑鍒负 A 鑲＄殑闂 (Issue #153)

## [2.2.5] - 2026-02-01

### 鏂板
- 馃 **AstrBot 娑堟伅鎺ㄩ€?* (PR #217)
  - 鏂板 AstrBot 閫氱煡娓犻亾锛屾敮鎸佹帹閫佸埌 QQ 鍜屽井淇?  - 鏀寔 HMAC SHA256 绛惧悕楠岃瘉锛岀‘淇濋€氫俊瀹夊叏
  - 閫氳繃 `ASTRBOT_URL` 鍜?`ASTRBOT_TOKEN` 閰嶇疆

## [2.2.4] - 2026-02-01

### 鏂板
- 鈿欙笍 **鍙厤缃暟鎹簮浼樺厛绾?* (PR #215)
  - 鏀寔閫氳繃鐜鍙橀噺锛堝 `YFINANCE_PRIORITY=0`锛夊姩鎬佽皟鏁存暟鎹簮浼樺厛绾?  - 鏃犻渶淇敼浠ｇ爜鍗冲彲浼樺厛浣跨敤鐗瑰畾鏁版嵁婧愶紙濡?Yahoo Finance锛?
## [2.2.3] - 2026-01-31

### 淇
- 馃摝 鏇存柊 requirements.txt锛屽鍔?`lxml_html_clean` 渚濊禆浠ヨВ鍐冲吋瀹规€ч棶棰?
## [2.2.2] - 2026-01-31

### 淇
- 馃悰 淇浠ｇ悊閰嶇疆鍖哄垎澶у皬鍐欓棶棰?(fixes #211)

## [2.2.1] - 2026-01-31

### 淇
- 馃悰 **YFinance 鍏煎鎬т慨澶?* (PR #210, fixes #209)
  - 淇鏂扮増 yfinance 杩斿洖 MultiIndex 鍒楀悕瀵艰嚧鐨勬暟鎹В鏋愰敊璇?
## [2.2.0] - 2026-01-31

### 鏂板
- 馃攧 **澶氭簮鍥為€€绛栫暐澧炲己**
  - 瀹炵幇浜嗘洿鍋ュ．鐨勬暟鎹幏鍙栧洖閫€鏈哄埗 (feat: multi-source fallback strategy)
  - 浼樺寲浜嗘暟鎹簮鏁呴殰鏃剁殑鑷姩鍒囨崲閫昏緫

### 淇
- 馃悰 淇 analyzer 杩愯鍚庢棤娉曢€氳繃鏀?.env 鏂囦欢鐨?stock_list 鍐呭璋冩暣璺熻釜鐨勮偂绁?
## [2.1.14] - 2026-01-31

### 鏂囨。
- 馃摑 鏇存柊 README 鍜屼紭鍖?auto-tag 瑙勫垯

## [2.1.13] - 2026-01-31

### 淇
- 馃悰 **Tushare 浼樺厛绾т笌瀹炴椂琛屾儏** (Fixed #185)
  - 淇 Tushare 鏁版嵁婧愪紭鍏堢骇璁剧疆闂
  - 淇 Tushare 瀹炴椂琛屾儏鑾峰彇鍔熻兘

## [2.1.12] - 2026-01-30

### 淇
- 馃寪 淇浠ｇ悊閰嶇疆鍦ㄦ煇浜涙儏鍐典笅鐨勫尯鍒嗗ぇ灏忓啓闂
- 馃寪 淇鏈湴鐜绂佺敤浠ｇ悊鐨勯€昏緫

## [2.1.11] - 2026-01-30

### 浼樺寲
- 馃殌 **椋炰功娑堟伅娴佷紭鍖?* (PR #192)
  - 浼樺寲椋炰功 Stream 妯″紡鐨勬秷鎭被鍨嬪鐞?  - 淇敼 Stream 娑堟伅妯″紡榛樿涓哄叧闂紝闃叉閰嶇疆閿欒杩愯鏃舵姤閿?
## [2.1.10] - 2026-01-30

### 鍚堝苟
- 馃摝 鍚堝苟 PR #154 璐＄尞

## [2.1.9] - 2026-01-30

### 鏂板
- 馃挰 **寰俊鏂囨湰娑堟伅鏀寔** (PR #137)
  - 鏂板寰俊鎺ㄩ€佺殑绾枃鏈秷鎭被鍨嬫敮鎸?  - 娣诲姞 `WECHAT_MSG_TYPE` 閰嶇疆椤?
## [2.1.8] - 2026-01-30

### 淇
- 馃悰 淇鏃ュ織涓?API 鎻愪緵鍟嗘樉绀洪敊璇?(PR #197)

## [2.1.7] - 2026-01-30

### 淇
- 馃寪 绂佺敤鏈湴鐜鐨勪唬鐞嗚缃紝閬垮厤缃戠粶杩炴帴闂

## [2.1.6] - 2026-01-29

### 鏂板
- 馃摗 **Pytdx 鏁版嵁婧?(Priority 2)**
  - 鏂板閫氳揪淇℃暟鎹簮锛屽厤璐规棤闇€娉ㄥ唽
  - 澶氭湇鍔″櫒鑷姩鍒囨崲
  - 鏀寔瀹炴椂琛屾儏鍜屽巻鍙叉暟鎹?- 馃彿锔?**澶氭簮鑲＄エ鍚嶇О瑙ｆ瀽**
  - DataFetcherManager 鏂板 `get_stock_name()` 鏂规硶
  - 鏂板 `batch_get_stock_names()` 鎵归噺鏌ヨ
  - 鑷姩鍦ㄥ鏁版嵁婧愰棿鍥為€€
  - Tushare 鍜?Baostock 鏂板鑲＄エ鍚嶇О/鍒楄〃鏂规硶
- 馃攳 **澧炲己鎼滅储鍥為€€**
  - 鏂板 `search_stock_price_fallback()` 鐢ㄤ簬鏁版嵁婧愬叏閮ㄥけ璐ユ椂
  - 鏂板鎼滅储缁村害锛氬競鍦哄垎鏋愩€佽涓氬垎鏋?  - 鏈€澶ф悳绱㈡鏁颁粠 3 澧炲姞鍒?5
  - 鏀硅繘鎼滅储缁撴灉鏍煎紡锛堟瘡缁村害 4 鏉＄粨鏋滐級

### 鏀硅繘
- 鏇存柊鎼滅储鏌ヨ妯℃澘浠ユ彁楂樼浉鍏虫€?- 澧炲己 `format_intel_report()` 杈撳嚭缁撴瀯

## [2.1.5] - 2026-01-29

### 鏂板
- 馃摗 鏂板 Pytdx 鏁版嵁婧愬拰澶氭簮鑲＄エ鍚嶇О瑙ｆ瀽鍔熻兘

## [2.1.4] - 2026-01-29

### 鏂囨。
- 馃摑 鏇存柊璧炲姪鍟嗕俊鎭?
## [2.1.3] - 2026-01-28

### 鏂囨。
- 馃摑 閲嶆瀯 README 甯冨眬
- 馃寪 鏂板绻佷綋涓枃缈昏瘧 (README_CHT.md)

### 淇
- 馃悰 淇 WebUI 鏃犳硶杈撳叆缇庤偂浠ｇ爜闂
  - 杈撳叆妗嗛€昏緫鏀规垚鎵€鏈夊瓧姣嶉兘杞崲鎴愬ぇ鍐?  - 鏀寔 `.` 鐨勮緭鍏ワ紙濡?`BRK.B`锛?
## [2.1.2] - 2026-01-27

### 淇
- 馃悰 淇涓偂鍒嗘瀽鎺ㄩ€佸け璐ュ拰鎶ュ憡璺緞闂 (fixes #166)
- 馃悰 淇敼 CR 閿欒锛岀‘淇濆井淇℃秷鎭渶澶у瓧鑺傞厤缃敓鏁?
## [2.1.1] - 2026-01-26

### 鏂板
- 馃敡 娣诲姞 GitHub Actions auto-tag 宸ヤ綔娴?- 馃摗 娣诲姞 yfinance 鍏滃簳鏁版嵁婧愬強鏁版嵁缂哄け璀﹀憡

### 淇
- 馃惓 淇 docker-compose 璺緞鍜屾枃妗ｅ懡浠?- 馃惓 Dockerfile 琛ュ厖 copy src 鏂囦欢澶?(fixes #145)

## [2.1.0] - 2026-01-25

### 鏂板
- 馃嚭馃嚫 **缇庤偂鍒嗘瀽鏀寔**
  - 鏀寔缇庤偂浠ｇ爜鐩存帴杈撳叆锛堝 `AAPL`, `TSLA`锛?  - 浣跨敤 YFinance 浣滀负缇庤偂鏁版嵁婧?- 馃搱 **MACD 鍜?RSI 鎶€鏈寚鏍?*
  - MACD锛氳秼鍔跨‘璁ゃ€侀噾鍙夋鍙変俊鍙凤紙闆惰酱涓婇噾鍙夆瓙銆侀噾鍙夆渽銆佹鍙夆潓锛?  - RSI锛氳秴涔拌秴鍗栧垽鏂紙瓒呭崠猸愩€佸己鍔库渽銆佽秴涔扳殸锔忥級
  - 鎸囨爣淇″彿绾冲叆缁煎悎璇勫垎绯荤粺
- 馃幃 **Discord 鎺ㄩ€佹敮鎸?* (PR #124, #125, #144)
  - 鏀寔 Discord Webhook 鍜?Bot API 涓ょ鏂瑰紡
  - 閫氳繃 `DISCORD_WEBHOOK_URL` 鎴?`DISCORD_BOT_TOKEN` + `DISCORD_MAIN_CHANNEL_ID` 閰嶇疆
- 馃 **鏈哄櫒浜哄懡浠や氦浜?*
  - 閽夐拤鏈哄櫒浜烘敮鎸?`/鍒嗘瀽 鑲＄エ浠ｇ爜` 鍛戒护瑙﹀彂鍒嗘瀽
  - 鏀寔 Stream 闀胯繛鎺ユā寮?- 馃尅锔?**AI 娓╁害鍙傛暟鍙厤缃?* (PR #142)
  - 鏀寔鑷畾涔?AI 妯″瀷娓╁害鍙傛暟
- 馃惓 **Zeabur 閮ㄧ讲鏀寔**
  - 娣诲姞 Zeabur 闀滃儚閮ㄧ讲宸ヤ綔娴?  - 鏀寔 commit hash 鍜?latest 鍙屾爣绛?
### 閲嶆瀯
- 馃彈锔?**椤圭洰缁撴瀯浼樺寲**
  - 鏍稿績浠ｇ爜绉昏嚦 `src/` 鐩綍锛屾牴鐩綍鏇存竻鐖?  - 鏂囨。绉昏嚦 `docs/` 鐩綍
  - Docker 閰嶇疆绉昏嚦 `docker/` 鐩綍
  - 淇鎵€鏈?import 璺緞锛屼繚鎸佸悜鍚庡吋瀹?- 馃攧 **鏁版嵁婧愭灦鏋勫崌绾?*
  - 鏂板鏁版嵁婧愮啍鏂満鍒讹紝鍗曟暟鎹簮杩炵画澶辫触鑷姩鍒囨崲
  - 瀹炴椂琛屾儏缂撳瓨浼樺寲锛屾壒閲忛鍙栧噺灏?API 璋冪敤
  - 缃戠粶浠ｇ悊鏅鸿兘鍒嗘祦锛屽浗鍐呮帴鍙ｈ嚜鍔ㄧ洿杩?- 馃 Discord 鏈哄櫒浜洪噸鏋勪负骞冲彴閫傞厤鍣ㄦ灦鏋?
### 淇
- 馃寪 **缃戠粶绋冲畾鎬у寮?*
  - 鑷姩妫€娴嬩唬鐞嗛厤缃紝瀵瑰浗鍐呰鎯呮帴鍙ｅ己鍒剁洿杩?  - 淇 EfinanceFetcher 鍋跺彂鐨?`ProtocolError`
  - 澧炲姞瀵瑰簳灞傜綉缁滈敊璇殑鎹曡幏鍜岄噸璇曟満鍒?- 馃摟 **閭欢娓叉煋浼樺寲**
  - 淇閭欢涓〃鏍间笉娓叉煋闂 (#134)
  - 浼樺寲閭欢鎺掔増锛屾洿绱у噾缇庤
- 馃摙 **浼佷笟寰俊鎺ㄩ€佷慨澶?*
  - 淇澶х洏澶嶇洏鎺ㄩ€佷笉瀹屾暣闂
  - 澧炲己娑堟伅鍒嗗壊閫昏緫锛屾敮鎸佹洿澶氭爣棰樻牸寮?  - 澧炲姞鍒嗘壒鍙戦€侀棿闅旓紝閬垮厤闄愭祦涓㈠け
- 馃懛 **CI/CD 淇**
  - 淇 GitHub Actions 涓矾寰勫紩鐢ㄧ殑閿欒

## [2.0.0] - 2026-01-24

### 鏂板
- 馃嚭馃嚫 **缇庤偂鍒嗘瀽鏀寔**
  - 鏀寔缇庤偂浠ｇ爜鐩存帴杈撳叆锛堝 `AAPL`, `TSLA`锛?  - 浣跨敤 YFinance 浣滀负缇庤偂鏁版嵁婧?- 馃 **鏈哄櫒浜哄懡浠や氦浜?* (PR #113)
  - 閽夐拤鏈哄櫒浜烘敮鎸?`/鍒嗘瀽 鑲＄エ浠ｇ爜` 鍛戒护瑙﹀彂鍒嗘瀽
  - 鏀寔 Stream 闀胯繛鎺ユā寮?  - 鏀寔閫夋嫨绮剧畝鎶ュ憡鎴栧畬鏁存姤鍛?- 馃幃 **Discord 鎺ㄩ€佹敮鎸?* (PR #124)
  - 鏀寔 Discord Webhook 鎺ㄩ€?  - 娣诲姞 Discord 鐜鍙橀噺鍒板伐浣滄祦

### 淇
- 馃惓 淇 WebUI 鍦?Docker 涓粦瀹?0.0.0.0 (fixed #118)
- 馃敂 淇椋炰功闀胯繛鎺ラ€氱煡闂
- 馃悰 淇 `analysis_delay` 鏈畾涔夐敊璇?- 馃敡 鍚姩鏃?config.py 妫€娴嬮€氱煡娓犻亾锛屼慨澶嶅凡閰嶇疆鑷畾涔夋笭閬撴儏鍐典笅浠嶇劧鎻愮ず鏈厤缃棶棰?
### 鏀硅繘
- 馃敡 浼樺寲 Tushare 浼樺厛绾у垽鏂€昏緫锛屾彁鍗囧皝瑁呮€?- 馃敡 淇 Tushare 浼樺厛绾ф彁鍗囧悗浠嶆帓鍦?Efinance 涔嬪悗鐨勯棶棰?- 鈿欙笍 閰嶇疆 TUSHARE_TOKEN 鏃惰嚜鍔ㄦ彁鍗?Tushare 鏁版嵁婧愪紭鍏堢骇
- 鈿欙笍 瀹炵幇 4 涓敤鎴峰弽棣?issue (#112, #128, #38, #119)

## [1.6.0] - 2026-01-19

### 鏂板
- 馃枼锔?WebUI 绠＄悊鐣岄潰鍙?API 鏀寔锛圥R #72锛?  - 鍏ㄦ柊 Web 鏋舵瀯锛氬垎灞傝璁★紙Server/Router/Handler/Service锛?  - 鏍稿績 API锛氭敮鎸?`/analysis` (瑙﹀彂鍒嗘瀽), `/tasks` (鏌ヨ杩涘害), `/health` (鍋ュ悍妫€鏌?
  - 浜や簰鐣岄潰锛氭敮鎸侀〉闈㈢洿鎺ヨ緭鍏ヤ唬鐮佸苟瑙﹀彂鍒嗘瀽锛屽疄鏃跺睍绀鸿繘搴?  - 杩愯妯″紡锛氭柊澧?`--webui-only` 妯″紡锛屼粎鍚姩 Web 鏈嶅姟
  - 瑙ｅ喅浜?[#70](https://github.com/ZhuLinsen/daily_stock_analysis/issues/70) 鐨勬牳蹇冮渶姹傦紙鎻愪緵瑙﹀彂鍒嗘瀽鐨勬帴鍙ｏ級
- 鈿欙笍 GitHub Actions 閰嶇疆鐏垫椿鎬у寮猴紙[#79](https://github.com/ZhuLinsen/daily_stock_analysis/issues/79)锛?  - 鏀寔浠?Repository Variables 璇诲彇闈炴晱鎰熼厤缃紙濡?STOCK_LIST, GEMINI_MODEL锛?  - 淇濇寔瀵?Secrets 鐨勫悜涓嬪吋瀹?
### 淇
- 馃悰 淇浼佷笟寰俊/椋炰功鎶ュ憡鎴柇闂锛圼#73](https://github.com/ZhuLinsen/daily_stock_analysis/issues/73)锛?  - 绉婚櫎 notification.py 涓笉蹇呰鐨勯暱搴︾‖鎴柇閫昏緫
  - 渚濊禆搴曞眰鑷姩鍒嗙墖鏈哄埗澶勭悊闀挎秷鎭?- 馃悰 淇 GitHub Workflow 鐜鍙橀噺缂哄け锛圼#80](https://github.com/ZhuLinsen/daily_stock_analysis/issues/80)锛?  - 淇 `CUSTOM_WEBHOOK_BEARER_TOKEN` 鏈纭紶閫掑埌 Runner 鐨勯棶棰?
## [1.5.0] - 2026-01-17

### 鏂板
- 馃摬 鍗曡偂鎺ㄩ€佹ā寮忥紙[#55](https://github.com/ZhuLinsen/daily_stock_analysis/issues/55)锛?  - 姣忓垎鏋愬畬涓€鍙偂绁ㄧ珛鍗虫帹閫侊紝涓嶇敤绛夊叏閮ㄥ垎鏋愬畬
  - 鍛戒护琛屽弬鏁帮細`--single-notify`
  - 鐜鍙橀噺锛歚SINGLE_STOCK_NOTIFY=true`
- 馃攼 鑷畾涔?Webhook Bearer Token 璁よ瘉锛圼#51](https://github.com/ZhuLinsen/daily_stock_analysis/issues/51)锛?  - 鏀寔闇€瑕?Token 璁よ瘉鐨?Webhook 绔偣
  - 鐜鍙橀噺锛歚CUSTOM_WEBHOOK_BEARER_TOKEN`

## [1.4.0] - 2026-01-17

### 鏂板
- 馃摫 Pushover 鎺ㄩ€佹敮鎸侊紙PR #26锛?  - 鏀寔 iOS/Android 璺ㄥ钩鍙版帹閫?  - 閫氳繃 `PUSHOVER_USER_KEY` 鍜?`PUSHOVER_API_TOKEN` 閰嶇疆
- 馃攳 鍗氭煡鎼滅储 API 闆嗘垚锛圥R #27锛?  - 涓枃鎼滅储浼樺寲锛屾敮鎸?AI 鎽樿
  - 閫氳繃 `BOCHA_API_KEYS` 閰嶇疆
- 馃搳 Efinance 鏁版嵁婧愭敮鎸侊紙PR #59锛?  - 鏂板 efinance 浣滀负鏁版嵁婧愰€夐」
- 馃嚟馃嚢 娓偂鏀寔锛圥R #17锛?  - 鏀寔 5 浣嶄唬鐮佹垨 HK 鍓嶇紑锛堝 `hk00700`銆乣hk1810`锛?
### 淇
- 馃敡 椋炰功 Markdown 娓叉煋浼樺寲锛圥R #34锛?  - 浣跨敤浜や簰鍗＄墖鍜屾牸寮忓寲鍣ㄤ慨澶嶆覆鏌撻棶棰?- 鈾伙笍 鑲＄エ鍒楄〃鐑噸杞斤紙PR #42 淇锛?  - 鍒嗘瀽鍓嶈嚜鍔ㄩ噸杞?`STOCK_LIST` 閰嶇疆
- 馃悰 閽夐拤 Webhook 20KB 闄愬埗澶勭悊
  - 闀挎秷鎭嚜鍔ㄥ垎鍧楀彂閫侊紝閬垮厤琚埅鏂?- 馃攧 AkShare API 閲嶈瘯鏈哄埗澧炲己
  - 娣诲姞澶辫触缂撳瓨锛岄伩鍏嶉噸澶嶈姹傚け璐ユ帴鍙?
### 鏀硅繘
- 馃摑 README 绮剧畝浼樺寲
  - 楂樼骇閰嶇疆绉昏嚦 `docs/full-guide.md`


## [1.3.0] - 2026-01-12

### 鏂板
- 馃敆 鑷畾涔?Webhook 鏀寔
  - 鏀寔浠绘剰 POST JSON 鐨?Webhook 绔偣
  - 鑷姩璇嗗埆閽夐拤銆丏iscord銆丼lack銆丅ark 绛夊父瑙佹湇鍔℃牸寮?  - 鏀寔閰嶇疆澶氫釜 Webhook锛堥€楀彿鍒嗛殧锛?  - 閫氳繃 `CUSTOM_WEBHOOK_URLS` 鐜鍙橀噺閰嶇疆

### 淇
- 馃摑 浼佷笟寰俊闀挎秷鎭垎鎵瑰彂閫?  - 瑙ｅ喅鑷€夎偂杩囧鏃跺唴瀹硅秴杩?4096 瀛楃闄愬埗瀵艰嚧鎺ㄩ€佸け璐ョ殑闂
  - 鏅鸿兘鎸夎偂绁ㄥ垎鏋愬潡鍒嗗壊锛屾瘡鎵规坊鍔犲垎椤垫爣璁帮紙濡?1/3, 2/3锛?  - 鎵规闂撮殧 1 绉掞紝閬垮厤瑙﹀彂棰戠巼闄愬埗

## [1.2.0] - 2026-01-11

### 鏂板
- 馃摙 澶氭笭閬撴帹閫佹敮鎸?  - 浼佷笟寰俊 Webhook
  - 椋炰功 Webhook锛堟柊澧烇級
  - 閭欢 SMTP锛堟柊澧烇級
  - 鑷姩璇嗗埆娓犻亾绫诲瀷锛岄厤缃洿绠€鍗?
### 鏀硅繘
- 缁熶竴浣跨敤 `NOTIFICATION_URL` 閰嶇疆锛屽吋瀹规棫鐨?`WECHAT_WEBHOOK_URL`
- 閭欢鏀寔 Markdown 杞?HTML 娓叉煋

## [1.1.0] - 2026-01-11

### 鏂板
- 馃 OpenAI 鍏煎 API 鏀寔
  - 鏀寔 DeepSeek銆侀€氫箟鍗冮棶銆丮oonshot銆佹櫤璋?GLM 绛?  - Gemini 鍜?OpenAI 鏍煎紡浜岄€変竴
  - 鑷姩闄嶇骇閲嶈瘯鏈哄埗

## [1.0.0] - 2026-01-10

### 鏂板
- 馃幆 AI 鍐崇瓥浠〃鐩樺垎鏋?  - 涓€鍙ヨ瘽鏍稿績缁撹
  - 绮剧‘涔板叆/姝㈡崯/鐩爣鐐逛綅
  - 妫€鏌ユ竻鍗曪紙鉁呪殸锔忊潓锛?  - 鍒嗘寔浠撳缓璁紙绌轰粨鑰?vs 鎸佷粨鑰咃級
- 馃搳 澶х洏澶嶇洏鍔熻兘
  - 涓昏鎸囨暟琛屾儏
  - 娑ㄨ穼缁熻
  - 鏉垮潡娑ㄨ穼姒?  - AI 鐢熸垚澶嶇洏鎶ュ憡
- 馃攳 澶氭暟鎹簮鏀寔
  - AkShare锛堜富鏁版嵁婧愶紝鍏嶈垂锛?  - Tushare Pro
  - Baostock
  - YFinance
- 馃摪 鏂伴椈鎼滅储鏈嶅姟
  - Tavily API
  - SerpAPI
- 馃挰 浼佷笟寰俊鏈哄櫒浜烘帹閫?- 鈴?瀹氭椂浠诲姟璋冨害
- 馃惓 Docker 閮ㄧ讲鏀寔
- 馃殌 GitHub Actions 闆舵垚鏈儴缃?
### 鎶€鏈壒鎬?- Gemini AI 妯″瀷锛坓emini-3-flash-preview锛?- 429 闄愭祦鑷姩閲嶈瘯 + 妯″瀷鍒囨崲
- 璇锋眰闂村欢鏃堕槻灏佺
- 澶?API Key 璐熻浇鍧囪　
- SQLite 鏈湴鏁版嵁瀛樺偍

---

[Unreleased]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.18.0...HEAD
[3.18.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.17.1...v3.18.0
[3.17.1]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.17.0...v3.17.1
[3.17.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.16.0...v3.17.0
[3.16.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.15.0...v3.16.0
[3.15.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.14.2...v3.15.0
[3.14.2]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.14.1...v3.14.2
[3.14.1]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.14.0...v3.14.1
[3.14.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.13.0...v3.14.0
[3.13.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.12.0...v3.13.0
[3.12.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.11.0...v3.12.0
[3.11.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.10.1...v3.11.0
[3.10.1]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.10.0...v3.10.1
[3.10.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.9.0...v3.10.0
[3.9.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.8.0...v3.9.0
[3.8.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.7.0...v3.8.0
[3.7.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.6.0...v3.7.0
[3.6.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.5.0...v3.6.0
[3.5.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.4.10...v3.5.0
[3.4.10]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.4.9...v3.4.10
[3.4.9]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.4.8...v3.4.9
[3.4.8]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.4.7...v3.4.8
[3.4.7]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.4.0...v3.4.7
[3.4.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.3.22...v3.4.0
[3.3.22]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.3.12...v3.3.22
[3.3.12]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.2.11...v3.3.12
[3.2.11]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v3.2.10...v3.2.11
[2.3.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v2.2.5...v2.3.0
[2.2.5]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v2.2.4...v2.2.5
[2.2.4]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v2.2.3...v2.2.4
[2.2.3]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v2.2.2...v2.2.3
[2.2.2]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v2.2.1...v2.2.2
[2.2.1]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v2.2.0...v2.2.1
[2.2.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v2.1.14...v2.2.0
[2.1.14]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v2.1.13...v2.1.14
[2.1.13]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v2.1.12...v2.1.13
[2.1.12]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v2.1.11...v2.1.12
[2.1.11]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v2.1.10...v2.1.11
[2.1.10]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v2.1.9...v2.1.10
[2.1.9]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v2.1.8...v2.1.9
[2.1.8]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v2.1.7...v2.1.8
[2.1.7]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v2.1.6...v2.1.7
[2.1.6]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v2.1.5...v2.1.6
[2.1.5]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v2.1.4...v2.1.5
[2.1.4]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v2.1.3...v2.1.4
[2.1.3]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v2.1.2...v2.1.3
[2.1.2]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v2.1.1...v2.1.2
[2.1.1]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v2.1.0...v2.1.1
[2.1.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v1.6.0...v2.0.0
[1.6.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v1.5.0...v1.6.0
[1.5.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v1.4.0...v1.5.0
[1.4.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v1.3.0...v1.4.0
[1.3.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/ZhuLinsen/daily_stock_analysis/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/ZhuLinsen/daily_stock_analysis/releases/tag/v1.0.0

