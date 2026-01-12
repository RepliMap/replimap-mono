# P0: 功能门控安全漏洞

**会话**: Session 3.1 - 功能门控安全性审查
**审查日期**: 2026-01-11
**严重程度**: P0 (Critical)
**类别**: Security / Business Logic / Revenue Protection

---

## 执行摘要 (Executive Summary)

RepliMap 的授权系统存在 **严重的客户端验证绕过漏洞**，允许用户通过简单手段获取 ENTERPRISE 级别功能，直接威胁商业模式和收入。

**核心问题**: 授权验证完全依赖客户端，缺乏服务器端验证、签名校验和防篡改机制。

**影响**:
- 🔴 **收入风险**: 用户可通过环境变量免费获得 $500/月 ENTERPRISE 功能
- 🔴 **商业风险**: 缓存文件可被篡改，绕过所有付费门控
- 🔴 **法律风险**: 缺乏有效的许可证执行机制

**发现数量**: 5 个 P0 问题
**修复优先级**: 立即修复 (v0.4.0 前必须完成)

---

## 功能门控安全矩阵 (Licensing Security Matrix)

| 检查点 | 实现状态 | 绕过难度 | 风险等级 | 影响范围 |
|--------|---------|---------|---------|---------|
| **Dev Mode 检查** | ❌ 环境变量 | 🟢 Trivial (1 line) | 🔴 Critical | 所有 ENTERPRISE 功能 |
| **许可证签名** | ❌ 无签名 | 🟢 Trivial | 🔴 Critical | 任意计划伪造 |
| **缓存文件完整性** | ❌ 明文 JSON | 🟢 Trivial | 🔴 Critical | 本地篡改 |
| **机器指纹验证** | ⚠️ 弱验证 | 🟡 Easy (容器克隆) | 🟡 Medium | 多机使用 |
| **服务器端验证** | ❌ 仅激活时 | 🟡 Easy (离线) | 🔴 High | 长期离线使用 |
| **过期检查** | ✅ 客户端 | 🟡 Easy (系统时钟) | 🟡 Medium | 过期后继续使用 |
| **在线重验证** | ❌ 未实现 | N/A | 🟡 Medium | 7天宽限期 |

**总体安全评分**: ⚠️ D- (10/100)

**关键统计**:
- **无需技术技能绕过**: 3 个方法
- **需基本技能绕过**: 2 个方法
- **有效防护措施**: 0 个

---

## [FINDING-LS001] Dev Mode 环境变量绕过所有授权检查 🔥

**严重程度**: Critical
**优先级**: P0
**类别**: Security / Revenue Protection
**组件**: [replimap/licensing/manager.py](../../replimap/licensing/manager.py):45-55, 103-104

### 描述

设置 `REPLIMAP_DEV_MODE=1` 环境变量可直接获得 ENTERPRISE 计划，绕过所有功能门控和授权检查。

```python
# replimap/licensing/manager.py:45-55
def is_dev_mode() -> bool:
    """
    Check if dev mode is enabled.

    Dev mode bypasses license restrictions for local development and testing.
    Enable with: REPLIMAP_DEV_MODE=1  # 🔴 文档化的绕过方法！
    """
    return os.environ.get("REPLIMAP_DEV_MODE", "").lower() in ("1", "true", "yes")

# replimap/licensing/manager.py:103-104
@property
def current_plan(self) -> Plan:
    if is_dev_mode():
        return Plan.ENTERPRISE  # 🔴 直接返回最高权限
```

**问题**:
1. **环境变量无验证**: 任何用户都可设置环境变量
2. **ENTERPRISE 访问**: 包括价值 $500/月 的功能:
   - 无限 AWS 账户扫描
   - 完整审计报告导出 (PDF/JSON/CSV)
   - Trust Center (审计日志)
   - 区域合规报告 (APRA CPS234, Essential Eight, RBNZ BS11)
   - 优先 Remediate 访问
