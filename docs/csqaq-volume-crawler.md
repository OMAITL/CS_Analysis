# CSQAQ 成交量抓取脚本

本仓库提供了一个基于 CSQAQ Open API 的成交量导出脚本：

```bash
python tools/export_csqaq_volume.py
```

相比直接去抓 `https://csqaq.com/home` 页面里的 Canvas 图表，这个脚本直接调用站点背后的结构化接口，稳定性更高，也更适合做日频数据落库。

## 前置条件

1. 在 `.env` 中配置 `CSQAQ_API_TOKEN`
2. 可选配置：

```bash
CSQAQ_BASE_URL=https://api.csqaq.com
CSQAQ_PRICE_PLATFORM=yyyp
CSQAQ_CACHE_DB=data/cs_csqaq_cache.db
```

`.env.example` 已经包含这些字段，无需新增配置项。

## 1. 导出饰品指数日成交量

首页“饰品指数”默认使用 `sub_index_id=1`：

```bash
python tools/export_csqaq_volume.py index --sub-index-id 1 --output data/csqaq_index_daily_volume.csv
```

输出列：

- `sub_index_id`
- `date`
- `volume`
- `close`
- `amount`
- `pct_chg`

## 2. 导出单个饰品每日成交量

按饰品名称或 `market_hash_name` 导出：

```bash
python tools/export_csqaq_volume.py item --item-query "AK-47 | Redline (Field-Tested)" --platform yyyp --period-days 365
```

如果你已经知道 `good_id`，也可以直接传：

```bash
python tools/export_csqaq_volume.py item --good-id 135
```

输出列：

- `good_id`
- `item_name`
- `market_hash_name`
- `platform`
- `date`
- `volume`
- `close`
- `amount`
- `pct_chg`
- `volume_source`

其中：

- `volume_source=turnover_number` 表示使用了真实成交量序列
- `volume_source=sell_num` 表示接口没有返回成交量时，退化为卖单数量快照

## 3. 批量导出多个饰品

可以重复传多个 `--item-query`：

```bash
python tools/export_csqaq_volume.py batch --item-query "AK-47 | Redline (Field-Tested)" --item-query "AWP | Asiimov (Field-Tested)"
```

也可以准备一个文本文件，每行一个饰品名：

```text
AK-47 | Redline (Field-Tested)
AWP | Asiimov (Field-Tested)
```

然后执行：

```bash
python tools/export_csqaq_volume.py batch --item-file items.txt
```

批量模式会在输出目录中生成：

- 每个饰品单独的 CSV
- `combined_daily_volume.csv`
- `manifest.csv`

## 说明

- 脚本内部已经复用了仓库现有的 `market_provider/csqaq` client、限频和缓存逻辑。
- 指数成交量来自原生指数 K 线接口。
- 饰品日成交量优先使用 `turnover_number`，没有返回时自动降级。
