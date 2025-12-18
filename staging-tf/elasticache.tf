# ElastiCache Subnet Group: test-etime-14si
resource "aws_elasticache_subnet_group" "test-etime-14si" {
  name        = "test-etime-14si"
  description = "Elasticache subnet group for test-etime-14si"

  subnet_ids = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  tags = {
    Name        = "test-etime-14si"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# ElastiCache Subnet Group: test-elementtime
resource "aws_elasticache_subnet_group" "test-elementtime" {
  name        = "test-elementtime"
  description = "Elasticache subnet group for test-elementtime"

  subnet_ids = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  tags = {
    Name        = "test-elementtime"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# ElastiCache Subnet Group: stage-etime-14si
resource "aws_elasticache_subnet_group" "stage-etime-14si" {
  name        = "stage-etime-14si"
  description = "Elasticache subnet group for stage-etime-14si"

  subnet_ids = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  tags = {
    Name        = "stage-etime-14si"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# ElastiCache Subnet Group: stage-etime-14si
resource "aws_elasticache_subnet_group" "stage-etime-14si" {
  name        = "stage-etime-14si"
  description = "Elasticache subnet group for stage-etime-14si"

  subnet_ids = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  tags = {
    Name        = "stage-etime-14si"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# ElastiCache Subnet Group: stage-esup
resource "aws_elasticache_subnet_group" "stage-esup" {
  name        = "stage-esup"
  description = "Elasticache subnet group for stage-esup"

  subnet_ids = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  tags = {
    Name        = "stage-esup"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# ElastiCache Subnet Group: stage-ecentre
resource "aws_elasticache_subnet_group" "stage-ecentre" {
  name        = "stage-ecentre"
  description = "Elasticache subnet group for stage-ecentre"

  subnet_ids = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  tags = {
    Name        = "stage-ecentre"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# ElastiCache Subnet Group: redis-group
resource "aws_elasticache_subnet_group" "redis-group" {
  name        = "redis-group"
  description = " "

  subnet_ids = [
    aws_subnet.aws_subnet_public-2a_id.id,
    aws_subnet.aws_subnet_public-2c_id.id,
  ]

  tags = {
    Name        = "redis-group"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# ElastiCache Subnet Group: elementsup-redis-subnet
resource "aws_elasticache_subnet_group" "elementsup-redis-subnet" {
  name        = "elementsup-redis-subnet"
  description = "elementsup-redis-subnet-group (managed)"

  subnet_ids = [
    aws_subnet.aws_subnet_public-2b_id.id,
    aws_subnet.aws_subnet_public-2c_id.id,
    aws_subnet.aws_subnet_public-2a_id.id,
  ]

  tags = {
    Name        = "elementsup-redis-subnet"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# ElastiCache Subnet Group: elementcentre-redis-subnet
resource "aws_elasticache_subnet_group" "elementcentre-redis-subnet" {
  name        = "elementcentre-redis-subnet"
  description = "elementcentre-redis-subnet-group (managed)"

  subnet_ids = [
    aws_subnet.aws_subnet_public-2b_id.id,
    aws_subnet.aws_subnet_public-2c_id.id,
    aws_subnet.aws_subnet_public-2a_id.id,
  ]

  tags = {
    Name        = "elementcentre-redis-subnet"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# ElastiCache Cluster: test-etime-14si-001
resource "aws_elasticache_cluster" "test-etime-14si-001" {
  cluster_id           = "test-etime-14si-001"
  engine               = "redis"
  engine_version       = "6.2.6"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  port                 = 6379

  subnet_group_name = aws_elasticache_subnet_group.test-etime-14si.name

  security_group_ids = [
    aws_security_group.aws_security_group_test-etime-14si_id.id,
  ]

  parameter_group_name = "test-etime-14si-redis6-x"

  maintenance_window = "wed:03:00-wed:04:00"


  tags = {
    Name        = "test-etime-14si-001"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# ElastiCache Cluster: test-elementtime-001
resource "aws_elasticache_cluster" "test-elementtime-001" {
  cluster_id           = "test-elementtime-001"
  engine               = "redis"
  engine_version       = "6.2.6"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  port                 = 6379

  subnet_group_name = aws_elasticache_subnet_group.test-elementtime.name

  security_group_ids = [
    aws_security_group.aws_security_group_test-elementtime_id.id,
  ]

  parameter_group_name = "test-elementtime-redis6-x"

  maintenance_window = "wed:03:00-wed:04:00"


  tags = {
    Name        = "test-elementtime-001"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# ElastiCache Cluster: stage-etime-14si-001
resource "aws_elasticache_cluster" "stage-etime-14si-001" {
  cluster_id           = "stage-etime-14si-001"
  engine               = "redis"
  engine_version       = "6.2.6"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  port                 = 6379

  subnet_group_name = aws_elasticache_subnet_group.stage-etime-14si.name

  security_group_ids = [
    aws_security_group.aws_security_group_stage-etime-14si_id.id,
  ]

  parameter_group_name = "stage-etime-14si-redis6-x"

  maintenance_window = "wed:03:00-wed:04:00"


  tags = {
    Name        = "stage-etime-14si-001"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# ElastiCache Cluster: stage-etime-14si-001
resource "aws_elasticache_cluster" "stage-etime-14si-001" {
  cluster_id           = "prod-etime-14si-001"
  engine               = "redis"
  engine_version       = "6.2.6"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  port                 = 6379

  subnet_group_name = aws_elasticache_subnet_group.stage-etime-14si.name

  security_group_ids = [
    aws_security_group.aws_security_group_stage-etime-14si_id.id,
  ]

  parameter_group_name = "stage-etime-14si-redis6-x"

  maintenance_window = "wed:03:00-wed:04:00"


  tags = {
    Name        = "stage-etime-14si-001"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# ElastiCache Cluster: stage-esup-001
resource "aws_elasticache_cluster" "stage-esup-001" {
  cluster_id           = "prod-esup-001"
  engine               = "redis"
  engine_version       = "7.1.0"
  node_type            = "cache.t4g.small"
  num_cache_nodes      = 1
  port                 = 6379

  subnet_group_name = aws_elasticache_subnet_group.stage-esup.name

  security_group_ids = [
    aws_security_group.aws_security_group_stage-esup_id.id,
  ]

  parameter_group_name = "stage-esup-redis7"

  maintenance_window = "wed:03:00-wed:04:00"


  tags = {
    Name        = "stage-esup-001"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# ElastiCache Cluster: stage-ecentre-001
resource "aws_elasticache_cluster" "stage-ecentre-001" {
  cluster_id           = "prod-ecentre-001"
  engine               = "redis"
  engine_version       = "7.1.0"
  node_type            = "cache.t4g.small"
  num_cache_nodes      = 1
  port                 = 6379

  subnet_group_name = aws_elasticache_subnet_group.stage-ecentre.name

  security_group_ids = [
    aws_security_group.aws_security_group_stage-ecentre_id.id,
  ]

  parameter_group_name = "stage-ecentre-redis7"

  maintenance_window = "wed:03:00-wed:04:00"


  tags = {
    Name        = "stage-ecentre-001"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# ElastiCache Cluster: elementtime-app-001
resource "aws_elasticache_cluster" "elementtime-app-001" {
  cluster_id           = "elementtime-app-001"
  engine               = "redis"
  engine_version       = "7.0.7"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  port                 = 6379

  subnet_group_name = aws_elasticache_subnet_group.redis-group.name

  security_group_ids = [
    aws_security_group.aws_security_group_sg-0b914bf14337d2ac1_id.id,
  ]

  parameter_group_name = "default.redis7"

  maintenance_window = "sat:15:00-sat:16:00"


  tags = {
    Name        = "elementtime-app-001"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# ElastiCache Cluster: elementtime2
resource "aws_elasticache_cluster" "elementtime2" {
  cluster_id           = "elementtime2"
  engine               = "redis"
  engine_version       = "5.0.6"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  port                 = 6379

  subnet_group_name = aws_elasticache_subnet_group.redis-group.name

  security_group_ids = [
    aws_security_group.aws_security_group_sg-0b914bf14337d2ac1_id.id,
  ]

  parameter_group_name = "default.redis5.0"

  maintenance_window = "thu:18:00-thu:19:00"

  snapshot_retention_limit = 1

  tags = {
    Name        = "elementtime2"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# ElastiCache Cluster: elementsup-redis
resource "aws_elasticache_cluster" "elementsup-redis" {
  cluster_id           = "elementsup-redis"
  engine               = "redis"
  engine_version       = "7.1.0"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  port                 = 6379

  subnet_group_name = aws_elasticache_subnet_group.elementsup-redis-subnet.name

  security_group_ids = [
    aws_security_group.aws_security_group_elementsup-redis_id.id,
  ]

  parameter_group_name = "default.redis7"

  maintenance_window = "sat:05:30-sat:06:30"

  snapshot_retention_limit = 14

  tags = {
    Name        = "elementsup-redis"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# ElastiCache Cluster: elementstaff-app-001
resource "aws_elasticache_cluster" "elementstaff-app-001" {
  cluster_id           = "elementstaff-app-001"
  engine               = "redis"
  engine_version       = "7.0.7"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  port                 = 6379

  subnet_group_name = aws_elasticache_subnet_group.redis-group.name

  security_group_ids = [
    aws_security_group.aws_security_group_sg-0b914bf14337d2ac1_id.id,
  ]

  parameter_group_name = "default.redis7"

  maintenance_window = "wed:17:30-wed:18:30"


  tags = {
    Name        = "elementstaff-app-001"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# ElastiCache Cluster: elementcentre-redis
resource "aws_elasticache_cluster" "elementcentre-redis" {
  cluster_id           = "elementcentre-redis"
  engine               = "redis"
  engine_version       = "7.1.0"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  port                 = 6379

  subnet_group_name = aws_elasticache_subnet_group.elementcentre-redis-subnet.name

  security_group_ids = [
    aws_security_group.aws_security_group_elementcentre-redis_id.id,
  ]

  parameter_group_name = "default.redis7"

  maintenance_window = "sat:05:30-sat:06:30"

  snapshot_retention_limit = 14

  tags = {
    Name        = "elementcentre-redis"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}