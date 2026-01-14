# P0: 凭证安全与会话管理缺陷

**会话**: Session 2.6 - 凭证安全审查
**审查日期**: 2026-01-11
**严重程度**: P0 (Critical)
**类别**: Security / Credential Management / Compliance

---

## 执行摘要 (Executive Summary)

> **状态**: ✅ **已修复** (2026-01-12)
>
> 所有凭证安全问题已在 `replimap/core/security/` 模块中实现修复。

RepliMap 的 AWS 凭证处理已升级为 **Sovereign Grade** 安全等级。

**当前状态**:
- ✅ **良好**: 凭证未被日志记录
- ✅ **良好**: 使用 boto3 标准凭证链
- ✅ **已修复**: 长时间扫描中 STS 会话令牌过期 → SessionManager 自动刷新
- ✅ **已修复**: 凭证缓存文件权限设置正确但未验证 → SecureStorage 严格模式
- ✅ **已修复**: 无凭证轮换提醒机制 → CredentialChecker 90/180 天警告

**修复组件**:
- `replimap/core/security/storage.py` - SecureStorage 原子写入 + 权限验证
- `replimap/core/security/session_manager.py` - SessionManager 凭证刷新
- `replimap/core/security/credential_checker.py` - CredentialChecker 健康检查
- `replimap/core/pagination.py` - RobustPaginator 集成 SessionManager

**发现数量**: 3 个 P0/P1 问题 → **全部修复**
**修复优先级**: ~~中等优先级 (v0.4.0)~~ → **已完成**

---

## 凭证处理安全矩阵 (Credential Security Matrix)

| 检查点 | 实现状态 | 风险等级 | 合规性 | 备注 |
|--------|---------|---------|--------|------|
| **凭证日志记录** | ✅ 无泄露 | 🟢 Low | ✅ Pass | 未发现 logger 记录凭证 |
| **明文存储** | ✅ 无 | 🟢 Low | ✅ Pass | 使用 boto3 标准路径 |
| **文件权限** | ✅ 0o600 + 验证 | 🟢 Low | ✅ Pass | SecureStorage 读取时验证 |
| **会话令牌过期** | ✅ 自动刷新 | 🟢 Low | ✅ Pass | SessionManager + MFA 重认证 |
| **MFA 重试次数** | ✅ 限制 1 次 | 🟢 Low | ✅ Pass | max_auth_retries 防止无限循环 |
| **凭证缓存 TTL** | ✅ 12 小时 | 🟢 Low | ✅ Pass | 合理时间窗口 |
| **原子写入** | ✅ 预设权限 | 🟢 Low | ✅ Pass | fchmod → write → rename |
| **并发安全** | ✅ 线程锁 | 🟢 Low | ✅ Pass | SessionManager._refresh_lock |
| **凭证轮换** | ✅ 90/180 天警告 | 🟢 Low | ✅ Pass | CredentialChecker 提醒 |
| **审计日志** | ❌ 无 | 🟡 Medium | ⚠️ Partial | 未来 Trust Center 功能 |

**总体评分**: A (95/100)

---

## [FINDING-CS001] STS 会话令牌过期导致长时间扫描中途失败

**严重程度**: Medium
**优先级**: P0
**类别**: Reliability / User Experience
**组件**: [replimap/cli/utils/aws_session.py](../../replimap/cli/utils/aws_session.py):239-315

### 描述

当使用 MFA 或 assume-role 时，boto3 生成临时会话令牌，默认有效期 1 小时。大型 AWS 账户扫描可能需要 1-3 小时，导致扫描中途失败。

```python
# replimap/cli/utils/aws_session.py:280-315
def get_aws_session(...):
    try:
        session = boto3.Session(profile_name=profile, region_name=region)

        # Verify credentials work
        sts = session.client("sts")
        identity = sts.get_caller_identity()  # 🔴 初始验证，但不检查剩余有效期

        # Cache the credentials if they're temporary (MFA)
        credentials = session.get_credentials()
        if credentials and use_cache:
            frozen = credentials.get_frozen_credentials()
            if frozen.token:  # Has session token = temporary credentials
                save_cached_credentials(
                    profile,
                    {
                        "access_key": frozen.access_key,
                        "secret_key": frozen.secret_key,
                        "session_token": frozen.token,  # 🔴 无过期时间
                    },
                )
```

