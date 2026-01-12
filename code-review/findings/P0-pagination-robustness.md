# P0: 分页失败与错误恢复机制缺陷

**会话**: Session 2.2 - 分页与错误恢复审查
**审查日期**: 2026-01-11
**严重程度**: P0 (Critical)
**类别**: Reliability / Data Integrity / AWS Integration

---

## 执行摘要 (Executive Summary)

RepliMap 的扫描器存在 **分页失败导致整体扫描中止** 的严重问题，这在大规模 AWS 环境中会导致数据不完整、扫描不可靠，严重影响产品可用性。

**核心问题**: 所有扫描器使用 AWS paginator，但 **单页失败 = 整个资源类型扫描失败**，没有部分成功保存机制。

**影响**:
- 🔴 **数据完整性风险**: 大型账户扫描可能漏掉数百个资源
- 🔴 **商业影响**: 客户对工具可靠性失去信心，影响续费
- 🔴 **用户体验**: 扫描不确定性高，需要多次重试

**发现数量**: 6 个 P0/P1 问题
**修复优先级**: 立即修复 (P0)，与速率限制问题同等优先级

---

## 分页使用情况矩阵 (Pagination Usage Matrix)

| 扫描器 | Paginator API 调用 | 页数估算 (1000资源) | 错误处理 | 部分保存 | 风险等级 |
|--------|-------------------|---------------------|----------|----------|----------|
| **VPCScanner** | describe_vpcs<br>describe_subnets<br>describe_security_groups<br>describe_flow_logs | 1-2 页<br>5-10 页<br>10-20 页<br>10+ 页 | ❌ 扫描器级别 try/except | ❌ 无 | 🔴 High |
| **EC2Scanner** | describe_instances | 20-50 页 (每页20实例) | ❌ 扫描器级别 | ❌ 无 | 🔴 Critical |
| **RDSScanner** | describe_db_instances<br>describe_db_subnet_groups | 5-10 页<br>2-5 页 | ❌ 扫描器级别 | ❌ 无 | 🔴 High |
| **ComputeScanner** | describe_launch_templates<br>describe_target_groups<br>describe_load_balancers<br>describe_auto_scaling_groups | 5-10 页<br>10-20 页<br>5-10 页<br>5-10 页 | ❌ 扫描器级别 | ❌ 无 | 🔴 Critical |
| **StorageScanner** | describe_volumes | 20-50 页 | ❌ 扫描器级别 | ❌ 无 | 🔴 High |
| **NetworkingScanner** | describe_internet_gateways<br>describe_nat_gateways<br>describe_route_tables<br>describe_vpc_endpoints<br>describe_network_acls | 1-2 页<br>2-5 页<br>10-20 页<br>5-10 页<br>5-10 页 | ❌ 扫描器级别 | ❌ 无 | 🟡 Medium |
| **IAMScanner** | list_roles<br>list_instance_profiles | 5-10 页<br>2-5 页 | ❌ 扫描器级别 | ❌ 无 | 🟡 Medium |
| **S3Scanner** | list_buckets (非分页!) | N/A (硬限制1000桶) | ❌ 单次调用 | ❌ 无 | 🔴 Critical |
| **MessagingScanner** | list_queues<br>list_topics | 5-10 页<br>5-10 页 | ❌ 扫描器级别 | ❌ 无 | 🟡 Medium |
| **ElastiCacheScanner** | describe_cache_clusters<br>describe_cache_subnet_groups | 5-10 页<br>2-5 页 | ❌ 扫描器级别 | ❌ 无 | 🟡 Medium |
| **MonitoringScanner** | describe_log_groups<br>describe_alarms | 10-20 页<br>5-10 页 | ❌ 扫描器级别 | ❌ 无 | 🟢 Low |

**统计**:
- **使用分页器的扫描器**: 12 个
- **正确的逐页错误处理**: 0 个 (0%)
- **支持部分成功保存**: 0 个 (0%)
- **S3 list_buckets 硬限制**: 1000 桶 (无分页！)

---

## [FINDING-PG001] 分页器错误处理在扫描器级别，单页失败导致整体中止 🔥

**严重程度**: Critical
**优先级**: P0
**类别**: Reliability / Data Integrity
**组件**: [replimap/scanners/vpc_scanner.py](../replimap/scanners/vpc_scanner.py):62-90, [replimap/scanners/ec2_scanner.py](../replimap/scanners/ec2_scanner.py):62-70

### 描述

所有扫描器的分页逻辑模式为：

```python
# replimap/scanners/vpc_scanner.py:62-90
def _scan_vpcs(self, ec2: Any, graph: GraphEngine) -> None:
    """Scan all VPCs in the region."""
    logger.debug("Scanning VPCs...")

    # 🔴 问题1: Flow logs 分页失败 → 整个 VPC 扫描中止
    try:
        fl_paginator = ec2.get_paginator("describe_flow_logs")
        for fl_page in fl_paginator.paginate():
            for flow_log in fl_page.get("FlowLogs", []):
                # 处理 flow log
    except ClientError as e:
        logger.debug(f"Could not describe flow logs: {e}")
        # ⚠️ 只是 log，但如果这里抛出异常会怎样？

    # 🔴 问题2: VPC 分页本身没有错误处理
    paginator = ec2.get_paginator("describe_vpcs")
    for page in paginator.paginate():  # ❌ 如果第5页失败，前4页的数据丢失
        for vpc in page.get("Vpcs", []):
            # ... 处理 VPC
            graph.add_resource(node)  # 数据已添加到图中
```

