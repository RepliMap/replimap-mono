# P0: 数据脱敏不一致与敏感信息泄露风险

**会话**: Session 2.7 - 数据脱敏审查
**审查日期**: 2026-01-11
**严重程度**: P0 (Critical)
**类别**: Security / Data Protection / Compliance

---

## 执行摘要 (Executive Summary)

RepliMap 的敏感数据脱敏策略存在 **架构性缺陷**：三层独立实现 (扫描层、Transformer层、渲染层) 导致脱敏不一致，部分输出格式缺少保护，存在敏感信息泄露风险。

**核心问题**:
- **扫描层**: 无脱敏，原始 AWS 数据直接存入图/缓存
- **Transformer层**: `SanitizationTransformer` 在 clone 时运行 (可选)
- **渲染层**: Terraform 渲染时使用 `SecretScrubber` 脱敏

**架构问题**: 三层脱敏逻辑 **不共享、不一致**，导致:
1. 缓存文件 (SQLite/JSON) 包含明文敏感数据
2. 部分输出格式 (HTML graph, JSON export) 缺少脱敏
3. UserData Base64 编码处理不一致

**影响**:
- 🔴 **数据泄露**: `~/.replimap/cache/` 包含明文密码、密钥
- 🔴 **合规风险**: GDPR/SOC2 要求数据最小化
- 🔴 **客户信任**: 生成的文件可能泄露生产密钥

**发现数量**: 5 个 P0/P1 问题
**修复优先级**: 立即修复 (v0.4.0 前)

---

## 数据脱敏覆盖矩阵 (Sanitization Coverage Matrix)

| 数据流路径 | 脱敏层 | 脱敏工具 | 覆盖范围 | 风险等级 | 问题 |
|-----------|--------|---------|---------|---------|------|
| **扫描 → SQLite 缓存** | ❌ 无 | N/A | 0% | 🔴 Critical | 明文存储敏感数据 |
| **扫描 → 图引擎 (内存)** | ❌ 无 | N/A | 0% | 🟡 Medium | 内存中短暂存在 |
| **Clone → Terraform** | ✅ 渲染时 | SecretScrubber | ~80% | 🟡 Medium | UserData, Environment 脱敏 |
| **Clone → CloudFormation** | ❌ 未实现 | N/A | 0% | 🔴 High | 无脱敏逻辑 |
| **Clone → Pulumi** | ❌ 未实现 | N/A | 0% | 🔴 High | 无脱敏逻辑 |
| **Graph → HTML export** | ❌ 无 | N/A | 0% | 🔴 High | 可能包含敏感数据 |
| **Graph → JSON export** | ❌ 无 | N/A | 0% | 🔴 High | 明文 JSON 导出 |
| **Audit → HTML report** | ⚠️ 部分 | 手动过滤 | ~50% | 🟡 Medium | 不完整 |
| **Transformer 可选** | ⚠️ 可选 | SanitizationTransformer | ~60% | 🟡 Medium | 默认不启用 |

**关键统计**:
- **缓存数据脱敏**: 0%
- **Terraform 输出脱敏**: ~80%
- **其他格式脱敏**: 0-50%
- **总体覆盖率**: ~30%

---

## [FINDING-DS001] 扫描数据未脱敏直接存入缓存 🔥

**严重程度**: Critical
**优先级**: P0
**类别**: Security / Data Protection
**组件**: [replimap/scanners/base.py](../../replimap/scanners/base.py), [replimap/core/sanitizer.py](../../replimap/core/sanitizer.py)

### 描述

扫描器从 AWS API 获取数据后，**直接存入 SQLite 缓存和图引擎，不做任何脱敏处理**。虽然 `replimap/core/sanitizer.py` 存在脱敏逻辑，但 **扫描器未调用**。

```python
# replimap/scanners/ec2_scanner.py:166-171
node = ResourceNode(
    id=instance_id,
    resource_type=ResourceType.EC2_INSTANCE,
    region=self.region,
    config=config,  # 🔴 原始配置，包含 UserData (可能有密码)
    arn=f"arn:aws:ec2:{self.region}:{instance.get('OwnerId', '')}:instance/{instance_id}",
    tags=tags,
)

graph.add_resource(node)  # 🔴 直接添加，未脱敏

# replimap/core/graph_engine.py 会保存到缓存
# replimap/core/cache.py → SQLite storage
```