**问题**:
1. **无过期时间存储**: 缓存只有 `expires_at` (缓存过期)，没有 `credentials_expire_at` (凭证过期)
2. **无中途检查**: 扫描过程中不验证会话令牌是否仍然有效
3. **错误处理不友好**: 过期时抛出 `ExpiredToken`，但用户不知道已扫描了多少

### 影响

**用户场景**:
```
时间线:
T+0:00  - 用户输入 MFA token，激活 1 小时临时凭证
T+0:05  - 开始扫描 (预计 2 小时，3000 资源)
T+1:00  - 凭证过期
T+1:00  - VPCScanner 运行正常 (已缓存数据)
T+1:05  - EC2Scanner 调用 describe_instances → ExpiredToken ❌
        - 扫描中止
        - 前面已扫描的 VPC/Subnet/SecurityGroup 数据丢失？
        - 用户需要重新输入 MFA，重新开始扫描
```

**业务影响**:
- 大客户 (Enterprise) 扫描失败率高
- Support ticket 增加
- 用户挫败感 → 影响续费

### 证据

**代码证据 1: 无凭证过期时间**
```python
# replimap/cli/utils/aws_session.py:135-173
def save_cached_credentials(...):
    # Use provided expiration or default TTL
    if expiration:
        expires_at = expiration  # 🟢 支持自定义过期时间
    else:
        expires_at = datetime.now() + CREDENTIAL_CACHE_TTL  # 🔴 但默认 12 小时

    cache[cache_key] = {
        "credentials": credentials,
        "expires_at": expires_at.isoformat(),  # 🔴 这是缓存过期，不是凭证过期
        "profile": profile,
    }
```

**代码证据 2: 过期错误处理**
```python
# replimap/cli/utils/aws_session.py:347-358
except ClientError as e:
    error_code = e.response.get("Error", {}).get("Code", "")
    if error_code == "ExpiredToken":
        clear_credential_cache(profile)  # 🔴 清除缓存
        console.print(
            Panel(
                "[yellow]Session token expired.[/]\n\n"
                "Please re-authenticate. Your cached credentials have been cleared.",
                title="Session Expired",
                border_style="yellow",
            )
        )
    # 🔴 但扫描中途如何恢复？
```

**测试复现**:
```bash
# 1. 使用 MFA profile
aws configure --profile prod-mfa
# 添加 mfa_serial = arn:aws:iam::123456789012:mfa/user

# 2. 强制短期令牌 (测试用)
aws sts get-session-token --duration-seconds 900  # 15 分钟

# 3. 运行长扫描
time replimap -p prod-mfa -r us-east-1 scan

# 预期结果:
# - 15 分钟后扫描失败
# - 错误: ExpiredToken
# - 已扫描数据可能丢失
```

### 推荐修复

**方案 1: 存储并验证凭证过期时间** ⭐ 推荐

