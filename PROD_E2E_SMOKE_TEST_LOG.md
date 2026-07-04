# RepliMap 生产环境端到端冒烟测试日志

**日期:** 2026-07-05
**背景:** 本轮支付加固 + live price ID 上线后,第一笔**真实 live 信用卡交易**的端到端验证。
**交易:** Pro Monthly($29 USD)订阅,来自 https://www.replimap.com
**Checkout session:** `cs_live_b1Hz…5qGvkz`(打码)
**License key:** `RM-5LTH-ATZ4-J2YC-YWNS`

---

## 第一部分:正向链路验证(只读,已完成)

### licenses 表(prod D1 `replimap-prod`)

| 字段 | 值 | 预期 | 结论 |
|---|---|---|---|
| `id` | `67bf0415-2d02-44f2-adf6-4057bbf0a1bd` | 存在 | ✅ |
| `license_key` | `RM-5LTH-ATZ4-J2YC-YWNS` | 匹配 | ✅ |
| `plan` | `pro` | pro | ✅ |
| `plan_type` | `monthly` | monthly | ✅ |
| `status` | `active` | active | ✅ |
| `stripe_subscription_id` | `sub_1TpSEPAM46G6RB9JY2OdOZhN` | 有值 | ✅ |
| `stripe_price_id` | `price_1TpOOZAM46G6RB9JWWSMK6PH` | **live Pro Monthly** | ✅ live 映射生效 |
| `stripe_session_id` | `null` | — | ⚠️ 见下(订阅模式正常) |
| `current_period_start` | `2026-07-04T11:59:40.551Z` | Stripe 周期起点 | ⚠️ =created_at,疑似默认值 |
| `current_period_end` | `null` | Stripe 周期终点 | ⚠️ 见下(followups §5) |
| `canceled_at` / `revoked_at` / `revoked_reason` | `null` | null | ✅ |
| `created_at` / `updated_at` | `2026-07-04T11:59:40.551Z` | — | ✅ |

### user 表

| 字段 | 值 |
|---|---|
| `id` | `7a8fa90e-837f-4ddd-a845-799d2b35a139` |
| `email` | `davidlu1001@gmail.com` |
| `normalized_email` | `davidlu1001@gmail.com` |
| `customer_id` | `cus_Up6RaA4La6uxDE` |

user 记录存在,邮箱与购买账户一致 ✅

### processed_events 表(全部 3 个事件已处理)

| # | event_id | event_type | processed_at |
|---|---|---|---|
| 1 | `evt_1TpSERAM46G6RB9JvdEGKIjO` | `invoice.paid` | 2026-07-04T11:59:40.126Z |
| 2 | `evt_1TpSERAM46G6RB9JHM9xsTCx` | `checkout.session.completed` | 2026-07-04T11:59:40.495Z |
| 3 | `evt_1TpSEQAM46G6RB9J7B36cDFj` | `customer.subscription.created` | 2026-07-04T11:59:40.893Z |

三个预期事件全部收到并落 processed_events ✅ —— 证明 live webhook 端点签名校验与处理链路正常工作。

### 两处已知/预期的异常观察(非阻塞)

1. **`stripe_session_id = null`**:订阅模式(subscription)下,license 由订阅链路创建,不携带 checkout session id,故为 null。这是**预期行为**,不是错误。副作用见第二部分——退款的 payment_intent→session→license 精确定位路径对这条 license **不适用**。
2. **`current_period_end = null` 且 `current_period_start = created_at`**:对应 `docs/roadmap/commercial-flow-followups.md` §5 的时序问题,并被本次事件顺序**实证**:`invoice.paid`(.126)在 license 创建(.551)**之前**就到达并被处理,`customer.subscription.created`(.893)在之后——首期账单周期回填因此丢失,且事件级幂等已把这几个事件标记为已处理,后续重投无法自愈。**这是已知延后项,不阻塞本次冒烟结论**,但建议纳入 followups 跟踪(见文末)。

### wrangler tail
跳过。交易发生在 2026-07-04 11:59Z,`wrangler tail` 仅实时,无法回捞历史日志。processed_events 三条记录已足以证明 webhook 处理成功。

### 第一部分结论
✅ 正向链路验证**通过**:webhook 收到并处理了这笔真实 live 交易,license 以正确的 plan/status/live-price 落到 prod D1,user 记录正确关联。仅有的两处异常均为已知项(订阅模式 session_id 为 null;首期周期回填丢失),不影响 license 有效性。

---

## 第二部分:退款 + 取消订阅(计划,**未执行,待确认 + 待 live 账户访问**)

### ⚠️ 阻塞:当前 Stripe MCP 连的是 SANDBOX 账户,无法操作 live 资源

- MCP 账户:`RepliMap-Sandbox`(`acct_1Sg0CYAKLIiL9hdw`)—— **test/sandbox**
- live 订阅 `sub_1TpSEPAM46G6RB9JY2OdOZhN` 在该账户查询返回 **"No such subscription"**
- 因此**我无法通过 Stripe MCP 执行退款或取消订阅**。二者必须由你在 **live Stripe Dashboard** 手动操作(或把 Stripe MCP 切到 live keys 后我再来)。

### 需要两个动作(缺一不可)

| 动作 | 目标 | 金额 | 触发 webhook | 对 license 的影响 |
|---|---|---|---|---|
| **A. 退款** | 首期发票对应的 charge / payment_intent(customer `cus_Up6RaA4La6uxDE`、sub `sub_1TpSEP…` 的首张 invoice) | **2900**(=$29,全额) | `charge.refunded` | **无**(见下,设计如此) |
| **B. 取消订阅** | `sub_1TpSEPAM46G6RB9JY2OdOZhN`(立即取消,非期末) | — | `customer.subscription.deleted` | status → **`canceled`**,置 `canceled_at` |