3. **永久有效**: 无时间限制、无使用统计、无日志记录

### 影响

**收入影响**:
- ENTERPRISE 计划年费: $5,000/年
- FREE → ENTERPRISE 转化率损失: 100%
- 预估年度收入风险: $200K+ (假设 40 个潜在 ENTERPRISE 客户)

**商业影响**:
- 付费客户投诉 ("为什么我要付费？")
- 无法执行许可证合规性
- 影响投资人信心

**技术影响**:
- 功能门控完全失效
- 无法收集使用数据
- 无法追踪 dev mode 滥用

### 证据

**绕过步骤 (10 秒)**:
```bash
# 1. 设置环境变量
export REPLIMAP_DEV_MODE=1

# 2. 运行任何命令，享受 ENTERPRISE 功能
replimap -p prod scan
replimap audit export --format pdf  # 原本需要 ENTERPRISE
replimap trust status              # 原本需要 ENTERPRISE

# 3. 确认计划级别
replimap license status
# 输出: ENTERPRISE plan active  # 🔴 无需付费
```

**代码证据**:
```python
# 所有功能检查都调用这个 property
license_manager.current_plan
  → is_dev_mode() returns True
  → Plan.ENTERPRISE
  → 所有 Feature.* 检查通过 ✅
```

**影响范围**:
```python
# replimap/licensing/models.py:719
Plan.ENTERPRISE: PlanFeatures(
    features=set(Feature),  # 🔴 所有 57 个功能！
)
```

### 推荐修复

**方案 1: 移除 Dev Mode (生产发布)** ⭐ 推荐
```python
# replimap/licensing/manager.py
def is_dev_mode() -> bool:
    """Dev mode only in development builds."""
    # 🔐 仅在明确的开发构建中启用
    if not __debug__:  # Python -O flag
        return False

    # 额外检查：仅在 pytest 环境或明确的开发标记
    import sys
    if "pytest" in sys.modules:
        return True

    # 需要特殊的开发密钥，而非简单环境变量
    dev_key = os.environ.get("REPLIMAP_DEV_KEY", "")
    expected_hash = "a7f5c8e9d2b3..."  # 内部开发密钥的哈希
    return hashlib.sha256(dev_key.encode()).hexdigest() == expected_hash
```

**方案 2: Dev Mode 时间限制**
```python
def is_dev_mode() -> bool:
    if not os.environ.get("REPLIMAP_DEV_MODE"):
        return False

    # 🔐 Dev mode 有效期：7天
    dev_mode_start = Path.home() / ".replimap" / ".dev_mode_start"
    if not dev_mode_start.exists():
        dev_mode_start.write_text(datetime.now(UTC).isoformat())

    start_time = datetime.fromisoformat(dev_mode_start.read_text())
    if datetime.now(UTC) - start_time > timedelta(days=7):
        logger.error("Dev mode expired. Contact support for development license.")
        return False

    return True
```

**方案 3: Dev Mode 日志和警告**
```python
def is_dev_mode() -> bool:
    enabled = os.environ.get("REPLIMAP_DEV_MODE", "").lower() in ("1", "true")
    if enabled:
        # 🔐 强制显示警告
        console.print("[bold red]⚠️  DEV MODE ACTIVE - ENTERPRISE FEATURES UNLOCKED[/]")
        console.print("[yellow]This violates license terms if used in production.[/]")

        # 🔐 记录使用情况
        _log_dev_mode_usage()
    return enabled
```

### 努力估算

**修复时间**: 2-4 小时
- 代码修改: 30 分钟
- 测试验证: 1 小时
- 回归测试: 1-2 小时
- 文档更新: 30 分钟

