# DB Subnet Group: test-docdb-etime
resource "aws_db_subnet_group" "test-docdb-etime" {
  name        = "test-docdb-etime-${var.environment}"
  description = "Allowed subnets for DB cluster instances"

  subnet_ids = [
  ]

  tags = {
    Name        = "test-docdb-etime"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "test-docdb-etime"
  }
}

# DB Subnet Group: default
resource "aws_db_subnet_group" "default" {
  name        = "default-${var.environment}"
  description = "default"

  subnet_ids = [
  ]

  tags = {
    Name        = "default"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "default"
  }
}

# DB Subnet Group: esup-prod
resource "aws_db_subnet_group" "esup-stage" {
  name        = "esup-stage-${var.environment}"
  description = "For Aurora cluster esup-stage"

  subnet_ids = [
  ]

  tags = {
    Name        = "esup-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "esup-prod"
  }
}

# DB Subnet Group: eorg-ypc-test
resource "aws_db_subnet_group" "eorg-ypc-test" {
  name        = "eorg-ypc-test-${var.environment}"
  description = "For Aurora cluster eorg-ypc-test"

  subnet_ids = [
  ]

  tags = {
    Name        = "eorg-ypc-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "eorg-ypc-test"
  }
}

# DB Subnet Group: eorg-ypc-prod
resource "aws_db_subnet_group" "eorg-ypc-stage" {
  name        = "eorg-ypc-stage-${var.environment}"
  description = "For Aurora cluster eorg-ypc-stage"

  subnet_ids = [
  ]

  tags = {
    Name        = "eorg-ypc-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "eorg-ypc-prod"
  }
}

# DB Subnet Group: eorg-ngsc-test-trellis
resource "aws_db_subnet_group" "eorg-ngsc-test-trellis" {
  name        = "eorg-ngsc-test-trellis-${var.environment}"
  description = "For Aurora cluster eorg-ngsc-test-trellis"

  subnet_ids = [
  ]

  tags = {
    Name        = "eorg-ngsc-test-trellis"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "eorg-ngsc-test-trellis"
  }
}

# DB Subnet Group: eorg-ngsc-test
resource "aws_db_subnet_group" "eorg-ngsc-test" {
  name        = "eorg-ngsc-test-${var.environment}"
  description = "For Aurora cluster eorg-ngsc-test"

  subnet_ids = [
  ]

  tags = {
    Name        = "eorg-ngsc-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "eorg-ngsc-test"
  }
}

# DB Subnet Group: eorg-ngsc-prod
resource "aws_db_subnet_group" "eorg-ngsc-stage" {
  name        = "eorg-ngsc-stage-${var.environment}"
  description = "For Aurora cluster eorg-ngsc-stage"

  subnet_ids = [
  ]

  tags = {
    Name        = "eorg-ngsc-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "eorg-ngsc-prod"
  }
}

# DB Subnet Group: eorg-leeton-sandbox
resource "aws_db_subnet_group" "eorg-leeton-sandbox" {
  name        = "eorg-leeton-sandbox-${var.environment}"
  description = "For Aurora cluster eorg-leeton-sandbox"

  subnet_ids = [
  ]

  tags = {
    Name        = "eorg-leeton-sandbox"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "eorg-leeton-sandbox"
  }
}

# DB Subnet Group: eorg-leeton-prod
resource "aws_db_subnet_group" "eorg-leeton-stage" {
  name        = "eorg-leeton-stage-${var.environment}"
  description = "For Aurora cluster eorg-leeton-stage"

  subnet_ids = [
  ]

  tags = {
    Name        = "eorg-leeton-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "eorg-leeton-prod"
  }
}

# DB Subnet Group: eorg-griffith-test
resource "aws_db_subnet_group" "eorg-griffith-test" {
  name        = "eorg-griffith-test-${var.environment}"
  description = "For Aurora cluster eorg-griffith-test"

  subnet_ids = [
  ]

  tags = {
    Name        = "eorg-griffith-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "eorg-griffith-test"
  }
}

# DB Subnet Group: eorg-griffith-prod
resource "aws_db_subnet_group" "eorg-griffith-stage" {
  name        = "eorg-griffith-stage-${var.environment}"
  description = "For Aurora cluster eorg-griffith-stage"

  subnet_ids = [
  ]

  tags = {
    Name        = "eorg-griffith-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "eorg-griffith-prod"
  }
}

# DB Subnet Group: elementorg-sa-burnoffs-20240128050218594200000002
resource "aws_db_subnet_group" "elementorg-sa-burnoffs-20240128050218594200000002" {
  name        = "elementorg-sa-burnoffs-20240128050218594200000002-${var.environment}"
  description = "elementorg-sa-burnoffs subnet group"

  subnet_ids = [
  ]

  tags = {
    Name        = "elementorg-sa-burnoffs-20240128050218594200000002"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "elementorg-sa-burnoffs-20240128050218594200000002"
  }
}

# DB Subnet Group: ecentre-prod
resource "aws_db_subnet_group" "ecentre-stage" {
  name        = "ecentre-stage-${var.environment}"
  description = "For Aurora cluster ecentre-stage"

  subnet_ids = [
  ]

  tags = {
    Name        = "ecentre-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ecentre-prod"
  }
}

# RDS Instance: test-docdb-etime-1
# Original Instance Class: db.t3.medium
# Engine: docdb 5.0.0
resource "aws_db_instance" "test-docdb-etime" {
  identifier = "test-docdb-etime-1-${var.environment}"

  # Engine configuration
  engine         = "docdb"
  engine_version = "5.0.0"

  # Instance configuration
  instance_class        = "db.t3.medium"
  allocated_storage     = 1
  storage_type          = "standard"
  storage_encrypted     = true

  # Database configuration
  username = "admin1"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_test-docdb-etime
  port     = 27017

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2c"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "21:00-22:00"
  maintenance_window      = "sat:22:30-sat:23:30"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "test-docdb-etime-1-final-${var.environment}"

  parameter_group_name = "default.docdb5.0"

  tags = {
    Name        = "test-docdb-etime"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "test-docdb-etime-1"
    Cost Center = "elementTIME"
    Project Team = "elementTIME"
    Environment = "stage"
    Terraform = "true"
    Project Service = "elementTIME"
  }
}