```python
# 修改缓存结构
def save_cached_credentials(
    profile: str | None,
    credentials: dict,
    credentials_expire_at: datetime | None = None,  # 🔐 新增凭证过期时间
    expiration: datetime | None = None,  # 缓存过期时间
) -> None:
    """Save credentials to cache with expiration info."""
    # ...
    cache[cache_key] = {
        "credentials": credentials,
        "cached_at": datetime.now().isoformat(),
        "cache_expires_at": (expiration or datetime.now() + CREDENTIAL_CACHE_TTL).isoformat(),
        "credentials_expire_at": credentials_expire_at.isoformat() if credentials_expire_at else None,  # 🔐
        "profile": profile,
    }

def get_cached_credentials(profile: str | None) -> dict | None:
    """Get cached credentials if valid."""
    # ...
    entry = cache[cache_key]
    cache_expires_at = datetime.fromisoformat(entry["cache_expires_at"])

    # 🔐 检查缓存是否过期
    if datetime.now() >= cache_expires_at:
        return None

    # 🔐 检查凭证是否过期
    if entry.get("credentials_expire_at"):
        creds_expire = datetime.fromisoformat(entry["credentials_expire_at"])
        if datetime.now() >= creds_expire:
            logger.warning(f"Cached credentials expired at {creds_expire}")
            return None

    return entry["credentials"]

# 修改 get_aws_session 获取凭证过期时间
def get_aws_session(...):
    # ...
    credentials = session.get_credentials()
    if credentials and use_cache:
        frozen = credentials.get_frozen_credentials()
        if frozen.token:
            # 🔐 从 STS 获取凭证过期时间
            try:
                sts = session.client("sts")
                caller = sts.get_caller_identity()

                # 解析 AssumedRoleId 或使用默认
                # 临时凭证通常 1 小时，保守估计 50 分钟
                credentials_expire_at = datetime.now() + timedelta(minutes=50)

                save_cached_credentials(
                    profile,
                    {...},
                    credentials_expire_at=credentials_expire_at,  # 🔐
                )
            except Exception as e:
                logger.warning(f"Could not determine credentials expiration: {e}")
                # 回退到默认行为
```

**方案 2: 扫描器中途验证凭证** (补充)

```python
# replimap/scanners/base.py
class BaseScanner:
    def scan(self, graph: GraphEngine) -> None:
        """Scan resources with credential validity check."""
        # 🔐 扫描前检查凭证
        self._verify_credentials_valid()

        # ... 扫描逻辑

    def _verify_credentials_valid(self) -> None:
        """Verify AWS credentials are still valid."""
        try:
            sts = self.session.client("sts")
            sts.get_caller_identity()
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "ExpiredToken":
                raise ScannerError(
                    "AWS credentials expired during scan. "
                    "Please re-authenticate and resume scan."
                ) from e
            raise
```

**方案 3: 自动刷新凭证** (高级)

```python
# 使用 boto3 的 RefreshableCredentials
from botocore.credentials import RefreshableCredentials
from botocore.session import get_session

def get_refreshable_session(profile: str | None, region: str) -> boto3.Session:
    """Create session with auto-refreshing credentials."""

    def refresh():
        """Refresh credentials by prompting for MFA."""
        # 提示用户重新输入 MFA token
        mfa_token = typer.prompt("MFA token expired. Enter new token")

        # 调用 STS get-session-token
        sts = boto3.client("sts")
        response = sts.get_session_token(
            SerialNumber=mfa_serial,
            TokenCode=mfa_token,
            DurationSeconds=3600,
        )

        credentials = response["Credentials"]
        return {
            "access_key": credentials["AccessKeyId"],
            "secret_key": credentials["SecretAccessKey"],
            "token": credentials["SessionToken"],
            "expiry_time": credentials["Expiration"].isoformat(),
        }

    session_credentials = RefreshableCredentials.create_from_metadata(
        metadata=refresh(),
        refresh_using=refresh,
        method="sts-token",
    )

    botocore_session = get_session()
    botocore_session._credentials = session_credentials
    return boto3.Session(botocore_session=botocore_session, region_name=region)
```

### 努力估算

**方案 1 (推荐)**:
- 修改时间: 4-6 小时
- 测试: 2 小时
- 总计: 6-8 小时

**方案 2 (补充)**:
- 修改时间: 2 小时
- 集成到所有扫描器: 1 小时
- 测试: 1 小时
- 总计: 4 小时

**方案 3 (高级)**:
- 研究 boto3 RefreshableCredentials: 4 小时
- 实现: 6 小时
- MFA UI/UX: 4 小时
- 测试: 4 小时
- 总计: 18 小时

**建议**: 先实现方案 1 + 方案 2 (10-12 小时)，方案 3 作为未来优化

---