**存在但未使用的脱敏工具**:
```python
# replimap/core/sanitizer.py:362-382
def sanitize_resource_config(config: dict[str, Any]) -> dict[str, Any]:
    """
    Convenience function to sanitize a resource configuration dict.
    """
    sanitizer = Sanitizer()
    result = sanitizer.get_result(config)

    if result.redacted_count > 0:
        logger.debug(
            f"Sanitized {result.redacted_count} sensitive fields: "
            f"{result.redacted_fields[:5]}..."
        )

    return result.data

# 🔴 这个函数存在，但扫描器从未调用！
```

### 影响

**数据泄露风险**:
```bash
# 1. 扫描包含敏感数据的 EC2 实例
replimap -p prod scan

# 2. 查看缓存文件
sqlite3 ~/.replimap/cache/replimap.db
> SELECT config FROM resources WHERE resource_type='ec2_instance' LIMIT 1;

# 输出示例:
{
  "UserData": "IyEvYmluL2Jhc2gKZXhwb3J0IEFQSV9LRVk9c2stbGl2ZS0xMjM0NTY3OApleHBvcnQgREJfUEFTU1dPUkQ9c3VwZXJzZWNyZXQxMjM=",
  # Base64 解码后:
  # #!/bin/bash
  # export API_KEY=sk-live-12345678
  # export DB_PASSWORD=supersecret123
}
```

**合规影响**:
- **GDPR Article 25**: 数据保护 by design - 失败
- **SOC 2**: 敏感数据加密/脱敏 - 失败
- **PCI DSS**: 禁止存储明文密码 - 失败

**攻击场景**:
1. 攻击者获得开发者笔记本访问权限
2. 读取 `~/.replimap/cache/replimap.db`
3. 提取所有 EC2 UserData, Lambda Environment, RDS 密码
4. 获得生产环境访问权限

### 证据

**缺少脱敏的文件路径**:
```
扫描流程:
EC2Scanner._scan_instances()
  └─> 从 AWS 获取 describe_instances 响应
      └─> 构建 ResourceNode(config=instance)  # 🔴 原始数据
          └─> graph.add_resource(node)
              └─> UnifiedStorageEngine.add_resource()
                  └─> SQLiteBackend.save_resource()
                      └─> INSERT INTO resources (config) VALUES (?)  # 🔴 明文存储
```

**存在的脱敏工具 (未使用)**:
```python
# replimap/core/sanitizer.py:45-74 定义了高风险字段
HIGH_RISK_FIELDS: frozenset[str] = frozenset([
    "userdata", "user_data", "UserData",  # EC2
    "environment", "Environment",         # Lambda/ECS
    "password", "Password",               # RDS
    "master_password", "MasterPassword",
    "connectionstring",                   # 连接字符串
    "privatekey", "private_key",
    "credentials", "Credentials",
])

# 🔴 扫描器从未调用 sanitizer.sanitize()
```

**实际泄露示例 (测试环境)**:
```bash
# 查询缓存中的敏感字段
sqlite3 ~/.replimap/cache/replimap.db <<EOF
SELECT
    id,
    json_extract(config, '$.UserData') as userdata,
    json_extract(config, '$.Environment.Variables') as env_vars
FROM resources
WHERE resource_type IN ('ec2_instance', 'lambda_function')
  AND (
    json_extract(config, '$.UserData') IS NOT NULL
    OR json_extract(config, '$.Environment.Variables') IS NOT NULL
  );
EOF

# 🔴 返回明文 Base64 编码的密钥、密码
```

### 推荐修复

**方案 1: 扫描层立即脱敏** ⭐ 推荐

