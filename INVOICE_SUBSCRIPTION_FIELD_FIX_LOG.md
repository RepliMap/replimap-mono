# Fix Log: invoice.subscription 字段在 API ≥2025-03-31 下为 null,订阅发票被整体跳过

**日期**:2026-07-04 · **分支**:`fix/payment-flow-hardening` · **发现来源**:E2E dev 验证 Item 3(见 `E2E_DEV_VALIDATION_LOG.md`)

## 问题

Stripe API 版本 **2025-03-31(basil)及之后(含 dev endpoint 使用的 2025-12-15.clover)** 移除了发票对象顶层的 `invoice.subscription` 字段,订阅 id 移至 `parent.subscription_details.subscription`。

`handleInvoicePaid` 与 `handlePaymentFailed`(`apps/api/src/handlers/stripe-webhook.ts`)只读顶层字段,导致当前部署上**所有订阅发票被误判为"非订阅发票"并直接跳过**:

1. `invoice.paid` 不回填/延展 `current_period_end` → 订阅 license 周期永远为 null,续费不延展;
2. `invoice.payment_failed` 不置 `past_due` → 扣款失败后 license 仍保持 active。

**性质**:收入完整性问题(方向对客户有利、对公司不利);且 Item 5(扣款失败)验证直接依赖此路径,不修会污染后续验证结果。

## 复现证据(真实 clover 事件)

- 事件 `evt_1TpLd7AKLIiL9hdw2NceIJUH`(invoice.paid,2026-07-04):
  - `data.object.subscription` = **null**
  - `data.object.parent.subscription_details.subscription` = `sub_1TpLd5AKLIiL9hdwKYDaNHQ8`
  - `lines.data[0].period` = `{start: 1783140999, end: 1785819399}`(数据完整存在,只是 id 读取路径错了)
- 后果实测:该订阅的 license(`abe18793-…`)`current_period_end` 保持 null,事件被无操作标记 processed。

## TDD 过程

**RED**(`apps/api/tests/stripe-webhook.test.ts` 新增 3 测,真实 handler + 真实 HMAC 签名 + 真实 D1):

1. `invoice.paid` clover 形态(顶层 null + parent 路径有值)→ 期望回填周期并 reactivate。**实测失败**:status 停在 `past_due`、period 未回填(被当非订阅发票跳过)。
2. `invoice.payment_failed` clover 形态 → 期望置 `past_due`。**实测失败**:status 停在 `active`。
3. 边界钉子:两个位置都无订阅 id → 仍应判为非订阅发票、无副作用。(此测通过,钉住修复后的边界)

**GREEN**(最小修复):

- 新增 `getInvoiceSubscriptionId(invoice)`:**优先读 `parent.subscription_details.subscription`,回退顶层 `invoice.subscription`**(兼容旧版本/历史事件),两者皆无才判非订阅发票。
- `handleInvoicePaid` / `handlePaymentFailed` 改用该 resolver;`StripeInvoice` 接口补充 `parent` 结构、`subscription` 改为可选。
- 未改动其他逻辑(period 仍取 `lines.data[0].period`,clover 下实测该字段仍在)。

## 验证

| 步骤 | 结果 |
|---|---|
| 新增 3 测 | RED→GREEN,文件内 45/45 通过 |
| 全量 CI 四步 | `pnpm build` ✓ / `lint` ✓ / `typecheck` ✓ / `test` ✓(api 12 文件 197 测 + web 4 测,无回归) |
| 部署 dev | `replimap-api` version `60dcae64-e92b-4163-a656-3068c0266af1`(2026-07-04 ~06:47 UTC) |
| **真实事件复验** | 对 `sub_1TpLd5…` 创建并支付真实订阅发票 `in_1TpNPwAKLIiL9hdwqRdwfiuo`(line period=1783140999→1785819399)。事件 `evt_1TpNQ1AKLIiL9hdw7ozVQJDg` 200 处理,license `current_period_end`:**null → `2026-08-04T04:56:39Z`**,`current_period_start` 同时从 nowISO fallback 假值修正为真实周期起点 `2026-07-04T04:56:39Z`,status=active,plan=team 不受影响。 |

## 残留事项(未在本次修复范围)

1. **事件时序**:Item 3 观察到 invoice.paid 可能先于 subscription.created 到达;此时 license 尚不存在,事件无操作但被标记 processed,事件级幂等会挡掉重投 → 首期周期回填可能永久丢失。已记入 `docs/roadmap/commercial-flow-followups.md`。
2. `invoice.payment_failed` 的真实投递验证留给 Item 5(单测已覆盖 clover 形态)。
