# EBS Volume: etime-stage-skt-g-14si
resource "aws_ebs_volume" "etime-stage-skt-g-14si_1" {
  availability_zone = "ap-southeast-2c"
  size              = 1
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true

  tags = {
    Name        = "etime-stage-skt-g-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0a5f9ed06d07e21a9"
    MakeSnapshot = "False"
    "Cost Center" = "etime"
    vpc_domain = "sydney.stage.adroitcreations.org"
    MakeSnapshotLongTerm = "False"
    MakeSnapshotShortTerm = "False"
    Terraform = "true"
    Environment = "stage"
    ami_id = "ami-04ca030c26a97465a"
  }
}

# EBS Volume: vol-0f8146c74b9278f89
resource "aws_ebs_volume" "vol-0f8146c74b9278f89" {
  availability_zone = "ap-southeast-2b"
  size              = 64
  type              = "gp2"

  encrypted = true
  snapshot_id = "snap-0055ed17f5b799606"

  tags = {
    Name        = "vol-0f8146c74b9278f89"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0f8146c74b9278f89"
  }
}

# EBS Volume: vol-07679a375d548f4cc
resource "aws_ebs_volume" "vol-07679a375d548f4cc" {
  availability_zone = "ap-southeast-2a"
  size              = 50
  type              = "gp2"

  encrypted = true
  snapshot_id = "snap-0670ddf991e2fe0de"

  tags = {
    Name        = "vol-07679a375d548f4cc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-07679a375d548f4cc"
    "Cost Center" = "Platform"
    MakeSnapshotShortTerm = "False"
    MakeSnapshot = "False"
    MakeSnapshotLongTerm = "False"
  }
}

# EBS Volume: vol-0a43efa642ad9fdfc
resource "aws_ebs_volume" "vol-0a43efa642ad9fdfc" {
  availability_zone = "ap-southeast-2b"
  size              = 200
  type              = "gp2"

  encrypted = true
  snapshot_id = "snap-058b3614f23ff3bee"

  tags = {
    Name        = "vol-0a43efa642ad9fdfc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0a43efa642ad9fdfc"
    MakeSnapshotLongTerm = "False"
    MakeSnapshotShortTerm = "False"
    "Cost Center" = "elementOrg"
    MakeSnapshot = "False"
  }
}

# EBS Volume: elementtime-stage-green
resource "aws_ebs_volume" "elementtime-stage-green_3" {
  availability_zone = "ap-southeast-2c"
  size              = 100
  type              = "gp3"

  iops = 4000
  throughput = 250
  encrypted = true
  snapshot_id = "snap-06b4134076d0f791c"

  tags = {
    Name        = "elementtime-stage-green"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-08c7cd44854a5aa0f"
    MakeSnapshotLongTerm = "False"
    MakeSnapshotShortTerm = "False"
    Environment = "stage"
    ami_id = "ami-04ca030c26a97465a"
    "Cost Center" = "elementtime"
    Terraform = "true"
    MakeSnapshot = "False"
    vpc_domain = "sydney.stage.adroitcreations.org"
  }
}

# EBS Volume: vol-03d941f62c9edb247
resource "aws_ebs_volume" "vol-03d941f62c9edb247" {
  availability_zone = "ap-southeast-2b"
  size              = 1
  type              = "gp2"

  encrypted = true

  tags = {
    Name        = "vol-03d941f62c9edb247"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-03d941f62c9edb247"
    MakeSnapshotLongTerm = "False"
    MakeSnapshotShortTerm = "False"
    MakeSnapshot = "False"
    "Cost Center" = "elementOrg"
  }
}

# EBS Volume: vol-07dab0dfd1e1e6b13
resource "aws_ebs_volume" "vol-07dab0dfd1e1e6b13" {
  availability_zone = "ap-southeast-2b"
  size              = 50
  type              = "gp2"

  encrypted = true
  snapshot_id = "snap-058b3614f23ff3bee"

  tags = {
    Name        = "vol-07dab0dfd1e1e6b13"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-07dab0dfd1e1e6b13"
    MakeSnapshotLongTerm = "False"
    MakeSnapshot = "False"
    "Cost Center" = "elementOrg"
    MakeSnapshotShortTerm = "False"
  }
}

# EBS Volume: vol-0fb689c2f7d677eb5
resource "aws_ebs_volume" "vol-0fb689c2f7d677eb5" {
  availability_zone = "ap-southeast-2b"
  size              = 50
  type              = "gp2"

  encrypted = true
  snapshot_id = "snap-058b3614f23ff3bee"

  tags = {
    Name        = "vol-0fb689c2f7d677eb5"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0fb689c2f7d677eb5"
    MakeSnapshot = "False"
    MakeSnapshotShortTerm = "False"
    "Cost Center" = "Platform"
    MakeSnapshotLongTerm = "False"
  }
}

# EBS Volume: elementtime-stage-socket-blue
resource "aws_ebs_volume" "elementtime-stage-socket-blue_1" {
  availability_zone = "ap-southeast-2b"
  size              = 100
  type              = "gp3"

  iops = 4000
  throughput = 250
  encrypted = true
  snapshot_id = "snap-06b4134076d0f791c"

  tags = {
    Name        = "elementtime-stage-socket-blue"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-07354229a28b0668e"
    Environment = "stage"
    MakeSnapshotShortTerm = "False"
    MakeSnapshot = "False"
    ami_id = "ami-04ca030c26a97465a"
    vpc_domain = "sydney.stage.adroitcreations.org"
    "Cost Center" = "elementtime"
    Terraform = "true"
    MakeSnapshotLongTerm = "False"
  }
}

