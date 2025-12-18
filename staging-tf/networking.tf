# Internet Gateway: lifesupport-igw
resource "aws_internet_gateway" "lifesupport-igw" {
  # WARNING: VPC aws_vpc.lifesupport.id not found in graph
  vpc_id = "aws_vpc.lifesupport.id"

  tags = {
    Name        = "lifesupport-igw"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "igw-0882e3deb7bc709f7"
    Terraform = "true"
    "Cost Center" = "Platform"
    Environment = "staging"
  }
}

# NAT Gateway: nat-0a9542afdbe893546
resource "aws_eip" "nat-0a9542afdbe893546_eip" {
  domain = "vpc"

  tags = {
    Name        = "nat-0a9542afdbe893546-eip"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "nat-0a9542afdbe893546"
  }
}

resource "aws_nat_gateway" "nat-0a9542afdbe893546" {
  allocation_id = aws_eip.nat-0a9542afdbe893546_eip.id
  # WARNING: Subnet aws_subnet.stage-subnet-public-ap-southeast-2a.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-public-ap-southeast-2a.id"

  tags = {
    Name        = "nat-0a9542afdbe893546"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "nat-0a9542afdbe893546"
  }

}

# NAT Gateway: nat-02553c99f9118b982
resource "aws_eip" "nat-02553c99f9118b982_eip" {
  domain = "vpc"

  tags = {
    Name        = "nat-02553c99f9118b982-eip"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "nat-02553c99f9118b982"
  }
}

resource "aws_nat_gateway" "nat-02553c99f9118b982" {
  allocation_id = aws_eip.nat-02553c99f9118b982_eip.id
  # WARNING: Subnet aws_subnet.public-2c.id not found in graph
  subnet_id     = "aws_subnet.public-2c.id"

  tags = {
    Name        = "nat-02553c99f9118b982"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "nat-02553c99f9118b982"
  }

}

# NAT Gateway: nat-010460b85ae257df8
resource "aws_eip" "nat-010460b85ae257df8_eip" {
  domain = "vpc"

  tags = {
    Name        = "nat-010460b85ae257df8-eip"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "nat-010460b85ae257df8"
  }
}

resource "aws_nat_gateway" "nat-010460b85ae257df8" {
  allocation_id = aws_eip.nat-010460b85ae257df8_eip.id
  # WARNING: Subnet aws_subnet.lifesupport-subnet-public-ap-southeast-2a.id not found in graph
  subnet_id     = "aws_subnet.lifesupport-subnet-public-ap-southeast-2a.id"

  tags = {
    Name        = "nat-010460b85ae257df8"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "nat-010460b85ae257df8"
  }

}

# Internet Gateway: public-internet-gw
resource "aws_internet_gateway" "public-internet-gw" {
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id = "aws_vpc.public.id"

  tags = {
    Name        = "public-internet-gw"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "igw-0b5ecc6e"
  }
}

# Internet Gateway: stage-igw
resource "aws_internet_gateway" "stage-igw" {
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id = "aws_vpc.stage.id"

  tags = {
    Name        = "stage-igw"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "igw-09a86850eb881c544"
    Terraform = "true"
    "Cost Center" = "Platform"
    Environment = "stage"
  }
}

# VPC Endpoint: vpce-002c74882de88640a
resource "aws_vpc_endpoint" "vpce-002c74882de88640a" {
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id            = "aws_vpc.public.id"
  service_name      = "com.amazonaws.vpce.ap-southeast-2.vpce-svc-0648c3b18381e4dd6"
  vpc_endpoint_type = "Interface"

  subnet_ids = [
    "aws_subnet.public-2b.id",
    "aws_subnet.public-2c.id",
    "aws_subnet.public-2a.id",
  ]

  security_group_ids = [
    "aws_security_group.rds-proxy-etime-14si-stage.id",
  ]

  private_dns_enabled = 

  tags = {
    Name        = "vpce-002c74882de88640a"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vpce-002c74882de88640a"
  }
}

# VPC Endpoint: vpce-0b2bd52e7f833cfff
resource "aws_vpc_endpoint" "vpce-0b2bd52e7f833cfff" {
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id            = "aws_vpc.public.id"
  service_name      = "com.amazonaws.vpce.ap-southeast-2.vpce-svc-0648c3b18381e4dd6"
  vpc_endpoint_type = "Interface"

  subnet_ids = [
    "aws_subnet.public-2b.id",
    "aws_subnet.public-2c.id",
    "aws_subnet.public-2a.id",
  ]

  security_group_ids = [
    "aws_security_group.rds-proxy-etime-14si-stage.id",
  ]

  private_dns_enabled = 

  tags = {
    Name        = "vpce-0b2bd52e7f833cfff"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vpce-0b2bd52e7f833cfff"
  }
}

