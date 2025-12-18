# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:yorke-inranet-buget-adjust-approval
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_yorke-inranet-buget-adjust-approval" {
  name = "yorke-inranet-buget-adjust-approval"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:yorke-inranet-buget-adjust-approval"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:yorke-inranet-buget-adjust-approval"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:yorke-ghostrpc-queue-server-test
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_yorke-ghostrpc-queue-server-test" {
  name = "yorke-ghostrpc-queue-server-test"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 1209600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:yorke-ghostrpc-queue-server-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:yorke-ghostrpc-queue-server-test"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:yorke-ghostrpc-queue-server
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_yorke-ghostrpc-queue-server" {
  name = "yorke-ghostrpc-queue-server"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:yorke-ghostrpc-queue-server"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:yorke-ghostrpc-queue-server"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:wollondilly-ghostrpc-queue-server-test
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_wollondilly-ghostrpc-queue-server-test" {
  name = "wollondilly-ghostrpc-queue-server-test"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:wollondilly-ghostrpc-queue-server-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:wollondilly-ghostrpc-queue-server-test"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:wollondilly-ghostrpc-queue-server
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_wollondilly-ghostrpc-queue-server" {
  name = "wollondilly-ghostrpc-queue-server"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:wollondilly-ghostrpc-queue-server"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:wollondilly-ghostrpc-queue-server"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:shrcc-ghostrpc-queue-server-test
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_shrcc-ghostrpc-queue-server-test" {
  name = "shrcc-ghostrpc-queue-server-test"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:shrcc-ghostrpc-queue-server-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:shrcc-ghostrpc-queue-server-test"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:shrcc-ghostrpc-queue-server
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_shrcc-ghostrpc-queue-server" {
  name = "shrcc-ghostrpc-queue-server"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:shrcc-ghostrpc-queue-server"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:shrcc-ghostrpc-queue-server"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:rmagent-app-yorke
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_rmagent-app-yorke" {
  name = "rmagent-app-yorke"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 1209600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 20



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:rmagent-app-yorke"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:rmagent-app-yorke"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:rmagent-app-mtbarker
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_rmagent-app-mtbarker" {
  name = "rmagent-app-mtbarker"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:rmagent-app-mtbarker"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:rmagent-app-mtbarker"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:portaugusta-ghostrpc-queue-server-test
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_portaugusta-ghostrpc-queue-server-test" {
  name = "portaugusta-ghostrpc-queue-server-test"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:portaugusta-ghostrpc-queue-server-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:portaugusta-ghostrpc-queue-server-test"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:portaugusta-ghostrpc-queue-server-live
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_portaugusta-ghostrpc-queue-server-live" {
  name = "portaugusta-ghostrpc-queue-server-live"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:portaugusta-ghostrpc-queue-server-live"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:portaugusta-ghostrpc-queue-server-live"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:nirc-ghostrpc-queue-server-test
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_nirc-ghostrpc-queue-server-test" {
  name = "nirc-ghostrpc-queue-server-test"


  visibility_timeout_seconds  = 180
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:nirc-ghostrpc-queue-server-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:nirc-ghostrpc-queue-server-test"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:nirc-ghostrpc-queue-server
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_nirc-ghostrpc-queue-server" {
  name = "nirc-ghostrpc-queue-server"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:nirc-ghostrpc-queue-server"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:nirc-ghostrpc-queue-server"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:ngsc-prem-ghostrpc-queue-server-test
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_ngsc-prem-ghostrpc-queue-server-test" {
  name = "ngsc-prem-ghostrpc-queue-server-test"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:ngsc-prem-ghostrpc-queue-server-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:ngsc-prem-ghostrpc-queue-server-test"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:ngsc-prem-ghostrpc-queue-server
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_ngsc-prem-ghostrpc-queue-server" {
  name = "ngsc-prem-ghostrpc-queue-server"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:ngsc-prem-ghostrpc-queue-server"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:ngsc-prem-ghostrpc-queue-server"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:ngsc-ghostrpc-queue-server
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_ngsc-ghostrpc-queue-server" {
  name = "ngsc-ghostrpc-queue-server"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 1209600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:ngsc-ghostrpc-queue-server"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:ngsc-ghostrpc-queue-server"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:nambucca-ghostrpc-queue-server-test
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_nambucca-ghostrpc-queue-server-test" {
  name = "nambucca-ghostrpc-queue-server-test"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:nambucca-ghostrpc-queue-server-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:nambucca-ghostrpc-queue-server-test"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:nambucca-ghostrpc-queue-server
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_nambucca-ghostrpc-queue-server" {
  name = "nambucca-ghostrpc-queue-server"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:nambucca-ghostrpc-queue-server"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:nambucca-ghostrpc-queue-server"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:mtbarker-ghostrpc-queue-server
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_mtbarker-ghostrpc-queue-server" {
  name = "mtbarker-ghostrpc-queue-server"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 864000
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 20



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:mtbarker-ghostrpc-queue-server"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:mtbarker-ghostrpc-queue-server"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:leeton-ghostrpc-queue-server-test
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_leeton-ghostrpc-queue-server-test" {
  name = "leeton-ghostrpc-queue-server-test"


  visibility_timeout_seconds  = 180
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:leeton-ghostrpc-queue-server-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:leeton-ghostrpc-queue-server-test"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:leeton-ghostrpc-queue-server
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_leeton-ghostrpc-queue-server" {
  name = "leeton-ghostrpc-queue-server"


  visibility_timeout_seconds  = 180
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:leeton-ghostrpc-queue-server"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:leeton-ghostrpc-queue-server"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:gwydir-ghostrpc-queue-server-test
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_gwydir-ghostrpc-queue-server-test" {
  name = "gwydir-ghostrpc-queue-server-test"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:gwydir-ghostrpc-queue-server-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:gwydir-ghostrpc-queue-server-test"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:gwydir-ghostrpc-queue-server
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_gwydir-ghostrpc-queue-server" {
  name = "gwydir-ghostrpc-queue-server"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:gwydir-ghostrpc-queue-server"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:gwydir-ghostrpc-queue-server"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:gwcc-ghostrpc-queue-server-test
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_gwcc-ghostrpc-queue-server-test" {
  name = "gwcc-ghostrpc-queue-server-test"


  visibility_timeout_seconds  = 180
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:gwcc-ghostrpc-queue-server-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:gwcc-ghostrpc-queue-server-test"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:gwcc-ghostrpc-queue-server-db-test
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_gwcc-ghostrpc-queue-server-db-test" {
  name = "gwcc-ghostrpc-queue-server-db-test"


  visibility_timeout_seconds  = 300
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:gwcc-ghostrpc-queue-server-db-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:gwcc-ghostrpc-queue-server-db-test"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:gwcc-ghostrpc-queue-server-db
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_gwcc-ghostrpc-queue-server-db" {
  name = "gwcc-ghostrpc-queue-server-db"


  visibility_timeout_seconds  = 300
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:gwcc-ghostrpc-queue-server-db"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:gwcc-ghostrpc-queue-server-db"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:gwcc-ghostrpc-queue-server
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_gwcc-ghostrpc-queue-server" {
  name = "gwcc-ghostrpc-queue-server"


  visibility_timeout_seconds  = 180
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:gwcc-ghostrpc-queue-server"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:gwcc-ghostrpc-queue-server"
  }
}