# EBS Volume: elementcentre-stage-blue
resource "aws_ebs_volume" "elementcentre-stage-blue_1" {
  availability_zone = "ap-southeast-2b"
  size              = 100
  type              = "gp3"

  iops = 4000
  throughput = 250
  encrypted = true
  snapshot_id = "snap-0c28e66d069da2a71"

  tags = {
    Name        = "elementcentre-stage-blue"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-05b4c785e19bb33a0"
    Terraform = "true"
    "Cost Center" = "elementcentre"
    vpc_domain = "sydney.stage.adroitcreations.org"
    ami_id = "ami-03dbcf19ff380ef96"
    MakeSnapshot = "False"
    MakeSnapshotLongTerm = "False"
    MakeSnapshotShortTerm = "False"
    Environment = "stage"
  }
}

# EBS Volume: vol-0e4f77d5deefc1100
resource "aws_ebs_volume" "vol-0e4f77d5deefc1100" {
  availability_zone = "ap-southeast-2a"
  size              = 1
  type              = "gp2"

  encrypted = true

  tags = {
    Name        = "vol-0e4f77d5deefc1100"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0e4f77d5deefc1100"
    MakeSnapshotLongTerm = "False"
    MakeSnapshotShortTerm = "False"
    "Cost Center" = "Platform"
    MakeSnapshot = "False"
  }
}

# EBS Volume: vol-0c52abbe51d8f0fc7
resource "aws_ebs_volume" "vol-0c52abbe51d8f0fc7" {
  availability_zone = "ap-southeast-2a"
  size              = 50
  type              = "gp2"

  encrypted = true
  snapshot_id = "snap-07b13db869e3b773f"

  tags = {
    Name        = "vol-0c52abbe51d8f0fc7"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0c52abbe51d8f0fc7"
    MakeSnapshot = "False"
    "Cost Center" = "Platform"
    MakeSnapshotShortTerm = "False"
    MakeSnapshotLongTerm = "False"
  }
}

# EBS Volume: vol-007eb15bc8728040f
resource "aws_ebs_volume" "vol-007eb15bc8728040f" {
  availability_zone = "ap-southeast-2b"
  size              = 200
  type              = "standard"

  encrypted = true

  tags = {
    Name        = "vol-007eb15bc8728040f"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-007eb15bc8728040f"
  }
}

# EBS Volume: vol-0ac16c64f22b7eaf4
resource "aws_ebs_volume" "vol-0ac16c64f22b7eaf4" {
  availability_zone = "ap-southeast-2b"
  size              = 100
  type              = "gp2"

  encrypted = true
  snapshot_id = "snap-058b3614f23ff3bee"

  tags = {
    Name        = "vol-0ac16c64f22b7eaf4"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0ac16c64f22b7eaf4"
    MakeSnapshot = "False"
    "Cost Center" = "elementOrg"
    MakeSnapshotLongTerm = "False"
    MakeSnapshotShortTerm = "False"
  }
}

# EBS Volume: vol-0ab033e26fda150ba
resource "aws_ebs_volume" "vol-0ab033e26fda150ba" {
  availability_zone = "ap-southeast-2b"
  size              = 64
  type              = "gp2"

  encrypted = true
  snapshot_id = "snap-0055ed17f5b799606"

  tags = {
    Name        = "vol-0ab033e26fda150ba"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0ab033e26fda150ba"
  }
}

# EBS Volume: elementtime-stage-green
resource "aws_ebs_volume" "elementtime-stage-green_2" {
  availability_zone = "ap-southeast-2a"
  size              = 1
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true

  tags = {
    Name        = "elementtime-stage-green"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0c43fb259cf7bef15"
    Terraform = "true"
    vpc_domain = "sydney.stage.adroitcreations.org"
    "Cost Center" = "elementtime"
    MakeSnapshot = "False"
    MakeSnapshotLongTerm = "False"
    MakeSnapshotShortTerm = "False"
    ami_id = "ami-04ca030c26a97465a"
    Environment = "stage"
  }
}

# EBS Volume: vol-0c040206f0c824050
resource "aws_ebs_volume" "vol-0c040206f0c824050" {
  availability_zone = "ap-southeast-2a"
  size              = 1
  type              = "gp2"

  encrypted = true

  tags = {
    Name        = "vol-0c040206f0c824050"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0c040206f0c824050"
    MakeSnapshot = "False"
    MakeSnapshotShortTerm = "False"
    "Cost Center" = "Platform"
    MakeSnapshotLongTerm = "False"
  }
}

# EBS Volume: elementsup-stage-blue
resource "aws_ebs_volume" "elementsup-stage-blue_1" {
  availability_zone = "ap-southeast-2a"
  size              = 100
  type              = "gp3"

  iops = 4000
  throughput = 250
  encrypted = true
  snapshot_id = "snap-0c28e66d069da2a71"

  tags = {
    Name        = "elementsup-stage-blue"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-03579615eff50b40a"
    Environment = "stage"
    MakeSnapshotLongTerm = "False"
    MakeSnapshotShortTerm = "False"
    Terraform = "true"
    "Cost Center" = "elementsup"
    MakeSnapshot = "False"
    ami_id = "ami-03dbcf19ff380ef96"
    vpc_domain = "sydney.stage.adroitcreations.org"
  }
}

