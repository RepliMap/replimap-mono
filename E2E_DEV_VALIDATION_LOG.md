# E2E Dev Validation Log — Stripe test-mode 全链路验证

> **用途**:9 项 dev 部署真实链路验证的**增量进度与证据记录**。每完成一项立即追加,不攒批。
> **会话恢复**:如果会话中断,新会话应**优先读本文件**恢复上下文,而不是重新搜索记忆或翻找其他文件。
> **约定**:所有清理动作推迟到 9 项全部完成后统一执行,见文末「清理台账」。

## 环境

| 项 | 值 |
|---|---|
| 目标部署 | dev worker `replimap-api` → https://api-dev.replimap.com |
| 部署版本 | ~~9caa0ead(03:25Z)~~ → **`60dcae64-e92b-4163-a656-3068c0266af1`**(2026-07-04 ~06:47Z,新增 invoice.subscription 字段修复;Item 1–3 在 9caa0ead 上验证,Item 4 起在 60dcae64 上) |
| 数据库 | D1 `replimap-dev`(remote,id `212335fc-ffeb-40d2-8794-c0d84a0991a1`) |
| Stripe | sandbox test mode;dev webhook endpoint `we_1TpJSVAKLIiL9hdwgJv7Mdvu`,API version **2025-12-15.clover**,订阅 8 类事件:checkout.session.completed / customer.subscription.{created,updated,deleted} / invoice.{paid,payment_failed} / charge.refunded / customer.deleted |
| Webhook 路由 | `POST /v1/webhooks/stripe` |
| 幂等机制(两层,勿混淆) | ① **事件级**:`processed_events` 表按 Stripe event id 去重(`isEventProcessed`/`markEventProcessed`),挡同一事件的重投;② **会话级**:migration 012 恢复的 `UNIQUE(licenses.stripe_session_id)`,挡**并发**下同一 checkout session 产生两张 license 的竞态(`createLifetimeLicense` 的 race fallback 依赖它)。Item 1 中观察到的 "already processed, skipping" 属于①,不是②。 |

## 验证项进度(共 9 项)

| # | 项目 | 状态 |
|---|------|------|
| 1 | Lifetime 一次性付款链路 | ✅ 2026-07-04 |
| 2 | 社区版授权开通(auth 必须) | ✅ 2026-07-04 |
| 3 | 订阅升级/降级(subscription.updated) | ✅ 2026-07-04 |
| 3a | (插入)invoice.subscription 字段修复(Item 3 发现的 P1) | ✅ 2026-07-04 已修复+部署+真实事件复验 |
| 4 | 订阅取消(subscription.deleted) | ✅ 2026-07-04 |
| 5 | 扣款失败(invoice.payment_failed + P1-7) | ✅ 2026-07-04 |
| 6 | 退款 lifetime(charge.refunded) | ✅ 2026-07-04(首测发现缺陷 → 6a 修复后真实场景复验通过) |
| 6a | (插入)refund license 定位修复(B:payment_intent 精确定位 + A:customer_creation=always) | ✅ 2026-07-04 已修复+部署+真实事件复验 |
| 7 | customer.deleted → licenses expired | ⬜ |
| 8 | 幂等性压力测试(迁移 012 UNIQUE 层) | ⬜ |
| 9 | CLI 侧验证(真实 key 功能门禁) | ⬜ |
| 收尾 | 清理全部测试数据,恢复 D1 基线,行数对比 | ⬜ |

## 权威任务清单(A6 剩余验证项,用户 2026-07-04 提供原文)

> 以下为用户提供的原文,是本轮验证的**权威清单**。新会话直接读本节,不要依赖会话记忆重建。

### 4. 订阅取消
- 触发 customer.subscription.deleted
- 确认:license 状态正确变为 canceled 或对应状态,而不是被删除或者卡在 active

### 5. 扣款失败
- 触发 invoice.payment_failed
- 确认:license 状态变为 past_due(或对应状态);同时验证 P1-7
  ——此时如果同一用户触发 provision-community,不会因为付费 license 变
  non-active 就被社区版覆盖