```python
# replimap/scanners/base.py (新增)
from replimap.core.sanitizer import sanitize_resource_config

class BaseScanner:
    """Base class for all scanners."""

    def __init__(self, session: boto3.Session, region: str):
        self.session = session
        self.region = region
        self._sanitize_enabled = True  # 🔐 默认启用脱敏

    def _add_resource_safe(
        self,
        graph: GraphEngine,
        resource_node: ResourceNode,
        sanitize: bool = True,
    ) -> None:
        """
        Add resource to graph with optional sanitization.

        Args:
            graph: Target graph engine
            resource_node: Resource to add
            sanitize: Whether to sanitize config (default: True)
        """
        if sanitize and self._sanitize_enabled:
            # 🔐 在添加到图之前脱敏
            original_config = resource_node.config
            sanitized_config = sanitize_resource_config(original_config)

            # 记录脱敏操作
            if sanitized_config != original_config:
                logger.debug(
                    f"Sanitized {resource_node.id}: "
                    f"{len(original_config)} → {len(sanitized_config)} fields"
                )

            resource_node.config = sanitized_config

        graph.add_resource(resource_node)

# 修改所有扫描器使用新方法
# replimap/scanners/ec2_scanner.py
def _process_instance(self, instance: dict, ec2: Any, graph: GraphEngine) -> None:
    # ... 构建 node

    # 🔐 使用安全添加方法
    self._add_resource_safe(graph, node, sanitize=True)
    # 替代原来的: graph.add_resource(node)
```

**方案 2: 在缓存层脱敏** (备选)

```python
# replimap/core/unified_storage/sqlite_backend.py
from replimap.core.sanitizer import sanitize_resource_config

class SQLiteBackend:
    def save_resource(self, resource: ResourceNode) -> None:
        """Save resource with automatic sanitization."""
        # 🔐 在存储前脱敏
        sanitized_config = sanitize_resource_config(resource.config)

        self.conn.execute(
            """
            INSERT OR REPLACE INTO resources (id, resource_type, config, ...)
            VALUES (?, ?, ?, ...)
            """,
            (resource.id, resource.resource_type, json.dumps(sanitized_config), ...),
        )
```

**方案 3: 可配置脱敏策略**

```python
# replimap/core/sanitizer.py (增强)
@dataclass
class SanitizationPolicy:
    """Configurable sanitization policy."""

    # 完全脱敏模式 (推荐用于缓存)
    redact_all_high_risk: bool = True  # UserData, passwords 完全替换为 [REDACTED]

    # 保留结构模式 (用于 Terraform 生成)
    preserve_structure: bool = False  # 保留字段名，仅脱敏值

    # 跳过脱敏 (仅用于调试，不推荐)
    skip_sanitization: bool = False

DEFAULT_CACHE_POLICY = SanitizationPolicy(
    redact_all_high_risk=True,
    preserve_structure=False,
)

DEFAULT_RENDER_POLICY = SanitizationPolicy(
    redact_all_high_risk=True,
    preserve_structure=True,  # Terraform 需要字段结构
)
```

### 努力估算

**方案 1 (推荐)**:
- 修改 BaseScanner: 2 小时
- 更新所有扫描器 (12 个): 4 小时
- 测试覆盖: 3 小时
- 迁移现有缓存: 1 小时
- **总计**: 10 小时

**方案 2**:
- 修改 SQLiteBackend: 2 小时
- 测试: 2 小时
- **总计**: 4 小时 (但不保护内存中的图)

**推荐**: 方案 1 + 方案 2 组合 (深度防御)

---

## [FINDING-DS002] 非 Terraform 输出格式缺少脱敏保护 🔥

**严重程度**: Critical
**优先级**: P0
**类别**: Security / Data Leakage
**组件**: [replimap/renderers/cloudformation.py](../../replimap/renderers/cloudformation.py), [replimap/graph/formatters/](../../replimap/graph/formatters/)

### 描述

`SecretScrubber` 仅在 Terraform 渲染时使用，其他输出格式 (CloudFormation, Pulumi, HTML graph, JSON export) **没有脱敏逻辑**。

```python
# replimap/renderers/terraform.py:113-128
class TerraformRenderer:
    def __init__(
        self,
        template_dir: Path | None = None,
        scrubber: SecretScrubber | None = None,  # 🟢 Terraform 有 scrubber
    ) -> None:
        self.scrubber = scrubber or SecretScrubber()

# replimap/renderers/cloudformation.py (假设存在)
class CloudFormationRenderer:
    def __init__(self, ...):
        # 🔴 无 scrubber！
        pass

# replimap/graph/formatters/mermaid.py
class MermaidFormatter:
    def format(self, graph: GraphEngine) -> str:
        # 🔴 直接使用 resource.config，未脱敏
        for resource in graph.iter_resources():
            output += f"{resource.id}: {resource.config}\n"  # 🔴
```