# EBS Volume: test_elements
resource "aws_ebs_volume" "test_elements" {
  availability_zone = "ap-southeast-2b"
  size              = 100
  type              = "gp2"

  encrypted = true
  snapshot_id = "snap-045584ed6cbbc8a35"

  tags = {
    Name        = "test_elements"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0eff9d79d6a9a5d6d"
  }
}

# EBS Volume: vol-0a7555eaeb569de74
resource "aws_ebs_volume" "vol-0a7555eaeb569de74" {
  availability_zone = "ap-southeast-2a"
  size              = 100
  type              = "gp2"

  encrypted = true
  snapshot_id = "snap-0025cb46cf35f9b08"

  tags = {
    Name        = "vol-0a7555eaeb569de74"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0a7555eaeb569de74"
  }
}

# EBS Volume: elementstaff-stage-blue
resource "aws_ebs_volume" "elementstaff-stage-blue_1" {
  availability_zone = "ap-southeast-2a"
  size              = 1
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true

  tags = {
    Name        = "elementstaff-stage-blue"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-044fbd5e406012703"
    vpc_domain = "sydney.stage.adroitcreations.org"
    MakeSnapshot = "False"
    ami_id = "ami-0299dc8622d5d2613"
    MakeSnapshotLongTerm = "False"
    MakeSnapshotShortTerm = "False"
    "Cost Center" = "elementstaff"
    Terraform = "true"
    Environment = "stage"
  }
}

# EBS Volume: etime-stage-skt-b-14si
resource "aws_ebs_volume" "etime-stage-skt-b-14si_1" {
  availability_zone = "ap-southeast-2b"
  size              = 100
  type              = "gp3"

  iops = 4000
  throughput = 250
  encrypted = true
  snapshot_id = "snap-06b4134076d0f791c"

  tags = {
    Name        = "etime-stage-skt-b-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-08b4c8bd820f7ad22"
    Terraform = "true"
    ami_id = "ami-04ca030c26a97465a"
    vpc_domain = "sydney.stage.adroitcreations.org"
    "Cost Center" = "etime"
    Environment = "stage"
    MakeSnapshotLongTerm = "False"
    MakeSnapshotShortTerm = "False"
    MakeSnapshot = "False"
  }
}

# EBS Volume: vol-0f9a76faabfb836ae
resource "aws_ebs_volume" "vol-0f9a76faabfb836ae" {
  availability_zone = "ap-southeast-2b"
  size              = 100
  type              = "gp3"

  iops = 4000
  throughput = 250
  encrypted = true
  snapshot_id = "snap-058b3614f23ff3bee"

  tags = {
    Name        = "vol-0f9a76faabfb836ae"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0f9a76faabfb836ae"
    "Cost Center" = "elementOrg"
    MakeSnapshot = "False"
    MakeSnapshotShortTerm = "False"
    MakeSnapshotLongTerm = "False"
  }
}

# EBS Volume: etime-stage-skt-g-14si
resource "aws_ebs_volume" "etime-stage-skt-g-14si" {
  availability_zone = "ap-southeast-2c"
  size              = 100
  type              = "gp3"

  iops = 4000
  throughput = 250
  encrypted = true
  snapshot_id = "snap-06b4134076d0f791c"

  tags = {
    Name        = "etime-stage-skt-g-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0cc7b246c8d3e6521"
    Environment = "stage"
    MakeSnapshotLongTerm = "False"
    Terraform = "true"
    MakeSnapshot = "False"
    ami_id = "ami-04ca030c26a97465a"
    vpc_domain = "sydney.stage.adroitcreations.org"
    "Cost Center" = "etime"
    MakeSnapshotShortTerm = "False"
  }
}

# EBS Volume: vol-0aa4668601927b780
resource "aws_ebs_volume" "vol-0aa4668601927b780" {
  availability_zone = "ap-southeast-2b"
  size              = 1
  type              = "gp2"

  encrypted = true

  tags = {
    Name        = "vol-0aa4668601927b780"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0aa4668601927b780"
    MakeSnapshotLongTerm = "False"
    MakeSnapshotShortTerm = "False"
    "Cost Center" = "Platform"
    MakeSnapshot = "False"
  }
}

# EBS Volume: ghostrpc-stage-blue
resource "aws_ebs_volume" "ghostrpc-stage-blue_1" {
  availability_zone = "ap-southeast-2b"
  size              = 100
  type              = "gp2"

  encrypted = true
  snapshot_id = "snap-0fa1332d7dec4d72a"

  tags = {
    Name        = "ghostrpc-stage-blue"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0e84845d164097940"
    ami_id = "ami-0091208de35b8d49b"
    Environment = "stage"
    MakeSnapshotShortTerm = "False"
    vpc_domain = "sydney.stage.adroitcreations.org"
    "Cost Center" = "ghostrpc"
    MakeSnapshot = "False"
    Terraform = "true"
    MakeSnapshotLongTerm = "False"
  }
}