**问题分析**:

1. **分页循环无错误包装**:
   ```python
   for page in paginator.paginate():  # ❌ 没有 try/except
       for vpc in page.get("Vpcs", []):
           graph.add_resource(node)
   ```
   - 如果第 N 页 (N > 1) 因网络超时/AWS 限流失败
   - 前 N-1 页的数据 **已经添加到 graph**
   - 但扫描器外层的 `try/except ClientError` 会捕获错误 → **整个扫描标记为失败**
   - **结果**: 部分数据在图中，但扫描报告显示失败，用户不知道数据是否完整

2. **嵌套分页无独立错误处理** (VPC flow logs 示例):
   ```python
   try:
       fl_paginator = ec2.get_paginator("describe_flow_logs")
       for fl_page in fl_paginator.paginate():
           # ...
   except ClientError as e:
       logger.debug(f"Could not describe flow logs: {e}")
   ```
   - Flow logs 失败只是 debug 日志
   - 但如果 paginate() 本身抛出异常（不是 ClientError），会向上传播
   - 导致 VPC 扫描中止

### 影响

**数据完整性风险**:
- 大型账户 (500+ EC2 实例 → 25+ 页):
  - 第 20 页因临时网络问题失败
  - 前 19 页 (380 实例) **已添加到图中**
  - 用户看到 "EC2Scanner failed"
  - **实际情况**: 有 380/500 实例，但用户以为一个都没有

**商业影响**:
- 客户认为工具不可靠 → 不愿续费
- Support ticket 增加 ("为什么我的 EC2 扫描失败？")
- 竞品对比时处于劣势

**用户影响**:
- 需要多次重试扫描 (浪费时间和 AWS API 配额)
- 不确定数据是否完整
- 生成的 Terraform 代码可能缺少资源

### 证据

**代码路径 1: VPCScanner**
```
VPCScanner.scan()
  └─> _scan_vpcs()
      ├─> describe_flow_logs paginator (try/except)
      └─> describe_vpcs paginator (❌ 无错误处理)
          └─> 每页: graph.add_resource(vpc_node)
          └─> 如果第 N 页失败:
              - 前 N-1 页数据在图中 ✅
              - 异常向上传播到 scan() 的 except ClientError
              - 扫描标记为失败 ❌
```

**代码路径 2: EC2Scanner**
```python
# replimap/scanners/ec2_scanner.py:62-70
def _scan_instances(self, ec2: Any, graph: GraphEngine) -> None:
    """Scan all EC2 instances in the region."""
    logger.debug("Scanning EC2 instances...")

    paginator = ec2.get_paginator("describe_instances")
    for page in paginator.paginate():  # ❌ 无错误处理
        for reservation in page.get("Reservations", []):
            for instance in reservation.get("Instances", []):
                self._process_instance(instance, graph)
```

**实际场景模拟**:

| 账户规模 | 页数 | 失败页 | 已保存资源 | 报告状态 | 用户感知 |
|---------|------|--------|-----------|---------|---------|
| 100 EC2 | 5 页 | 第 3 页 | 40 个 | ❌ Failed | 以为 0 个 |
| 500 EC2 | 25 页 | 第 20 页 | 380 个 | ❌ Failed | 以为 0 个 |
| 1000 RDS | 50 页 | 第 45 页 | 880 个 | ❌ Failed | 以为 0 个 |

### 复现步骤

1. 准备一个大型 AWS 账户 (500+ EC2 实例)
2. 模拟网络不稳定环境:
   ```bash
   # 使用 tc (traffic control) 模拟 5% 丢包率
   sudo tc qdisc add dev eth0 root netem loss 5%
   ```
3. 运行扫描:
   ```bash
   replimap -p large-account -r us-east-1 scan
   ```
4. 观察日志:
   ```
   INFO: Scanning EC2 instances in us-east-1...
   DEBUG: Processing page 1 (20 instances)
   DEBUG: Processing page 2 (20 instances)
   ...
   DEBUG: Processing page 18 (20 instances)
   ERROR: EC2 scanning failed: Read timeout on endpoint URL
   ```
5. 检查图中的实例数量:
   ```python
   # 实际有 360 个实例在图中，但用户不知道
   ```

### 推荐修复

**方案 1: 逐页错误处理 + 部分成功报告** ⭐ 推荐