**测试覆盖**:
```python
# tests/test_licensing.py
def test_dev_mode_disabled_in_production():
    """Dev mode should not work in production builds."""
    os.environ["REPLIMAP_DEV_MODE"] = "1"
    assert is_dev_mode() is False  # 在生产构建中

def test_dev_mode_requires_dev_key():
    """Dev mode requires secret dev key."""
    os.environ["REPLIMAP_DEV_MODE"] = "1"
    assert is_dev_mode() is False

    os.environ["REPLIMAP_DEV_KEY"] = "correct_key"
    assert is_dev_mode() is True
```

---

## [FINDING-LS002] 许可证缓存文件可任意篡改 🔥

**严重程度**: Critical
**优先级**: P0
**类别**: Security / Data Integrity
**组件**: [replimap/licensing/manager.py](../../replimap/licensing/manager.py):365-387, ~/.replimap/license.json

### 描述

许可证缓存文件 (`~/.replimap/license.json`) 存储为明文 JSON，无签名、无加密、无完整性校验，可被用户随意修改。

```python
# replimap/licensing/manager.py:365-374
def _cache_license(self, license_obj: License) -> None:
    """Cache the license to disk."""
    cache_data = {
        "license": license_obj.to_dict(),  # 🔴 明文 JSON
        "cached_at": datetime.now(UTC).isoformat(),
        "fingerprint": get_machine_fingerprint(),
    }
    self.cache_path.write_text(json.dumps(cache_data, indent=2))  # 🔴 无签名
```

**问题**:
1. **无签名验证**: 文件内容可被修改，程序无法检测
2. **明文存储**: 所有字段可读可改
3. **无加密**: 许可证详情完全暴露
4. **无完整性校验**: 无 HMAC、无哈希验证

### 影响

**攻击场景**:
1. 用户激活 SOLO ($49/月)
2. 修改缓存文件:
   ```bash
   # ~/.replimap/license.json
   {
     "license": {
       "plan": "enterprise",  # 🔴 改为 ENTERPRISE
       "expires_at": "2030-12-31T23:59:59+00:00",  # 🔴 延长到 2030 年
       "machine_fingerprint": null,  # 🔴 移除机器绑定
       "max_machines": 999  # 🔴 无限机器
     },
     "cached_at": "2026-01-11T10:00:00+00:00",
     "fingerprint": "abc123"
   }
   ```
3. 运行 RepliMap → ENTERPRISE 功能全部可用
4. 7 天宽限期后需重新验证，但可断网使用

**收入影响**:
- SOLO → ENTERPRISE 差价: $451/月 × 12 = $5,412/年
- 50 个 SOLO 用户升级: $270,600/年收入损失

### 证据

**篡改测试**:
```bash
# 1. 正常激活
replimap license activate RM-SOLO-1234-5678-ABCD
# 输出: SOLO plan activated

# 2. 修改缓存
cat ~/.replimap/license.json
# 修改 "plan": "solo" → "plan": "enterprise"

# 3. 验证
replimap license status
# 输出: enterprise plan active  # 🔴 篡改成功！

# 4. 使用 ENTERPRISE 功能
replimap audit export --format csv  # 原本需 ENTERPRISE
# 成功！ 🔴
```

**代码证据**:
```python
# replimap/licensing/manager.py:376-387
def _load_cached_license(self) -> License | None:
    """Load license from cache."""
    if not self.cache_path.exists():
        return None

    try:
        data = json.loads(self.cache_path.read_text())  # 🔴 直接信任文件内容
        self._cached_at = datetime.fromisoformat(data["cached_at"])
        return License.from_dict(data["license"])  # 🔴 无签名验证
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        logger.warning(f"Failed to load cached license: {e}")
        return None
```

### 推荐修复

