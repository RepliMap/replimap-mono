# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/ghostrpc-alb-stage-green/e6ea5c97d2d8fce0
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_ghostrpc-alb-stage-green_e6ea5c97d2d8fce0" {
  name        = "ghostrpc-alb-stage-green"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/robots.txt"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/ghostrpc-alb-stage-green/e6ea5c97d2d8fce0"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/ghostrpc-alb-prod-green/e6ea5c97d2d8fce0"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/ghostrpc-alb-stage-blue/fe898ecb1068f985
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_ghostrpc-alb-stage-blue_fe898ecb1068f985" {
  name        = "ghostrpc-alb-stage-blue"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/robots.txt"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/ghostrpc-alb-stage-blue/fe898ecb1068f985"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/ghostrpc-alb-prod-blue/fe898ecb1068f985"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-skt-g-14si/34ce0d4fd832ebee
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-test-skt-g-14si_34ce0d4fd832ebee" {
  name        = "etime-alb-test-skt-g-14si"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-skt-g-14si/34ce0d4fd832ebee"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-skt-g-14si/34ce0d4fd832ebee"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-skt-b-14si/9ce161490594477c
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-test-skt-b-14si_9ce161490594477c" {
  name        = "etime-alb-test-skt-b-14si"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-skt-b-14si/9ce161490594477c"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-skt-b-14si/9ce161490594477c"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-g-14si/a4c818664f160ca3
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-test-g-14si_a4c818664f160ca3" {
  name        = "etime-alb-test-g-14si"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-g-14si/a4c818664f160ca3"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-g-14si/a4c818664f160ca3"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-cmd-g-14si/20b818f5f1bf64b0
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-test-cmd-g-14si_20b818f5f1bf64b0" {
  name        = "etime-alb-test-cmd-g-14si"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-cmd-g-14si/20b818f5f1bf64b0"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-cmd-g-14si/20b818f5f1bf64b0"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-cmd-b-14si/0f5eb0935ae53c51
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-test-cmd-b-14si_0f5eb0935ae53c51" {
  name        = "etime-alb-test-cmd-b-14si"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-cmd-b-14si/0f5eb0935ae53c51"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-cmd-b-14si/0f5eb0935ae53c51"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-b-14si/63b805c28ac9b7b0
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-test-b-14si_63b805c28ac9b7b0" {
  name        = "etime-alb-test-b-14si"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-b-14si/63b805c28ac9b7b0"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-b-14si/63b805c28ac9b7b0"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-skt-g-14si/caca675f49518d51
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-skt-g-14si_caca675f49518d51" {
  name        = "etime-alb-stage-skt-g-14si"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-skt-g-14si/caca675f49518d51"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-skt-g-14si/caca675f49518d51"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-skt-b-14si/94e78c753ef07194
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-skt-b-14si_94e78c753ef07194" {
  name        = "etime-alb-stage-skt-b-14si"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-skt-b-14si/94e78c753ef07194"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-skt-b-14si/94e78c753ef07194"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-g-14si/6f686d10e8e4bdc3
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-g-14si_6f686d10e8e4bdc3" {
  name        = "etime-alb-stage-g-14si"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-g-14si/6f686d10e8e4bdc3"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-g-14si/6f686d10e8e4bdc3"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-cmd-g-14si/92428e2976ec9624
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-cmd-g-14si_92428e2976ec9624" {
  name        = "etime-alb-stage-cmd-g-14si"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-cmd-g-14si/92428e2976ec9624"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-cmd-g-14si/92428e2976ec9624"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-cmd-b-14si/8ae6beafa0fab497
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-cmd-b-14si_8ae6beafa0fab497" {
  name        = "etime-alb-stage-cmd-b-14si"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-cmd-b-14si/8ae6beafa0fab497"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-cmd-b-14si/8ae6beafa0fab497"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-b-14si/e9649c8e9cfca7bd
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-b-14si_e9649c8e9cfca7bd" {
  name        = "etime-alb-stage-b-14si"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-b-14si/e9649c8e9cfca7bd"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-b-14si/e9649c8e9cfca7bd"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-skt-g-14si/b2ac75ed028f753a
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-skt-g-14si_b2ac75ed028f753a" {
  name        = "etime-alb-stage-skt-g-14si"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-skt-g-14si/b2ac75ed028f753a"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-prod-skt-g-14si/b2ac75ed028f753a"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-skt-b-14si/f3a1fa1acc3d8aab
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-skt-b-14si_f3a1fa1acc3d8aab" {
  name        = "etime-alb-stage-skt-b-14si"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-skt-b-14si/f3a1fa1acc3d8aab"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-prod-skt-b-14si/f3a1fa1acc3d8aab"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-g-14si/bb47a23d13331ca0
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-g-14si_bb47a23d13331ca0" {
  name        = "etime-alb-stage-g-14si"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-g-14si/bb47a23d13331ca0"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-prod-g-14si/bb47a23d13331ca0"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-cmd-g-14si/a48d46b24f2ca9b2
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-cmd-g-14si_a48d46b24f2ca9b2" {
  name        = "etime-alb-stage-cmd-g-14si"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-cmd-g-14si/a48d46b24f2ca9b2"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-prod-cmd-g-14si/a48d46b24f2ca9b2"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-cmd-b-14si/5e754f4e63975546
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-cmd-b-14si_5e754f4e63975546" {
  name        = "etime-alb-stage-cmd-b-14si"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-cmd-b-14si/5e754f4e63975546"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-prod-cmd-b-14si/5e754f4e63975546"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-b-14si/f643851b073af7fa
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-b-14si_f643851b073af7fa" {
  name        = "etime-alb-stage-b-14si"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-b-14si/f643851b073af7fa"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-prod-b-14si/f643851b073af7fa"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-socket-green/6b1446596a895d1d
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-test-socket-green_6b1446596a895d1d" {
  name        = "etime-alb-test-socket-green"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-socket-green/6b1446596a895d1d"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-socket-green/6b1446596a895d1d"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-socket-blue/7702ed0921031361
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-test-socket-blue_7702ed0921031361" {
  name        = "etime-alb-test-socket-blue"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-socket-blue/7702ed0921031361"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-socket-blue/7702ed0921031361"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-green/1d8fc63f16d0bd23
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-test-green_1d8fc63f16d0bd23" {
  name        = "etime-alb-test-green"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-green/1d8fc63f16d0bd23"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-green/1d8fc63f16d0bd23"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-cmd-green/24c5eed35c12d165
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-test-cmd-green_24c5eed35c12d165" {
  name        = "etime-alb-test-cmd-green"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-cmd-green/24c5eed35c12d165"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-cmd-green/24c5eed35c12d165"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-cmd-blue/9cb9b9bfb91c728b
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-test-cmd-blue_9cb9b9bfb91c728b" {
  name        = "etime-alb-test-cmd-blue"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-cmd-blue/9cb9b9bfb91c728b"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-cmd-blue/9cb9b9bfb91c728b"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-blue/adf00bf65e691a41
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-test-blue_adf00bf65e691a41" {
  name        = "etime-alb-test-blue"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-blue/adf00bf65e691a41"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-test-blue/adf00bf65e691a41"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-socket-green/e9d1b115681f2b9a
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-socket-green_e9d1b115681f2b9a" {
  name        = "etime-alb-stage-socket-green"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-socket-green/e9d1b115681f2b9a"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-socket-green/e9d1b115681f2b9a"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-socket-blue/4247d208ae10d096
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-socket-blue_4247d208ae10d096" {
  name        = "etime-alb-stage-socket-blue"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-socket-blue/4247d208ae10d096"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-socket-blue/4247d208ae10d096"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-green/f3f73cc137565811
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-green_f3f73cc137565811" {
  name        = "etime-alb-stage-green"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-green/f3f73cc137565811"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-green/f3f73cc137565811"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-cmd-green/df42649d76cf2a3f
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-cmd-green_df42649d76cf2a3f" {
  name        = "etime-alb-stage-cmd-green"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-cmd-green/df42649d76cf2a3f"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-cmd-green/df42649d76cf2a3f"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-cmd-blue/372538449cab9357
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-cmd-blue_372538449cab9357" {
  name        = "etime-alb-stage-cmd-blue"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-cmd-blue/372538449cab9357"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-cmd-blue/372538449cab9357"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-blue/3080d01af67bb17e
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-blue_3080d01af67bb17e" {
  name        = "etime-alb-stage-blue"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-blue/3080d01af67bb17e"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-blue/3080d01af67bb17e"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-socket-green/8c70e31eba804609
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-socket-green_8c70e31eba804609" {
  name        = "etime-alb-stage-socket-green"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-socket-green/8c70e31eba804609"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-prod-socket-green/8c70e31eba804609"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-socket-blue/db10ec971800e3af
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-socket-blue_db10ec971800e3af" {
  name        = "etime-alb-stage-socket-blue"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-socket-blue/db10ec971800e3af"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-prod-socket-blue/db10ec971800e3af"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-green/8c851fcbc83b25c4
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-green_8c851fcbc83b25c4" {
  name        = "etime-alb-stage-green"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-green/8c851fcbc83b25c4"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-prod-green/8c851fcbc83b25c4"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-cmd-green/5b4d25ce0fc0a151
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-cmd-green_5b4d25ce0fc0a151" {
  name        = "etime-alb-stage-cmd-green"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-cmd-green/5b4d25ce0fc0a151"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-prod-cmd-green/5b4d25ce0fc0a151"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-cmd-blue/897ea90d93409140
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-cmd-blue_897ea90d93409140" {
  name        = "etime-alb-stage-cmd-blue"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-cmd-blue/897ea90d93409140"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-prod-cmd-blue/897ea90d93409140"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-blue/435d18369923348c
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_etime-alb-stage-blue_435d18369923348c" {
  name        = "etime-alb-stage-blue"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 5
    timeout             = 15
    interval            = 30
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-stage-blue/435d18369923348c"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/etime-alb-prod-blue/435d18369923348c"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/esup-alb-stage-green/77771596b18edef1
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_esup-alb-stage-green_77771596b18edef1" {
  name        = "esup-alb-stage-green"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/robots.txt"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/esup-alb-stage-green/77771596b18edef1"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/esup-alb-prod-green/77771596b18edef1"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/esup-alb-stage-blue/72bf20c9a45fcadb
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_esup-alb-stage-blue_72bf20c9a45fcadb" {
  name        = "esup-alb-stage-blue"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/robots.txt"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/esup-alb-stage-blue/72bf20c9a45fcadb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/esup-alb-prod-blue/72bf20c9a45fcadb"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/estaff-alb-stage-green/80e221840808a45f
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_estaff-alb-stage-green_80e221840808a45f" {
  name        = "estaff-alb-stage-green"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/api/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/estaff-alb-stage-green/80e221840808a45f"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/estaff-alb-prod-green/80e221840808a45f"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/estaff-alb-stage-blue/9c3174929d979eba
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_estaff-alb-stage-blue_9c3174929d979eba" {
  name        = "estaff-alb-stage-blue"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/api/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/estaff-alb-stage-blue/9c3174929d979eba"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/estaff-alb-prod-blue/9c3174929d979eba"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/erec-alb-stage-green/d2baecf0a6c5cdb7
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_erec-alb-stage-green_d2baecf0a6c5cdb7" {
  name        = "erec-alb-stage-green"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/robots.txt"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/erec-alb-stage-green/d2baecf0a6c5cdb7"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/erec-alb-prod-green/d2baecf0a6c5cdb7"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/erec-alb-stage-blue/3f8141308c99dc70
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_erec-alb-stage-blue_3f8141308c99dc70" {
  name        = "erec-alb-stage-blue"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/robots.txt"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/erec-alb-stage-blue/3f8141308c99dc70"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/erec-alb-prod-blue/3f8141308c99dc70"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/ecentre-alb-stage-green/7b3287f17303e670
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_ecentre-alb-stage-green_7b3287f17303e670" {
  name        = "ecentre-alb-stage-green"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/ecentre-alb-stage-green/7b3287f17303e670"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/ecentre-alb-prod-green/7b3287f17303e670"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/ecentre-alb-stage-blue/eec84dc640ab5474
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_ecentre-alb-stage-blue_eec84dc640ab5474" {
  name        = "ecentre-alb-stage-blue"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/ecentre-alb-stage-blue/eec84dc640ab5474"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/ecentre-alb-prod-blue/eec84dc640ab5474"
  }
}