### 6. 退款(lifetime)
- 对 Item 1 创建的那个 lifetime license 对应的 charge 触发 charge.refunded
- 确认:该 lifetime license 被正确撤销(状态变为 revoked 或对应状态)

### 7. customer.deleted
- 触发 customer.deleted
- 确认:该 customer 名下所有 license 正确置为 expired

### 8. 幂等性压力测试
- 对 Item 1 的 checkout.session.completed 事件,用 Stripe CLI 或脚本方式
  快速连续投递 3-5 次(模拟并发重投)
- 确认:只有一张 license 被创建,没有因为竞态产生重复或报错
- 这一项是真正验证迁移 012 UNIQUE 约束的地方(Item 1 的 Resend 验证的只是
  事件级幂等,不是 012 那层)

### 9. CLI 侧验证
- 用 Item 1 真实生成的 license key,跑一次 replimap CLI 命令
- 确认:CLI 能正确识别这个 plan,功能门禁符合对应档位应有的权限

### 收尾(9 项全部完成后)
清理本轮产生的全部测试数据(license、user、customer、订阅——注意 sub_1TpLd5...
是活跃订阅,需要先 cancel 再清理,否则 sandbox 会持续续费产生事件),恢复
dev D1 到验证前的基线状态,汇报清理前后的行数对比。

---

## Item 1:Lifetime 链路(checkout.session.completed,mode=payment)✅

- **触发方式**:Stripe sandbox 构造真实 Checkout Session(Pro lifetime,一次性付款),由 Stripe 向 dev endpoint 真实签名投递 `checkout.session.completed`。生效事件:`evt_1TpKfhAKLIiL9hdwrP3FLVaI` @ 2026-07-04T03:55:17Z,session `cs_test_a1tHV5UUtvCaWoWKIeYcebcxOEU8YRHI1TTWWBpao36NCLmfM5W0DHfCpl`,customer email `stripe@example.com`(fixture 默认)。
- **验证的关键点**:webhook 签名验证通过 → email 解析(customer_details fallback)→ plan 解析(不猜测)→ license 落库 → 事件标记已处理。
- **实际结果**:PASS。
  - license `2cce54c3-23d1-4c3f-90d2-af64de78f585`,key `RM-XRLI-E40S-N9CO-MN09`,plan=`pro`,plan_type=`lifetime`,status=`active`,period_end=`2099-12-31T23:59:59Z`。
  - user `35e35e9f-5c83-45d0-b494-331f9d90e7ce`(stripe@example.com)自动创建。
  - `processed_events` 含该 event id。
- **偏差与澄清**:
  - 当天更早有 3 次迭代尝试(evt_1TpJZL… @02:44、evt_1TpKDV… @03:26、evt_1TpKKM… @03:33),均已进入 `processed_events` 但未产生 license,属调试迭代;最终采信 03:55 这次。02:44 的事件直到 03:11:34 才处理成功——是 03:09:47 部署后 Stripe 自动重投的结果,顺带验证了 5xx→重投→成功 的路径。
  - **澄清(事件级幂等 vs 迁移 012)**:重投时返回 `{received:true, duplicate:true}` 来自 `processed_events` 事件级去重;migration 012 的 `UNIQUE(stripe_session_id)` 针对的是并发场景下不同 event id 重复建 license 的竞态。两者作用不同,验证时不要把前者的通过当成后者已验证。

## Item 2:社区版授权开通(POST /v1/license/provision-community,需认证)✅

- **触发方式**:用 **Clerk BAPI(后端 API,dev 实例)** 创建测试用户并签发**真实 session token**(非 mock):user `user_3G1TPqm…` + session `sess_3G1TUAT…`(完整 ID 见清理台账),以 Bearer token 调用 `POST https://api-dev.replimap.com/v1/license/provision-community`。
- **验证的关键点**:端点强制 Clerk 认证(a570276 的 P1-8 修复)在真实令牌下正常放行;community license 自动开通。
- **实际结果**:PASS。
  - license `5b698562-c22d-499f-9a32-59aacf6b29db`,key `RM-CCEM-C5WC-58MH-RSGR`,plan=`community`,plan_type=`free`,status=`active` @ 2026-07-04T04:11:07Z。
  - user `5bc58735-7680-410d-a5cb-f31d04f75aac`(e2e-community@replimap-test.dev)。