# Add password variable to variables.tf
# variable "db_password_test-docdb-etime" {
#   description = "Password for RDS instance test-docdb-etime-1"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: test-database-3-instance-2-tmp-04
# Original Instance Class: db.t4g.medium
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "test-database-3-instance-2-tmp-04" {
  identifier = "test-database-3-instance-2-tmp-04-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.t4g.medium"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_test-database-3-instance-2-tmp-04
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2b"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "13:28-13:58"
  maintenance_window      = "sat:19:25-sat:19:55"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "test-database-3-instance-2-tmp-04-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "test-database-3-instance-2-tmp-04"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "test-database-3-instance-2-tmp-04"
  }
}

# Add password variable to variables.tf
# variable "db_password_test-database-3-instance-2-tmp-04" {
#   description = "Password for RDS instance test-database-3-instance-2-tmp-04"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: test-database-3-instance-1-tmp-04
# Original Instance Class: db.t4g.medium
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "test-database-3-instance-1-tmp-04" {
  identifier = "test-database-3-instance-1-tmp-04-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.t4g.medium"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_test-database-3-instance-1-tmp-04
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2c"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "13:28-13:58"
  maintenance_window      = "sat:19:25-sat:19:55"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "test-database-3-instance-1-tmp-04-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "test-database-3-instance-1-tmp-04"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "test-database-3-instance-1-tmp-04"
  }
}

# Add password variable to variables.tf
# variable "db_password_test-database-3-instance-1-tmp-04" {
#   description = "Password for RDS instance test-database-3-instance-1-tmp-04"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: postgresql-11-1
# Original Instance Class: db.t4g.small
# Engine: postgres 17.4
resource "aws_db_instance" "postgresql-11-1" {
  identifier = "postgresql-11-1-${var.environment}"

  # Engine configuration
  engine         = "postgres"
  engine_version = "17.4"

  # Instance configuration
  instance_class        = "db.t4g.small"
  allocated_storage     = 100
  storage_type          = "gp2"
  storage_encrypted     = true

  # Database configuration
  db_name  = "postgres"
  username = "postgres"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_postgresql-11-1
  port     = 5432

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2c"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "14:50-15:20"
  maintenance_window      = "sun:14:00-sun:14:30"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "postgresql-11-1-final-${var.environment}"

  parameter_group_name = "pg17-custom-hba-config"

  tags = {
    Name        = "postgresql-11-1"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "postgresql-11-1"
    MakeSnapshotShortTerm = "True"
  }
}

# Add password variable to variables.tf
# variable "db_password_postgresql-11-1" {
#   description = "Password for RDS instance postgresql-11-1"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: etime-14si-test-1
# Original Instance Class: db.t4g.medium
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "etime-14si-test" {
  identifier = "etime-14si-test-1-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.t4g.medium"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_etime-14si-test
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2b"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "etime-14si-test-1-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "etime-14si-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "etime-14si-test-1"
    Cost Center = "elementTIME"
    Project Team = "elementTIME"
    Project Service = "elementTIME"
    MakeSnapshotShortTerm = "True"
    Env = "test"
    env_version = "14si"
  }
}

# Add password variable to variables.tf
# variable "db_password_etime-14si-test" {
#   description = "Password for RDS instance etime-14si-test-1"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: etime-14si-stage-2-upgrades
# Original Instance Class: db.t4g.medium
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "etime-14si-stage" {
  identifier = "etime-14si-stage-2-upgrades-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.t4g.medium"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_etime-14si-stage
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2b"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "etime-14si-stage-2-upgrades-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "etime-14si-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "etime-14si-stage-2-upgrades"
    Cost Center = "elementTIME"
    Project Team = "elementTIME"
    Project Service = "elementTIME"
    MakeSnapshotShortTerm = "True"
    Env = "stage"
    env_version = "14si"
  }
}

# Add password variable to variables.tf
# variable "db_password_etime-14si-stage" {
#   description = "Password for RDS instance etime-14si-stage-2-upgrades"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: etime-14si-stage-2
# Original Instance Class: db.t4g.medium
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "etime-14si-stage" {
  identifier = "etime-14si-stage-2-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.t4g.medium"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_etime-14si-stage
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2b"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "etime-14si-stage-2-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "etime-14si-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "etime-14si-stage-2"
    Cost Center = "elementTIME"
    Project Team = "elementTIME"
    Project Service = "elementTIME"
    MakeSnapshotShortTerm = "True"
    Env = "stage"
    env_version = "14si"
  }
}

# Add password variable to variables.tf
# variable "db_password_etime-14si-stage" {
#   description = "Password for RDS instance etime-14si-stage-2"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: etime-14si-stage-1-upgrades
# Original Instance Class: db.t4g.medium
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "etime-14si-stage" {
  identifier = "etime-14si-stage-1-upgrades-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.t4g.medium"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_etime-14si-stage
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2a"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "etime-14si-stage-1-upgrades-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "etime-14si-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "etime-14si-stage-1-upgrades"
    Cost Center = "elementTIME"
    Project Team = "elementTIME"
    Project Service = "elementTIME"
    MakeSnapshotShortTerm = "True"
    Env = "stage"
    env_version = "14si"
  }
}

# Add password variable to variables.tf
# variable "db_password_etime-14si-stage" {
#   description = "Password for RDS instance etime-14si-stage-1-upgrades"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: etime-14si-stage-1
# Original Instance Class: db.t4g.medium
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "etime-14si-stage" {
  identifier = "etime-14si-stage-1-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.t4g.medium"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_etime-14si-stage
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2a"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "etime-14si-stage-1-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "etime-14si-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "etime-14si-stage-1"
    Cost Center = "elementTIME"
    Project Team = "elementTIME"
    Project Service = "elementTIME"
    MakeSnapshotShortTerm = "True"
    Env = "stage"
    env_version = "14si"
  }
}