# Load Balancer: alb-etime-test-cmd-14si
resource "aws_lb" "alb-etime-test-cmd-14si" {
  name               = "alb-etime-test-cmd-14si"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0c48a0522ace9cd5f.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-etime-test-cmd-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-etime-test-cmd-14si/00083a72c6f819f5"
    "Cost Center" = "etime"
    Environment = "test"
  }
}

# Load Balancer: alb-etime-stage-cmd-14si
resource "aws_lb" "alb-etime-stage-cmd-14si_1" {
  name               = "alb-etime-stage-cmd-14si"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0c48a0522ace9cd5f.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-etime-stage-cmd-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-etime-prod-cmd-14si/1aa3995ded131824"
    "Cost Center" = "etime"
    Environment = "stage"
  }
}

# Load Balancer: alb-etime-stage-cmd-14si
resource "aws_lb" "alb-etime-stage-cmd-14si" {
  name               = "alb-etime-stage-cmd-14si"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0c48a0522ace9cd5f.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-etime-stage-cmd-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-etime-stage-cmd-14si/6529dbcd4bf4fb68"
    "Cost Center" = "etime"
    Environment = "stage"
  }
}

# Load Balancer: alb-elementtime-stage-cmd
resource "aws_lb" "alb-elementtime-stage-cmd_1" {
  name               = "alb-elementtime-stage-cmd"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0ccaad06b44bfac19.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-elementtime-stage-cmd"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-elementtime-prod-cmd/19ccf39c6d4f8dc0"
    "Cost Center" = "elementtime"
    Environment = "stage"
  }
}

# Load Balancer: alb-elementtime-test-cmd
resource "aws_lb" "alb-elementtime-test-cmd" {
  name               = "alb-elementtime-test-cmd"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0ccaad06b44bfac19.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-elementtime-test-cmd"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-elementtime-test-cmd/437995ab15a8dc2f"
    "Cost Center" = "elementtime"
    Environment = "test"
  }
}

# Load Balancer: alb-elementtime-stage-cmd
resource "aws_lb" "alb-elementtime-stage-cmd" {
  name               = "alb-elementtime-stage-cmd"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0ccaad06b44bfac19.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-elementtime-stage-cmd"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-elementtime-stage-cmd/35e2b68cadc6f899"
    "Cost Center" = "elementtime"
    Environment = "stage"
  }
}