## [FINDING-CS002] 凭证缓存文件权限验证缺失

**严重程度**: Low
**优先级**: P1
**类别**: Security / Defense in Depth
**组件**: [replimap/cli/utils/aws_session.py](../../replimap/cli/utils/aws_session.py):135-189

### 描述

虽然代码正确设置了缓存文件权限 `0o600` (仅所有者读写)，但缺少验证机制，无法确保文件权限在后续操作中保持正确。

```python
# replimap/cli/utils/aws_session.py:174-187
# Atomic write: write to temp file, then rename
fd, temp_path = tempfile.mkstemp(
    dir=CACHE_DIR, prefix=".credentials_", suffix=".tmp"
)
try:
    with os.fdopen(fd, "w") as temp_f:
        json.dump(cache, temp_f, indent=2)
    os.chmod(temp_path, 0o600)  # 🟢 设置正确权限
    os.rename(temp_path, CREDENTIAL_CACHE_FILE)  # 🔴 但 rename 后权限可能被改变？
```

**潜在问题**:
1. **umask 影响**: 系统 umask 设置可能影响最终文件权限
2. **无定期验证**: 文件存在后不再检查权限
3. **无用户警告**: 如果权限被意外改变 (如 `chmod 644`)，程序不提醒

### 影响

**风险场景**:
```bash
# 1. 用户无意中修改权限
chmod 644 ~/.replimap/cache/credentials.json

# 2. 其他用户可读取
cat ~/.replimap/cache/credentials.json  # 🔴 暴露 AWS 凭证

# 3. RepliMap 继续使用，未检测到权限问题
replimap scan  # ✅ 正常运行，但凭证已泄露
```

**影响评估**:
- 共享服务器环境: 高风险
- 单用户工作站: 低风险
- 容器环境: 低风险

### 推荐修复

**方案 1: 读取时验证权限** ⭐ 推荐

```python
def get_cached_credentials(profile: str | None) -> dict | None:
    """Get cached credentials if valid."""
    if not CREDENTIAL_CACHE_FILE.exists():
        return None

    # 🔐 验证文件权限
    stat_info = CREDENTIAL_CACHE_FILE.stat()
    file_mode = stat.S_IMODE(stat_info.st_mode)

    if file_mode != 0o600:
        logger.error(
            f"Credential cache file has insecure permissions: {oct(file_mode)}. "
            f"Expected 0o600. Refusing to read."
        )
        console.print(
            Panel(
                f"[red]Security Warning[/]\n\n"
                f"Credential cache file has insecure permissions: [bold]{oct(file_mode)}[/]\n"
                f"Expected: [bold]0o600[/] (owner read/write only)\n\n"
                f"Fix with:\n"
                f"  chmod 600 {CREDENTIAL_CACHE_FILE}",
                title="Insecure File Permissions",
                border_style="red",
            )
        )
        return None  # 🔐 拒绝读取

    # 继续正常流程
    try:
        with open(CREDENTIAL_CACHE_FILE) as f:
            # ...
```

**方案 2: 写入后强制验证**

```python
def save_cached_credentials(...):
    # ... 原有写入逻辑
    os.chmod(temp_path, 0o600)
    os.rename(temp_path, CREDENTIAL_CACHE_FILE)

    # 🔐 验证最终文件权限
    stat_info = CREDENTIAL_CACHE_FILE.stat()
    final_mode = stat.S_IMODE(stat_info.st_mode)

    if final_mode != 0o600:
        logger.error(
            f"Failed to set secure permissions on credential cache. "
            f"Got {oct(final_mode)}, expected 0o600"
        )
        # 尝试修复
        CREDENTIAL_CACHE_FILE.chmod(0o600)

        # 再次验证
        if stat.S_IMODE(CREDENTIAL_CACHE_FILE.stat().st_mode) != 0o600:
            raise PermissionError(
                "Unable to set secure file permissions for credential cache"
            )
```

### 努力估算

**修复时间**: 2-3 小时
- 实现权限验证: 1 小时
- 测试 (各种权限场景): 1 小时
- 文档和警告消息: 30 分钟

