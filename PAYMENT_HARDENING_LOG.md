# 支付流程加固记录(PAYMENT_HARDENING_LOG)

**日期:** 2026-07-04
**输入:** `replimap-payment-diagnosis/PAYMENT_FLOW_DIAGNOSIS.md`(2026-07-04 只读诊断)
**分支:**
- `replimap-mono` → `fix/payment-flow-hardening`(API/前端/CI/文档)
- `replimap`(Python CLI,worktree `replimap-payment-diagnosis`)→ `fix/payment-flow-hardening`
**方法论:** 每个 bug 先写失败测试(RED)再修复(GREEN);测试针对真实 handler + 真实数据库,不用与实际脱节的 mock。
**明确未做(按本轮约定):** 生产部署、CLI 端 Ed25519 验签消费逻辑重做、创建/修改任何 Stripe 资源、真实 Stripe test-mode 全链路验证。

---

## 0. 新建测试基座(支撑全部 webhook 测试)

`apps/api/tests/real-d1.ts`:
- **真实数据库**:用 Miniflare(`wrangler dev --local` 同款引擎 workerd/SQLite)起 D1,套用真实 schema 引导链 `schema.sql` → `migrations/003..012`。UNIQUE 约束、ON CONFLICT、FK 级联都是真实行为——旧的正则表名 mock(`helpers.ts createMockDB`)无法覆盖这些。
- **真实签名**:`stripeSignatureHeader()` 按 Stripe 文档算法计算 `t=<unix>,v1=hex(HMAC_SHA256(secret, "<t>.<payload>"))`,生产 `verifyStripeSignature` 原样运行,**没有任何 crypto stub**(旧测试文件把全局 crypto.subtle.sign stub 成固定 32 字节)。
- 唯一保留的 stub:`customer.subscription.created` 自愈路径里对 `api.stripe.com` 的 fetch(测试不能真打 Stripe)。

---

## 1. P0-3:Stripe webhook handler 零测试 → 32 个真实 handler 测试

**修复前证据:** 旧 `tests/stripe-webhook.test.ts` 从不 import `handleStripeWebhook`,只断言手写字面量(如 `expect(subscriptionSession.mode).toBe('subscription')`),注释自认 "In actual handler, this returns early"。

**修复后:** `tests/stripe-webhook.test.ts` 全部重写(32 个测试,全部调用真实 handler + 真实 D1):
- 验签 6 个:合法签名通过;错误 secret 被拒(401,且无任何副作用落库);签名后篡改 payload 被拒;缺签名头 400;时间戳超 5 分钟容差 401;未配置 secret 503。
- 幂等 4 个:同 event id 顺序重投(第二次返回 `duplicate:true`,只有 1 张 license);**同 event id 并发 ×5**;同订阅不同 event id 重投;同 session 不同 event id 并发(lifetime)。
- 8 类事件全覆盖:checkout.session.completed(subscription/payment/setup 三种 mode)、subscription.created(含自愈、自愈失败返 500 且**不标记已处理**以保住 Stripe 重试、缺周期字段容错)、subscription.updated(升级保设备/降级踢设备/status 映射/未知订阅不崩)、subscription.deleted、invoice.paid(周期回填+复活)、invoice.payment_failed、charge.refunded(撤销 lifetime/不动订阅/无 customer 容错)、customer.deleted(全部过期)。
- 纯函数测试(lifetime 助手、价格映射)搬到 `tests/license-helpers.test.ts`,去掉了污染全局的 crypto stub。

**测试基座顺带抓到两个诊断未发现的真 bug(先 RED 后修):**

### 1a. `findOrCreateUser` 并发竞态 → 500
- **RED:** 并发重投同一 checkout 事件,部分请求 500(`user.email` UNIQUE 约束打掉 check-then-act 的输家)。
- **修复:** `src/lib/db.ts` findOrCreateUser 加竞态兜底——insert 失败后按 email 重查,存在则复用(并按需回填 customer id),与 license 创建路径的兜底模式一致。