# Load Balancer: alb-eodefault-sa-redirect
resource "aws_lb" "alb-eodefault-sa-redirect" {
  name               = "alb-eodefault-sa-redirect"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-00fdbb40e90bd913c.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-eodefault-sa-redirect"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-eodefault-sa-redirect/33bd6bf748e0a107"
    "Cost Center" = "elementOrg"
    Environment = "stage"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-test-griffith-alb-80/e36e225c11fff72a
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_eorg-test-griffith-alb-80_e36e225c11fff72a" {
  name        = "eorg-test-griffith-alb-80"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/wp/wp-login.php"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-302"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-test-griffith-alb-80/e36e225c11fff72a"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-test-griffith-alb-80/e36e225c11fff72a"
  }
}

# Load Balancer: alb-eodefault-test-griffith
resource "aws_lb" "alb-eodefault-test-griffith" {
  name               = "alb-eodefault-test-griffith"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0014ac18168dfb556.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-eodefault-test-griffith"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-eodefault-test-griffith/1cf05509a320655a"
    "Cost Center" = "elementOrg"
    Environment = "stage"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-test-griffith-alb-8080/f3edca9e0699eb33
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_eorg-test-griffith-alb-8080_f3edca9e0699eb33" {
  name        = "eorg-test-griffith-alb-8080"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-test-griffith-alb-8080/f3edca9e0699eb33"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-test-griffith-alb-8080/f3edca9e0699eb33"
  }
}

# Load Balancer: alb-eodefault-griffith
resource "aws_lb" "alb-eodefault-griffith" {
  name               = "alb-eodefault-griffith"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-03fa52cbe64ec7a1d.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-eodefault-griffith"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-eodefault-griffith/fc30b8e8733d27d2"
    "Cost Center" = "elementOrg"
    Environment = "stage"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-griffith-alb-80/2913d876dea23cf7
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_eorg-griffith-alb-80_2913d876dea23cf7" {
  name        = "eorg-griffith-alb-80"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/wp/wp-login.php"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-302"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-griffith-alb-80/2913d876dea23cf7"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-griffith-alb-80/2913d876dea23cf7"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-griffith-alb-8080/7be4e650bca5f174
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_eorg-griffith-alb-8080_7be4e650bca5f174" {
  name        = "eorg-griffith-alb-8080"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-griffith-alb-8080/7be4e650bca5f174"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-griffith-alb-8080/7be4e650bca5f174"
  }
}

# Load Balancer: alb-eo-test-ngsc-trellis
resource "aws_lb" "alb-eo-test-ngsc-trellis" {
  name               = "alb-eo-test-ngsc-trellis"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-093f297aca654df37.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-eo-test-ngsc-trellis"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-eo-test-ngsc-trellis/909a70fd9f6ed999"
    "Cost Center" = "elementOrg"
    Environment = "stage"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eo-test-ngsc-trellis-alb-80/45cdec0b984c6282
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_eo-test-ngsc-trellis-alb-80_45cdec0b984c6282" {
  name        = "eo-test-ngsc-trellis-alb-80"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/wp/wp-login.php"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 10
    interval            = 60
    matcher             = "200-302"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eo-test-ngsc-trellis-alb-80/45cdec0b984c6282"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eo-test-ngsc-trellis-alb-80/45cdec0b984c6282"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eo-test-ngsc-trellis-alb-8080/98e9ed041d55efbf
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_eo-test-ngsc-trellis-alb-8080_98e9ed041d55efbf" {
  name        = "eo-test-ngsc-trellis-alb-8080"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eo-test-ngsc-trellis-alb-8080/98e9ed041d55efbf"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eo-test-ngsc-trellis-alb-8080/98e9ed041d55efbf"
  }
}

# Load Balancer: alb-eodefault-leeton-c5
resource "aws_lb" "alb-eodefault-leeton-c5" {
  name               = "alb-eodefault-leeton-c5"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-02f52c777d84da01b.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-eodefault-leeton-c5"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-eodefault-leeton-c5/08a99dddda4bcfc7"
    "Cost Center" = "elementOrg"
    Environment = "stage"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eodefault-leeton-alb-8080-c5/1b2c3c777cb8004a
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_eodefault-leeton-alb-8080-c5_1b2c3c777cb8004a" {
  name        = "eodefault-leeton-alb-8080-c5"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eodefault-leeton-alb-8080-c5/1b2c3c777cb8004a"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eodefault-leeton-alb-8080-c5/1b2c3c777cb8004a"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eodefault-leeton-alb-80-c5/3db27c896e5ff211
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_eodefault-leeton-alb-80-c5_3db27c896e5ff211" {
  name        = "eodefault-leeton-alb-80-c5"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/wp/wp-login.php"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-302"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eodefault-leeton-alb-80-c5/3db27c896e5ff211"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eodefault-leeton-alb-80-c5/3db27c896e5ff211"
  }
}

# Load Balancer: alb-eodefault-ngsc
resource "aws_lb" "alb-eodefault-ngsc" {
  name               = "alb-eodefault-ngsc"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0271ca4f3afee1604.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-eodefault-ngsc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-eodefault-ngsc/2ff93196a330a9b1"
    "Cost Center" = "elementOrg"
    Environment = "stage"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-ngsc-alb-80/9addc31e3bac25da
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_eorg-ngsc-alb-80_9addc31e3bac25da" {
  name        = "eorg-ngsc-alb-80"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/wp/healthcheck.php"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 10
    interval            = 60
    matcher             = "200-302"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-ngsc-alb-80/9addc31e3bac25da"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-ngsc-alb-80/9addc31e3bac25da"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-ngsc-alb-8080/c0f3b582d52ce58b
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_eorg-ngsc-alb-8080_c0f3b582d52ce58b" {
  name        = "eorg-ngsc-alb-8080"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-ngsc-alb-8080/c0f3b582d52ce58b"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-ngsc-alb-8080/c0f3b582d52ce58b"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-test-ngsc-alb-8080/36237c7ab58369e4
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_eorg-test-ngsc-alb-8080_36237c7ab58369e4" {
  name        = "eorg-test-ngsc-alb-8080"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-test-ngsc-alb-8080/36237c7ab58369e4"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-test-ngsc-alb-8080/36237c7ab58369e4"
  }
}

# Load Balancer: alb-eodefault-test-ngsc
resource "aws_lb" "alb-eodefault-test-ngsc" {
  name               = "alb-eodefault-test-ngsc"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-093f297aca654df37.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-eodefault-test-ngsc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-eodefault-test-ngsc/af1fb68ffaa39a98"
    "Cost Center" = "elementOrg"
    Environment = "stage"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-test-ngsc-alb-80/d6ec13213e3070ce
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_eorg-test-ngsc-alb-80_d6ec13213e3070ce" {
  name        = "eorg-test-ngsc-alb-80"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 10
    interval            = 60
    matcher             = "200-302"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-test-ngsc-alb-80/d6ec13213e3070ce"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-test-ngsc-alb-80/d6ec13213e3070ce"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-test-ypc-alb-8080/2e2a9c70138d891e
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_eorg-test-ypc-alb-8080_2e2a9c70138d891e" {
  name        = "eorg-test-ypc-alb-8080"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-test-ypc-alb-8080/2e2a9c70138d891e"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-test-ypc-alb-8080/2e2a9c70138d891e"
  }
}