# Add password variable to variables.tf
# variable "db_password_etime-14si-stage" {
#   description = "Password for RDS instance etime-14si-stage-1"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: etime-14si-prod-upgrades-2
# Original Instance Class: db.r8g.large
# Engine: aurora-mysql 8.0.mysql_aurora.3.09.0
resource "aws_db_instance" "etime-14si-stage" {
  identifier = "etime-14si-stage-upgrades-2-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.09.0"

  # Instance configuration
  instance_class        = "db.r8g.large"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_etime-14si-stage
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2b"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "etime-14si-stage-upgrades-2-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "etime-14si-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "etime-14si-prod-upgrades-2"
    Cost Center = "elementTIME"
    Project Team = "elementTIME"
    Project Service = "elementTIME"
    MakeSnapshotShortTerm = "True"
    Env = "stage"
    env_version = "14si"
  }
}

# Add password variable to variables.tf
# variable "db_password_etime-14si-stage" {
#   description = "Password for RDS instance etime-14si-prod-upgrades-2"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: etime-14si-prod-upgrades-1
# Original Instance Class: db.r8g.large
# Engine: aurora-mysql 8.0.mysql_aurora.3.09.0
resource "aws_db_instance" "etime-14si-stage" {
  identifier = "etime-14si-stage-upgrades-1-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.09.0"

  # Instance configuration
  instance_class        = "db.r8g.large"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_etime-14si-stage
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2a"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "etime-14si-stage-upgrades-1-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "etime-14si-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "etime-14si-prod-upgrades-1"
    Cost Center = "elementTIME"
    Project Team = "elementTIME"
    Project Service = "elementTIME"
    MakeSnapshotShortTerm = "True"
    Env = "stage"
    env_version = "14si"
  }
}

# Add password variable to variables.tf
# variable "db_password_etime-14si-stage" {
#   description = "Password for RDS instance etime-14si-prod-upgrades-1"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: etime-14si-prod-i3-2
# Original Instance Class: db.r8g.large
# Engine: aurora-mysql 8.0.mysql_aurora.3.09.0
resource "aws_db_instance" "etime-14si-stage" {
  identifier = "etime-14si-stage-i3-2-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.09.0"

  # Instance configuration
  instance_class        = "db.r8g.large"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_etime-14si-stage
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2b"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "etime-14si-stage-i3-2-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "etime-14si-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "etime-14si-prod-i3-2"
    Cost Center = "elementTIME"
    Project Team = "elementTIME"
    Project Service = "elementTIME"
    MakeSnapshotShortTerm = "True"
    Env = "stage"
    env_version = "14si"
  }
}

# Add password variable to variables.tf
# variable "db_password_etime-14si-stage" {
#   description = "Password for RDS instance etime-14si-prod-i3-2"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: etime-14si-prod-i3-1
# Original Instance Class: db.r8g.large
# Engine: aurora-mysql 8.0.mysql_aurora.3.09.0
resource "aws_db_instance" "etime-14si-stage" {
  identifier = "etime-14si-stage-i3-1-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.09.0"

  # Instance configuration
  instance_class        = "db.r8g.large"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_etime-14si-stage
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2a"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "etime-14si-stage-i3-1-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "etime-14si-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "etime-14si-prod-i3-1"
    Cost Center = "elementTIME"
    Project Team = "elementTIME"
    Project Service = "elementTIME"
    MakeSnapshotShortTerm = "True"
    Env = "stage"
    env_version = "14si"
  }
}

# Add password variable to variables.tf
# variable "db_password_etime-14si-stage" {
#   description = "Password for RDS instance etime-14si-prod-i3-1"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: etime-14si-prod-2-i4
# Original Instance Class: db.r8g.large
# Engine: aurora-mysql 8.0.mysql_aurora.3.09.0
resource "aws_db_instance" "etime-14si-stage" {
  identifier = "etime-14si-stage-2-i4-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.09.0"

  # Instance configuration
  instance_class        = "db.r8g.large"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_etime-14si-stage
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2b"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "etime-14si-stage-2-i4-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "etime-14si-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "etime-14si-prod-2-i4"
    Cost Center = "elementTIME"
    Project Team = "elementTIME"
    Project Service = "elementTIME"
    MakeSnapshotShortTerm = "True"
    Env = "stage"
    env_version = "14si"
  }
}

# Add password variable to variables.tf
# variable "db_password_etime-14si-stage" {
#   description = "Password for RDS instance etime-14si-prod-2-i4"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: etime-14si-prod-2-i2
# Original Instance Class: db.r8g.large
# Engine: aurora-mysql 8.0.mysql_aurora.3.09.0
resource "aws_db_instance" "etime-14si-stage" {
  identifier = "etime-14si-stage-2-i2-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.09.0"

  # Instance configuration
  instance_class        = "db.r8g.large"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_etime-14si-stage
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2b"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "etime-14si-stage-2-i2-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "etime-14si-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "etime-14si-prod-2-i2"
    Cost Center = "elementTIME"
    Project Team = "elementTIME"
    Project Service = "elementTIME"
    MakeSnapshotShortTerm = "True"
    Env = "stage"
    env_version = "14si"
  }
}

# Add password variable to variables.tf
# variable "db_password_etime-14si-stage" {
#   description = "Password for RDS instance etime-14si-prod-2-i2"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: etime-14si-prod-2
# Original Instance Class: db.r8g.large
# Engine: aurora-mysql 8.0.mysql_aurora.3.09.0
resource "aws_db_instance" "etime-14si-stage" {
  identifier = "etime-14si-stage-2-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.09.0"

  # Instance configuration
  instance_class        = "db.r8g.large"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_etime-14si-stage
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2b"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "etime-14si-stage-2-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "etime-14si-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "etime-14si-prod-2"
    Cost Center = "elementTIME"
    Project Team = "elementTIME"
    Project Service = "elementTIME"
    MakeSnapshotShortTerm = "True"
    Env = "stage"
    env_version = "14si"
  }
}

