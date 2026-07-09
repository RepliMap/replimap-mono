# 支付链路生产化 TODO(2026-07-09 盘点)

> **执行进度(2026-07-09 会话):A 组全部完成(含残项),B-1/B-2/B-5 完成。**
> A-1 修复+反例测试(`b709db7`);A-2 **全闭环**(旧 401 端点是 sandbox 端点且已删;live 端点 `we_1TpRvVAM46G6RB9J...` 经 live key 只读核实:enabled、8 类事件含 `customer.deleted`);A-3 **全闭环**(secrets 全在;无 token/伪造 token → 401;正向路径真 Clerk session → 200 幂等;伪造他人邮箱 → 403;CLI 验签对 prod 确认);A-4 账本 7/4 已对齐,今日复核通过。B-1 核查+CI guard(`faa2b79`);B-2 nbf 回溯 300s(`c317532`);B-5 文档更正+空壳树已删(`71d1c49`)。
> **API 已部署:dev `98d6b901` + prod `cacc361d`(A-1+B-2 已 live,双端验证 `iat-nbf==300`)。**
> 剩余:B-3 告警接线(渠道待定夺:Logpush/Tail Worker/通知目标)、B-4 Dependabot;C 组按既定条件延后。
> 附带修复:replimap CLI 缺 `cryptography` 运行时依赖(pipx 安装即崩)——已在 CLI 仓库修复(`ab32a44`,pyproject+uv.lock+CHANGELOG),本机已 `pipx inject` 先行解锁。

- 依据:2026-07-09 对 main(HEAD dea20a1,工作树干净,领先 origin 1 commit)的只读读码盘点,证据均为 文件:行号。
- 本文自包含:执行会话不需要旧会话上下文。**7 月 4 日诊断的记忆已大量过期,以本文为准。**
- 新会话开场白(建议):`执行 docs/plans/2026-07-09-payment-prod-todo.md,按优先级从 A 组开始;每项验收标准在条目内;Landmine 区红线不可越。`

## 0. 当前已核实状态(不要重复诊断这些)

| 旧情报(2026-07-04) | 现状(2026-07-09 核实) |
|---|---|
| 生产 worker 是 1 月代码、D1 全表 0 行 | **过期**。支付代码已上 prod,真实 $29 Pro 购买→webhook→license→refund/cancel 全链路已验证(PROD_E2E_SMOKE_TEST_LOG.md;CLAUDE.md:102-112);§5 修复在 API f62bd94c,#6/#7 在 API 90bfc4ca |
| provision-community 无鉴权 P0 | **已修**。Clerk session 强制、email 以 token 身份为准、未配 Clerk 则 fail-closed 503(provision-community.ts:59-93;PROVISION_COMMUNITY_AUTH_FIX_LOG.md) |
| fix/payment-flow-hardening 等 commit | **已并入 main**(main..branch 为空);webhook 32 个真 D1 测试在 apps/api/tests/stripe-webhook.test.ts |
| "license 404 recovery server 侧做到一半" | **不存在独立半成品**。7/7-7/8 的工作是 Ed25519 license-blob 签名上线(cd58f29/611f106/dea20a1),已 live on dev+prod,CLI v0.4.2 对 prod 验证过;"D1 migration preparation" 的结论是无需迁移。所谓 recovery 是手工 playbook(docs/testing/commercial-flow.md:165-209) |
| CLI Ed25519 验签未接线 | **大概率已接线**(签名 runbook 记录 2026-07-08 用 CLI v0.4.2 对 prod 验证;CLI 仓库 485ccb6 已加 nbf/iat 300s leeway)。执行 A-3 smoke 时顺手确认 |

## Landmine(红线,来自 CLAUDE.md:24-29 与 DEPLOY-LICENSE-SIGNING.md:30-36)

- **严禁对 prod D1 跑 `wrangler d1 migrations apply`**——prod 是 drizzle-kit 血统,索引名冲突会 DROP `payment.payment_session_id_idx`。prod 只允许 §1.3 的 metadata ledger INSERT。
- 签名是 fail-open 设计,只读既有列,无 schema 变更。

## A 组:正确性/生产健康(先做)

### A-1. Path B 竞态残留:success 页可能把 community key 当购买结果展示 【~1h】
- 现状:页面本身已不回退 community(success/page.tsx:49,70-88,184-206 只轮询 `getCheckoutLicense`),但 server 侧 Path B 的 `getLicenseByUserEmailLatest`(db.ts:881-901)只过滤 `status='active'`、**无 plan 过滤**(checkout-license.ts:82-88)。已有 community license 的用户(先逛过 dashboard)在付费 webhook 落地前轮询,会拿到 community key 展示为 "Your license"。全新用户无 community 行 → 404 NOT_READY 继续轮询(安全)。
- 修法:Path B 排除 community plan(或仅返回付费 plan);补反例测试——tests/checkout-license.test.ts:67-103 只有正例,缺"预存 community 行不得被返回"。
- 验收:新反例测试红→绿;既有 Path A/B 测试不回归。

