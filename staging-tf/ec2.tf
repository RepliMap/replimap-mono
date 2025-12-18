# EC2 Instance: asg-etime-stage-skt-g-14si
# Original ID: i-085fa7b6496135edc
# Original Type: m8g.large
resource "aws_instance" "asg-etime-stage-skt-g-14si" {
  ami           = "ami-04ca030c26a97465a"
  instance_type = "m8g.large"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2c.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2c.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]

  iam_instance_profile = "asg-etime-stage-skt-g-14si"

  ebs_optimized = true
  monitoring    = true

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "asg-etime-stage-skt-g-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-085fa7b6496135edc"
    ANSIBLE_POOL = "ac-stage"
    "Cost Center" = "etime"
    ANSIBLE_PLAY = "plays/base-ami-etime-stage-skt-new-env-14si.yml"
    ami_id = "ami-04ca030c26a97465a"
    "aws:ec2launchtemplate:version" = "9"
    MakeSnapshotLongTerm = "False"
    ENV_VERSION = "14si"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    ANSIBLE_DC = "stage-ap-southeast-2"
    ANSIBLE_ROLE = "etime-stage"
    route53_record_prefix = "asg-etime-stage-skt-g-14si"
    MakeSnapshotShortTerm = "False"
    "aws:ec2launchtemplate:id" = "lt-03efae88b42d320d5"
    "N/A" = "owned"
    "aws:ec2:fleet-id" = "fleet-9f94f92f-ab8c-463c-2e38-a7081b820caf"
    MakeSnapshot = "False"
    "aws:autoscaling:groupName" = "asg-etime-stage-skt-g-14si"
    Environment = "stage"
    zone_id = "Z0510321LZZI860UP8GE"
    ANSIBLE_BRANCH = "upgrade-2204"
    vpc_domain = "sydney.stage.adroitcreations.org"
  }
}

# EC2 Instance: gateway
# Original ID: i-03cf8a01a5f3c79b1
# Original Type: t3a.small
resource "aws_instance" "gateway" {
  ami           = "ami-08cf95f27a67def0e"
  instance_type = "t3a.small"

  # WARNING: Subnet aws_subnet.stage-subnet-public-ap-southeast-2a.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-public-ap-southeast-2a.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ee33593e107f36f1.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    "aws_security_group.office-vpn-ssh-ingress.id",
  ]

  iam_instance_profile = "gateway"

  ebs_optimized = true
  monitoring    = false

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "gateway"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-03cf8a01a5f3c79b1"
    "Cost Center" = "Platform"
    route53_record_prefix = "gateway"
    zone_id = "Z0510321LZZI860UP8GE"
    vpc_domain = "sydney.stage.adroitcreations.org"
    Environment = "stage"
    SUDOERS_GROUPS_TAG = "engineering,platform,security"
    ANSIBLE_POOL = "ac-stage"
    ami_id = "ami-08cf95f27a67def0e"
    ANSIBLE_BRANCH = "master"
    ANSIBLE_PLAY = "plays/gateway-developer.yml"
    ANSIBLE_ROLE = "gateway"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    ANSIBLE_DC = "stage-ap-southeast-2"
    Terraform = "true"
  }
}

# EC2 Instance: elementorg-ngsc
# Original ID: i-03f57d9cf462710ce
# Original Type: c5a.large
resource "aws_instance" "elementorg-ngsc" {
  ami           = "ami-019b9823dfb70e1ce"
  instance_type = "c5a.large"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2b.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2b.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ee33593e107f36f1.id",
    "aws_security_group.sg-0466bf33a2b40ed19.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    "aws_security_group.office-vpn-ssh-ingress.id",
  ]

  iam_instance_profile = "elementorg-ngsc-profile"

  ebs_optimized = true
  monitoring    = false

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "elementorg-ngsc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-03f57d9cf462710ce"
    ANSIBLE_POOL = "ac-stage"
    ANSIBLE_BRANCH = "upgrade-2204-base"
    Environment = "stage"
    Terraform = "true"
    "Cost Center" = "elementOrg"
    route53_record_prefix = "elementorg-ngsc"
    ami_id = "ami-019b9823dfb70e1ce"
    ANSIBLE_PLAY = "plays/elementorg-ngsc.yml"
    vpc_domain = "sydney.stage.adroitcreations.org"
    zone_id = "Z0510321LZZI860UP8GE"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    ANSIBLE_DC = "stage-ap-southeast-2"
    SUDOERS_GROUPS_TAG = "engineering,platform,security"
    ANSIBLE_ROLE = "elementorg"
  }
}

# EC2 Instance: asg-elementtime-stage-green
# Original ID: i-0120764de2b5d67d7
# Original Type: m8g.large
resource "aws_instance" "asg-elementtime-stage-green" {
  ami           = "ami-04ca030c26a97465a"
  instance_type = "m8g.large"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2c.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2c.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
  ]

  iam_instance_profile = "asg-elementtime-stage-green"

  ebs_optimized = true
  monitoring    = true

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "asg-elementtime-stage-green"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-0120764de2b5d67d7"
    ANSIBLE_ROLE = "elementtime-stage"
    MakeSnapshotShortTerm = "False"
    MakeSnapshotLongTerm = "False"
    "Cost Center" = "elementtime"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    ANSIBLE_POOL = "ac-stage"
    ANSIBLE_DC = "stage-ap-southeast-2"
    ami_id = "ami-04ca030c26a97465a"
    "aws:ec2launchtemplate:id" = "lt-0fe81c28bab290f06"
    zone_id = "Z0510321LZZI860UP8GE"
    "aws:ec2:fleet-id" = "fleet-3fb6fba5-218e-6696-06ba-85829e584e05"
    MakeSnapshot = "False"
    "N/A" = "owned"
    "aws:autoscaling:groupName" = "asg-elementtime-stage-green"
    route53_record_prefix = "asg-elementtime-stage-green"
    ANSIBLE_PLAY = "plays/base-ami-etime-stage.yml"
    ENV_VERSION = ""
    "aws:ec2launchtemplate:version" = "16"
    vpc_domain = "sydney.stage.adroitcreations.org"
    ANSIBLE_BRANCH = "upgrade-2204-fix-vul-improve"
    Environment = "stage"
  }
}