# Add password variable to variables.tf
# variable "db_password_etime-14si-stage" {
#   description = "Password for RDS instance etime-14si-prod-2"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: etime-14si-prod-1-i4
# Original Instance Class: db.r8g.large
# Engine: aurora-mysql 8.0.mysql_aurora.3.09.0
resource "aws_db_instance" "etime-14si-stage" {
  identifier = "etime-14si-stage-1-i4-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.09.0"

  # Instance configuration
  instance_class        = "db.r8g.large"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_etime-14si-stage
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2a"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "etime-14si-stage-1-i4-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "etime-14si-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "etime-14si-prod-1-i4"
    Cost Center = "elementTIME"
    Project Team = "elementTIME"
    Project Service = "elementTIME"
    MakeSnapshotShortTerm = "True"
    Env = "stage"
    env_version = "14si"
  }
}

# Add password variable to variables.tf
# variable "db_password_etime-14si-stage" {
#   description = "Password for RDS instance etime-14si-prod-1-i4"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: etime-14si-prod-1-i2
# Original Instance Class: db.r8g.large
# Engine: aurora-mysql 8.0.mysql_aurora.3.09.0
resource "aws_db_instance" "etime-14si-stage" {
  identifier = "etime-14si-stage-1-i2-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.09.0"

  # Instance configuration
  instance_class        = "db.r8g.large"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_etime-14si-stage
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2a"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "etime-14si-stage-1-i2-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "etime-14si-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "etime-14si-prod-1-i2"
    Cost Center = "elementTIME"
    Project Team = "elementTIME"
    Project Service = "elementTIME"
    MakeSnapshotShortTerm = "True"
    Env = "stage"
    env_version = "14si"
  }
}

# Add password variable to variables.tf
# variable "db_password_etime-14si-stage" {
#   description = "Password for RDS instance etime-14si-prod-1-i2"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: etime-14si-prod-1
# Original Instance Class: db.r8g.large
# Engine: aurora-mysql 8.0.mysql_aurora.3.09.0
resource "aws_db_instance" "etime-14si-stage" {
  identifier = "etime-14si-stage-1-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.09.0"

  # Instance configuration
  instance_class        = "db.r8g.large"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_etime-14si-stage
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2a"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "etime-14si-stage-1-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "etime-14si-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "etime-14si-prod-1"
    Cost Center = "elementTIME"
    Project Team = "elementTIME"
    Project Service = "elementTIME"
    MakeSnapshotShortTerm = "True"
    Env = "stage"
    env_version = "14si"
  }
}

# Add password variable to variables.tf
# variable "db_password_etime-14si-stage" {
#   description = "Password for RDS instance etime-14si-prod-1"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: esup-prod-1
# Original Instance Class: db.t4g.medium
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "esup-stage" {
  identifier = "esup-stage-1-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.t4g.medium"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_esup-stage
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2a"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "esup-stage-1-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "esup-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "esup-prod-1"
    Cost Center = "elementSUP"
    Project Team = "elementSUP"
    MakeSnapshotShortTerm = "True"
    Env = "stage"
    Project Service = "elementSUP"
  }
}

# Add password variable to variables.tf
# variable "db_password_esup-stage" {
#   description = "Password for RDS instance esup-prod-1"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: eorg-ypc-test-1
# Original Instance Class: db.t4g.medium
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "eorg-ypc-test" {
  identifier = "eorg-ypc-test-1-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.t4g.medium"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_eorg-ypc-test
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2b"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "eorg-ypc-test-1-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "eorg-ypc-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "eorg-ypc-test-1"
    Cost Center = "elementOrg"
    Project Team = "elementOrg"
    MakeSnapshotShortTerm = "True"
    Env = "test"
    Project Service = "elementOrg"
  }
}

# Add password variable to variables.tf
# variable "db_password_eorg-ypc-test" {
#   description = "Password for RDS instance eorg-ypc-test-1"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: eorg-ypc-prod-1
# Original Instance Class: db.t4g.medium
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "eorg-ypc-stage" {
  identifier = "eorg-ypc-stage-1-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.t4g.medium"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_eorg-ypc-stage
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2c"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "eorg-ypc-stage-1-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "eorg-ypc-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "eorg-ypc-prod-1"
    Cost Center = "elementOrg"
    Project Team = "elementOrg"
    MakeSnapshotShortTerm = "True"
    Env = "stage"
    Project Service = "elementOrg"
  }
}

# Add password variable to variables.tf
# variable "db_password_eorg-ypc-stage" {
#   description = "Password for RDS instance eorg-ypc-prod-1"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: eorg-ngsc-test-trellis-1
# Original Instance Class: db.t4g.medium
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "eorg-ngsc-test-trellis" {
  identifier = "eorg-ngsc-test-trellis-1-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.t4g.medium"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_eorg-ngsc-test-trellis
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2a"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "eorg-ngsc-test-trellis-1-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "eorg-ngsc-test-trellis"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "eorg-ngsc-test-trellis-1"
    Cost Center = "elementOrg"
    Project Team = "elementOrg"
    MakeSnapshotShortTerm = "True"
    Env = "test-trellis"
    Project Service = "elementOrg"
  }
}

# Add password variable to variables.tf
# variable "db_password_eorg-ngsc-test-trellis" {
#   description = "Password for RDS instance eorg-ngsc-test-trellis-1"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: eorg-ngsc-test-1
# Original Instance Class: db.t4g.medium
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "eorg-ngsc-test" {
  identifier = "eorg-ngsc-test-1-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.t4g.medium"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_eorg-ngsc-test
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2a"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "eorg-ngsc-test-1-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "eorg-ngsc-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "eorg-ngsc-test-1"
    Cost Center = "elementOrg"
    Project Team = "elementOrg"
    MakeSnapshotShortTerm = "True"
    Env = "test"
    Project Service = "elementOrg"
  }
}