**方案 1: HMAC 签名验证** ⭐ 推荐
```python
import hmac
import secrets

# 🔐 每个安装生成唯一密钥 (首次运行)
def get_installation_secret() -> bytes:
    secret_path = Path.home() / ".replimap" / ".install_secret"
    if not secret_path.exists():
        secret_path.parent.mkdir(exist_ok=True)
        secret = secrets.token_bytes(32)
        secret_path.write_bytes(secret)
        secret_path.chmod(0o600)
    return secret_path.read_bytes()

def _cache_license(self, license_obj: License) -> None:
    """Cache the license with HMAC signature."""
    cache_data = {
        "license": license_obj.to_dict(),
        "cached_at": datetime.now(UTC).isoformat(),
        "fingerprint": get_machine_fingerprint(),
    }

    # 🔐 计算 HMAC 签名
    secret = get_installation_secret()
    message = json.dumps(cache_data, sort_keys=True).encode()
    signature = hmac.new(secret, message, hashlib.sha256).hexdigest()

    signed_data = {
        "data": cache_data,
        "signature": signature,
    }
    self.cache_path.write_text(json.dumps(signed_data, indent=2))

def _load_cached_license(self) -> License | None:
    """Load and verify cached license."""
    if not self.cache_path.exists():
        return None

    try:
        signed_data = json.loads(self.cache_path.read_text())

        # 🔐 验证签名
        secret = get_installation_secret()
        message = json.dumps(signed_data["data"], sort_keys=True).encode()
        expected_sig = hmac.new(secret, message, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(signed_data["signature"], expected_sig):
            logger.error("License cache signature invalid - file may be tampered")
            return None

        # 签名验证通过，加载数据
        data = signed_data["data"]
        self._cached_at = datetime.fromisoformat(data["cached_at"])
        return License.from_dict(data["license"])
    except Exception as e:
        logger.warning(f"Failed to load cached license: {e}")
        return None
```

**方案 2: 加密缓存 (更高安全性)**
```python
from cryptography.fernet import Fernet

def _cache_license(self, license_obj: License) -> None:
    """Cache encrypted license."""
    key = get_installation_secret()  # 32 bytes
    f = Fernet(base64.urlsafe_b64encode(key))

    cache_data = {...}
    plaintext = json.dumps(cache_data).encode()
    encrypted = f.encrypt(plaintext)

    self.cache_path.write_bytes(encrypted)
```

### 努力估算

**修复时间**: 4-6 小时
- HMAC 实现: 2 小时
- 迁移逻辑 (处理旧缓存): 1 小时
- 测试: 2 小时
- 文档: 1 小时

---

## [FINDING-LS003] 机器指纹验证过弱，容器环境易克隆 🔥

**严重程度**: High
**优先级**: P0
**类别**: Security / Multi-tenancy
**组件**: [replimap/licensing/models.py](../../replimap/licensing/models.py):849-873

### 描述

机器指纹仅基于 `hostname + MAC address`，在容器/虚拟机环境中极易克隆，导致单一许可证可被多台机器使用。

```python
# replimap/licensing/models.py:849-873
def get_machine_fingerprint() -> str:
    """Generate a unique fingerprint for the current machine."""
    components = [
        platform.node(),      # 🔴 Hostname (容器中可随意设置)
        platform.machine(),   # x86_64 (所有机器相同)
        platform.system(),    # Linux (所有机器相同)
    ]

    # Try to get MAC address
    try:
        mac = uuid.getnode()  # 🔴 容器中可克隆
        if mac == uuid.getnode():
            components.append(str(mac))
    except OSError:
        pass

    fingerprint_string = "|".join(components)
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()[:32]
```

**问题**:
1. **容器克隆**: Docker/Kubernetes 中复制镜像 = 相同指纹
2. **虚拟机克隆**: VMware/VirtualBox 克隆 = MAC 地址相同
3. **无硬件绑定**: 不使用 CPU ID、主板序列号等
4. **无云实例验证**: 不检查 AWS/GCP Instance ID

### 影响

**攻击场景**:
```bash
# 1. 在机器 A 激活许可证
replimap license activate RM-SOLO-1234-5678-ABCD

# 2. 复制缓存文件和设置 hostname
docker run -it --hostname machine-a ubuntu
cp ~/.replimap/license.json /container/

# 3. 在机器 B/C/D... 使用相同配置
# 所有机器都有相同的 fingerprint → 验证通过 ✅
```

