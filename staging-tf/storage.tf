# EBS Volume: etime-stage-skt-g-14si
resource "aws_ebs_volume" "etime-stage-skt-g-14si" {
  availability_zone = "ap-southeast-2c"
  size              = 1
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true

  tags = {
    Name        = "etime-stage-skt-g-14si"
    Environment = var.environment
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
  }
}

# EBS Volume: elementtime-stage-green
resource "aws_ebs_volume" "elementtime-stage-green" {
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
  }
}

# EBS Volume: elementtime-stage-socket-blue
resource "aws_ebs_volume" "elementtime-stage-socket-blue" {
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
    ManagedBy   = "RepliMap"
  }
}

# EBS Volume: elementcentre-stage-blue
resource "aws_ebs_volume" "elementcentre-stage-blue" {
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
  }
}

# EBS Volume: elementtime-stage-green
resource "aws_ebs_volume" "elementtime-stage-green" {
  availability_zone = "ap-southeast-2a"
  size              = 1
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true

  tags = {
    Name        = "elementtime-stage-green"
    Environment = var.environment
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
  }
}

# EBS Volume: elementsup-stage-blue
resource "aws_ebs_volume" "elementsup-stage-blue" {
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
  }
}

# EBS Volume: elementstaff-stage-blue
resource "aws_ebs_volume" "elementstaff-stage-blue" {
  availability_zone = "ap-southeast-2a"
  size              = 1
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true

  tags = {
    Name        = "elementstaff-stage-blue"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# EBS Volume: etime-stage-skt-b-14si
resource "aws_ebs_volume" "etime-stage-skt-b-14si" {
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
  }
}

# EBS Volume: ghostrpc-stage-blue
resource "aws_ebs_volume" "ghostrpc-stage-blue" {
  availability_zone = "ap-southeast-2b"
  size              = 100
  type              = "gp2"

  encrypted = true
  snapshot_id = "snap-0fa1332d7dec4d72a"

  tags = {
    Name        = "ghostrpc-stage-blue"
    Environment = var.environment
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
  }
}

# EBS Volume: etime-stage-b-14si
resource "aws_ebs_volume" "etime-stage-b-14si" {
  availability_zone = "ap-southeast-2b"
  size              = 1
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true

  tags = {
    Name        = "etime-stage-b-14si"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# EBS Volume: elementtime-stage-blue
resource "aws_ebs_volume" "elementtime-stage-blue" {
  availability_zone = "ap-southeast-2b"
  size              = 1
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true

  tags = {
    Name        = "elementtime-stage-blue"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# EBS Volume: elementorg-griffith
resource "aws_ebs_volume" "elementorg-griffith" {
  availability_zone = "ap-southeast-2b"
  size              = 1
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true

  tags = {
    Name        = "elementorg-griffith"
    Environment = var.environment
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
  }
}

# EBS Volume: elementtime-stage-socket-green
resource "aws_ebs_volume" "elementtime-stage-socket-green" {
  availability_zone = "ap-southeast-2a"
  size              = 1
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true

  tags = {
    Name        = "elementtime-stage-socket-green"
    Environment = var.environment
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
  }
}

# EBS Volume: etime-stage-g-14si
resource "aws_ebs_volume" "etime-stage-g-14si" {
  availability_zone = "ap-southeast-2a"
  size              = 1
  type              = "gp3"

  iops = 3000
  throughput = 125
  encrypted = true

  tags = {
    Name        = "etime-stage-g-14si"
    Environment = var.environment
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
  }
}

# EBS Volume: elementtime-stage-green
resource "aws_ebs_volume" "elementtime-stage-green" {
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
  }
}

# EBS Volume: etime-stage-g-14si
resource "aws_ebs_volume" "etime-stage-g-14si" {
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
  }
}

# EBS Volume: etime-stage-g-14si
resource "aws_ebs_volume" "etime-stage-g-14si" {
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
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
    ManagedBy   = "RepliMap"
  }
}