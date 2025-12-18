# Launch Template: lt-083d04a82785704e6
resource "aws_launch_template" "lt-083d04a82785704e6" {
  name = "ghostrpc-stage-green-20240206095857633800000003"

  instance_type = "t3a.small"
  image_id = "ami-0091208de35b8d49b"

  vpc_security_group_ids = [
    "aws_security_group.elementSeries_prod_vpc.id",
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0e2e9a590c75ed9fe.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-083d04a82785704e6"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-083d04a82785704e6"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-083d04a82785704e6"
  }
}

# Launch Template: lt-02f309985479760cc
resource "aws_launch_template" "lt-02f309985479760cc" {
  name = "ghostrpc-stage-blue-20240206095857632300000001"

  instance_type = "t3a.small"
  image_id = "ami-0091208de35b8d49b"

  vpc_security_group_ids = [
    "aws_security_group.elementSeries_prod_vpc.id",
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0e2e9a590c75ed9fe.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-02f309985479760cc"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-02f309985479760cc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-02f309985479760cc"
  }
}

# Launch Template: lt-00b6e0c382f1ba833
resource "aws_launch_template" "lt-00b6e0c382f1ba833" {
  name = "etime-test-skt-g-14si-20240410102753576800000007"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-00b6e0c382f1ba833"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-00b6e0c382f1ba833"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-00b6e0c382f1ba833"
  }
}

# Launch Template: lt-0e728efb8f33f7088
resource "aws_launch_template" "lt-0e728efb8f33f7088" {
  name = "etime-test-skt-b-14si-20240410102754000700000009"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0e728efb8f33f7088"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0e728efb8f33f7088"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0e728efb8f33f7088"
  }
}

# Launch Template: lt-04554c82ad17a666c
resource "aws_launch_template" "lt-04554c82ad17a666c" {
  name = "etime-test-g-14si-2024041010280246290000000e"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-04554c82ad17a666c"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-04554c82ad17a666c"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-04554c82ad17a666c"
  }
}

# Launch Template: lt-010dc2097987f7157
resource "aws_launch_template" "lt-010dc2097987f7157" {
  name = "etime-test-cmd-g-14si-20241108082320604200000001"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-010dc2097987f7157"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-010dc2097987f7157"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-010dc2097987f7157"
  }
}

# Launch Template: lt-0619ec649ed523863
resource "aws_launch_template" "lt-0619ec649ed523863" {
  name = "etime-test-cmd-b-14si-20241108082320660300000003"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0619ec649ed523863"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0619ec649ed523863"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0619ec649ed523863"
  }
}

# Launch Template: lt-0956f8e744006ef1e
resource "aws_launch_template" "lt-0956f8e744006ef1e" {
  name = "etime-test-b-14si-20240410102802749700000010"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0956f8e744006ef1e"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0956f8e744006ef1e"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0956f8e744006ef1e"
  }
}

# Launch Template: lt-0c4c3b7bc83ee5b4b
resource "aws_launch_template" "lt-0c4c3b7bc83ee5b4b" {
  name = "etime-stage-skt-g-14si-20240410102753574600000001"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0c4c3b7bc83ee5b4b"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0c4c3b7bc83ee5b4b"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0c4c3b7bc83ee5b4b"
  }
}

# Launch Template: lt-026402e837ad46bc1
resource "aws_launch_template" "lt-026402e837ad46bc1" {
  name = "etime-stage-skt-b-14si-2024041010275403810000000b"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-026402e837ad46bc1"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-026402e837ad46bc1"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-026402e837ad46bc1"
  }
}

# Launch Template: lt-03e1bae900ffc94bc
resource "aws_launch_template" "lt-03e1bae900ffc94bc" {
  name = "etime-stage-g-14si-20240410102803525700000018"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-03e1bae900ffc94bc"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-03e1bae900ffc94bc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-03e1bae900ffc94bc"
  }
}

# Launch Template: lt-09ae1bebe1240319f
resource "aws_launch_template" "lt-09ae1bebe1240319f" {
  name = "etime-stage-cmd-g-14si-20241108085629540100000003"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-09ae1bebe1240319f"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-09ae1bebe1240319f"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-09ae1bebe1240319f"
  }
}

# Launch Template: lt-0210f62074b70c53c
resource "aws_launch_template" "lt-0210f62074b70c53c" {
  name = "etime-stage-cmd-b-14si-20241108085629572500000005"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0210f62074b70c53c"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0210f62074b70c53c"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0210f62074b70c53c"
  }
}