**收入影响**:
- 1 个 SOLO 许可证 ($49/月) 被 10 台机器共享
- 应收入: $490/月 × 10 = $4,900/月
- 实际收入: $49/月
- **损失**: $4,851/月 = $58,212/年

### 推荐修复

**方案 1: 多因素机器指纹** ⭐ 推荐
```python
def get_machine_fingerprint() -> str:
    """Enhanced machine fingerprint with multiple factors."""
    components = []

    # 1. 基础信息
    components.append(platform.node())
    components.append(platform.machine())

    # 2. 🔐 CPU 信息 (Linux)
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if "Serial" in line or "processor" in line:
                    components.append(line.strip())
                    break
    except Exception:
        pass

    # 3. 🔐 云实例 ID (AWS/GCP/Azure)
    cloud_id = _get_cloud_instance_id()
    if cloud_id:
        components.append(f"cloud:{cloud_id}")

    # 4. 🔐 主板 UUID (Linux)
    try:
        import subprocess
        result = subprocess.run(
            ["cat", "/sys/class/dmi/id/product_uuid"],
            capture_output=True, text=True, timeout=1
        )
        if result.returncode == 0:
            components.append(f"uuid:{result.stdout.strip()}")
    except Exception:
        pass

    # 5. MAC 地址 (保留)
    try:
        mac = uuid.getnode()
        if mac != uuid.getnode():  # 不稳定则跳过
            pass
        else:
            components.append(f"mac:{mac}")
    except Exception:
        pass

    if len(components) < 3:
        logger.warning("Weak machine fingerprint - only %d components", len(components))

    fingerprint_string = "|".join(sorted(components))
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()[:32]

def _get_cloud_instance_id() -> str | None:
    """Get cloud instance ID if running in cloud."""
    # AWS
    try:
        resp = httpx.get(
            "http://169.254.169.254/latest/meta-data/instance-id",
            timeout=0.5
        )
        if resp.status_code == 200:
            return f"aws:{resp.text}"
    except Exception:
        pass

    # GCP
    try:
        resp = httpx.get(
            "http://metadata.google.internal/computeMetadata/v1/instance/id",
            headers={"Metadata-Flavor": "Google"},
            timeout=0.5
        )
        if resp.status_code == 200:
            return f"gcp:{resp.text}"
    except Exception:
        pass

    return None
```

### 努力估算

**修复时间**: 6-8 小时
- 增强指纹逻辑: 3 小时
- 跨平台测试 (Linux/macOS/Windows): 3 小时
- 迁移旧指纹: 1 小时
- 文档: 1 小时

---

## [FINDING-LS004] 无服务器端许可证验证，长期离线使用

**严重程度**: High
**优先级**: P0
**类别**: Security / Revenue Protection
**组件**: [replimap/licensing/manager.py](../../replimap/licensing/manager.py):356-363, 399-404

### 描述

在线重验证逻辑未实现，用户激活后可离线使用 7 天宽限期，之后仍可通过断网继续使用。

```python
# replimap/licensing/manager.py:356-363
def _revalidate_online(self) -> None:
    """Revalidate the current license with the API."""
    if self._current_license is None:
        return

    # TODO: Implement actual API revalidation  # 🔴 未实现！
    logger.debug("Revalidation would happen here")
    self._cached_at = datetime.now(UTC)  # 🔴 直接重置缓存时间
```

**问题**:
1. **重验证未实现**: 只是 debug 日志，无实际 API 调用
2. **宽限期绕过**: 7 天后断网 → 验证失败 → 继续使用缓存
3. **吊销无效**: 服务器端吊销许可证，客户端无法感知

### 影响

