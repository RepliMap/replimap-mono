# VPC: stage
# Original ID: vpc-09f6dc50cbabb6b17
resource "aws_vpc" "stage" {
  cidr_block           = "172.17.0.0/16"
  instance_tenancy     = "default"
  enable_dns_support   = true
  enable_dns_hostnames = false

  tags = {
    Name        = "stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vpc-09f6dc50cbabb6b17"
    Terraform = "true"
    Environment = "stage"
    Cost Center = "Platform"
  }
}

# VPC: public
# Original ID: vpc-f27a5797
resource "aws_vpc" "public" {
  cidr_block           = "172.31.0.0/16"
  instance_tenancy     = "default"
  enable_dns_support   = true
  enable_dns_hostnames = false

  tags = {
    Name        = "public"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vpc-f27a5797"
  }
}

# VPC: lifesupport
# Original ID: vpc-0df54189f81fbdaba
resource "aws_vpc" "lifesupport" {
  cidr_block           = "172.19.0.0/16"
  instance_tenancy     = "default"
  enable_dns_support   = true
  enable_dns_hostnames = false

  tags = {
    Name        = "lifesupport"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vpc-0df54189f81fbdaba"
    Environment = "staging"
    Terraform = "true"
    Cost Center = "Platform"
  }
}

# Subnet: stage-subnet-private-ap-southeast-2c
# Original ID: subnet-00349a9d4cde1e3c1
# Availability Zone: ap-southeast-2c
resource "aws_subnet" "stage-subnet-private-ap-southeast-2c" {
  vpc_id                  = aws_vpc..id
  cidr_block              = "172.17.32.0/20"
  availability_zone       = "ap-southeast-2c"
  map_public_ip_on_launch = false

  tags = {
    Name        = "stage-subnet-private-ap-southeast-2c"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "subnet-00349a9d4cde1e3c1"
    Cost Center = "Platform"
    Environment = "stage"
    Kind = "private"
    Terraform = "true"
  }
}

# Subnet: stage-subnet-public-ap-southeast-2a
# Original ID: subnet-0e1480382007c1dc7
# Availability Zone: ap-southeast-2a
resource "aws_subnet" "stage-subnet-public-ap-southeast-2a" {
  vpc_id                  = aws_vpc..id
  cidr_block              = "172.17.48.0/20"
  availability_zone       = "ap-southeast-2a"
  map_public_ip_on_launch = true

  tags = {
    Name        = "stage-subnet-public-ap-southeast-2a"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "subnet-0e1480382007c1dc7"
    Kind = "public"
    Cost Center = "Platform"
    Terraform = "true"
    Environment = "stage"
  }
}

# Subnet: stage-subnet-private-ap-southeast-2b
# Original ID: subnet-008e35c5f7638fccc
# Availability Zone: ap-southeast-2b
resource "aws_subnet" "stage-subnet-private-ap-southeast-2b" {
  vpc_id                  = aws_vpc..id
  cidr_block              = "172.17.16.0/20"
  availability_zone       = "ap-southeast-2b"
  map_public_ip_on_launch = false

  tags = {
    Name        = "stage-subnet-private-ap-southeast-2b"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "subnet-008e35c5f7638fccc"
    Environment = "stage"
    Terraform = "true"
    Cost Center = "Platform"
    Kind = "private"
  }
}

# Subnet: public-2b
# Original ID: subnet-15f31271
# Availability Zone: ap-southeast-2b
resource "aws_subnet" "public-2b" {
  vpc_id                  = aws_vpc..id
  cidr_block              = "172.31.0.0/20"
  availability_zone       = "ap-southeast-2b"
  map_public_ip_on_launch = true

  tags = {
    Name        = "public-2b"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "subnet-15f31271"
  }
}

# Subnet: public-2a
# Original ID: subnet-db6c6eac
# Availability Zone: ap-southeast-2a
resource "aws_subnet" "public-2a" {
  vpc_id                  = aws_vpc..id
  cidr_block              = "172.31.32.0/20"
  availability_zone       = "ap-southeast-2a"
  map_public_ip_on_launch = true

  tags = {
    Name        = "public-2a"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "subnet-db6c6eac"
  }
}

# Subnet: stage-subnet-private-ap-southeast-2a
# Original ID: subnet-009da00d0a0aa0de6
# Availability Zone: ap-southeast-2a
resource "aws_subnet" "stage-subnet-private-ap-southeast-2a" {
  vpc_id                  = aws_vpc..id
  cidr_block              = "172.17.0.0/20"
  availability_zone       = "ap-southeast-2a"
  map_public_ip_on_launch = false

  tags = {
    Name        = "stage-subnet-private-ap-southeast-2a"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "subnet-009da00d0a0aa0de6"
    Terraform = "true"
    Cost Center = "Platform"
    Kind = "private"
    Environment = "stage"
  }
}

# Subnet: public-2c
# Original ID: subnet-32504274
# Availability Zone: ap-southeast-2c
resource "aws_subnet" "public-2c" {
  vpc_id                  = aws_vpc..id
  cidr_block              = "172.31.16.0/20"
  availability_zone       = "ap-southeast-2c"
  map_public_ip_on_launch = true

  tags = {
    Name        = "public-2c"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "subnet-32504274"
  }
}

# Subnet: stage-subnet-public-ap-southeast-2c
# Original ID: subnet-0d056c96429820111
# Availability Zone: ap-southeast-2c
resource "aws_subnet" "stage-subnet-public-ap-southeast-2c" {
  vpc_id                  = aws_vpc..id
  cidr_block              = "172.17.80.0/20"
  availability_zone       = "ap-southeast-2c"
  map_public_ip_on_launch = true

  tags = {
    Name        = "stage-subnet-public-ap-southeast-2c"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "subnet-0d056c96429820111"
    Environment = "stage"
    Kind = "public"
    Cost Center = "Platform"
    Terraform = "true"
  }
}