---

## [FINDING-CS003] 无凭证老化检测和轮换提醒

**严重程度**: Low
**优先级**: P1
**类别**: Security / Compliance
**组件**: [replimap/cli/utils/aws_session.py](../../replimap/cli/utils/aws_session.py):239-315

### 描述

RepliMap 未检测长期凭证 (IAM User access keys) 的使用时长，缺少轮换提醒，不符合安全最佳实践 (AWS 建议 90 天轮换)。

```python
# replimap/cli/utils/aws_session.py:280-315
def get_aws_session(...):
    try:
        session = boto3.Session(profile_name=profile, region_name=region)
        sts = session.client("sts")
        identity = sts.get_caller_identity()

        console.print(
            f"[green]Authenticated[/] as [bold]{identity['Arn']}[/] "
            f"(Account: {identity['Account']})"
        )
        # 🔴 无检查凭证年龄
```

**问题**:
1. **无年龄检测**: 不查询凭证创建时间
2. **无轮换提醒**: 不建议用户轮换老化凭证
3. **合规风险**: 金融/医疗行业要求定期轮换

### 影响

**合规场景**:
- **SOC 2**: 要求凭证定期轮换
- **PCI DSS**: 要求 90 天轮换密码和密钥
- **AWS Well-Architected**: 推荐 90 天轮换 IAM keys

**用户影响**:
- 审计失败
- 安全事件响应慢
- 凭证泄露影响范围大

### 推荐修复

```python
def get_aws_session(...):
    # ... 现有认证逻辑

    # 🔐 检查凭证年龄
    if not frozen.token:  # 长期凭证 (IAM User)
        _check_credential_age(session, identity)

    return session

def _check_credential_age(session: boto3.Session, identity: dict) -> None:
    """Check IAM access key age and warn if rotation needed."""
    try:
        iam = session.client("iam")
        user_name = identity["Arn"].split("/")[-1]

        # 获取 access keys
        response = iam.list_access_keys(UserName=user_name)

        for key in response["AccessKeyMetadata"]:
            if key["Status"] != "Active":
                continue

            create_date = key["CreateDate"]
            age_days = (datetime.now(UTC) - create_date).days

            # 🔐 90 天警告
            if age_days > 90:
                console.print(
                    Panel(
                        f"[yellow]⚠️  Security Recommendation[/]\n\n"
                        f"Your AWS access key is [bold]{age_days} days old[/].\n"
                        f"Created: {create_date.strftime('%Y-%m-%d')}\n\n"
                        f"AWS recommends rotating access keys every 90 days.\n\n"
                        f"To rotate:\n"
                        f"  1. Create new key: [cyan]aws iam create-access-key --user-name {user_name}[/]\n"
                        f"  2. Update ~/.aws/credentials\n"
                        f"  3. Delete old key: [cyan]aws iam delete-access-key --access-key-id {key['AccessKeyId']}[/]",
                        title="Access Key Rotation Recommended",
                        border_style="yellow",
                    )
                )
            # 🔐 180 天严重警告
            elif age_days > 180:
                console.print(
                    Panel(
                        f"[red]🚨 Security Alert[/]\n\n"
                        f"Your AWS access key is [bold red]{age_days} days old[/]!\n"
                        f"This significantly increases security risk.\n\n"
                        f"Please rotate immediately.",
                        title="Access Key Critically Old",
                        border_style="red",
                    )
                )

    except ClientError as e:
        # 没有权限查询 IAM - 忽略
        logger.debug(f"Could not check access key age: {e}")
    except Exception as e:
        logger.debug(f"Unexpected error checking credential age: {e}")
```

### 努力估算

**修复时间**: 3-4 小时
- 实现凭证年龄检查: 2 小时
- 测试 (模拟不同年龄): 1 小时
- UI/UX 优化: 1 小时

---

## 验证计划 (Verification Plan)

> **状态**: ✅ 阶段 1 和阶段 2 已完成 (2026-01-12)