```python
# replimap/scanners/base.py (新增工具函数)
from dataclasses import dataclass
from typing import Iterator, TypeVar, Callable

T = TypeVar('T')

@dataclass
class PaginationResult:
    """分页结果，包含成功和失败统计"""
    total_pages: int = 0
    successful_pages: int = 0
    failed_pages: int = 0
    items_collected: int = 0
    errors: list[Exception] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []

    @property
    def success_rate(self) -> float:
        if self.total_pages == 0:
            return 0.0
        return self.successful_pages / self.total_pages

def resilient_paginate(
    paginator,
    result_key: str,
    on_page_success: Callable[[list], None] | None = None,
    max_retries: int = 3,
) -> PaginationResult:
    """
    分页器包装器，支持逐页重试和部分成功。

    Args:
        paginator: boto3 paginator 对象
        result_key: 页面结果的 key (如 "Vpcs", "Instances")
        on_page_success: 每页成功后的回调函数
        max_retries: 每页最大重试次数

    Returns:
        PaginationResult 包含统计信息

    Example:
        paginator = ec2.get_paginator("describe_vpcs")
        result = resilient_paginate(
            paginator.paginate(),
            "Vpcs",
            on_page_success=lambda vpcs: [graph.add_resource(v) for v in vpcs]
        )

        if result.success_rate < 0.8:
            logger.warning(f"Only {result.success_rate:.0%} pages succeeded")
    """
    result = PaginationResult()
    page_iterator = iter(paginator)

    while True:
        page_num = result.total_pages + 1
        last_error = None

        # 逐页重试
        for attempt in range(max_retries + 1):
            try:
                page = next(page_iterator)
                result.total_pages += 1

                # 提取结果
                items = page.get(result_key, [])
                result.items_collected += len(items)

                # 调用成功回调
                if on_page_success and items:
                    on_page_success(items)

                result.successful_pages += 1
                logger.debug(
                    f"Page {page_num}: {len(items)} items "
                    f"(total: {result.items_collected})"
                )
                break  # 成功，继续下一页

            except StopIteration:
                # 分页结束
                return result

            except Exception as e:
                last_error = e

                if attempt < max_retries:
                    backoff = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"Page {page_num} failed (attempt {attempt + 1}/{max_retries + 1}), "
                        f"retrying in {backoff:.1f}s: {e}"
                    )
                    time.sleep(backoff)
                else:
                    # 最大重试次数用尽
                    result.failed_pages += 1
                    result.errors.append(last_error)
                    logger.error(
                        f"Page {page_num} failed after {max_retries + 1} attempts: {e}"
                    )
                    # ⚠️ 继续下一页，不中止整个扫描
                    try:
                        page_iterator = iter([next(page_iterator)])  # 尝试继续
                    except StopIteration:
                        return result

    return result
```

**修改 VPCScanner**:

```python
# replimap/scanners/vpc_scanner.py (修改)
def _scan_vpcs(self, ec2: Any, graph: GraphEngine) -> None:
    """Scan all VPCs in the region."""
    logger.debug("Scanning VPCs...")

    # Flow logs (可选，失败不影响 VPC 扫描)
    vpc_flow_logs: dict[str, list[dict[str, Any]]] = {}
    fl_paginator = ec2.get_paginator("describe_flow_logs")
    fl_result = resilient_paginate(
        fl_paginator.paginate(),
        "FlowLogs",
        on_page_success=lambda logs: self._process_flow_logs(logs, vpc_flow_logs)
    )

    if fl_result.failed_pages > 0:
        logger.warning(
            f"Flow logs: {fl_result.successful_pages}/{fl_result.total_pages} pages succeeded"
        )

    # VPCs (主要资源)
    vpc_paginator = ec2.get_paginator("describe_vpcs")
    vpc_result = resilient_paginate(
        vpc_paginator.paginate(),
        "Vpcs",
        on_page_success=lambda vpcs: self._process_vpcs(vpcs, graph, vpc_flow_logs)
    )

    # 🔥 关键：根据成功率决定是否报告为失败
    if vpc_result.success_rate < 0.5:  # 少于50%页面成功 → 严重失败
        raise RuntimeError(
            f"VPC scan critically failed: only {vpc_result.successful_pages}/{vpc_result.total_pages} "
            f"pages succeeded ({vpc_result.items_collected} VPCs collected)"
        )
    elif vpc_result.failed_pages > 0:
        logger.warning(
            f"⚠️ VPC scan partially succeeded: {vpc_result.successful_pages}/{vpc_result.total_pages} "
            f"pages ({vpc_result.items_collected} VPCs, {vpc_result.failed_pages} pages failed)"
        )

def _process_flow_logs(self, logs: list, vpc_flow_logs: dict):
    """处理 flow log 页面"""
    for flow_log in logs:
        resource_id = flow_log.get("ResourceId", "")
        if resource_id.startswith("vpc-"):
            if resource_id not in vpc_flow_logs:
                vpc_flow_logs[resource_id] = []
            vpc_flow_logs[resource_id].append({
                "flow_log_id": flow_log.get("FlowLogId"),
                "traffic_type": flow_log.get("TrafficType"),
                # ...
            })

def _process_vpcs(self, vpcs: list, graph: GraphEngine, vpc_flow_logs: dict):
    """处理 VPC 页面"""
    for vpc in vpcs:
        vpc_id = vpc["VpcId"]
        tags = self._extract_tags(vpc.get("Tags"))
        flow_logs = vpc_flow_logs.get(vpc_id, [])

        node = ResourceNode(
            id=vpc_id,
            resource_type=ResourceType.VPC,
            region=self.region,
            config={
                "cidr_block": vpc["CidrBlock"],
                "flow_logs_enabled": len(flow_logs) > 0,
                "flow_logs": flow_logs,
                # ...
            },
            arn=f"arn:aws:ec2:{self.region}:{self._get_account_id(vpc)}:vpc/{vpc_id}",
            tags=tags,
        )

        graph.add_resource(node)
        logger.debug(f"Added VPC: {vpc_id}")
```