- **方法沉淀**:「Clerk BAPI 后端签发真令牌」可复用于后续任何需要模拟真实登录态的验证场景。

## Item 3:订阅升级 pro→team(customer.subscription.updated)✅

- **触发方式**(全部真实 Stripe sandbox 对象 + 真实 webhook 投递):
  1. 创建 customer `cus_UozcAiSe7rlbHG`(e2e-upgrade@replimap-test.dev),attach `pm_card_visa`;
  2. 创建订阅 `sub_1TpLd5AKLIiL9hdwKYDaNHQ8`(Pro monthly `price_1SiMYg…`)→ `customer.subscription.created`(`evt_1TpLd7AKLIiL9hdwWttUSMjZ`)由 webhook 自动建 license;
  3. 更新订阅 item `si_Uozc0LTtfHyjg0` 价格 → Team monthly `price_1SiMZv…`,`proration_behavior=none` → `customer.subscription.updated`(`evt_1TpLdkAKLIiL9hdwGSIJa2zl` @ 04:57:20Z)。
- **实际结果**:PASS。
  - license `abe18793-42eb-4e75-a49a-0dc0383837ee`(RM-BM7S-AN8R-X1R4-3JK4)plan 由 `pro` → **`team`**,stripe_price_id 同步更新,updated_at=04:57:21.385Z(事件后 1 秒内);status 保持 active。
  - 三个事件(created / invoice.paid / updated)全部 200 并进入 `processed_events`,**无任何 500**。
  - 升级路径不触发 `isPlanDowngrade` 设备下线逻辑(符合预期,未观察到设备变动)。
- **P1-5 验证方式与原计划的重要偏差**:endpoint API version **2025-12-15.clover ≥ basil(2025-03-31),订阅对象顶层的 `current_period_start/end` 已被 Stripe 移除**(移到 item 层)。因此:
  - 原计划的"带完整顶层 period 字段的正常升级"**在真实投递中不可能出现**——clover 下正常事件天然就是"缺字段"形态;
  - 也就是说,本次真实升级事件**本身就是 P1-5 场景**:缺顶层 period 字段 → 守卫优雅跳过(license 的 period 字段保持原值)→ plan 变更正常落库,**不再 500**。P1-5 修复在当前部署上验证通过,且这是生产流量的常态形态,每个真实 update 事件都会走这条守卫路径;
  - "字段存在时正常写入 period"的分支无法用真实投递构造,仍由单元测试(PAYMENT_HARDENING_LOG §2 的 RED→GREEN 回归)锁定。修复前的行为是 `timestampToISO(undefined)` 抛 RangeError → 500 → tier 变更丢失;修复后 plan 照常更新——本次已在部署上实测。
- **额外发现(P1 级,已于同日修复,见下方 Item 3a)**:clover 下 `invoice.subscription` 顶层字段为 null(实测 `evt_1TpLd7AKLIiL9hdw2NceIJUH`:订阅 id 在 `parent.subscription_details.subscription`)。`handleInvoicePaid`/`handlePaymentFailed` 依赖 `invoice.subscription`(stripe-webhook.ts:505/534),在当前 endpoint 版本下会把**所有订阅发票判为"非订阅发票"直接跳过**。后果:
  1. 订阅 license 的 `current_period_end` 永远为 null(本例实测:invoice.paid 未回填;line 层 period 数据其实存在:1783140999→1785819399);
  2. 续费时周期不会延展;
  3. 扣款失败不会置 `past_due`。
  另有一个叠加因素:本次 invoice.paid(04:56:42.8)比 subscription.created(04:56:44.1)先到,当时 license 尚不存在,事件被无操作地标记 processed,重投也会被事件级幂等挡掉——即使修好字段解析,这个时序仍可能让首期回填丢失。**时序问题保持 open,已记入 `docs/roadmap/commercial-flow-followups.md` §5。**

