# RepliMap 支付流程 — 生产部署前检查清单

**创建日期:** 2026-07-04
**背景:** 本清单汇总自任务 3(端到端支付流程打通)全过程的诊断与加固工作。所有代码修复已在 `fix/payment-flow-hardening` 分支上完成,并在 **dev worker + Stripe sandbox** 环境下用真实数据完整验证通过(见 `E2E_DEV_VALIDATION_LOG.md`)。

> **⚠️ 状态更新(2026-07-09):下面这段"核心结论"是 2026-07-04 写清单时的快照,已全部过期。** 加固分支已并入 main 并部署 prod;真实 $29 购买→webhook→license→退款/取消全链路已在 live 环境验证(`PROD_E2E_SMOKE_TEST_LOG.md`);§5 修复(API `f62bd94c`)与 #6/#7(API `90bfc4ca`)也已上 prod。当前以各小节 checkbox 与标注日期为准,不要按这段旧结论重新诊断。

**核心结论(2026-07-04 快照,已过期):** 生产商业化链路目前实质上不可用——prod worker 落后代码 3 个月、webhook 签名一直失败(401)、多个真实场景下会静默产生错误数据(错发 license 档位、退款无法撤销 lifetime 授权等)。这份清单的目的是确保上线前把这些已知问题全部闭环,而不是"部署完再说"。

---

## 参考文档索引

| 文档 | 内容 |
|---|---|
| `PAYMENT_FLOW_DIAGNOSIS.md` | 最初端到端只读诊断 + Stripe sandbox 实配核对结果 |
| `PAYMENT_HARDENING_LOG.md` | 第一轮加固(webhook 测试、P1-5/P1-7/P2-8 等修复) |
| `PROVISION_COMMUNITY_AUTH_FIX_LOG.md` | provision-community 鉴权漏洞修复(P0) |
| `WEBHOOK_NULL_EMAIL_FIX_LOG.md` | webhook null-email 崩溃 + 错误档位 license 修复 |
| `INVOICE_SUBSCRIPTION_FIELD_FIX_LOG.md` | Stripe API clover 版本字段迁移修复 |
| `REFUND_LICENSE_LOOKUP_FIX_LOG.md` | 退款无法定位 license 的修复 |
| `E2E_DEV_VALIDATION_LOG.md` | A6 九项真实端到端验证的完整过程与证据 |
| `docs/roadmap/commercial-flow-followups.md` | 已知但明确延后的问题跟踪 |

---

## 一、必须做(Blocking——不做就不能上线)

### 1.1 部署最新代码到 prod

```
pnpm deploy:prod
```

~~`fix/payment-flow-hardening` 分支目前领先 main 8 个 commit,包含本轮全部安全修复、收入完整性修复、测试覆盖。Prod 目前跑的是 2026-01-20 的代码,不含任何本轮内容。~~
**(2026-07-09 更正:上述表述已过期——分支早已并入 main 且 prod 已在跑加固后代码,live 购买链路验证见 §1.5。)**