# EC2 Instance: elementorg-ypc
# Original ID: i-0b118c20b597f90c7
# Original Type: c6a.large
resource "aws_instance" "elementorg-ypc" {
  ami           = "ami-019b9823dfb70e1ce"
  instance_type = "c6a.large"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2b.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2b.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ee33593e107f36f1.id",
    "aws_security_group.sg-0ad7ac2979564cc3b.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    "aws_security_group.office-vpn-ssh-ingress.id",
  ]

  iam_instance_profile = "elementorg-ypc-profile"

  ebs_optimized = true
  monitoring    = false

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "elementorg-ypc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-0b118c20b597f90c7"
    ANSIBLE_BRANCH = "upgrade-2204-base"
    Environment = "stage"
    Terraform = "true"
    ANSIBLE_POOL = "ac-stage"
    route53_record_prefix = "elementorg-ypc"
    "Cost Center" = "elementOrg"
    ANSIBLE_PLAY = "plays/elementorg-ypc.yml"
    ANSIBLE_ROLE = "elementorg"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    vpc_domain = "sydney.stage.adroitcreations.org"
    ANSIBLE_DC = "stage-ap-southeast-2"
    ami_id = "ami-019b9823dfb70e1ce"
    zone_id = "Z0510321LZZI860UP8GE"
    SUDOERS_GROUPS_TAG = "engineering,platform,security"
  }
}

# EC2 Instance: elementorg-test-ngsc-nodocker-trellis
# Original ID: i-0b4c8659b661cf247
# Original Type: t3a.small
resource "aws_instance" "elementorg-test-ngsc-nodocker-trellis" {
  ami           = "ami-019b9823dfb70e1ce"
  instance_type = "t3a.small"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2b.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2b.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ee33593e107f36f1.id",
    "aws_security_group.sg-0d7d46135b4284504.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    "aws_security_group.office-vpn-ssh-ingress.id",
  ]

  iam_instance_profile = "elementorg-test-ngsc-profile"

  ebs_optimized = true
  monitoring    = false

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "elementorg-test-ngsc-nodocker-trellis"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-0b4c8659b661cf247"
    zone_id = "Z0510321LZZI860UP8GE"
    ANSIBLE_PLAY = "plays/elementorg-test-ngsc-nodocker-trellis.yml"
    ANSIBLE_DC = "stage-ap-southeast-2"
    SUDOERS_GROUPS_TAG = "engineering,platform,security"
    Terraform = "true"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    ANSIBLE_ROLE = "elementorg"
    ANSIBLE_POOL = "ac-stage"
    route53_record_prefix = "elementorg-test-ngsc-nodocker-trellis"
    ANSIBLE_BRANCH = "upgrade-2204-base"
    Environment = "stage"
    "Cost Center" = "elementOrg"
    ami_id = "ami-019b9823dfb70e1ce"
    vpc_domain = "sydney.stage.adroitcreations.org"
  }
}

# EC2 Instance: vpn
# Original ID: i-0d3d6ef60d6eb524c
# Original Type: t3a.nano
resource "aws_instance" "vpn" {
  ami           = "ami-019b9823dfb70e1ce"
  instance_type = "t3a.nano"

  # WARNING: Subnet aws_subnet.public-2b.id not found in graph
  subnet_id     = "aws_subnet.public-2b.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-09032f0c1e675cba6.id",
    "aws_security_group.sg-03b61b529117d9048.id",
  ]

  iam_instance_profile = "vpn-current"

  ebs_optimized = true
  monitoring    = false

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "vpn"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-0d3d6ef60d6eb524c"
    Environment = "stage"
    route53_record_prefix = "vpn"
    vpc_domain = "sydney.stage.adroitcreations.org"
    ANSIBLE_POOL = "ac-stage"
    Terraform = "true"
    ANSIBLE_ROLE = "vpn"
    ANSIBLE_DC = "stage-ap-southeast-2"
    SUDOERS_GROUPS_TAG = "engineering,platform,security"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    zone_id = "Z0510321LZZI860UP8GE"
    ANSIBLE_PLAY = "plays/vpn.yml"
    ami_id = "ami-019b9823dfb70e1ce"
    "Cost Center" = "Platform"
    ANSIBLE_BRANCH = "upgrade-2204-base"
  }
}

# EC2 Instance: asg-elementtime-stage-socket-blue
# Original ID: i-0a71ae55e11550a8a
# Original Type: m8g.medium
resource "aws_instance" "asg-elementtime-stage-socket-blue" {
  ami           = "ami-04ca030c26a97465a"
  instance_type = "m8g.medium"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2b.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2b.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
  ]

  iam_instance_profile = "asg-elementtime-stage-socket-blue"

  ebs_optimized = true
  monitoring    = true

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "asg-elementtime-stage-socket-blue"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-0a71ae55e11550a8a"
    ANSIBLE_DC = "stage-ap-southeast-2"
    "aws:ec2launchtemplate:version" = "15"
    ENV_VERSION = ""
    Environment = "stage"
    zone_id = "Z0510321LZZI860UP8GE"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    ami_id = "ami-04ca030c26a97465a"
    "aws:autoscaling:groupName" = "asg-elementtime-stage-socket-blue"
    route53_record_prefix = "asg-elementtime-stage-socket-blue"
    MakeSnapshot = "False"
    "aws:ec2:fleet-id" = "fleet-019ee514-14a6-ec87-8492-09a23c4d544e"
    MakeSnapshotLongTerm = "False"
    ANSIBLE_PLAY = "plays/base-ami-etime-stage-socket.yml"
    ANSIBLE_BRANCH = "upgrade-2204-fix-vul-improve"
    "aws:ec2launchtemplate:id" = "lt-05b0a9a8f291d2dfb"
    vpc_domain = "sydney.stage.adroitcreations.org"
    MakeSnapshotShortTerm = "False"
    ANSIBLE_POOL = "ac-stage"
    "N/A" = "owned"
    "Cost Center" = "elementtime"
    ANSIBLE_ROLE = "elementtime-stage"
  }
}