# EBS Volume: vol-0d9f9121f56f5e7ea
resource "aws_ebs_volume" "vol-0d9f9121f56f5e7ea" {
  availability_zone = "ap-southeast-2b"
  size              = 100
  type              = "gp2"

  encrypted = true
  snapshot_id = "snap-058b3614f23ff3bee"

  tags = {
    Name        = "vol-0d9f9121f56f5e7ea"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0d9f9121f56f5e7ea"
    MakeSnapshotShortTerm = "False"
    MakeSnapshotLongTerm = "False"
    MakeSnapshot = "False"
    "Cost Center" = "elementOrg"
  }
}

# EBS Volume: ghostrpc-stage-blue
resource "aws_ebs_volume" "ghostrpc-stage-blue" {
  availability_zone = "ap-southeast-2b"
  size              = 1
  type              = "gp2"

  encrypted = true

  tags = {
    Name        = "ghostrpc-stage-blue"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-06c39f1b8bd4b11b2"
    MakeSnapshot = "False"
    vpc_domain = "sydney.stage.adroitcreations.org"
    "Cost Center" = "ghostrpc"
    MakeSnapshotLongTerm = "False"
    MakeSnapshotShortTerm = "False"
    Environment = "stage"
    Terraform = "true"
    ami_id = "ami-0091208de35b8d49b"
  }
}

# EBS Volume: vol-04973c7cc56a42839
resource "aws_ebs_volume" "vol-04973c7cc56a42839" {
  availability_zone = "ap-southeast-2b"
  size              = 1
  type              = "gp2"

  encrypted = true

  tags = {
    Name        = "vol-04973c7cc56a42839"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-04973c7cc56a42839"
    MakeSnapshot = "False"
    MakeSnapshotLongTerm = "False"
    "Cost Center" = "elementOrg"
    MakeSnapshotShortTerm = "False"
  }
}

# EBS Volume: vol-0d732bace618b2599
resource "aws_ebs_volume" "vol-0d732bace618b2599" {
  availability_zone = "ap-southeast-2b"
  size              = 100
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true
  snapshot_id = "snap-083e5486bfaf36ed8"

  tags = {
    Name        = "vol-0d732bace618b2599"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0d732bace618b2599"
  }
}

# EBS Volume: vol-066d87ab77e98a669
resource "aws_ebs_volume" "vol-066d87ab77e98a669" {
  availability_zone = "ap-southeast-2b"
  size              = 200
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true
  snapshot_id = "snap-0bce1b705e606fc8c"

  tags = {
    Name        = "vol-066d87ab77e98a669"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-066d87ab77e98a669"
  }
}

# EBS Volume: etime-stage-b-14si
resource "aws_ebs_volume" "etime-stage-b-14si_1" {
  availability_zone = "ap-southeast-2b"
  size              = 1
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true

  tags = {
    Name        = "etime-stage-b-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-08dcf119e3eb6ea11"
    "Cost Center" = "etime"
    MakeSnapshot = "False"
    vpc_domain = "sydney.stage.adroitcreations.org"
    MakeSnapshotLongTerm = "False"
    Environment = "stage"
    MakeSnapshotShortTerm = "False"
    Terraform = "true"
    ami_id = "ami-04ca030c26a97465a"
  }
}

# EBS Volume: elementtime-stage-blue
resource "aws_ebs_volume" "elementtime-stage-blue_1" {
  availability_zone = "ap-southeast-2b"
  size              = 1
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true

  tags = {
    Name        = "elementtime-stage-blue"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-07a8c6174e64db727"
    "Cost Center" = "elementtime"
    Environment = "stage"
    MakeSnapshotLongTerm = "False"
    ami_id = "ami-04ca030c26a97465a"
    MakeSnapshot = "False"
    Terraform = "true"
    MakeSnapshotShortTerm = "False"
    vpc_domain = "sydney.stage.adroitcreations.org"
  }
}

# EBS Volume: elementorg-griffith
resource "aws_ebs_volume" "elementorg-griffith_1" {
  availability_zone = "ap-southeast-2b"
  size              = 1
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true

  tags = {
    Name        = "elementorg-griffith"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-085d134795d840287"
    ANSIBLE_POOL = "ac-stage"
    ANSIBLE_BRANCH = "upgrade-2204-base"
    MakeSnapshot = "False"
    ANSIBLE_ROLE = "elementorg"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    MakeSnapshotShortTerm = "False"
    ANSIBLE_DC = "stage-ap-southeast-2"
    SUDOERS_GROUPS_TAG = "engineering,platform,security"
    "Cost Center" = "elementOrg"
    MakeSnapshotLongTerm = "False"
    ANSIBLE_PLAY = "plays/elementorg-griffith.yml"
  }
}

# EBS Volume: vol-0a8f67a963073f2ca
resource "aws_ebs_volume" "vol-0a8f67a963073f2ca" {
  availability_zone = "ap-southeast-2b"
  size              = 200
  type              = "gp2"

  encrypted = true

  tags = {
    Name        = "vol-0a8f67a963073f2ca"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0a8f67a963073f2ca"
    MakeSnapshotLongTerm = "False"
    MakeSnapshotShortTerm = "False"
    "Cost Center" = "elementOrg"
    MakeSnapshot = "False"
  }
}