# Launch Template: lt-0dbd35aafb1de6063
resource "aws_launch_template" "lt-0dbd35aafb1de6063" {
  name = "etime-stage-b-14si-20240410102803479400000016"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0dbd35aafb1de6063"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0dbd35aafb1de6063"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0dbd35aafb1de6063"
  }
}

# Launch Template: lt-03efae88b42d320d5
resource "aws_launch_template" "lt-03efae88b42d320d5" {
  name = "etime-stage-skt-g-14si-20240410102753575400000005"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-03efae88b42d320d5"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-03efae88b42d320d5"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-03efae88b42d320d5"
  }
}

# Launch Template: lt-0c2298f8dafed605a
resource "aws_launch_template" "lt-0c2298f8dafed605a" {
  name = "etime-stage-skt-b-14si-20240410102753575300000003"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0c2298f8dafed605a"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0c2298f8dafed605a"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0c2298f8dafed605a"
  }
}

# Launch Template: lt-07317d18625133ffc
resource "aws_launch_template" "lt-07317d18625133ffc" {
  name = "etime-stage-g-14si-20240410102803204000000014"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-07317d18625133ffc"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-07317d18625133ffc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-07317d18625133ffc"
  }
}

# Launch Template: lt-0a25463a25a4f718a
resource "aws_launch_template" "lt-0a25463a25a4f718a" {
  name = "etime-stage-cmd-g-14si-20241108085629531800000001"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0a25463a25a4f718a"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0a25463a25a4f718a"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0a25463a25a4f718a"
  }
}

# Launch Template: lt-021f08838ac9cede4
resource "aws_launch_template" "lt-021f08838ac9cede4" {
  name = "etime-stage-cmd-b-14si-20241108085629645800000007"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-021f08838ac9cede4"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-021f08838ac9cede4"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-021f08838ac9cede4"
  }
}

# Launch Template: lt-068f342622b22f30a
resource "aws_launch_template" "lt-068f342622b22f30a" {
  name = "etime-stage-b-14si-20240410102803055500000012"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-06e2817ae86814235.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-068f342622b22f30a"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-068f342622b22f30a"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-068f342622b22f30a"
  }
}

# Launch Template: lt-0f96ceb7b890bd5a2
resource "aws_launch_template" "lt-0f96ceb7b890bd5a2" {
  name = "elementtime-test-socket-green-20220801053600505900000001"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0f96ceb7b890bd5a2"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0f96ceb7b890bd5a2"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0f96ceb7b890bd5a2"
  }
}

# Launch Template: lt-037d270f1eb9eea9c
resource "aws_launch_template" "lt-037d270f1eb9eea9c" {
  name = "elementtime-test-socket-blue-20220802101408554000000001"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-037d270f1eb9eea9c"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-037d270f1eb9eea9c"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-037d270f1eb9eea9c"
  }
}

# Launch Template: lt-0f8a3144cff4dae51
resource "aws_launch_template" "lt-0f8a3144cff4dae51" {
  name = "elementtime-test-green-20220808102316610600000001"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0f8a3144cff4dae51"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0f8a3144cff4dae51"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0f8a3144cff4dae51"
  }
}

# Launch Template: lt-06995da340bc7e5c6
resource "aws_launch_template" "lt-06995da340bc7e5c6" {
  name = "elementtime-test-cmd-green-20241108095715442700000009"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-06995da340bc7e5c6"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-06995da340bc7e5c6"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-06995da340bc7e5c6"
  }
}

# Launch Template: lt-0a090a26a2e98751a
resource "aws_launch_template" "lt-0a090a26a2e98751a" {
  name = "elementtime-test-cmd-blue-20241108095714979800000003"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0a090a26a2e98751a"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0a090a26a2e98751a"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0a090a26a2e98751a"
  }
}

# Launch Template: lt-0a9e1a6d54722b12e
resource "aws_launch_template" "lt-0a9e1a6d54722b12e" {
  name = "elementtime-test-blue-20220808102316846900000003"

  instance_type = "t4g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0a9e1a6d54722b12e"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0a9e1a6d54722b12e"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0a9e1a6d54722b12e"
  }
}

# Launch Template: lt-0fbfa6b341ae5a01f
resource "aws_launch_template" "lt-0fbfa6b341ae5a01f" {
  name = "elementtime-stage-socket-green-20220808104728914200000001"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0fbfa6b341ae5a01f"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0fbfa6b341ae5a01f"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0fbfa6b341ae5a01f"
  }
}

