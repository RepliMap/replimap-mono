# Launch Template: lt-083d04a82785704e6
resource "aws_launch_template" "lt-083d04a82785704e6" {
  name = "ghostrpc-stage-green-20240206095857633800000003"

  instance_type = "t3a.small"
  image_id = "ami-0091208de35b8d49b"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_elementSeries_prod_vpc_id.id,
    aws_security_group.aws_security_group_sg-0e2e9a590c75ed9fe_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-083d04a82785704e6"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-083d04a82785704e6"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-02f309985479760cc
resource "aws_launch_template" "lt-02f309985479760cc" {
  name = "ghostrpc-stage-blue-20240206095857632300000001"

  instance_type = "t3a.small"
  image_id = "ami-0091208de35b8d49b"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_elementSeries_prod_vpc_id.id,
    aws_security_group.aws_security_group_sg-0e2e9a590c75ed9fe_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-02f309985479760cc"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-02f309985479760cc"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-00b6e0c382f1ba833
resource "aws_launch_template" "lt-00b6e0c382f1ba833" {
  name = "etime-test-skt-g-14si-20240410102753576800000007"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-06e2817ae86814235_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-00b6e0c382f1ba833"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-00b6e0c382f1ba833"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0e728efb8f33f7088
resource "aws_launch_template" "lt-0e728efb8f33f7088" {
  name = "etime-test-skt-b-14si-20240410102754000700000009"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-06e2817ae86814235_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0e728efb8f33f7088"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0e728efb8f33f7088"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-04554c82ad17a666c
resource "aws_launch_template" "lt-04554c82ad17a666c" {
  name = "etime-test-g-14si-2024041010280246290000000e"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-06e2817ae86814235_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-04554c82ad17a666c"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-04554c82ad17a666c"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-010dc2097987f7157
resource "aws_launch_template" "lt-010dc2097987f7157" {
  name = "etime-test-cmd-g-14si-20241108082320604200000001"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-06e2817ae86814235_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-010dc2097987f7157"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-010dc2097987f7157"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0619ec649ed523863
resource "aws_launch_template" "lt-0619ec649ed523863" {
  name = "etime-test-cmd-b-14si-20241108082320660300000003"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-06e2817ae86814235_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0619ec649ed523863"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0619ec649ed523863"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0956f8e744006ef1e
resource "aws_launch_template" "lt-0956f8e744006ef1e" {
  name = "etime-test-b-14si-20240410102802749700000010"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-06e2817ae86814235_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0956f8e744006ef1e"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0956f8e744006ef1e"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0c4c3b7bc83ee5b4b
resource "aws_launch_template" "lt-0c4c3b7bc83ee5b4b" {
  name = "etime-stage-skt-g-14si-20240410102753574600000001"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-06e2817ae86814235_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0c4c3b7bc83ee5b4b"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0c4c3b7bc83ee5b4b"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-026402e837ad46bc1
resource "aws_launch_template" "lt-026402e837ad46bc1" {
  name = "etime-stage-skt-b-14si-2024041010275403810000000b"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-06e2817ae86814235_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-026402e837ad46bc1"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-026402e837ad46bc1"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-03e1bae900ffc94bc
resource "aws_launch_template" "lt-03e1bae900ffc94bc" {
  name = "etime-stage-g-14si-20240410102803525700000018"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-06e2817ae86814235_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-03e1bae900ffc94bc"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-03e1bae900ffc94bc"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-09ae1bebe1240319f
resource "aws_launch_template" "lt-09ae1bebe1240319f" {
  name = "etime-stage-cmd-g-14si-20241108085629540100000003"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-06e2817ae86814235_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-09ae1bebe1240319f"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-09ae1bebe1240319f"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0210f62074b70c53c
resource "aws_launch_template" "lt-0210f62074b70c53c" {
  name = "etime-stage-cmd-b-14si-20241108085629572500000005"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-06e2817ae86814235_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0210f62074b70c53c"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0210f62074b70c53c"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0dbd35aafb1de6063
resource "aws_launch_template" "lt-0dbd35aafb1de6063" {
  name = "etime-stage-b-14si-20240410102803479400000016"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-06e2817ae86814235_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0dbd35aafb1de6063"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0dbd35aafb1de6063"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-03efae88b42d320d5
resource "aws_launch_template" "lt-03efae88b42d320d5" {
  name = "etime-stage-skt-g-14si-20240410102753575400000005"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-06e2817ae86814235_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-03efae88b42d320d5"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-03efae88b42d320d5"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0c2298f8dafed605a
resource "aws_launch_template" "lt-0c2298f8dafed605a" {
  name = "etime-stage-skt-b-14si-20240410102753575300000003"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-06e2817ae86814235_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0c2298f8dafed605a"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0c2298f8dafed605a"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-07317d18625133ffc
resource "aws_launch_template" "lt-07317d18625133ffc" {
  name = "etime-stage-g-14si-20240410102803204000000014"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-06e2817ae86814235_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-07317d18625133ffc"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-07317d18625133ffc"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0a25463a25a4f718a
resource "aws_launch_template" "lt-0a25463a25a4f718a" {
  name = "etime-stage-cmd-g-14si-20241108085629531800000001"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-06e2817ae86814235_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0a25463a25a4f718a"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0a25463a25a4f718a"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-021f08838ac9cede4
resource "aws_launch_template" "lt-021f08838ac9cede4" {
  name = "etime-stage-cmd-b-14si-20241108085629645800000007"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-06e2817ae86814235_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-021f08838ac9cede4"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-021f08838ac9cede4"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-068f342622b22f30a
resource "aws_launch_template" "lt-068f342622b22f30a" {
  name = "etime-stage-b-14si-20240410102803055500000012"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-06e2817ae86814235_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-068f342622b22f30a"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-068f342622b22f30a"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0f96ceb7b890bd5a2
resource "aws_launch_template" "lt-0f96ceb7b890bd5a2" {
  name = "elementtime-test-socket-green-20220801053600505900000001"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-0e9d9aa5c428a5c03_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0f96ceb7b890bd5a2"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0f96ceb7b890bd5a2"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-037d270f1eb9eea9c
resource "aws_launch_template" "lt-037d270f1eb9eea9c" {
  name = "elementtime-test-socket-blue-20220802101408554000000001"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-0e9d9aa5c428a5c03_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-037d270f1eb9eea9c"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-037d270f1eb9eea9c"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0f8a3144cff4dae51
resource "aws_launch_template" "lt-0f8a3144cff4dae51" {
  name = "elementtime-test-green-20220808102316610600000001"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-0e9d9aa5c428a5c03_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0f8a3144cff4dae51"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0f8a3144cff4dae51"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-06995da340bc7e5c6
resource "aws_launch_template" "lt-06995da340bc7e5c6" {
  name = "elementtime-test-cmd-green-20241108095715442700000009"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-0e9d9aa5c428a5c03_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-06995da340bc7e5c6"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-06995da340bc7e5c6"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0a090a26a2e98751a
resource "aws_launch_template" "lt-0a090a26a2e98751a" {
  name = "elementtime-test-cmd-blue-20241108095714979800000003"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-0e9d9aa5c428a5c03_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0a090a26a2e98751a"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0a090a26a2e98751a"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0a9e1a6d54722b12e
resource "aws_launch_template" "lt-0a9e1a6d54722b12e" {
  name = "elementtime-test-blue-20220808102316846900000003"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-0e9d9aa5c428a5c03_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0a9e1a6d54722b12e"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0a9e1a6d54722b12e"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0fbfa6b341ae5a01f
resource "aws_launch_template" "lt-0fbfa6b341ae5a01f" {
  name = "elementtime-stage-socket-green-20220808104728914200000001"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-0e9d9aa5c428a5c03_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0fbfa6b341ae5a01f"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0fbfa6b341ae5a01f"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-05b0a9a8f291d2dfb
resource "aws_launch_template" "lt-05b0a9a8f291d2dfb" {
  name = "elementtime-stage-socket-blue-20220808104729545800000007"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-0e9d9aa5c428a5c03_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-05b0a9a8f291d2dfb"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-05b0a9a8f291d2dfb"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-05139e0a9b8cf06e3
resource "aws_launch_template" "lt-05139e0a9b8cf06e3" {
  name = "elementtime-stage-green-2022080810474174790000000f"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-0e9d9aa5c428a5c03_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-05139e0a9b8cf06e3"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-05139e0a9b8cf06e3"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0e7eff28f37b34df9
resource "aws_launch_template" "lt-0e7eff28f37b34df9" {
  name = "elementtime-stage-cmd-green-20241108095715273400000005"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-0e9d9aa5c428a5c03_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0e7eff28f37b34df9"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0e7eff28f37b34df9"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-06e7b24f25b1af45d
resource "aws_launch_template" "lt-06e7b24f25b1af45d" {
  name = "elementtime-stage-cmd-blue-20241108095714735100000001"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-0e9d9aa5c428a5c03_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-06e7b24f25b1af45d"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-06e7b24f25b1af45d"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0f2b473baa85e32a2
resource "aws_launch_template" "lt-0f2b473baa85e32a2" {
  name = "elementtime-stage-blue-2022080810474174780000000d"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-0e9d9aa5c428a5c03_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0f2b473baa85e32a2"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0f2b473baa85e32a2"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-090b6efcc2b0d4f99
resource "aws_launch_template" "lt-090b6efcc2b0d4f99" {
  name = "elementtime-stage-socket-green-20220808104728969800000003"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-0e9d9aa5c428a5c03_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-090b6efcc2b0d4f99"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-090b6efcc2b0d4f99"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0eab43453208c2377
resource "aws_launch_template" "lt-0eab43453208c2377" {
  name = "elementtime-stage-socket-blue-20220808104729363200000005"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-0e9d9aa5c428a5c03_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0eab43453208c2377"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0eab43453208c2377"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0fe81c28bab290f06
resource "aws_launch_template" "lt-0fe81c28bab290f06" {
  name = "elementtime-stage-green-20220808104741365600000009"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-0e9d9aa5c428a5c03_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0fe81c28bab290f06"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0fe81c28bab290f06"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0b04e638418b62aac
resource "aws_launch_template" "lt-0b04e638418b62aac" {
  name = "elementtime-stage-cmd-green-2024110809571545790000000b"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-0e9d9aa5c428a5c03_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0b04e638418b62aac"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0b04e638418b62aac"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0e57656fe14c138c0
resource "aws_launch_template" "lt-0e57656fe14c138c0" {
  name = "elementtime-stage-cmd-blue-20241108095715385700000007"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-0e9d9aa5c428a5c03_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0e57656fe14c138c0"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0e57656fe14c138c0"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0e9ca7f6d95b30f52
resource "aws_launch_template" "lt-0e9ca7f6d95b30f52" {
  name = "elementtime-stage-blue-2022080810474136570000000b"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_sg-0e9d9aa5c428a5c03_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0e9ca7f6d95b30f52"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0e9ca7f6d95b30f52"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0432a41ea4785ba95
resource "aws_launch_template" "lt-0432a41ea4785ba95" {
  name = "elementsup-stage-green-20240204051109257100000001"

  instance_type = "t4g.small"
  image_id = "ami-075beeb4b028a712d"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_elementSeries_prod_vpc_id.id,
    aws_security_group.aws_security_group_sg-0d4ca909ae44ef9a4_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0432a41ea4785ba95"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0432a41ea4785ba95"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0bf2553d035a5590e
resource "aws_launch_template" "lt-0bf2553d035a5590e" {
  name = "elementsup-stage-blue-20240204051109267100000003"

  instance_type = "t4g.small"
  image_id = "ami-075beeb4b028a712d"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_elementSeries_prod_vpc_id.id,
    aws_security_group.aws_security_group_sg-0d4ca909ae44ef9a4_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0bf2553d035a5590e"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0bf2553d035a5590e"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0706143bb0def5e8f
resource "aws_launch_template" "lt-0706143bb0def5e8f" {
  name = "elementstaff-stage-green-20240212104241109900000004"

  instance_type = "t4g.small"
  image_id = "ami-075beeb4b028a712d"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_elementSeries_prod_vpc_id.id,
    aws_security_group.aws_security_group_sg-02c028c79d15adf86_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0706143bb0def5e8f"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0706143bb0def5e8f"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0cc8e2d2ee2af8118
resource "aws_launch_template" "lt-0cc8e2d2ee2af8118" {
  name = "elementstaff-stage-blue-20240212104241107800000002"

  instance_type = "t4g.small"
  image_id = "ami-075beeb4b028a712d"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_elementSeries_prod_vpc_id.id,
    aws_security_group.aws_security_group_sg-02c028c79d15adf86_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0cc8e2d2ee2af8118"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0cc8e2d2ee2af8118"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0f14d9e6488689826
resource "aws_launch_template" "lt-0f14d9e6488689826" {
  name = "elementrec-stage-green-20240212092143522300000003"

  instance_type = "t3a.small"
  image_id = "ami-0091208de35b8d49b"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0b433a6d6c584ef79_id.id,
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_elementSeries_prod_vpc_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0f14d9e6488689826"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0f14d9e6488689826"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0b632550e3bf25eaa
resource "aws_launch_template" "lt-0b632550e3bf25eaa" {
  name = "elementrec-stage-blue-20240212092143457900000001"

  instance_type = "t3a.small"
  image_id = "ami-0091208de35b8d49b"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0b433a6d6c584ef79_id.id,
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_elementSeries_prod_vpc_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0b632550e3bf25eaa"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0b632550e3bf25eaa"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-0459e774ce8822a2f
resource "aws_launch_template" "lt-0459e774ce8822a2f" {
  name = "elementcentre-stage-green-20240207095935633800000001"

  instance_type = "t4g.small"
  image_id = "ami-075beeb4b028a712d"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_elementSeries_prod_vpc_id.id,
    aws_security_group.aws_security_group_sg-0ac562a2b2761e254_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0459e774ce8822a2f"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-0459e774ce8822a2f"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Launch Template: lt-079f444f6bc8a8ec9
resource "aws_launch_template" "lt-079f444f6bc8a8ec9" {
  name = "elementcentre-stage-blue-20240207095935650400000003"

  instance_type = "t4g.small"
  image_id = "ami-075beeb4b028a712d"

  vpc_security_group_ids = [
    aws_security_group.aws_security_group_sg-0ea9a1c02b8ef60bd_id.id,
    aws_security_group.aws_security_group_sg-0ea2aca1e6a8d47fe_id.id,
    aws_security_group.aws_security_group_elementSeries_prod_vpc_id.id,
    aws_security_group.aws_security_group_sg-0ac562a2b2761e254_id.id,
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-079f444f6bc8a8ec9"
      Environment = var.environment
      ManagedBy   = "RepliMap"
    }
  }

  tags = {
    Name        = "lt-079f444f6bc8a8ec9"
    Environment = var.environment
    ManagedBy   = "RepliMap"
  }
}

# Auto Scaling Group: asg-ghostrpc-stage-green
resource "aws_autoscaling_group" "asg-ghostrpc-stage-green" {
  name = "asg-ghostrpc-stage-green"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-083d04a82785704e6.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_ghostrpc-alb-prod-green_e6ea5c97d2d8fce0.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-ghostrpc-stage-green"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-ghostrpc-stage-blue
resource "aws_autoscaling_group" "asg-ghostrpc-stage-blue" {
  name = "asg-ghostrpc-stage-blue"

  min_size         = 1
  max_size         = 1
  desired_capacity = 1

  launch_template {
    id      = aws_launch_template.lt-02f309985479760cc.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_ghostrpc-alb-prod-blue_fe898ecb1068f985.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-ghostrpc-stage-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-test-skt-g-14si
resource "aws_autoscaling_group" "asg-etime-test-skt-g-14si" {
  name = "asg-etime-test-skt-g-14si"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-00b6e0c382f1ba833.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-test-skt-g-14si_34ce0d4fd832ebee.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-etime-test-skt-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-test-skt-b-14si
resource "aws_autoscaling_group" "asg-etime-test-skt-b-14si" {
  name = "asg-etime-test-skt-b-14si"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0e728efb8f33f7088.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-test-skt-b-14si_9ce161490594477c.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-etime-test-skt-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-test-g-14si
resource "aws_autoscaling_group" "asg-etime-test-g-14si" {
  name = "asg-etime-test-g-14si"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-04554c82ad17a666c.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-test-g-14si_a4c818664f160ca3.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-etime-test-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-test-cmd-g-14si
resource "aws_autoscaling_group" "asg-etime-test-cmd-g-14si" {
  name = "asg-etime-test-cmd-g-14si"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-010dc2097987f7157.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-test-cmd-g-14si_20b818f5f1bf64b0.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-etime-test-cmd-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-test-cmd-b-14si
resource "aws_autoscaling_group" "asg-etime-test-cmd-b-14si" {
  name = "asg-etime-test-cmd-b-14si"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0619ec649ed523863.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-test-cmd-b-14si_0f5eb0935ae53c51.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-etime-test-cmd-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-test-b-14si
resource "aws_autoscaling_group" "asg-etime-test-b-14si" {
  name = "asg-etime-test-b-14si"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0956f8e744006ef1e.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-test-b-14si_63b805c28ac9b7b0.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-etime-test-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-stage-skt-g-14si
resource "aws_autoscaling_group" "asg-etime-stage-skt-g-14si" {
  name = "asg-etime-stage-skt-g-14si"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0c4c3b7bc83ee5b4b.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-stage-skt-g-14si_caca675f49518d51.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-etime-stage-skt-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-stage-skt-b-14si
resource "aws_autoscaling_group" "asg-etime-stage-skt-b-14si" {
  name = "asg-etime-stage-skt-b-14si"

  min_size         = 1
  max_size         = 1
  desired_capacity = 1

  launch_template {
    id      = aws_launch_template.lt-026402e837ad46bc1.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-stage-skt-b-14si_94e78c753ef07194.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-etime-stage-skt-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-stage-g-14si
resource "aws_autoscaling_group" "asg-etime-stage-g-14si" {
  name = "asg-etime-stage-g-14si"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-03e1bae900ffc94bc.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-stage-g-14si_6f686d10e8e4bdc3.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-etime-stage-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-stage-cmd-g-14si
resource "aws_autoscaling_group" "asg-etime-stage-cmd-g-14si" {
  name = "asg-etime-stage-cmd-g-14si"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-09ae1bebe1240319f.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-stage-cmd-g-14si_92428e2976ec9624.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-etime-stage-cmd-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-stage-cmd-b-14si
resource "aws_autoscaling_group" "asg-etime-stage-cmd-b-14si" {
  name = "asg-etime-stage-cmd-b-14si"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0210f62074b70c53c.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-stage-cmd-b-14si_8ae6beafa0fab497.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-etime-stage-cmd-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-stage-b-14si
resource "aws_autoscaling_group" "asg-etime-stage-b-14si" {
  name = "asg-etime-stage-b-14si"

  min_size         = 1
  max_size         = 2
  desired_capacity = 1

  launch_template {
    id      = aws_launch_template.lt-0dbd35aafb1de6063.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-stage-b-14si_e9649c8e9cfca7bd.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-etime-stage-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-stage-skt-g-14si
resource "aws_autoscaling_group" "asg-etime-stage-skt-g-14si" {
  name = "asg-etime-stage-skt-g-14si"

  min_size         = 1
  max_size         = 1
  desired_capacity = 1

  launch_template {
    id      = aws_launch_template.lt-03efae88b42d320d5.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-prod-skt-g-14si_b2ac75ed028f753a.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-etime-stage-skt-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-stage-skt-b-14si
resource "aws_autoscaling_group" "asg-etime-stage-skt-b-14si" {
  name = "asg-etime-stage-skt-b-14si"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0c2298f8dafed605a.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-prod-skt-b-14si_f3a1fa1acc3d8aab.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-etime-stage-skt-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-stage-g-14si
resource "aws_autoscaling_group" "asg-etime-stage-g-14si" {
  name = "asg-etime-stage-g-14si"

  min_size         = 1
  max_size         = 2
  desired_capacity = 1

  launch_template {
    id      = aws_launch_template.lt-07317d18625133ffc.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-prod-g-14si_bb47a23d13331ca0.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-etime-stage-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-stage-cmd-g-14si
resource "aws_autoscaling_group" "asg-etime-stage-cmd-g-14si" {
  name = "asg-etime-stage-cmd-g-14si"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0a25463a25a4f718a.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-prod-cmd-g-14si_a48d46b24f2ca9b2.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-etime-stage-cmd-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-stage-cmd-b-14si
resource "aws_autoscaling_group" "asg-etime-stage-cmd-b-14si" {
  name = "asg-etime-stage-cmd-b-14si"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-021f08838ac9cede4.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-prod-cmd-b-14si_5e754f4e63975546.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-etime-stage-cmd-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-stage-b-14si
resource "aws_autoscaling_group" "asg-etime-stage-b-14si" {
  name = "asg-etime-stage-b-14si"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-068f342622b22f30a.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-prod-b-14si_f643851b073af7fa.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-etime-stage-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-test-socket-green
resource "aws_autoscaling_group" "asg-elementtime-test-socket-green" {
  name = "asg-elementtime-test-socket-green"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0f96ceb7b890bd5a2.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-test-socket-green_6b1446596a895d1d.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementtime-test-socket-green"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-test-socket-blue
resource "aws_autoscaling_group" "asg-elementtime-test-socket-blue" {
  name = "asg-elementtime-test-socket-blue"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-037d270f1eb9eea9c.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-test-socket-blue_7702ed0921031361.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementtime-test-socket-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-test-green
resource "aws_autoscaling_group" "asg-elementtime-test-green" {
  name = "asg-elementtime-test-green"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0f8a3144cff4dae51.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-test-green_1d8fc63f16d0bd23.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementtime-test-green"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-test-cmd-green
resource "aws_autoscaling_group" "asg-elementtime-test-cmd-green" {
  name = "asg-elementtime-test-cmd-green"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-06995da340bc7e5c6.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-test-cmd-green_24c5eed35c12d165.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementtime-test-cmd-green"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-test-cmd-blue
resource "aws_autoscaling_group" "asg-elementtime-test-cmd-blue" {
  name = "asg-elementtime-test-cmd-blue"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0a090a26a2e98751a.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-test-cmd-blue_9cb9b9bfb91c728b.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementtime-test-cmd-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-test-blue
resource "aws_autoscaling_group" "asg-elementtime-test-blue" {
  name = "asg-elementtime-test-blue"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0a9e1a6d54722b12e.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-test-blue_adf00bf65e691a41.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementtime-test-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-stage-socket-green
resource "aws_autoscaling_group" "asg-elementtime-stage-socket-green" {
  name = "asg-elementtime-stage-socket-green"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0fbfa6b341ae5a01f.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-stage-socket-green_e9d1b115681f2b9a.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementtime-stage-socket-green"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-stage-socket-blue
resource "aws_autoscaling_group" "asg-elementtime-stage-socket-blue" {
  name = "asg-elementtime-stage-socket-blue"

  min_size         = 1
  max_size         = 1
  desired_capacity = 1

  launch_template {
    id      = aws_launch_template.lt-05b0a9a8f291d2dfb.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-stage-socket-blue_4247d208ae10d096.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementtime-stage-socket-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-stage-green
resource "aws_autoscaling_group" "asg-elementtime-stage-green" {
  name = "asg-elementtime-stage-green"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-05139e0a9b8cf06e3.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-stage-green_f3f73cc137565811.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementtime-stage-green"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-stage-cmd-green
resource "aws_autoscaling_group" "asg-elementtime-stage-cmd-green" {
  name = "asg-elementtime-stage-cmd-green"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0e7eff28f37b34df9.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-stage-cmd-green_df42649d76cf2a3f.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementtime-stage-cmd-green"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-stage-cmd-blue
resource "aws_autoscaling_group" "asg-elementtime-stage-cmd-blue" {
  name = "asg-elementtime-stage-cmd-blue"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-06e7b24f25b1af45d.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-stage-cmd-blue_372538449cab9357.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementtime-stage-cmd-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-stage-blue
resource "aws_autoscaling_group" "asg-elementtime-stage-blue" {
  name = "asg-elementtime-stage-blue"

  min_size         = 1
  max_size         = 2
  desired_capacity = 1

  launch_template {
    id      = aws_launch_template.lt-0f2b473baa85e32a2.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-stage-blue_3080d01af67bb17e.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementtime-stage-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-stage-socket-green
resource "aws_autoscaling_group" "asg-elementtime-stage-socket-green" {
  name = "asg-elementtime-stage-socket-green"

  min_size         = 1
  max_size         = 1
  desired_capacity = 1

  launch_template {
    id      = aws_launch_template.lt-090b6efcc2b0d4f99.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-prod-socket-green_8c70e31eba804609.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementtime-stage-socket-green"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-stage-socket-blue
resource "aws_autoscaling_group" "asg-elementtime-stage-socket-blue" {
  name = "asg-elementtime-stage-socket-blue"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0eab43453208c2377.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-prod-socket-blue_db10ec971800e3af.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementtime-stage-socket-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-stage-green
resource "aws_autoscaling_group" "asg-elementtime-stage-green" {
  name = "asg-elementtime-stage-green"

  min_size         = 1
  max_size         = 2
  desired_capacity = 1

  launch_template {
    id      = aws_launch_template.lt-0fe81c28bab290f06.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-prod-green_8c851fcbc83b25c4.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementtime-stage-green"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-stage-cmd-green
resource "aws_autoscaling_group" "asg-elementtime-stage-cmd-green" {
  name = "asg-elementtime-stage-cmd-green"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0b04e638418b62aac.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-prod-cmd-green_5b4d25ce0fc0a151.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementtime-stage-cmd-green"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-stage-cmd-blue
resource "aws_autoscaling_group" "asg-elementtime-stage-cmd-blue" {
  name = "asg-elementtime-stage-cmd-blue"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0e57656fe14c138c0.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-prod-cmd-blue_897ea90d93409140.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementtime-stage-cmd-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-stage-blue
resource "aws_autoscaling_group" "asg-elementtime-stage-blue" {
  name = "asg-elementtime-stage-blue"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0e9ca7f6d95b30f52.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_etime-alb-prod-blue_435d18369923348c.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 300
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementtime-stage-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementsup-stage-green
resource "aws_autoscaling_group" "asg-elementsup-stage-green" {
  name = "asg-elementsup-stage-green"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0432a41ea4785ba95.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_esup-alb-prod-green_77771596b18edef1.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementsup-stage-green"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementsup-stage-blue
resource "aws_autoscaling_group" "asg-elementsup-stage-blue" {
  name = "asg-elementsup-stage-blue"

  min_size         = 1
  max_size         = 1
  desired_capacity = 1

  launch_template {
    id      = aws_launch_template.lt-0bf2553d035a5590e.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_esup-alb-prod-blue_72bf20c9a45fcadb.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 7200
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementsup-stage-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementstaff-stage-green
resource "aws_autoscaling_group" "asg-elementstaff-stage-green" {
  name = "asg-elementstaff-stage-green"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0706143bb0def5e8f.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_estaff-alb-prod-green_80e221840808a45f.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementstaff-stage-green"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementstaff-stage-blue
resource "aws_autoscaling_group" "asg-elementstaff-stage-blue" {
  name = "asg-elementstaff-stage-blue"

  min_size         = 1
  max_size         = 1
  desired_capacity = 1

  launch_template {
    id      = aws_launch_template.lt-0cc8e2d2ee2af8118.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_estaff-alb-prod-blue_9c3174929d979eba.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementstaff-stage-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementrec-stage-green
resource "aws_autoscaling_group" "asg-elementrec-stage-green" {
  name = "asg-elementrec-stage-green"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0f14d9e6488689826.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_erec-alb-prod-green_d2baecf0a6c5cdb7.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementrec-stage-green"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementrec-stage-blue
resource "aws_autoscaling_group" "asg-elementrec-stage-blue" {
  name = "asg-elementrec-stage-blue"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0b632550e3bf25eaa.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_erec-alb-prod-blue_3f8141308c99dc70.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementrec-stage-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementcentre-stage-green
resource "aws_autoscaling_group" "asg-elementcentre-stage-green" {
  name = "asg-elementcentre-stage-green"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0459e774ce8822a2f.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_ecentre-alb-prod-green_7b3287f17303e670.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementcentre-stage-green"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementcentre-stage-blue
resource "aws_autoscaling_group" "asg-elementcentre-stage-blue" {
  name = "asg-elementcentre-stage-blue"

  min_size         = 1
  max_size         = 1
  desired_capacity = 1

  launch_template {
    id      = aws_launch_template.lt-079f444f6bc8a8ec9.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2b_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2c_id.id,
    aws_subnet.aws_subnet_stage-subnet-private-ap-southeast-2a_id.id,
  ]

  target_group_arns = [
    aws_lb_target_group.arn_aws_elasticloadbalancing_ap-southeast-2___var_aws_account_id__targetgroup_ecentre-alb-prod-blue_eec84dc640ab5474.arn,
  ]

  health_check_type         = "EC2"
  health_check_grace_period = 3000
  default_cooldown          = 420

  tag {
    key                 = "Name"
    value               = "asg-elementcentre-stage-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = "Environment"
    value               = var.environment
    propagate_at_launch = true
  }

  tag {
    key                 = "ManagedBy"
    value               = "RepliMap"
    propagate_at_launch = true
  }
}