# EC2 Instance: asg-elementcentre-stage-blue
# Original ID: i-06b9b3f6245f180be
# Original Type: t4g.small
resource "aws_instance" "asg-elementcentre-stage-blue" {
  ami           = "ami-03dbcf19ff380ef96"
  instance_type = "t4g.small"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2b.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2b.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ac562a2b2761e254.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    "aws_security_group.elementSeries_prod_vpc.id",
  ]

  iam_instance_profile = "asg-elementcentre-stage-blue"

  ebs_optimized = true
  monitoring    = true

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "asg-elementcentre-stage-blue"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-06b9b3f6245f180be"
    zone_id = "Z0510321LZZI860UP8GE"
    ami_id = "ami-03dbcf19ff380ef96"
    "N/A" = "owned"
    MakeSnapshot = "False"
    "aws:ec2launchtemplate:version" = "2"
    "Cost Center" = "elementcentre"
    ANSIBLE_DC = "stage-ap-southeast-2"
    ANSIBLE_POOL = "ac-stage"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    MakeSnapshotLongTerm = "False"
    ANSIBLE_BRANCH = "upgrade-2204-base"
    ANSIBLE_ROLE = "elementcentre-stage"
    MakeSnapshotShortTerm = "False"
    ANSIBLE_PLAY = "plays/base-ami-elementcentre-stage.yml"
    ENV_VERSION = ""
    vpc_domain = "sydney.stage.adroitcreations.org"
    route53_record_prefix = "asg-elementcentre-stage-blue"
    Environment = "stage"
    "aws:autoscaling:groupName" = "asg-elementcentre-stage-blue"
    "aws:ec2:fleet-id" = "fleet-371ef32d-8986-c61c-ac18-ad2078193a79"
    "aws:ec2launchtemplate:id" = "lt-079f444f6bc8a8ec9"
  }
}

# EC2 Instance: gateway-current
# Original ID: i-00238b7f5e909178b
# Original Type: t3a.small
resource "aws_instance" "gateway-current" {
  ami           = "ami-09ba144f87abb1c20"
  instance_type = "t3a.small"

  # WARNING: Subnet aws_subnet.public-2a.id not found in graph
  subnet_id     = "aws_subnet.public-2a.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0c00b8511d60caa56.id",
    "aws_security_group.sg-09032f0c1e675cba6.id",
    "aws_security_group.office-vpn-ssh-ingress-current.id",
    "aws_security_group.sg-002adf82ccd2da02d.id",
    "aws_security_group.sg-03c2af77d267b7126.id",
  ]

  iam_instance_profile = "gateway-current"

  ebs_optimized = true
  monitoring    = false

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "gateway-current"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-00238b7f5e909178b"
    ANSIBLE_ROLE = "gateway"
    ANSIBLE_PLAY = "plays/gateway-developer.yml"
    SUDOERS_GROUPS_TAG = "engineering,platform,security"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    ANSIBLE_BRANCH = "master"
    ANSIBLE_POOL = "ac-stage"
    ANSIBLE_DC = "stage-ap-southeast-2"
    Terraform = "true"
    vpc_domain = "sydney.stage.adroitcreations.org"
    route53_record_prefix = "gateway"
    "Cost Center" = "Platform"
    ami_id = "ami-09ba144f87abb1c20"
    Environment = "stage"
    zone_id = "Z0510321LZZI860UP8GE"
  }
}

# EC2 Instance: pro_hosting
# Original ID: i-0718c65f5d7d9b3ae
# Original Type: t3.small
resource "aws_instance" "pro_hosting" {
  ami           = "ami-e9c7208b"
  instance_type = "t3.small"

  # WARNING: Subnet aws_subnet.public-2b.id not found in graph
  subnet_id     = "aws_subnet.public-2b.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0c00b8511d60caa56.id",
    "aws_security_group.sg-01430ba65e3c749aa.id",
  ]

  iam_instance_profile = "EC2Instances"

  ebs_optimized = false
  monitoring    = false

  root_block_device {
    delete_on_termination = false
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "pro_hosting"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-0718c65f5d7d9b3ae"
    os = "centos"
    pro_elementorg = "1"
    MakeSnapshotShortTerm = "True"
  }
}

# EC2 Instance: elementorg-test-ypc
# Original ID: i-032b5c40b5106755f
# Original Type: t3a.small
resource "aws_instance" "elementorg-test-ypc" {
  ami           = "ami-019b9823dfb70e1ce"
  instance_type = "t3a.small"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2b.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2b.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ee33593e107f36f1.id",
    "aws_security_group.sg-0d03d0d0d4b1857a2.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    "aws_security_group.office-vpn-ssh-ingress.id",
  ]

  iam_instance_profile = "elementorg-test-ypc-profile"

  ebs_optimized = true
  monitoring    = false

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "elementorg-test-ypc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-032b5c40b5106755f"
    Environment = "stage"
    vpc_domain = "sydney.stage.adroitcreations.org"
    route53_record_prefix = "elementorg-test-ypc"
    ANSIBLE_BRANCH = "upgrade-2204-base"
    "Cost Center" = "elementOrg"
    ANSIBLE_DC = "stage-ap-southeast-2"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    SUDOERS_GROUPS_TAG = "engineering,platform,security"
    zone_id = "Z0510321LZZI860UP8GE"
    ami_id = "ami-019b9823dfb70e1ce"
    ANSIBLE_ROLE = "elementorg"
    ANSIBLE_POOL = "ac-stage"
    Terraform = "true"
    ANSIBLE_PLAY = "plays/elementorg-test-ypc.yml"
  }
}

# EC2 Instance: asg-elementtime-stage-green
# Original ID: i-043ee203c6ece9649
# Original Type: m8g.large
resource "aws_instance" "asg-elementtime-stage-green_6ece9649" {
  ami           = "ami-04ca030c26a97465a"
  instance_type = "m8g.large"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2a.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2a.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
  ]

  iam_instance_profile = "asg-elementtime-stage-green"

  ebs_optimized = true
  monitoring    = true

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "asg-elementtime-stage-green"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-043ee203c6ece9649"
    ENV_VERSION = ""
    "aws:autoscaling:groupName" = "asg-elementtime-stage-green"
    ami_id = "ami-04ca030c26a97465a"
    route53_record_prefix = "asg-elementtime-stage-green"
    "aws:ec2launchtemplate:version" = "16"
    ANSIBLE_PLAY = "plays/base-ami-etime-stage.yml"
    MakeSnapshotLongTerm = "False"
    zone_id = "Z0510321LZZI860UP8GE"
    "aws:ec2:fleet-id" = "fleet-17aff0a5-fbb5-439c-8e10-84a0d911f8ee"
    Environment = "stage"
    ANSIBLE_BRANCH = "upgrade-2204-fix-vul-improve"
    MakeSnapshot = "False"
    vpc_domain = "sydney.stage.adroitcreations.org"
    ANSIBLE_ROLE = "elementtime-stage"
    MakeSnapshotShortTerm = "False"
    "aws:ec2launchtemplate:id" = "lt-0fe81c28bab290f06"
    ANSIBLE_POOL = "ac-stage"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    "N/A" = "owned"
    ANSIBLE_DC = "stage-ap-southeast-2"
    "Cost Center" = "elementtime"
  }
}

