# Fix Log: charge.refunded 无法映射到 license(lifetime 退款不撤销授权)

**日期**:2026-07-04 · **分支**:`fix/payment-flow-hardening` · **发现来源**:E2E dev 验证 Item 6(见 `E2E_DEV_VALIDATION_LOG.md`)

## 问题

`handleChargeRefunded` 唯一的定位路径是 `charge.customer` → D1 `user.customer_id` → 该用户**最新** lifetime license。两个缺陷:

1. **生产 lifetime 购买的 charge 通常没有 customer**:checkout 走 `mode=payment` 只传 `customer_email`,未设 `customer_creation=always`(Stripe 默认 `if_required` 不创建 Customer)→ 第一道守卫直接 no-op,**退了钱、终身授权还在**(收入完整性问题);
2. **"最新 lifetime"启发式在同一账户多张 lifetime 时可能撤销错张**。

## 复现证据

- 真实退款 `re_3TpKfgAKLIiL9hdw1dmtZuXi`(Item 1 的 charge,customer=null)→ worker 日志:
  `[Stripe] No customer on refunded charge ch_3TpKfgAKLIiL9hdw1nd67oRY`(warn → no-op),license `RM-XRLI…` 保持 active。
- 现有单测的 charge fixture 恰好带 customer,掩盖了生产形态。

## 修复(方案 B 为主 + 方案 A 数据卫生)

**B(webhook 侧,`stripe-webhook.ts`)**:新增 `revokeLicenseByPaymentIntent()` ——
`charge.payment_intent` → `GET /v1/checkout/sessions?payment_intent=…&limit=1` → 用 session id 匹配 `licenses.stripe_session_id` **精确定位**那一张。守卫保持:仅 lifetime、仅 active。session/license 未命中或查询失败(warn)→ **回退**原有 customer 启发式路径(兼容无 payment_intent 的旧事件)。"命中但非 lifetime/非 active" 视为已定案,不再回退(避免启发式误伤别的 license)。

**A(checkout 侧,`billing.ts`)**:lifetime(payment mode)session 增加 `customer_creation: 'always'`,让以后每笔购买都有 Customer(user.customer_id 由既有 `findOrCreateUser(email, session.customer)` 自动落库)。

## TDD 过程

**RED**(`tests/stripe-webhook.test.ts` 新增 2 测,真实 handler/签名/D1,仅 stub api.stripe.com fetch):

1. `customer=null` + `payment_intent` 有值(生产形态)→ 期望经 PI 定位并 revoke。**实测失败**:license 停在 active(no-op)。
2. 同账户两张 lifetime(Session01/Session02),退款 PI 指向 Session01 → 期望只 revoke Session01。**实测失败**:Session01 停在 active(旧代码经 customer 启发式撤销了错误的 Session02)。

**GREEN**:修复后文件内 47/47;billing 18/18;全量 `build`/`lint`/`typecheck`/`test` ✓(api 199 + web 4,无回归)。旧的 customer 回退路径测试原样保持绿。

## 部署与真实验证(dev,version `c00bb334-6b86-40cf-8448-d4a070fb1953`)

| 验证 | 结果 |
|---|---|
| 方案 A | 经真实 dev API `POST /v1/checkout/session`(pro/lifetime)创建 session `cs_test_b1hA90…`,Stripe 侧确认 `customer_creation: always` ✅(该 session 未支付,24h 自动过期) |
| 方案 B 主路径 | `stripe trigger` 复刻 Item 1 式 lifetime 购买(session `cs_test_a1Wqvub…`,**customer=None**,PI `pi_3TpO0Q…`,同样落在 stripe@example.com 用户)→ license `RM-TCCB-R80J-IMQQ-H49A` 创建 → 真实退款 `re_3TpO0Q…` → **license 变 revoked**,reason=`Refunded: charge_ch_3TpO0Q…`。worker 日志:`Lifetime license d3dcaeef-… revoked due to refund (resolved via payment_intent pi_3TpO0Q…)` ✅ |
| 多张 lifetime 精确性(实测) | 同用户的另一张 lifetime `RM-XRLI…` 保持 active,未被误伤 ✅ |
| 断言 3 重验 | Item 5 的 `RM-VN6K…`(pro/past_due)与 Item 2 的 `RM-CCEM…`(community/active)均不受影响 ✅ |

## 备注

- Item 6 原始退款事件 `evt_3TpKfgAKLIiL9hdw1WKFf6tV` 已被标记 processed(no-op 时代),不会重投,故 `RM-XRLI…` 仍为 active——属已知残留,收尾清理时随测试数据一并删除。
- "no-op 也标记 processed" 的通用模式与 followups §5 同类,§5 保持 open。
