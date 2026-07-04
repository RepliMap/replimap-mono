# provision-community 鉴权修复记录(P0 安全)

**日期:** 2026-07-04
**分支:** `fix/payment-flow-hardening`(replimap-mono)
**范围:** 只修 `POST /v1/license/provision-community` 的鉴权缺失,不做其他重构。不部署,不动已延后项(CLI 验签接线等)。
**方法论:** RED→GREEN;测试针对真实 handler + 真实 D1 + **真实 RS256 令牌**(真 JWKS 验签),不用与实际脱节的 mock。

---

## 1. 漏洞复现证据(修复前)

**修复前 `handleProvisionCommunity` 无任何身份验证**:`src/index.ts:212-213` 直接分发,handler 内只做 IP 限流(`activate` 档 10/60s)+ 邮箱正则,邮箱**完全取自请求 body**。因此:
- 任意匿名调用者传 `{email: "victim@…"}` 即可为该邮箱建 community license;
- 更严重:若该邮箱已有**任何非 expired license(含付费)**,幂等分支会把**该邮箱现有 license key 原样返回**——一个"输入邮箱、吐出对方 key"的凭证泄露预言机,且不区分 plan。

**RED(14/15 失败)**:新 `tests/provision-community.test.ts` 的 `authentication` 套件对旧 handler 运行,7 条 auth 断言全红,7 条"已认证自助开通"因缺 token 全红;唯一通过的是"body 匹配"那条(旧逻辑恰好用 body email 建 license)。命令:`npx vitest run tests/provision-community.test.ts`。

## 2. 修复方案

**核心原则:令牌身份是唯一真源,body 邮箱不再被信任。**

新增 `src/lib/clerk.ts` —— Worker 内的 Clerk 会话令牌验证(无 Clerk SDK,纯 Web Crypto + JWKS):
- `verifyClerkSession(request, env)`:取 `Authorization: Bearer <jwt>` → 按 header.kid 从 `{CLERK_ISSUER}/.well-known/jwks.json` 取 JWK → RS256 验签(`RSASSA-PKCS1-v1_5`/SHA-256)→ 校验 `iss === CLERK_ISSUER`(钉住签发方,拒绝他实例令牌)、`exp`/`nbf`(±60s 容差)→ 解析邮箱:优先 `email` claim(需 Clerk JWT 模板),否则用 `CLERK_SECRET_KEY` 调 Clerk Backend API `GET /v1/users/{sub}` 取主邮箱。任一步失败返回 `null`(调用方按 401 处理)。
- `isClerkConfigured(env)`:缺 `CLERK_ISSUER` 或 `CLERK_SECRET_KEY` 时为 false。

`src/handlers/provision-community.ts` 强制鉴权(新增逻辑,顺序):
1. **fail closed**:`!isClerkConfigured(env)` → **503**(宁可拒绝也不开放)。
2. `verifyClerkSession` 返回 null → **401**。
3. 解析 body(可选);若 `body.email` 存在且 `!== identity.email`(小写比较)→ **403**,不发/不返回任何 license。
4. **provisioning 使用 `identity.email`(令牌身份)**,而非 body。其余幂等/建库逻辑不变(P1-7 行为保留)。

`src/types/env.ts`:新增 `CLERK_ISSUER?`、`CLERK_SECRET_KEY?`。
`src/types/api.ts`:ErrorCode 联合新增 `FORBIDDEN`、`SERVER_CONFIG_ERROR`。
`apps/api/.env.example`:补 Clerk 两项 + fail-closed 说明。

前端(`apps/web`):
- `src/lib/api.ts`:`request` 支持 `authToken`(设 `Authorization: Bearer`);`provisionCommunityLicense(authToken)` 改为发令牌、body `{}`、**不再发邮箱**;`getOrProvisionLicenseKey(authToken | null)` 无令牌直接返回可见错误(不打 API)。
- `src/app/dashboard/page.tsx`、`src/app/dashboard/license/page.tsx`:服务端组件用 `auth().getToken()` 取令牌转发(取代原来传 `user.emailAddresses[0]`)。

## 3. GREEN 与"正常自助开通未被破坏"的证据

`tests/provision-community.test.ts` **15/15 通过**。测试基座 `tests/clerk-harness.ts` 现场生成 RSA 密钥对、发布真实 JWKS、签真实 JWT,生产验签代码原样运行(与 webhook 的真实 HMAC 基座同一哲学);唯一 stub 是 JWKS/Clerk-backend 的 `fetch` 边界。