# EC2 Instance: gateway-upgrade
# Original ID: i-0b1517966f2e54938
# Original Type: t3a.small
resource "aws_instance" "gateway-upgrade" {
  ami           = "ami-0091208de35b8d49b"
  instance_type = "t3a.small"

  # WARNING: Subnet aws_subnet.stage-subnet-public-ap-southeast-2a.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-public-ap-southeast-2a.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ee33593e107f36f1.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    "aws_security_group.office-vpn-ssh-ingress.id",
  ]

  iam_instance_profile = "gateway_upgrade"

  ebs_optimized = true
  monitoring    = false

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "gateway-upgrade"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-0b1517966f2e54938"
    ANSIBLE_PLAY = "plays/gateway-developer.yml"
    ANSIBLE_POOL = "ac-stage"
    ANSIBLE_ROLE = "gateway"
    Terraform = "true"
    ANSIBLE_DC = "stage-ap-southeast-2"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    "Cost Center" = "Platform"
    zone_id = "Z0510321LZZI860UP8GE"
    vpc_domain = "sydney.stage.adroitcreations.org"
    SUDOERS_GROUPS_TAG = "engineering,platform,security"
    route53_record_prefix = "gateway-upgrade"
    Environment = "stage"
    ami_id = "ami-0091208de35b8d49b"
    ANSIBLE_BRANCH = "upgrade-2204-base"
  }
}

# EC2 Instance: asg-elementsup-stage-blue
# Original ID: i-04c238df5aa6770c0
# Original Type: t4g.small
resource "aws_instance" "asg-elementsup-stage-blue" {
  ami           = "ami-03dbcf19ff380ef96"
  instance_type = "t4g.small"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2a.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2a.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0d4ca909ae44ef9a4.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    "aws_security_group.elementSeries_prod_vpc.id",
  ]

  iam_instance_profile = "asg-elementsup-stage-blue"

  ebs_optimized = true
  monitoring    = true

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "asg-elementsup-stage-blue"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-04c238df5aa6770c0"
    MakeSnapshot = "False"
    ami_id = "ami-03dbcf19ff380ef96"
    "Cost Center" = "elementsup"
    "N/A" = "owned"
    route53_record_prefix = "asg-elementsup-stage-blue"
    zone_id = "Z0510321LZZI860UP8GE"
    vpc_domain = "sydney.stage.adroitcreations.org"
    ANSIBLE_DC = "stage-ap-southeast-2"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    "aws:ec2launchtemplate:version" = "2"
    "aws:ec2launchtemplate:id" = "lt-0bf2553d035a5590e"
    "aws:ec2:fleet-id" = "fleet-17bcd38d-898e-64b6-ae98-8702144daef6"
    ANSIBLE_POOL = "ac-stage"
    ENV_VERSION = ""
    MakeSnapshotShortTerm = "False"
    ANSIBLE_PLAY = "plays/base-ami-elementsup-stage.yml"
    ANSIBLE_ROLE = "elementsup-stage"
    Environment = "stage"
    "aws:autoscaling:groupName" = "asg-elementsup-stage-blue"
    MakeSnapshotLongTerm = "False"
    ANSIBLE_BRANCH = "upgrade-2204-base"
  }
}

# EC2 Instance: test_other_elements
# Original ID: i-0c680cb8021d64358
# Original Type: t3.small
resource "aws_instance" "test_other_elements" {
  ami           = "ami-0a0bc4282fb32e6d8"
  instance_type = "t3.small"

  # WARNING: Subnet aws_subnet.public-2b.id not found in graph
  subnet_id     = "aws_subnet.public-2b.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0b21ee2705bb5a01d.id",
    "aws_security_group.sg-0c00b8511d60caa56.id",
    "aws_security_group.sg-022cca1d7ed3a7a0a.id",
    "aws_security_group.sg-0c3996e514e9d6196.id",
    "aws_security_group.sg-0577c665d2185f61e.id",
  ]

  iam_instance_profile = "EC2Instances"

  ebs_optimized = true
  monitoring    = false

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "test_other_elements"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-0c680cb8021d64358"
    test_internaltools = "g1"
    test_elementrec = "g1"
    test_elementstaff2 = "g1"
    os = "ubuntu"
    test_elementorg = "g1"
  }
}

# EC2 Instance: pro_other_elements_11
# Original ID: i-0f06c52f33523b502
# Original Type: t3.micro
resource "aws_instance" "pro_other_elements_11" {
  ami           = "ami-081018e5838689744"
  instance_type = "t3.micro"

  # WARNING: Subnet aws_subnet.public-2a.id not found in graph
  subnet_id     = "aws_subnet.public-2a.id"

  vpc_security_group_ids = [
    "aws_security_group.elementSeries.id",
    "aws_security_group.sg-0c00b8511d60caa56.id",
  ]

  iam_instance_profile = "EC2Instances"

  ebs_optimized = false
  monitoring    = false

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "pro_other_elements_11"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-0f06c52f33523b502"
    os = "ubuntu"
    pro_elementsup = "g1"
    pro_elementstaff = "g1"
    pro_elementcentre = "g1"
    MakeSnapshotShortTerm = "True"
    pro_elementrec = "g1"
    pro_elementstaff2 = "g1"
  }
}

# EC2 Instance: asg-elementstaff-stage-blue
# Original ID: i-07fe866f345841a38
# Original Type: t4g.small
resource "aws_instance" "asg-elementstaff-stage-blue" {
  ami           = "ami-0299dc8622d5d2613"
  instance_type = "t4g.small"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2a.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2a.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-02c028c79d15adf86.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    "aws_security_group.elementSeries_prod_vpc.id",
  ]

  iam_instance_profile = "asg-elementstaff-stage-blue"

  ebs_optimized = true
  monitoring    = true

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "asg-elementstaff-stage-blue"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-07fe866f345841a38"
    ANSIBLE_POOL = "ac-stage"
    ANSIBLE_PLAY = "plays/base-ami-estaff-new-stage.yml"
    MakeSnapshotShortTerm = "False"
    ANSIBLE_BRANCH = "upgrade-2204-base"
    MakeSnapshotLongTerm = "False"
    "aws:ec2:fleet-id" = "fleet-97367125-2b2e-4614-8cb8-27883ca5c1a0"
    ENV_VERSION = ""
    ANSIBLE_ROLE = "elementstaff-stage"
    "aws:ec2launchtemplate:version" = "4"
    ami_id = "ami-0299dc8622d5d2613"
    "aws:ec2launchtemplate:id" = "lt-0cc8e2d2ee2af8118"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    ANSIBLE_DC = "stage-ap-southeast-2"
    "N/A" = "owned"
    "aws:autoscaling:groupName" = "asg-elementstaff-stage-blue"
    route53_record_prefix = "asg-elementstaff-stage-blue"
    vpc_domain = "sydney.stage.adroitcreations.org"
    MakeSnapshot = "False"
    "Cost Center" = "elementstaff"
    zone_id = "Z0510321LZZI860UP8GE"
    Environment = "stage"
  }
}