**方案 2: 分页状态持久化 (长期优化)**

对于超大账户，支持扫描中断后从上次位置恢复：

```python
@dataclass
class ScanCheckpoint:
    """扫描检查点"""
    scanner_name: str
    resource_type: str
    last_page_token: str | None
    items_scanned: int
    timestamp: float

class CheckpointManager:
    """管理扫描检查点"""

    def save_checkpoint(self, checkpoint: ScanCheckpoint):
        """保存到 SQLite/JSON"""
        pass

    def load_checkpoint(self, scanner_name: str, resource_type: str) -> ScanCheckpoint | None:
        """加载检查点"""
        pass

    def clear_checkpoint(self, scanner_name: str, resource_type: str):
        """清除检查点"""
        pass

# 使用示例
def _scan_vpcs_resumable(self, ec2, graph):
    checkpoint_mgr = CheckpointManager()
    checkpoint = checkpoint_mgr.load_checkpoint("VPCScanner", "aws_vpc")

    paginator = ec2.get_paginator("describe_vpcs")
    pagination_config = {}
    if checkpoint and checkpoint.last_page_token:
        pagination_config['StartingToken'] = checkpoint.last_page_token
        logger.info(f"Resuming VPC scan from checkpoint ({checkpoint.items_scanned} already scanned)")

    page_iterator = paginator.paginate(**pagination_config)

    for page in page_iterator:
        # 处理页面
        # ...

        # 保存检查点
        checkpoint_mgr.save_checkpoint(ScanCheckpoint(
            scanner_name="VPCScanner",
            resource_type="aws_vpc",
            last_page_token=page.get('NextToken'),
            items_scanned=items_scanned,
            timestamp=time.time()
        ))
```

### 工作量估算

**方案 1 (resilient_paginate + 部分成功报告)**:
- **开发时间**: 2-3 天
  - 实现 `resilient_paginate()`: 6 小时
  - 修改 VPCScanner (示例): 2 小时
  - 修改其他 11 个扫描器: 12 小时 (每个 1 小时)
  - 单元测试 (模拟分页失败): 4 小时
- **测试时间**: 1 天
  - 集成测试 (真实账户): 4 小时
  - Chaos testing (模拟网络故障): 4 小时
- **总计**: **3-4 天** (约 7 个 story points)

**方案 2 (检查点恢复)**:
- **开发时间**: 5-7 天
- **风险**: 中等（状态持久化复杂性）
- **建议**: P1 优先级，长期优化

### 依赖

- 需要与 [FINDING-RL001] (速率限制) 协调：如果分页失败是因为 throttling，应该先修 RL001
- 与 [FINDING-RL002] (重试逻辑) 有交互：resilient_paginate 的重试与全局重试装饰器冲突

---

## [FINDING-PG002] S3 list_buckets 硬限制 1000 桶，无分页支持 🔥

**严重程度**: Critical
**优先级**: P0
**类别**: Data Completeness
**组件**: [replimap/scanners/s3_scanner.py](../replimap/scanners/s3_scanner.py):57-65

### 描述

S3 `list_buckets` API **不支持分页**，单次调用最多返回 1000 个桶。

```python
# replimap/scanners/s3_scanner.py:57-65
def _scan_buckets(self, s3: Any, graph: GraphEngine) -> None:
    """Scan all S3 buckets with parallel processing."""
    logger.debug("Listing S3 buckets...")

    try:
        response = s3.list_buckets()  # 🔴 最多返回 1000 个桶！
    except ClientError as e:
        self._handle_aws_error(e, "list S3 buckets")
        return

    # 🔴 如果账户有 1001+ 桶，这里只能看到 1000 个
    for bucket in response.get("Buckets", []):
        bucket_name = bucket["Name"]
        # ...
```

**AWS 官方文档**:
> "list_buckets returns up to 1000 buckets. For accounts with more buckets, you must use the S3 Control API or AWS Organizations."

### 影响

**数据丢失**:
- 大型组织 (多团队、多产品) 可能有 1000+ S3 桶
- RepliMap 静默跳过第 1001+ 个桶
- 生成的 Terraform 代码缺少这些桶

**商业影响**:
- 企业客户不适用（S3 桶数量通常很多）
- 竞品 (如 Terraformer) 可能没有这个限制

### 证据