# SQS Queue: griffith-ghostrpc-queue-server-test
resource "aws_sqs_queue" "griffith-ghostrpc-queue-server-test" {
  name = "griffith-ghostrpc-queue-server-test"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "griffith-ghostrpc-queue-server-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:griffith-ghostrpc-queue-server-test"
    "Cost Center" = "eOrg - Griffith"
    Project = "eOrg - Griffith"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: griffith-ghostrpc-queue-server
resource "aws_sqs_queue" "griffith-ghostrpc-queue-server" {
  name = "griffith-ghostrpc-queue-server"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "griffith-ghostrpc-queue-server"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:griffith-ghostrpc-queue-server"
    "Cost Center" = "eOrg - Griffith"
    Project = "eOrg - Griffith"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-yorke-queue-server-test
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_ghostrpc-yorke-queue-server-test" {
  name = "ghostrpc-yorke-queue-server-test"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-yorke-queue-server-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-yorke-queue-server-test"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-yorke-queue-server
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_ghostrpc-yorke-queue-server" {
  name = "ghostrpc-yorke-queue-server"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-yorke-queue-server"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-yorke-queue-server"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-warwyn-queue-server-test
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_ghostrpc-warwyn-queue-server-test" {
  name = "ghostrpc-warwyn-queue-server-test"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-warwyn-queue-server-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-warwyn-queue-server-test"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-warwyn-queue-server
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_ghostrpc-warwyn-queue-server" {
  name = "ghostrpc-warwyn-queue-server"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-warwyn-queue-server"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-warwyn-queue-server"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-local-leo
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_ghostrpc-local-leo" {
  name = "ghostrpc-local-leo"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-local-leo"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-local-leo"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-local-fernando
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_ghostrpc-local-fernando" {
  name = "ghostrpc-local-fernando"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-local-fernando"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-local-fernando"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-gawler-queue-server-test
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_ghostrpc-gawler-queue-server-test" {
  name = "ghostrpc-gawler-queue-server-test"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-gawler-queue-server-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-gawler-queue-server-test"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-gawler-queue-server
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_ghostrpc-gawler-queue-server" {
  name = "ghostrpc-gawler-queue-server"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-gawler-queue-server"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:ghostrpc-gawler-queue-server"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:gawler-ghostrpc-queue-server
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_gawler-ghostrpc-queue-server" {
  name = "gawler-ghostrpc-queue-server"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:gawler-ghostrpc-queue-server"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:gawler-ghostrpc-queue-server"
  }
}

# SQS Queue: etime-face-auth-stage-lambda-dlq
resource "aws_sqs_queue" "etime-face-auth-stage-lambda-dlq" {
  name = "etime-face-auth-stage-lambda-dlq"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 1209600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0

  sqs_managed_sse_enabled = true


  tags = {
    Name        = "etime-face-auth-stage-lambda-dlq"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-face-auth-prod-lambda-dlq"
    "Cost Center" = "elementTIME"
    Project = "etime-face-auth"
    ManagedBy = "terraform"
    Terraform = "true"
    Environment = "stage"
    Service = "face-auth"
    Component = "lambda"
  }
}