# EC2 Instance: asg-etime-stage-skt-b-14si
# Original ID: i-041c441256a9cc0ef
# Original Type: m8g.medium
resource "aws_instance" "asg-etime-stage-skt-b-14si" {
  ami           = "ami-04ca030c26a97465a"
  instance_type = "m8g.medium"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2b.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2b.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]

  iam_instance_profile = "asg-etime-stage-skt-b-14si"

  ebs_optimized = true
  monitoring    = true

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "asg-etime-stage-skt-b-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-041c441256a9cc0ef"
    ANSIBLE_BRANCH = "upgrade-2204"
    vpc_domain = "sydney.stage.adroitcreations.org"
    MakeSnapshot = "False"
    "aws:ec2launchtemplate:id" = "lt-026402e837ad46bc1"
    "N/A" = "owned"
    Environment = "stage"
    "aws:autoscaling:groupName" = "asg-etime-stage-skt-b-14si"
    "aws:ec2launchtemplate:version" = "11"
    zone_id = "Z0510321LZZI860UP8GE"
    route53_record_prefix = "asg-etime-stage-skt-b-14si"
    ANSIBLE_POOL = "ac-stage"
    "Cost Center" = "etime"
    MakeSnapshotShortTerm = "False"
    MakeSnapshotLongTerm = "False"
    ANSIBLE_ROLE = "etime-stage"
    ENV_VERSION = "14si"
    ANSIBLE_PLAY = "plays/base-ami-etime-stage-skt-new-env-14si.yml"
    "aws:ec2:fleet-id" = "fleet-9f2d5807-d335-e9be-a4b8-ac2af26a8f01"
    ANSIBLE_DC = "stage-ap-southeast-2"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    ami_id = "ami-04ca030c26a97465a"
  }
}

# EC2 Instance: asg-ghostrpc-stage-blue
# Original ID: i-0dd5ea6a58525b2ac
# Original Type: t3a.small
resource "aws_instance" "asg-ghostrpc-stage-blue" {
  ami           = "ami-0091208de35b8d49b"
  instance_type = "t3a.small"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2b.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2b.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0e2e9a590c75ed9fe.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    "aws_security_group.elementSeries_prod_vpc.id",
  ]

  iam_instance_profile = "asg-ghostrpc-stage-blue"

  ebs_optimized = true
  monitoring    = true

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "asg-ghostrpc-stage-blue"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-0dd5ea6a58525b2ac"
    "aws:ec2launchtemplate:version" = "3"
    Environment = "stage"
    ami_id = "ami-0091208de35b8d49b"
    ANSIBLE_PLAY = "plays/base-ami-ghostrpc-stage.yml"
    ANSIBLE_BRANCH = "upgrade-2204-base"
    MakeSnapshotLongTerm = "False"
    "aws:ec2launchtemplate:id" = "lt-02f309985479760cc"
    "N/A" = "owned"
    ENV_VERSION = ""
    "aws:autoscaling:groupName" = "asg-ghostrpc-stage-blue"
    zone_id = "Z0510321LZZI860UP8GE"
    route53_record_prefix = "asg-ghostrpc-stage-blue"
    vpc_domain = "sydney.stage.adroitcreations.org"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    ANSIBLE_DC = "stage-ap-southeast-2"
    "aws:ec2:fleet-id" = "fleet-17b6dbaf-0b04-4ebc-0632-0da2bf17e68e"
    ANSIBLE_POOL = "ac-stage"
    MakeSnapshot = "False"
    ANSIBLE_ROLE = "ghostrpc-stage"
    "Cost Center" = "ghostrpc"
    MakeSnapshotShortTerm = "False"
  }
}

# EC2 Instance: elementorg-test-ngsc
# Original ID: i-0e266203042da111c
# Original Type: t3a.small
resource "aws_instance" "elementorg-test-ngsc" {
  ami           = "ami-019b9823dfb70e1ce"
  instance_type = "t3a.small"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2b.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2b.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ee33593e107f36f1.id",
    "aws_security_group.sg-0d7d46135b4284504.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    "aws_security_group.office-vpn-ssh-ingress.id",
  ]

  iam_instance_profile = "elementorg-test-ngsc-profile"

  ebs_optimized = true
  monitoring    = true

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "elementorg-test-ngsc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-0e266203042da111c"
    ANSIBLE_DC = "stage-ap-southeast-2"
    SUDOERS_GROUPS_TAG = "engineering,platform,security"
    zone_id = "Z0510321LZZI860UP8GE"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    ANSIBLE_PLAY = "plays/elementorg-test-ngsc.yml"
    ami_id = "ami-019b9823dfb70e1ce"
    ANSIBLE_ROLE = "elementorg"
    "Cost Center" = "elementOrg"
    vpc_domain = "sydney.stage.adroitcreations.org"
    ANSIBLE_BRANCH = "upgrade-2204-base"
    Environment = "stage"
    route53_record_prefix = "elementorg-test-ngsc"
    Terraform = "true"
    ANSIBLE_POOL = "ac-stage"
  }
}

