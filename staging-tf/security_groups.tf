# Security Group: ssh
# Original ID: sg-0ea9a1c02b8ef60bd
resource "aws_security_group" "sg-0ea9a1c02b8ef60bd" {
  name        = "ssh"
  description = "SSH access from the gateway (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 22
    to_port          = 22
    security_groups  = [
"aws_security_group.sg-0ee33593e107f36f1.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 30222
    to_port          = 30222
    security_groups  = [
"aws_security_group.sg-0ee33593e107f36f1.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "ssh"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0ea9a1c02b8ef60bd"
    "Cost Center" = "stage"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: etime-14si
# Original ID: sg-06e2817ae86814235
resource "aws_security_group" "sg-06e2817ae86814235" {
  name        = "etime-14si"
  description = "etime server have this SG to expose their ports to other SGs (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    security_groups  = [
"aws_security_group.sg-0c48a0522ace9cd5f.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 0
    to_port          = 65535
    cidr_blocks      = ["192.168.248.0/21"]
    security_groups  = [
"aws_security_group.sg-06e2817ae86814235.id",
"aws_security_group.sg-0c48a0522ace9cd5f.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8080
    to_port          = 8080
    security_groups  = [
"aws_security_group.sg-0c48a0522ace9cd5f.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3000
    to_port          = 3000
    security_groups  = [
"aws_security_group.sg-0c48a0522ace9cd5f.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["172.17.0.0/16", "192.168.248.0/21"]
  }

  tags = {
    Name        = "etime-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-06e2817ae86814235"
    "Cost Center" = "etime"
    Environment = "stage"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: internal-icmp
# Original ID: sg-0ea2aca1e6a8d47fe
resource "aws_security_group" "sg-0ea2aca1e6a8d47fe" {
  name        = "internal-icmp"
  description = "Useful internal ICMP (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "icmp"
    from_port        = 3
    to_port          = -1
    cidr_blocks      = ["172.17.0.0/16"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "icmp"
    from_port        = 0
    to_port          = -1
    cidr_blocks      = ["172.17.0.0/16"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "icmp"
    from_port        = 4
    to_port          = -1
    cidr_blocks      = ["172.17.0.0/16"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "icmp"
    from_port        = 8
    to_port          = -1
    cidr_blocks      = ["172.17.0.0/16"]
  }

  tags = {
    Name        = "internal-icmp"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0ea2aca1e6a8d47fe"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: office-vpn-ssh-ingress
# Original ID: sg-04fbadfe4550c1f5a
resource "aws_security_group" "office-vpn-ssh-ingress_550c1f5a" {
  name        = "office-vpn-ssh-ingress"
  description = "Allow ingress from the Auckland office and VPN"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 22
    to_port          = 22
    cidr_blocks      = ["123.255.56.65/32", "14.1.34.16/32", "122.59.27.77/32", "3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 30222
    to_port          = 30222
    cidr_blocks      = ["123.255.56.65/32", "14.1.34.16/32", "122.59.27.77/32", "3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 587
    to_port          = 587
    cidr_blocks      = ["16.26.5.213/32"]
  }

  tags = {
    Name        = "office-vpn-ssh-ingress"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-04fbadfe4550c1f5a"
    "Cost Center" = "stage"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: bastion
# Original ID: sg-0ee33593e107f36f1
resource "aws_security_group" "sg-0ee33593e107f36f1" {
  name        = "bastion"
  description = "Bastion and SSH gateway rules (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["3.24.7.167/32", "123.255.56.65/32", "122.59.27.77/32", "14.1.34.16/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8080
    to_port          = 8080
    cidr_blocks      = ["14.1.34.16/32", "3.24.7.167/32", "123.255.56.65/32", "122.59.27.77/32", "0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 22
    to_port          = 22
    cidr_blocks      = ["14.1.34.16/32", "123.255.56.65/32", "3.24.7.167/32", "122.59.27.77/32", "203.129.27.199/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 50443
    to_port          = 50443
    cidr_blocks      = ["3.24.7.167/32", "123.255.56.65/32", "14.1.34.16/32", "122.59.27.77/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "udp"
    from_port        = 41641
    to_port          = 41641
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 9090
    to_port          = 9090
    cidr_blocks      = ["123.255.56.65/32", "14.1.34.16/32", "122.59.27.77/32", "3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 30222
    to_port          = 30222
    cidr_blocks      = ["14.1.34.16/32", "123.255.56.65/32", "122.59.27.77/32", "3.24.7.167/32", "203.49.153.35/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["122.59.27.77/32", "123.255.56.65/32", "14.1.34.16/32", "3.24.7.167/32", "0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3389
    to_port          = 3389
    cidr_blocks      = ["3.24.7.167/32", "123.255.56.65/32", "122.59.27.77/32", "14.1.34.16/32"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "bastion"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0ee33593e107f36f1"
    "Cost Center" = "stage"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: allow-elb-eodefault-ngsc
# Original ID: sg-0466bf33a2b40ed19
resource "aws_security_group" "sg-0466bf33a2b40ed19" {
  name        = "allow-elb-eodefault-ngsc"
  description = "Allow 80/443/8080/8443 ingress from ALB eodefault-ngsc to EC2 elementorg-ngsc"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8443
    to_port          = 8443
    cidr_blocks      = ["3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "allow-elb-eodefault-ngsc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0466bf33a2b40ed19"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: elementtime
# Original ID: sg-0e9d9aa5c428a5c03
resource "aws_security_group" "sg-0e9d9aa5c428a5c03" {
  name        = "elementtime"
  description = "elementtime server have this SG to expose their ports to other SGs (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    security_groups  = [
"aws_security_group.sg-0ccaad06b44bfac19.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 0
    to_port          = 65535
    security_groups  = [
"aws_security_group.sg-0ccaad06b44bfac19.id",
"aws_security_group.sg-0e9d9aa5c428a5c03.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8080
    to_port          = 8080
    security_groups  = [
"aws_security_group.sg-0ccaad06b44bfac19.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3000
    to_port          = 3000
    security_groups  = [
"aws_security_group.sg-0ccaad06b44bfac19.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["172.17.0.0/16"]
  }

  tags = {
    Name        = "elementtime"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0e9d9aa5c428a5c03"
    Environment = "stage"
    "Cost Center" = "elementtime"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: allow-elb-eodefault-ypc
# Original ID: sg-0ad7ac2979564cc3b
resource "aws_security_group" "sg-0ad7ac2979564cc3b" {
  name        = "allow-elb-eodefault-ypc"
  description = "Allow 80/443/8080/8443 ingress from ALB eodefault-ypc to EC2 elementorg-ypc"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8443
    to_port          = 8443
    cidr_blocks      = ["3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "allow-elb-eodefault-ypc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0ad7ac2979564cc3b"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: allow-elb-eodefault-test-ngsc
# Original ID: sg-0d7d46135b4284504
resource "aws_security_group" "sg-0d7d46135b4284504" {
  name        = "allow-elb-eodefault-test-ngsc"
  description = "Allow 80/443/8080/8443 ingress from ALB eodefault-test-ngsc to EC2 elementorg-test-ngsc"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8443
    to_port          = 8443
    cidr_blocks      = ["3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "allow-elb-eodefault-test-ngsc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0d7d46135b4284504"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: vpn-current
# Original ID: sg-03b61b529117d9048
resource "aws_security_group" "sg-03b61b529117d9048" {
  name        = "vpn-current"
  description = "Access from the VPN (managed)"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 4433
    to_port          = 4433
    cidr_blocks      = ["122.59.27.77/32", "123.255.56.65/32", "14.1.34.16/32", "3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "udp"
    from_port        = 1194
    to_port          = 1194
    cidr_blocks      = ["123.255.56.65/32", "14.1.34.16/32", "122.59.27.77/32", "3.24.7.167/32", "0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 1195
    to_port          = 1195
    cidr_blocks      = ["3.24.7.167/32", "123.255.56.65/32", "122.59.27.77/32", "14.1.34.16/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "udp"
    from_port        = 41641
    to_port          = 41641
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 30222
    to_port          = 30222
    cidr_blocks      = ["123.255.56.65/32", "14.1.34.16/32", "122.59.27.77/32", "3.24.7.167/32", "172.31.0.0/16"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "udp"
    from_port        = 4433
    to_port          = 4433
    cidr_blocks      = ["122.59.27.77/32", "14.1.34.16/32", "123.255.56.65/32", "3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 4343
    to_port          = 4343
    cidr_blocks      = ["123.255.56.65/32", "3.24.7.167/32", "14.1.34.16/32", "122.59.27.77/32"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "vpn-current"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-03b61b529117d9048"
    "Cost Center" = "vpn-current"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: internal-icmp-current
# Original ID: sg-09032f0c1e675cba6
resource "aws_security_group" "sg-09032f0c1e675cba6" {
  name        = "internal-icmp-current"
  description = "Useful internal ICMP (managed)"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "icmp"
    from_port        = 3
    to_port          = -1
    cidr_blocks      = ["172.31.0.0/16"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "icmp"
    from_port        = 0
    to_port          = -1
    cidr_blocks      = ["172.31.0.0/16"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "icmp"
    from_port        = 4
    to_port          = -1
    cidr_blocks      = ["172.31.0.0/16"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "icmp"
    from_port        = 8
    to_port          = -1
    cidr_blocks      = ["172.31.0.0/16"]
  }

  tags = {
    Name        = "internal-icmp-current"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-09032f0c1e675cba6"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: elementSeries_prod_vpc
# Original ID: sg-02aed57dbbcb9a592
resource "aws_security_group" "elementSeries_prod_vpc" {
  name        = "elementSeries_prod_vpc"
  description = "elementSeries security group in stage VPC"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 0
    to_port          = 10000
    cidr_blocks      = ["172.17.0.0/16", "172.31.0.0/16"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 0
    to_port          = 65535
    security_groups  = [
"aws_security_group.elementSeries_prod_vpc.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 10001
    to_port          = 30000
    cidr_blocks      = ["172.17.0.0/16", "172.31.0.0/16"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 22
    to_port          = 22
    security_groups  = [
"aws_security_group.sg-0c00b8511d60caa56.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 30001
    to_port          = 65535
    cidr_blocks      = ["172.17.0.0/16", "172.31.0.0/16"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 89
    security_groups  = [
"aws_security_group.sg-14a91872.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 30222
    to_port          = 30222
    security_groups  = [
"aws_security_group.sg-0c00b8511d60caa56.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8080
    to_port          = 8100
    security_groups  = [
"aws_security_group.sg-14a91872.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3000
    to_port          = 3100
    security_groups  = [
"aws_security_group.elementSeries_prod_vpc.id",
"aws_security_group.sg-14a91872.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "elementSeries_prod_vpc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-02aed57dbbcb9a592"
    "Cost Center" = "elementSeries"
    Environment = "stage"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: elementcentre
# Original ID: sg-0ac562a2b2761e254
resource "aws_security_group" "sg-0ac562a2b2761e254" {
  name        = "elementcentre"
  description = "elementcentre server have this SG to expose their ports to other SGs (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 0
    to_port          = 65535
    security_groups  = [
"aws_security_group.sg-0ccc2eb3cce8f3bf8.id",
"aws_security_group.sg-0ac562a2b2761e254.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 89
    security_groups  = [
"aws_security_group.sg-0ccc2eb3cce8f3bf8.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8080
    to_port          = 8100
    security_groups  = [
"aws_security_group.sg-0ccc2eb3cce8f3bf8.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3000
    to_port          = 3100
    security_groups  = [
"aws_security_group.sg-0ccc2eb3cce8f3bf8.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["172.17.0.0/16"]
  }

  tags = {
    Name        = "elementcentre"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0ac562a2b2761e254"
    Environment = "stage"
    "Cost Center" = "elementcentre"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: ec2-rds-1
# Original ID: sg-03c2af77d267b7126
resource "aws_security_group" "sg-03c2af77d267b7126" {
  name        = "ec2-rds-1"
  description = "Security group attached to instances to securely connect to postgresql-11-1. Modification could lead to connection loss."
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  egress {
    description      = "Egress rule"
    protocol         = "tcp"
    from_port        = 5432
    to_port          = 5432
  }

  tags = {
    Name        = "ec2-rds-1"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-03c2af77d267b7126"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: bastion-current
# Original ID: sg-002adf82ccd2da02d
resource "aws_security_group" "sg-002adf82ccd2da02d" {
  name        = "bastion-current"
  description = "Bastion and SSH gateway rules (managed)"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["172.31.0.0/16"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 22
    to_port          = 22
    cidr_blocks      = ["14.1.34.16/32", "123.255.56.65/32", "3.24.7.167/32", "122.59.27.77/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "udp"
    from_port        = 41641
    to_port          = 41641
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 30222
    to_port          = 30222
    cidr_blocks      = ["14.1.34.16/32", "123.255.56.65/32", "122.59.27.77/32", "3.24.7.167/32"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "bastion-current"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-002adf82ccd2da02d"
    "Cost Center" = "stage-current"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: office-vpn-ssh-ingress-current
# Original ID: sg-063875e9c747d0941
resource "aws_security_group" "office-vpn-ssh-ingress-current" {
  name        = "office-vpn-ssh-ingress-current"
  description = "Allow ingress from the Auckland office and VPN"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 22
    to_port          = 22
    cidr_blocks      = ["123.255.56.65/32", "14.1.34.16/32", "122.59.27.77/32", "3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 30222
    to_port          = 30222
    cidr_blocks      = ["123.255.56.65/32", "14.1.34.16/32", "122.59.27.77/32", "3.24.7.167/32"]
  }

  tags = {
    Name        = "office-vpn-ssh-ingress-current"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-063875e9c747d0941"
    "Cost Center" = "stage-current"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: ssh-current
# Original ID: sg-0c00b8511d60caa56
resource "aws_security_group" "sg-0c00b8511d60caa56" {
  name        = "ssh-current"
  description = "SSH access from the gateway (managed)"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 22
    to_port          = 22
    security_groups  = [
"aws_security_group.sg-002adf82ccd2da02d.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 30222
    to_port          = 30222
    security_groups  = [
"aws_security_group.sg-002adf82ccd2da02d.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "ssh-current"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0c00b8511d60caa56"
    "Cost Center" = "stage-current"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: hosting
# Original ID: sg-01430ba65e3c749aa
resource "aws_security_group" "sg-01430ba65e3c749aa" {
  name        = "hosting"
  description = "hosting"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 2083
    to_port          = 2083
    cidr_blocks      = ["14.1.34.16/32", "3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    security_groups  = [
"aws_security_group.sg-05ca6d63.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 22
    to_port          = 22
    cidr_blocks      = ["14.200.37.190/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 19999
    to_port          = 19999
    cidr_blocks      = ["104.20.22.2/32", "172.66.170.216/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    security_groups  = [
"aws_security_group.sg-0ebf9170b06104b03.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 2087
    to_port          = 2087
    cidr_blocks      = ["14.1.34.16/32", "3.24.7.167/32"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "hosting"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-01430ba65e3c749aa"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: allow-elb-eodefault-test-ypc
# Original ID: sg-0d03d0d0d4b1857a2
resource "aws_security_group" "sg-0d03d0d0d4b1857a2" {
  name        = "allow-elb-eodefault-test-ypc"
  description = "Allow 80/443/8080/8443 ingress from ALB eodefault-test-ypc to EC2 elementorg-test-ypc"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8443
    to_port          = 8443
    cidr_blocks      = ["3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "allow-elb-eodefault-test-ypc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0d03d0d0d4b1857a2"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: elementsup
# Original ID: sg-0d4ca909ae44ef9a4
resource "aws_security_group" "sg-0d4ca909ae44ef9a4" {
  name        = "elementsup"
  description = "elementsup server have this SG to expose their ports to other SGs (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 0
    to_port          = 65535
    security_groups  = [
"aws_security_group.sg-0732fc93ae6bed8f8.id",
"aws_security_group.sg-0d4ca909ae44ef9a4.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 89
    security_groups  = [
"aws_security_group.sg-0732fc93ae6bed8f8.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8080
    to_port          = 8100
    security_groups  = [
"aws_security_group.sg-0732fc93ae6bed8f8.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3000
    to_port          = 3100
    security_groups  = [
"aws_security_group.sg-0732fc93ae6bed8f8.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["172.17.0.0/16"]
  }

  tags = {
    Name        = "elementsup"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0d4ca909ae44ef9a4"
    "Cost Center" = "elementsup"
    Environment = "stage"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: test
# Original ID: sg-0577c665d2185f61e
resource "aws_security_group" "sg-0577c665d2185f61e" {
  name        = "test"
  description = "test servers"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    security_groups  = [
"aws_security_group.sg-14a91872.id",
"aws_security_group.sg-05ca6d63.id",
    ]
  }

  tags = {
    Name        = "test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0577c665d2185f61e"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: TempAccessToProRDS
# Original ID: sg-0c3996e514e9d6196
resource "aws_security_group" "sg-0c3996e514e9d6196" {
  name        = "TempAccessToProRDS"
  description = "TempAccessToProRDS"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  tags = {
    Name        = "TempAccessToProRDS"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0c3996e514e9d6196"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: test-db
# Original ID: sg-022cca1d7ed3a7a0a
resource "aws_security_group" "sg-022cca1d7ed3a7a0a" {
  name        = "test-db"
  description = "dbs for testing"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 5432
    to_port          = 5432
    security_groups  = [
"aws_security_group.sg-0577c665d2185f61e.id",
"aws_security_group.sg-0b21ee2705bb5a01d.id",
"aws_security_group.elementSeries.id",
"aws_security_group.sg-0ebf9170b06104b03.id",
"aws_security_group.sg-0f213d73676a37994.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["172.31.39.30/32"]
    security_groups  = [
"aws_security_group.sg-05ca6d63.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 22
    to_port          = 22
    security_groups  = [
"aws_security_group.sg-0577c665d2185f61e.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    security_groups  = [
"aws_security_group.sg-0577c665d2185f61e.id",
"aws_security_group.sg-0b21ee2705bb5a01d.id",
"aws_security_group.sg-0ebf9170b06104b03.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "test-db"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-022cca1d7ed3a7a0a"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: webserver
# Original ID: sg-0b21ee2705bb5a01d
resource "aws_security_group" "sg-0b21ee2705bb5a01d" {
  name        = "webserver"
  description = "open 80 and 443"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 0
    to_port          = 65535
    security_groups  = [
"aws_security_group.sg-0b21ee2705bb5a01d.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "webserver"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0b21ee2705bb5a01d"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: elementSeries
# Original ID: sg-901037f7
resource "aws_security_group" "elementSeries" {
  name        = "elementSeries"
  description = "elementSeries Servers"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 0
    to_port          = 65535
    cidr_blocks      = ["172.31.0.0/16"]
    security_groups  = [
"aws_security_group.sg-05ca6d63.id",
"aws_security_group.elementSeries.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 22
    to_port          = 22
    security_groups  = [
"aws_security_group.sg-0c00b8511d60caa56.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 89
    security_groups  = [
"aws_security_group.sg-14a91872.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 30222
    to_port          = 30222
    security_groups  = [
"aws_security_group.sg-0c00b8511d60caa56.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8080
    to_port          = 8100
    security_groups  = [
"aws_security_group.sg-14a91872.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "udp"
    from_port        = 0
    to_port          = 65535
    security_groups  = [
"aws_security_group.sg-05ca6d63.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3000
    to_port          = 3100
    security_groups  = [
"aws_security_group.sg-14a91872.id",
"aws_security_group.elementSeries.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "elementSeries"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-901037f7"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: elementstaff
# Original ID: sg-02c028c79d15adf86
resource "aws_security_group" "sg-02c028c79d15adf86" {
  name        = "elementstaff"
  description = "elementstaff server have this SG to expose their ports to other SGs (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 0
    to_port          = 65535
    security_groups  = [
"aws_security_group.sg-0a1b0deb59dc518b8.id",
"aws_security_group.sg-02c028c79d15adf86.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 89
    security_groups  = [
"aws_security_group.sg-0a1b0deb59dc518b8.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8080
    to_port          = 8100
    security_groups  = [
"aws_security_group.sg-0a1b0deb59dc518b8.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3000
    to_port          = 3100
    security_groups  = [
"aws_security_group.sg-0a1b0deb59dc518b8.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["172.17.0.0/16"]
  }

  tags = {
    Name        = "elementstaff"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-02c028c79d15adf86"
    "Cost Center" = "elementstaff"
    Environment = "stage"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: ghostrpc
# Original ID: sg-0e2e9a590c75ed9fe
resource "aws_security_group" "sg-0e2e9a590c75ed9fe" {
  name        = "ghostrpc"
  description = "ghostrpc server have this SG to expose their ports to other SGs (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 0
    to_port          = 65535
    security_groups  = [
"aws_security_group.sg-0e006c6c7bed45756.id",
"aws_security_group.sg-0e2e9a590c75ed9fe.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 89
    security_groups  = [
"aws_security_group.sg-0e006c6c7bed45756.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8080
    to_port          = 8100
    security_groups  = [
"aws_security_group.sg-0e006c6c7bed45756.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3000
    to_port          = 3100
    security_groups  = [
"aws_security_group.sg-0e006c6c7bed45756.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["172.17.0.0/16"]
  }

  tags = {
    Name        = "ghostrpc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0e2e9a590c75ed9fe"
    Environment = "stage"
    "Cost Center" = "ghostrpc"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: allow-elb-eodefault-test-griffith
# Original ID: sg-0856f781bc6a82376
resource "aws_security_group" "sg-0856f781bc6a82376" {
  name        = "allow-elb-eodefault-test-griffith"
  description = "Allow 80/443/8080/8443 ingress from ALB eodefault-test-griffith to EC2 elementorg-test-griffith"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8443
    to_port          = 8443
    cidr_blocks      = ["3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "allow-elb-eodefault-test-griffith"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0856f781bc6a82376"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: allow-elb-eodefault-griffith
# Original ID: sg-05e1cde8f7af63483
resource "aws_security_group" "sg-05e1cde8f7af63483" {
  name        = "allow-elb-eodefault-griffith"
  description = "Allow 80/443/8080/8443 ingress from ALB eodefault-griffith to EC2 elementorg-griffith"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8443
    to_port          = 8443
    cidr_blocks      = ["3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "allow-elb-eodefault-griffith"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-05e1cde8f7af63483"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: allow-elb-eodefault-sa-fires
# Original ID: sg-0d8fca21c227c3464
resource "aws_security_group" "sg-0d8fca21c227c3464" {
  name        = "allow-elb-eodefault-sa-fires"
  description = "Allow 80/443/8080/8443 ingress from ALB eodefault-sa-fires to EC2 elementorg-sa-fires"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8443
    to_port          = 8443
    cidr_blocks      = ["3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "allow-elb-eodefault-sa-fires"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0d8fca21c227c3464"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: allow-elb-eodefault-leeton-sandbox
# Original ID: sg-0960763e74d2494ee
resource "aws_security_group" "sg-0960763e74d2494ee" {
  name        = "allow-elb-eodefault-leeton-sandbox"
  description = "Allow 80/443/8080/8443 ingress from ALB eodefault-leeton-sandbox to EC2 elementorg-leeton-sandbox"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8443
    to_port          = 8443
    cidr_blocks      = ["3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "allow-elb-eodefault-leeton-sandbox"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0960763e74d2494ee"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: InternalSystems
# Original ID: sg-0ebf9170b06104b03
resource "aws_security_group" "sg-0ebf9170b06104b03" {
  name        = "InternalSystems"
  description = "InternalSystems"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    security_groups  = [
"aws_security_group.sg-05ca6d63.id",
"aws_security_group.sg-14a91872.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "InternalSystems"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0ebf9170b06104b03"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: allow-elb-eodefault-leeton
# Original ID: sg-07f567a32cb484323
resource "aws_security_group" "sg-07f567a32cb484323" {
  name        = "allow-elb-eodefault-leeton"
  description = "Allow 80/443/8080/8443 ingress from ALB eodefault-leeton to EC2 elementorg-leeton"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8443
    to_port          = 8443
    cidr_blocks      = ["3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "allow-elb-eodefault-leeton"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-07f567a32cb484323"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: elementrec
# Original ID: sg-0b433a6d6c584ef79
resource "aws_security_group" "sg-0b433a6d6c584ef79" {
  name        = "elementrec"
  description = "elementrec server have this SG to expose their ports to other SGs (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 0
    to_port          = 65535
    security_groups  = [
"aws_security_group.sg-03b68e085e90f0b6f.id",
"aws_security_group.sg-0b433a6d6c584ef79.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 89
    security_groups  = [
"aws_security_group.sg-03b68e085e90f0b6f.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8080
    to_port          = 8100
    security_groups  = [
"aws_security_group.sg-03b68e085e90f0b6f.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3000
    to_port          = 3100
    security_groups  = [
"aws_security_group.sg-03b68e085e90f0b6f.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["172.17.0.0/16"]
  }

  tags = {
    Name        = "elementrec"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0b433a6d6c584ef79"
    Environment = "stage"
    "Cost Center" = "elementrec"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: etime-elb-14si
# Original ID: sg-0c48a0522ace9cd5f
resource "aws_security_group" "sg-0c48a0522ace9cd5f" {
  name        = "etime-elb-14si"
  description = "Elastic Load Balancer for etime (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "etime-elb-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0c48a0522ace9cd5f"
    "Cost Center" = "etime"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: elementtime-elb
# Original ID: sg-0ccaad06b44bfac19
resource "aws_security_group" "sg-0ccaad06b44bfac19" {
  name        = "elementtime-elb"
  description = "Elastic Load Balancer for elementtime (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "elementtime-elb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0ccaad06b44bfac19"
    "Cost Center" = "elementtime"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: eodefault-sa-redirect-elb
# Original ID: sg-00fdbb40e90bd913c
resource "aws_security_group" "sg-00fdbb40e90bd913c" {
  name        = "eodefault-sa-redirect-elb"
  description = "Elastic Load Balancer for elementorg-sa-fires (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8443
    to_port          = 8443
    cidr_blocks      = ["3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "eodefault-sa-redirect-elb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-00fdbb40e90bd913c"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: eodefault-test-griffith-elb
# Original ID: sg-0014ac18168dfb556
resource "aws_security_group" "sg-0014ac18168dfb556" {
  name        = "eodefault-test-griffith-elb"
  description = "Elastic Load Balancer for elementorg-test-griffith (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8443
    to_port          = 8443
    cidr_blocks      = ["3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "eodefault-test-griffith-elb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0014ac18168dfb556"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: eodefault-griffith-elb
# Original ID: sg-03fa52cbe64ec7a1d
resource "aws_security_group" "sg-03fa52cbe64ec7a1d" {
  name        = "eodefault-griffith-elb"
  description = "Elastic Load Balancer for elementorg-griffith (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8443
    to_port          = 8443
    cidr_blocks      = ["3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "eodefault-griffith-elb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-03fa52cbe64ec7a1d"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: eodefault-test-ngsc-elb
# Original ID: sg-093f297aca654df37
resource "aws_security_group" "sg-093f297aca654df37" {
  name        = "eodefault-test-ngsc-elb"
  description = "Elastic Load Balancer for elementorg-test-ngsc (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8443
    to_port          = 8443
    cidr_blocks      = ["3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "eodefault-test-ngsc-elb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-093f297aca654df37"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: eodefault-leeton-elb
# Original ID: sg-02f52c777d84da01b
resource "aws_security_group" "sg-02f52c777d84da01b" {
  name        = "eodefault-leeton-elb"
  description = "Elastic Load Balancer for elementorg-leeton (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8443
    to_port          = 8443
    cidr_blocks      = ["3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "eodefault-leeton-elb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-02f52c777d84da01b"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: eodefault-ngsc-elb
# Original ID: sg-0271ca4f3afee1604
resource "aws_security_group" "sg-0271ca4f3afee1604" {
  name        = "eodefault-ngsc-elb"
  description = "Elastic Load Balancer for elementorg-ngsc (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8443
    to_port          = 8443
    cidr_blocks      = ["3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "eodefault-ngsc-elb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0271ca4f3afee1604"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: eodefault-test-ypc-elb
# Original ID: sg-0912b5ed29155af6c
resource "aws_security_group" "sg-0912b5ed29155af6c" {
  name        = "eodefault-test-ypc-elb"
  description = "Elastic Load Balancer for elementorg-test-ypc (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8443
    to_port          = 8443
    cidr_blocks      = ["3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "eodefault-test-ypc-elb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0912b5ed29155af6c"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: eodefault-ypc-elb
# Original ID: sg-064dd8e412e058b6d
resource "aws_security_group" "sg-064dd8e412e058b6d" {
  name        = "eodefault-ypc-elb"
  description = "Elastic Load Balancer for elementorg-ypc (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8443
    to_port          = 8443
    cidr_blocks      = ["3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "eodefault-ypc-elb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-064dd8e412e058b6d"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: elementstaff-elb
# Original ID: sg-0a1b0deb59dc518b8
resource "aws_security_group" "sg-0a1b0deb59dc518b8" {
  name        = "elementstaff-elb"
  description = "Elastic Load Balancer for elementstaff (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["172.17.0.0/16"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["172.17.0.0/16"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "elementstaff-elb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0a1b0deb59dc518b8"
    "Cost Center" = "elementstaff"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: elementrec-elb
# Original ID: sg-03b68e085e90f0b6f
resource "aws_security_group" "sg-03b68e085e90f0b6f" {
  name        = "elementrec-elb"
  description = "Elastic Load Balancer for elementrec (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "elementrec-elb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-03b68e085e90f0b6f"
    "Cost Center" = "elementrec"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: elementcentre-elb
# Original ID: sg-0ccc2eb3cce8f3bf8
resource "aws_security_group" "sg-0ccc2eb3cce8f3bf8" {
  name        = "elementcentre-elb"
  description = "Elastic Load Balancer for elementcentre (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "elementcentre-elb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0ccc2eb3cce8f3bf8"
    "Cost Center" = "elementcentre"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: ghostrpc-elb
# Original ID: sg-0e006c6c7bed45756
resource "aws_security_group" "sg-0e006c6c7bed45756" {
  name        = "ghostrpc-elb"
  description = "Elastic Load Balancer for ghostrpc (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "ghostrpc-elb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0e006c6c7bed45756"
    "Cost Center" = "ghostrpc"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: elementsup-elb
# Original ID: sg-0732fc93ae6bed8f8
resource "aws_security_group" "sg-0732fc93ae6bed8f8" {
  name        = "elementsup-elb"
  description = "Elastic Load Balancer for elementsup (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "elementsup-elb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0732fc93ae6bed8f8"
    "Cost Center" = "elementsup"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: eodefault-sa-fires-elb
# Original ID: sg-08e1289231dfb6455
resource "aws_security_group" "sg-08e1289231dfb6455" {
  name        = "eodefault-sa-fires-elb"
  description = "Elastic Load Balancer for elementorg-sa-fires (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8443
    to_port          = 8443
    cidr_blocks      = ["3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "eodefault-sa-fires-elb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-08e1289231dfb6455"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: eodefault-leeton-sandbox-elb
# Original ID: sg-0e4af2ca20429ee9b
resource "aws_security_group" "sg-0e4af2ca20429ee9b" {
  name        = "eodefault-leeton-sandbox-elb"
  description = "Elastic Load Balancer for elementorg-leeton-sandbox (managed)"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8443
    to_port          = 8443
    cidr_blocks      = ["3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "eodefault-leeton-sandbox-elb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0e4af2ca20429ee9b"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: LB
# Original ID: sg-14a91872
resource "aws_security_group" "sg-14a91872" {
  name        = "LB"
  description = "LoadBalancers"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3000
    to_port          = 3000
    cidr_blocks      = ["172.31.19.135/32"]
    security_groups  = [
"aws_security_group.elementSeries.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3000
    to_port          = 3100
    cidr_blocks      = ["172.31.0.0/16"]
    security_groups  = [
"aws_security_group.elementSeries.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "LB"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-14a91872"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: test-etime-14si--_7dK-20240412055414270400000001
# Original ID: sg-0d1b498e4647df162
resource "aws_security_group" "test-etime-14si" {
  name        = "test-etime-14si--_7dK-20240412055414270400000001"
  description = "Security group for Elasticache Redis"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 6379
    to_port          = 6379
    security_groups  = [
"aws_security_group.sg-0ea9a1c02b8ef60bd.id",
"aws_security_group.sg-06e2817ae86814235.id",
"aws_security_group.sg-0ee33593e107f36f1.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "test-etime-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0d1b498e4647df162"
    Stage = "test"
    Attributes = "14si"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: test-elementtime--NyH9-20250724230519446900000001
# Original ID: sg-09f00f03771e66e44
resource "aws_security_group" "test-elementtime" {
  name        = "test-elementtime--NyH9-20250724230519446900000001"
  description = "Security group for Elasticache Redis"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 6379
    to_port          = 6379
    security_groups  = [
"aws_security_group.sg-0e9d9aa5c428a5c03.id",
"aws_security_group.sg-0ee33593e107f36f1.id",
"aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "test-elementtime"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-09f00f03771e66e44"
    Stage = "test"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: stage-etime-14si--0_e7-20240412071246611100000002
# Original ID: sg-0ae7324c64854b6c6
resource "aws_security_group" "stage-etime-14si" {
  name        = "stage-etime-14si--0_e7-20240412071246611100000002"
  description = "Security group for Elasticache Redis"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 6379
    to_port          = 6379
    security_groups  = [
"aws_security_group.sg-0ee33593e107f36f1.id",
"aws_security_group.sg-0ea9a1c02b8ef60bd.id",
"aws_security_group.sg-06e2817ae86814235.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "stage-etime-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0ae7324c64854b6c6"
    Attributes = "14si"
    Stage = "stage"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: stage-etime-14si--Jpox-20240412071246599800000001
# Original ID: sg-0975dde06babb513c
resource "aws_security_group" "stage-etime-14si_babb513c" {
  name        = "stage-etime-14si--Jpox-20240412071246599800000001"
  description = "Security group for Elasticache Redis"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 6379
    to_port          = 6379
    security_groups  = [
"aws_security_group.sg-06e2817ae86814235.id",
"aws_security_group.sg-0ea9a1c02b8ef60bd.id",
"aws_security_group.sg-0ee33593e107f36f1.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "stage-etime-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0975dde06babb513c"
    Attributes = "14si"
    Stage = "stage"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: stage-esup--rK6I-20250429224917268000000002
# Original ID: sg-08b9a2868b3a00bf4
resource "aws_security_group" "stage-esup" {
  name        = "stage-esup--rK6I-20250429224917268000000002"
  description = "Security group for Elasticache Redis"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 6379
    to_port          = 6379
    security_groups  = [
"aws_security_group.sg-0d4ca909ae44ef9a4.id",
"aws_security_group.sg-0ea9a1c02b8ef60bd.id",
"aws_security_group.sg-0ee33593e107f36f1.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "stage-esup"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-08b9a2868b3a00bf4"
    Stage = "stage"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: stage-ecentre--f53U-20250428054210387300000002
# Original ID: sg-079312bac3dbeb860
resource "aws_security_group" "stage-ecentre" {
  name        = "stage-ecentre--f53U-20250428054210387300000002"
  description = "Security group for Elasticache Redis"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 6379
    to_port          = 6379
    security_groups  = [
"aws_security_group.sg-0ee33593e107f36f1.id",
"aws_security_group.sg-0ac562a2b2761e254.id",
"aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "stage-ecentre"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-079312bac3dbeb860"
    Stage = "stage"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: default-sg-public-vpc
# Original ID: sg-0b914bf14337d2ac1
resource "aws_security_group" "sg-0b914bf14337d2ac1" {
  name        = "default-sg-public-vpc"
  description = "SOC - copy from default sg in public vpc"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 32768
    to_port          = 65535
    cidr_blocks      = ["172.31.0.0/16"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["172.31.0.0/16"]
    security_groups  = [
"aws_security_group.sg-5036b934.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 6379
    to_port          = 6379
    cidr_blocks      = ["172.31.0.0/16", "172.17.0.0/16"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "default-sg-public-vpc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0b914bf14337d2ac1"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: elementsup-redis-inbound
# Original ID: sg-0dad917659c54babb
resource "aws_security_group" "elementsup-redis" {
  name        = "elementsup-redis-inbound"
  description = "Allow inbound traffic to redis nodes (managed)"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 6379
    to_port          = 6379
    cidr_blocks      = ["172.17.0.0/16"]
    security_groups  = [
"aws_security_group.sg-5036b934.id",
"aws_security_group.elementsup-redis.id",
    ]
  }

  tags = {
    Name        = "elementsup-redis"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0dad917659c54babb"
    "Project Service" = "elementSUP"
    "Project Team" = "elementSUP"
    "Cost Center" = "elementSUP"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: elementcentre-redis-inbound
# Original ID: sg-06da90e19036e4f57
resource "aws_security_group" "elementcentre-redis" {
  name        = "elementcentre-redis-inbound"
  description = "Allow inbound traffic to redis nodes (managed)"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 6379
    to_port          = 6379
    cidr_blocks      = ["172.17.0.0/16"]
    security_groups  = [
"aws_security_group.sg-5036b934.id",
"aws_security_group.elementcentre-redis.id",
    ]
  }

  tags = {
    Name        = "elementcentre-redis"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-06da90e19036e4f57"
    "Project Team" = "elementCentre"
    "Project Service" = "elementCentre"
    "Cost Center" = "elementCentre"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: test-docdb-etime
# Original ID: sg-03b663805aac0bbd2
resource "aws_security_group" "test-docdb-etime" {
  name        = "test-docdb-etime"
  description = "Security Group for DocumentDB cluster"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 27017
    to_port          = 27017
    cidr_blocks      = ["172.17.0.0/16", "172.19.0.0/16", "172.31.0.0/16"]
    security_groups  = [
"aws_security_group.sg-0ee33593e107f36f1.id",
"aws_security_group.sg-002adf82ccd2da02d.id",
"sg-07471ea55cb8641c2",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "test-docdb-etime"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-03b663805aac0bbd2"
    "Project Team" = "elementTIME"
    "Project Service" = "elementTIME"
    Terraform = "true"
    Environment = "stage"
    "Cost Center" = "elementTIME"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: et_test_db
# Original ID: sg-0fe556df8fc268379
resource "aws_security_group" "sg-0fe556df8fc268379" {
  name        = "et_test_db"
  description = "Allow client connect to test db"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 0
    to_port          = 65535
    security_groups  = [
"aws_security_group.sg-0ebf9170b06104b03.id",
"aws_security_group.elementSeries.id",
"aws_security_group.sg-05ca6d63.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["172.17.0.0/16"]
    security_groups  = [
"aws_security_group.sg-0577c665d2185f61e.id",
"aws_security_group.sg-002adf82ccd2da02d.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "et_test_db"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0fe556df8fc268379"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: et_db
# Original ID: sg-945d70f3
resource "aws_security_group" "db" {
  name        = "et_db"
  description = "elementtime staging db"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 0
    to_port          = 65535
    security_groups  = [
"aws_security_group.sg-05ca6d63.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 5432
    to_port          = 5432
    cidr_blocks      = ["172.17.0.0/16"]
    security_groups  = [
"aws_security_group.sg-0c3996e514e9d6196.id",
"aws_security_group.sg-0ebf9170b06104b03.id",
"aws_security_group.elementSeries.id",
"aws_security_group.sg-002adf82ccd2da02d.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["172.17.0.0/16"]
    security_groups  = [
"aws_security_group.sg-0c3996e514e9d6196.id",
"aws_security_group.sg-0ebf9170b06104b03.id",
"aws_security_group.elementSeries.id",
"aws_security_group.sg-002adf82ccd2da02d.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "db"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-945d70f3"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: rds-ec2-1
# Original ID: sg-0f213d73676a37994
resource "aws_security_group" "sg-0f213d73676a37994" {
  name        = "rds-ec2-1"
  description = "Security group attached to postgresql-11-1 to allow EC2 instances with specific security groups attached to connect to the database. Modification could lead to connection loss."
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 5432
    to_port          = 5432
    security_groups  = [
"aws_security_group.sg-03c2af77d267b7126.id",
    ]
  }

  tags = {
    Name        = "rds-ec2-1"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0f213d73676a37994"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: etime-14si-test-20240508011930201500000001
# Original ID: sg-0ded09f8ba9fec34b
resource "aws_security_group" "etime-14si-test" {
  name        = "etime-14si-test-20240508011930201500000001"
  description = "Control traffic to/from RDS Aurora etime-14si-test"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  tags = {
    Name        = "etime-14si-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0ded09f8ba9fec34b"
    "Cost Center" = "elementTIME"
    MakeSnapshotShortTerm = "True"
    "Project Team" = "elementTIME"
    env_version = "14si"
    Env = "test"
    "Project Service" = "elementTIME"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: rds-etime-14si-test
# Original ID: sg-0e726a762eaf56142
resource "aws_security_group" "etime-14si-test_eaf56142" {
  name        = "rds-etime-14si-test"
  description = "Allow traffic to eTIME RDS - etime-14si-test"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["172.31.0.0/16"]
  }

  tags = {
    Name        = "etime-14si-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0e726a762eaf56142"
    env_version = "14si"
    MakeSnapshotShortTerm = "True"
    "Project Service" = "elementTIME"
    "Project Team" = "elementTIME"
    "Cost Center" = "elementTIME"
    Env = "test"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: etime-14si-stage-20241013222422354200000001
# Original ID: sg-03dc619cb7ca6c3a4
resource "aws_security_group" "etime-14si-stage_7ca6c3a4" {
  name        = "etime-14si-stage-20241013222422354200000001"
  description = "Control traffic to/from RDS Aurora etime-14si-stage"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  tags = {
    Name        = "etime-14si-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-03dc619cb7ca6c3a4"
    "Project Service" = "elementTIME"
    Env = "stage"
    MakeSnapshotShortTerm = "True"
    "Project Team" = "elementTIME"
    "Cost Center" = "elementTIME"
    env_version = "14si"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: rds-etime-14si-stage
# Original ID: sg-0df5113198d2e8269
resource "aws_security_group" "etime-14si-stage_8d2e8269" {
  name        = "rds-etime-14si-stage"
  description = "Allow traffic to eTIME RDS - etime-14si-stage"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["172.31.0.0/16"]
  }

  tags = {
    Name        = "etime-14si-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0df5113198d2e8269"
    "Cost Center" = "elementTIME"
    Env = "stage"
    "Project Service" = "elementTIME"
    MakeSnapshotShortTerm = "True"
    "Project Team" = "elementTIME"
    env_version = "14si"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: rds-etime-14si-stage
# Original ID: sg-072c65dfd31d69b92
resource "aws_security_group" "etime-14si-stage" {
  name        = "rds-etime-14si-stage"
  description = "Allow traffic to eTIME RDS - etime-14si-stage"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["172.31.0.0/16"]
  }

  tags = {
    Name        = "etime-14si-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-072c65dfd31d69b92"
    MakeSnapshotShortTerm = "True"
    "Project Service" = "elementTIME"
    "Cost Center" = "elementTIME"
    env_version = "14si"
    "Project Team" = "elementTIME"
    Env = "stage"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: etime-14si-stage-20250723232925777800000001
# Original ID: sg-07b8f1345eb956446
resource "aws_security_group" "etime-14si-stage_eb956446" {
  name        = "etime-14si-stage-20250723232925777800000001"
  description = "Control traffic to/from RDS Aurora etime-14si-stage"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  tags = {
    Name        = "etime-14si-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-07b8f1345eb956446"
    "Cost Center" = "elementTIME"
    Env = "stage"
    "Project Service" = "elementTIME"
    env_version = "14si"
    "Project Team" = "elementTIME"
    MakeSnapshotShortTerm = "True"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: esup-stage-20250429102648744900000002
# Original ID: sg-01c1aee0790a145cc
resource "aws_security_group" "esup-stage_90a145cc" {
  name        = "esup-stage-20250429102648744900000002"
  description = "Control traffic to/from RDS Aurora esup-stage"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  tags = {
    Name        = "esup-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-01c1aee0790a145cc"
    "Cost Center" = "elementSUP"
    "Project Team" = "elementSUP"
    Env = "stage"
    "Project Service" = "elementSUP"
    MakeSnapshotShortTerm = "True"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: rds-esup-stage-20250429102648739700000001
# Original ID: sg-0048d16be98a34290
resource "aws_security_group" "esup-stage" {
  name        = "rds-esup-stage-20250429102648739700000001"
  description = "Allow traffic to eSUP RDS - esup-stage"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["172.17.0.0/16", "172.31.0.0/16"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "esup-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0048d16be98a34290"
    MakeSnapshotShortTerm = "True"
    "Project Team" = "elementSUP"
    "Cost Center" = "elementSUP"
    "Project Service" = "elementSUP"
    Env = "stage"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: eorg-ypc-test-20240926032759668900000001
# Original ID: sg-0f98e30cfdac4d7c2
resource "aws_security_group" "eorg-ypc-test" {
  name        = "eorg-ypc-test-20240926032759668900000001"
  description = "Control traffic to/from RDS Aurora eorg-ypc-test"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  tags = {
    Name        = "eorg-ypc-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0f98e30cfdac4d7c2"
    MakeSnapshotShortTerm = "True"
    "Cost Center" = "elementOrg"
    "Project Team" = "elementOrg"
    Env = "test"
    "Project Service" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: rds-eorg-ypc-test
# Original ID: sg-053fb515dcd590236
resource "aws_security_group" "eorg-ypc-test_cd590236" {
  name        = "rds-eorg-ypc-test"
  description = "Allow traffic to eOrg YPC RDS - eorg-ypc-test"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["172.17.0.0/16"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "eorg-ypc-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-053fb515dcd590236"
    MakeSnapshotShortTerm = "True"
    "Project Service" = "elementOrg"
    "Cost Center" = "elementOrg"
    Env = "test"
    "Project Team" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: rds-eorg-ypc-stage
# Original ID: sg-077931d1010b9f94d
resource "aws_security_group" "eorg-ypc-stage" {
  name        = "rds-eorg-ypc-stage"
  description = "Allow traffic to eOrg YPC RDS - eorg-ypc-stage"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["172.17.0.0/16"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "eorg-ypc-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-077931d1010b9f94d"
    "Project Service" = "elementOrg"
    Env = "stage"
    "Project Team" = "elementOrg"
    "Cost Center" = "elementOrg"
    MakeSnapshotShortTerm = "True"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: eorg-ypc-stage-20241105020308771700000001
# Original ID: sg-0be20e0edbcdc60b1
resource "aws_security_group" "eorg-ypc-stage_bcdc60b1" {
  name        = "eorg-ypc-stage-20241105020308771700000001"
  description = "Control traffic to/from RDS Aurora eorg-ypc-stage"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  tags = {
    Name        = "eorg-ypc-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0be20e0edbcdc60b1"
    MakeSnapshotShortTerm = "True"
    "Cost Center" = "elementOrg"
    "Project Team" = "elementOrg"
    "Project Service" = "elementOrg"
    Env = "stage"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: rds-eorg-ngsc-test-trellis
# Original ID: sg-051e254bf096f48db
resource "aws_security_group" "eorg-ngsc-test-trellis_096f48db" {
  name        = "rds-eorg-ngsc-test-trellis"
  description = "Allow traffic to eOrg NGSC RDS - eorg-ngsc-test-trellis"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["172.17.0.0/16"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "eorg-ngsc-test-trellis"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-051e254bf096f48db"
    "Cost Center" = "elementOrg"
    MakeSnapshotShortTerm = "True"
    "Project Service" = "elementOrg"
    "Project Team" = "elementOrg"
    Env = "test-trellis"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: eorg-ngsc-test-trellis-20241017221924816100000001
# Original ID: sg-036bd86cb4adf9841
resource "aws_security_group" "eorg-ngsc-test-trellis" {
  name        = "eorg-ngsc-test-trellis-20241017221924816100000001"
  description = "Control traffic to/from RDS Aurora eorg-ngsc-test-trellis"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  tags = {
    Name        = "eorg-ngsc-test-trellis"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-036bd86cb4adf9841"
    "Project Team" = "elementOrg"
    "Cost Center" = "elementOrg"
    MakeSnapshotShortTerm = "True"
    "Project Service" = "elementOrg"
    Env = "test-trellis"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: rds-eorg-ngsc-test
# Original ID: sg-000aca7efd1e38477
resource "aws_security_group" "eorg-ngsc-test_d1e38477" {
  name        = "rds-eorg-ngsc-test"
  description = "Allow traffic to eOrg NGSC RDS - eorg-ngsc-test"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["172.17.0.0/16"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "eorg-ngsc-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-000aca7efd1e38477"
    MakeSnapshotShortTerm = "True"
    "Project Team" = "elementOrg"
    Env = "test"
    "Cost Center" = "elementOrg"
    "Project Service" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: eorg-ngsc-test-20240612003113905200000001
# Original ID: sg-0ae5f7ad5fbe64444
resource "aws_security_group" "eorg-ngsc-test" {
  name        = "eorg-ngsc-test-20240612003113905200000001"
  description = "Control traffic to/from RDS Aurora eorg-ngsc-test"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  tags = {
    Name        = "eorg-ngsc-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0ae5f7ad5fbe64444"
    "Cost Center" = "elementOrg"
    MakeSnapshotShortTerm = "True"
    "Project Service" = "elementOrg"
    Env = "test"
    "Project Team" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: eorg-ngsc-stage-20240716215342031800000001
# Original ID: sg-08df1de5f3d6d7657
resource "aws_security_group" "eorg-ngsc-stage" {
  name        = "eorg-ngsc-stage-20240716215342031800000001"
  description = "Control traffic to/from RDS Aurora eorg-ngsc-stage"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  tags = {
    Name        = "eorg-ngsc-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-08df1de5f3d6d7657"
    "Project Service" = "elementOrg"
    MakeSnapshotShortTerm = "True"
    Env = "stage"
    "Project Team" = "elementOrg"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: rds-eorg-ngsc-stage
# Original ID: sg-01c689ab4621168df
resource "aws_security_group" "eorg-ngsc-stage_621168df" {
  name        = "rds-eorg-ngsc-stage"
  description = "Allow traffic to eOrg NGSC RDS - eorg-ngsc-stage"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["172.17.0.0/16"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "eorg-ngsc-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-01c689ab4621168df"
    MakeSnapshotShortTerm = "True"
    "Cost Center" = "elementOrg"
    Env = "stage"
    "Project Service" = "elementOrg"
    "Project Team" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: eorg-leeton-sandbox-20240710043401409200000001
# Original ID: sg-08b6d7198f3e0d68a
resource "aws_security_group" "eorg-leeton-sandbox_f3e0d68a" {
  name        = "eorg-leeton-sandbox-20240710043401409200000001"
  description = "Control traffic to/from RDS Aurora eorg-leeton-sandbox"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  tags = {
    Name        = "eorg-leeton-sandbox"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-08b6d7198f3e0d68a"
    Env = "sandbox"
    MakeSnapshotShortTerm = "True"
    "Project Service" = "elementOrg"
    "Project Team" = "elementOrg"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: rds-eorg-leeton-sandbox
# Original ID: sg-068cbc49449419a08
resource "aws_security_group" "eorg-leeton-sandbox" {
  name        = "rds-eorg-leeton-sandbox"
  description = "Allow traffic to eOrg Leeton RDS - eorg-leeton-sandbox"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["172.17.0.0/16"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "eorg-leeton-sandbox"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-068cbc49449419a08"
    "Project Service" = "elementOrg"
    Env = "sandbox"
    "Cost Center" = "elementOrg"
    "Project Team" = "elementOrg"
    MakeSnapshotShortTerm = "True"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: rds-eorg-leeton-stage
# Original ID: sg-05545a49b9409cdfb
resource "aws_security_group" "eorg-leeton-stage" {
  name        = "rds-eorg-leeton-stage"
  description = "Allow traffic to eOrg Leeton RDS - eorg-leeton-stage"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["172.17.0.0/16"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "eorg-leeton-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-05545a49b9409cdfb"
    "Project Team" = "elementOrg"
    "Cost Center" = "elementOrg"
    Env = "stage"
    MakeSnapshotShortTerm = "True"
    "Project Service" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: eorg-leeton-stage-20240710044909523300000001
# Original ID: sg-005bc166ce97ef592
resource "aws_security_group" "eorg-leeton-stage_e97ef592" {
  name        = "eorg-leeton-stage-20240710044909523300000001"
  description = "Control traffic to/from RDS Aurora eorg-leeton-stage"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  tags = {
    Name        = "eorg-leeton-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-005bc166ce97ef592"
    MakeSnapshotShortTerm = "True"
    "Project Service" = "elementOrg"
    "Cost Center" = "elementOrg"
    Env = "stage"
    "Project Team" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: eorg-griffith-test-20250227003103948600000001
# Original ID: sg-0c093a6a7263c9dfa
resource "aws_security_group" "eorg-griffith-test" {
  name        = "eorg-griffith-test-20250227003103948600000001"
  description = "Control traffic to/from RDS Aurora eorg-griffith-test"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  tags = {
    Name        = "eorg-griffith-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0c093a6a7263c9dfa"
    MakeSnapshotShortTerm = "True"
    "Project Service" = "elementOrg"
    Env = "test"
    "Project Team" = "elementOrg"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: rds-eorg-griffith-test
# Original ID: sg-011bb976f3151a985
resource "aws_security_group" "eorg-griffith-test_3151a985" {
  name        = "rds-eorg-griffith-test"
  description = "Allow traffic to eOrg Griffith RDS - eorg-griffith-test"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["172.17.0.0/16"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "eorg-griffith-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-011bb976f3151a985"
    "Project Team" = "elementOrg"
    "Cost Center" = "elementOrg"
    Env = "test"
    MakeSnapshotShortTerm = "True"
    "Project Service" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: rds-eorg-griffith-stage
# Original ID: sg-08cec92be4801bc92
resource "aws_security_group" "eorg-griffith-stage_4801bc92" {
  name        = "rds-eorg-griffith-stage"
  description = "Allow traffic to eOrg Griffith RDS - eorg-griffith-stage"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["172.17.0.0/16"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "eorg-griffith-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-08cec92be4801bc92"
    Env = "stage"
    "Cost Center" = "elementOrg"
    "Project Team" = "elementOrg"
    "Project Service" = "elementOrg"
    MakeSnapshotShortTerm = "True"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: eorg-griffith-stage-20250227005837375300000001
# Original ID: sg-021c66bf937ed13ef
resource "aws_security_group" "eorg-griffith-stage" {
  name        = "eorg-griffith-stage-20250227005837375300000001"
  description = "Control traffic to/from RDS Aurora eorg-griffith-stage"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  tags = {
    Name        = "eorg-griffith-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-021c66bf937ed13ef"
    Env = "stage"
    MakeSnapshotShortTerm = "True"
    "Project Service" = "elementOrg"
    "Project Team" = "elementOrg"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: rds-elementorg-sa-burnoffs
# Original ID: sg-02dc8634039ce1c6b
resource "aws_security_group" "rds-elementorg-sa-burnoffs" {
  name        = "rds-elementorg-sa-burnoffs"
  description = "Allow traffic to elementorg-sa-burnoffs RDS"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["172.17.0.0/16"]
  }

  tags = {
    Name        = "rds-elementorg-sa-burnoffs"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-02dc8634039ce1c6b"
    "Project Team" = "elementOrg"
    "Cost Center" = "elementOrg"
    "Project Service" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: rds-ecentre-stage-20250429024641621900000002
# Original ID: sg-0f401e88dac73f880
resource "aws_security_group" "ecentre-stage_ac73f880" {
  name        = "rds-ecentre-stage-20250429024641621900000002"
  description = "Allow traffic to eCentre RDS - ecentre-stage"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["172.31.0.0/16", "172.17.0.0/16"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "ecentre-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0f401e88dac73f880"
    Env = "stage"
    "Cost Center" = "elementCentre"
    MakeSnapshotShortTerm = "True"
    "Project Team" = "elementCentre"
    "Project Service" = "elementCentre"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: ecentre-stage-20250429024641621900000001
# Original ID: sg-0f2fd1dcdc1ec9c4c
resource "aws_security_group" "ecentre-stage" {
  name        = "ecentre-stage-20250429024641621900000001"
  description = "Control traffic to/from RDS Aurora ecentre-stage"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  tags = {
    Name        = "ecentre-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0f2fd1dcdc1ec9c4c"
    "Project Service" = "elementCentre"
    Env = "stage"
    MakeSnapshotShortTerm = "True"
    "Cost Center" = "elementCentre"
    "Project Team" = "elementCentre"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: rds-proxy-etime-14si-stage
# Original ID: sg-04fd18e2c9ea995f2
resource "aws_security_group" "rds-proxy-etime-14si-stage" {
  name        = "rds-proxy-etime-14si-stage"
  description = "Security group for RDS Proxy - etime-14si-stage"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["172.17.0.0/16", "172.31.0.0/16"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "rds-proxy-etime-14si-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-04fd18e2c9ea995f2"
    "Project Service" = "elementTIME"
    Env = "stage"
    MakeSnapshotShortTerm = "True"
    "Cost Center" = "elementTIME"
    env_version = "14si"
    "Project Team" = "elementTIME"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: rds-proxy-etime-14si-stage-i3
# Original ID: sg-0ac213849dbc52704
resource "aws_security_group" "rds-proxy-etime-14si-stage-i3" {
  name        = "rds-proxy-etime-14si-stage-i3"
  description = "Security group for RDS Proxy - etime-14si-stage-i3"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["172.17.0.0/16", "172.31.0.0/16"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "rds-proxy-etime-14si-stage-i3"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0ac213849dbc52704"
    MakeSnapshotShortTerm = "True"
    "Project Team" = "elementTIME"
    env_version = "14si"
    "Project Service" = "elementTIME"
    "Cost Center" = "elementTIME"
    Env = "stage"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: office-vpn-http-https-ingress
# Original ID: sg-0d04d071977f7eb3f
resource "aws_security_group" "office-vpn-http-https-ingress_77f7eb3f" {
  name        = "office-vpn-http-https-ingress"
  description = "Allow HTTP and HTTPS ingress from the Auckland office and VPN"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["122.59.27.77/32", "123.255.56.65/32", "14.1.34.16/32", "3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["122.59.27.77/32", "14.1.34.16/32", "123.255.56.65/32", "3.24.7.167/32"]
  }

  tags = {
    Name        = "office-vpn-http-https-ingress"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0d04d071977f7eb3f"
    "Cost Center" = "stage"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: sms-report-lifesupport-EnvironmentSecurityGroup-1JFJHJGH2I7O8
# Original ID: sg-053c870946955be50
resource "aws_security_group" "copilot-sms-report-lifesupport-env" {
  name        = "sms-report-lifesupport-EnvironmentSecurityGroup-1JFJHJGH2I7O8"
  description = "sms-report-lifesupportEnvironmentSecurityGroup"
  # WARNING: VPC aws_vpc.lifesupport.id not found in graph
  vpc_id      = "aws_vpc.lifesupport.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    security_groups  = [
"aws_security_group.copilot-sms-report-lifesupport-env.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "copilot-sms-report-lifesupport-env"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-053c870946955be50"
    copilot-environment = "lifesupport"
    copilot-application = "sms-report"
    "aws:cloudformation:stack-name" = "sms-report-lifesupport"
    "aws:cloudformation:logical-id" = "EnvironmentSecurityGroup"
    "aws:cloudformation:stack-id" = "arn:aws:cloudformation:ap-southeast-2:${var.aws_account_id}:stack/sms-report-lifesupport/4b95c910-df62-11ed-94e7-064f178b9614"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: rds-elementorg-leeton-sandbox
# Original ID: sg-09030af5ff9c964a3
resource "aws_security_group" "rds-elementorg-leeton-sandbox" {
  name        = "rds-elementorg-leeton-sandbox"
  description = "Allow traffic to elementorg-leeton-sandbox RDS"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["172.17.0.0/16"]
  }

  tags = {
    Name        = "rds-elementorg-leeton-sandbox"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-09030af5ff9c964a3"
    "Project Service" = "elementOrg"
    "Cost Center" = "elementOrg"
    "Project Team" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: default
# Original ID: sg-0be0ed76533eb5791
resource "aws_security_group" "sg-0be0ed76533eb5791" {
  name        = "default"
  description = "default VPC security group"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  tags = {
    Name        = "default"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0be0ed76533eb5791"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: yorke-web-database
# Original ID: sg-0ee8930c869e9b873
resource "aws_security_group" "sg-0ee8930c869e9b873" {
  name        = "yorke-web-database"
  description = "allow old/new website host only"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 0
    to_port          = 65535
    security_groups  = [
"aws_security_group.sg-01430ba65e3c749aa.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3308
    to_port          = 3308
    cidr_blocks      = ["13.236.215.158/32", "49.156.27.199/32", "49.156.27.195/32", "150.101.10.0/24"]
    security_groups  = [
"aws_security_group.sg-01430ba65e3c749aa.id",
    ]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["172.31.39.30/32"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "yorke-web-database"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0ee8930c869e9b873"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: office-vpn-http-https-ingress
# Original ID: sg-01b09486eda56d3d6
resource "aws_security_group" "office-vpn-http-https-ingress" {
  name        = "office-vpn-http-https-ingress"
  description = "Allow HTTP and HTTPS ingress from the Auckland office and VPN"
  # WARNING: VPC aws_vpc.lifesupport.id not found in graph
  vpc_id      = "aws_vpc.lifesupport.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["123.255.56.65/32", "122.59.27.77/32", "14.1.34.16/32", "3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["122.59.27.77/32", "14.1.34.16/32", "123.255.56.65/32", "3.24.7.167/32"]
  }

  tags = {
    Name        = "office-vpn-http-https-ingress"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-01b09486eda56d3d6"
    "Cost Center" = "Platform"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: allow-elb-eodefault-sa-redirect
# Original ID: sg-0f6944262216e298a
resource "aws_security_group" "sg-0f6944262216e298a" {
  name        = "allow-elb-eodefault-sa-redirect"
  description = "Allow 80/443/8080/8443 ingress from ALB eodefault-sa-redirect to EC2 elementorg-sa-fires"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 8443
    to_port          = 8443
    cidr_blocks      = ["3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["0.0.0.0/0"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "allow-elb-eodefault-sa-redirect"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0f6944262216e298a"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: vpn
# Original ID: sg-05ca6d63
resource "aws_security_group" "sg-05ca6d63" {
  name        = "vpn"
  description = "launch-wizard-4 created 2017-09-26T11:54:57.331+13:00"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 4433
    to_port          = 4433
    cidr_blocks      = ["14.1.34.16/32", "3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "udp"
    from_port        = 1194
    to_port          = 1194
    cidr_blocks      = ["0.0.0.0/0"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 1195
    to_port          = 1195
    cidr_blocks      = ["14.1.34.16/32", "3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 30222
    to_port          = 30222
    cidr_blocks      = ["3.24.7.167/32", "14.1.34.16/32", "123.255.56.65/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 53
    to_port          = 53
    cidr_blocks      = ["3.24.7.167/32", "14.1.34.16/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "udp"
    from_port        = 4433
    to_port          = 4433
    cidr_blocks      = ["14.1.34.16/32", "3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 4343
    to_port          = 4343
    cidr_blocks      = ["3.24.7.167/32", "14.1.34.16/32"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "vpn"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-05ca6d63"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: rds-proxy-etime-14si-test
# Original ID: sg-032bd4bc120df3992
resource "aws_security_group" "rds-proxy-etime-14si-test" {
  name        = "rds-proxy-etime-14si-test"
  description = "Security group for RDS Proxy - etime-14si-test"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["172.31.0.0/16", "172.17.0.0/16"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "rds-proxy-etime-14si-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-032bd4bc120df3992"
    "Project Service" = "elementTIME"
    Env = "test"
    env_version = "14si"
    "Project Team" = "elementTIME"
    "Cost Center" = "elementTIME"
    MakeSnapshotShortTerm = "True"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: elementorg
# Original ID: sg-05d10210c0f59718b
resource "aws_security_group" "sg-05d10210c0f59718b" {
  name        = "elementorg"
  description = "Created by RDS management console"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["115.188.148.42/32"]
    security_groups  = [
"aws_security_group.sg-05ca6d63.id",
"aws_security_group.sg-01430ba65e3c749aa.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "elementorg"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-05d10210c0f59718b"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: check-aws-ri-lifesupport-EnvironmentSecurityGroup-19WT13KVRKYBH
# Original ID: sg-05489ce9da347c7a0
resource "aws_security_group" "copilot-check-aws-ri-lifesupport-env" {
  name        = "check-aws-ri-lifesupport-EnvironmentSecurityGroup-19WT13KVRKYBH"
  description = "check-aws-ri-lifesupportEnvironmentSecurityGroup"
  # WARNING: VPC aws_vpc.lifesupport.id not found in graph
  vpc_id      = "aws_vpc.lifesupport.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    security_groups  = [
"aws_security_group.copilot-check-aws-ri-lifesupport-env.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "copilot-check-aws-ri-lifesupport-env"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-05489ce9da347c7a0"
    copilot-environment = "lifesupport"
    "aws:cloudformation:logical-id" = "EnvironmentSecurityGroup"
    "aws:cloudformation:stack-id" = "arn:aws:cloudformation:ap-southeast-2:${var.aws_account_id}:stack/check-aws-ri-lifesupport/98d32d10-b800-11ec-98ec-0a870a246182"
    "aws:cloudformation:stack-name" = "check-aws-ri-lifesupport"
    copilot-application = "check-aws-ri"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: test-elementtime-mongodb
# Original ID: sg-086681330bc3274ce
resource "aws_security_group" "sg-086681330bc3274ce" {
  name        = "test-elementtime-mongodb"
  description = "Access from the test_elementtime EC2 (managed)"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 22
    to_port          = 22
    cidr_blocks      = ["172.31.4.43/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 27017
    to_port          = 27019
    cidr_blocks      = ["172.31.4.43/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 30222
    to_port          = 30222
    cidr_blocks      = ["172.31.4.43/32"]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "test-elementtime-mongodb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-086681330bc3274ce"
    "Cost Center" = "stage-current"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: default
# Original ID: sg-5036b934
resource "aws_security_group" "sg-5036b934" {
  name        = "default"
  description = "default VPC security group"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  tags = {
    Name        = "default"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-5036b934"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: redis-stage-eorg-leeton-ingress
# Original ID: sg-0927c4ec5a31e625d
resource "aws_security_group" "redis-stage-eorg-leeton-ingress" {
  name        = "redis-stage-eorg-leeton-ingress"
  description = "Allow traffic to eOrg Leeton Redis - stage-eorg-leeton"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 6379
    to_port          = 6379
    cidr_blocks      = ["172.17.0.0/16", "122.59.27.77/32", "14.1.34.16/32", "123.255.56.65/32"]
  }

  tags = {
    Name        = "redis-stage-eorg-leeton-ingress"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0927c4ec5a31e625d"
    "Cost Center" = "stage"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: etime-face-auth-stage-lambda-20251018103611230200000001
# Original ID: sg-0dc8b0cf9351f87e0
resource "aws_security_group" "etime-face-auth-stage-lambda-sg" {
  name        = "etime-face-auth-stage-lambda-20251018103611230200000001"
  description = "Security group for Face Auth Lambda functions"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "etime-face-auth-stage-lambda-sg"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0dc8b0cf9351f87e0"
    ManagedBy = "terraform"
    Project = "etime-face-auth"
    Component = "security"
    Service = "face-auth"
    "Cost Center" = "elementTIME"
    Terraform = "true"
    Environment = "stage"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: aws-cost-report-lifesupport-EnvironmentSecurityGroup-1DYCNX9OAFGEO
# Original ID: sg-0311229fe8e6521e5
resource "aws_security_group" "copilot-aws-cost-report-lifesupport-env" {
  name        = "aws-cost-report-lifesupport-EnvironmentSecurityGroup-1DYCNX9OAFGEO"
  description = "aws-cost-report-lifesupportEnvironmentSecurityGroup"
  # WARNING: VPC aws_vpc.lifesupport.id not found in graph
  vpc_id      = "aws_vpc.lifesupport.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    security_groups  = [
"aws_security_group.copilot-aws-cost-report-lifesupport-env.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "copilot-aws-cost-report-lifesupport-env"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-0311229fe8e6521e5"
    "aws:cloudformation:stack-name" = "aws-cost-report-lifesupport"
    copilot-application = "aws-cost-report"
    "aws:cloudformation:stack-id" = "arn:aws:cloudformation:ap-southeast-2:${var.aws_account_id}:stack/aws-cost-report-lifesupport/74514750-b987-11ec-a208-0231c76dc538"
    "aws:cloudformation:logical-id" = "EnvironmentSecurityGroup"
    copilot-environment = "lifesupport"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: office-vpn-ssh-ingress
# Original ID: sg-05436eb7c1b96d5d9
resource "aws_security_group" "office-vpn-ssh-ingress" {
  name        = "office-vpn-ssh-ingress"
  description = "Allow ingress from the Auckland office and VPN"
  # WARNING: VPC aws_vpc.lifesupport.id not found in graph
  vpc_id      = "aws_vpc.lifesupport.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 22
    to_port          = 22
    cidr_blocks      = ["123.255.56.65/32", "14.1.34.16/32", "122.59.27.77/32", "3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 30222
    to_port          = 30222
    cidr_blocks      = ["123.255.56.65/32", "14.1.34.16/32", "122.59.27.77/32", "3.24.7.167/32"]
  }

  tags = {
    Name        = "office-vpn-ssh-ingress"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-05436eb7c1b96d5d9"
    "Cost Center" = "Platform"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: office-vpn-http-https-ingress-current
# Original ID: sg-050845c8e90185a92
resource "aws_security_group" "office-vpn-http-https-ingress-current" {
  name        = "office-vpn-http-https-ingress-current"
  description = "Allow HTTP and HTTPS ingress from the Auckland office and VPN"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 80
    to_port          = 80
    cidr_blocks      = ["122.59.27.77/32", "123.255.56.65/32", "14.1.34.16/32", "3.24.7.167/32"]
  }

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 443
    to_port          = 443
    cidr_blocks      = ["122.59.27.77/32", "14.1.34.16/32", "123.255.56.65/32", "3.24.7.167/32"]
  }

  tags = {
    Name        = "office-vpn-http-https-ingress-current"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-050845c8e90185a92"
    "Cost Center" = "stage-current"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: default
# Original ID: sg-01b3a4f5e9de79784
resource "aws_security_group" "sg-01b3a4f5e9de79784" {
  name        = "default"
  description = "default VPC security group"
  # WARNING: VPC aws_vpc.lifesupport.id not found in graph
  vpc_id      = "aws_vpc.lifesupport.id"

  tags = {
    Name        = "default"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-01b3a4f5e9de79784"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: security-report-lifesupport-EnvironmentSecurityGroup-9STCF80UUPSF
# Original ID: sg-098a90f2ddcedc1f5
resource "aws_security_group" "copilot-security-report-lifesupport-env" {
  name        = "security-report-lifesupport-EnvironmentSecurityGroup-9STCF80UUPSF"
  description = "security-report-lifesupportEnvironmentSecurityGroup"
  # WARNING: VPC aws_vpc.lifesupport.id not found in graph
  vpc_id      = "aws_vpc.lifesupport.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    security_groups  = [
"aws_security_group.copilot-security-report-lifesupport-env.id",
    ]
  }

  egress {
    description      = "Egress rule"
    protocol         = "-1"
    from_port        = 0
    to_port          = 0
    cidr_blocks      = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "copilot-security-report-lifesupport-env"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-098a90f2ddcedc1f5"
    "aws:cloudformation:stack-name" = "security-report-lifesupport"
    "aws:cloudformation:logical-id" = "EnvironmentSecurityGroup"
    "aws:cloudformation:stack-id" = "arn:aws:cloudformation:ap-southeast-2:${var.aws_account_id}:stack/security-report-lifesupport/d38eeed0-91a3-11ed-bd27-067b5254eacc"
    copilot-application = "security-report"
    copilot-environment = "lifesupport"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# Security Group: rds-elementorg-leeton
# Original ID: sg-09deca4f2386e1ce0
resource "aws_security_group" "rds-elementorg-leeton" {
  name        = "rds-elementorg-leeton"
  description = "Allow traffic to elementorg-leeton RDS"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"

  ingress {
    description      = "Ingress rule"
    protocol         = "tcp"
    from_port        = 3306
    to_port          = 3306
    cidr_blocks      = ["172.17.0.0/16"]
  }

  tags = {
    Name        = "rds-elementorg-leeton"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "sg-09deca4f2386e1ce0"
    "Project Service" = "elementOrg"
    "Project Team" = "elementOrg"
    "Cost Center" = "elementOrg"
  }

  lifecycle {
    create_before_destroy = true
  }
}