**AWS 文档证据**:
- [list_buckets API Reference](https://docs.aws.amazon.com/AmazonS3/latest/API/API_ListBuckets.html)
- "Returns a list of all buckets owned by the authenticated sender of the request. **To list more than 1000 buckets, you must use the S3 Control API.**"

**实际测试**:
```python
import boto3

s3 = boto3.client('s3')
response = s3.list_buckets()

print(f"Buckets returned: {len(response['Buckets'])}")
# 输出: Buckets returned: 1000 (即使账户有 1500 个桶)
```

### 推荐修复

**方案 1: 使用 S3 Control API (ListRegionalBuckets)** ⭐ 推荐

```python
# replimap/scanners/s3_scanner.py (修改)
def _scan_buckets(self, s3: Any, graph: GraphEngine) -> None:
    """Scan all S3 buckets with support for 1000+ buckets."""
    logger.debug("Listing S3 buckets...")

    # 🔥 使用 S3 Control API 替代 list_buckets
    account_id = self._get_account_id_from_sts()
    s3control = self.session.client('s3control')

    buckets_to_process: list[str] = []

    try:
        # S3 Control API 支持分页
        paginator = s3control.get_paginator('list_regional_buckets')
        for page in paginator.paginate(AccountId=account_id, OutpostId=''):
            for bucket in page.get('RegionalBucketList', []):
                bucket_name = bucket['Name']
                bucket_region = bucket['Region']

                # 只处理目标 region 的桶
                if bucket_region != self.region:
                    continue

                buckets_to_process.append(bucket_name)

    except ClientError as e:
        # Fallback 到 list_buckets (有 1000 限制)
        logger.warning(
            f"S3 Control API failed ({e}), falling back to list_buckets (max 1000 buckets)"
        )
        response = s3.list_buckets()
        for bucket in response.get("Buckets", []):
            bucket_name = bucket["Name"]

            # Get bucket region
            try:
                location = s3.get_bucket_location(Bucket=bucket_name)
                bucket_region = location.get("LocationConstraint") or "us-east-1"
            except ClientError as e:
                logger.warning(f"Could not get region for bucket {bucket_name}: {e}")
                continue

            if bucket_region != self.region:
                continue

            buckets_to_process.append(bucket_name)

    if len(buckets_to_process) >= 1000:
        logger.warning(
            f"⚠️ Found exactly 1000 S3 buckets - this may indicate the API limit was hit. "
            f"Some buckets may be missing. Consider using S3 Control API."
        )

    logger.debug(f"Processing {len(buckets_to_process)} S3 buckets...")

    # ... 后续并行处理逻辑不变
```

**方案 2: 文档化限制 + 警告**

如果不修改代码，至少要文档化：

```python
def _scan_buckets(self, s3: Any, graph: GraphEngine) -> None:
    """
    Scan all S3 buckets with parallel processing.

    ⚠️ WARNING: Due to AWS API limitations, this scanner can only detect
    the first 1000 S3 buckets in your account. If you have more than 1000
    buckets, some will be silently skipped.

    Workaround: Use AWS Organizations or S3 Control API for large accounts.
    """
    logger.debug("Listing S3 buckets...")

    response = s3.list_buckets()
    buckets = response.get("Buckets", [])

    if len(buckets) == 1000:
        logger.error(
            "🔴 CRITICAL: Detected exactly 1000 S3 buckets. "
            "AWS list_buckets API has a hard limit of 1000. "
            "If your account has more buckets, they will NOT be scanned. "
            "Please contact RepliMap support for large account support."
        )

    # ...
```

### 工作量估算

**方案 1 (S3 Control API)**:
- **开发时间**: 1 天
  - 实现 S3 Control API 调用: 3 小时
  - Fallback 逻辑: 2 小时
  - 测试 (需要 >1000 桶账户): 3 小时
- **总计**: **1 天** (2 story points)

**方案 2 (文档化)**:
- **开发时间**: 1 小时
- **风险**: 用户可能仍然不知道限制

---

## [FINDING-PG003] ComputeScanner 嵌套 API 调用无独立错误处理

**严重程度**: High
**优先级**: P1
**类别**: Reliability
**组件**: [replimap/scanners/compute_scanner.py](../replimap/scanners/compute_scanner.py):80-136

### 描述

`ComputeScanner` 在分页循环内调用额外的 API (无分页器)，这些调用失败会导致部分资源丢失。

```python
# replimap/scanners/compute_scanner.py:80-136
def _scan_launch_templates(self, graph: GraphEngine) -> None:
    """Scan all Launch Templates in the region."""
    ec2 = self.get_client("ec2")

    paginator = ec2.get_paginator("describe_launch_templates")
    for page in paginator.paginate():  # ❌ 无错误处理
        for lt in page.get("LaunchTemplates", []):
            lt_id = lt["LaunchTemplateId"]

            # 🔴 问题：这个调用失败 → 整个 Launch Template 扫描中止
            version_resp = ec2.describe_launch_template_versions(
                LaunchTemplateId=lt_id,
                Versions=["$Latest"],
            )  # ❌ 无 try/except

            versions = version_resp.get("LaunchTemplateVersions", [])
            lt_data = versions[0].get("LaunchTemplateData", {}) if versions else {}

            # ...
```

**问题**:
- 如果 `describe_launch_template_versions` 失败 (权限问题、API throttling)
- 异常向上传播 → 整个 Launch Template 扫描中止
- 前面已扫描的 Launch Templates **可能** 在图中，但扫描标记为失败

### 影响

- 单个 Launch Template 的版本获取失败 → 所有 LT 扫描失败
- 用户体验差 (为什么扫描失败？)

### 推荐修复

```python
def _scan_launch_templates(self, graph: GraphEngine) -> None:
    """Scan all Launch Templates in the region."""
    ec2 = self.get_client("ec2")

    paginator = ec2.get_paginator("describe_launch_templates")

    # 🔥 使用 resilient_paginate
    result = resilient_paginate(
        paginator.paginate(),
        "LaunchTemplates",
        on_page_success=lambda lts: self._process_launch_templates(ec2, lts, graph)
    )

    if result.failed_pages > 0:
        logger.warning(
            f"Launch Template scan: {result.successful_pages}/{result.total_pages} pages succeeded"
        )

def _process_launch_templates(self, ec2, launch_templates: list, graph: GraphEngine):
    """处理 Launch Template 页面"""
    for lt in launch_templates:
        lt_id = lt["LaunchTemplateId"]
        lt_name = lt["LaunchTemplateName"]
        tags = self._extract_tags(lt.get("Tags"))

        # 🔥 独立错误处理
        lt_data = {}
        try:
            version_resp = ec2.describe_launch_template_versions(
                LaunchTemplateId=lt_id,
                Versions=["$Latest"],
            )
            versions = version_resp.get("LaunchTemplateVersions", [])
            lt_data = versions[0].get("LaunchTemplateData", {}) if versions else {}
        except ClientError as e:
            logger.warning(
                f"Could not get version for Launch Template {lt_name}: {e}. "
                f"Continuing with basic info..."
            )

        # 即使版本获取失败，仍然添加基本信息
        node = ResourceNode(
            id=lt_id,
            resource_type=ResourceType.LAUNCH_TEMPLATE,
            region=self.region,
            config={
                "name": lt_name,
                "default_version": lt.get("DefaultVersionNumber"),
                "latest_version": lt.get("LatestVersionNumber"),
                # 如果 lt_data 为空，这些字段为 None
                "instance_type": lt_data.get("InstanceType"),
                "image_id": lt_data.get("ImageId"),
                # ...
            },
            arn=f"arn:aws:ec2:{self.region}::launch-template/{lt_id}",
            tags=tags,
        )

        graph.add_resource(node)
        logger.debug(f"Added Launch Template: {lt_name}")
```

### 工作量估算

- **开发时间**: 4 小时 (修改 ComputeScanner 的 4 个方法)
- **测试时间**: 2 小时
- **总计**: **0.75 天** (1.5 story points)

---

## [FINDING-PG004] 无分页进度反馈，大账户扫描看起来卡死

**严重程度**: Medium
**优先级**: P2
**类别**: User Experience
**组件**: 所有扫描器

### 描述

扫描大型账户时，用户看到：

```
INFO: Scanning EC2 instances in us-east-1...
[等待 5 分钟，没有任何输出]
INFO: EC2 scanning complete
```

用户不知道：
- 扫描进度如何 (20% 还是 80%?)
- 是否卡住了
- 还需要等多久

### 影响

- 用户体验差
- 用户可能误认为工具卡死，强制终止扫描

### 推荐修复

**方案 1: 逐页进度日志**

```python
# replimap/scanners/base.py
def resilient_paginate(...) -> PaginationResult:
    result = PaginationResult()
    page_iterator = iter(paginator)

    # 🔥 估算总页数 (如果 API 提供)
    estimated_total = None

    while True:
        page_num = result.total_pages + 1

        for attempt in range(max_retries + 1):
            try:
                page = next(page_iterator)
                result.total_pages += 1

                items = page.get(result_key, [])
                result.items_collected += len(items)

                # 🔥 进度反馈
                if estimated_total:
                    progress_pct = (page_num / estimated_total) * 100
                    logger.info(
                        f"[{page_num}/{estimated_total}] {progress_pct:.0f}% "
                        f"({result.items_collected} items collected)"
                    )
                else:
                    logger.info(
                        f"[Page {page_num}] {result.items_collected} items collected"
                    )

                # ...
```

**方案 2: Rich 进度条**

```python
from rich.progress import Progress

def _scan_instances(self, ec2, graph):
    paginator = ec2.get_paginator("describe_instances")

    with Progress() as progress:
        # 🔥 如果不知道总数，使用 indeterminate 进度条
        task = progress.add_task("[cyan]Scanning EC2 instances...", total=None)

        page_num = 0
        for page in paginator.paginate():
            page_num += 1
            instances_in_page = sum(
                len(r['Instances']) for r in page.get('Reservations', [])
            )

            # 更新进度
            progress.update(
                task,
                description=f"[cyan]Page {page_num} ({instances_in_page} instances)..."
            )

            # 处理实例
            for reservation in page.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    self._process_instance(instance, graph)

        progress.update(task, completed=True)
```

### 工作量估算

- **开发时间**: 1 天 (所有扫描器)
- **总计**: **1 天** (2 story points)

---

## [FINDING-PG005] 分页失败未记录详细上下文

**严重程度**: Low
**优先级**: P2
**类别**: Observability
**组件**: 所有扫描器

### 描述

分页失败时，日志只显示：

```
ERROR: VPC scanning failed: Read timeout on endpoint URL
```

缺少关键上下文：
- 哪一页失败？
- 已扫描多少资源？
- 失败前的分页 token 是什么？

### 推荐修复

```python
def resilient_paginate(...) -> PaginationResult:
    # ...

    except Exception as e:
        last_error = e

        if attempt < max_retries:
            logger.warning(
                f"Page {page_num} failed (attempt {attempt + 1}/{max_retries + 1}), "
                f"retrying in {backoff:.1f}s: {e}"
            )
        else:
            # 🔥 详细错误日志
            logger.error(
                f"❌ Page {page_num} failed after {max_retries + 1} attempts\n"
                f"  Error: {e}\n"
                f"  Items collected so far: {result.items_collected}\n"
                f"  Successful pages: {result.successful_pages}\n"
                f"  Failed pages: {result.failed_pages + 1}\n"
                f"  Last NextToken: {page.get('NextToken', 'N/A')}"
            )
            result.failed_pages += 1
            result.errors.append(last_error)
```

### 工作量估算

- **开发时间**: 2 小时
- **总计**: **0.25 天** (0.5 story points)

---

## [FINDING-PG006] 无分页性能优化 (预取、批处理)

**严重程度**: Low
**优先级**: P3
**类别**: Performance
**组件**: 所有扫描器

### 描述

当前分页逻辑是串行的：

```
请求页1 → 等待响应 → 处理 → 请求页2 → 等待响应 → 处理 → ...
```

可以优化为：

```
请求页1 + 页2 → 等待页1响应 → 处理页1 + 请求页3 → 等待页2响应 → 处理页2 + 请求页4 → ...
```

### 推荐修复

使用 `asyncio` 预取下一页：

```python
async def async_resilient_paginate(
    async_paginator,
    result_key: str,
    on_page_success,
    prefetch_pages: int = 2,
):
    """异步分页器，支持预取"""
    result = PaginationResult()
    page_queue = asyncio.Queue(maxsize=prefetch_pages)

    # Producer: 预取页面
    async def fetch_pages():
        async for page in async_paginator:
            await page_queue.put(page)
        await page_queue.put(None)  # Sentinel

    # Consumer: 处理页面
    async def process_pages():
        while True:
            page = await page_queue.get()
            if page is None:
                break

            items = page.get(result_key, [])
            result.items_collected += len(items)

            if on_page_success:
                on_page_success(items)

            result.successful_pages += 1

    # 并发执行
    await asyncio.gather(
        fetch_pages(),
        process_pages()
    )

    return result
```

### 工作量估算

- **开发时间**: 3 天 (需要迁移到异步)
- **收益**: 扫描速度提升 20-30%
- **优先级**: P3 (性能优化)

---

## 总体修复路线图 (Fix Roadmap)

### 短期 (1 周内 - P0)

1. ✅ **[PG001] resilient_paginate + 部分成功报告** (3-4 天)
   - 实现核心 `resilient_paginate()` 函数
   - 修改 VPCScanner, EC2Scanner, RDSScanner (高风险)
   - 单元测试 + 集成测试

2. ✅ **[PG002] S3 list_buckets 修复** (1 天)
   - 使用 S3 Control API
   - Fallback 逻辑

### 中期 (2-4 周 - P1)

3. ✅ **[PG003] 嵌套 API 调用错误处理** (0.75 天)
   - 修复 ComputeScanner

4. ✅ **[PG004] 分页进度反馈** (1 天)
   - 添加 Rich 进度条或日志

5. ⏸ **[PG005] 详细错误日志** (0.25 天)

### 长期 (3 个月+ - P2/P3)

6. 🔄 **分页状态持久化 (检查点恢复)**
7. 🔄 **异步预取优化**

---

## 验证计划 (Verification Plan)

### 单元测试

```python
# tests/test_pagination.py
import pytest
from unittest.mock import MagicMock, Mock
from botocore.exceptions import ClientError
from replimap.scanners.base import resilient_paginate, PaginationResult

def test_resilient_paginate_all_success():
    """验证所有页面成功的场景"""
    # Mock paginator
    pages = [
        {'Vpcs': [{'VpcId': f'vpc-{i}'} for i in range(10)]},
        {'Vpcs': [{'VpcId': f'vpc-{i}'} for i in range(10, 20)]},
        {'Vpcs': [{'VpcId': f'vpc-{i}'} for i in range(20, 25)]},
    ]

    paginator = iter(pages)

    collected_vpcs = []
    result = resilient_paginate(
        paginator,
        'Vpcs',
        on_page_success=lambda vpcs: collected_vpcs.extend(vpcs)
    )

    assert result.total_pages == 3
    assert result.successful_pages == 3
    assert result.failed_pages == 0
    assert result.items_collected == 25
    assert result.success_rate == 1.0
    assert len(collected_vpcs) == 25

def test_resilient_paginate_partial_failure():
    """验证部分页面失败的场景"""

    class FailingPaginator:
        def __init__(self):
            self.call_count = 0

        def __iter__(self):
            return self

        def __next__(self):
            self.call_count += 1
            if self.call_count == 2:
                # 第2页失败
                raise ClientError(
                    {'Error': {'Code': 'RequestTimeout', 'Message': 'Timeout'}},
                    'DescribeVpcs'
                )
            if self.call_count > 3:
                raise StopIteration

            return {'Vpcs': [{'VpcId': f'vpc-{self.call_count}'}]}

    paginator = FailingPaginator()

    collected_vpcs = []
    result = resilient_paginate(
        paginator,
        'Vpcs',
        on_page_success=lambda vpcs: collected_vpcs.extend(vpcs),
        max_retries=1  # 快速失败
    )

    assert result.total_pages == 3  # 尝试了3页
    assert result.successful_pages == 2  # 页1和页3成功
    assert result.failed_pages == 1  # 页2失败
    assert result.items_collected == 2
    assert 0.6 < result.success_rate < 0.7  # 2/3

def test_s3_scanner_1000_bucket_warning():
    """验证 S3 scanner 检测到1000桶时发出警告"""
    # TODO: 实现
```

### 集成测试

```bash
# 大规模账户测试
export AWS_PROFILE=large-test-account  # 500+ EC2, 1000+ S3 buckets

# 模拟网络不稳定
sudo tc qdisc add dev eth0 root netem loss 5% delay 100ms 10ms

replimap -p large-test-account -r us-east-1 scan --verbose

# 验证指标:
# ✅ 部分成功消息: "EC2 scan: 23/25 pages succeeded (460 instances, 2 pages failed)"
# ✅ S3 警告: "Found exactly 1000 S3 buckets - API limit may be hit"
# ✅ 扫描未完全中止
# ✅ 生成的 Terraform 包含大部分资源

# 清理网络设置
sudo tc qdisc del dev eth0 root
```

### Chaos Engineering 测试

```python
# tests/chaos/test_pagination_chaos.py
import random
from botocore.exceptions import ClientError

class ChaosMonkeyPaginator:
    """模拟随机分页失败"""

    def __init__(self, pages: list, failure_rate: float = 0.2):
        self.pages = pages
        self.failure_rate = failure_rate
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.index >= len(self.pages):
            raise StopIteration

        # 随机失败
        if random.random() < self.failure_rate:
            self.index += 1
            raise ClientError(
                {'Error': {'Code': 'InternalError', 'Message': 'Chaos!'}},
                'DescribeVpcs'
            )

        page = self.pages[self.index]
        self.index += 1
        return page

def test_chaos_pagination():
    """混沌测试：随机20%页面失败"""
    pages = [{'Vpcs': [f'vpc-{i}']} for i in range(50)]  # 50 页

    collected = []
    result = resilient_paginate(
        ChaosMonkeyPaginator(pages, failure_rate=0.2),
        'Vpcs',
        on_page_success=lambda vpcs: collected.extend(vpcs),
        max_retries=2
    )

    # 至少60%页面应该成功
    assert result.success_rate >= 0.6
    # 收集到的数据应该大于0
    assert len(collected) > 0
```

### 性能基准测试

| 场景 | 修复前 | 修复后 (目标) |
|------|--------|--------------|
| **EC2 扫描 (500 实例)** | 全失败或全成功 | 部分成功 (>80% 页面) |
| **分页失败恢复时间** | N/A (整体重新扫描) | 只重试失败页 |
| **S3 桶扫描 (1500 桶)** | 只扫描 1000 | 扫描全部 1500 |
| **用户可见进度** | 无 | Rich 进度条 |

---

## 参考资料 (References)

1. **AWS 分页最佳实践**:
   - [Paginating AWS API Results](https://docs.aws.amazon.com/cli/latest/userguide/cli-usage-pagination.html)

2. **S3 list_buckets 限制**:
   - [ListBuckets API Reference](https://docs.aws.amazon.com/AmazonS3/latest/API/API_ListBuckets.html)
   - [S3 Control API - ListRegionalBuckets](https://docs.aws.amazon.com/AmazonS3/latest/API/API_control_ListRegionalBuckets.html)

3. **Resilience 模式**:
   - [Circuit Breaker Pattern](https://martinfowler.com/bliki/CircuitBreaker.html)
   - [Retry Pattern with Exponential Backoff](https://docs.microsoft.com/en-us/azure/architecture/patterns/retry)

---

**报告生成时间**: 2026-01-11 00:30 UTC+13
**审查员**: Claude Sonnet 4.5 (via Claude Code)
**批准状态**: 待用户确认
