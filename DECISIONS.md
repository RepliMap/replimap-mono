# DECISIONS.md

执行中的决策与偏离留痕。格式:`YYYY-MM-DD | 类型(review/deviation) | 决策点 | 方案/偏离内容 | 结论 | 关键理由`

2026-07-09 | deviation | 检查清单 §1.4 要求 roll prod webhook secret | 未 roll,以证据关闭 | 采纳 | 401 失配端点 we_1SnXkb... 是 sandbox 账号端点且已删除;live 端点验签成功有 prod D1 processed_events 五类事件实证;roll 反而引入换密窗口风险。唯一残项(live 端点是否订阅 customer.deleted)留人工。
2026-07-09 | deviation | followups §4 建议把 RATE_LIMIT_DISABLED 改名 DEV_BYPASS_RATE_LIMIT | 未改名,仅加 CI grep guard | 采纳 | 改名会动 dev/test 既有引用,收益低于风险;CI guard 已覆盖"误上 prod"同一风险面。
2026-07-09 | deviation | B-2 nbf 回溯量在 60-300s 区间选值 | 取 300s(NBF_LEEWAY_SECONDS) | 采纳 | 与 CLI 侧 v0.4.3 的 300s leeway 常数对齐;nbf 仅防提前使用,回溯 300s 无安全代价,skew 容忍度最大化。