# Load Balancer: alb-eodefault-test-ypc
resource "aws_lb" "alb-eodefault-test-ypc" {
  name               = "alb-eodefault-test-ypc"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0912b5ed29155af6c.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-eodefault-test-ypc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-eodefault-test-ypc/00d275316fcab139"
    "Cost Center" = "elementOrg"
    Environment = "stage"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-test-ypc-alb-80/7c039f5b27a7fc54
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_eorg-test-ypc-alb-80_7c039f5b27a7fc54" {
  name        = "eorg-test-ypc-alb-80"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/wp/wp-login.php"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-302"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-test-ypc-alb-80/7c039f5b27a7fc54"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-test-ypc-alb-80/7c039f5b27a7fc54"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-ypc-alb-8080/a5348577a6f7ac27
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_eorg-ypc-alb-8080_a5348577a6f7ac27" {
  name        = "eorg-ypc-alb-8080"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-ypc-alb-8080/a5348577a6f7ac27"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-ypc-alb-8080/a5348577a6f7ac27"
  }
}

# Load Balancer: alb-eodefault-ypc
resource "aws_lb" "alb-eodefault-ypc" {
  name               = "alb-eodefault-ypc"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-064dd8e412e058b6d.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-eodefault-ypc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-eodefault-ypc/6fad7ac3a422b536"
    "Cost Center" = "elementOrg"
    Environment = "stage"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-ypc-alb-80/4fa13aa94cbe9b42
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_eorg-ypc-alb-80_4fa13aa94cbe9b42" {
  name        = "eorg-ypc-alb-80"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/wp/wp-login.php"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-302"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-ypc-alb-80/4fa13aa94cbe9b42"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-ypc-alb-80/4fa13aa94cbe9b42"
  }
}

# Load Balancer: alb-etime-stage-skt-14si
resource "aws_lb" "alb-etime-stage-skt-14si_1" {
  name               = "alb-etime-stage-skt-14si"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0c48a0522ace9cd5f.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-etime-stage-skt-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-etime-stage-skt-14si/d4adce6270f2afaa"
    "Cost Center" = "etime"
    Environment = "stage"
  }
}

# Load Balancer: alb-etime-test-14si
resource "aws_lb" "alb-etime-test-14si" {
  name               = "alb-etime-test-14si"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0c48a0522ace9cd5f.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-etime-test-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-etime-test-14si/abbb1c5b91a49ccd"
    "Cost Center" = "etime"
    Environment = "test"
  }
}

# Load Balancer: alb-etime-stage-14si
resource "aws_lb" "alb-etime-stage-14si_1" {
  name               = "alb-etime-stage-14si"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0c48a0522ace9cd5f.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-etime-stage-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-etime-stage-14si/f5206669b62794d1"
    "Cost Center" = "etime"
    Environment = "stage"
  }
}

# Load Balancer: alb-etime-stage-skt-14si
resource "aws_lb" "alb-etime-stage-skt-14si" {
  name               = "alb-etime-stage-skt-14si"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0c48a0522ace9cd5f.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-etime-stage-skt-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-etime-prod-skt-14si/904f880122fda3bb"
    "Cost Center" = "etime"
    Environment = "stage"
  }
}

# Load Balancer: alb-etime-stage-14si
resource "aws_lb" "alb-etime-stage-14si" {
  name               = "alb-etime-stage-14si"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0c48a0522ace9cd5f.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-etime-stage-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-etime-prod-14si/4d8692a055667eb8"
    "Cost Center" = "etime"
    Environment = "stage"
  }
}

# Load Balancer: alb-etime-test-skt-14si
resource "aws_lb" "alb-etime-test-skt-14si" {
  name               = "alb-etime-test-skt-14si"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0c48a0522ace9cd5f.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-etime-test-skt-14si"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-etime-test-skt-14si/78142af02e211cb3"
    "Cost Center" = "etime"
    Environment = "test"
  }
}

# Load Balancer: alb-elementstaff-stage
resource "aws_lb" "alb-elementstaff-stage" {
  name               = "alb-elementstaff-stage"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0a1b0deb59dc518b8.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-elementstaff-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-elementstaff-prod/0724f4c888c4fa57"
    "Cost Center" = "elementstaff"
    Environment = "stage"
  }
}

# Load Balancer: alb-elementrec-stage
resource "aws_lb" "alb-elementrec-stage" {
  name               = "alb-elementrec-stage"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-03b68e085e90f0b6f.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-elementrec-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-elementrec-prod/44b532f1fa4618ed"
    "Cost Center" = "elementrec"
    Environment = "stage"
  }
}

# Load Balancer: alb-elementcentre-stage
resource "aws_lb" "alb-elementcentre-stage" {
  name               = "alb-elementcentre-stage"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0ccc2eb3cce8f3bf8.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-elementcentre-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-elementcentre-prod/c1146ade74093080"
    "Cost Center" = "elementcentre"
    Environment = "stage"
  }
}

# Load Balancer: alb-ghostrpc-stage
resource "aws_lb" "alb-ghostrpc-stage" {
  name               = "alb-ghostrpc-stage"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0e006c6c7bed45756.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-ghostrpc-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-ghostrpc-prod/3ecdfc854471729a"
    "Cost Center" = "ghostrpc"
    Environment = "stage"
  }
}

# Load Balancer: alb-elementsup-stage
resource "aws_lb" "alb-elementsup-stage" {
  name               = "alb-elementsup-stage"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0732fc93ae6bed8f8.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-elementsup-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-elementsup-prod/b6ece851d268c0d2"
    "Cost Center" = "elementsup"
    Environment = "stage"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-sa-fires-alb-8080/fe538c6242bd0c92
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_eorg-sa-fires-alb-8080_fe538c6242bd0c92" {
  name        = "eorg-sa-fires-alb-8080"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-sa-fires-alb-8080/fe538c6242bd0c92"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-sa-fires-alb-8080/fe538c6242bd0c92"
  }
}

# Load Balancer: alb-eodefault-sa-fires
resource "aws_lb" "alb-eodefault-sa-fires" {
  name               = "alb-eodefault-sa-fires"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-08e1289231dfb6455.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-eodefault-sa-fires"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-eodefault-sa-fires/efad51bf2adc9bf2"
    "Cost Center" = "elementOrg"
    Environment = "stage"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-sa-fires-alb-80/3ac00140f1e60037
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_eorg-sa-fires-alb-80_3ac00140f1e60037" {
  name        = "eorg-sa-fires-alb-80"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/wp/wp-login.php"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-302"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-sa-fires-alb-80/3ac00140f1e60037"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/eorg-sa-fires-alb-80/3ac00140f1e60037"
  }
}

# Load Balancer: alb-eodefault-leeton-sandbox
resource "aws_lb" "alb-eodefault-leeton-sandbox" {
  name               = "alb-eodefault-leeton-sandbox"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0e4af2ca20429ee9b.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-eodefault-leeton-sandbox"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-eodefault-leeton-sandbox/2946f6ab02af5b2d"
    "Cost Center" = "elementOrg"
    Environment = "sandbox"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/leeton-sandbox-alb-8080/215e97715d465f02
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_leeton-sandbox-alb-8080_215e97715d465f02" {
  name        = "leeton-sandbox-alb-8080"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/leeton-sandbox-alb-8080/215e97715d465f02"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/leeton-sandbox-alb-8080/215e97715d465f02"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/leeton-sandbox-alb-80/56bfc2c845eac3b2
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_leeton-sandbox-alb-80_56bfc2c845eac3b2" {
  name        = "leeton-sandbox-alb-80"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.stage.id not found in graph
  vpc_id      = "aws_vpc.stage.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/wp/wp-login.php"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 8
    matcher             = "200-302"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/leeton-sandbox-alb-80/56bfc2c845eac3b2"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/leeton-sandbox-alb-80/56bfc2c845eac3b2"
  }
}