# EBS Volume: vol-093a2f17f4f45844b
resource "aws_ebs_volume" "vol-093a2f17f4f45844b" {
  availability_zone = "ap-southeast-2b"
  size              = 100
  type              = "gp2"

  encrypted = true
  snapshot_id = "snap-058b3614f23ff3bee"

  tags = {
    Name        = "vol-093a2f17f4f45844b"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-093a2f17f4f45844b"
    MakeSnapshotLongTerm = "False"
    MakeSnapshotShortTerm = "False"
    "Cost Center" = "elementOrg"
    MakeSnapshot = "False"
  }
}

# EBS Volume: vol-023f93bac707dad7e
resource "aws_ebs_volume" "vol-023f93bac707dad7e" {
  availability_zone = "ap-southeast-2b"
  size              = 1
  type              = "gp2"

  encrypted = true

  tags = {
    Name        = "vol-023f93bac707dad7e"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-023f93bac707dad7e"
    MakeSnapshotLongTerm = "False"
    MakeSnapshotShortTerm = "False"
    "Cost Center" = "elementOrg"
    MakeSnapshot = "False"
  }
}

# EBS Volume: vol-0d543d82bbaa49951
resource "aws_ebs_volume" "vol-0d543d82bbaa49951" {
  availability_zone = "ap-southeast-2b"
  size              = 50
  type              = "gp2"

  encrypted = true
  snapshot_id = "snap-0488dba5097908f35"

  tags = {
    Name        = "vol-0d543d82bbaa49951"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0d543d82bbaa49951"
    "Cost Center" = "elementOrg"
    MakeSnapshot = "False"
    MakeSnapshotShortTerm = "False"
    MakeSnapshotLongTerm = "False"
  }
}

# EBS Volume: elementtime-stage-socket-green
resource "aws_ebs_volume" "elementtime-stage-socket-green_1" {
  availability_zone = "ap-southeast-2a"
  size              = 1
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true

  tags = {
    Name        = "elementtime-stage-socket-green"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-04356820461555354"
    MakeSnapshotShortTerm = "False"
    MakeSnapshotLongTerm = "False"
    MakeSnapshot = "False"
    "Cost Center" = "elementtime"
    Terraform = "true"
    ami_id = "ami-04ca030c26a97465a"
    vpc_domain = "sydney.stage.adroitcreations.org"
    Environment = "stage"
  }
}

# EBS Volume: vol-069512720ed249fc5
resource "aws_ebs_volume" "vol-069512720ed249fc5" {
  availability_zone = "ap-southeast-2b"
  size              = 50
  type              = "gp2"

  encrypted = true

  tags = {
    Name        = "vol-069512720ed249fc5"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-069512720ed249fc5"
    MakeSnapshotShortTerm = "False"
    MakeSnapshotLongTerm = "False"
    "Cost Center" = "elementOrg"
    MakeSnapshot = "False"
  }
}

# EBS Volume: vol-01de30020695d632e
resource "aws_ebs_volume" "vol-01de30020695d632e" {
  availability_zone = "ap-southeast-2b"
  size              = 100
  type              = "gp2"

  encrypted = true
  snapshot_id = "snap-0d764624be9a38053"

  tags = {
    Name        = "vol-01de30020695d632e"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-01de30020695d632e"
    MakeSnapshotLongTerm = "False"
    MakeSnapshotShortTerm = "False"
    MakeSnapshot = "False"
    "Cost Center" = "elementOrg"
  }
}

# EBS Volume: vol-05eba8d3cdc1c8207
resource "aws_ebs_volume" "vol-05eba8d3cdc1c8207" {
  availability_zone = "ap-southeast-2a"
  size              = 1
  type              = "gp2"

  encrypted = true

  tags = {
    Name        = "vol-05eba8d3cdc1c8207"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-05eba8d3cdc1c8207"
    MakeSnapshot = "False"
    "Cost Center" = "Platform"
    MakeSnapshotLongTerm = "False"
    MakeSnapshotShortTerm = "False"
  }
}

# EBS Volume: elementtime-stage-blue
resource "aws_ebs_volume" "elementtime-stage-blue" {
  availability_zone = "ap-southeast-2b"
  size              = 100
  type              = "gp3"

  iops = 4000
  throughput = 250
  encrypted = true
  snapshot_id = "snap-06b4134076d0f791c"

  tags = {
    Name        = "elementtime-stage-blue"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-004b063170ae5fad6"
    MakeSnapshotLongTerm = "False"
    MakeSnapshotShortTerm = "False"
    "Cost Center" = "elementtime"
    Terraform = "true"
    ami_id = "ami-04ca030c26a97465a"
    Environment = "stage"
    vpc_domain = "sydney.stage.adroitcreations.org"
    MakeSnapshot = "False"
  }
}

# EBS Volume: etime-stage-g-14si
resource "aws_ebs_volume" "etime-stage-g-14si_3" {
  availability_zone = "ap-southeast-2a"
  size              = 1
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true

  tags = {
    Name        = "etime-stage-g-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0cf77bcb9d30ac008"
    vpc_domain = "sydney.stage.adroitcreations.org"
    "Cost Center" = "etime"
    Environment = "stage"
    Terraform = "true"
    ami_id = "ami-04ca030c26a97465a"
    MakeSnapshotLongTerm = "False"
    MakeSnapshotShortTerm = "False"
    MakeSnapshot = "False"
  }
}