**执行前确认:**
- [x] 分支已 merge 到 main(2026-07-05 前完成,`main..fix/payment-flow-hardening` 为空)
- [x] 本地 CI 四步(build/lint/typecheck/test)全绿
- [x] 部署后 `curl https://api.replimap.com/` 确认返回的版本/环境信息已更新(§5 修复 `f62bd94c`、#6/#7 `90bfc4ca` 均已 live)

### 1.2 配置 prod secrets

`wrangler.toml` 的 prod secrets 清单本身有误(缺 `CLERK_ISSUER`,列了代码不用的 `CLERK_PUBLISHABLE_KEY`),按实际代码需求配置:

```
npx wrangler secret put STRIPE_SECRET_KEY --env prod
npx wrangler secret put STRIPE_WEBHOOK_SECRET --env prod   # 见 1.4,需先拿到新 secret
npx wrangler secret put CLERK_ISSUER --env prod
npx wrangler secret put CLERK_SECRET_KEY --env prod
npx wrangler secret put ADMIN_API_KEY --env prod
```

**已知风险:** `CLERK_ISSUER` 未设置时,`provision-community` 会 fail-closed 返回 503(设计如此,不是 bug),但意味着 dashboard 首屏自助开通 community 会全部失败。**部署当天必须一次性配齐,不能分批。**

- [x] `wrangler secret list --env prod` 确认全部 5 个 secret 已设置(**2026-07-09 核实**:实际存在 8 个——上述 5 个全部在列,另有 `CLERK_PUBLISHABLE_KEY`、`ED25519_PRIVATE_KEY`、`LICENSE_SIGNING_KEY`。`CLERK_ISSUER` 生效的行为证据:prod `provision-community` 无 token 返回 401 而非 fail-closed 503)

### 1.3 对齐 prod D1 迁移账本(不执行任何迁移)

**真实结论(2026-07-04 只读核实):`replimap-prod` 已经是 011/012 的目标终态,不需要执行任何迁移,只需要账本对齐。** 这推翻了本节此前"照 dev 一样套用 012 + 核实 011"的假设——dev 与 prod 不是同一血统。

Prod 库由 **drizzle-kit 直接建表**(dev 是迁移血统,prod 是 drizzle 血统),现状已逐项核实:

- 单数 `user` 表存在、无 `users`(复数)→ 011 的 rename 目标已达成
- `licenses.plan` 定义为 `text DEFAULT 'free' NOT NULL`,**没有任何 CHECK 约束** → 011 声称的重建理由(旧 CHECK 拒绝 `'community'`)对 prod 不成立(默认值仍是遗留的 `'free'`,但只是 cosmetic——handler 每次 insert 都显式写入 plan,从不依赖默认值)
- 已存在 `licenses_session_id_idx`(`is_unique=1`,列 `stripe_session_id`)→ **012 想恢复的 UNIQUE 并发保护 prod 本来就有**,只是索引名不同
- 全部数据表 **0 行**(user / licenses / payment / license_machines / processed_events / account / session 均为 0),无客户或测试数据
- `d1_migrations` 已记录到 `010_fingerprint_type.sql`(2026-01-20),**011、012 未记录**

> 注:D1 控制台/list API 报的 `num_tables: 0` 是过期的不可靠元数据。实际 `sqlite_master` 里有约 21 张表 + 2 视图,库是完整的。

**⚠️ 绝对不要跑 `wrangler d1 migrations apply replimap-prod --env prod --remote`。** 它会把未记录的 011、012 当作待应用执行,而这两条在 prod 上是**破坏性**的(数据不丢,但会回退 schema):

1. **011 的 licenses 重建是无条件的**:`DROP TABLE IF EXISTS licenses; ALTER TABLE licenses_new RENAME TO licenses;` 会删掉 prod 当前正确的 drizzle licenses 表并整表替换(注释里写的 "no-op on production" 是错的)。
2. **索引名全局撞车(核心机制)**:011 执行 `CREATE INDEX IF NOT EXISTS payment_session_id_idx ON licenses(stripe_session_id)`。但 prod 已有同名索引 `payment_session_id_idx`——它是 **payment 表**上的合法索引(`CREATE INDEX payment_session_id_idx ON payment(session_id)`)。SQLite 索引名是**全局唯一**的,`IF NOT EXISTS` 命中这个已存在的名字后**静默跳过**,导致重建后的 licenses 表 `stripe_session_id` 上**没有任何索引**(丢失当前的 UNIQUE 保护),而 011 的 `licenses_new` 内联定义也没有该列 UNIQUE。
3. **012 连带误删**:接着 `DROP INDEX IF EXISTS payment_session_id_idx` 会把上面 **payment 表那个真索引删掉**(且不会重建),再建 `licenses_session_id_unique_idx`。最终 payment 表白白丢一个索引。

**正确做法 —— 只做账本对齐(纯元数据写,不碰任何表/索引):**

```sql
-- 仅账本对齐,勿跑 wrangler d1 migrations apply。
-- 把 011/012 标记为已应用,因为 prod 的目标终态已由 drizzle-kit 直接建好。
-- id 省略(AUTOINCREMENT 自动分配);name 必须是精确文件名;
-- applied_at 用执行当刻的 UTC,非真实历史执行时间(prod 从未真正跑过这两条)。
INSERT INTO d1_migrations (name, applied_at) VALUES
  ('011_drizzle_schema_bootstrap.sql', datetime('now')),
  ('012_restore_session_id_unique.sql', datetime('now'));
```

- [x] 用 `wrangler d1 execute replimap-prod --env prod --remote --command "<上面的 INSERT>"` 执行账本对齐(已于 2026-07-04 11:16:55 UTC 执行,`d1_migrations` id 13/14)
- [x] 执行后 `SELECT name FROM d1_migrations WHERE name LIKE '01%'` 确认 011、012 已记录(2026-07-09 复核通过)
- [x] `wrangler d1 migrations list replimap-prod --env prod --remote` 显示 **"No migrations to apply!"**(2026-07-09 核实;注:用只读的 `migrations list` 验证即可,不要用 `migrations apply` 做验证)
- [x] 只读核对 prod 仍保有 payment 表的 `payment_session_id_idx` 和 licenses 的 UNIQUE(stripe_session_id)(2026-07-09 核实:`payment_session_id_idx ON payment(session_id)` 与 `licenses_session_id_idx` UNIQUE 均原封不动)

### 1.4 对齐 prod webhook signing secret

**当前状态(2026-07-09 核实,本节矛盾已解):** 旧的 `we_1SnXkbAKLIiL9hdwR1W9kOif`(inspiring-splendor,401 Invalid signature)是 **sandbox 账号**(`acct_1Sg0CYAKLIiL9hdw`,ID 内嵌账号哈希可证)上指向 prod URL 的端点,**现已删除**——sandbox 账号目前仅剩 dev 端点(`we_1TpJSVAKLIiL9hdw...` → api-dev,含 `customer.deleted` 共 8 类事件)。真正的 live 端点在 live 账号(`acct_...AM46G6RB9J`)上,且与 prod `STRIPE_WEBHOOK_SECRET` 匹配:prod D1 `processed_events` 记录了 2026-07-04 UTC 真实购买的全部 5 类事件(`invoice.paid` / `checkout.session.completed` / `customer.subscription.created` / `charge.refunded` / `customer.subscription.deleted`)均验签+处理成功。

- [x] ~~Roll signing secret~~(不再需要:失配的旧端点已删,live 端点验签成功有 processed_events 实证)
- [x] `STRIPE_WEBHOOK_SECRET --env prod` 已设置且与 live 端点匹配(同上实证)
- [ ] **仍待人工**:登录 live Stripe Dashboard 确认 live 端点已订阅 `customer.deleted`(本机只有 sandbox API key,无法远程核实;这是 §1.4 唯一剩余项)
- [x] live 端点投递 200 有实证(真实购买链路,见 `PROD_E2E_SMOKE_TEST_LOG.md`)

**顺序提醒:** 必须先完成 1.1(部署新代码),再做这一步——如果先对齐密钥、代码还是旧的,Stripe 侧积压的重试事件会被旧代码(无本轮任何加固)处理,可能产生脏数据。

### 1.5 部署后端到端冒烟测试

**✅ 支付主链路(正向 + 退款/取消)已在 live 环境端到端验证 —— 证据:[`PROD_E2E_SMOKE_TEST_LOG.md`](./PROD_E2E_SMOKE_TEST_LOG.md)(2026-07-05:真实 $29 Pro Monthly 购买 → 退款 + 立即取消,全程按预期)。**

参照 `E2E_DEV_VALIDATION_LOG.md` 的方法,在 prod 上验证:
- [x] 真实 live 交易 → webhook 200 → license 正确落库:本次以 **subscription 模式 + 全额退款/取消**验证(比"test-mode lifetime"更强);`checkout.session.completed`/`customer.subscription.created`/`invoice.paid` 三事件均入 processed_events,退款/取消逆向链路也验证通过,全表零漂移。lifetime checkout 未单独跑,可选补测。
- [ ] provision-community:鉴权闸门已验证(2026-07-09 live 复测:无 token → 401,伪造 token → 401,均非 503,证明 Clerk 已配置且 fail-closed 逻辑未触发);**正向开通(真实 Clerk 登录)+ 伪造他人邮箱被拒(403)仍待验证——需要真实浏览器 Clerk session,无法脚本化,留给人工**。
- [ ] 确认 `[Stripe][MANUAL_REVIEW]` 这类关键错误日志在 prod 上是否有实际可见的监控/告警渠道(**仍未接入**;建议 Cloudflare Logpush 或等效告警,否则"收了钱但发错/不发 license"不会被及时发现)。

---

## 二、强烈建议(Should——不阻塞上线,但建议部署当天或紧接着做)

- [x] **followups §5 时序问题** —— **已修复并上线 prod**(2026-07-05,commit `2134d8b`,prod 版本 `f62bd94c`)。两个方向都做了:主修复从 `subscription.items.data[]` 读取账单周期(clover API 字段位置,零额外 API 调用),兜底是 license 不存在时 `invoice.paid` 返回 500 且不标记 processed。dev 真实 sandbox 事件验证通过(乱序自然复现,`current_period_end` 正确落库)。详见 `INVOICE_ORDERING_BACKFILL_FIX_LOG.md`。
- [ ] **GitHub Dependabot 45 个依赖漏洞**(8 high, 20 moderate, 17 low)—— push 时 GitHub 已提示,一直没有专门处理。建议找时间看一下具体是哪些依赖,评估影响。
- [ ] **checkout-license 的 session_id-as-bearer 时效性**——该 session_id 会出现在 success 页 URL 里,如果被分享出去,持有链接的人可以取回 license key。建议加时效或一次性限制。

---

## 三、可以留到以后(产品决策,非阻塞)

- [ ] **CLI 端 Ed25519 签名验证消费**(`SecureLicenseManager` 重新设计接入)——目前 CLI 完全不验签,`REPLIMAP_DEV_MODE=1` + 明文缓存可以绕过付费墙。已加了警示日志,但底层验证逻辑未启用。是否现在补上,取决于你对"防作弊 vs 优先追增长"的判断。
- [ ] **PLAN_FEATURES 三份独立副本**(`constants.ts` / `features.ts` / `packages/config/plans.json`)——目前没有实际矛盾,只有漂移风险。建议以 `packages/config` 为真源收敛,不紧急。
- [ ] **compliance.tf 的两个原始 blocker**(subdomain slug 修复确认、真实 tfstate 端到端验证)——大概率已被这一路核心算法优化那几轮的真实数据验证(1594 资源 demo)顺带满足,建议正式核实后勾掉,不需要重新做。
- [ ] **cost 定价表未知型号兜底**——不同链路对未知实例型号的默认值不同,数字会不一致,但已知型号全部统一。属价格表维护范畴。
- [ ] **`core/drift/detector.py`(B 套引擎)死代码清理**——已确认 100% 无调用,是否清理不影响任何功能。

---

## 四、执行顺序总览

```
1.1 部署新代码 → 1.2 配置 secrets → 1.3 D1 迁移账本对齐(仅 INSERT,不跑 apply)
  → 1.4 对齐 webhook secret + 补事件订阅 → 1.5 端到端冒烟验证
  → (确认全部通过后)正式对外宣布/开放付费入口
  → 二、三 部分按优先级陆续处理,不阻塞已完成的上线
```

**任何一步发现异常,回到对应的 fix log 文档核实修复是否真的已经部署生效,不要假设"dev 验证过了所以 prod 一定没问题"——尤其是 1.3:dev 是迁移血统、prod 是 drizzle 血统,两者 schema 来源根本不同,绝不能照搬 dev 的 `migrations apply` 执行记录(会触发 payment 索引撞车)。**