# Launch Template: lt-05b0a9a8f291d2dfb
resource "aws_launch_template" "lt-05b0a9a8f291d2dfb" {
  name = "elementtime-stage-socket-blue-20220808104729545800000007"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-05b0a9a8f291d2dfb"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-05b0a9a8f291d2dfb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-05b0a9a8f291d2dfb"
  }
}

# Launch Template: lt-05139e0a9b8cf06e3
resource "aws_launch_template" "lt-05139e0a9b8cf06e3" {
  name = "elementtime-stage-green-2022080810474174790000000f"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-05139e0a9b8cf06e3"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-05139e0a9b8cf06e3"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-05139e0a9b8cf06e3"
  }
}

# Launch Template: lt-0e7eff28f37b34df9
resource "aws_launch_template" "lt-0e7eff28f37b34df9" {
  name = "elementtime-stage-cmd-green-20241108095715273400000005"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0e7eff28f37b34df9"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0e7eff28f37b34df9"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0e7eff28f37b34df9"
  }
}

# Launch Template: lt-06e7b24f25b1af45d
resource "aws_launch_template" "lt-06e7b24f25b1af45d" {
  name = "elementtime-stage-cmd-blue-20241108095714735100000001"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-06e7b24f25b1af45d"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-06e7b24f25b1af45d"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-06e7b24f25b1af45d"
  }
}

# Launch Template: lt-0f2b473baa85e32a2
resource "aws_launch_template" "lt-0f2b473baa85e32a2" {
  name = "elementtime-stage-blue-2022080810474174780000000d"

  instance_type = "m8g.medium"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0f2b473baa85e32a2"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0f2b473baa85e32a2"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0f2b473baa85e32a2"
  }
}

# Launch Template: lt-090b6efcc2b0d4f99
resource "aws_launch_template" "lt-090b6efcc2b0d4f99" {
  name = "elementtime-stage-socket-green-20220808104728969800000003"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-090b6efcc2b0d4f99"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-090b6efcc2b0d4f99"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-090b6efcc2b0d4f99"
  }
}

# Launch Template: lt-0eab43453208c2377
resource "aws_launch_template" "lt-0eab43453208c2377" {
  name = "elementtime-stage-socket-blue-20220808104729363200000005"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0eab43453208c2377"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0eab43453208c2377"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0eab43453208c2377"
  }
}

# Launch Template: lt-0fe81c28bab290f06
resource "aws_launch_template" "lt-0fe81c28bab290f06" {
  name = "elementtime-stage-green-20220808104741365600000009"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0fe81c28bab290f06"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0fe81c28bab290f06"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0fe81c28bab290f06"
  }
}

# Launch Template: lt-0b04e638418b62aac
resource "aws_launch_template" "lt-0b04e638418b62aac" {
  name = "elementtime-stage-cmd-green-2024110809571545790000000b"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0b04e638418b62aac"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0b04e638418b62aac"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0b04e638418b62aac"
  }
}

# Launch Template: lt-0e57656fe14c138c0
resource "aws_launch_template" "lt-0e57656fe14c138c0" {
  name = "elementtime-stage-cmd-blue-20241108095715385700000007"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0e57656fe14c138c0"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0e57656fe14c138c0"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0e57656fe14c138c0"
  }
}

# Launch Template: lt-0e9ca7f6d95b30f52
resource "aws_launch_template" "lt-0e9ca7f6d95b30f52" {
  name = "elementtime-stage-blue-2022080810474136570000000b"

  instance_type = "m8g.large"
  image_id = "ami-04ca030c26a97465a"

  vpc_security_group_ids = [
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0e9d9aa5c428a5c03.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0e9ca7f6d95b30f52"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0e9ca7f6d95b30f52"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0e9ca7f6d95b30f52"
  }
}

# Launch Template: lt-0432a41ea4785ba95
resource "aws_launch_template" "lt-0432a41ea4785ba95" {
  name = "elementsup-stage-green-20240204051109257100000001"

  instance_type = "t4g.small"
  image_id = "ami-075beeb4b028a712d"

  vpc_security_group_ids = [
    "aws_security_group.elementSeries_prod_vpc.id",
    "aws_security_group.sg-0d4ca909ae44ef9a4.id",
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0432a41ea4785ba95"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0432a41ea4785ba95"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0432a41ea4785ba95"
  }
}