# EC2 Instance: elementorg-test-griffith
# Original ID: i-01bc6a6725339df32
# Original Type: t3a.small
resource "aws_instance" "elementorg-test-griffith" {
  ami           = "ami-0ae9e870e9aba19af"
  instance_type = "t3a.small"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2b.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2b.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ee33593e107f36f1.id",
    "aws_security_group.sg-0856f781bc6a82376.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    "aws_security_group.office-vpn-ssh-ingress.id",
  ]

  iam_instance_profile = "elementorg-test-griffith-profile"

  ebs_optimized = true
  monitoring    = false

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "elementorg-test-griffith"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-01bc6a6725339df32"
    Terraform = "true"
    ami_id = "ami-0ae9e870e9aba19af"
    "Cost Center" = "elementOrg"
    ANSIBLE_DC = "stage-ap-southeast-2"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    route53_record_prefix = "elementorg-test-griffith"
    ANSIBLE_POOL = "ac-stage"
    zone_id = "Z0510321LZZI860UP8GE"
    ANSIBLE_PLAY = "plays/elementorg-test-griffith.yml"
    ANSIBLE_BRANCH = "upgrade-2204-base"
    ANSIBLE_ROLE = "elementorg"
    SUDOERS_GROUPS_TAG = "engineering,platform,security"
    Environment = "stage"
    vpc_domain = "sydney.stage.adroitcreations.org"
  }
}

# EC2 Instance: asg-etime-stage-b-14si
# Original ID: i-02428f54750a4785b
# Original Type: m8g.medium
resource "aws_instance" "asg-etime-stage-b-14si" {
  ami           = "ami-04ca030c26a97465a"
  instance_type = "m8g.medium"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2b.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2b.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]

  iam_instance_profile = "asg-etime-stage-b-14si"

  ebs_optimized = true
  monitoring    = true

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "asg-etime-stage-b-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-02428f54750a4785b"
    vpc_domain = "sydney.stage.adroitcreations.org"
    MakeSnapshot = "False"
    "N/A" = "owned"
    "aws:ec2:fleet-id" = "fleet-093cefbc-b68e-4e2f-2630-838a3bedb8ec"
    Environment = "stage"
    "aws:ec2launchtemplate:id" = "lt-0dbd35aafb1de6063"
    ANSIBLE_BRANCH = "upgrade-2204"
    "Cost Center" = "etime"
    zone_id = "Z0510321LZZI860UP8GE"
    ami_id = "ami-04ca030c26a97465a"
    route53_record_prefix = "asg-etime-stage-b-14si"
    "aws:autoscaling:groupName" = "asg-etime-stage-b-14si"
    "aws:ec2launchtemplate:version" = "11"
    ANSIBLE_ROLE = "etime-stage"
    MakeSnapshotLongTerm = "False"
    ANSIBLE_PLAY = "plays/base-ami-etime-stage-new-env-14si.yml"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    ANSIBLE_DC = "stage-ap-southeast-2"
    ENV_VERSION = "14si"
    ANSIBLE_POOL = "ac-stage"
    MakeSnapshotShortTerm = "False"
  }
}

# EC2 Instance: asg-elementtime-stage-blue
# Original ID: i-0edbe7acedc745039
# Original Type: m8g.medium
resource "aws_instance" "asg-elementtime-stage-blue" {
  ami           = "ami-04ca030c26a97465a"
  instance_type = "m8g.medium"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2b.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2b.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
  ]

  iam_instance_profile = "asg-elementtime-stage-blue"

  ebs_optimized = true
  monitoring    = true

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "asg-elementtime-stage-blue"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-0edbe7acedc745039"
    "aws:ec2:fleet-id" = "fleet-1714d12f-a98e-c49c-2632-a78238544b8f"
    ANSIBLE_ROLE = "elementtime-stage"
    MakeSnapshotShortTerm = "False"
    MakeSnapshotLongTerm = "False"
    ENV_VERSION = ""
    "aws:autoscaling:groupName" = "asg-elementtime-stage-blue"
    ANSIBLE_PLAY = "plays/base-ami-etime-stage.yml"
    route53_record_prefix = "asg-elementtime-stage-blue"
    vpc_domain = "sydney.stage.adroitcreations.org"
    ANSIBLE_BRANCH = "upgrade-2204-fix-vul-improve"
    Environment = "stage"
    "aws:ec2launchtemplate:version" = "18"
    zone_id = "Z0510321LZZI860UP8GE"
    "aws:ec2launchtemplate:id" = "lt-0f2b473baa85e32a2"
    "N/A" = "owned"
    MakeSnapshot = "False"
    "Cost Center" = "elementtime"
    ANSIBLE_POOL = "ac-stage"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    ANSIBLE_DC = "stage-ap-southeast-2"
    ami_id = "ami-04ca030c26a97465a"
  }
}

# EC2 Instance: elementorg-griffith
# Original ID: i-001d304ab85c746b2
# Original Type: c6a.large
resource "aws_instance" "elementorg-griffith" {
  ami           = "ami-0ae9e870e9aba19af"
  instance_type = "c6a.large"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2b.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2b.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ee33593e107f36f1.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    "aws_security_group.sg-05e1cde8f7af63483.id",
    "aws_security_group.office-vpn-ssh-ingress.id",
  ]

  iam_instance_profile = "elementorg-griffith-profile"

  ebs_optimized = true
  monitoring    = false

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "elementorg-griffith"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-001d304ab85c746b2"
    ami_id = "ami-0ae9e870e9aba19af"
    ANSIBLE_BRANCH = "upgrade-2204-base"
    route53_record_prefix = "elementorg-griffith"
    SUDOERS_GROUPS_TAG = "engineering,platform,security"
    ANSIBLE_ROLE = "elementorg"
    ANSIBLE_POOL = "ac-stage"
    Terraform = "true"
    ANSIBLE_DC = "stage-ap-southeast-2"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    vpc_domain = "sydney.stage.adroitcreations.org"
    ANSIBLE_PLAY = "plays/elementorg-griffith.yml"
    "Cost Center" = "elementOrg"
    zone_id = "Z0510321LZZI860UP8GE"
    Environment = "stage"
  }
}

# EC2 Instance: elementorg-sa-fires
# Original ID: i-06d60597f00e4f830
# Original Type: t3a.small
resource "aws_instance" "elementorg-sa-fires" {
  ami           = "ami-019b9823dfb70e1ce"
  instance_type = "t3a.small"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2b.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2b.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ee33593e107f36f1.id",
    "aws_security_group.sg-0d8fca21c227c3464.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    "aws_security_group.office-vpn-ssh-ingress.id",
  ]

  iam_instance_profile = "elementorg-sa-fires-profile"

  ebs_optimized = true
  monitoring    = false

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "elementorg-sa-fires"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-06d60597f00e4f830"
    route53_record_prefix = "elementorg-sa-fires"
    ANSIBLE_BRANCH = "upgrade-2204-base"
    "Cost Center" = "elementOrg"
    Environment = "stage"
    vpc_domain = "sydney.stage.adroitcreations.org"
    ami_id = "ami-019b9823dfb70e1ce"
    ANSIBLE_ROLE = "elementorg"
    zone_id = "Z0510321LZZI860UP8GE"
    SUDOERS_GROUPS_TAG = "engineering,platform,security"
    Terraform = "true"
    ANSIBLE_DC = "stage-ap-southeast-2"
    ANSIBLE_PLAY = "plays/elementorg-sa-fires.yml"
    ANSIBLE_POOL = "ac-stage"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
  }
}