### 1b. `licenses.stripe_session_id` 的 UNIQUE 约束在迁移 011 中丢失
- **证据:** 008 建了 `CREATE UNIQUE INDEX licenses_session_id_idx`;011 重建 licenses 表时旧索引随 DROP TABLE 消失,重建成了**普通索引** `payment_session_id_idx`;而 `src/db/schema.ts:214` 仍声明 `.unique()`(schema 漂移)。webhook 代码注释声称的"UNIQUE 兜底"对 lifetime 幂等实际不存在——并发不同 event id 重投同一 session 可发出两张 license。
- **修复:** 新增 `migrations/012_restore_session_id_unique.sql`(drop 普通索引,建 UNIQUE 索引)。dev/prod 库现在均为 0 行 license,套用无风险。**注意:dev/prod 远程库尚未套用此迁移(本轮不动生产),部署时需 `wrangler d1 migrations apply`。**

---

## 2. P1-5:subscription.updated 缺周期字段 500(RED→GREEN)

- **RED:** `P1-5 regression` 测试——update 事件缺 `current_period_start/end` → 实测 500(`timestampToISO(undefined)` → `new Date(NaN).toISOString()` RangeError),tier 变更丢失。
- **修复:** `src/handlers/stripe-webhook.ts` handleSubscriptionUpdated 按 create 分支同款 `typeof === 'number'` 守卫;`updateLicensePlan` 本就跳过 undefined 字段,既有周期值不被破坏。
- **GREEN:** 200 + plan 更新为 team + 原周期字段保留。

## 3. P1-7:付费 license 非 active 后 provision-community 重复发放(RED→GREEN)

- **RED:** `tests/provision-community.test.ts` 整体转为真 D1(9 个测试);两个 P1-7 回归测试实测失败——pro license 置 past_due/canceled 后再 provision,产生第二张 active community license。
- **修复:** `src/lib/db.ts` 新增 `getNonExpiredLicenseByUserEmail`(最新一张 status != 'expired' 的 license);`provision-community.ts` 幂等检查改用它。语义:**任何非 expired 状态(active/past_due/canceled/revoked)都阻止重复发放**,并把该 license 原样返回(dashboard 能看到真实状态);只有完全 expired 才允许发新社区 key。revoked 也阻止——退款被撤销的用户不会静默拿到新 key(如需放开是产品决策,单独讨论)。
- **GREEN:** 9/9,含"expired 后允许重新发放"的正向用例。

## 4. P2-8:Sovereign checkout 显式拒绝(RED→GREEN)

- **RED:** `tests/billing.test.ts` 加 3 个测试(monthly/annual/lifetime),实测走到 Stripe 调用(占位 price id)。
- **修复:** `src/handlers/billing.ts` 在 plan 解析前显式拒绝 `plan === 'sovereign'`,返回 400 + "not available for self-serve checkout … contact sales",不触碰 Stripe。
- **GREEN:** 18/18,断言含 `mockFetch` 未被调用。

## 5. P2-10:文档失实声明纠正

`docs/roadmap/commercial-flow-followups.md` §3 原文 "Idempotency is verified by unit tests" 为假(那些函数当时没有任何测试)。已改写为准确状态:注明 2026-07-04 起真实覆盖的范围(真 handler + 真 D1:顺序重投/并发重投/跨 event id 重投),保留历史注记,并如实列出**仍未覆盖**:50+ 高并发压测、事件乱序排列组合、经真实 HTTP 栈(wrangler dev)的重投。

## 6. P2-11:一致性修复

### 6a. license key 改用 CSPRNG(RED→GREEN)
- **RED:** `license-helpers.test.ts` 把 `Math.random` stub 成抛异常 → generateLicenseKey 崩溃,证明依赖 PRNG。
- **修复:** `src/lib/license.ts` 改用 `crypto.getRandomValues` + 拒绝采样(接受 <252=7×36,消除取模偏差)。格式与唯一性测试(5000 样本无重复)通过。