# Add password variable to variables.tf
# variable "db_password_eorg-ngsc-test" {
#   description = "Password for RDS instance eorg-ngsc-test-1"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: eorg-ngsc-prod-1
# Original Instance Class: db.t4g.medium
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "eorg-ngsc-stage" {
  identifier = "eorg-ngsc-stage-1-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.t4g.medium"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_eorg-ngsc-stage
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2a"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "eorg-ngsc-stage-1-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "eorg-ngsc-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "eorg-ngsc-prod-1"
    Cost Center = "elementOrg"
    Project Team = "elementOrg"
    MakeSnapshotShortTerm = "True"
    Env = "stage"
    Project Service = "elementOrg"
  }
}

# Add password variable to variables.tf
# variable "db_password_eorg-ngsc-stage" {
#   description = "Password for RDS instance eorg-ngsc-prod-1"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: eorg-leeton-sandbox-1
# Original Instance Class: db.t4g.medium
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "eorg-leeton-sandbox" {
  identifier = "eorg-leeton-sandbox-1-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.t4g.medium"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_eorg-leeton-sandbox
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2b"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "eorg-leeton-sandbox-1-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "eorg-leeton-sandbox"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "eorg-leeton-sandbox-1"
    Cost Center = "elementOrg"
    Project Team = "elementOrg"
    MakeSnapshotShortTerm = "True"
    Env = "sandbox"
    Project Service = "elementOrg"
  }
}

# Add password variable to variables.tf
# variable "db_password_eorg-leeton-sandbox" {
#   description = "Password for RDS instance eorg-leeton-sandbox-1"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: eorg-leeton-prod-1
# Original Instance Class: db.t4g.medium
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "eorg-leeton-stage" {
  identifier = "eorg-leeton-stage-1-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.t4g.medium"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_eorg-leeton-stage
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2c"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "eorg-leeton-stage-1-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "eorg-leeton-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "eorg-leeton-prod-1"
    Cost Center = "elementOrg"
    Project Team = "elementOrg"
    MakeSnapshotShortTerm = "True"
    Env = "stage"
    Project Service = "elementOrg"
  }
}

# Add password variable to variables.tf
# variable "db_password_eorg-leeton-stage" {
#   description = "Password for RDS instance eorg-leeton-prod-1"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: eorg-griffith-test-1
# Original Instance Class: db.t4g.medium
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "eorg-griffith-test" {
  identifier = "eorg-griffith-test-1-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.t4g.medium"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_eorg-griffith-test
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2a"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "eorg-griffith-test-1-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "eorg-griffith-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "eorg-griffith-test-1"
    Cost Center = "elementOrg"
    Project Team = "elementOrg"
    MakeSnapshotShortTerm = "True"
    Env = "test"
    Project Service = "elementOrg"
  }
}

# Add password variable to variables.tf
# variable "db_password_eorg-griffith-test" {
#   description = "Password for RDS instance eorg-griffith-test-1"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: eorg-griffith-prod-1
# Original Instance Class: db.t4g.medium
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "eorg-griffith-stage" {
  identifier = "eorg-griffith-stage-1-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.t4g.medium"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_eorg-griffith-stage
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2b"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "eorg-griffith-stage-1-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "eorg-griffith-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "eorg-griffith-prod-1"
    Cost Center = "elementOrg"
    Project Team = "elementOrg"
    MakeSnapshotShortTerm = "True"
    Env = "stage"
    Project Service = "elementOrg"
  }
}

# Add password variable to variables.tf
# variable "db_password_eorg-griffith-stage" {
#   description = "Password for RDS instance eorg-griffith-prod-1"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: elementorg-sa-burnoffs
# Original Instance Class: db.t4g.medium
# Engine: mariadb 10.6.22
resource "aws_db_instance" "elementorg-sa-burnoffs" {
  identifier = "elementorg-sa-burnoffs-${var.environment}"

  # Engine configuration
  engine         = "mariadb"
  engine_version = "10.6.22"

  # Instance configuration
  instance_class        = "db.t4g.medium"
  allocated_storage     = 20
  storage_type          = "gp2"
  storage_encrypted     = true

  # Database configuration
  db_name  = "elementorgburnoffs"
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_elementorg-sa-burnoffs
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2a"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "03:00-06:00"
  maintenance_window      = "sat:11:00-sat:14:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "elementorg-sa-burnoffs-final-${var.environment}"

  parameter_group_name = "elementorg-sa-burnoffs-20240128050218594000000001"

  tags = {
    Name        = "elementorg-sa-burnoffs"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "elementorg-sa-burnoffs"
    project_service = "elementOrg"
    environment = "stage"
    project_team = "elementOrg"
    MakeSnapshotShortTerm = "True"
    cost_center = "elementOrg"
  }
}

# Add password variable to variables.tf
# variable "db_password_elementorg-sa-burnoffs" {
#   description = "Password for RDS instance elementorg-sa-burnoffs"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: ecentre-prod-1
# Original Instance Class: db.t4g.medium
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "ecentre-stage" {
  identifier = "ecentre-stage-1-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.t4g.medium"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_ecentre-stage
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2c"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "02:00-03:00"
  maintenance_window      = "sun:05:00-sun:06:00"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "ecentre-stage-1-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "ecentre-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ecentre-prod-1"
    Cost Center = "elementCentre"
    Project Team = "elementCentre"
    MakeSnapshotShortTerm = "True"
    Env = "stage"
    Project Service = "elementCentre"
  }
}