# Load Balancer: alb-elementtime-stage-socket
resource "aws_lb" "alb-elementtime-stage-socket_1" {
  name               = "alb-elementtime-stage-socket"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0ccaad06b44bfac19.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-elementtime-stage-socket"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-elementtime-stage-socket/a7d9d488cadecb8e"
    "Cost Center" = "elementtime"
    Environment = "stage"
  }
}

# Load Balancer: alb-elementtime-stage
resource "aws_lb" "alb-elementtime-stage_1" {
  name               = "alb-elementtime-stage"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0ccaad06b44bfac19.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-elementtime-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-elementtime-prod/2b4667dd44bcb6fb"
    "Cost Center" = "elementtime"
    Environment = "stage"
  }
}

# Load Balancer: alb-elementtime-stage-socket
resource "aws_lb" "alb-elementtime-stage-socket" {
  name               = "alb-elementtime-stage-socket"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0ccaad06b44bfac19.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-elementtime-stage-socket"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-elementtime-prod-socket/8d84d5304c5a50c8"
    "Cost Center" = "elementtime"
    Environment = "stage"
  }
}

# Load Balancer: alb-elementtime-stage
resource "aws_lb" "alb-elementtime-stage" {
  name               = "alb-elementtime-stage"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0ccaad06b44bfac19.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-elementtime-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-elementtime-stage/5e6af6b82e5637c6"
    "Cost Center" = "elementtime"
    Environment = "stage"
  }
}

# Load Balancer: alb-elementtime-test-socket
resource "aws_lb" "alb-elementtime-test-socket" {
  name               = "alb-elementtime-test-socket"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0ccaad06b44bfac19.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-elementtime-test-socket"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-elementtime-test-socket/6bb7ce201e3f834d"
    "Cost Center" = "elementtime"
    Environment = "test"
  }
}

# Load Balancer: alb-elementtime-test
resource "aws_lb" "alb-elementtime-test" {
  name               = "alb-elementtime-test"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-0ccaad06b44bfac19.id",
  ]

  subnets = [
    "aws_subnet.stage-subnet-public-ap-southeast-2b.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2c.id",
    "aws_subnet.stage-subnet-public-ap-southeast-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "alb-elementtime-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/alb-elementtime-test/3fc733f538ef662b"
    "Cost Center" = "elementtime"
    Environment = "test"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementTIME-Test/32eae8cc2c482caa
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_elementTIME-Test_32eae8cc2c482caa" {
  name        = "elementTIME-Test"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 2
    interval            = 5
    matcher             = "200"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementTIME-Test/32eae8cc2c482caa"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementTIME-Test/32eae8cc2c482caa"
  }
}

# Load Balancer: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/TestALB/077cfb0024f98bfd
resource "aws_lb" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_loadbalancer_app_TestALB_077cfb0024f98bfd" {
  name               = "TestALB"
  internal           = true
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-14a91872.id",
  ]

  subnets = [
    "aws_subnet.public-2b.id",
    "aws_subnet.public-2c.id",
    "aws_subnet.public-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/TestALB/077cfb0024f98bfd"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/TestALB/077cfb0024f98bfd"
  }
}

# Load Balancer: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/elementTIME-ALB/9f79c2e3052977f1
resource "aws_lb" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_loadbalancer_app_elementTIME-ALB_9f79c2e3052977f1" {
  name               = "elementTIME-ALB"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-14a91872.id",
  ]

  subnets = [
    "aws_subnet.public-2b.id",
    "aws_subnet.public-2c.id",
    "aws_subnet.public-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/elementTIME-ALB/9f79c2e3052977f1"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/elementTIME-ALB/9f79c2e3052977f1"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementTIME-Group/b40c2f43e5ad2abc
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_elementTIME-Group_b40c2f43e5ad2abc" {
  name        = "elementTIME-Group"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 2
    interval            = 5
    matcher             = "200"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementTIME-Group/b40c2f43e5ad2abc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementTIME-Group/b40c2f43e5ad2abc"
  }
}

# Load Balancer: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/elementREC/953437bbb066b95d
resource "aws_lb" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_loadbalancer_app_elementREC_953437bbb066b95d" {
  name               = "elementREC"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-14a91872.id",
  ]

  subnets = [
    "aws_subnet.public-2b.id",
    "aws_subnet.public-2c.id",
    "aws_subnet.public-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/elementREC/953437bbb066b95d"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/elementREC/953437bbb066b95d"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementREC/dbf0c2a8c6321a46
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_elementREC_dbf0c2a8c6321a46" {
  name        = "elementREC"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/robots.txt"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 2
    interval            = 5
    matcher             = "200"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementREC/dbf0c2a8c6321a46"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementREC/dbf0c2a8c6321a46"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementstaff2/46cb8bed88db16ea
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_elementstaff2_46cb8bed88db16ea" {
  name        = "elementstaff2"
  port        = 86
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/api/health"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 10
    timeout             = 75
    interval            = 90
    matcher             = "200-299"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementstaff2/46cb8bed88db16ea"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementstaff2/46cb8bed88db16ea"
  }
}

# Load Balancer: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/elementStaffALB/f2cdbd427fdab333
resource "aws_lb" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_loadbalancer_app_elementStaffALB_f2cdbd427fdab333" {
  name               = "elementStaffALB"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-14a91872.id",
  ]

  subnets = [
    "aws_subnet.public-2b.id",
    "aws_subnet.public-2c.id",
    "aws_subnet.public-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/elementStaffALB/f2cdbd427fdab333"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/elementStaffALB/f2cdbd427fdab333"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementCentre/e308de1c9eeb6cfc
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_elementCentre_e308de1c9eeb6cfc" {
  name        = "elementCentre"
  port        = 82
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/robots.txt"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 2
    interval            = 5
    matcher             = "200"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementCentre/e308de1c9eeb6cfc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementCentre/e308de1c9eeb6cfc"
  }
}

