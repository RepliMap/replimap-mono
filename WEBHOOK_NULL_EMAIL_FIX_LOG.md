# Webhook null-email 崩溃修复记录

**日期:** 2026-07-04
**分支:** `fix/payment-flow-hardening`(replimap-mono)
**触发来源:** dev worker 真实 webhook 投递(A6 验证阶段)——`checkout.session.completed`(Stripe CLI 通用 fixture,`evt_1TpJZLAKLIiL9hdwm9vrpbvf`)返回 **500**。
**方法论:** RED→GREEN,针对真实 handler + 真实 Miniflare D1。

---

## 1. 复现证据(dev 实测 + RED 测试)

**dev worker 实时日志(`wrangler tail`,Resend 重放捕获):**
```
LOG   [Stripe] Checkout completed: cs_test_a11poAqsla…, mode: payment
ERROR Stripe webhook error: TypeError: Cannot read properties of null (reading 'toLowerCase')
```

**根因(日志时序 + 唯一 `.toLowerCase()` 调用点锁定):**
- `stripe-webhook.ts:189`(旧)`findOrCreateUser(db, session.customer_email, session.customer)` —— 只读顶层 `customer_email`。
- 通用 fixture 的顶层 `customer_email` 为 `null`(邮箱在 `customer_details.email`)。
- `db.ts:507`(旧)`const normalizedEmail = email.toLowerCase();` —— **无 null 守卫** → `null.toLowerCase()` 抛 `TypeError` → 被 handler catch 兜住返回 **500** → Stripe 对 5xx 会重试 ~3 天(重试风暴)。

**RED 测试(5 条,全部先失败):**
- `checkout.session.completed — email resolution`(3 条):`customer_email=null` + `customer_details.email` 有值(payment / subscription 两模式)→ 实测 **500**(期望 200);两字段都空 → 实测 **500**(期望 200 ack-and-skip)。
- `findOrCreateUser email guard`(2 条):传 `null` → 抛 **TypeError**(期望 AppError);传 `''` → **静默创建一个空邮箱的垃圾 user**(期望 reject)。

---

## 2. 修复方案

### 修复 1 — 统一邮箱解析 + 无邮箱优雅 ack(`stripe-webhook.ts`)
- `StripeCheckoutSession` 接口:`customer` / `customer_email` 改为 `string | null`,新增 `customer_details?: { email?: string | null } | null`。
- `handleCheckoutCompleted`:邮箱解析改为 `session.customer_email ?? session.customer_details?.email ?? null`(与 `checkout-license.ts:57` 一致);两者皆空时 **`console.warn` + `return`**(ack-and-skip),让主 handler 标记事件已处理并返回 **200**——**绝不 500**(避免对无解事件的无意义重试风暴)。`findOrCreateUser` 现在收到的是解析后的非空 email(`session.customer` 为 null 时传 `undefined`)。

### 修复 2 — `findOrCreateUser` 空值守卫(`db.ts`,纵深防御)
- 函数顶部加守卫:`if (!email || typeof email !== 'string' || !email.trim()) throw Errors.invalidRequest(...)`。让任何 null/空/纯空白 email 变成**类型化 AppError**(调用方可转干净 4xx),而不是裸 TypeError 冒泡或静默建垃圾 user。新增 `import { Errors } from './errors'`(errors.ts 不 import db,无循环)。

**调用点影响确认:** `findOrCreateUser` 三个调用点均不受负面影响——
- `handleCheckoutCompleted`(修复 1 后已在传入前解析并挡掉 null);
- `handleSubscriptionCreated` 自愈路径(`stripe-webhook.ts:332` 早有 `if (!customer.email)` 前置守卫,守卫永不被破坏性命中);
- `provision-community.ts`(传入的是鉴权后的 `identity.email`,非空)。
守卫纯属安全网。

---

## 3. GREEN + 回归

- 新增 6 条测试全部通过;`tests/stripe-webhook.test.ts` **38/38**(原 32)。
- **全量 API 测试 190/190**(原 184,+6),无回归;含自愈路径两条测试(`self-heals a missing user…` / `returns 500 (Stripe retry)…`)仍绿,证明修复 2 未破坏 subscription.created。
- `tsc --noEmit` 干净;`eslint src/` 0 错误。

---

## 4. (a)/(b) 定性 与 明确不做的下游项

**定性:主要是 (a) 真实健壮性缺陷**(缺 null 守卫 + 没读规范邮箱字段 `customer_details.email`),被一条对我们不真实的通用 fixture 触发。真实付费 checkout 经 `billing.ts:175` 一定带 `customer_email`,**不阻塞真实付费链路**;但 Stripe 真实存在"顶层 `customer_email=null` 但 `customer_details.email` 有值"的会话,那类真实事件旧代码会崩 + 触发重试风暴,故值得修。