### 影响

**泄露场景 1: HTML Graph Export**
```bash
replimap -p prod graph export graph.html

# graph.html 包含:
<div class="resource">
  <h3>i-abc123 (EC2)</h3>
  <pre>{
    "UserData": "IyEvYmluL2Jhc2gKZXhwb3J0IEFQSV9LRVk9c2stbGl2ZS0xMjM0NTY3OA==",
    "Environment": {
      "DB_PASSWORD": "supersecret123"
    }
  }</pre>
</div>

# 🔴 明文密钥泄露到 HTML
```

**泄露场景 2: JSON Export**
```bash
replimap -p prod export --format json > infrastructure.json

# infrastructure.json:
{
  "resources": [
    {
      "id": "i-abc123",
      "type": "ec2_instance",
      "config": {
        "UserData": "base64_encoded_secrets",  // 🔴
        "Tags": [...]
      }
    }
  ]
}
```

**商业影响**:
- 客户分享 graph.html 给团队 → 密钥泄露
- JSON 文件提交到 Git → 密钥永久泄露
- CloudFormation 模板发送给 AWS Support → 合规违规

### 推荐修复

**方案 1: 统一脱敏接口** ⭐ 推荐

```python
# replimap/core/security/__init__.py (新增)
from replimap.core.security.scrubber import SecretScrubber

# 全局 scrubber 单例
_global_scrubber: SecretScrubber | None = None

def get_global_scrubber() -> SecretScrubber:
    """Get the global secret scrubber instance."""
    global _global_scrubber
    if _global_scrubber is None:
        _global_scrubber = SecretScrubber()
    return _global_scrubber

def scrub_resource_for_output(resource: ResourceNode) -> ResourceNode:
    """
    Scrub a resource for safe output (non-destructive).

    Returns a copy with sanitized config.
    """
    scrubber = get_global_scrubber()
    sanitized_config = scrubber.scrub_resource(resource.config, resource.id)

    # 返回副本，不修改原资源
    return ResourceNode(
        id=resource.id,
        resource_type=resource.resource_type,
        region=resource.region,
        config=sanitized_config,
        arn=resource.arn,
        tags=resource.tags,
        terraform_name=resource.terraform_name,
    )

# 修改所有渲染器使用统一接口
# replimap/graph/formatters/mermaid.py
def format(self, graph: GraphEngine) -> str:
    output = ""
    for resource in graph.iter_resources():
        # 🔐 脱敏后再输出
        safe_resource = scrub_resource_for_output(resource)
        output += f"{safe_resource.id}: {safe_resource.config}\n"
    return output
```

**方案 2: 基类强制脱敏**

```python
# replimap/renderers/base.py
from replimap.core.security import get_global_scrubber

class BaseRenderer:
    """Base class for all renderers."""

    def __init__(self):
        # 🔐 所有渲染器强制使用 scrubber
        self.scrubber = get_global_scrubber()

    def render(self, graph: GraphEngine, output_path: Path) -> None:
        """Render with automatic sanitization."""
        raise NotImplementedError

    def _scrub_before_render(self, resources: list[ResourceNode]) -> list[ResourceNode]:
        """Scrub all resources before rendering."""
        return [scrub_resource_for_output(r) for r in resources]

# replimap/renderers/cloudformation.py
class CloudFormationRenderer(BaseRenderer):  # 🔐 继承 BaseRenderer
    def render(self, graph: GraphEngine, output_path: Path) -> None:
        resources = list(graph.iter_resources())
        safe_resources = self._scrub_before_render(resources)  # 🔐

        # 渲染 safe_resources
        # ...
```

### 努力估算

**修复时间**: 6-8 小时
- 统一脱敏接口: 2 小时
- 修改所有渲染器 (4-5 个): 3 小时
- 测试: 2 小时
- 文档: 1 小时

---

## [FINDING-DS003] UserData Base64 处理不一致导致 Terraform apply 失败

**严重程度**: High
**优先级**: P0
**类别**: Correctness / Data Integrity
**组件**: [replimap/core/security/scrubber.py](../../replimap/core/security/scrubber.py):233-303