### 6b. Ed25519 密钥导出格式修复(RED→GREEN)
- **RED:** `tests/ed25519.test.ts`(新增 5 个测试)——`generateEd25519KeyPair` 用 `exportKey('raw')` 导出私钥,WebCrypto 对 Ed25519 私钥根本不支持 raw(运行时直接抛),即使支持也与 signer(pkcs8)/verifier(spki)不匹配。5/5 失败。
- **修复:** `src/lib/ed25519.ts` 私钥导出 pkcs8、公钥导出 spki(base64)+ raw(32 字节 hex,供 CLI 内嵌)。生成→签名→验签往返、篡改拒绝、错密钥拒绝、过期拒绝,5/5 通过。**注:CLI 端验签消费逻辑本轮不动(按约定)。**

### 6c. CLI 缺省 plan 统一为 community(RED→GREEN,Python 仓库)
- **RED:** `tests/test_licensing_hardening.py` —— validate 响应缺 `plan` 字段时,实测得到 `Plan.PRO`。
- **修复:** `replimap/licensing/manager.py:316` 缺省值 `"pro"` → `"community"`,与服务端 `getPlanFromPriceId` 的缺省一致,CLI 永不授予高于服务端的权限。

### 6d. PLAN_FEATURES 三份副本:评估后本轮不收敛,差异记录如下
- **三份定义:** ① `apps/api/src/lib/constants.ts:44` `PLAN_FEATURES`(resources_per_scan/scans_per_month/aws_accounts/machines/export_formats);② `apps/api/src/features.ts` `PLAN_FEATURES`(feature 名单)+ `PLAN_LIMITS`(max_accounts/max_regions/…/offline_grace_days);③ `packages/config/src/plans.json`(营销/UI 源,仅被 packages/config 构建脚本消费,API 从不 import)。
- **交叉使用点:** `validate-license.ts` 同一请求里两套都用(:148 用①的 machines/export_formats,:229-230 用②的 flags/limits)。
- **不收敛的理由:** 统一真源需要重构 validate 响应组装与共享包导出面,牵动 CLI 消费端字段,风险量级超出本轮"补测试+修正确性"的定位;且当前三份内容尚无实际矛盾(仅漂移风险)。
- **建议(后续单独立项):** 以 `packages/config` 为唯一真源导出运行时矩阵,①②改为 import,plans.json 由同一源生成。

## 7. P2-12:前端裂纹

### 7a. `GET /v1/me/usage` 死代码:删除(而非补路由)
- **决策理由:** 后端从未有该路由;前端零调用方;同数据已有真实路由 `/v1/usage/{license_key}`。补一个无消费者的别名路由只增加 API 表面积和维护负担。删除 `getLicenseUsage` 及其类型 import(`src/lib/api.ts`),`@/types/license` 里的 `LicenseUsage` 类型保留未动。

### 7b. `getOrProvisionLicenseKey` 静默吞错(RED→GREEN)
- **测试基础设施:** apps/web 原本没有单测 runner(只有 Playwright e2e)。为遵守本轮 TDD 方法论,加了最小 vitest 配置(devDep + `vitest.config.ts`,只收 `src/**/*.test.ts`,与 Playwright 的 e2e/ 互不干扰)。
- **RED:** `src/lib/api.test.ts` 3 个测试——现实现返回裸 string/null,无法区分"没有 license"和"请求失败"。
- **修复:** 返回可区分的 `LicenseKeyResult`(`{status:'ok',licenseKey}` | `{status:'error',message}`);`dashboard/page.tsx` 失败时渲染 `role="alert"` 错误横幅(不再静默显示"No License"空态);`dashboard/license/page.tsx` 失败时复用既有 `ErrorState` 组件。
- **GREEN:** 3/3 + `tsc --noEmit` 干净。

## 8. P0-4:CI 把关