# VPC Endpoint: vpce-0f2fd50f594473181
resource "aws_vpc_endpoint" "vpce-0f2fd50f594473181" {
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id            = "aws_vpc.public.id"
  service_name      = "com.amazonaws.vpce.ap-southeast-2.vpce-svc-0648c3b18381e4dd6"
  vpc_endpoint_type = "Interface"

  subnet_ids = [
    "aws_subnet.public-2b.id",
    "aws_subnet.public-2c.id",
    "aws_subnet.public-2a.id",
  ]

  security_group_ids = [
    "aws_security_group.rds-proxy-etime-14si-stage-i3.id",
  ]

  private_dns_enabled = 

  tags = {
    Name        = "vpce-0f2fd50f594473181"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vpce-0f2fd50f594473181"
  }
}

# VPC Endpoint: vpce-089e31664c9e683af
resource "aws_vpc_endpoint" "vpce-089e31664c9e683af" {
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id            = "aws_vpc.public.id"
  service_name      = "com.amazonaws.vpce.ap-southeast-2.vpce-svc-0648c3b18381e4dd6"
  vpc_endpoint_type = "Interface"

  subnet_ids = [
    "aws_subnet.public-2b.id",
    "aws_subnet.public-2c.id",
    "aws_subnet.public-2a.id",
  ]

  security_group_ids = [
    "aws_security_group.rds-proxy-etime-14si-stage-i3.id",
  ]

  private_dns_enabled = 

  tags = {
    Name        = "vpce-089e31664c9e683af"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vpce-089e31664c9e683af"
  }
}

# VPC Endpoint: vpce-02b95255d01ef9ef9
resource "aws_vpc_endpoint" "vpce-02b95255d01ef9ef9" {
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id            = "aws_vpc.public.id"
  service_name      = "com.amazonaws.vpce.ap-southeast-2.vpce-svc-00b463612df7a3e36"
  vpc_endpoint_type = "Interface"

  subnet_ids = [
    "aws_subnet.public-2b.id",
    "aws_subnet.public-2c.id",
  ]

  security_group_ids = [
    "aws_security_group.rds-proxy-etime-14si-stage-i3.id",
  ]

  private_dns_enabled = 

  tags = {
    Name        = "vpce-02b95255d01ef9ef9"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vpce-02b95255d01ef9ef9"
  }
}

# VPC Endpoint: vpce-06bce7c8f5743f882
resource "aws_vpc_endpoint" "vpce-06bce7c8f5743f882" {
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id            = "aws_vpc.public.id"
  service_name      = "com.amazonaws.vpce.ap-southeast-2.vpce-svc-00b463612df7a3e36"
  vpc_endpoint_type = "Interface"

  subnet_ids = [
    "aws_subnet.public-2b.id",
    "aws_subnet.public-2c.id",
  ]

  security_group_ids = [
    "aws_security_group.rds-proxy-etime-14si-stage.id",
  ]

  private_dns_enabled = 

  tags = {
    Name        = "vpce-06bce7c8f5743f882"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vpce-06bce7c8f5743f882"
  }
}

# Route Table: lifesupport-rt-public
resource "aws_route_table" "lifesupport-rt-public" {
  # WARNING: VPC aws_vpc.lifesupport.id not found in graph
  vpc_id = "aws_vpc.lifesupport.id"

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.lifesupport-igw.id
  }

  tags = {
    Name        = "lifesupport-rt-public"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "rtb-071fc8661f71e8021"
    "Cost Center" = "Platform"
    Terraform = "true"
    Environment = "staging"
  }
}

# WARNING: Subnet aws_subnet.lifesupport-subnet-public-ap-southeast-2c.id not found in graph
# WARNING: Subnet aws_subnet.lifesupport-subnet-public-ap-southeast-2a.id not found in graph
# WARNING: Subnet aws_subnet.lifesupport-subnet-public-ap-southeast-2b.id not found in graph


# Route Table: stage-rt-private-ap-southeast-2b
resource "aws_route_table" "stage-rt-private-ap-southeast-2b" {
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id = "aws_vpc.stage.id"

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat-0a9542afdbe893546.id
  }

  tags = {
    Name        = "stage-rt-private-ap-southeast-2b"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "rtb-0e353c926a2179fcd"
    "Cost Center" = "Platform"
    Environment = "stage"
    Terraform = "true"
  }
}

# WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2b.id not found in graph


# Route Table: nat-routing
resource "aws_route_table" "nat-routing" {
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id = "aws_vpc.public.id"

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat-02553c99f9118b982.id
  }

  tags = {
    Name        = "nat-routing"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "rtb-0e78de62043b438e4"
  }
}

# WARNING: Subnet aws_subnet.private-2c.id not found in graph