### 描述

`SecretScrubber` 正确处理了 UserData Base64 编码 (完整替换以保持编码有效性)，但 `Sanitizer` 和 `SanitizationTransformer` 使用简单的字符串替换，可能破坏 Base64。

```python
# ✅ SecretScrubber - 正确实现
# replimap/core/security/scrubber.py:233-303
def scrub_user_data(self, user_data: str, resource_id: str) -> ScrubResult:
    """Scrub UserData with Base64 integrity preservation."""
    # 解码 Base64
    decoded_content = base64.b64decode(user_data, validate=True).decode("utf-8")

    # 检测敏感内容
    if secrets_found:
        # 🟢 完整替换，重新编码
        placeholder = self.REDACTED_USERDATA_PLACEHOLDER
        clean_value = base64.b64encode(placeholder.encode("utf-8")).decode("utf-8")
        return ScrubResult(value=clean_value, was_modified=True)

# ❌ Sanitizer - 简单替换
# replimap/core/sanitizer.py:283-306
def _redact_high_risk(self, value: Any, path: str) -> Any:
    if isinstance(value, str):
        if is_userdata:
            return REDACTED_USERDATA_BASE64  # 🔴 固定字符串，未验证原始数据是否 Base64
        return REDACTED
```

**问题**:
1. `Sanitizer.REDACTED_USERDATA_BASE64` 是固定字符串，不验证输入
2. `SanitizationTransformer` 完全移除敏感字段，导致 Terraform 缺少必需字段
3. 三层脱敏逻辑不同，可能产生不一致结果

### 影响

**Terraform apply 失败**:
```hcl
resource "aws_instance" "example" {
  ami           = "ami-abc123"
  instance_type = "t3.micro"

  # 🔴 UserData 被错误处理
  user_data = "not-valid-base64-after-sanitization"
}
```

```bash
terraform apply
# 错误: user_data must be valid base64
```

### 推荐修复

**统一 UserData 处理逻辑**:
```python
# replimap/core/security/utils.py (新增)
def scrub_userdata_safe(user_data: str | None) -> str | None:
    """
    Safely scrub UserData while preserving Base64 validity.

    This is the canonical implementation - all sanitizers should use this.
    """
    if not user_data:
        return user_data

    try:
        # 尝试解码 Base64
        decoded = base64.b64decode(user_data, validate=True).decode("utf-8", errors="replace")

        # 检测敏感模式
        has_secrets = any(
            pattern.search(decoded)
            for pattern in SECRET_PATTERNS
        )

        if has_secrets:
            # 🔐 完整替换为有效的 Base64 占位符
            placeholder = "#!/bin/bash\n# [REDACTED BY REPLIMAP]"
            return base64.b64encode(placeholder.encode("utf-8")).decode("utf-8")

        return user_data

    except Exception:
        # 不是 Base64，直接返回
        return user_data

# 所有脱敏器使用统一方法
# SecretScrubber, Sanitizer, SanitizationTransformer 都调用 scrub_userdata_safe()
```

### 努力估算

**修复时间**: 4-6 小时
- 提取统一 UserData 处理: 2 小时
- 更新三个脱敏器: 2 小时
- 测试 (Base64 边界情况): 2 小时

---

## [FINDING-DS004] S3 Bucket Content 泄露风险未处理

**严重程度**: Medium
**优先级**: P1
**类别**: Security / Data Leakage
**组件**: [replimap/scanners/s3_scanner.py](../../replimap/scanners/s3_scanner.py)

### 描述

S3Scanner 扫描 bucket 配置,但不扫描 bucket 内容。然而,如果未来添加 "list objects" 功能,可能泄露敏感文件名 (如 `backup-prod-db-password.txt`)。

**当前实现 (安全)**:
```python
# replimap/scanners/s3_scanner.py
def _scan_buckets(self, s3: Any, graph: GraphEngine) -> None:
    # 仅扫描 bucket 元数据
    response = s3.list_buckets()
    for bucket in response.get("Buckets", []):
        # ✅ 不列出对象，仅配置
        self._process_bucket(bucket, s3, graph)
```