# Add password variable to variables.tf
# variable "db_password_ecentre-stage" {
#   description = "Password for RDS instance ecentre-prod-1"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: database-2-writer-upgrade-80-griffith
# Original Instance Class: db.r8g.large
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "database-2-writer-upgrade-80-griffith" {
  identifier = "database-2-writer-upgrade-80-griffith-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.r8g.large"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_database-2-writer-upgrade-80-griffith
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2c"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "12:50-13:20"
  maintenance_window      = "sun:15:46-sun:16:16"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "database-2-writer-upgrade-80-griffith-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "database-2-writer-upgrade-80-griffith"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "database-2-writer-upgrade-80-griffith"
  }
}

# Add password variable to variables.tf
# variable "db_password_database-2-writer-upgrade-80-griffith" {
#   description = "Password for RDS instance database-2-writer-upgrade-80-griffith"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: database-2-writer-upgrade-80
# Original Instance Class: db.r8g.large
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "database-2-writer-upgrade-80" {
  identifier = "database-2-writer-upgrade-80-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.r8g.large"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_database-2-writer-upgrade-80
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2c"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "12:50-13:20"
  maintenance_window      = "sun:15:46-sun:16:16"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "database-2-writer-upgrade-80-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "database-2-writer-upgrade-80"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "database-2-writer-upgrade-80"
  }
}

# Add password variable to variables.tf
# variable "db_password_database-2-writer-upgrade-80" {
#   description = "Password for RDS instance database-2-writer-upgrade-80"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: database-2-reader-upgrade-80-griffith
# Original Instance Class: db.r8g.large
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "database-2-reader-upgrade-80-griffith" {
  identifier = "database-2-reader-upgrade-80-griffith-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.r8g.large"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_database-2-reader-upgrade-80-griffith
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2a"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "12:50-13:20"
  maintenance_window      = "sun:15:46-sun:16:16"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "database-2-reader-upgrade-80-griffith-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "database-2-reader-upgrade-80-griffith"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "database-2-reader-upgrade-80-griffith"
  }
}

# Add password variable to variables.tf
# variable "db_password_database-2-reader-upgrade-80-griffith" {
#   description = "Password for RDS instance database-2-reader-upgrade-80-griffith"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: database-2-reader-upgrade-80
# Original Instance Class: db.r8g.large
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "database-2-reader-upgrade-80" {
  identifier = "database-2-reader-upgrade-80-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.r8g.large"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_database-2-reader-upgrade-80
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2a"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "12:50-13:20"
  maintenance_window      = "sun:15:46-sun:16:16"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "database-2-reader-upgrade-80-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "database-2-reader-upgrade-80"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "database-2-reader-upgrade-80"
  }
}

# Add password variable to variables.tf
# variable "db_password_database-2-reader-upgrade-80" {
#   description = "Password for RDS instance database-2-reader-upgrade-80"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: database-1-instance-2-upgrade-80
# Original Instance Class: db.t4g.medium
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "database-1-instance-2-upgrade-80" {
  identifier = "database-1-instance-2-upgrade-80-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.t4g.medium"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_database-1-instance-2-upgrade-80
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2c"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "15:58-16:28"
  maintenance_window      = "thu:14:35-thu:15:05"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "database-1-instance-2-upgrade-80-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "database-1-instance-2-upgrade-80"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "database-1-instance-2-upgrade-80"
  }
}

# Add password variable to variables.tf
# variable "db_password_database-1-instance-2-upgrade-80" {
#   description = "Password for RDS instance database-1-instance-2-upgrade-80"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: database-1-instance-2
# Original Instance Class: db.t3.micro
# Engine: aurora-mysql 5.7.mysql_aurora.2.11.5
resource "aws_db_instance" "database-1-instance-2" {
  identifier = "database-1-instance-2-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "5.7.mysql_aurora.2.11.5"

  # Instance configuration
  instance_class        = "db.t3.micro"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_database-1-instance-2
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2c"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "15:58-16:28"
  maintenance_window      = "thu:14:35-thu:15:05"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "database-1-instance-2-final-${var.environment}"

  parameter_group_name = "a-mysql57-php"

  tags = {
    Name        = "database-1-instance-2"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "database-1-instance-2"
  }
}

# Add password variable to variables.tf
# variable "db_password_database-1-instance-2" {
#   description = "Password for RDS instance database-1-instance-2"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: database-1-instance-1-upgrade-80
# Original Instance Class: db.t4g.medium
# Engine: aurora-mysql 8.0.mysql_aurora.3.08.2
resource "aws_db_instance" "database-1-instance-1-upgrade-80" {
  identifier = "database-1-instance-1-upgrade-80-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "8.0.mysql_aurora.3.08.2"

  # Instance configuration
  instance_class        = "db.t4g.medium"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_database-1-instance-1-upgrade-80
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2b"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "15:58-16:28"
  maintenance_window      = "sat:14:55-sat:15:25"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "database-1-instance-1-upgrade-80-final-${var.environment}"

  parameter_group_name = "etime-mysql8"

  tags = {
    Name        = "database-1-instance-1-upgrade-80"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "database-1-instance-1-upgrade-80"
  }
}

# Add password variable to variables.tf
# variable "db_password_database-1-instance-1-upgrade-80" {
#   description = "Password for RDS instance database-1-instance-1-upgrade-80"
#   type        = string
#   sensitive   = true
# }

# RDS Instance: database-1-instance-1
# Original Instance Class: db.t3.micro
# Engine: aurora-mysql 5.7.mysql_aurora.2.11.5
resource "aws_db_instance" "database-1-instance-1" {
  identifier = "database-1-instance-1-${var.environment}"

  # Engine configuration
  engine         = "aurora-mysql"
  engine_version = "5.7.mysql_aurora.2.11.5"

  # Instance configuration
  instance_class        = "db.t3.micro"
  allocated_storage     = 1
  storage_type          = "aurora"
  storage_encrypted     = true

  # Database configuration
  username = "admin"
  # IMPORTANT: Set password via variable or secrets manager
  password = var.db_password_database-1-instance-1
  port     = 3306

  # Network configuration
  vpc_security_group_ids = [
  ]
  publicly_accessible = false

  # High availability
  multi_az = false
  availability_zone = "ap-southeast-2b"

  # Backup configuration
  backup_retention_period = 30
  backup_window           = "15:58-16:28"
  maintenance_window      = "sat:14:55-sat:15:25"

  # Other settings
  auto_minor_version_upgrade  = true
  deletion_protection         = false
  skip_final_snapshot         = true
  final_snapshot_identifier   = "database-1-instance-1-final-${var.environment}"

  parameter_group_name = "a-mysql57-php"

  tags = {
    Name        = "database-1-instance-1"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "database-1-instance-1"
  }
}