**攻击场景**:
```bash
# 1. 激活许可证
replimap license activate RM-SOLO-1234-ABCD

# 2. 24 小时后需要重验证，但...
# - 断网或防火墙阻止 API 访问
# - 重验证失败，但进入 7 天宽限期

# 3. 7 天宽限期后
# - 仍然断网
# - 验证再次失败，但缓存仍然有效
# - 继续使用 SOLO 功能 ✅
```

### 推荐修复

```python
def _revalidate_online(self) -> None:
    """Revalidate the current license with the API."""
    if self._current_license is None:
        return

    try:
        # 🔐 实际调用 API 重验证
        response = httpx.post(
            f"{self.api_base_url}/license/revalidate",
            json={
                "license_key": self._current_license.license_key,
                "machine_id": get_machine_fingerprint(),
                "cli_version": __version__,
            },
            timeout=API_TIMEOUT,
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("valid"):
                self._cached_at = datetime.now(UTC)
                logger.info("License revalidated successfully")
            else:
                raise LicenseValidationError(data.get("message", "License no longer valid"))
        elif response.status_code == 403:
            # 许可证已吊销
            self.deactivate()
            raise LicenseValidationError("License has been revoked")
        else:
            raise LicenseValidationError(f"Revalidation failed: HTTP {response.status_code}")

    except httpx.RequestError as e:
        logger.warning(f"Network error during revalidation: {e}")
        raise  # 向上传播，触发宽限期检查
```

### 努力估算

**修复时间**: 4-6 小时
- API 调用实现: 2 小时
- 错误处理: 1 小时
- 测试 (在线/离线): 2 小时
- 服务器端 API: 需协调后端团队

---

## [FINDING-LS005] 客户端许可证激活无服务器端签名校验

**严重程度**: High
**优先级**: P1
**类别**: Security / Authentication
**组件**: [replimap/licensing/manager.py](../../replimap/licensing/manager.py):273-350

### 描述

服务器返回的许可证数据没有数字签名，客户端无法验证响应是否来自合法服务器，存在中间人攻击风险。

```python
# replimap/licensing/manager.py:302-323
if response.status_code == 200:
    data = response.json()  # 🔴 直接信任 JSON 响应
    if data.get("valid"):
        return License(
            license_key=license_key.upper(),
            plan=Plan(data.get("plan", "solo").lower()),  # 🔴 无签名验证
            email=data.get("email", ""),
            ...
        )
```

**问题**:
1. **无 JWT 签名**: 响应数据未签名，可被篡改
2. **中间人攻击**: 攻击者可修改 API 响应 (如 Burp Suite)
3. **无 HTTPS 证书固定**: 可被自签名证书劫持

### 推荐修复

```python
# 服务器端返回 JWT 签名
# Response:
{
    "valid": true,
    "token": "eyJhbGciOiJIUzI1NiIs...",  # JWT with license data
    "plan": "solo",
    ...
}

# 客户端验证
import jwt

def _validate_online(self, license_key: str) -> License:
    response = httpx.post(...)

    if response.status_code == 200:
        data = response.json()

        # 🔐 验证 JWT 签名
        try:
            jwt_token = data.get("token")
            decoded = jwt.decode(
                jwt_token,
                PUBLIC_KEY,  # 内置公钥
                algorithms=["RS256"]
            )

            # 验证内容一致性
            if decoded["plan"] != data["plan"]:
                raise LicenseValidationError("Token data mismatch")

            return License(**decoded)
        except jwt.InvalidSignatureError:
            raise LicenseValidationError("Invalid license signature")
```

### 努力估算

**修复时间**: 8-12 小时
- JWT 实现: 4 小时
- 密钥管理: 2 小时
- 服务器端改造: 4 小时
- 测试: 2 小时

---

## 验证计划 (Verification Plan)

### 阶段 1: 紧急修复 (Week 1)

**目标**: 关闭 3 个最高风险漏洞