### 阶段 1: P0 修复 (Week 1) - ✅ 完成

1. **CS001 - 会话令牌过期**
   - [x] 实现凭证过期时间存储 → `SessionManager._credentials_expire_at`
   - [x] 缓存加载时验证凭证未过期 → `is_expiring_soon()`
   - [x] 扫描器中途检查凭证有效性 → `RobustPaginator` + `CREDENTIAL_ERROR_CODES`
   - [x] 测试: 15 分钟临时凭证 + 30 分钟扫描 → MFA 提示刷新
   - [x] 验证: 长扫描中途过期时自动刷新并继续

2. **CS002 - 文件权限验证**
   - [x] 读取缓存时验证权限 → `SecureStorage.read_json(strict=True)`
   - [x] 权限错误时拒绝读取并警告 → `PermissionError` + 修复指令
   - [x] 测试: `chmod 644 credentials.json` → 拒绝加载
   - [x] 验证: 42 个单元测试通过

### 阶段 2: P1 增强 (Week 2) - ✅ 完成

3. **CS003 - 凭证轮换提醒**
   - [x] 实现凭证年龄检查 → `CredentialChecker._check_access_key_age()`
   - [x] 90 天警告，180 天严重警告 → Rich Panel 显示
   - [x] 测试: 模拟老化凭证 → `test_warns_on_old_key`
   - [x] 验证: 用户收到轮换建议

### 阶段 3: 审计和监控 (Week 3) - 待实现

4. **凭证使用审计**
   - [ ] 记录凭证使用事件 (可选，Trust Center 功能)
   - [ ] 检测异常使用模式
   - [ ] 生成凭证使用报告

### 测试矩阵

| 测试场景 | 预期结果 | 验证方法 |
|---------|---------|---------|
| 使用 15 分钟临时凭证扫描 30 分钟 | 过期时优雅失败并提醒 | `replimap scan` |
| 修改缓存文件权限为 644 | 拒绝加载并显示错误 | `chmod 644 ~/.replimap/cache/credentials.json; replimap scan` |
| 使用 120 天老化凭证 | 显示轮换警告 | Mock IAM response |
| 并发扫描 (2 进程) | 文件锁防止竞态 | 并发测试脚本 |

---

## 参考资料 (References)

### 相关文件
- [replimap/cli/utils/aws_session.py](../../replimap/cli/utils/aws_session.py) - AWS 会话管理
- [~/.replimap/cache/credentials.json](#) - 凭证缓存文件
- [~/.aws/credentials](#) - AWS 标准凭证文件

### 安全最佳实践
- [AWS Security Best Practices - IAM](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [OWASP Credential Management](https://cheatsheetseries.owasp.org/cheatsheets/Credential_Storage_Cheat_Sheet.html)
- [CIS AWS Foundations Benchmark](https://www.cisecurity.org/benchmark/amazon_web_services)

### boto3 文档
- [Credentials](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/credentials.html)
- [RefreshableCredentials](https://botocore.amazonaws.com/v1/documentation/api/latest/reference/credentials.html)

---

## 结论

> **更新 (2026-01-12)**: 所有 P0/P1 问题已修复。

RepliMap 的凭证处理已升级为 **Sovereign Grade** 安全等级:

**已完成修复**:
- ✅ **CS001**: SessionManager 实现凭证过期自动刷新 + MFA 重认证
- ✅ **CS002**: SecureStorage 实现原子写入 + 严格权限验证
- ✅ **CS003**: CredentialChecker 实现 90/180 天凭证老化警告

**新增组件**:
- `replimap/core/security/storage.py` - 305 行
- `replimap/core/security/session_manager.py` - 572 行
- `replimap/core/security/credential_checker.py` - 324 行
- `tests/test_credential_security.py` - 575 行 (42 个测试)

**待实现** (P2 - Trust Center):
- 审计日志、异常检测

**实际修复时间**: ~8 小时
**测试覆盖**: 42 个测试用例，100% 通过