# EBS Volume: etime-stage-skt-b-14si
resource "aws_ebs_volume" "etime-stage-skt-b-14si" {
  availability_zone = "ap-southeast-2b"
  size              = 1
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true

  tags = {
    Name        = "etime-stage-skt-b-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0ee8e3c498f692f3b"
    "Cost Center" = "etime"
    MakeSnapshotShortTerm = "False"
    MakeSnapshotLongTerm = "False"
    vpc_domain = "sydney.stage.adroitcreations.org"
    MakeSnapshot = "False"
    Environment = "stage"
    ami_id = "ami-04ca030c26a97465a"
    Terraform = "true"
  }
}

# EBS Volume: vol-090a832bf6bf99e74
resource "aws_ebs_volume" "vol-090a832bf6bf99e74" {
  availability_zone = "ap-southeast-2b"
  size              = 1
  type              = "gp2"

  encrypted = true

  tags = {
    Name        = "vol-090a832bf6bf99e74"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-090a832bf6bf99e74"
    MakeSnapshotShortTerm = "False"
    MakeSnapshotLongTerm = "False"
    "Cost Center" = "elementOrg"
    MakeSnapshot = "False"
  }
}

# EBS Volume: elementtime-stage-socket-blue
resource "aws_ebs_volume" "elementtime-stage-socket-blue" {
  availability_zone = "ap-southeast-2b"
  size              = 1
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true

  tags = {
    Name        = "elementtime-stage-socket-blue"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-020a2000fb956c260"
    "Cost Center" = "elementtime"
    Terraform = "true"
    ami_id = "ami-04ca030c26a97465a"
    vpc_domain = "sydney.stage.adroitcreations.org"
    MakeSnapshotShortTerm = "False"
    MakeSnapshotLongTerm = "False"
    Environment = "stage"
    MakeSnapshot = "False"
  }
}

# EBS Volume: vol-020c1bf9dec458fa7
resource "aws_ebs_volume" "vol-020c1bf9dec458fa7" {
  availability_zone = "ap-southeast-2c"
  size              = 20
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true
  snapshot_id = "snap-0ea0c6f077913be72"

  tags = {
    Name        = "vol-020c1bf9dec458fa7"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-020c1bf9dec458fa7"
  }
}

# EBS Volume: etime-stage-b-14si
resource "aws_ebs_volume" "etime-stage-b-14si" {
  availability_zone = "ap-southeast-2b"
  size              = 100
  type              = "gp3"

  iops = 4000
  throughput = 250
  encrypted = true
  snapshot_id = "snap-06b4134076d0f791c"

  tags = {
    Name        = "etime-stage-b-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0bae0783cd81c3f8d"
    Environment = "stage"
    MakeSnapshotLongTerm = "False"
    MakeSnapshot = "False"
    Terraform = "true"
    ami_id = "ami-04ca030c26a97465a"
    vpc_domain = "sydney.stage.adroitcreations.org"
    MakeSnapshotShortTerm = "False"
    "Cost Center" = "etime"
  }
}

# EBS Volume: pro_ghostrpc
resource "aws_ebs_volume" "pro_ghostrpc" {
  availability_zone = "ap-southeast-2a"
  size              = 100
  type              = "gp2"

  encrypted = true
  snapshot_id = "snap-061d951eeb8219128"

  tags = {
    Name        = "pro_ghostrpc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0a63bd9e6e996448f"
    MakeSnapshotShortTerm = "True"
  }
}

# EBS Volume: elementsup-stage-blue
resource "aws_ebs_volume" "elementsup-stage-blue" {
  availability_zone = "ap-southeast-2a"
  size              = 1
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true

  tags = {
    Name        = "elementsup-stage-blue"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0f282fcc61b61e58b"
    MakeSnapshotShortTerm = "False"
    ami_id = "ami-03dbcf19ff380ef96"
    "Cost Center" = "elementsup"
    MakeSnapshot = "False"
    Terraform = "true"
    MakeSnapshotLongTerm = "False"
    Environment = "stage"
    vpc_domain = "sydney.stage.adroitcreations.org"
  }
}

# EBS Volume: elementtime-stage-green
resource "aws_ebs_volume" "elementtime-stage-green_1" {
  availability_zone = "ap-southeast-2a"
  size              = 100
  type              = "gp3"

  iops = 4000
  throughput = 250
  encrypted = true
  snapshot_id = "snap-06b4134076d0f791c"

  tags = {
    Name        = "elementtime-stage-green"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0ea1f5489a995c42e"
    MakeSnapshotShortTerm = "False"
    Environment = "stage"
    MakeSnapshot = "False"
    vpc_domain = "sydney.stage.adroitcreations.org"
    Terraform = "true"
    ami_id = "ami-04ca030c26a97465a"
    "Cost Center" = "elementtime"
    MakeSnapshotLongTerm = "False"
  }
}

# EBS Volume: vol-01dba2c99f373861c
resource "aws_ebs_volume" "vol-01dba2c99f373861c" {
  availability_zone = "ap-southeast-2b"
  size              = 50
  type              = "gp2"

  encrypted = true

  tags = {
    Name        = "vol-01dba2c99f373861c"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-01dba2c99f373861c"
  }
}

