# Internet Gateway: lifesupport-igw
resource "aws_internet_gateway" "lifesupport-igw" {
  vpc_id = aws_vpc.aws_vpc_lifesupport_id.id

  tags = {
    Name        = "lifesupport-igw"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# NAT Gateway: nat-0a9542afdbe893546
resource "aws_eip" "nat-0a9542afdbe893546_eip" {
  domain = "vpc"

  tags = {
    Name        = "nat-0a9542afdbe893546-eip"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

resource "aws_nat_gateway" "nat-0a9542afdbe893546" {
  allocation_id = aws_eip.nat-0a9542afdbe893546_eip.id
  subnet_id     = aws_subnet.aws_subnet_stage-subnet-public-ap-southeast-2a_id.id

  tags = {
    Name        = "nat-0a9542afdbe893546"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }

  depends_on = [aws_internet_gateway.aws_vpc_stage_id]
}

# NAT Gateway: nat-02553c99f9118b982
resource "aws_eip" "nat-02553c99f9118b982_eip" {
  domain = "vpc"

  tags = {
    Name        = "nat-02553c99f9118b982-eip"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

resource "aws_nat_gateway" "nat-02553c99f9118b982" {
  allocation_id = aws_eip.nat-02553c99f9118b982_eip.id
  subnet_id     = aws_subnet.aws_subnet_public-2c_id.id

  tags = {
    Name        = "nat-02553c99f9118b982"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }

  depends_on = [aws_internet_gateway.aws_vpc_public_id]
}

# NAT Gateway: nat-010460b85ae257df8
resource "aws_eip" "nat-010460b85ae257df8_eip" {
  domain = "vpc"

  tags = {
    Name        = "nat-010460b85ae257df8-eip"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

resource "aws_nat_gateway" "nat-010460b85ae257df8" {
  allocation_id = aws_eip.nat-010460b85ae257df8_eip.id
  subnet_id     = aws_subnet.aws_subnet_lifesupport-subnet-public-ap-southeast-2a_id.id

  tags = {
    Name        = "nat-010460b85ae257df8"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }

  depends_on = [aws_internet_gateway.aws_vpc_lifesupport_id]
}

# Internet Gateway: public-internet-gw
resource "aws_internet_gateway" "public-internet-gw" {
  vpc_id = aws_vpc.aws_vpc_public_id.id

  tags = {
    Name        = "public-internet-gw"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Internet Gateway: stage-igw
resource "aws_internet_gateway" "stage-igw" {
  vpc_id = aws_vpc.aws_vpc_stage_id.id

  tags = {
    Name        = "stage-igw"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# VPC Endpoint: vpce-002c74882de88640a
resource "aws_vpc_endpoint" "vpce-002c74882de88640a" {
  vpc_id            = aws_vpc.aws_vpc_public_id.id
  service_name      = "com.amazonaws.vpce.ap-southeast-2.vpce-svc-0648c3b18381e4dd6"
  vpc_endpoint_type = "Interface"

  subnet_ids = [
    aws_subnet.aws_subnet_public-2b_id.id,
    aws_subnet.aws_subnet_public-2c_id.id,
    aws_subnet.aws_subnet_public-2a_id.id,
  ]

  security_group_ids = [
    aws_security_group.aws_security_group_rds-proxy-etime-14si-stage_id.id,
  ]

  private_dns_enabled = 

  tags = {
    Name        = "vpce-002c74882de88640a"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# VPC Endpoint: vpce-0b2bd52e7f833cfff
resource "aws_vpc_endpoint" "vpce-0b2bd52e7f833cfff" {
  vpc_id            = aws_vpc.aws_vpc_public_id.id
  service_name      = "com.amazonaws.vpce.ap-southeast-2.vpce-svc-0648c3b18381e4dd6"
  vpc_endpoint_type = "Interface"

  subnet_ids = [
    aws_subnet.aws_subnet_public-2b_id.id,
    aws_subnet.aws_subnet_public-2c_id.id,
    aws_subnet.aws_subnet_public-2a_id.id,
  ]

  security_group_ids = [
    aws_security_group.aws_security_group_rds-proxy-etime-14si-stage_id.id,
  ]

  private_dns_enabled = 

  tags = {
    Name        = "vpce-0b2bd52e7f833cfff"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# VPC Endpoint: vpce-0f2fd50f594473181
resource "aws_vpc_endpoint" "vpce-0f2fd50f594473181" {
  vpc_id            = aws_vpc.aws_vpc_public_id.id
  service_name      = "com.amazonaws.vpce.ap-southeast-2.vpce-svc-0648c3b18381e4dd6"
  vpc_endpoint_type = "Interface"

  subnet_ids = [
    aws_subnet.aws_subnet_public-2b_id.id,
    aws_subnet.aws_subnet_public-2c_id.id,
    aws_subnet.aws_subnet_public-2a_id.id,
  ]

  security_group_ids = [
    aws_security_group.aws_security_group_rds-proxy-etime-14si-stage-i3_id.id,
  ]

  private_dns_enabled = 

  tags = {
    Name        = "vpce-0f2fd50f594473181"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# VPC Endpoint: vpce-089e31664c9e683af
resource "aws_vpc_endpoint" "vpce-089e31664c9e683af" {
  vpc_id            = aws_vpc.aws_vpc_public_id.id
  service_name      = "com.amazonaws.vpce.ap-southeast-2.vpce-svc-0648c3b18381e4dd6"
  vpc_endpoint_type = "Interface"

  subnet_ids = [
    aws_subnet.aws_subnet_public-2b_id.id,
    aws_subnet.aws_subnet_public-2c_id.id,
    aws_subnet.aws_subnet_public-2a_id.id,
  ]

  security_group_ids = [
    aws_security_group.aws_security_group_rds-proxy-etime-14si-stage-i3_id.id,
  ]

  private_dns_enabled = 

  tags = {
    Name        = "vpce-089e31664c9e683af"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# VPC Endpoint: vpce-02b95255d01ef9ef9
resource "aws_vpc_endpoint" "vpce-02b95255d01ef9ef9" {
  vpc_id            = aws_vpc.aws_vpc_public_id.id
  service_name      = "com.amazonaws.vpce.ap-southeast-2.vpce-svc-00b463612df7a3e36"
  vpc_endpoint_type = "Interface"

  subnet_ids = [
    aws_subnet.aws_subnet_public-2b_id.id,
    aws_subnet.aws_subnet_public-2c_id.id,
  ]

  security_group_ids = [
    aws_security_group.aws_security_group_rds-proxy-etime-14si-stage-i3_id.id,
  ]

  private_dns_enabled = 

  tags = {
    Name        = "vpce-02b95255d01ef9ef9"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# VPC Endpoint: vpce-06bce7c8f5743f882
resource "aws_vpc_endpoint" "vpce-06bce7c8f5743f882" {
  vpc_id            = aws_vpc.aws_vpc_public_id.id
  service_name      = "com.amazonaws.vpce.ap-southeast-2.vpce-svc-00b463612df7a3e36"
  vpc_endpoint_type = "Interface"

  subnet_ids = [
    aws_subnet.aws_subnet_public-2b_id.id,
    aws_subnet.aws_subnet_public-2c_id.id,
  ]

  security_group_ids = [
    aws_security_group.aws_security_group_rds-proxy-etime-14si-stage_id.id,
  ]

  private_dns_enabled = 

  tags = {
    Name        = "vpce-06bce7c8f5743f882"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Route Table: lifesupport-rt-public
resource "aws_route_table" "lifesupport-rt-public" {
  vpc_id = aws_vpc.aws_vpc_lifesupport_id.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw-0882e3deb7bc709f7.id
  }

  tags = {
    Name        = "lifesupport-rt-public"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

resource "aws_route_table_association" "lifesupport-rt-public_aws_subnet_lifesupport-subnet-public-ap-southeast-2c_id" {
  subnet_id      = aws_subnet.aws_subnet_lifesupport-subnet-public-ap-southeast-2c_id.id
  route_table_id = aws_route_table.lifesupport-rt-public.id
}
resource "aws_route_table_association" "lifesupport-rt-public_aws_subnet_lifesupport-subnet-public-ap-southeast-2a_id" {
  subnet_id      = aws_subnet.aws_subnet_lifesupport-subnet-public-ap-southeast-2a_id.id
  route_table_id = aws_route_table.lifesupport-rt-public.id
}
resource "aws_route_table_association" "lifesupport-rt-public_aws_subnet_lifesupport-subnet-public-ap-southeast-2b_id" {
  subnet_id      = aws_subnet.aws_subnet_lifesupport-subnet-public-ap-southeast-2b_id.id
  route_table_id = aws_route_table.lifesupport-rt-public.id
}


# Route Table: stage-rt-private-ap-southeast-2b
resource "aws_route_table" "stage-rt-private-ap-southeast-2b" {
  vpc_id = aws_vpc.aws_vpc_stage_id.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat-0a9542afdbe893546.id
  }

  tags = {
    Name        = "stage-rt-private-ap-southeast-2b"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

resource "aws_route_table_association" "stage-rt-private-ap-southeast-2b_aws_subnet_stage-subnet-private-ap-southeast-2b_id" {
  subnet_id      = aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id
  route_table_id = aws_route_table.stage-rt-private-ap-southeast-2b.id
}


# Route Table: nat-routing
resource "aws_route_table" "nat-routing" {
  vpc_id = aws_vpc.aws_vpc_public_id.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat-02553c99f9118b982.id
  }

  tags = {
    Name        = "nat-routing"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

resource "aws_route_table_association" "nat-routing_aws_subnet_private-2c_id" {
  subnet_id      = aws_subnet.aws_subnet_private-2c_id.id
  route_table_id = aws_route_table.nat-routing.id
}


# Route Table: rtb-0d883b04aae6f054a
resource "aws_route_table" "rtb-0d883b04aae6f054a" {
  vpc_id = aws_vpc.aws_vpc_lifesupport_id.id


  tags = {
    Name        = "rtb-0d883b04aae6f054a"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}



# Route Table: rtb-0f20354c71dd82588
resource "aws_route_table" "rtb-0f20354c71dd82588" {
  vpc_id = aws_vpc.aws_vpc_stage_id.id


  tags = {
    Name        = "rtb-0f20354c71dd82588"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}



# Route Table: lifesupport-rt-private-ap-southeast-2a
resource "aws_route_table" "lifesupport-rt-private-ap-southeast-2a" {
  vpc_id = aws_vpc.aws_vpc_lifesupport_id.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat-010460b85ae257df8.id
  }

  tags = {
    Name        = "lifesupport-rt-private-ap-southeast-2a"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

resource "aws_route_table_association" "lifesupport-rt-private-ap-southeast-2a_aws_subnet_lifesupport-subnet-private-ap-southeast-2a_id" {
  subnet_id      = aws_subnet.aws_subnet_lifesupport-subnet-private-ap-southeast-2a_id.id
  route_table_id = aws_route_table.lifesupport-rt-private-ap-southeast-2a.id
}


# Route Table: stage-rt-private-ap-southeast-2c
resource "aws_route_table" "stage-rt-private-ap-southeast-2c" {
  vpc_id = aws_vpc.aws_vpc_stage_id.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat-0a9542afdbe893546.id
  }

  tags = {
    Name        = "stage-rt-private-ap-southeast-2c"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

resource "aws_route_table_association" "stage-rt-private-ap-southeast-2c_aws_subnet_stage-subnet-private-ap-southeast-2c_id" {
  subnet_id      = aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id
  route_table_id = aws_route_table.stage-rt-private-ap-southeast-2c.id
}


# Route Table: lifesupport-rt-private-ap-southeast-2c
resource "aws_route_table" "lifesupport-rt-private-ap-southeast-2c" {
  vpc_id = aws_vpc.aws_vpc_lifesupport_id.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat-010460b85ae257df8.id
  }

  tags = {
    Name        = "lifesupport-rt-private-ap-southeast-2c"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

resource "aws_route_table_association" "lifesupport-rt-private-ap-southeast-2c_aws_subnet_lifesupport-subnet-private-ap-southeast-2c_id" {
  subnet_id      = aws_subnet.aws_subnet_lifesupport-subnet-private-ap-southeast-2c_id.id
  route_table_id = aws_route_table.lifesupport-rt-private-ap-southeast-2c.id
}


# Route Table: public-main
resource "aws_route_table" "public-main" {
  vpc_id = aws_vpc.aws_vpc_public_id.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw-0b5ecc6e.id
  }
  route {
    cidr_block = ""
    gateway_id = aws_internet_gateway.igw-0b5ecc6e.id
  }

  tags = {
    Name        = "public-main"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

resource "aws_route_table_association" "public-main_aws_subnet_public-2b_id" {
  subnet_id      = aws_subnet.aws_subnet_public-2b_id.id
  route_table_id = aws_route_table.public-main.id
}


# Route Table: lifesupport-rt-private-ap-southeast-2b
resource "aws_route_table" "lifesupport-rt-private-ap-southeast-2b" {
  vpc_id = aws_vpc.aws_vpc_lifesupport_id.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat-010460b85ae257df8.id
  }

  tags = {
    Name        = "lifesupport-rt-private-ap-southeast-2b"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

resource "aws_route_table_association" "lifesupport-rt-private-ap-southeast-2b_aws_subnet_lifesupport-subnet-private-ap-southeast-2b_id" {
  subnet_id      = aws_subnet.aws_subnet_lifesupport-subnet-private-ap-southeast-2b_id.id
  route_table_id = aws_route_table.lifesupport-rt-private-ap-southeast-2b.id
}


# Route Table: stage-rt-public
resource "aws_route_table" "stage-rt-public" {
  vpc_id = aws_vpc.aws_vpc_stage_id.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw-09a86850eb881c544.id
  }

  tags = {
    Name        = "stage-rt-public"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

resource "aws_route_table_association" "stage-rt-public_aws_subnet_stage-subnet-public-ap-southeast-2b_id" {
  subnet_id      = aws_subnet.aws_subnet_stage-subnet-public-ap-southeast-2b_id.id
  route_table_id = aws_route_table.stage-rt-public.id
}
resource "aws_route_table_association" "stage-rt-public_aws_subnet_stage-subnet-public-ap-southeast-2a_id" {
  subnet_id      = aws_subnet.aws_subnet_stage-subnet-public-ap-southeast-2a_id.id
  route_table_id = aws_route_table.stage-rt-public.id
}
resource "aws_route_table_association" "stage-rt-public_aws_subnet_stage-subnet-public-ap-southeast-2c_id" {
  subnet_id      = aws_subnet.aws_subnet_stage-subnet-public-ap-southeast-2c_id.id
  route_table_id = aws_route_table.stage-rt-public.id
}


# Route Table: stage-rt-private-ap-southeast-2a
resource "aws_route_table" "stage-rt-private-ap-southeast-2a" {
  vpc_id = aws_vpc.aws_vpc_stage_id.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat-0a9542afdbe893546.id
  }

  tags = {
    Name        = "stage-rt-private-ap-southeast-2a"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

resource "aws_route_table_association" "stage-rt-private-ap-southeast-2a_aws_subnet_stage-subnet-private-ap-southeast-2a_id" {
  subnet_id      = aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id
  route_table_id = aws_route_table.stage-rt-private-ap-southeast-2a.id
}