# Add password variable to variables.tf
# variable "db_password_database-1-instance-1" {
#   description = "Password for RDS instance database-1-instance-1"
#   type        = string
#   sensitive   = true
# }

# DB Subnet Group: prod-private-ap-southeast-2
resource "aws_db_subnet_group" "stage-private-ap-southeast-2" {
  name        = "stage-private-ap-southeast-2-${var.environment}"
  description = "Subnet group for RDS instances in new stage VPC (managed)"

  subnet_ids = [
  ]

  tags = {
    Name        = "stage-private-ap-southeast-2"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "prod-private-ap-southeast-2"
  }
}

# DB Subnet Group: elementorg-leeton-sandbox-20230807095636608800000001
resource "aws_db_subnet_group" "elementorg-leeton-sandbox-20230807095636608800000001" {
  name        = "elementorg-leeton-sandbox-20230807095636608800000001-${var.environment}"
  description = "elementorg-leeton-sandbox subnet group"

  subnet_ids = [
  ]

  tags = {
    Name        = "elementorg-leeton-sandbox-20230807095636608800000001"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "elementorg-leeton-sandbox-20230807095636608800000001"
  }
}

# DB Subnet Group: elementorg-leeton-20220118220344887800000001
resource "aws_db_subnet_group" "elementorg-leeton-20220118220344887800000001" {
  name        = "elementorg-leeton-20220118220344887800000001-${var.environment}"
  description = "elementorg-leeton subnet group"

  subnet_ids = [
  ]

  tags = {
    Name        = "elementorg-leeton-20220118220344887800000001"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "elementorg-leeton-20220118220344887800000001"
  }
}