# Route Table: rtb-0d883b04aae6f054a
resource "aws_route_table" "rtb-0d883b04aae6f054a" {
  # WARNING: VPC aws_vpc.lifesupport.id not found in graph
  vpc_id = "aws_vpc.lifesupport.id"


  tags = {
    Name        = "rtb-0d883b04aae6f054a"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "rtb-0d883b04aae6f054a"
  }
}



# Route Table: rtb-0f20354c71dd82588
resource "aws_route_table" "rtb-0f20354c71dd82588" {
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id = "aws_vpc.stage.id"


  tags = {
    Name        = "rtb-0f20354c71dd82588"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "rtb-0f20354c71dd82588"
  }
}



# Route Table: lifesupport-rt-private-ap-southeast-2a
resource "aws_route_table" "lifesupport-rt-private-ap-southeast-2a" {
  # WARNING: VPC aws_vpc.lifesupport.id not found in graph
  vpc_id = "aws_vpc.lifesupport.id"

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat-010460b85ae257df8.id
  }

  tags = {
    Name        = "lifesupport-rt-private-ap-southeast-2a"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "rtb-0e9b61ab63e53299e"
    Environment = "staging"
    "Cost Center" = "Platform"
    Terraform = "true"
  }
}

# WARNING: Subnet aws_subnet.lifesupport-subnet-private-ap-southeast-2a.id not found in graph


# Route Table: stage-rt-private-ap-southeast-2c
resource "aws_route_table" "stage-rt-private-ap-southeast-2c" {
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id = "aws_vpc.stage.id"

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat-0a9542afdbe893546.id
  }

  tags = {
    Name        = "stage-rt-private-ap-southeast-2c"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "rtb-01117134defc38447"
    Terraform = "true"
    "Cost Center" = "Platform"
    Environment = "stage"
  }
}

# WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2c.id not found in graph


# Route Table: lifesupport-rt-private-ap-southeast-2c
resource "aws_route_table" "lifesupport-rt-private-ap-southeast-2c" {
  # WARNING: VPC aws_vpc.lifesupport.id not found in graph
  vpc_id = "aws_vpc.lifesupport.id"

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat-010460b85ae257df8.id
  }

  tags = {
    Name        = "lifesupport-rt-private-ap-southeast-2c"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "rtb-09ca4b20dd32f3a6e"
    Environment = "staging"
    "Cost Center" = "Platform"
    Terraform = "true"
  }
}

# WARNING: Subnet aws_subnet.lifesupport-subnet-private-ap-southeast-2c.id not found in graph


# Route Table: public-main
resource "aws_route_table" "public-main" {
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id = "aws_vpc.public.id"

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.public-internet-gw.id
  }
  route {
    cidr_block = ""
    gateway_id = aws_internet_gateway.public-internet-gw.id
  }

  tags = {
    Name        = "public-main"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "rtb-31766054"
  }
}

# WARNING: Subnet aws_subnet.public-2b.id not found in graph


# Route Table: lifesupport-rt-private-ap-southeast-2b
resource "aws_route_table" "lifesupport-rt-private-ap-southeast-2b" {
  # WARNING: VPC aws_vpc.lifesupport.id not found in graph
  vpc_id = "aws_vpc.lifesupport.id"

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat-010460b85ae257df8.id
  }

  tags = {
    Name        = "lifesupport-rt-private-ap-southeast-2b"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "rtb-0bdac3730b08157e9"
    "Cost Center" = "Platform"
    Environment = "staging"
    Terraform = "true"
  }
}

# WARNING: Subnet aws_subnet.lifesupport-subnet-private-ap-southeast-2b.id not found in graph


# Route Table: stage-rt-public
resource "aws_route_table" "stage-rt-public" {
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id = "aws_vpc.stage.id"

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.stage-igw.id
  }

  tags = {
    Name        = "stage-rt-public"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "rtb-0f77700769a4714da"
    Terraform = "true"
    "Cost Center" = "Platform"
    Environment = "stage"
  }
}

# WARNING: Subnet aws_subnet.stage-subnet-public-ap-southeast-2b.id not found in graph
# WARNING: Subnet aws_subnet.stage-subnet-public-ap-southeast-2c.id not found in graph
# WARNING: Subnet aws_subnet.stage-subnet-public-ap-southeast-2a.id not found in graph


# Route Table: stage-rt-private-ap-southeast-2a
resource "aws_route_table" "stage-rt-private-ap-southeast-2a" {
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id = "aws_vpc.stage.id"

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat-0a9542afdbe893546.id
  }

  tags = {
    Name        = "stage-rt-private-ap-southeast-2a"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "rtb-09413ab8c0fd071df"
    Terraform = "true"
    "Cost Center" = "Platform"
    Environment = "stage"
  }
}

# WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2a.id not found in graph