# EBS Volume: pro_other_elements_9
resource "aws_ebs_volume" "pro_other_elements_9" {
  availability_zone = "ap-southeast-2c"
  size              = 100
  type              = "gp2"

  encrypted = true
  snapshot_id = "snap-045584ed6cbbc8a35"

  tags = {
    Name        = "pro_other_elements_9"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-090d50863c861b9ea"
  }
}

# EBS Volume: vol-0eedcd588278ec991
resource "aws_ebs_volume" "vol-0eedcd588278ec991" {
  availability_zone = "ap-southeast-2a"
  size              = 50
  type              = "gp2"

  encrypted = true
  snapshot_id = "snap-058b3614f23ff3bee"

  tags = {
    Name        = "vol-0eedcd588278ec991"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0eedcd588278ec991"
    MakeSnapshotShortTerm = "False"
    MakeSnapshot = "False"
    "Cost Center" = "elementOrg"
    MakeSnapshotLongTerm = "False"
  }
}

# EBS Volume: vol-0691d3872e385aaf2
resource "aws_ebs_volume" "vol-0691d3872e385aaf2" {
  availability_zone = "ap-southeast-2b"
  size              = 1
  type              = "gp2"

  encrypted = true

  tags = {
    Name        = "vol-0691d3872e385aaf2"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0691d3872e385aaf2"
    "Cost Center" = "elementOrg"
    MakeSnapshot = "False"
    MakeSnapshotLongTerm = "False"
    MakeSnapshotShortTerm = "False"
  }
}

# EBS Volume: etime-stage-g-14si
resource "aws_ebs_volume" "etime-stage-g-14si_2" {
  availability_zone = "ap-southeast-2a"
  size              = 100
  type              = "gp3"

  iops = 4000
  throughput = 250
  encrypted = true
  snapshot_id = "snap-06b4134076d0f791c"

  tags = {
    Name        = "etime-stage-g-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0d62a8b28d5b6616c"
    MakeSnapshotLongTerm = "False"
    ami_id = "ami-04ca030c26a97465a"
    MakeSnapshot = "False"
    Terraform = "true"
    "Cost Center" = "etime"
    Environment = "stage"
    MakeSnapshotShortTerm = "False"
    vpc_domain = "sydney.stage.adroitcreations.org"
  }
}

# EBS Volume: vol-0973866874d155a25
resource "aws_ebs_volume" "vol-0973866874d155a25" {
  availability_zone = "ap-southeast-2a"
  size              = 1
  type              = "gp2"

  encrypted = true

  tags = {
    Name        = "vol-0973866874d155a25"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0973866874d155a25"
    "Cost Center" = "elementOrg"
    MakeSnapshotShortTerm = "False"
    MakeSnapshot = "False"
    MakeSnapshotLongTerm = "False"
  }
}

# EBS Volume: vol-0227dab916c48e617
resource "aws_ebs_volume" "vol-0227dab916c48e617" {
  availability_zone = "ap-southeast-2b"
  size              = 8
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true
  snapshot_id = "snap-0a7c683f30c5ecd45"

  tags = {
    Name        = "vol-0227dab916c48e617"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0227dab916c48e617"
  }
}

# EBS Volume: vol-05d2fb61417eb5ffe
resource "aws_ebs_volume" "vol-05d2fb61417eb5ffe" {
  availability_zone = "ap-southeast-2b"
  size              = 1
  type              = "gp2"

  encrypted = true

  tags = {
    Name        = "vol-05d2fb61417eb5ffe"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-05d2fb61417eb5ffe"
    "Cost Center" = "elementOrg"
    MakeSnapshotLongTerm = "False"
    MakeSnapshotShortTerm = "False"
    MakeSnapshot = "False"
  }
}

# EBS Volume: elementstaff-stage-blue
resource "aws_ebs_volume" "elementstaff-stage-blue" {
  availability_zone = "ap-southeast-2a"
  size              = 100
  type              = "gp3"

  iops = 4000
  throughput = 250
  encrypted = true
  snapshot_id = "snap-095beb7ce68e2e7ec"

  tags = {
    Name        = "elementstaff-stage-blue"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0ff9e24b9b93af56c"
    "Cost Center" = "elementstaff"
    ami_id = "ami-0299dc8622d5d2613"
    Terraform = "true"
    Environment = "stage"
    MakeSnapshotShortTerm = "False"
    MakeSnapshotLongTerm = "False"
    vpc_domain = "sydney.stage.adroitcreations.org"
    MakeSnapshot = "False"
  }
}

# EBS Volume: vol-05207dc3d68af2177
resource "aws_ebs_volume" "vol-05207dc3d68af2177" {
  availability_zone = "ap-southeast-2a"
  size              = 1
  type              = "gp2"

  encrypted = true

  tags = {
    Name        = "vol-05207dc3d68af2177"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-05207dc3d68af2177"
    MakeSnapshot = "False"
    "Cost Center" = "Platform"
    MakeSnapshotShortTerm = "False"
    MakeSnapshotLongTerm = "False"
  }
}