# Load Balancer: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/elementCentreALB/611395c52f98bcab
resource "aws_lb" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_loadbalancer_app_elementCentreALB_611395c52f98bcab" {
  name               = "elementCentreALB"
  internal           = false
  load_balancer_type = "application"

  security_groups = [
    "aws_security_group.sg-14a91872.id",
  ]

  subnets = [
    "aws_subnet.public-2b.id",
    "aws_subnet.public-2c.id",
    "aws_subnet.public-2a.id",
  ]

  enable_deletion_protection = false

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/elementCentreALB/611395c52f98bcab"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:loadbalancer/app/elementCentreALB/611395c52f98bcab"
  }
}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-etime-test-cmd-14si_00083a72c6f819f5_b50b5eaee5d2a856" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-etime-test-cmd-14si/00083a72c6f819f5"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/9ae39044-cb82-4490-ad41-b5691f1db9d5"

}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-etime-test-cmd-14si_00083a72c6f819f5_7b282fa05418d019" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-etime-test-cmd-14si/00083a72c6f819f5"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-etime-stage-cmd-14si_1aa3995ded131824_de7ad75ded4e7a9b" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-etime-prod-cmd-14si/1aa3995ded131824"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/972135ee-283e-407d-a50a-f973ce0fe5d1"

}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-etime-stage-cmd-14si_1aa3995ded131824_bd6af6a71231f80e" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-etime-prod-cmd-14si/1aa3995ded131824"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-etime-stage-cmd-14si_6529dbcd4bf4fb68_f33676d3d5abe19b" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-etime-stage-cmd-14si/6529dbcd4bf4fb68"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-etime-stage-cmd-14si_6529dbcd4bf4fb68_23b618307de8e38f" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-etime-stage-cmd-14si/6529dbcd4bf4fb68"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/972135ee-283e-407d-a50a-f973ce0fe5d1"

}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementtime-stage-cmd_19ccf39c6d4f8dc0_b76b205a348e7e59" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementtime-prod-cmd/19ccf39c6d4f8dc0"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementtime-stage-cmd_19ccf39c6d4f8dc0_2cfd034a7ae820f0" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementtime-prod-cmd/19ccf39c6d4f8dc0"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/972135ee-283e-407d-a50a-f973ce0fe5d1"

}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementtime-test-cmd_437995ab15a8dc2f_ea129d5932c85cae" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementtime-test-cmd/437995ab15a8dc2f"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementtime-test-cmd_437995ab15a8dc2f_07a7c74061b195d4" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementtime-test-cmd/437995ab15a8dc2f"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/9ae39044-cb82-4490-ad41-b5691f1db9d5"

}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementtime-stage-cmd_35e2b68cadc6f899_7b806613bb8fe418" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementtime-stage-cmd/35e2b68cadc6f899"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/972135ee-283e-407d-a50a-f973ce0fe5d1"

}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementtime-stage-cmd_35e2b68cadc6f899_37078939b31de050" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementtime-stage-cmd/35e2b68cadc6f899"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-sa-redirect_33bd6bf748e0a107_f84eab400305e60c" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-sa-redirect/33bd6bf748e0a107"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/08400034-20b8-41d3-b8d0-31cfd74aee87"

}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-sa-redirect_33bd6bf748e0a107_e5125a4bdb2bb2c0" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-sa-redirect/33bd6bf748e0a107"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-test-griffith_1cf05509a320655a_e34c7a58063d9002" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-test-griffith/1cf05509a320655a"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/085ab2fd-35c0-4bb6-a9c1-ab91c27459e9"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/eorg-test-griffith-alb-80/e36e225c11fff72a"
  }
}

# LB Listener: HTTP:8080
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-test-griffith_1cf05509a320655a_9e7c4fc19fd0087f" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-test-griffith/1cf05509a320655a"
  port              = 8080
  protocol          = "HTTP"


}

# LB Listener: HTTPS:8443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-test-griffith_1cf05509a320655a_9337709b4e4c5d65" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-test-griffith/1cf05509a320655a"
  port              = 8443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/085ab2fd-35c0-4bb6-a9c1-ab91c27459e9"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/eorg-test-griffith-alb-8080/f3edca9e0699eb33"
  }
}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-test-griffith_1cf05509a320655a_668c24281e828718" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-test-griffith/1cf05509a320655a"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTP:8080
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-griffith_fc30b8e8733d27d2_e7952fec91964516" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-griffith/fc30b8e8733d27d2"
  port              = 8080
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-griffith_fc30b8e8733d27d2_de15d8c88b9b3b3e" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-griffith/fc30b8e8733d27d2"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/bbe69260-8648-4660-9994-65ad89fce45c"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/eorg-griffith-alb-80/2913d876dea23cf7"
  }
}

# LB Listener: HTTPS:8443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-griffith_fc30b8e8733d27d2_7d23829b9e8c8333" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-griffith/fc30b8e8733d27d2"
  port              = 8443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/bbe69260-8648-4660-9994-65ad89fce45c"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/eorg-griffith-alb-8080/7be4e650bca5f174"
  }
}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-griffith_fc30b8e8733d27d2_172f8ced43b46bc1" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-griffith/fc30b8e8733d27d2"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eo-test-ngsc-trellis_909a70fd9f6ed999_b1d56483174b64c7" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eo-test-ngsc-trellis/909a70fd9f6ed999"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTP:8080
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eo-test-ngsc-trellis_909a70fd9f6ed999_a186f8f0b77d6b26" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eo-test-ngsc-trellis/909a70fd9f6ed999"
  port              = 8080
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eo-test-ngsc-trellis_909a70fd9f6ed999_62d8a9d48981a349" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eo-test-ngsc-trellis/909a70fd9f6ed999"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/c569b3c2-9b43-487e-bf5f-1f59bd090b2e"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/eo-test-ngsc-trellis-alb-80/45cdec0b984c6282"
  }
}

# LB Listener: HTTPS:8443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eo-test-ngsc-trellis_909a70fd9f6ed999_53acdef9e781f83a" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eo-test-ngsc-trellis/909a70fd9f6ed999"
  port              = 8443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/c569b3c2-9b43-487e-bf5f-1f59bd090b2e"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/eo-test-ngsc-trellis-alb-8080/98e9ed041d55efbf"
  }
}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-leeton-c5_08a99dddda4bcfc7_c692d583cee6d18c" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-leeton-c5/08a99dddda4bcfc7"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTP:8080
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-leeton-c5_08a99dddda4bcfc7_ab1eb0cc6d1b199a" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-leeton-c5/08a99dddda4bcfc7"
  port              = 8080
  protocol          = "HTTP"


}

# LB Listener: HTTPS:8443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-leeton-c5_08a99dddda4bcfc7_6e2a7569a7da8d08" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-leeton-c5/08a99dddda4bcfc7"
  port              = 8443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/bc26e122-8788-44f9-a227-19f250028ebc"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/eodefault-leeton-alb-8080-c5/1b2c3c777cb8004a"
  }
}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-leeton-c5_08a99dddda4bcfc7_3e7dc229e48bd045" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-leeton-c5/08a99dddda4bcfc7"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/bc26e122-8788-44f9-a227-19f250028ebc"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/eodefault-leeton-alb-80-c5/3db27c896e5ff211"
  }
}

# LB Listener: HTTP:8080
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-ngsc_2ff93196a330a9b1_3a56759846103966" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-ngsc/2ff93196a330a9b1"
  port              = 8080
  protocol          = "HTTP"


}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-ngsc_2ff93196a330a9b1_310a7ec056c164bc" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-ngsc/2ff93196a330a9b1"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-ngsc_2ff93196a330a9b1_210f2bcb8989ae39" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-ngsc/2ff93196a330a9b1"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/4eedbe43-3453-4d34-918d-9a2fad9160c1"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/eorg-ngsc-alb-80/9addc31e3bac25da"
  }
}

# LB Listener: HTTPS:8443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-ngsc_2ff93196a330a9b1_1f3ad78289a97c61" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-ngsc/2ff93196a330a9b1"
  port              = 8443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/4eedbe43-3453-4d34-918d-9a2fad9160c1"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/eorg-ngsc-alb-8080/c0f3b582d52ce58b"
  }
}

# LB Listener: HTTPS:8443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-test-ngsc_af1fb68ffaa39a98_c3a4ff159381b6d5" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-test-ngsc/af1fb68ffaa39a98"
  port              = 8443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/e8a8a95e-20f7-4f89-b8f5-0bb14fd0afb4"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/eorg-test-ngsc-alb-8080/36237c7ab58369e4"
  }
}

# LB Listener: HTTP:8080
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-test-ngsc_af1fb68ffaa39a98_a5fcedc35df76dca" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-test-ngsc/af1fb68ffaa39a98"
  port              = 8080
  protocol          = "HTTP"


}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-test-ngsc_af1fb68ffaa39a98_286ad2519d033fb8" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-test-ngsc/af1fb68ffaa39a98"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-test-ngsc_af1fb68ffaa39a98_2293002912a8eb96" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-test-ngsc/af1fb68ffaa39a98"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/e8a8a95e-20f7-4f89-b8f5-0bb14fd0afb4"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/eorg-test-ngsc-alb-80/d6ec13213e3070ce"
  }
}