**攻击面(全部拒绝且无泄露):**
- 无 token → 401,库中 0 license;
- token 身份 ≠ body 邮箱 → 403,0 license;
- 受害者已有付费 license 时,不匹配令牌调用 → 403 且响应体**不含**受害者 key(显式断言);
- 他方密钥签发的伪造令牌 → 401;过期令牌(超容差)→ 401;非信任 `iss` → 401;
- Clerk 未配置 → 503。

**正常自助开通(全部 GREEN——证明修复没破坏合法路径):**
- 带 email claim 的令牌 → 201,license 建在**令牌邮箱**上(查 `user.email` 确认);
- body 邮箱与令牌一致(大小写不敏感)→ 201;
- **令牌无 email claim(默认 Clerk 会话令牌就是这样)→ 走 Backend API 回退取邮箱 → 201**;
- 幂等重复调用 → 200 同一 key;自己的付费 license 原样返回不覆盖;P1-7(past_due/canceled 不重发)保留;expired 后允许重发。

dashboard 首屏自助开通场景本就是登录后调用,天然带会话令牌 → 上述"无 email claim 令牌 → Backend 回退 → 201"这条正是该场景的真实写照,已 GREEN。前端单测 `apps/web/src/lib/api.test.ts` 另加断言:请求带 `Authorization: Bearer <token>`、body 为 `{}`(邮箱不出客户端)、无令牌时不打 API。

**回归:** 本地 CI 四步全绿——`pnpm build`✓ / `pnpm lint`✓ / `pnpm typecheck`✓ / `pnpm test`✓(API **184** 测试,较上轮 178 +6;web **4**)。

## 4. 同类端点审计(接受邮箱 / 返回 license 信息)

| 端点 | 文件 | 鉴权现状 | 结论 |
|---|---|---|---|
| `POST /v1/license/provision-community` | provision-community.ts | ~~无~~ → **本轮修复:Clerk 令牌** | 已修 |
| `POST /v1/me/resend-key` | user.ts:288-359 | 无 token,但**不在响应里返回 key**(只 log/将来发到邮箱本人),且恒定返回同一消息防枚举(`user.ts:333-351`) | **设计安全**,无泄露面。投递是 TODO;真正发信前需确保只发到库中该邮箱地址 |
| `GET /v1/checkout/session/:id/license` | checkout-license.ts | 无 Clerk;以 **Stripe `cs_` session_id 作为 bearer**(文件头注释明示),邮箱由 session_id 反查 Stripe 得到、非调用者输入 | **可接受但偏弱**:任何持有该 `cs_` id 者可取回 key(post-checkout 设计如此)。session_id 不可枚举是唯一屏障。建议后续加时效/一次性,但**不在本轮范围** |
| `POST /v1/billing/portal` | billing.ts | 输入 `license_key`(非邮箱),需持有 key | 无邮箱枚举面 |
| `GET /v1/me/license`、`/v1/me/machines` | user.ts | 输入 `license_key`(query),需持有 key | 无邮箱枚举面;注:持 key 即可读,属现有模型 |
| `POST /v1/license/validate`、`activate`、`deactivate` | validate/activate/deactivate-license.ts | 输入 `license_key`(+machine),需持有 key | 无邮箱面 |

**本轮只修 provision-community(唯一"输入任意邮箱→返回 key"的直接泄露通道)。** checkout-license 的 session_id-as-bearer 时效性加固记录在案、留待后续决策。

## 5. 影响与残留

- **破坏性变更(内部 API)**:provision-community 现在**必须**带 Clerk 令牌;前端已同步改造。任何其他调用方(如 e2e community-signup spec、脚本)若直接打该端点且不带令牌,会收到 401/503——需相应更新(本轮未改 e2e harness,因它依赖真实 Clerk 会话,属部署/验证轮范畴)。
- **部署前置**:`replimap-api`/`-prod` worker 需设 `CLERK_ISSUER` + `CLERK_SECRET_KEY`(secret 已在 wrangler.toml 清单中);未设则该端点 503(fail closed,符合预期,但会挡住 dashboard 自助开通,部署时必须一并配置)。
- **未动**:checkout-license session 时效、CLI Ed25519 验签接线、生产部署、真实 Stripe test-mode 验证——均按既定延后。