# Subnet: stage-subnet-public-ap-southeast-2b
# Original ID: subnet-0c1543f6321bd77e6
# Availability Zone: ap-southeast-2b
resource "aws_subnet" "stage-subnet-public-ap-southeast-2b" {
  vpc_id                  = aws_vpc..id
  cidr_block              = "172.17.64.0/20"
  availability_zone       = "ap-southeast-2b"
  map_public_ip_on_launch = true

  tags = {
    Name        = "stage-subnet-public-ap-southeast-2b"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "subnet-0c1543f6321bd77e6"
    Cost Center = "Platform"
    Kind = "public"
    Environment = "stage"
    Terraform = "true"
  }
}

# Subnet: lifesupport-subnet-public-ap-southeast-2a
# Original ID: subnet-072e801b76cf2620d
# Availability Zone: ap-southeast-2a
resource "aws_subnet" "lifesupport-subnet-public-ap-southeast-2a" {
  vpc_id                  = aws_vpc..id
  cidr_block              = "172.19.48.0/20"
  availability_zone       = "ap-southeast-2a"
  map_public_ip_on_launch = true

  tags = {
    Name        = "lifesupport-subnet-public-ap-southeast-2a"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "subnet-072e801b76cf2620d"
    Terraform = "true"
    Kind = "public"
    Cost Center = "Platform"
    Environment = "staging"
  }
}

# Subnet: lifesupport-subnet-private-ap-southeast-2b
# Original ID: subnet-05cfe0b2fde0f56bf
# Availability Zone: ap-southeast-2b
resource "aws_subnet" "lifesupport-subnet-private-ap-southeast-2b" {
  vpc_id                  = aws_vpc..id
  cidr_block              = "172.19.16.0/20"
  availability_zone       = "ap-southeast-2b"
  map_public_ip_on_launch = false

  tags = {
    Name        = "lifesupport-subnet-private-ap-southeast-2b"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "subnet-05cfe0b2fde0f56bf"
    Environment = "staging"
    Terraform = "true"
    Cost Center = "Platform"
    Kind = "private"
  }
}

# Subnet: lifesupport-subnet-private-ap-southeast-2a
# Original ID: subnet-0b4cf5575a6eeaa5f
# Availability Zone: ap-southeast-2a
resource "aws_subnet" "lifesupport-subnet-private-ap-southeast-2a" {
  vpc_id                  = aws_vpc..id
  cidr_block              = "172.19.0.0/20"
  availability_zone       = "ap-southeast-2a"
  map_public_ip_on_launch = false

  tags = {
    Name        = "lifesupport-subnet-private-ap-southeast-2a"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "subnet-0b4cf5575a6eeaa5f"
    Kind = "private"
    Cost Center = "Platform"
    Environment = "staging"
    Terraform = "true"
  }
}

# Subnet: private-2c
# Original ID: subnet-0c14e6a2075f75ea0
# Availability Zone: ap-southeast-2c
resource "aws_subnet" "private-2c" {
  vpc_id                  = aws_vpc..id
  cidr_block              = "172.31.240.0/20"
  availability_zone       = "ap-southeast-2c"
  map_public_ip_on_launch = false

  tags = {
    Name        = "private-2c"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "subnet-0c14e6a2075f75ea0"
  }
}

# Subnet: lifesupport-subnet-private-ap-southeast-2c
# Original ID: subnet-0481f29b29293e359
# Availability Zone: ap-southeast-2c
resource "aws_subnet" "lifesupport-subnet-private-ap-southeast-2c" {
  vpc_id                  = aws_vpc..id
  cidr_block              = "172.19.32.0/20"
  availability_zone       = "ap-southeast-2c"
  map_public_ip_on_launch = false

  tags = {
    Name        = "lifesupport-subnet-private-ap-southeast-2c"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "subnet-0481f29b29293e359"
    Cost Center = "Platform"
    Environment = "staging"
    Kind = "private"
    Terraform = "true"
  }
}

# Subnet: lifesupport-subnet-public-ap-southeast-2c
# Original ID: subnet-07b513b2b521f33a1
# Availability Zone: ap-southeast-2c
resource "aws_subnet" "lifesupport-subnet-public-ap-southeast-2c" {
  vpc_id                  = aws_vpc..id
  cidr_block              = "172.19.80.0/20"
  availability_zone       = "ap-southeast-2c"
  map_public_ip_on_launch = true

  tags = {
    Name        = "lifesupport-subnet-public-ap-southeast-2c"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "subnet-07b513b2b521f33a1"
    Environment = "staging"
    Kind = "public"
    Cost Center = "Platform"
    Terraform = "true"
  }
}

# Subnet: lifesupport-subnet-public-ap-southeast-2b
# Original ID: subnet-0679b0da70f38e87e
# Availability Zone: ap-southeast-2b
resource "aws_subnet" "lifesupport-subnet-public-ap-southeast-2b" {
  vpc_id                  = aws_vpc..id
  cidr_block              = "172.19.64.0/20"
  availability_zone       = "ap-southeast-2b"
  map_public_ip_on_launch = true

  tags = {
    Name        = "lifesupport-subnet-public-ap-southeast-2b"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "subnet-0679b0da70f38e87e"
    Cost Center = "Platform"
    Environment = "staging"
    Terraform = "true"
    Kind = "public"
  }
}