# EC2 Instance: elementorg-leeton-sandbox
# Original ID: i-0779f257a291f5a6f
# Original Type: t3a.small
resource "aws_instance" "elementorg-leeton-sandbox" {
  ami           = "ami-0c71f3454344fdf8d"
  instance_type = "t3a.small"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2b.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2b.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ee33593e107f36f1.id",
    "aws_security_group.sg-0960763e74d2494ee.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    "aws_security_group.office-vpn-ssh-ingress.id",
  ]

  iam_instance_profile = "elementorg-leeton-sandbox-profile"

  ebs_optimized = true
  monitoring    = false

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "elementorg-leeton-sandbox"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-0779f257a291f5a6f"
    ami_id = "ami-0c71f3454344fdf8d"
    Environment = "sandbox"
    zone_id = "Z0510321LZZI860UP8GE"
    vpc_domain = "sydney.stage.adroitcreations.org"
    ANSIBLE_BRANCH = "elementorg-stage"
    ANSIBLE_DC = "stage-ap-southeast-2"
    "Cost Center" = "elementOrg"
    SUDOERS_GROUPS_TAG = "engineering,platform,security"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    ANSIBLE_PLAY = "plays/elementorg-leeton-sandbox.yml"
    route53_record_prefix = "leeton-sandbox"
    Terraform = "true"
    ANSIBLE_POOL = "ac-stage"
    ANSIBLE_ROLE = "elementorg"
  }
}

# EC2 Instance: asg-elementtime-stage-socket-green
# Original ID: i-014f649096c9d5e30
# Original Type: m8g.large
resource "aws_instance" "asg-elementtime-stage-socket-green" {
  ami           = "ami-04ca030c26a97465a"
  instance_type = "m8g.large"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2a.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2a.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
  ]

  iam_instance_profile = "asg-elementtime-stage-socket-green"

  ebs_optimized = true
  monitoring    = true

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "asg-elementtime-stage-socket-green"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-014f649096c9d5e30"
    MakeSnapshotShortTerm = "False"
    ANSIBLE_POOL = "ac-stage"
    ANSIBLE_ROLE = "elementtime-stage"
    "aws:ec2:fleet-id" = "fleet-b516d1a7-a906-4ebc-8430-0fa2621e6f38"
    MakeSnapshotLongTerm = "False"
    ANSIBLE_BRANCH = "upgrade-2204-fix-vul-improve"
    Environment = "stage"
    ami_id = "ami-04ca030c26a97465a"
    ANSIBLE_PLAY = "plays/base-ami-etime-stage-socket.yml"
    MakeSnapshot = "False"
    zone_id = "Z0510321LZZI860UP8GE"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    route53_record_prefix = "asg-elementtime-stage-socket-green"
    ANSIBLE_DC = "stage-ap-southeast-2"
    "aws:autoscaling:groupName" = "asg-elementtime-stage-socket-green"
    ENV_VERSION = ""
    "Cost Center" = "elementtime"
    vpc_domain = "sydney.stage.adroitcreations.org"
    "aws:ec2launchtemplate:version" = "17"
    "aws:ec2launchtemplate:id" = "lt-090b6efcc2b0d4f99"
    "N/A" = "owned"
  }
}

# EC2 Instance: asg-etime-stage-g-14si
# Original ID: i-021a94ee8af1b0b96
# Original Type: m8g.large
resource "aws_instance" "asg-etime-stage-g-14si_af1b0b96" {
  ami           = "ami-04ca030c26a97465a"
  instance_type = "m8g.large"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2a.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2a.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]

  iam_instance_profile = "asg-etime-stage-g-14si"

  ebs_optimized = true
  monitoring    = true

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "asg-etime-stage-g-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-021a94ee8af1b0b96"
    ANSIBLE_DC = "stage-ap-southeast-2"
    ENV_VERSION = "14si"
    route53_record_prefix = "asg-etime-stage-g-14si"
    ANSIBLE_ROLE = "etime-stage"
    ami_id = "ami-04ca030c26a97465a"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    "Cost Center" = "etime"
    zone_id = "Z0510321LZZI860UP8GE"
    MakeSnapshot = "False"
    MakeSnapshotLongTerm = "False"
    "aws:autoscaling:groupName" = "asg-etime-stage-g-14si"
    "aws:ec2launchtemplate:version" = "9"
    "aws:ec2:fleet-id" = "fleet-099cc5bc-968e-4605-2432-8b0a55edb5d8"
    ANSIBLE_PLAY = "plays/base-ami-etime-stage-new-env-14si.yml"
    vpc_domain = "sydney.stage.adroitcreations.org"
    Environment = "stage"
    MakeSnapshotShortTerm = "False"
    ANSIBLE_POOL = "ac-stage"
    "N/A" = "owned"
    ANSIBLE_BRANCH = "upgrade-2204"
    "aws:ec2launchtemplate:id" = "lt-07317d18625133ffc"
  }
}

# EC2 Instance: int_redash
# Original ID: i-044744ef1a61dcb45
# Original Type: t3.micro
resource "aws_instance" "int_redash" {
  ami           = "ami-0bae8773e653a32ec"
  instance_type = "t3.micro"

  # WARNING: Subnet aws_subnet.public-2c.id not found in graph
  subnet_id     = "aws_subnet.public-2c.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ebf9170b06104b03.id",
    "aws_security_group.sg-0c00b8511d60caa56.id",
  ]

  iam_instance_profile = "EC2Instances"

  ebs_optimized = false
  monitoring    = false

  root_block_device {
    delete_on_termination = false
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "int_redash"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-044744ef1a61dcb45"
    MakeSnapshotShortTerm = "True"
    os = "ubuntu"
  }
}