# SQS Queue: etime-14si-test-workflows
resource "aws_sqs_queue" "etime-14si-test-workflows" {
  name = "etime-14si-test-workflows"


  visibility_timeout_seconds  = 180
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-test-workflows"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-test-workflows"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-test-user
resource "aws_sqs_queue" "etime-14si-test-user" {
  name = "etime-14si-test-user"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-test-user"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-test-user"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-test-upgrades
resource "aws_sqs_queue" "etime-14si-test-upgrades" {
  name = "etime-14si-test-upgrades"


  visibility_timeout_seconds  = 36000
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-test-upgrades"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-test-upgrades"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-test-timesheets
resource "aws_sqs_queue" "etime-14si-test-timesheets" {
  name = "etime-14si-test-timesheets"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-test-timesheets"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-test-timesheets"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-test-tenant
resource "aws_sqs_queue" "etime-14si-test-tenant" {
  name = "etime-14si-test-tenant"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-test-tenant"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-test-tenant"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-test-shifts
resource "aws_sqs_queue" "etime-14si-test-shifts" {
  name = "etime-14si-test-shifts"


  visibility_timeout_seconds  = 1200
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-test-shifts"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-test-shifts"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-test-settings
resource "aws_sqs_queue" "etime-14si-test-settings" {
  name = "etime-14si-test-settings"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-test-settings"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-test-settings"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-test-reports
resource "aws_sqs_queue" "etime-14si-test-reports" {
  name = "etime-14si-test-reports"


  visibility_timeout_seconds  = 1800
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-test-reports"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-test-reports"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-test-penalties
resource "aws_sqs_queue" "etime-14si-test-penalties" {
  name = "etime-14si-test-penalties"


  visibility_timeout_seconds  = 300
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-test-penalties"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-test-penalties"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-test-payroll-authority-response
resource "aws_sqs_queue" "etime-14si-test-payroll-authority-response" {
  name = "etime-14si-test-payroll-authority-response"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-test-payroll-authority-response"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-test-payroll-authority-response"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-test-notifications-triggers
resource "aws_sqs_queue" "etime-14si-test-notifications-triggers" {
  name = "etime-14si-test-notifications-triggers"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-test-notifications-triggers"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-test-notifications-triggers"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-test-notifications
resource "aws_sqs_queue" "etime-14si-test-notifications" {
  name = "etime-14si-test-notifications"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-test-notifications"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-test-notifications"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-test-leave-balances
resource "aws_sqs_queue" "etime-14si-test-leave-balances" {
  name = "etime-14si-test-leave-balances"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-test-leave-balances"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-test-leave-balances"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-test-integrations
resource "aws_sqs_queue" "etime-14si-test-integrations" {
  name = "etime-14si-test-integrations"


  visibility_timeout_seconds  = 300
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-test-integrations"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-test-integrations"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-test-generic-authority-response
resource "aws_sqs_queue" "etime-14si-test-generic-authority-response" {
  name = "etime-14si-test-generic-authority-response"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-test-generic-authority-response"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-test-generic-authority-response"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-test-general
resource "aws_sqs_queue" "etime-14si-test-general" {
  name = "etime-14si-test-general"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-test-general"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-test-general"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-test-excess-time
resource "aws_sqs_queue" "etime-14si-test-excess-time" {
  name = "etime-14si-test-excess-time"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-test-excess-time"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-test-excess-time"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-test-edrms-responses
resource "aws_sqs_queue" "etime-14si-test-edrms-responses" {
  name = "etime-14si-test-edrms-responses"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-test-edrms-responses"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-test-edrms-responses"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-test-browser-notifications
resource "aws_sqs_queue" "etime-14si-test-browser-notifications" {
  name = "etime-14si-test-browser-notifications"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-test-browser-notifications"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-test-browser-notifications"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-test-broadcasts
resource "aws_sqs_queue" "etime-14si-test-broadcasts" {
  name = "etime-14si-test-broadcasts"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-test-broadcasts"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-test-broadcasts"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-workflows
resource "aws_sqs_queue" "etime-14si-stage-workflows_orkflows" {
  name = "etime-14si-stage-workflows"


  visibility_timeout_seconds  = 180
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-workflows"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-stage-workflows"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-user
resource "aws_sqs_queue" "etime-14si-stage-user_age_user" {
  name = "etime-14si-stage-user"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-user"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-stage-user"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-upgrades
resource "aws_sqs_queue" "etime-14si-stage-upgrades_upgrades" {
  name = "etime-14si-stage-upgrades"


  visibility_timeout_seconds  = 36000
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-upgrades"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-stage-upgrades"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-timesheets
resource "aws_sqs_queue" "etime-14si-stage-timesheets_mesheets" {
  name = "etime-14si-stage-timesheets"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-timesheets"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-stage-timesheets"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-tenant
resource "aws_sqs_queue" "etime-14si-stage-tenant_e_tenant" {
  name = "etime-14si-stage-tenant"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-tenant"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-stage-tenant"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-shifts
resource "aws_sqs_queue" "etime-14si-stage-shifts_e_shifts" {
  name = "etime-14si-stage-shifts"


  visibility_timeout_seconds  = 1200
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-shifts"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-stage-shifts"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-settings
resource "aws_sqs_queue" "etime-14si-stage-settings_settings" {
  name = "etime-14si-stage-settings"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-settings"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-stage-settings"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-reports
resource "aws_sqs_queue" "etime-14si-stage-reports__reports" {
  name = "etime-14si-stage-reports"


  visibility_timeout_seconds  = 1800
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-reports"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-stage-reports"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-penalties
resource "aws_sqs_queue" "etime-14si-stage-penalties_enalties" {
  name = "etime-14si-stage-penalties"


  visibility_timeout_seconds  = 300
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-penalties"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-stage-penalties"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-payroll-authority-response
resource "aws_sqs_queue" "etime-14si-stage-payroll-authority-response_response" {
  name = "etime-14si-stage-payroll-authority-response"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-payroll-authority-response"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-stage-payroll-authority-response"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-notifications-triggers
resource "aws_sqs_queue" "etime-14si-stage-notifications-triggers_triggers" {
  name = "etime-14si-stage-notifications-triggers"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-notifications-triggers"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-stage-notifications-triggers"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-notifications
resource "aws_sqs_queue" "etime-14si-stage-notifications_ications" {
  name = "etime-14si-stage-notifications"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-notifications"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-stage-notifications"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-leave-balances
resource "aws_sqs_queue" "etime-14si-stage-leave-balances_balances" {
  name = "etime-14si-stage-leave-balances"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-leave-balances"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-stage-leave-balances"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-integrations
resource "aws_sqs_queue" "etime-14si-stage-integrations_grations" {
  name = "etime-14si-stage-integrations"


  visibility_timeout_seconds  = 300
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-integrations"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-stage-integrations"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-generic-authority-response
resource "aws_sqs_queue" "etime-14si-stage-generic-authority-response_response" {
  name = "etime-14si-stage-generic-authority-response"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-generic-authority-response"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-stage-generic-authority-response"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-general
resource "aws_sqs_queue" "etime-14si-stage-general__general" {
  name = "etime-14si-stage-general"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-general"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-stage-general"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-excess-time
resource "aws_sqs_queue" "etime-14si-stage-excess-time_ess_time" {
  name = "etime-14si-stage-excess-time"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-excess-time"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-stage-excess-time"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-edrms-responses
resource "aws_sqs_queue" "etime-14si-stage-edrms-responses_esponses" {
  name = "etime-14si-stage-edrms-responses"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-edrms-responses"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-stage-edrms-responses"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-browser-notifications
resource "aws_sqs_queue" "etime-14si-stage-browser-notifications_ications" {
  name = "etime-14si-stage-browser-notifications"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-browser-notifications"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-stage-browser-notifications"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-broadcasts
resource "aws_sqs_queue" "etime-14si-stage-broadcasts_oadcasts" {
  name = "etime-14si-stage-broadcasts"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-broadcasts"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-stage-broadcasts"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-workflows
resource "aws_sqs_queue" "etime-14si-stage-workflows" {
  name = "etime-14si-stage-workflows"


  visibility_timeout_seconds  = 180
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-workflows"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-prod-workflows"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-user
resource "aws_sqs_queue" "etime-14si-stage-user" {
  name = "etime-14si-stage-user"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-user"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-prod-user"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-upgrades
resource "aws_sqs_queue" "etime-14si-stage-upgrades" {
  name = "etime-14si-stage-upgrades"


  visibility_timeout_seconds  = 36000
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-upgrades"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-prod-upgrades"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-timesheets
resource "aws_sqs_queue" "etime-14si-stage-timesheets" {
  name = "etime-14si-stage-timesheets"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-timesheets"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-prod-timesheets"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-tenant
resource "aws_sqs_queue" "etime-14si-stage-tenant" {
  name = "etime-14si-stage-tenant"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-tenant"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-prod-tenant"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-shifts
resource "aws_sqs_queue" "etime-14si-stage-shifts" {
  name = "etime-14si-stage-shifts"


  visibility_timeout_seconds  = 1200
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-shifts"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-prod-shifts"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-settings
resource "aws_sqs_queue" "etime-14si-stage-settings" {
  name = "etime-14si-stage-settings"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-settings"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-prod-settings"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-reports
resource "aws_sqs_queue" "etime-14si-stage-reports" {
  name = "etime-14si-stage-reports"


  visibility_timeout_seconds  = 1800
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-reports"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-prod-reports"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-penalties
resource "aws_sqs_queue" "etime-14si-stage-penalties" {
  name = "etime-14si-stage-penalties"


  visibility_timeout_seconds  = 300
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-penalties"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-prod-penalties"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-payroll-authority-response
resource "aws_sqs_queue" "etime-14si-stage-payroll-authority-response" {
  name = "etime-14si-stage-payroll-authority-response"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-payroll-authority-response"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-prod-payroll-authority-response"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-notifications-triggers
resource "aws_sqs_queue" "etime-14si-stage-notifications-triggers" {
  name = "etime-14si-stage-notifications-triggers"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-notifications-triggers"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-prod-notifications-triggers"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-notifications
resource "aws_sqs_queue" "etime-14si-stage-notifications" {
  name = "etime-14si-stage-notifications"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-notifications"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-prod-notifications"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-leave-balances
resource "aws_sqs_queue" "etime-14si-stage-leave-balances" {
  name = "etime-14si-stage-leave-balances"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-leave-balances"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-prod-leave-balances"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-integrations
resource "aws_sqs_queue" "etime-14si-stage-integrations" {
  name = "etime-14si-stage-integrations"


  visibility_timeout_seconds  = 300
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-integrations"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-prod-integrations"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-generic-authority-response
resource "aws_sqs_queue" "etime-14si-stage-generic-authority-response" {
  name = "etime-14si-stage-generic-authority-response"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-generic-authority-response"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-prod-generic-authority-response"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-general
resource "aws_sqs_queue" "etime-14si-stage-general" {
  name = "etime-14si-stage-general"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-general"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-prod-general"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-excess-time
resource "aws_sqs_queue" "etime-14si-stage-excess-time" {
  name = "etime-14si-stage-excess-time"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-excess-time"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-prod-excess-time"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-edrms-responses
resource "aws_sqs_queue" "etime-14si-stage-edrms-responses" {
  name = "etime-14si-stage-edrms-responses"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-edrms-responses"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-prod-edrms-responses"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-browser-notifications
resource "aws_sqs_queue" "etime-14si-stage-browser-notifications" {
  name = "etime-14si-stage-browser-notifications"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-browser-notifications"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-prod-browser-notifications"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: etime-14si-stage-broadcasts
resource "aws_sqs_queue" "etime-14si-stage-broadcasts" {
  name = "etime-14si-stage-broadcasts"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "etime-14si-stage-broadcasts"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:etime-14si-prod-broadcasts"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:er-response-dev-leo
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_er-response-dev-leo" {
  name = "er-response-dev-leo"


  visibility_timeout_seconds  = 300
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:er-response-dev-leo"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:er-response-dev-leo"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:er-response
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_er-response" {
  name = "er-response"


  visibility_timeout_seconds  = 300
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:er-response"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:er-response"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:er-agent-general-dev-leo
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_er-agent-general-dev-leo" {
  name = "er-agent-general-dev-leo"


  visibility_timeout_seconds  = 300
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:er-agent-general-dev-leo"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:er-agent-general-dev-leo"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:er-agent-general
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_er-agent-general" {
  name = "er-agent-general"


  visibility_timeout_seconds  = 300
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:er-agent-general"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:er-agent-general"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-sandbox
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-ghostrpc-sandbox" {
  name = "elementtime-ghostrpc-sandbox"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-sandbox"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-sandbox"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-test
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-ghostrpc-response-test" {
  name = "elementtime-ghostrpc-response-test"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-test"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-local-leo
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-ghostrpc-response-local-leo" {
  name = "elementtime-ghostrpc-response-local-leo"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-local-leo"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-local-leo"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-authority-sb
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-ghostrpc-response-authority-sb" {
  name = "elementtime-ghostrpc-response-authority-sb"


  visibility_timeout_seconds  = 180
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-authority-sb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-authority-sb"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-authority-local-leo
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-ghostrpc-response-authority-local-leo" {
  name = "elementtime-ghostrpc-response-authority-local-leo"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-authority-local-leo"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-authority-local-leo"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-authority-generic-sb
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-ghostrpc-response-authority-generic-sb" {
  name = "elementtime-ghostrpc-response-authority-generic-sb"


  visibility_timeout_seconds  = 180
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-authority-generic-sb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-authority-generic-sb"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-authority-generic-local-leo
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-ghostrpc-response-authority-generic-local-leo" {
  name = "elementtime-ghostrpc-response-authority-generic-local-leo"


  visibility_timeout_seconds  = 180
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-authority-generic-local-leo"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-authority-generic-local-leo"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-authority-generic
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-ghostrpc-response-authority-generic" {
  name = "elementtime-ghostrpc-response-authority-generic"


  visibility_timeout_seconds  = 180
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-authority-generic"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-authority-generic"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-authority
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-ghostrpc-response-authority" {
  name = "elementtime-ghostrpc-response-authority"


  visibility_timeout_seconds  = 180
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-authority"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response-authority"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-ghostrpc-response" {
  name = "elementtime-ghostrpc-response"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-ghostrpc-response"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-11-broadcasts
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-test-11-broadcasts" {
  name = "elementtime-app-queue-test-11-broadcasts"


  visibility_timeout_seconds  = 180
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-11-broadcasts"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-11-broadcasts"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-10-broadcasts
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-test-10-broadcasts" {
  name = "elementtime-app-queue-test-10-broadcasts"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-10-broadcasts"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-10-broadcasts"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-09-settings
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-test-09-settings" {
  name = "elementtime-app-queue-test-09-settings"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-09-settings"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-09-settings"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-08-notifications-triggers
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-test-08-notifications-triggers" {
  name = "elementtime-app-queue-test-08-notifications-triggers"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-08-notifications-triggers"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-08-notifications-triggers"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-08-notifications
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-test-08-notifications" {
  name = "elementtime-app-queue-test-08-notifications"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-08-notifications"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-08-notifications"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-08-browser-notifications
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-test-08-browser-notifications" {
  name = "elementtime-app-queue-test-08-browser-notifications"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-08-browser-notifications"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-08-browser-notifications"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-07-reports
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-test-07-reports" {
  name = "elementtime-app-queue-test-07-reports"


  visibility_timeout_seconds  = 300
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-07-reports"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-07-reports"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-06-user
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-test-06-user" {
  name = "elementtime-app-queue-test-06-user"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-06-user"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-06-user"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-05-leave-balances
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-test-05-leave-balances" {
  name = "elementtime-app-queue-test-05-leave-balances"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-05-leave-balances"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-05-leave-balances"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-04-penalties
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-test-04-penalties" {
  name = "elementtime-app-queue-test-04-penalties"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-04-penalties"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-04-penalties"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-03-excess-time
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-test-03-excess-time" {
  name = "elementtime-app-queue-test-03-excess-time"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-03-excess-time"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-03-excess-time"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-02-timesheets
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-test-02-timesheets" {
  name = "elementtime-app-queue-test-02-timesheets"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-02-timesheets"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-02-timesheets"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-01-shifts
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-test-01-shifts" {
  name = "elementtime-app-queue-test-01-shifts"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-01-shifts"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-01-shifts"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-00-tenant
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-test-00-tenant" {
  name = "elementtime-app-queue-test-00-tenant"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-00-tenant"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test-00-tenant"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-test" {
  name = "elementtime-app-queue-test"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-test"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--workflows
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-sb--workflows" {
  name = "elementtime-app-queue-sb--workflows"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--workflows"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--workflows"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--user
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-sb--user" {
  name = "elementtime-app-queue-sb--user"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--user"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--user"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--timesheets
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-sb--timesheets" {
  name = "elementtime-app-queue-sb--timesheets"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--timesheets"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--timesheets"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--tenant
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-sb--tenant" {
  name = "elementtime-app-queue-sb--tenant"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--tenant"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--tenant"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--shifts
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-sb--shifts" {
  name = "elementtime-app-queue-sb--shifts"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--shifts"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--shifts"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--settings
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-sb--settings" {
  name = "elementtime-app-queue-sb--settings"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--settings"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--settings"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--reports
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-sb--reports" {
  name = "elementtime-app-queue-sb--reports"


  visibility_timeout_seconds  = 1800
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--reports"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--reports"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--penalties
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-sb--penalties" {
  name = "elementtime-app-queue-sb--penalties"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--penalties"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--penalties"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--notifications-triggers
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-sb--notifications-triggers" {
  name = "elementtime-app-queue-sb--notifications-triggers"


  visibility_timeout_seconds  = 300
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--notifications-triggers"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--notifications-triggers"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--notifications
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-sb--notifications" {
  name = "elementtime-app-queue-sb--notifications"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--notifications"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--notifications"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--leave-balances
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-sb--leave-balances" {
  name = "elementtime-app-queue-sb--leave-balances"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--leave-balances"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--leave-balances"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--integrations
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-sb--integrations" {
  name = "elementtime-app-queue-sb--integrations"


  visibility_timeout_seconds  = 180
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--integrations"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--integrations"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--excess-time
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-sb--excess-time" {
  name = "elementtime-app-queue-sb--excess-time"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--excess-time"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--excess-time"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--browser-notifications
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-sb--browser-notifications" {
  name = "elementtime-app-queue-sb--browser-notifications"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--browser-notifications"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--browser-notifications"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--broadcasts
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-sb--broadcasts" {
  name = "elementtime-app-queue-sb--broadcasts"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--broadcasts"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb--broadcasts"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-sb" {
  name = "elementtime-app-queue-sb"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-sb"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-rafael
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-local-rafael" {
  name = "elementtime-app-queue-local-rafael"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-rafael"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-rafael"
  }
}

# SQS Queue: elementtime-app-queue-local-matheus-mei
resource "aws_sqs_queue" "elementtime-app-queue-local-matheus-mei" {
  name = "elementtime-app-queue-local-matheus-mei"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "elementtime-app-queue-local-matheus-mei"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-matheus-mei"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: elementtime-app-queue-local-leo-13-upgrades
resource "aws_sqs_queue" "elementtime-app-queue-local-leo-13-upgrades" {
  name = "elementtime-app-queue-local-leo-13-upgrades"


  visibility_timeout_seconds  = 1800
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "elementtime-app-queue-local-leo-13-upgrades"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-13-upgrades"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-12-integrations
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-local-leo-12-integrations" {
  name = "elementtime-app-queue-local-leo-12-integrations"


  visibility_timeout_seconds  = 300
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-12-integrations"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-12-integrations"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-11-workflows
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-local-leo-11-workflows" {
  name = "elementtime-app-queue-local-leo-11-workflows"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-11-workflows"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-11-workflows"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-10-broadcasts
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-local-leo-10-broadcasts" {
  name = "elementtime-app-queue-local-leo-10-broadcasts"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-10-broadcasts"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-10-broadcasts"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-09-settings
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-local-leo-09-settings" {
  name = "elementtime-app-queue-local-leo-09-settings"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-09-settings"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-09-settings"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-08-notifications-triggers
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-local-leo-08-notifications-triggers" {
  name = "elementtime-app-queue-local-leo-08-notifications-triggers"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-08-notifications-triggers"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-08-notifications-triggers"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-08-notifications
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-local-leo-08-notifications" {
  name = "elementtime-app-queue-local-leo-08-notifications"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-08-notifications"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-08-notifications"
  }
}

# SNS Topic: s3-shared-files-changed
resource "aws_sns_topic" "s3-shared-files-changed" {
  name = "s3-shared-files-changed"




  tags = {
    Name        = "s3-shared-files-changed"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:s3-shared-files-changed"
    "Cost Center" = "Platform"
    environment = "staging"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-08-browser-notifications
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-local-leo-08-browser-notifications" {
  name = "elementtime-app-queue-local-leo-08-browser-notifications"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-08-browser-notifications"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-08-browser-notifications"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:monitoring-sysadmin
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_monitoring-sysadmin" {
  name = "monitoring-sysadmin"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:monitoring-sysadmin"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:monitoring-sysadmin"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-07-reports
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-local-leo-07-reports" {
  name = "elementtime-app-queue-local-leo-07-reports"


  visibility_timeout_seconds  = 1800
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-07-reports"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-07-reports"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:monitoring-security
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_monitoring-security" {
  name = "monitoring-security"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:monitoring-security"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:monitoring-security"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-06-user
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-local-leo-06-user" {
  name = "elementtime-app-queue-local-leo-06-user"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-06-user"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-06-user"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:monitoring-generic
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_monitoring-generic" {
  name = "monitoring-generic"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:monitoring-generic"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:monitoring-generic"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-05-leave-balances
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-local-leo-05-leave-balances" {
  name = "elementtime-app-queue-local-leo-05-leave-balances"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-05-leave-balances"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-05-leave-balances"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:microservice-notify
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_microservice-notify" {
  name = "microservice-notify"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:microservice-notify"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:microservice-notify"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-04-penalties
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-local-leo-04-penalties" {
  name = "elementtime-app-queue-local-leo-04-penalties"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-04-penalties"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-04-penalties"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-03-excess-time
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-local-leo-03-excess-time" {
  name = "elementtime-app-queue-local-leo-03-excess-time"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-03-excess-time"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-03-excess-time"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:etime-face-auth-stage-alerts
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_etime-face-auth-stage-alerts" {
  name = "etime-face-auth-stage-alerts"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:etime-face-auth-stage-alerts"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:etime-face-auth-prod-alerts"
    "Cost Center" = "elementTIME"
    Project = "etime-face-auth"
    ManagedBy = "terraform"
    Terraform = "true"
    Environment = "stage"
    Service = "face-auth"
    Component = "monitoring"
  }
}

# SNS Topic: sns-to-slack-eo-leeton
resource "aws_sns_topic" "sns-to-slack-eo-leeton" {
  name = "eo-leeton"




  tags = {
    Name        = "sns-to-slack-eo-leeton"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:eo-leeton"
    Project = "elementOrg"
    Owner = "ac"
    CostCenter = "platform"
    Terraform = "true"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-02-timesheets
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-local-leo-02-timesheets" {
  name = "elementtime-app-queue-local-leo-02-timesheets"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-02-timesheets"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-02-timesheets"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:elementTimeDepStage
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_elementTimeDepStage" {
  name = "elementTimeDepStage"


  display_name = "Staging"


  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:elementTimeDepStage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:elementTimeDepStage"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:elementTIMEDepTest
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_elementTIMEDepTest" {
  name = "elementTIMEDepTest"


  display_name = "Test"


  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:elementTIMEDepTest"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:elementTIMEDepTest"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-01-shifts
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-local-leo-01-shifts" {
  name = "elementtime-app-queue-local-leo-01-shifts"


  visibility_timeout_seconds  = 3600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-01-shifts"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-01-shifts"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:elementTIMEDepPro
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_elementTIMEDepPro" {
  name = "elementTIMEDepPro"


  display_name = "staging"


  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:elementTIMEDepPro"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:elementTIMEDepPro"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-00-tenant
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-local-leo-00-tenant" {
  name = "elementtime-app-queue-local-leo-00-tenant"


  visibility_timeout_seconds  = 20
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-00-tenant"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo-00-tenant"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:elementTIME-Instance-Alert
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_elementTIME-Instance-Alert" {
  name = "elementTIME-Instance-Alert"


  display_name = "elementTIME Instance Alert"


  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:elementTIME-Instance-Alert"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:elementTIME-Instance-Alert"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-local-leo" {
  name = "elementtime-app-queue-local-leo"


  visibility_timeout_seconds  = 1200
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-leo"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:dynamodb
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_dynamodb" {
  name = "dynamodb"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:dynamodb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:dynamodb"
  }
}

# SQS Queue: elementtime-app-queue-local-isaac-santos
resource "aws_sqs_queue" "elementtime-app-queue-local-isaac-santos" {
  name = "elementtime-app-queue-local-isaac-santos"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "elementtime-app-queue-local-isaac-santos"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-isaac-santos"
    "Cost Center" = "elementTIME"
    Environment = "stage"
    Terraform = "true"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:codestar-notifications-elementstaff
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_codestar-notifications-elementstaff" {
  name = "codestar-notifications-elementstaff"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:codestar-notifications-elementstaff"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:codestar-notifications-elementstaff"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-gustavo
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-local-gustavo" {
  name = "elementtime-app-queue-local-gustavo"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-gustavo"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local-gustavo"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:aws-backup-failures
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_aws-backup-failures" {
  name = "aws-backup-failures"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:aws-backup-failures"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:aws-backup-failures"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue-local" {
  name = "elementtime-app-queue-local"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue-local"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:aurora-replica-scheduler-notifications
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_aurora-replica-scheduler-notifications" {
  name = "aurora-replica-scheduler-notifications"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:aurora-replica-scheduler-notifications"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:aurora-replica-scheduler-notifications"
    Terraform = "true"
    Project = "elementtime"
    Environment = "stage"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--workflows
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue--workflows" {
  name = "elementtime-app-queue--workflows"


  visibility_timeout_seconds  = 180
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--workflows"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--workflows"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:asg-lifecycle-events
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_asg-lifecycle-events" {
  name = "asg-lifecycle-events"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:asg-lifecycle-events"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:asg-lifecycle-events"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--user
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue--user" {
  name = "elementtime-app-queue--user"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--user"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--user"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:asg-events-test
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_asg-events-test" {
  name = "asg-events-test"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:asg-events-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:asg-events-test"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:asg-events-stage
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_asg-events-stage" {
  name = "asg-events-stage"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:asg-events-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:asg-events-stage"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:asg-events
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_asg-events" {
  name = "asg-events"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:asg-events"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:asg-events"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--timesheets
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue--timesheets" {
  name = "elementtime-app-queue--timesheets"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--timesheets"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--timesheets"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-elementTIME-Pipeline
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_Internal-Notification-elementTIME-Pipeline" {
  name = "Internal-Notification-elementTIME-Pipeline"


  display_name = "elementTIME Build and Deployment"


  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-elementTIME-Pipeline"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-elementTIME-Pipeline"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--tenant
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue--tenant" {
  name = "elementtime-app-queue--tenant"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--tenant"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--tenant"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-elementTIME-Minor-Alram
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_Internal-Notification-elementTIME-Minor-Alram" {
  name = "Internal-Notification-elementTIME-Minor-Alram"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-elementTIME-Minor-Alram"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-elementTIME-Minor-Alram"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--shifts
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue--shifts" {
  name = "elementtime-app-queue--shifts"


  visibility_timeout_seconds  = 1200
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--shifts"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--shifts"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-elementTIME-Major-Alram
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_Internal-Notification-elementTIME-Major-Alram" {
  name = "Internal-Notification-elementTIME-Major-Alram"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-elementTIME-Major-Alram"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-elementTIME-Major-Alram"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--settings
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue--settings" {
  name = "elementtime-app-queue--settings"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--settings"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--settings"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-elementTIME-Critical-Alram
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_Internal-Notification-elementTIME-Critical-Alram" {
  name = "Internal-Notification-elementTIME-Critical-Alram"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-elementTIME-Critical-Alram"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-elementTIME-Critical-Alram"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-Pipelines
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_Internal-Notification-Pipelines" {
  name = "Internal-Notification-Pipelines"


  display_name = "All product build and deployment"


  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-Pipelines"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-Pipelines"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-Minor-Alram
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_Internal-Notification-Minor-Alram" {
  name = "Internal-Notification-Minor-Alram"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-Minor-Alram"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-Minor-Alram"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--reports
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue--reports" {
  name = "elementtime-app-queue--reports"


  visibility_timeout_seconds  = 1800
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--reports"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--reports"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-Major-Alram
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_Internal-Notification-Major-Alram" {
  name = "Internal-Notification-Major-Alram"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-Major-Alram"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-Major-Alram"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--penalties
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue--penalties" {
  name = "elementtime-app-queue--penalties"


  visibility_timeout_seconds  = 300
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--penalties"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--penalties"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-Critical-Alram
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_Internal-Notification-Critical-Alram" {
  name = "Internal-Notification-Critical-Alram"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-Critical-Alram"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:Internal-Notification-Critical-Alram"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--notifications-triggers
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue--notifications-triggers" {
  name = "elementtime-app-queue--notifications-triggers"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--notifications-triggers"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--notifications-triggers"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:GhostRPC-Alarm
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_GhostRPC-Alarm" {
  name = "GhostRPC-Alarm"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:GhostRPC-Alarm"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:GhostRPC-Alarm"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--notifications
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue--notifications" {
  name = "elementtime-app-queue--notifications"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--notifications"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--notifications"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:ElementTimeAlarms
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_ElementTimeAlarms" {
  name = "ElementTimeAlarms"


  display_name = "ETAlarms"


  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:ElementTimeAlarms"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:ElementTimeAlarms"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--leave-balances
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue--leave-balances" {
  name = "elementtime-app-queue--leave-balances"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--leave-balances"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--leave-balances"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:ESDeploymentNotice
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_ESDeploymentNotice" {
  name = "ESDeploymentNotice"


  display_name = "ESDeploy"


  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:ESDeploymentNotice"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:ESDeploymentNotice"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:DeploymentNoticeTest
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_DeploymentNoticeTest" {
  name = "DeploymentNoticeTest"


  display_name = "DepNoteTst"


  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:DeploymentNoticeTest"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:DeploymentNoticeTest"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--integrations
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue--integrations" {
  name = "elementtime-app-queue--integrations"


  visibility_timeout_seconds  = 300
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--integrations"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--integrations"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:DeploymentNotice
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_DeploymentNotice" {
  name = "DeploymentNotice"


  display_name = "ETDeploy"


  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:DeploymentNotice"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:DeploymentNotice"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:AlertsForYorke
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_AlertsForYorke" {
  name = "AlertsForYorke"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:AlertsForYorke"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:AlertsForYorke"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:AlertsForMtBarker
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_AlertsForMtBarker" {
  name = "AlertsForMtBarker"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:AlertsForMtBarker"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:AlertsForMtBarker"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--excess-time
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue--excess-time" {
  name = "elementtime-app-queue--excess-time"


  visibility_timeout_seconds  = 120
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--excess-time"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--excess-time"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:Adroit-staging-Alarm
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_Adroit-staging-Alarm" {
  name = "Adroit-staging-Alarm"




  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:Adroit-staging-Alarm"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:Adroit-Production-Alarm"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--browser-notifications
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue--browser-notifications" {
  name = "elementtime-app-queue--browser-notifications"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--browser-notifications"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--browser-notifications"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--broadcasts
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue--broadcasts" {
  name = "elementtime-app-queue--broadcasts"


  visibility_timeout_seconds  = 60
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--broadcasts"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue--broadcasts"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementtime-app-queue" {
  name = "elementtime-app-queue"


  visibility_timeout_seconds  = 600
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementtime-app-queue"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:AWSSensitiveOperation
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_AWSSensitiveOperation" {
  name = "AWSSensitiveOperation"


  display_name = "AWS Sensitive Operation"


  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:AWSSensitiveOperation"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:AWSSensitiveOperation"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementrec-ghostrpc-response
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementrec-ghostrpc-response" {
  name = "elementrec-ghostrpc-response"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 1048576
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementrec-ghostrpc-response"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementrec-ghostrpc-response"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:AWSSecurityAlerts
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_AWSSecurityAlerts" {
  name = "AWSSecurityAlerts"


  display_name = "AWS Security Alerts"


  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:AWSSecurityAlerts"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:AWSSecurityAlerts"
  }
}

# SNS Topic: arn:aws:sns:ap-southeast-2:542859091916:AWSCriticalOperation
resource "aws_sns_topic" "arn_aws_sns_ap-southeast-2_542859091916_AWSCriticalOperation" {
  name = "AWSCriticalOperation"


  display_name = "AWS Critical Operation"


  tags = {
    Name        = "arn:aws:sns:ap-southeast-2:542859091916:AWSCriticalOperation"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sns:ap-southeast-2:542859091916:AWSCriticalOperation"
  }
}

# SQS Queue: arn:aws:sqs:ap-southeast-2:542859091916:elementorg-sqlmover2-error-log
resource "aws_sqs_queue" "arn_aws_sqs_ap-southeast-2_542859091916_elementorg-sqlmover2-error-log" {
  name = "elementorg-sqlmover2-error-log"


  visibility_timeout_seconds  = 30
  message_retention_seconds   = 345600
  max_message_size            = 262144
  delay_seconds               = 0
  receive_wait_time_seconds   = 0



  tags = {
    Name        = "arn:aws:sqs:ap-southeast-2:542859091916:elementorg-sqlmover2-error-log"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "arn:aws:sqs:ap-southeast-2:542859091916:elementorg-sqlmover2-error-log"
    project_service = "elementOrg"
    environment = "stage"
    project_team = "elementOrg"
    secure = "false"
    cost_center = "elementOrg"
  }
}