# Launch Template: lt-0bf2553d035a5590e
resource "aws_launch_template" "lt-0bf2553d035a5590e" {
  name = "elementsup-stage-blue-20240204051109267100000003"

  instance_type = "t4g.small"
  image_id = "ami-075beeb4b028a712d"

  vpc_security_group_ids = [
    "aws_security_group.elementSeries_prod_vpc.id",
    "aws_security_group.sg-0d4ca909ae44ef9a4.id",
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0bf2553d035a5590e"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0bf2553d035a5590e"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0bf2553d035a5590e"
  }
}

# Launch Template: lt-0706143bb0def5e8f
resource "aws_launch_template" "lt-0706143bb0def5e8f" {
  name = "elementstaff-stage-green-20240212104241109900000004"

  instance_type = "t4g.small"
  image_id = "ami-075beeb4b028a712d"

  vpc_security_group_ids = [
    "aws_security_group.elementSeries_prod_vpc.id",
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-02c028c79d15adf86.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0706143bb0def5e8f"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0706143bb0def5e8f"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0706143bb0def5e8f"
  }
}

# Launch Template: lt-0cc8e2d2ee2af8118
resource "aws_launch_template" "lt-0cc8e2d2ee2af8118" {
  name = "elementstaff-stage-blue-20240212104241107800000002"

  instance_type = "t4g.small"
  image_id = "ami-075beeb4b028a712d"

  vpc_security_group_ids = [
    "aws_security_group.elementSeries_prod_vpc.id",
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-02c028c79d15adf86.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0cc8e2d2ee2af8118"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0cc8e2d2ee2af8118"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0cc8e2d2ee2af8118"
  }
}

# Launch Template: lt-0f14d9e6488689826
resource "aws_launch_template" "lt-0f14d9e6488689826" {
  name = "elementrec-stage-green-20240212092143522300000003"

  instance_type = "t3a.small"
  image_id = "ami-0091208de35b8d49b"

  vpc_security_group_ids = [
    "aws_security_group.sg-0b433a6d6c584ef79.id",
    "aws_security_group.elementSeries_prod_vpc.id",
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0f14d9e6488689826"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0f14d9e6488689826"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0f14d9e6488689826"
  }
}

# Launch Template: lt-0b632550e3bf25eaa
resource "aws_launch_template" "lt-0b632550e3bf25eaa" {
  name = "elementrec-stage-blue-20240212092143457900000001"

  instance_type = "t3a.small"
  image_id = "ami-0091208de35b8d49b"

  vpc_security_group_ids = [
    "aws_security_group.sg-0b433a6d6c584ef79.id",
    "aws_security_group.elementSeries_prod_vpc.id",
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0b632550e3bf25eaa"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0b632550e3bf25eaa"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0b632550e3bf25eaa"
  }
}

# Launch Template: lt-0459e774ce8822a2f
resource "aws_launch_template" "lt-0459e774ce8822a2f" {
  name = "elementcentre-stage-green-20240207095935633800000001"

  instance_type = "t4g.small"
  image_id = "ami-075beeb4b028a712d"

  vpc_security_group_ids = [
    "aws_security_group.elementSeries_prod_vpc.id",
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ac562a2b2761e254.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-0459e774ce8822a2f"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-0459e774ce8822a2f"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-0459e774ce8822a2f"
  }
}