### 关键更正:退款本身不会改变这条 license 的状态

代码核实(`handleChargeRefunded` / `revokeLicenseByPaymentIntent`):**退款撤销逻辑只对 `lifetime` license 生效**。对本条 `monthly` 订阅 license:
- payment_intent→session 精确路径:session 能查到,但 `getLicenseBySessionId` 因本 license `stripe_session_id=null` 返回空 → 不匹配;
- 客户兜底路径:`getLifetimeLicenseByUserId` 找该用户的 lifetime license → 该用户只有 monthly,无 lifetime → 忽略;
- 即便匹配到也有 `planType !== 'lifetime'` 守卫直接忽略。

**所以订阅的终态来自「取消订阅」(→ `canceled`),不是来自退款。** 之前 dev 上验证的 payment_intent 精确定位是针对 **lifetime 退款**的场景,对本次 monthly 订阅**按设计不适用**——这不是 bug。**退款是为了把钱退给客户,取消订阅是为了停止下月扣款并把 license 置为终态**,两件事都要做。

### 预期最终结果

- license `67bf0415…` 的 `status`:`active` → **`canceled`**,`canceled_at` 被置为取消时刻;`revoked_at`/`revoked_reason` 保持 `null`(订阅走 cancel 不走 revoke)。
- 钱:$29 全额退回原卡。
- **不应影响任何其他 license/user 数据**(prod 目前也仅此一条真实 license)。

### 验证方式(动作完成后我来做,只读)
重新查询 prod D1:
1. `licenses` 该行 `status='canceled'`、`canceled_at` 非空;
2. `processed_events` 新增 `charge.refunded`、`customer.subscription.deleted`;
3. 确认退款/取消**只**动了这一条 license,没有误伤其他数据。

### 执行前对比快照(before)
```
license 67bf0415: status=active, canceled_at=null, revoked_at=null
licenses_total=1, users_total=1, active=1, canceled=0, revoked=0
```

### 执行后(after)—— 已回填(2026-07-05 只读复查)

退款 + 立即取消订阅已由用户在 **live Stripe Dashboard** 手动完成。复查 prod D1:

**licenses 该行(`67bf0415…`):**

| 字段 | before | after | 结论 |
|---|---|---|---|
| `status` | `active` | **`canceled`** | ✅ 按预期 |
| `canceled_at` | `null` | **`2026-07-04T12:14:04.174Z`** | ✅ 非空 |
| `revoked_at` | `null` | `null` | ✅ 订阅走 cancel 不走 revoke |
| `revoked_reason` | `null` | `null` | ✅ 同上 |
| `plan` / `plan_type` / `stripe_subscription_id` | pro / monthly / sub_1TpSEP… | 不变 | ✅ 只改状态 |
| `updated_at` | …40.551Z | …14:04.174Z | ✅ 取消时刻 |

**processed_events(新增 2 条,共 5 条):**

| event_type | processed_at | 对 license 的影响 |
|---|---|---|
| `charge.refunded` | 2026-07-04T12:13:47.791Z | **无**(monthly,退款撤销逻辑仅对 lifetime 生效,按设计跳过) |
| `customer.subscription.deleted` | 2026-07-04T12:14:04.354Z | → `cancelLicense`,status=`canceled`,canceled_at 置位 |

**时序实证了第二部分的代码分析:** `charge.refunded`(12:13:47)先到并被处理,但 license **仍是 active**;紧接着 `customer.subscription.deleted`(12:14:04)才把它翻成 `canceled`(canceled_at=12:14:04.174,与该事件对齐)。**终态确实来自取消订阅,而非退款** —— 与代码预期完全一致,退款路径没有误撤销这条 monthly license。

**无误伤(全表基线对比):**

| 计数 | before | after | 结论 |
|---|---|---|---|
| licenses_total | 1 | 1 | ✅ 无增删 |
| users_total | 1 | 1 | ✅ 无增删 |
| active / canceled / revoked | 1 / 0 / 0 | **0 / 1 / 0** | ✅ 唯一一条从 active→canceled |
| payment_total | 0 | 0 | ✅ 无变化 |
| processed_events_total | 3 | 5 | ✅ 仅新增预期的 2 条 |

只有目标 license 一条被改动(active→canceled),其余数据零变化,退款/取消**没有误伤**任何记录。

---

## 最终结论

**本次 prod 端到端冒烟测试:正向链路 + 逆向(退款/取消)链路,全部按预期工作。** ✅

- **正向**:真实 live 交易 → 3 个 webhook 事件正确处理 → license 以正确 plan/status/**live price** 落库,user 正确关联。
- **逆向**:退款 $29 全额到账客户;取消订阅触发 `customer.subscription.deleted` → license `active`→`canceled`、`canceled_at` 置位、`revoked_at/reason` 保持 null(订阅正确走 cancel 而非 revoke);退款事件对 monthly license 正确地无副作用,未误撤销;全表基线零漂移,无误伤。
- **唯一遗留(非阻塞)**:followups §5 首期周期回填丢失(`current_period_end=null`),本次 live 交易实证,建议后续修复。

本轮支付加固在 live 环境的第一笔真实端到端验证 **通过**。

---

## 待办 / followups
- [ ] **§5 首期周期回填丢失**:本次 live 交易实证了 `invoice.paid` 早于 `subscription.created`,导致 `current_period_end=null`。建议按 followups §5 的修复方向处理(license 不存在时不要把 `invoice.paid` 标为已处理,或在 `subscription.created` 里补周期自愈)。
- [x] 退款 + 取消订阅执行后回填本文档 after 快照与最终结论(2026-07-05 完成)。