## Item 3a(插入):invoice.subscription 字段修复 ✅

Item 3 的 P1 发现按用户决定**立即修复**(理由:收入完整性 + Item 5 直接依赖此路径)。全程 TDD,详细记录见 **`INVOICE_SUBSCRIPTION_FIELD_FIX_LOG.md`**。摘要:

- **修复**:新增 `getInvoiceSubscriptionId()` —— 优先读 `parent.subscription_details.subscription`(API ≥2025-03-31),回退顶层 `invoice.subscription`(兼容旧版本事件),两者皆无才判非订阅发票。`handleInvoicePaid`/`handlePaymentFailed` 均改用。
- **RED→GREEN**:新增 3 个真实形态测试(2 失败复现 + 1 边界钉子),修复后 45/45;全量 CI 四步通过(api 197 + web 4,无回归)。
- **部署**:dev worker version `60dcae64`(~06:47Z)。
- **真实事件复验**:对 `sub_1TpLd5…` 创建并支付真实订阅发票 `in_1TpNPwAKLIiL9hdwqRdwfiuo` → 事件 `evt_1TpNQ1AKLIiL9hdw7ozVQJDg` 200 处理,license `current_period_end`:**null → 2026-08-04T04:56:39Z**(line period end 精确一致),`current_period_start` 同步修正为真实值,plan/status 不受影响。
- **未覆盖**:`invoice.payment_failed` 的真实投递验证留给 Item 5(clover 形态已有单测锁定)。

## Item 4:订阅取消(customer.subscription.deleted)✅

- **触发方式**:对 Item 3 的真实订阅执行 `DELETE /v1/subscriptions/sub_1TpLd5AKLIiL9hdwKYDaNHQ8`(立即取消,Stripe 侧 status=canceled @ 07:00:32Z)→ Stripe 真实投递 `customer.subscription.deleted`(`evt_1TpNYyAKLIiL9hdwZa08123G`)。
- **验证的关键点**:license 状态变为 canceled;行**不被删除**;不卡在 active。
- **实际结果**:PASS(事件后 ~1.2s 内)。
  - license `abe18793-…`(RM-BM7S-AN8R-X1R4-3JK4):status `active` → **`canceled`**,`canceled_at=2026-07-04T07:00:33.775Z`;
  - 行保留,plan=team / plan_type=monthly / key / period(07-04→08-04)全部原样不动;
  - `processed_events` 含该事件,200 处理。
- **附带效果**:收尾清单要求的"先 cancel 活跃订阅 `sub_1TpLd5…`"已由本项提前完成,该订阅不会再产生续费事件,清理时直接删数据即可。
- **注**:Item 5(扣款失败)需要一个 active 的订阅 license,届时新建专用订阅,不复用本条(已 canceled)。

## Item 5:扣款失败(invoice.payment_failed)+ P1-7 不被社区版覆盖 ✅

- **触发方式**:
  1. 新建专用 customer `cus_Up1nPIHB7WPdqJ`(email=`e2e-community@replimap-test.dev`,与 Item 2 的 Clerk 测试用户同邮箱)+ Pro monthly 订阅 `sub_1TpNk4AKLIiL9hdw5SKhWU18`(visa 首扣成功)→ webhook 建 license `62ecc8a1-…`(RM-VN6K-5V9M-AIHV-8IZN,plan=pro,active),**与 Clerk 身份落在同一 D1 user `5bc58735-…`** ✅;
  2. attach `pm_card_chargeCustomerFail` → 对该订阅建真实发票 `in_1TpNklAKLIiL9hdw7e2CadTn`($29)→ finalize → `/pay` 用失败卡 → `card_declined` → Stripe 投递 `invoice.payment_failed`(`evt_1TpNkpAKLIiL9hdw4rCBdrxu`);
  3. Clerk BAPI 重新签发真实 session(`sess_3G1q1nsodcJFCqi3CWJeHSZsviM`)+ token,**立即**调 `POST /v1/license/provision-community`。