# Launch Template: lt-079f444f6bc8a8ec9
resource "aws_launch_template" "lt-079f444f6bc8a8ec9" {
  name = "elementcentre-stage-blue-20240207095935650400000003"

  instance_type = "t4g.small"
  image_id = "ami-075beeb4b028a712d"

  vpc_security_group_ids = [
    "aws_security_group.elementSeries_prod_vpc.id",
    "aws_security_group.sg-0ea2aca1e6a8d47fe.id",
    "aws_security_group.sg-0ac562a2b2761e254.id",
    "aws_security_group.sg-0ea9a1c02b8ef60bd.id",
  ]


  monitoring {
    enabled = true
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name        = "lt-079f444f6bc8a8ec9"
      Environment = var.environment
      ManagedBy   = "replimap"
    }
  }

  tags = {
    Name        = "lt-079f444f6bc8a8ec9"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "lt-079f444f6bc8a8ec9"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/ghostrpc-alb-prod-green/e6ea5c97d2d8fce0",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:351788af-e499-48f5-a280-77a99c495aae:autoScalingGroupName/asg-ghostrpc-prod-green"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-base"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-ghostrpc-stage.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "ghostrpc-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "ghostrpc"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-0091208de35b8d49b"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-ghostrpc-stage-green"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/ghostrpc-alb-prod-blue/fe898ecb1068f985",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:be9f5164-bb44-426e-b1f9-bfc73f92950d:autoScalingGroupName/asg-ghostrpc-prod-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-base"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-ghostrpc-stage.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "ghostrpc-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "ghostrpc"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-0091208de35b8d49b"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-ghostrpc-stage-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-test-skt-g-14si/34ce0d4fd832ebee",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:58392dd4-dd4e-4272-8bcc-c5370d66f93e:autoScalingGroupName/asg-etime-test-skt-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-test-skt-new-env-14si.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "etime-test"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "etime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = "14si"
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "test"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-etime-test-skt-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-test-skt-b-14si/9ce161490594477c",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:257acaea-2ea8-4046-a66c-17cac1b454a7:autoScalingGroupName/asg-etime-test-skt-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-test-skt-new-env-14si.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "etime-test"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "etime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = "14si"
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "test"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-etime-test-skt-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-test-g-14si/a4c818664f160ca3",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:b096fbcd-f389-4724-9f46-90bde8699be7:autoScalingGroupName/asg-etime-test-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-test-new-env-14si.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "etime-test"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "etime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = "14si"
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "test"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-etime-test-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-test-cmd-g-14si/20b818f5f1bf64b0",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:bf19a68e-6e53-4246-b5d8-2f8b0b47a244:autoScalingGroupName/asg-etime-test-cmd-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-test-cmd-new-env-14si.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "etime-test"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "etime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = "14si"
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "test"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-etime-test-cmd-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-test-cmd-b-14si/0f5eb0935ae53c51",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:852081d3-61b1-4a5b-8d65-0da210bcfeb2:autoScalingGroupName/asg-etime-test-cmd-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-test-cmd-new-env-14si.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "etime-test"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "etime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = "14si"
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "test"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-etime-test-cmd-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-test-b-14si/63b805c28ac9b7b0",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:082c0d78-6cc7-48a7-be75-6219718782af:autoScalingGroupName/asg-etime-test-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-test-new-env-14si.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "etime-test"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "etime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = "14si"
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "test"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-etime-test-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-stage-skt-g-14si
resource "aws_autoscaling_group" "asg-etime-stage-skt-g-14si_1" {
  name = "asg-etime-stage-skt-g-14si"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0c4c3b7bc83ee5b4b.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-stage-skt-g-14si/caca675f49518d51",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:81582dc1-bc9e-46e4-b4a7-9ff875cdb82e:autoScalingGroupName/asg-etime-stage-skt-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage-skt-new-env-14si.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "etime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "etime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = "14si"
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-etime-stage-skt-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-stage-skt-b-14si
resource "aws_autoscaling_group" "asg-etime-stage-skt-b-14si_1" {
  name = "asg-etime-stage-skt-b-14si"

  min_size         = 1
  max_size         = 1
  desired_capacity = 1

  launch_template {
    id      = aws_launch_template.lt-026402e837ad46bc1.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-stage-skt-b-14si/94e78c753ef07194",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:7f170b58-d272-4119-b337-98a613edd8c1:autoScalingGroupName/asg-etime-stage-skt-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage-skt-new-env-14si.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "etime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "etime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = "14si"
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-etime-stage-skt-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-stage-g-14si
resource "aws_autoscaling_group" "asg-etime-stage-g-14si_1" {
  name = "asg-etime-stage-g-14si"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-03e1bae900ffc94bc.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-stage-g-14si/6f686d10e8e4bdc3",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:0361ec3d-4534-4c1d-830e-9e290a1d7045:autoScalingGroupName/asg-etime-stage-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage-new-env-14si.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "etime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "etime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = "14si"
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-etime-stage-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-stage-cmd-g-14si
resource "aws_autoscaling_group" "asg-etime-stage-cmd-g-14si_1" {
  name = "asg-etime-stage-cmd-g-14si"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-09ae1bebe1240319f.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-stage-cmd-g-14si/92428e2976ec9624",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:2ed62f75-a40f-423b-94f8-2d3c1f8071c5:autoScalingGroupName/asg-etime-stage-cmd-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage-cmd-new-env-14si.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "etime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "etime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = "14si"
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-etime-stage-cmd-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-stage-cmd-b-14si
resource "aws_autoscaling_group" "asg-etime-stage-cmd-b-14si_1" {
  name = "asg-etime-stage-cmd-b-14si"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0210f62074b70c53c.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-stage-cmd-b-14si/8ae6beafa0fab497",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:045ef8b4-d4b6-44eb-9ca5-1ea45cebe7cd:autoScalingGroupName/asg-etime-stage-cmd-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage-cmd-new-env-14si.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "etime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "etime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = "14si"
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-etime-stage-cmd-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-etime-stage-b-14si
resource "aws_autoscaling_group" "asg-etime-stage-b-14si_1" {
  name = "asg-etime-stage-b-14si"

  min_size         = 1
  max_size         = 2
  desired_capacity = 1

  launch_template {
    id      = aws_launch_template.lt-0dbd35aafb1de6063.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-stage-b-14si/e9649c8e9cfca7bd",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:f7dd2672-4e42-4ac1-a52f-237a77047347:autoScalingGroupName/asg-etime-stage-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage-new-env-14si.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "etime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "etime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = "14si"
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-etime-stage-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-prod-skt-g-14si/b2ac75ed028f753a",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:43ddaec5-0c52-426b-b068-322982434238:autoScalingGroupName/asg-etime-prod-skt-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage-skt-new-env-14si.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "etime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "etime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = "14si"
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-etime-stage-skt-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-prod-skt-b-14si/f3a1fa1acc3d8aab",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:421c2efc-fee6-4adb-a576-ff70e5d4caf5:autoScalingGroupName/asg-etime-prod-skt-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage-skt-new-env-14si.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "etime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "etime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = "14si"
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-etime-stage-skt-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-prod-g-14si/bb47a23d13331ca0",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:81cf2d7c-5221-4637-b94d-31f097df4c01:autoScalingGroupName/asg-etime-prod-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage-new-env-14si.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "etime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "etime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = "14si"
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-etime-stage-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-prod-cmd-g-14si/a48d46b24f2ca9b2",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:497b4cc4-f6d6-40c4-ad48-6d89efa6f1f3:autoScalingGroupName/asg-etime-prod-cmd-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage-cmd-new-env-14si.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "etime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "etime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = "14si"
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-etime-stage-cmd-g-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-prod-cmd-b-14si/5e754f4e63975546",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:1e2285e1-1403-494b-91a1-c13a6f6d2077:autoScalingGroupName/asg-etime-prod-cmd-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage-cmd-new-env-14si.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "etime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "etime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = "14si"
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-etime-stage-cmd-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-prod-b-14si/f643851b073af7fa",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:caef9fa1-fcb7-4611-8ebb-cd2d932e3e59:autoScalingGroupName/asg-etime-prod-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage-new-env-14si.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "etime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "etime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = "14si"
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-etime-stage-b-14si"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-test-socket-green/6b1446596a895d1d",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:cdf0c804-fb3e-44af-b3b0-56c51eb21fdb:autoScalingGroupName/asg-elementtime-test-socket-green"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-fix-vul-improve"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-test-socket.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementtime-test"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementtime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "test"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementtime-test-socket-green"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-test-socket-blue/7702ed0921031361",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:0d5750da-80fe-492f-bd58-0eed755d39ba:autoScalingGroupName/asg-elementtime-test-socket-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-fix-vul-improve"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-test-socket.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementtime-test"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementtime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "test"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementtime-test-socket-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-test-green/1d8fc63f16d0bd23",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:2d445db8-68ab-4725-aa0d-0c731c11a2d9:autoScalingGroupName/asg-elementtime-test-green"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-fix-vul-improve"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-test.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementtime-test"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementtime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "test"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementtime-test-green"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-test-cmd-green/24c5eed35c12d165",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:be15902b-44fd-44dd-8cfe-ade04181a2b8:autoScalingGroupName/asg-elementtime-test-cmd-green"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-fix-vul-improve"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-test-cmd.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementtime-test"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementtime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "test"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementtime-test-cmd-green"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-test-cmd-blue/9cb9b9bfb91c728b",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:6f4bea1c-bddd-4aaa-870c-96b7530cce20:autoScalingGroupName/asg-elementtime-test-cmd-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-fix-vul-improve"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-test-cmd.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementtime-test"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementtime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "test"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementtime-test-cmd-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-test-blue/adf00bf65e691a41",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:165f0a05-a0a6-4d24-a486-8459ef29da63:autoScalingGroupName/asg-elementtime-test-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-fix-vul-improve"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-test.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementtime-test"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementtime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "test"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementtime-test-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-stage-socket-green
resource "aws_autoscaling_group" "asg-elementtime-stage-socket-green_1" {
  name = "asg-elementtime-stage-socket-green"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0fbfa6b341ae5a01f.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-stage-socket-green/e9d1b115681f2b9a",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:8b1c8c43-331a-4262-93a6-2f9e517e28fa:autoScalingGroupName/asg-elementtime-stage-socket-green"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-fix-vul-improve"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage-socket.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementtime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementtime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementtime-stage-socket-green"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-stage-socket-blue
resource "aws_autoscaling_group" "asg-elementtime-stage-socket-blue_1" {
  name = "asg-elementtime-stage-socket-blue"

  min_size         = 1
  max_size         = 1
  desired_capacity = 1

  launch_template {
    id      = aws_launch_template.lt-05b0a9a8f291d2dfb.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-stage-socket-blue/4247d208ae10d096",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:68eb2ebc-70ed-4ff5-9e93-4133184b1288:autoScalingGroupName/asg-elementtime-stage-socket-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-fix-vul-improve"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage-socket.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementtime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementtime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementtime-stage-socket-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-stage-green
resource "aws_autoscaling_group" "asg-elementtime-stage-green_1" {
  name = "asg-elementtime-stage-green"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-05139e0a9b8cf06e3.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-stage-green/f3f73cc137565811",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:dc4eea7e-593a-4916-b33a-3dccfc17415a:autoScalingGroupName/asg-elementtime-stage-green"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-fix-vul-improve"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementtime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementtime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementtime-stage-green"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-stage-cmd-green
resource "aws_autoscaling_group" "asg-elementtime-stage-cmd-green_1" {
  name = "asg-elementtime-stage-cmd-green"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-0e7eff28f37b34df9.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-stage-cmd-green/df42649d76cf2a3f",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:87943660-4cdc-4d78-b6b7-81ffa03ea808:autoScalingGroupName/asg-elementtime-stage-cmd-green"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-fix-vul-improve"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage-cmd.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementtime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementtime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementtime-stage-cmd-green"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-stage-cmd-blue
resource "aws_autoscaling_group" "asg-elementtime-stage-cmd-blue_1" {
  name = "asg-elementtime-stage-cmd-blue"

  min_size         = 0
  max_size         = 0
  desired_capacity = 0

  launch_template {
    id      = aws_launch_template.lt-06e7b24f25b1af45d.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-stage-cmd-blue/372538449cab9357",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:d4df912f-5696-496b-8bd2-ebed0490f0e8:autoScalingGroupName/asg-elementtime-stage-cmd-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-fix-vul-improve"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage-cmd.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementtime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementtime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementtime-stage-cmd-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
    propagate_at_launch = true
  }
}

# Auto Scaling Group: asg-elementtime-stage-blue
resource "aws_autoscaling_group" "asg-elementtime-stage-blue_1" {
  name = "asg-elementtime-stage-blue"

  min_size         = 1
  max_size         = 2
  desired_capacity = 1

  launch_template {
    id      = aws_launch_template.lt-0f2b473baa85e32a2.id
    version = "$Latest"
  }

  vpc_zone_identifier = [
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-stage-blue/3080d01af67bb17e",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:0939c802-63d0-4f0f-ae1a-1a96fa74caaa:autoScalingGroupName/asg-elementtime-stage-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-fix-vul-improve"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementtime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementtime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementtime-stage-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-prod-socket-green/8c70e31eba804609",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:94de1253-42be-4692-8629-d11b3a48efc5:autoScalingGroupName/asg-elementtime-prod-socket-green"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-fix-vul-improve"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage-socket.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementtime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementtime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementtime-stage-socket-green"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-prod-socket-blue/db10ec971800e3af",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:55e95a3c-10dd-434d-a614-a4abd604d049:autoScalingGroupName/asg-elementtime-prod-socket-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-fix-vul-improve"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage-socket.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementtime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementtime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementtime-stage-socket-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-prod-green/8c851fcbc83b25c4",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:f79048a6-55cc-4d6a-a28b-e6ce2136c7cf:autoScalingGroupName/asg-elementtime-prod-green"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-fix-vul-improve"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementtime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementtime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementtime-stage-green"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-prod-cmd-green/5b4d25ce0fc0a151",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:d1494b6c-5e23-430f-a08b-e41dc1c0bf9c:autoScalingGroupName/asg-elementtime-prod-cmd-green"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-fix-vul-improve"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage-cmd.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementtime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementtime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementtime-stage-cmd-green"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-prod-cmd-blue/897ea90d93409140",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:9e0eedf5-2f0c-4f53-a261-ed92090c8763:autoScalingGroupName/asg-elementtime-prod-cmd-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-fix-vul-improve"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage-cmd.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementtime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementtime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementtime-stage-cmd-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/etime-alb-prod-blue/435d18369923348c",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:f8926462-b24e-4cde-be48-fe91629a814a:autoScalingGroupName/asg-elementtime-prod-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-fix-vul-improve"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-etime-stage.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementtime-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementtime"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-04ca030c26a97465a"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementtime-stage-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/esup-alb-prod-green/77771596b18edef1",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:05a9723c-68fb-44c2-b9d9-2ad0ca66ffd3:autoScalingGroupName/asg-elementsup-prod-green"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-base"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-elementsup-stage.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementsup-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementsup"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-075beeb4b028a712d"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementsup-stage-green"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/esup-alb-prod-blue/72bf20c9a45fcadb",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:8d261fee-045a-4821-82cc-89e7179c7aba:autoScalingGroupName/asg-elementsup-prod-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-base"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-elementsup-stage.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementsup-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementsup"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-075beeb4b028a712d"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementsup-stage-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/estaff-alb-prod-green/80e221840808a45f",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:68e67b78-5080-420e-bc38-5b111d816628:autoScalingGroupName/asg-elementstaff-prod-green"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-base"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-estaff-new-stage.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementstaff-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementstaff"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-075beeb4b028a712d"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementstaff-stage-green"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/estaff-alb-prod-blue/9c3174929d979eba",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:02e852af-1faa-4876-87d0-488e1c50752f:autoScalingGroupName/asg-elementstaff-prod-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-base"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-estaff-new-stage.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementstaff-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementstaff"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-075beeb4b028a712d"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementstaff-stage-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/erec-alb-prod-green/d2baecf0a6c5cdb7",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:e03c114b-aa94-43a9-8d59-9e7b44ccc4ed:autoScalingGroupName/asg-elementrec-prod-green"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-base"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-elementrec-stage.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementrec-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementrec"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-0091208de35b8d49b"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementrec-stage-green"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/erec-alb-prod-blue/3f8141308c99dc70",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:f3fa7235-37f2-4bf0-802b-57e639b1c1eb:autoScalingGroupName/asg-elementrec-prod-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-base"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-elementrec-stage.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementrec-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementrec"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-0091208de35b8d49b"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementrec-stage-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/ecentre-alb-prod-green/7b3287f17303e670",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:acc367f3-93ba-4aab-a938-59047b08bde3:autoScalingGroupName/asg-elementcentre-prod-green"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-base"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-elementcentre-stage.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementcentre-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementcentre"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-075beeb4b028a712d"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementcentre-stage-green"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
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
    "aws_subnet.stage-subnet-private-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-private-ap-southeast-2a.id",
  ]

  target_group_arns = [
    "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/ecentre-alb-prod-blue/eec84dc640ab5474",
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
    value               = "replimap"
    propagate_at_launch = true
  }

  tag {
    key                 = "SourceId"
    value               = "arn:aws:autoscaling:ap-southeast-2:542859091916:autoScalingGroup:1be8d6e7-0f37-40f3-951d-01880d1e4c89:autoScalingGroupName/asg-elementcentre-prod-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_BRANCH
    value               = "upgrade-2204-base"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_DC
    value               = "stage-ap-southeast-2"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_PLAY
    value               = "plays/base-ami-elementcentre-stage.yml"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_POOL
    value               = "ac-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_ROLE
    value               = "elementcentre-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = ANSIBLE_S3_BUCKET
    value               = "ac-secrets-stage"
    propagate_at_launch = true
  }

  tag {
    key                 = "Cost Center"
    value               = "elementcentre"
    propagate_at_launch = true
  }

  tag {
    key                 = ENV_VERSION
    value               = ""
    propagate_at_launch = true
  }

  tag {
    key                 = Environment
    value               = "stage"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshot
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotLongTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = MakeSnapshotShortTerm
    value               = "False"
    propagate_at_launch = true
  }

  tag {
    key                 = "N/A"
    value               = "owned"
    propagate_at_launch = true
  }

  tag {
    key                 = ami_id
    value               = "ami-075beeb4b028a712d"
    propagate_at_launch = true
  }

  tag {
    key                 = route53_record_prefix
    value               = "asg-elementcentre-stage-blue"
    propagate_at_launch = true
  }

  tag {
    key                 = vpc_domain
    value               = "sydney.stage.adroitcreations.org"
    propagate_at_launch = true
  }

  tag {
    key                 = zone_id
    value               = "Z0510321LZZI860UP8GE"
    propagate_at_launch = true
  }
}