# LB Listener: HTTPS:8443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-test-ypc_00d275316fcab139_9b5a8fc86e074a3b" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-test-ypc/00d275316fcab139"
  port              = 8443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/e073fe25-36b9-4806-8f96-a50e78c76076"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/eorg-test-ypc-alb-8080/2e2a9c70138d891e"
  }
}

# LB Listener: HTTP:8080
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-test-ypc_00d275316fcab139_634a3e9d9b5e3403" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-test-ypc/00d275316fcab139"
  port              = 8080
  protocol          = "HTTP"


}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-test-ypc_00d275316fcab139_2ea5fa7ecfef861b" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-test-ypc/00d275316fcab139"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-test-ypc_00d275316fcab139_0f34cf97b51d83a4" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-test-ypc/00d275316fcab139"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/e073fe25-36b9-4806-8f96-a50e78c76076"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/eorg-test-ypc-alb-80/7c039f5b27a7fc54"
  }
}

# LB Listener: HTTPS:8443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-ypc_6fad7ac3a422b536_f805316f509f8b6b" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-ypc/6fad7ac3a422b536"
  port              = 8443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/e050cc51-8769-439a-ac00-64f6db0e9631"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/eorg-ypc-alb-8080/a5348577a6f7ac27"
  }
}

# LB Listener: HTTP:8080
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-ypc_6fad7ac3a422b536_f7fb24ca789dc682" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-ypc/6fad7ac3a422b536"
  port              = 8080
  protocol          = "HTTP"


}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-ypc_6fad7ac3a422b536_de4fa86201936ba9" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-ypc/6fad7ac3a422b536"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-ypc_6fad7ac3a422b536_85ca6c0a5fb3e392" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-ypc/6fad7ac3a422b536"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/e050cc51-8769-439a-ac00-64f6db0e9631"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/eorg-ypc-alb-80/4fa13aa94cbe9b42"
  }
}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-etime-stage-skt-14si_d4adce6270f2afaa_4ad6ca1c7bbe32b9" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-etime-stage-skt-14si/d4adce6270f2afaa"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/972135ee-283e-407d-a50a-f973ce0fe5d1"

}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-etime-stage-skt-14si_d4adce6270f2afaa_1a97dd5daf3c31f1" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-etime-stage-skt-14si/d4adce6270f2afaa"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-etime-test-14si_abbb1c5b91a49ccd_f9f9ff64adecc525" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-etime-test-14si/abbb1c5b91a49ccd"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-etime-test-14si_abbb1c5b91a49ccd_e06d2afd2228469b" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-etime-test-14si/abbb1c5b91a49ccd"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/9ae39044-cb82-4490-ad41-b5691f1db9d5"

}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-etime-stage-14si_f5206669b62794d1_e9514a8b55abbd34" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-etime-stage-14si/f5206669b62794d1"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-etime-stage-14si_f5206669b62794d1_c725315f158f69c9" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-etime-stage-14si/f5206669b62794d1"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/972135ee-283e-407d-a50a-f973ce0fe5d1"

}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-etime-stage-skt-14si_904f880122fda3bb_cc46fbe2e2f990da" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-etime-prod-skt-14si/904f880122fda3bb"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-etime-stage-skt-14si_904f880122fda3bb_793b29458765af26" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-etime-prod-skt-14si/904f880122fda3bb"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/972135ee-283e-407d-a50a-f973ce0fe5d1"

}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-etime-stage-14si_4d8692a055667eb8_714e550eb421e92a" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-etime-prod-14si/4d8692a055667eb8"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/972135ee-283e-407d-a50a-f973ce0fe5d1"

}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-etime-stage-14si_4d8692a055667eb8_34caa5ff55bef10f" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-etime-prod-14si/4d8692a055667eb8"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-etime-test-skt-14si_78142af02e211cb3_864bbd83f555b3bb" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-etime-test-skt-14si/78142af02e211cb3"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-etime-test-skt-14si_78142af02e211cb3_1eee6817b0955fc9" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-etime-test-skt-14si/78142af02e211cb3"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/9ae39044-cb82-4490-ad41-b5691f1db9d5"

}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementstaff-prod_0724f4c888c4fa57_f0e5dd291e8aab70" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementstaff-prod/0724f4c888c4fa57"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/41481162-0970-4785-9ebc-345177f394f8"

}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementstaff-prod_0724f4c888c4fa57_c38241bcf8f9b82d" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementstaff-prod/0724f4c888c4fa57"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementrec-prod_44b532f1fa4618ed_dd2ebd7a1815af77" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementrec-prod/44b532f1fa4618ed"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/354e3896-1c15-4916-bfa9-2dac801fbd79"

}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementrec-prod_44b532f1fa4618ed_9353b182508d3ea7" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementrec-prod/44b532f1fa4618ed"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementcentre-prod_c1146ade74093080_e4fedf4f685417bf" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementcentre-prod/c1146ade74093080"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/582af2e2-a610-41c9-ae42-822ce76d808e"

}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementcentre-prod_c1146ade74093080_dc81c7e3615d01c3" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementcentre-prod/c1146ade74093080"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-ghostrpc-prod_3ecdfc854471729a_fac3367a10554a85" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-ghostrpc-prod/3ecdfc854471729a"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-ghostrpc-prod_3ecdfc854471729a_0bc6aa7193103e87" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-ghostrpc-prod/3ecdfc854471729a"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/972135ee-283e-407d-a50a-f973ce0fe5d1"

}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementsup-prod_b6ece851d268c0d2_a7b9867b0c5edac2" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementsup-prod/b6ece851d268c0d2"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementsup-prod_b6ece851d268c0d2_1387736ba98f34e3" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementsup-prod/b6ece851d268c0d2"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/1cd0ca28-b1ce-4edc-9241-f88d598b5cc6"

}

# LB Listener: HTTPS:8443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-sa-fires_efad51bf2adc9bf2_f6e26ca8c07204f4" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-sa-fires/efad51bf2adc9bf2"
  port              = 8443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/ff40026c-9e25-4cb5-a2ae-f81d36fdd25a"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/eorg-sa-fires-alb-8080/fe538c6242bd0c92"
  }
}

# LB Listener: HTTP:8080
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-sa-fires_efad51bf2adc9bf2_c307928339c6345d" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-sa-fires/efad51bf2adc9bf2"
  port              = 8080
  protocol          = "HTTP"


}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-sa-fires_efad51bf2adc9bf2_8b5118a127645e02" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-sa-fires/efad51bf2adc9bf2"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-sa-fires_efad51bf2adc9bf2_7cc936acfdb82401" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-sa-fires/efad51bf2adc9bf2"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/ff40026c-9e25-4cb5-a2ae-f81d36fdd25a"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/eorg-sa-fires-alb-80/3ac00140f1e60037"
  }
}