`.github/workflows/ci.yml`:
- `pnpm lint || true` → `pnpm lint`;`pnpm typecheck || true` → `pnpm typecheck`;新增 `pnpm test` 步骤。
- 接线:root `package.json` 加 `"test": "turbo run test"`;`turbo.json` 加 test 任务;`apps/api`/`apps/web` 的 `test` 脚本统一为一次性 `vitest run`(原 api 的 `test` 是 watch 模式,会挂死 CI),watch 模式挪到 `test:watch`。

**去掉 `|| true` 后暴露的三个存量 CI 阻塞(全部修复,否则 CI 必红):**
1. **api typecheck:** `checkout-license.ts:65` 未使用参数 `request` → 改 `_request`。
2. **api lint:** apps/api 完全没有 ESLint 配置(ESLint 9 需要 flat config,原先直接 exit 2——这就是当初加 `|| true` 的原因)。新增 `eslint.config.mjs`(`@eslint/js` recommended + `typescript-eslint` recommended,`_` 前缀参数豁免),`eslint src/` 现为 0 错误;`eslint`/`@eslint/js`/`typescript-eslint` 加入 api devDependencies。
3. **web build(生产构建本来就是坏的):** `/checkout` 与 `/checkout/success` 顶层使用 `useSearchParams()` 无 Suspense 边界,`next build` 预渲染直接失败(missing-suspense-with-csr-bailout)。修复:两页拆出内层组件,默认导出包 `<Suspense>`(fallback 为加载态)。此项 RED 即 `next build` 失败本身,GREEN 为构建通过——这也意味着**在本轮之前,这两个支付核心页面无法出现在任何成功的生产构建里**,与诊断报告"生产链路从未上线"的结论互为印证。

**最终本地全链验证(与 CI 完全一致的四步):** `pnpm build` ✓ / `pnpm lint` ✓ / `pnpm typecheck` ✓ / `pnpm test` ✓(api 12 文件 178 测试 + web 1 文件 3 测试)。

## 9. REPLIMAP_DEV_MODE 警示(Python 仓库,RED→GREEN)

- **RED:** 3 个测试(激活时告警/只告警一次/未激活不告警)——现实现无任何日志。
- **修复:** `manager.py` `is_dev_mode()` 首次检测到激活时输出 WARNING:"⚠️ REPLIMAP_DEV_MODE is active — license checks are bypassed and all features are unlocked. This should never be set in production.",带 warn-once 闩锁避免刷屏。底层验证逻辑未动(按约定)。
- **GREEN:** 5/5(含 6c 的两个);ruff format/check 通过;既有 licensing 套件 118/118 无回归。

---

## 测试数量对账

| 位置 | 修复前 | 修复后 |
|---|---|---|
| apps/api vitest | 139(webhook handler 实际覆盖 0) | **178**(webhook 32 个全部打真实 handler + 真 D1) |
| apps/web 单测 | 0(无 runner) | **3**(新 vitest) |
| Python licensing | 既有若干 | **+5**(hardening 专项),全量单测见下方运行记录 |
| CI 把关 | 只 build,lint/typecheck 假绿 | build+lint+typecheck+test 四步硬门槛 |

## 残留缺口(本轮明确不做/后续决策)

1. **CLI Ed25519 验签消费**(SecureLicenseManager 重设计与接入)——等你单独决策;6b 已把服务端密钥工具修到可用。
2. **生产部署**:代码/迁移 012 都只在分支上;prod worker 仍是 2026-01-20 旧代码,`replimap-dev`/`replimap-prod` 远程库均未套 012。
3. **真实 Stripe test-mode 全链路验证**(Stripe MCP 已授权,下一轮)。
4. 高并发压测、事件乱序排列组合、经真实 HTTP 栈的重投(见 §5 文档新状态)。
5. `packages/config` 真源收敛(见 §6d 建议)。
6. 诊断报告中其余未列入本轮范围的问题(如 provision-community 无鉴权的 key 枚举风险 P0 级安全项、checkout success 页 Path B 返回社区 key 的竞态)——**注意:这两项不在本轮任务清单里,仍未修复**。
