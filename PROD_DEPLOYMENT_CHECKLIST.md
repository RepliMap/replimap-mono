# RepliMap 支付流程 — 生产部署前检查清单

**创建日期:** 2026-07-04
**背景:** 本清单汇总自任务 3(端到端支付流程打通)全过程的诊断与加固工作。所有代码修复已在 `fix/payment-flow-hardening` 分支上完成,并在 **dev worker + Stripe sandbox** 环境下用真实数据完整验证通过(见 `E2E_DEV_VALIDATION_LOG.md`)。**Prod 环境目前仍是 2026-01-20 的旧代码,尚未部署任何本轮加固。**

**核心结论:** 生产商业化链路目前实质上不可用——prod worker 落后代码 3 个月、webhook 签名一直失败(401)、多个真实场景下会静默产生错误数据(错发 license 档位、退款无法撤销 lifetime 授权等)。这份清单的目的是确保上线前把这些已知问题全部闭环,而不是"部署完再说"。

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

`fix/payment-flow-hardening` 分支目前领先 main 8 个 commit,包含本轮全部安全修复、收入完整性修复、测试覆盖。Prod 目前跑的是 2026-01-20 的代码,不含任何本轮内容。

**执行前确认:**
- [ ] 分支已 merge 到 main(或按你们的发布流程操作)
- [ ] 本地 CI 四步(build/lint/typecheck/test)全绿
- [ ] 部署后 `curl https://api.replimap.com/` 确认返回的版本/环境信息已更新

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

- [ ] `wrangler secret list --env prod` 确认全部 5 个 secret 已设置

### 1.3 套用迁移 012 到 prod D1

```
wrangler d1 migrations apply replimap-prod --env prod --remote
```

**执行前必读:** dev 环境执行这条命令时,发现待应用的不止 012,还有一条从未被追踪的 011(整表重建 `licenses` + 合并 `users`→`user` 单数表 + `DROP TABLE users`)。Prod 库当前状态(011 是否也需要跑)需要先用同样的方式核实,不能假设和 dev 一致:

- [ ] 先只读核实 prod D1 的 `d1_migrations` 表,确认哪些迁移待应用
- [ ] 如果 011 也待应用,先核实 `users`(复数)表在 prod 里的行数和数据、`user`(单数)表当前状态,评估整表重建的真实影响面(dev 上这一步发现只有 1 个 stale 用户,prod 可能有更多真实数据,需要重新评估风险)
- [ ] 确认后执行,执行后核对 `licenses_session_id_unique_idx` 确实是 UNIQUE 索引

### 1.4 对齐 prod webhook signing secret

**当前状态:** prod 的 webhook endpoint(`we_1SnXkbAKLIiL9hdwR1W9kOif`,inspiring-splendor)一直返回 `401 Invalid signature`,根因是 Stripe 侧的 signing secret 与 `STRIPE_WEBHOOK_SECRET` 不一致。这是导致"生产 D1 至今 0 行"的直接原因。

**建议:roll 一个新的 secret**(而不是复用现有值,因为现有值来历不明且已确认失配):
- [ ] Stripe Dashboard → Webhooks → inspiring-splendor → Roll signing secret
- [ ] `wrangler secret put STRIPE_WEBHOOK_SECRET --env prod`,粘贴新值
- [ ] 补充订阅缺失的 `customer.deleted` 事件(当前只有 7 类,少这一个)
- [ ] 用 Dashboard 的 "Send test events" 发一次测试事件,确认返回 200

**顺序提醒:** 必须先完成 1.1(部署新代码),再做这一步——如果先对齐密钥、代码还是旧的,Stripe 侧积压的重试事件会被旧代码(无本轮任何加固)处理,可能产生脏数据。

### 1.5 部署后端到端冒烟测试

参照 `E2E_DEV_VALIDATION_LOG.md` 的方法,在 prod 上至少验证:
- [ ] 一次真实 test-mode(如果 prod 连的是 live Stripe 账户,用 Stripe 的测试卡功能;如果还没切到 live,继续用 sandbox)lifetime checkout → webhook 200 → license 正确落库
- [ ] 一次 provision-community 调用(真实 Clerk 登录)→ 正确开通,且伪造他人邮箱会被拒绝(403)
- [ ] 确认 `[Stripe][MANUAL_REVIEW]` 这类关键错误日志在 prod 上是否有实际可见的监控/告警渠道(如果只有 `wrangler tail` 能看到,建议先接入 Cloudflare Logpush 或等效告警,否则这类"收了钱但发错/不发 license"的情况不会被及时发现)

---

## 二、强烈建议(Should——不阻塞上线,但建议部署当天或紧接着做)

- [ ] **followups §5 时序问题**:`invoice.paid` 可能早于 `customer.subscription.created` 到达(dev 环境两次真实复现,判定为常态而非偶发)。后果是首期账单周期回填丢失,且事件级幂等会挡住任何后续重投修复。建议修复方向:license 不存在时不要把 `invoice.paid` 标记为已处理(返回非 2xx 触发 Stripe 重试),或在 `subscription.created` 里补一次周期回填自愈逻辑。预估工作量约半天。
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
1.1 部署新代码 → 1.2 配置 secrets → 1.3 套用迁移 012(含核实 011)
  → 1.4 对齐 webhook secret + 补事件订阅 → 1.5 端到端冒烟验证
  → (确认全部通过后)正式对外宣布/开放付费入口
  → 二、三 部分按优先级陆续处理,不阻塞已完成的上线
```

**任何一步发现异常,回到对应的 fix log 文档核实修复是否真的已经部署生效,不要假设"dev 验证过了所以 prod 一定没问题"——尤其是 1.3 的迁移步骤,dev 和 prod 的历史数据状态可能不同,需要重新核实,不能照搬 dev 的执行记录。**
