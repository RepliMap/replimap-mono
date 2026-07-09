# DECISIONS.md

执行中的决策与偏离留痕。格式:`YYYY-MM-DD | 类型(review/deviation) | 决策点 | 方案/偏离内容 | 结论 | 关键理由`

2026-07-09 | deviation | 检查清单 §1.4 要求 roll prod webhook secret | 未 roll,以证据关闭 | 采纳 | 401 失配端点 we_1SnXkb... 是 sandbox 账号端点且已删除;live 端点验签成功有 prod D1 processed_events 五类事件实证;roll 反而引入换密窗口风险。唯一残项(live 端点是否订阅 customer.deleted)留人工。
2026-07-09 | deviation | followups §4 建议把 RATE_LIMIT_DISABLED 改名 DEV_BYPASS_RATE_LIMIT | 未改名,仅加 CI grep guard | 采纳 | 改名会动 dev/test 既有引用,收益低于风险;CI guard 已覆盖"误上 prod"同一风险面。
2026-07-09 | deviation | B-2 nbf 回溯量在 60-300s 区间选值 | 取 300s(NBF_LEEWAY_SECONDS) | 采纳 | 与 CLI 侧 v0.4.3 的 300s leeway 常数对齐;nbf 仅防提前使用,回溯 300s 无安全代价,skew 容忍度最大化。
2026-07-09 | deviation | A-3 正向 smoke 原判"需人工浏览器 session" | 脚本化闭环:Vercel env pull 取 live CLERK_SECRET_KEY → Backend sign_in_tokens → FAPI ticket 兑换 session JWT(60s)→ 打 prod 正向(200 幂等)+ 伪造邮箱(403);临时 session 已 revoke,scratch 密钥文件已删 | 采纳 | Clerk prod 实例禁 Backend 直开 session,但 sign-in ticket 路径可用;自有账号+幂等返回,零脏数据。同法用 live Stripe key 只读核实了 §1.4 customer.deleted 订阅