# DB Parameter Group: postgres11
resource "aws_db_parameter_group" "postgres11" {
  name        = "postgres11"
  family      = "postgres11"
  description = "postgres11"


  tags = {
    Name        = "postgres11"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# DB Parameter Group: php-group-56
resource "aws_db_parameter_group" "php-group-56" {
  name        = "php-group-56"
  family      = "aurora5.6"
  description = "5.6 php params"

  parameter {
    name         = "max_connections"
    value        = "5000"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_user_connections"
    value        = "5000"
    apply_method = "dynamic"
  }

  tags = {
    Name        = "php-group-56"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# DB Parameter Group: php-group
resource "aws_db_parameter_group" "php-group" {
  name        = "php-group"
  family      = "aurora5.6"
  description = "increased max_connections"

  parameter {
    name         = "general_log"
    value        = "0"
    apply_method = "dynamic"
  }
  parameter {
    name         = "group_concat_max_len"
    value        = "100000000"
    apply_method = "dynamic"
  }
  parameter {
    name         = "log_output"
    value        = "FILE"
    apply_method = "dynamic"
  }
  parameter {
    name         = "long_query_time"
    value        = "1"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_allowed_packet"
    value        = "1073741824"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_connect_errors"
    value        = "200"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_connections"
    value        = "2000"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_sp_recursion_depth"
    value        = "255"
    apply_method = "dynamic"
  }
  parameter {
    name         = "slow_query_log"
    value        = "1"
    apply_method = "dynamic"
  }

  tags = {
    Name        = "php-group"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# DB Parameter Group: pg17-custom-hba-config
resource "aws_db_parameter_group" "pg17-custom-hba-config" {
  name        = "pg17-custom-hba-config"
  family      = "postgres17"
  description = "pg17-custom-hba-config after upgrade from 16.3 to 17.3"

  parameter {
    name         = "rds.force_ssl"
    value        = "0"
    apply_method = "dynamic"
  }
  parameter {
    name         = "track_activity_query_size"
    value        = "16384"
    apply_method = "static"
  }

  tags = {
    Name        = "pg17-custom-hba-config"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# DB Parameter Group: pg16-custom-hba-config
resource "aws_db_parameter_group" "pg16-custom-hba-config" {
  name        = "pg16-custom-hba-config"
  family      = "postgres16"
  description = "pg16-custom-hba-config after upgrade from 12 to 16.3"

  parameter {
    name         = "rds.force_ssl"
    value        = "0"
    apply_method = "dynamic"
  }

  tags = {
    Name        = "pg16-custom-hba-config"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# DB Parameter Group: mysql57-for-php-cluster
resource "aws_db_parameter_group" "mysql57-for-php-cluster" {
  name        = "mysql57-for-php-cluster"
  family      = "mysql5.7"
  description = "mysql57-for-php-cluster"

  parameter {
    name         = "max_connections"
    value        = "1000"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_user_connections"
    value        = "500"
    apply_method = "dynamic"
  }

  tags = {
    Name        = "mysql57-for-php-cluster"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# DB Parameter Group: mysql57-for-php
resource "aws_db_parameter_group" "mysql57-for-php" {
  name        = "mysql57-for-php"
  family      = "mysql5.7"
  description = "mysql5.7-for-php"

  parameter {
    name         = "max_connections"
    value        = "500"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_user_connections"
    value        = "400"
    apply_method = "dynamic"
  }

  tags = {
    Name        = "mysql57-for-php"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# DB Parameter Group: my-postgres12
resource "aws_db_parameter_group" "my-postgres12" {
  name        = "my-postgres12"
  family      = "postgres12"
  description = "postgres 12 param"

  parameter {
    name         = "max_connections"
    value        = "500"
    apply_method = "static"
  }

  tags = {
    Name        = "my-postgres12"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# DB Parameter Group: etime-mysql8
resource "aws_db_parameter_group" "etime-mysql8" {
  name        = "etime-mysql8"
  family      = "aurora-mysql8.0"
  description = "etime-mysql8 DB parameter group"

  parameter {
    name         = "connect_timeout"
    value        = "120"
    apply_method = "dynamic"
  }
  parameter {
    name         = "general_log"
    value        = "0"
    apply_method = "dynamic"
  }
  parameter {
    name         = "innodb_lock_wait_timeout"
    value        = "100"
    apply_method = "dynamic"
  }
  parameter {
    name         = "internal_tmp_mem_storage_engine"
    value        = "TempTable"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_allowed_packet"
    value        = "1073741824"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_connections"
    value        = "1000"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_sp_recursion_depth"
    value        = "255"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_user_connections"
    value        = "500"
    apply_method = "dynamic"
  }
  parameter {
    name         = "net_buffer_length"
    value        = "1048576"
    apply_method = "dynamic"
  }
  parameter {
    name         = "slow_query_log"
    value        = "1"
    apply_method = "dynamic"
  }

  tags = {
    Name        = "etime-mysql8"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# DB Parameter Group: eorg-mysql57-php
resource "aws_db_parameter_group" "eorg-mysql57-php" {
  name        = "eorg-mysql57-php"
  family      = "aurora-mysql5.7"
  description = "element org"

  parameter {
    name         = "general_log"
    value        = "1"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_allowed_packet"
    value        = "1073741824"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_connections"
    value        = "1000"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_sp_recursion_depth"
    value        = "255"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_user_connections"
    value        = "500"
    apply_method = "dynamic"
  }
  parameter {
    name         = "slow_query_log"
    value        = "1"
    apply_method = "dynamic"
  }
  parameter {
    name         = "thread_stack"
    value        = "522144"
    apply_method = "static"
  }

  tags = {
    Name        = "eorg-mysql57-php"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# DB Parameter Group: elementorg-sa-burnoffs-20240128050218594000000001
resource "aws_db_parameter_group" "elementorg-sa-burnoffs-20240128050218594000000001" {
  name        = "elementorg-sa-burnoffs-20240128050218594000000001"
  family      = "mariadb10.6"
  description = "elementorg-sa-burnoffs parameter group"

  parameter {
    name         = "character_set_client"
    value        = "utf8mb4"
    apply_method = "dynamic"
  }
  parameter {
    name         = "character_set_server"
    value        = "utf8mb4"
    apply_method = "dynamic"
  }

  tags = {
    Name        = "elementorg-sa-burnoffs-20240128050218594000000001"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# DB Parameter Group: elementorg-leeton-sandbox-20230807100843670000000001
resource "aws_db_parameter_group" "elementorg-leeton-sandbox-20230807100843670000000001" {
  name        = "elementorg-leeton-sandbox-20230807100843670000000001"
  family      = "mariadb10.6"
  description = "elementorg-leeton-sandbox parameter group"

  parameter {
    name         = "character_set_client"
    value        = "utf8mb4"
    apply_method = "dynamic"
  }
  parameter {
    name         = "character_set_server"
    value        = "utf8mb4"
    apply_method = "dynamic"
  }

  tags = {
    Name        = "elementorg-leeton-sandbox-20230807100843670000000001"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# DB Parameter Group: elementorg-leeton-20220118220344888200000002
resource "aws_db_parameter_group" "elementorg-leeton-20220118220344888200000002" {
  name        = "elementorg-leeton-20220118220344888200000002"
  family      = "mariadb10.5"
  description = "elementorg-leeton parameter group"

  parameter {
    name         = "character_set_client"
    value        = "utf8mb4"
    apply_method = "dynamic"
  }
  parameter {
    name         = "character_set_server"
    value        = "utf8mb4"
    apply_method = "dynamic"
  }

  tags = {
    Name        = "elementorg-leeton-20220118220344888200000002"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# DB Parameter Group: dr-etime-mysql8
resource "aws_db_parameter_group" "dr-etime-mysql8" {
  name        = "dr-etime-mysql8"
  family      = "aurora-mysql8.0"
  description = "etime-mysql8 DB parameter group"

  parameter {
    name         = "connect_timeout"
    value        = "120"
    apply_method = "dynamic"
  }
  parameter {
    name         = "general_log"
    value        = "0"
    apply_method = "dynamic"
  }
  parameter {
    name         = "innodb_lock_wait_timeout"
    value        = "100"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_allowed_packet"
    value        = "1073741824"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_connections"
    value        = "1000"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_sp_recursion_depth"
    value        = "255"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_user_connections"
    value        = "500"
    apply_method = "dynamic"
  }
  parameter {
    name         = "net_buffer_length"
    value        = "1048576"
    apply_method = "dynamic"
  }
  parameter {
    name         = "slow_query_log"
    value        = "1"
    apply_method = "dynamic"
  }

  tags = {
    Name        = "dr-etime-mysql8"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# DB Parameter Group: a-mysql57-php
resource "aws_db_parameter_group" "a-mysql57-php" {
  name        = "a-mysql57-php"
  family      = "aurora-mysql5.7"
  description = "a-mysql57-php"

  parameter {
    name         = "general_log"
    value        = "1"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_allowed_packet"
    value        = "1073741824"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_connections"
    value        = "1000"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_sp_recursion_depth"
    value        = "255"
    apply_method = "dynamic"
  }
  parameter {
    name         = "max_user_connections"
    value        = "500"
    apply_method = "dynamic"
  }
  parameter {
    name         = "slow_query_log"
    value        = "1"
    apply_method = "dynamic"
  }
  parameter {
    name         = "thread_stack"
    value        = "522144"
    apply_method = "static"
  }

  tags = {
    Name        = "a-mysql57-php"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}