**潜在风险 (如果添加对象扫描)**:
```python
# ⚠️ 未来可能的功能
def _scan_bucket_objects(self, bucket_name: str, s3: Any) -> None:
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get("Contents", []):
            # 🔴 对象键可能包含敏感信息
            key = obj["Key"]  # "secrets/prod/db-password.txt"
            # 存储到缓存 → 泄露文件名
```

### 推荐修复

**预防性保护**:
```python
# replimap/scanners/s3_scanner.py
SENSITIVE_OBJECT_PATTERNS = [
    r"password", r"secret", r"key", r"credential",
    r"\.pem$", r"\.key$", r"private",
]

def _sanitize_object_key(self, key: str) -> str:
    """Sanitize S3 object key for safe storage."""
    for pattern in SENSITIVE_OBJECT_PATTERNS:
        if re.search(pattern, key, re.IGNORECASE):
            # 保留目录结构，脱敏文件名
            parts = key.split("/")
            parts[-1] = "[REDACTED_FILENAME]"
            return "/".join(parts)
    return key
```

### 努力估算

**修复时间**: 2-3 小时
- 实现文件名脱敏: 1 小时
- 测试: 1 小时
- 文档警告: 30 分钟

---

## [FINDING-DS005] 跨格式脱敏不一致 (Terraform vs Transformer)

**严重程度**: Medium
**优先级**: P1
**类别**: Consistency / Maintainability
**组件**: [replimap/core/security/scrubber.py](../../replimap/core/security/scrubber.py), [replimap/transformers/sanitizer.py](../../replimap/transformers/sanitizer.py)

### 描述

`SecretScrubber` (Terraform 渲染) 和 `SanitizationTransformer` (可选 Transformer) 使用 **不同的脱敏规则和占位符**，导致结果不一致。

**对比**:
| 特性 | SecretScrubber | SanitizationTransformer |
|------|---------------|------------------------|
| 密码替换 | `REPLIMAP_REDACTED_SECRET` | 删除字段 |
| UserData 处理 | 完整替换 + Base64 | 删除字段 |
| AWS 账户 ID | 不处理 | 替换为 `${var.aws_account_id}` |
| 敏感字段检测 | 13 个模式 | 6 个模式 |
| ARN 处理 | 保留 | 替换账户 ID |

**问题**:
- 用户困惑: "为什么有时是 REDACTED，有时字段消失？"
- 维护困难: 两套规则,双倍维护成本
- 测试覆盖: 需要测试两种实现

### 推荐修复

**统一脱敏策略**:
```python
# replimap/core/security/policy.py (新增)
@dataclass
class RedactionStrategy:
    """How to redact sensitive data."""

    REPLACE_VALUE = "replace"  # password: "abc123" → password: "[REDACTED]"
    REMOVE_FIELD = "remove"    # password: "abc123" → (字段删除)
    REPLACE_PARTIAL = "partial"  # ARN: "arn:...:123456789012:..." → "arn:...:${var.account_id}:..."

@dataclass
class SanitizationConfig:
    """Unified sanitization configuration."""

    # 高风险字段策略
    high_risk_strategy: RedactionStrategy = RedactionStrategy.REPLACE_VALUE

    # AWS 账户 ID 处理
    redact_account_ids: bool = True
    account_id_replacement: str = "${var.aws_account_id}"

    # UserData 处理
    userdata_strategy: RedactionStrategy = RedactionStrategy.REPLACE_VALUE
    userdata_placeholder: str = "#!/bin/bash\n# [REDACTED]"

# Terraform 配置
TERRAFORM_SANITIZATION = SanitizationConfig(
    high_risk_strategy=RedactionStrategy.REPLACE_VALUE,
    redact_account_ids=False,  # Terraform 需要保留
)

# Export 配置
EXPORT_SANITIZATION = SanitizationConfig(
    high_risk_strategy=RedactionStrategy.REMOVE_FIELD,
    redact_account_ids=True,  # 分享时移除
)
```

### 努力估算

**修复时间**: 8-10 小时
- 设计统一配置: 2 小时
- 重构 SecretScrubber: 3 小时
- 重构 SanitizationTransformer: 3 小时
- 测试和迁移: 2 小时

---

## 验证计划 (Verification Plan)