- **实际结果**:PASS(全部四个断言)。
  - license `RM-VN6K…` status `active` → **`past_due`**(事件后 <1s,07:12:48);
  - **P1-7**:provision-community 返回 HTTP 200 `{"license_key":"RM-VN6K-5V9M-AIHV-8IZN","plan":"pro","status":"past_due","created":false}`——命中 `getNonExpiredLicenseByUserEmail`(取最新非 expired,past_due 算非 expired),付费 license **原样透出**;
  - 未新建任何 license 行(该 user 仍为 2 行:community active + pro past_due),付费行未被改动;
  - Item 2 的旧 community license 不干扰断言(lookup 按 createdAt desc 取最新)。
- **附带验证**:3a 修复在 `invoice.payment_failed` 路径的真实投递验证在此完成(此前仅单测锁定)——clover 形态下事件被正确识别为订阅发票。
- **额外观察**:新订阅 license 的 `current_period_end` 再次为 null——followups §5 时序问题的又一次现场复现(首期 invoice.paid 先于 subscription.created 到达),与 3a 字段修复无关,维持 open。

## Item 6:退款 lifetime(charge.refunded)❌ 发现缺陷

- **触发方式**:对 Item 1 的真实 charge 执行 `POST /v1/refunds`(charge=`ch_3TpKfgAKLIiL9hdw1nd67oRY`,refund `re_3TpKfgAKLIiL9hdw1dmtZuXi` succeeded,$30 全退)→ Stripe 投递 `charge.refunded`(`evt_3TpKfgAKLIiL9hdw1WKFf6tV`)。
- **实际结果**:**license 未被撤销**。lifetime license `RM-XRLI-E40S-N9CO-MN09` 保持 `active`,revoked_at/revoked_reason 均为 null。事件本身 200 处理并进入 `processed_events`(即重投也不会再触发撤销)。
- **直接证据**(wrangler tail 抓取 worker 日志):
  ```
  [Stripe] Charge refunded: ch_3TpKfgAKLIiL9hdw1nd67oRY
  [Stripe] No customer on refunded charge ch_3TpKfgAKLIiL9hdw1nd67oRY   (warn → no-op)
  ```
- **根因链(不是 fixture 偏差,生产同样会踩)**:
  1. `handleChargeRefunded` 唯一的定位路径是 `charge.customer` → `user.customer_id` → 该用户最新 lifetime license;
  2. 生产 checkout(`billing.ts` `createCheckoutSession`)对 lifetime 走 `mode=payment`,只传 `customer_email`,**未设 `customer_creation=always`**——Stripe payment mode 默认 `if_required`,一般**不创建 Customer** → 真实 lifetime 购买的 charge 同样 `customer=null`;
  3. 且 lifetime 买家的 D1 `user.customer_id` 也为 null(`checkout.session.completed` 时 `session.customer` 为 null)。两头都断。
  4. 现有单测的 charge fixture 带 customer,能过但不代表生产形态。
- **性质**:收入完整性问题(退了钱、license 还在,方向对客户有利)。与 3a 同类。
- **断言 3(不误伤)**:通过——Item 5 的 pro/past_due 与 Item 2 的 community 均未被改动(no-op 自然不误伤,但此断言在修复后需重验)。
- **状态**:已按 B 为主 + A 顺手 修复并重验通过,见下方 Item 6a。

## Item 6a(插入):refund license 定位修复 ✅

详细记录见 **`REFUND_LICENSE_LOOKUP_FIX_LOG.md`**。摘要:

- **B(主)**:`handleChargeRefunded` 新增 `charge.payment_intent` → checkout session → `licenses.stripe_session_id` 精确定位;未命中回退 customer 启发式。**A(顺手)**:lifetime checkout session 增加 `customer_creation: 'always'`(经真实 dev API 创建 session 实测确认)。
- **RED→GREEN**:2 个新测试(customer=null 生产形态 + 多张 lifetime 精确性),修复后 47/47;全量 api 199 + web 4 无回归;部署 dev version `c00bb334`。
- **真实场景复验**:`stripe trigger` 复刻 lifetime 购买(customer=None,同 stripe@example.com 用户)→ license `RM-TCCB-R80J-IMQQ-H49A` → 真实退款 `re_3TpO0Q…` → **revoked**,reason=`Refunded: charge_ch_3TpO0Q…`,日志显示 `resolved via payment_intent`。同用户另一张 lifetime `RM-XRLI…` 保持 active(多张精确性实证);Item 5/2 的 license 不受影响(断言 3 重验通过)。
- **已知残留**:`RM-XRLI…` 因原始退款事件已消费(no-op 时代标记 processed)保持 active,收尾清理时删除。

---

## 清理台账(9 项全部完成后统一执行)

| 类型 | 对象 | 来源 |
|------|------|------|
| Clerk(dev) | 测试用户 `user_3G1TPqm…` + session `sess_3G1TUAT…` | Item 2 |
| D1 licenses | `2cce54c3-…`(RM-XRLI-E40S-N9CO-MN09) | Item 1 |
| D1 licenses | `5b698562-…`(RM-CCEM-C5WC-58MH-RSGR) | Item 2 |
| D1 user | `35e35e9f-…`(stripe@example.com) | Item 1 |
| D1 user | `5bc58735-…`(e2e-community@replimap-test.dev) | Item 2 |
| D1 processed_events | 2026-07-04 全部测试 event id | Items 1+ |
| Stripe sandbox | fixture 生成的 product/price(prod_Uoy…/price_1TpK… 等) | Item 1 迭代 |
| Stripe sandbox | customer `cus_UozcAiSe7rlbHG` + 订阅 `sub_1TpLd5AKLIiL9hdwKYDaNHQ8`(~~活跃,需先 cancel~~ → **已在 Item 4 取消**,2026-07-04T07:00:32Z,不再产生续费事件) | Item 3 |
| D1 licenses | `abe18793-…`(RM-BM7S-AN8R-X1R4-3JK4,plan=team) | Item 3 |
| D1 user | `4316c6f9-…`(e2e-upgrade@replimap-test.dev) | Item 3 |
| Stripe sandbox | 已支付发票 `in_1TpNPwAKLIiL9hdwqRdwfiuo` + invoice item `ii_1TpNPx…`($99,paid 不可删,随订阅/customer 清理归档) | Item 3a |
| Stripe sandbox | customer `cus_Up1nPIHB7WPdqJ` + **活跃订阅** `sub_1TpNk4AKLIiL9hdw5SKhWU18`(Pro monthly,默认卡为 visa 可正常续费——**清理时需先 cancel**)+ 未付发票 `in_1TpNkl…` | Item 5 |
| Clerk(dev) | 新增 session `sess_3G1q1nsodcJFCqi3CWJeHSZsviM`(用户仍是 Item 2 的 `user_3G1TPqmZ3eXxPww8xFmLy9RPFvl`,随用户一起清理) | Item 5 |
| D1 licenses | `62ecc8a1-…`(RM-VN6K-5V9M-AIHV-8IZN,plan=pro,past_due) | Item 5 |
| Stripe sandbox | refund `re_3TpKfgAKLIiL9hdw1dmtZuXi`(不可删,归档即可) | Item 6 |
| D1 licenses | `d3dcaeef-…`(RM-TCCB-R80J-IMQQ-H49A,lifetime,revoked) | Item 6a |
| Stripe sandbox | refund `re_3TpO0QAKLIiL9hdw03MvmW8U` + trigger fixture 生成的 product/price + 未支付 session `cs_test_b1hA90…`(24h 自动过期,无需处理) | Item 6a |