1. **LS001 - Dev Mode 绕过**
   - [ ] 移除生产环境 dev mode 或使用开发密钥
   - [ ] 添加使用警告和日志
   - [ ] 测试: `REPLIMAP_DEV_MODE=1` 应失败
   - [ ] 验证: 无法通过环境变量获得 ENTERPRISE

2. **LS002 - 缓存篡改**
   - [ ] 实现 HMAC 签名
   - [ ] 迁移现有缓存文件
   - [ ] 测试: 手动修改缓存应导致验证失败
   - [ ] 验证: 篡改后无法加载许可证

3. **LS004 - 在线重验证**
   - [ ] 实现 `_revalidate_online()` API 调用
   - [ ] 测试: 24 小时后自动重验证
   - [ ] 验证: 吊销的许可证被禁用

### 阶段 2: 加固 (Week 2-3)

4. **LS003 - 机器指纹**
   - [ ] 实现多因素指纹
   - [ ] 支持云实例 ID
   - [ ] 测试: 容器克隆产生不同指纹
   - [ ] 验证: 复制缓存到新机器失败

5. **LS005 - JWT 签名**
   - [ ] 后端实现 JWT 签名
   - [ ] 客户端验证逻辑
   - [ ] 测试: 篡改 API 响应失败
   - [ ] 验证: 中间人攻击被检测

### 阶段 3: 监控和响应 (Week 4)

6. **使用监控**
   - [ ] 记录许可证激活/验证事件
   - [ ] 检测异常使用模式
   - [ ] 实现许可证吊销机制

7. **渗透测试**
   - [ ] 雇佣安全研究员测试
   - [ ] Bug Bounty 计划
   - [ ] 定期安全审计

### 测试矩阵

| 测试场景 | 预期结果 | 验证方法 |
|---------|---------|---------|
| 设置 `REPLIMAP_DEV_MODE=1` | 失败 (无 ENTERPRISE) | `replimap license status` |
| 修改 `license.json` plan 字段 | 签名验证失败 | `replimap license status` → 错误 |
| 复制缓存到新机器 | 机器指纹不匹配 | `replimap license status` → 错误 |
| 断网 > 7 天后使用 | 宽限期过期，要求重新激活 | `replimap scan` → 阻止 |
| 篡改 API 响应 (Burp Suite) | JWT 签名验证失败 | 激活失败 |

---

## 参考资料 (References)

### 相关文件
- [replimap/licensing/manager.py](../../replimap/licensing/manager.py) - 授权管理器
- [replimap/licensing/models.py](../../replimap/licensing/models.py) - 计划和功能定义
- [~/.replimap/license.json](#) - 许可证缓存文件

### 安全最佳实践
- [OWASP: Client-side Enforcement](https://owasp.org/www-community/vulnerabilities/Client-Side_Enforcement)
- [JWT Best Practices](https://datatracker.ietf.org/doc/html/rfc8725)
- [License Key Security](https://www.cryptolens.io/docs/licensing-models/license-key-validation)

### 业界对比
- **Terraform Cloud**: JWT + 机器指纹 + 在线验证
- **GitHub CLI**: OAuth tokens + 定期重验证
- **Docker Desktop**: 本地签名 + 定期回调

---

## 结论

授权系统的安全漏洞对 RepliMap 的商业模式构成 **直接威胁**。当前实现允许用户通过简单手段免费获得价值 $500/月 的功能，必须在 **v0.4.0 发布前完全修复**。

**优先级排序**:
1. 🔴 **P0 - Week 1**: LS001 (Dev Mode), LS002 (缓存签名), LS004 (在线重验证)
2. 🟡 **P1 - Week 2**: LS003 (机器指纹), LS005 (JWT 签名)
3. 🟢 **P2 - Week 3**: 监控、日志、渗透测试

**总修复时间**: 24-36 小时 (3-4.5 天)
**ROI**: 保护 $200K+/年 潜在收入