**本轮明确不做(仅记录,留待单独决策):** 下游"空 `metadata` + 无 `line_items` 时 `createLifetimeLicense` 默认建 `plan='pro'` license"——即裸事件也会造出一张无 price 的 pro lifetime license。本轮**未处理**(按要求只修上述两处)。后续需决策:payment 模式下无法解析出有效 plan/price 时,是否应拒绝建 license,而不是默认 pro。

---

## 5. 部署状态(null-email 修复)

null-email 崩溃修复已 `wrangler deploy` 到 dev worker(Version `a88bdf49-…`)并**真实验证通过**:同一条之前必崩 500 的 `checkout.session.completed`(`evt_1TpJZL…`)Resend 后返回 **200**,`wrangler tail` 日志无任何 ERROR/TypeError,`customer_details.email` 回退取到 `stripe@example.com` → 建 user + lifetime license。

---

# 追加修复(2026-07-04):无法解析有效 plan/price 时不再默认建 pro license

## 6. 背景与复现

上面那次 dev 验证顺带暴露了本文件 §4 记录的、当时**明确延后**的下游问题:那条裸 fixture(空 `metadata` + 无 `line_items`)让 `createLifetimeLicense` **默认建了一张 `plan='pro'` 的 lifetime license**(`stripe_price_id=NULL`,license `RM-V1PN-…`)。这是真实的**收入完整性风险**——生产若真发生,客户会拿到与实付金额不符的授权档位。

**清理:** 该验证脏数据已从 dev D1 删除(`user` email=stripe@example.com 的 `f26e288e-…` + license `RM-V1PN-L3B3-VU6C-ZEME`),各 DELETE 影响 1 行,删后 `user`=1/`licenses`=3 回到基线,无 stray。

**RED 测试(2 条先失败):** payment 模式、空 metadata、无 line_items → 现有代码创建 `plan='pro'` license(期望:不建 license);metadata.plan=`'gold'`(垃圾值)→ 现有代码盲目建 `plan='gold'` license(期望:不建 license)。另 2 条回归(合法 metadata.plan=team / 合法 lifetime price)先通过。

## 7. 修复(`stripe-webhook.ts` `createLifetimeLicense`)

- plan 初值从 `'pro'` 改为 **`null`**(不再默认付费档)。
- 只在能确定时赋值:metadata.plan **必须是已知 PlanType**(`metaPlan in PLAN_RANK`,拒绝 `'gold'` 等垃圾值)、或 line_items 里的 price 命中映射(price 更权威,可覆盖 metadata)。
- 若 `plan` 仍为 `null`(无法解析):
  - **不建任何 license**;
  - `console.error` 打一条**显眼的 `[Stripe][MANUAL_REVIEW]` 标记日志**,含 `session`、`user`、`email`、`priceId`、`metadata.plan`,便于人工定位是哪一笔付款;
  - `return` → 主 handler 标记事件已处理并返回 **200**(ack,避免 Stripe 对无更多信息的事件无意义重试)。

**通知机制的取舍(回应任务"考虑是否需要额外通知机制"):** 本轮用**显眼的结构化 ERROR 日志 + 唯一 token `MANUAL_REVIEW`** 作为人工介入信号——可直接在 `wrangler tail` 看到,或通过 Cloudflare Logpush + 基于日志的告警对该 token 触发通知,无需 schema 改动。**未**新增"死信/待人工介入"表,因为那需要一次迁移 + schema 决策,超出本轮聚焦范围。**建议后续单独决策**:若要更强的持久化保证(日志在未配 Logpush 时是易失的),新增一张 `payment_review_queue` 表落库这类事件是推荐的下一步。核心原则已满足:**宁可少发 license 靠显眼日志人工介入,绝不错发档位而无人知晓。**

## 8. 正常流程未受影响 + 回归

- 真实 lifetime checkout 经 `billing.ts` 一定带正确的 metadata.plan(pro/team)或 price id → 继续正常建 license(两条回归测试:合法 metadata=team、合法 line_items price → 均正确建对应档 license,GREEN)。
- `tests/stripe-webhook.test.ts` **42/42**(原 38,+4);**全量 API 194/194**(原 190,+4),无回归;`tsc` 0 / `eslint` 0。

## 9. 部署状态(本追加修复)

**未部署。** 本追加修复仍在 `fix/payment-flow-hardening` 分支;dev worker 仍是 `a88bdf49`(只含 null-email 修复,不含本节的 plan-resolution 修复)。是否部署到 dev 再验一次"裸 fixture 不再建 pro license"由你决定。