# EC2 Instance: pro_ghostrpc
# Original ID: i-0e2c54afbf0399b2f
# Original Type: t3.micro
resource "aws_instance" "pro_ghostrpc" {
  ami           = "ami-0c36c9dba2dca5ca4"
  instance_type = "t3.micro"

  # WARNING: Subnet aws_subnet.public-2a.id not found in graph
  subnet_id     = "aws_subnet.public-2a.id"

  vpc_security_group_ids = [
    "aws_security_group.elementSeries.id",
    "aws_security_group.sg-0c00b8511d60caa56.id",
  ]

  iam_instance_profile = "EC2Instances"

  ebs_optimized = false
  monitoring    = false

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "pro_ghostrpc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-0e2c54afbf0399b2f"
    MakeSnapshotShortTerm = "True"
  }
}

# EC2 Instance: int_jumpbox
# Original ID: i-0e3c95616a83b068f
# Original Type: t3.micro
resource "aws_instance" "int_jumpbox" {
  ami           = "ami-08bd00d7713a39e7d"
  instance_type = "t3.micro"

  # WARNING: Subnet aws_subnet.public-2b.id not found in graph
  subnet_id     = "aws_subnet.public-2b.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ebf9170b06104b03.id",
    "aws_security_group.elementSeries.id",
  ]

  iam_instance_profile = "gateway_upgrade"

  ebs_optimized = false
  monitoring    = false

  root_block_device {
    delete_on_termination = false
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "int_jumpbox"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-0e3c95616a83b068f"
    os = "centos"
  }
}

# EC2 Instance: pro_other_elements_9
# Original ID: i-082289afa2e9d0a8a
# Original Type: t3.micro
resource "aws_instance" "pro_other_elements_9" {
  ami           = "ami-0a0bc4282fb32e6d8"
  instance_type = "t3.micro"

  # WARNING: Subnet aws_subnet.public-2c.id not found in graph
  subnet_id     = "aws_subnet.public-2c.id"

  vpc_security_group_ids = [
    "aws_security_group.elementSeries.id",
    "aws_security_group.sg-0c00b8511d60caa56.id",
  ]

  iam_instance_profile = "EC2Instances"

  ebs_optimized = false
  monitoring    = false

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "pro_other_elements_9"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-082289afa2e9d0a8a"
    pro_elementsup = "g1"
    pro_elementrec = "g1"
    os = "ubuntu"
    pro_elementstaff = "g1"
    pro_elementstaff2 = "g1"
    MakeSnapshotShortTerm = "True"
    pro_elementcentre = "g1"
  }
}

# EC2 Instance: elementorg-leeton-c5large
# Original ID: i-0ab98d811657c7ad6
# Original Type: c5a.large
resource "aws_instance" "elementorg-leeton-c5large" {
  ami           = "ami-019b9823dfb70e1ce"
  instance_type = "c5a.large"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2a.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2a.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ee33593e107f36f1.id",
    "aws_security_group.sg-07f567a32cb484323.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
    "aws_security_group.office-vpn-ssh-ingress.id",
  ]

  iam_instance_profile = "elementorg-profile"

  ebs_optimized = true
  monitoring    = true

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "elementorg-leeton-c5large"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-0ab98d811657c7ad6"
    ANSIBLE_DC = "stage-ap-southeast-2"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    SUDOERS_GROUPS_TAG = "engineering,platform,security"
    "Cost Center" = "elementOrg"
    route53_record_prefix = "elementorg-leeton-large"
    Terraform = "true"
    ANSIBLE_ROLE = "elementorg"
    ANSIBLE_POOL = "ac-stage"
    Environment = "stage"
    ANSIBLE_PLAY = "plays/elementorg-leeton.yml"
    ANSIBLE_BRANCH = "upgrade-2204-base"
    vpc_domain = "sydney.stage.adroitcreations.org"
    ami_id = "ami-019b9823dfb70e1ce"
    zone_id = "Z0510321LZZI860UP8GE"
  }
}

# EC2 Instance: asg-etime-stage-g-14si
# Original ID: i-0f9f71cfbb3092b34
# Original Type: m8g.large
resource "aws_instance" "asg-etime-stage-g-14si" {
  ami           = "ami-04ca030c26a97465a"
  instance_type = "m8g.large"

  # WARNING: Subnet aws_subnet.stage-subnet-private-ap-southeast-2c.id not found in graph
  subnet_id     = "aws_subnet.stage-subnet-private-ap-southeast-2c.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]

  iam_instance_profile = "asg-etime-stage-g-14si"

  ebs_optimized = true
  monitoring    = true

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "asg-etime-stage-g-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-0f9f71cfbb3092b34"
    ANSIBLE_ROLE = "etime-stage"
    "aws:autoscaling:groupName" = "asg-etime-stage-g-14si"
    ENV_VERSION = "14si"
    route53_record_prefix = "asg-etime-stage-g-14si"
    "aws:ec2launchtemplate:id" = "lt-07317d18625133ffc"
    "aws:ec2launchtemplate:version" = "9"
    ANSIBLE_DC = "stage-ap-southeast-2"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    ami_id = "ami-04ca030c26a97465a"
    ANSIBLE_POOL = "ac-stage"
    MakeSnapshotShortTerm = "False"
    ANSIBLE_PLAY = "plays/base-ami-etime-stage-new-env-14si.yml"
    "aws:ec2:fleet-id" = "fleet-099e4d9e-9e8c-4e27-2692-a982dfd746c9"
    MakeSnapshot = "False"
    "N/A" = "owned"
    ANSIBLE_BRANCH = "upgrade-2204"
    MakeSnapshotLongTerm = "False"
    Environment = "stage"
    vpc_domain = "sydney.stage.adroitcreations.org"
    "Cost Center" = "etime"
    zone_id = "Z0510321LZZI860UP8GE"
  }
}

# EC2 Instance: test_databases
# Original ID: i-0e9de3bb79bf84144
# Original Type: t3.micro
resource "aws_instance" "test_databases" {
  ami           = "ami-0a0bc4282fb32e6d8"
  instance_type = "t3.micro"

  # WARNING: Subnet aws_subnet.public-2a.id not found in graph
  subnet_id     = "aws_subnet.public-2a.id"

  vpc_security_group_ids = [
    "aws_security_group.sg-0c00b8511d60caa56.id",
    "aws_security_group.sg-022cca1d7ed3a7a0a.id",
  ]

  iam_instance_profile = "EC2Instances"

  ebs_optimized = false
  monitoring    = false

  root_block_device {
    delete_on_termination = true
  }

  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "optional"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name        = "test_databases"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "i-0e9de3bb79bf84144"
    os = "ubuntu"
  }
}