### A-2. Prod Stripe webhook signing secret 核实/轮换 【~30min,操作性】
- 现状:PROD_DEPLOYMENT_CHECKLIST.md:93-103(§1.4)记录 prod webhook endpoint(we_1SnXkbAKLIiL9hdwR1W9kOif)曾 401 Invalid signature(当初 prod D1 0 行的根因),要求 roll new secret + 订阅补 `customer.deleted`;**checkbox 未勾**。但 smoke log 声称真实购买已走通——两者矛盾,可能修过没回勾。
- 做法:先查 Stripe Dashboard 该 endpoint 近期投递成功率;不健康则按 §1.4 轮换 secret(`wrangler secret put STRIPE_WEBHOOK_SECRET --env prod`)+ 补事件;健康则勾掉并注明核实日期。
- 验收:endpoint 最近投递 2xx;`customer.deleted` 在订阅事件列表;checklist §1.4 勾掉。

### A-3. Prod secrets + live smoke 补课 【~30min,操作性】
- `CLERK_ISSUER` prod 未确认(§1.2,checklist:40-54 未勾)——没设则 provision-community 在 prod 直接 503。
- §1.5 两项未 live 验证(checklist:111-112):provision-community 正向路径 + 403 拒绝;`[Stripe][MANUAL_REVIEW]` 告警未接线(告警接线可降级为 B 组,先确认日志里能搜到该 tag)。
- 顺手:确认 CLI 验签(表 0 最后一行)——用 CLI 对 prod `/v1/license/validate` 跑一次 activate/validate。
- 验收:prod 上带 Clerk token 能 provision、伪造/缺 token 得 401/403;checklist §1.2/§1.5 勾掉。

### A-4. D1 迁移 ledger 对齐(INSERT-only) 【~15min,操作性】
- 现状:migrations 003-012 齐全(012 = 恢复 UNIQUE(stripe_session_id),无 013+);prod 库结构已在目标态,只差 metadata ledger INSERT 让 wrangler 账本一致;checklist §1.3(:56-91)未勾。
- 做法:严格按 §1.3 的 INSERT 语句执行(见 Landmine);dev 库先演练。
- 验收:`wrangler d1 migrations list --env prod` 显示 012 已记账;未跑 apply。

## B 组:防回归/运维硬化

- **B-1. RATE_LIMIT_DISABLED prod 核查 + CI guard**(followups §4,:63-80)【~20min】`wrangler secret list --env prod` 确认未设 + CI 加 grep guard。
- **B-2. nbf 回溯 60-300s(mono 侧签名器)**(DEPLOY-LICENSE-SIGNING.md 尾部 follow-up;license-blob-signer.ts:55-56,286,296-298 现为零 leeway)【~30min】CLI 侧 300s leeway 已发(replimap 仓库 485ccb6/v0.4.3),mono 侧是双保险;**搭下一次 worker deploy 顺风车,不为它单独部署**。
- **B-3. `[Stripe][MANUAL_REVIEW]` 告警接线**(若 A-3 中未顺手完成)。
- **B-4. 45 个 Dependabot 告警清理**(checklist:119)【半天,可再拆】。
- **B-5. 文档卫生**:checklist §1.1 "prod 是 2026-01-20 代码" 表述已过期(与 CLAUDE.md:102-112 矛盾),更正防误导;删 `apps/api/apps/**`、`apps/web/apps/**` 两棵 untracked 空壳树(仅 claude-mem 空 stub,gitignored 噪音)。

## C 组:产品补全(有付费用户增长再排)

- **C-1. Email 送 license key**(followups §1;真实 TODO 在 apps/api/src/handlers/user.ts:372)【~2h,Resend 最轻】。
- **C-2. /v1/me/\* license key 走 URL query 的 secrets-in-URL 问题**(followups §8,:215-254)——方向决策:header/body(~1-2h)vs Clerk 绑定(半天+);"上量前评估",非阻塞。伴生:session_id-as-bearer 可分享性(checklist:120)。
- **C-3. Webhook 高并发压测**(followups §3)——50+ 并发重投、事件乱序组合;>100 subs/day 前排上。
- **C-4. Team tier 独立 e2e**(followups §2)——仅当 Team 行为与 Pro 分叉时做。

## 参考文件索引

| 文件 | 用途 |
|---|---|
| PROD_DEPLOYMENT_CHECKLIST.md | §1.2-1.5 操作项与未勾清单(注意 §1.1 表述已过期) |
| DEPLOY-LICENSE-SIGNING.md | 签名上线 runbook + nbf follow-up + prod 验证记录 |
| docs/roadmap/commercial-flow-followups.md | §1-§8 长期项(§5/§6/§7 已修并上 prod) |
| docs/testing/commercial-flow.md:165-209 | "用户付了钱没拿到 license" 手工恢复 playbook |
| PROD_E2E_SMOKE_TEST_LOG.md | 真实购买链路验证记录 |
| apps/api/tests/ | webhook/checkout-license/provision 测试(A-1 在此补反例) |