# LB Listener: HTTP:8080
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-leeton-sandbox_2946f6ab02af5b2d_ac975b3a5bb48c67" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-leeton-sandbox/2946f6ab02af5b2d"
  port              = 8080
  protocol          = "HTTP"


}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-leeton-sandbox_2946f6ab02af5b2d_6ff7b2f2df14592f" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-leeton-sandbox/2946f6ab02af5b2d"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:8443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-leeton-sandbox_2946f6ab02af5b2d_606355bec09a7082" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-leeton-sandbox/2946f6ab02af5b2d"
  port              = 8443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/db87bd3d-1acb-4980-9a88-17f1149005f6"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/leeton-sandbox-alb-8080/215e97715d465f02"
  }
}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-eodefault-leeton-sandbox_2946f6ab02af5b2d_4b2c90618574abcb" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-eodefault-leeton-sandbox/2946f6ab02af5b2d"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/db87bd3d-1acb-4980-9a88-17f1149005f6"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/leeton-sandbox-alb-80/56bfc2c845eac3b2"
  }
}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementtime-stage-socket_a7d9d488cadecb8e_fc127a8b9e65f58f" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementtime-stage-socket/a7d9d488cadecb8e"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/972135ee-283e-407d-a50a-f973ce0fe5d1"

}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementtime-stage-socket_a7d9d488cadecb8e_1d2c425870eecd90" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementtime-stage-socket/a7d9d488cadecb8e"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementtime-prod_2b4667dd44bcb6fb_62962795f2997ddd" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementtime-prod/2b4667dd44bcb6fb"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/972135ee-283e-407d-a50a-f973ce0fe5d1"

}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementtime-prod_2b4667dd44bcb6fb_5ab105ca72c06aa8" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementtime-prod/2b4667dd44bcb6fb"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementtime-stage-socket_8d84d5304c5a50c8_c10ebf994be70b85" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementtime-prod-socket/8d84d5304c5a50c8"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/972135ee-283e-407d-a50a-f973ce0fe5d1"

}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementtime-stage-socket_8d84d5304c5a50c8_9fb6ee3febd738a1" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementtime-prod-socket/8d84d5304c5a50c8"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementtime-stage_5e6af6b82e5637c6_cc9ac97a2c5b8489" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementtime-stage/5e6af6b82e5637c6"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementtime-stage_5e6af6b82e5637c6_ba221476ec9058b7" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementtime-stage/5e6af6b82e5637c6"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/972135ee-283e-407d-a50a-f973ce0fe5d1"

}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementtime-test-socket_6bb7ce201e3f834d_b770ced834f22ab7" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementtime-test-socket/6bb7ce201e3f834d"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/9ae39044-cb82-4490-ad41-b5691f1db9d5"

}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementtime-test-socket_6bb7ce201e3f834d_3cff692eb719ebae" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementtime-test-socket/6bb7ce201e3f834d"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementtime-test_3fc733f538ef662b_f654189182a3fa97" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementtime-test/3fc733f538ef662b"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_alb-elementtime-test_3fc733f538ef662b_665d3189e17f0e3d" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/alb-elementtime-test/3fc733f538ef662b"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-Res-2021-06"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/9ae39044-cb82-4490-ad41-b5691f1db9d5"

}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_TestALB_077cfb0024f98bfd_06e60bf601a4cd14" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/TestALB/077cfb0024f98bfd"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/9ae39044-cb82-4490-ad41-b5691f1db9d5"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/elementTIME-Test/32eae8cc2c482caa"
  }
}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_TestALB_077cfb0024f98bfd_00e844053d9855a5" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/TestALB/077cfb0024f98bfd"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_elementTIME-ALB_9f79c2e3052977f1_8e5cb5e6746435b3" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/elementTIME-ALB/9f79c2e3052977f1"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_elementTIME-ALB_9f79c2e3052977f1_7191bbe3ba9b1f78" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/elementTIME-ALB/9f79c2e3052977f1"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/972135ee-283e-407d-a50a-f973ce0fe5d1"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/elementTIME-Group/b40c2f43e5ad2abc"
  }
}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_elementREC_953437bbb066b95d_efa9316de4239a29" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/elementREC/953437bbb066b95d"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_elementREC_953437bbb066b95d_59c235fc275dfab5" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/elementREC/953437bbb066b95d"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/354e3896-1c15-4916-bfa9-2dac801fbd79"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/elementREC/dbf0c2a8c6321a46"
  }
}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_elementStaffALB_f2cdbd427fdab333_e1b3254324290330" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/elementStaffALB/f2cdbd427fdab333"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/f8968bd5-bd8c-4bb7-a189-1c33b456f858"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/elementstaff2/46cb8bed88db16ea"
  }
}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_elementStaffALB_f2cdbd427fdab333_5af89f25855291c1" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/elementStaffALB/f2cdbd427fdab333"
  port              = 80
  protocol          = "HTTP"


}

# LB Listener: HTTPS:443
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_elementCentreALB_611395c52f98bcab_f0afbeb35221ce95" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/elementCentreALB/611395c52f98bcab"
  port              = 443
  protocol          = "HTTPS"

  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = "arn:aws:acm:ap-southeast-2:${var.aws_account_id}:certificate/582af2e2-a610-41c9-ae42-822ce76d808e"

  default_action {
    type             = "forward"
    target_group_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:targetgroup/elementCentre/e308de1c9eeb6cfc"
  }
}

# LB Listener: HTTP:80
resource "aws_lb_listener" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_listener_app_elementCentreALB_611395c52f98bcab_4d0b49556e47fdc8" {
  load_balancer_arn = "arn:aws:elasticloadbalancing:ap-southeast-2:${var.aws_account_id}:loadbalancer/app/elementCentreALB/611395c52f98bcab"
  port              = 80
  protocol          = "HTTP"


}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/redash/3a6be71e7b12754e
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_redash_3a6be71e7b12754e" {
  name        = "redash"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 2
    interval            = 5
    matcher             = "200"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/redash/3a6be71e7b12754e"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/redash/3a6be71e7b12754e"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementTIME-sandbox/38de0506d4a0a94a
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_elementTIME-sandbox_38de0506d4a0a94a" {
  name        = "elementTIME-sandbox"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 2
    interval            = 5
    matcher             = "200"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementTIME-sandbox/38de0506d4a0a94a"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementTIME-sandbox/38de0506d4a0a94a"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementTIME-jasper/ac19fb83d0f18e92
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_elementTIME-jasper_ac19fb83d0f18e92" {
  name        = "elementTIME-jasper"
  port        = 80
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/validate"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 2
    interval            = 5
    matcher             = "200"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementTIME-jasper/ac19fb83d0f18e92"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementTIME-jasper/ac19fb83d0f18e92"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementStaff/93b2920c550367f3
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_elementStaff_93b2920c550367f3" {
  name        = "elementStaff"
  port        = 81
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/robots.txt"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 2
    interval            = 5
    matcher             = "200"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementStaff/93b2920c550367f3"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementStaff/93b2920c550367f3"
  }
}

# Target Group: arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementSUP/20407bf7a79e8391
resource "aws_lb_target_group" "arn_aws_elasticloadbalancing_ap-southeast-2_542859091916_targetgroup_elementSUP_20407bf7a79e8391" {
  name        = "elementSUP"
  port        = 87
  protocol    = "HTTP"
  # WARNING: VPC aws_vpc.public.id not found in graph
  vpc_id      = "aws_vpc.public.id"
  target_type = "instance"

  health_check {
    enabled             = true
    path                = "/robots.txt"
    port                = "traffic-port"
    protocol            = "HTTP"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 2
    interval            = 5
    matcher             = "200"
  }

  tags = {
    Name        = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementSUP/20407bf7a79e8391"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:elasticloadbalancing:ap-southeast-2:542859091916:targetgroup/elementSUP/20407bf7a79e8391"
  }
}