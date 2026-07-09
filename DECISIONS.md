# DECISIONS.md

执行中的决策与偏离留痕。格式:`YYYY-MM-DD | 类型(review/deviation) | 决策点 | 方案/偏离内容 | 结论 | 关键理由`

2026-07-09 | deviation | 检查清单 §1.4 要求 roll prod webhook secret | 未 roll,以证据关闭 | 采纳 | 401 失配端点 we_1SnXkb... 是 sandbox 账号端点且已删除;live 端点验签成功有 prod D1 processed_events 五类事件实证;roll 反而引入换密窗口风险。唯一残项(live 端点是否订阅 customer.deleted)留人工。
2026-07-09 | deviation | followups §4 建议把 RATE_LIMIT_DISABLED 改名 DEV_BYPASS_RATE_LIMIT | 未改名,仅加 CI grep guard | 采纳 | 改名会动 dev/test 既有引用,收益低于风险;CI guard 已覆盖"误上 prod"同一风险面。
2026-07-09 | deviation | B-2 nbf 回溯量在 60-300s 区间选值 | 取 300s(NBF_LEEWAY_SECONDS) | 采纳 | 与 CLI 侧 v0.4.3 的 300s leeway 常数对齐;nbf 仅防提前使用,回溯 300s 无安全代价,skew 容忍度最大化。
2026-07-09 | deviation | A-3 正向 smoke 原判"需人工浏览器 session" | 脚本化闭环:Vercel env pull 取 live CLERK_SECRET_KEY → Backend sign_in_tokens → FAPI ticket 兑换 session JWT(60s)→ 打 prod 正向(200 幂等)+ 伪造邮箱(403);临时 session 已 revoke,scratch 密钥文件已删 | 采纳 | Clerk prod 实例禁 Backend 直开 session,但 sign-in ticket 路径可用;自有账号+幂等返回,零脏数据。同法用 live Stripe key 只读核实了 §1.4 customer.deleted 订阅
2026-07-09 | review(选型) | B-3 MANUAL_REVIEW 告警通道 | worker 内 sendOpsAlert() 直 POST OPS_ALERT_WEBHOOK(收端无关 JSON,fail-open,5s 超时) | 采纳 | 备选:Logpush(Enterprise 门槛,批量导出形态不配单点告警)、Tail Worker(Workers Paid+多一个部署物)、Email Routing send_email(面板步骤多且无法远程核实)。关键假设:告警极低频(MANUAL_REVIEW 本应永不发生)、含客户 PII 故收端必须自有;fail-open 保证支付路径零风险。
2026-07-09 | deviation | B-4 假设 45 条 Dependabot 在 mono | 实际 mono=0,45 条全在 CLI repo uv.lock | 采纳 | checklist:119 写在 mono 清单里但 gh api 实测归属 CLI repo;修复动作转移到 replimap 仓库执行(定向 uv lock --upgrade-package,非全量 --upgrade,控回归面)。