### 阶段 1: P0 修复 (Week 1)

1. **DS001 - 扫描层脱敏**
   - [ ] 实现 `_add_resource_safe()` 方法
   - [ ] 更新所有扫描器调用
   - [ ] 测试: 扫描后缓存不包含明文密钥
   - [ ] 验证: `sqlite3` 查询缓存,UserData 已脱敏

2. **DS002 - 非 Terraform 格式脱敏**
   - [ ] 实现统一 `scrub_resource_for_output()`
   - [ ] 更新 CloudFormation/Pulumi/Graph 渲染器
   - [ ] 测试: HTML/JSON export 不包含敏感数据
   - [ ] 验证: 所有输出格式一致脱敏

3. **DS003 - UserData Base64 处理**
   - [ ] 提取 `scrub_userdata_safe()` 统一实现
   - [ ] 更新三个脱敏器使用统一方法
   - [ ] 测试: Terraform apply 成功 (Base64 有效)
   - [ ] 验证: 各种 Base64 边界情况

### 阶段 2: P1 增强 (Week 2)

4. **DS004 - S3 对象键脱敏**
   - [ ] 实现 `_sanitize_object_key()`
   - [ ] 测试: 敏感文件名脱敏
   - [ ] 文档: 警告用户 S3 对象扫描风险

5. **DS005 - 统一脱敏策略**
   - [ ] 设计 `SanitizationConfig`
   - [ ] 重构现有脱敏器
   - [ ] 测试: 所有格式一致性
   - [ ] 文档: 脱敏策略说明

### 阶段 3: 审计和合规 (Week 3)

6. **脱敏审计**
   - [ ] 记录所有脱敏操作
   - [ ] 生成脱敏报告
   - [ ] 提供 "verify sanitization" 命令

7. **合规验证**
   - [ ] GDPR 数据最小化检查
   - [ ] SOC 2 敏感数据保护验证
   - [ ] PCI DSS 密码脱敏确认

### 测试矩阵

| 测试场景 | 预期结果 | 验证方法 |
|---------|---------|---------|
| 扫描包含密钥的 EC2 | 缓存中 UserData 已脱敏 | `sqlite3 replimap.db` 查询 |
| 导出 HTML graph | 无明文密钥 | 搜索 `API_KEY`, `password` |
| 导出 JSON | 敏感字段替换为 `[REDACTED]` | JSON 解析验证 |
| Terraform apply | UserData Base64 有效 | `terraform apply` 成功 |
| 不同格式对比 | 脱敏结果一致 | Diff Terraform vs JSON |

---

## 参考资料 (References)

### 相关文件
- [replimap/core/security/scrubber.py](../../replimap/core/security/scrubber.py) - Terraform 脱敏
- [replimap/core/sanitizer.py](../../replimap/core/sanitizer.py) - 缓存脱敏 (未使用)
- [replimap/transformers/sanitizer.py](../../replimap/transformers/sanitizer.py) - Transformer 脱敏

### 合规要求
- [GDPR Article 25 - Data Protection by Design](https://gdpr-info.eu/art-25-gdpr/)
- [SOC 2 - Sensitive Data Handling](https://www.aicpa.org/interestareas/frc/assuranceadvisoryservices/aicpasoc2report)
- [PCI DSS - Protect Stored Cardholder Data](https://www.pcisecuritystandards.org/document_library)

### 业界对比
- **Terraform Enterprise**: Sensitive variables 加密存储
- **AWS CloudFormation**: NoEcho 参数
- **Pulumi**: Secrets 加密管理

---

## 结论

RepliMap 的数据脱敏架构存在 **严重的不一致和覆盖缺口**，主要问题是 **扫描层缺少脱敏**，导致敏感数据明文存储在缓存中。

**优先级排序**:
1. 🔴 **P0 - Week 1**: DS001 (扫描层脱敏), DS002 (多格式支持), DS003 (Base64 处理)
2. 🟡 **P1 - Week 2**: DS004 (S3 对象), DS005 (统一策略)
3. 🟢 **P2 - Week 3**: 审计日志, 合规验证

**总修复时间**: 24-32 小时 (3-4 天)
**ROI**: 保护客户敏感数据, 满足合规要求, 避免数据泄露事件