# EBS Volume: etime-stage-g-14si
resource "aws_ebs_volume" "etime-stage-g-14si_1" {
  availability_zone = "ap-southeast-2c"
  size              = 100
  type              = "gp3"

  iops = 4000
  throughput = 250
  encrypted = true
  snapshot_id = "snap-06b4134076d0f791c"

  tags = {
    Name        = "etime-stage-g-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0a4eeb4d7471a3721"
    Environment = "stage"
    Terraform = "true"
    ami_id = "ami-04ca030c26a97465a"
    "Cost Center" = "etime"
    MakeSnapshotShortTerm = "False"
    MakeSnapshotLongTerm = "False"
    vpc_domain = "sydney.stage.adroitcreations.org"
    MakeSnapshot = "False"
  }
}

# EBS Volume: elementtime-stage-green
resource "aws_ebs_volume" "elementtime-stage-green" {
  availability_zone = "ap-southeast-2c"
  size              = 1
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true

  tags = {
    Name        = "elementtime-stage-green"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-063ab8b8dd493724d"
    MakeSnapshotShortTerm = "False"
    MakeSnapshot = "False"
    Environment = "stage"
    ami_id = "ami-04ca030c26a97465a"
    vpc_domain = "sydney.stage.adroitcreations.org"
    Terraform = "true"
    "Cost Center" = "elementtime"
    MakeSnapshotLongTerm = "False"
  }
}

# EBS Volume: vol-0792446c4b8e88274
resource "aws_ebs_volume" "vol-0792446c4b8e88274" {
  availability_zone = "ap-southeast-2a"
  size              = 50
  type              = "gp2"

  encrypted = true
  snapshot_id = "snap-0fa1332d7dec4d72a"

  tags = {
    Name        = "vol-0792446c4b8e88274"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0792446c4b8e88274"
    MakeSnapshotLongTerm = "False"
    "Cost Center" = "Platform"
    MakeSnapshot = "False"
    MakeSnapshotShortTerm = "False"
  }
}

# EBS Volume: elementcentre-stage-blue
resource "aws_ebs_volume" "elementcentre-stage-blue" {
  availability_zone = "ap-southeast-2b"
  size              = 1
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true

  tags = {
    Name        = "elementcentre-stage-blue"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0c42fe1354d2990bc"
    MakeSnapshot = "False"
    ami_id = "ami-03dbcf19ff380ef96"
    vpc_domain = "sydney.stage.adroitcreations.org"
    "Cost Center" = "elementcentre"
    MakeSnapshotShortTerm = "False"
    MakeSnapshotLongTerm = "False"
    Terraform = "true"
    Environment = "stage"
  }
}

# EBS Volume: vol-0081a47620656bcff
resource "aws_ebs_volume" "vol-0081a47620656bcff" {
  availability_zone = "ap-southeast-2a"
  size              = 50
  type              = "gp2"

  encrypted = true
  snapshot_id = "snap-045584ed6cbbc8a35"

  tags = {
    Name        = "vol-0081a47620656bcff"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-0081a47620656bcff"
  }
}

# EBS Volume: etime-stage-g-14si
resource "aws_ebs_volume" "etime-stage-g-14si" {
  availability_zone = "ap-southeast-2c"
  size              = 1
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true

  tags = {
    Name        = "etime-stage-g-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-07ade1531e656e735"
    MakeSnapshotShortTerm = "False"
    MakeSnapshotLongTerm = "False"
    Environment = "stage"
    ami_id = "ami-04ca030c26a97465a"
    "Cost Center" = "etime"
    Terraform = "true"
    vpc_domain = "sydney.stage.adroitcreations.org"
    MakeSnapshot = "False"
  }
}

# EBS Volume: elementtime-stage-socket-green
resource "aws_ebs_volume" "elementtime-stage-socket-green" {
  availability_zone = "ap-southeast-2a"
  size              = 100
  type              = "gp3"

  iops = 4000
  throughput = 250
  encrypted = true
  snapshot_id = "snap-06b4134076d0f791c"

  tags = {
    Name        = "elementtime-stage-socket-green"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-008c0c72977bec70d"
    ami_id = "ami-04ca030c26a97465a"
    MakeSnapshot = "False"
    Terraform = "true"
    "Cost Center" = "elementtime"
    MakeSnapshotLongTerm = "False"
    Environment = "stage"
    MakeSnapshotShortTerm = "False"
    vpc_domain = "sydney.stage.adroitcreations.org"
  }
}

# EBS Volume: elementorg-griffith
resource "aws_ebs_volume" "elementorg-griffith" {
  availability_zone = "ap-southeast-2b"
  size              = 100
  type              = "gp3"

  iops = 4000
  throughput = 250
  encrypted = true
  snapshot_id = "snap-0d764624be9a38053"

  tags = {
    Name        = "elementorg-griffith"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "vol-026ec4336afd966e4"
    ANSIBLE_S3_BUCKET = "ac-secrets-stage"
    ANSIBLE_ROLE = "elementorg"
    MakeSnapshotLongTerm = "False"
    ANSIBLE_PLAY = "plays/elementorg-griffith.yml"
    MakeSnapshotShortTerm = "False"
    ANSIBLE_BRANCH = "upgrade-2204-base"
    ANSIBLE_POOL = "ac-stage"
    ANSIBLE_DC = "stage-ap-southeast-2"
    "Cost Center" = "elementOrg"
    SUDOERS_GROUPS_TAG = "engineering,platform,security"
    MakeSnapshot = "False"
  }
}