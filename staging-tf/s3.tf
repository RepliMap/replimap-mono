# S3 Bucket: testmountbarker.elementrec.com
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "testmountbarker_elementrec_com" {
  bucket = "testmountbarker.elementrec.com-${var.environment}"

  tags = {
    Name        = "testmountbarker.elementrec.com"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "testmountbarker.elementrec.com"
  }
}

resource "aws_s3_bucket_versioning" "testmountbarker_elementrec_com" {
  bucket = aws_s3_bucket.testmountbarker_elementrec_com.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "testmountbarker_elementrec_com" {
  bucket = aws_s3_bucket.testmountbarker_elementrec_com.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "testmountbarker_elementrec_com" {
  bucket = aws_s3_bucket.testmountbarker_elementrec_com.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: tenant.elementstaff.com
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "tenant_elementstaff_com" {
  bucket = "tenant.elementstaff.com-${var.environment}"

  tags = {
    Name        = "tenant.elementstaff.com"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "tenant.elementstaff.com"
  }
}

resource "aws_s3_bucket_versioning" "tenant_elementstaff_com" {
  bucket = aws_s3_bucket.tenant_elementstaff_com.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tenant_elementstaff_com" {
  bucket = aws_s3_bucket.tenant_elementstaff_com.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: zzz-leo-sync
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "zzz-leo-sync" {
  bucket = "zzz-leo-sync-${var.environment}"

  tags = {
    Name        = "zzz-leo-sync"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "zzz-leo-sync"
  }
}

resource "aws_s3_bucket_versioning" "zzz-leo-sync" {
  bucket = aws_s3_bucket.zzz-leo-sync.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "zzz-leo-sync" {
  bucket = aws_s3_bucket.zzz-leo-sync.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "zzz-leo-sync" {
  bucket = aws_s3_bucket.zzz-leo-sync.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: tenant.elementstaff.test
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "tenant_elementstaff_test" {
  bucket = "tenant.elementstaff.test-${var.environment}"

  tags = {
    Name        = "tenant.elementstaff.test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "tenant.elementstaff.test"
  }
}

resource "aws_s3_bucket_versioning" "tenant_elementstaff_test" {
  bucket = aws_s3_bucket.tenant_elementstaff_test.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "tenant_elementstaff_test" {
  bucket = aws_s3_bucket.tenant_elementstaff_test.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: it-lambdas-sydney
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "it-lambdas-sydney" {
  bucket = "it-lambdas-sydney-${var.environment}"

  tags = {
    Name        = "it-lambdas-sydney"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "it-lambdas-sydney"
    Cost Center = "Platform"
    environment = "staging"
  }
}

resource "aws_s3_bucket_versioning" "it-lambdas-sydney" {
  bucket = aws_s3_bucket.it-lambdas-sydney.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "it-lambdas-sydney" {
  bucket = aws_s3_bucket.it-lambdas-sydney.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: stackset-aws-cost-report-pipelinebuiltartifactbuc-kvq8cnzxdzxw
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "stackset-aws-cost-report-pipelinebuiltartifactbuc-kvq8cnzxdzxw" {
  bucket = "stackset-aws-cost-report-pipelinebuiltartifactbuc-kvq8cnzxdzxw-${var.environment}"

  tags = {
    Name        = "stackset-aws-cost-report-pipelinebuiltartifactbuc-kvq8cnzxdzxw"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "stackset-aws-cost-report-pipelinebuiltartifactbuc-kvq8cnzxdzxw"
    aws:cloudformation:stack-name = "StackSet-aws-cost-report-infrastructure-be7be2f2-500b-4de6-ac5e-301f0f56a1ed"
    aws:cloudformation:logical-id = "PipelineBuiltArtifactBucket"
    aws:cloudformation:stack-id = "arn:aws:cloudformation:ap-southeast-2:${var.aws_account_id}:stack/StackSet-aws-cost-report-infrastructure-be7be2f2-500b-4de6-ac5e-301f0f56a1ed/1f8f20c0-b987-11ec-8f35-025dac9419cc"
    copilot-application = "aws-cost-report"
  }
}

resource "aws_s3_bucket_versioning" "stackset-aws-cost-report-pipelinebuiltartifactbuc-kvq8cnzxdzxw" {
  bucket = aws_s3_bucket.stackset-aws-cost-report-pipelinebuiltartifactbuc-kvq8cnzxdzxw.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "stackset-aws-cost-report-pipelinebuiltartifactbuc-kvq8cnzxdzxw" {
  bucket = aws_s3_bucket.stackset-aws-cost-report-pipelinebuiltartifactbuc-kvq8cnzxdzxw.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: remediate-athena-542859091916-ap-southeast-2
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "remediate-athena-542859091916-ap-southeast-2" {
  bucket = "remediate-athena-542859091916-ap-southeast-2-${var.environment}"

  tags = {
    Name        = "remediate-athena-542859091916-ap-southeast-2"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "remediate-athena-542859091916-ap-southeast-2"
  }
}

resource "aws_s3_bucket_versioning" "remediate-athena-542859091916-ap-southeast-2" {
  bucket = aws_s3_bucket.remediate-athena-542859091916-ap-southeast-2.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "remediate-athena-542859091916-ap-southeast-2" {
  bucket = aws_s3_bucket.remediate-athena-542859091916-ap-southeast-2.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "remediate-athena-542859091916-ap-southeast-2" {
  bucket = aws_s3_bucket.remediate-athena-542859091916-ap-southeast-2.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: stackset-sms-report-infr-pipelinebuiltartifactbuc-rn9wu063pnet
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "stackset-sms-report-infr-pipelinebuiltartifactbuc-rn9wu063pnet" {
  bucket = "stackset-sms-report-infr-pipelinebuiltartifactbuc-rn9wu063pnet-${var.environment}"

  tags = {
    Name        = "stackset-sms-report-infr-pipelinebuiltartifactbuc-rn9wu063pnet"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "stackset-sms-report-infr-pipelinebuiltartifactbuc-rn9wu063pnet"
    aws:cloudformation:stack-name = "StackSet-sms-report-infrastructure-9fb887a8-0fa4-44eb-a537-1c30fbab2015"
    aws:cloudformation:logical-id = "PipelineBuiltArtifactBucket"
    aws:cloudformation:stack-id = "arn:aws:cloudformation:ap-southeast-2:${var.aws_account_id}:stack/StackSet-sms-report-infrastructure-9fb887a8-0fa4-44eb-a537-1c30fbab2015/fcb05630-df61-11ed-9b49-020e12513ad0"
    copilot-application = "sms-report"
  }
}

resource "aws_s3_bucket_versioning" "stackset-sms-report-infr-pipelinebuiltartifactbuc-rn9wu063pnet" {
  bucket = aws_s3_bucket.stackset-sms-report-infr-pipelinebuiltartifactbuc-rn9wu063pnet.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "stackset-sms-report-infr-pipelinebuiltartifactbuc-rn9wu063pnet" {
  bucket = aws_s3_bucket.stackset-sms-report-infr-pipelinebuiltartifactbuc-rn9wu063pnet.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: stackset-check-aws-ri-in-pipelinebuiltartifactbuc-15f1th9a68wi0
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "stackset-check-aws-ri-in-pipelinebuiltartifactbuc-15f1th9a68wi0" {
  bucket = "stackset-check-aws-ri-in-pipelinebuiltartifactbuc-15f1th9a68wi0-${var.environment}"

  tags = {
    Name        = "stackset-check-aws-ri-in-pipelinebuiltartifactbuc-15f1th9a68wi0"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "stackset-check-aws-ri-in-pipelinebuiltartifactbuc-15f1th9a68wi0"
    aws:cloudformation:stack-name = "StackSet-check-aws-ri-infrastructure-3d0805f2-89df-4ed9-a966-1f964ebe0565"
    aws:cloudformation:logical-id = "PipelineBuiltArtifactBucket"
    aws:cloudformation:stack-id = "arn:aws:cloudformation:ap-southeast-2:${var.aws_account_id}:stack/StackSet-check-aws-ri-infrastructure-3d0805f2-89df-4ed9-a966-1f964ebe0565/44383d90-b800-11ec-9539-0219e5a28b7a"
    copilot-application = "check-aws-ri"
  }
}

resource "aws_s3_bucket_versioning" "stackset-check-aws-ri-in-pipelinebuiltartifactbuc-15f1th9a68wi0" {
  bucket = aws_s3_bucket.stackset-check-aws-ri-in-pipelinebuiltartifactbuc-15f1th9a68wi0.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "stackset-check-aws-ri-in-pipelinebuiltartifactbuc-15f1th9a68wi0" {
  bucket = aws_s3_bucket.stackset-check-aws-ri-in-pipelinebuiltartifactbuc-15f1th9a68wi0.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: stackset-security-report-pipelinebuiltartifactbuc-rkmerabp656e
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "stackset-security-report-pipelinebuiltartifactbuc-rkmerabp656e" {
  bucket = "stackset-security-report-pipelinebuiltartifactbuc-rkmerabp656e-${var.environment}"

  tags = {
    Name        = "stackset-security-report-pipelinebuiltartifactbuc-rkmerabp656e"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "stackset-security-report-pipelinebuiltartifactbuc-rkmerabp656e"
    aws:cloudformation:stack-name = "StackSet-security-report-infrastructure-ef079681-3d07-43b6-a744-51b9931d19c5"
    aws:cloudformation:logical-id = "PipelineBuiltArtifactBucket"
    aws:cloudformation:stack-id = "arn:aws:cloudformation:ap-southeast-2:${var.aws_account_id}:stack/StackSet-security-report-infrastructure-ef079681-3d07-43b6-a744-51b9931d19c5/831e2100-91a3-11ed-97b4-0a3e72f351ca"
    copilot-application = "security-report"
  }
}

resource "aws_s3_bucket_versioning" "stackset-security-report-pipelinebuiltartifactbuc-rkmerabp656e" {
  bucket = aws_s3_bucket.stackset-security-report-pipelinebuiltartifactbuc-rkmerabp656e.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "stackset-security-report-pipelinebuiltartifactbuc-rkmerabp656e" {
  bucket = aws_s3_bucket.stackset-security-report-pipelinebuiltartifactbuc-rkmerabp656e.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: mountbarker.elementrec.com
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "mountbarker_elementrec_com" {
  bucket = "mountbarker.elementrec.com-${var.environment}"

  tags = {
    Name        = "mountbarker.elementrec.com"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "mountbarker.elementrec.com"
  }
}

resource "aws_s3_bucket_versioning" "mountbarker_elementrec_com" {
  bucket = aws_s3_bucket.mountbarker_elementrec_com.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "mountbarker_elementrec_com" {
  bucket = aws_s3_bucket.mountbarker_elementrec_com.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: elementrec-public-bucket
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "elementrec-public-bucket" {
  bucket = "elementrec-public-bucket-${var.environment}"

  tags = {
    Name        = "elementrec-public-bucket"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "elementrec-public-bucket"
  }
}

resource "aws_s3_bucket_versioning" "elementrec-public-bucket" {
  bucket = aws_s3_bucket.elementrec-public-bucket.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "elementrec-public-bucket" {
  bucket = aws_s3_bucket.elementrec-public-bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "elementrec-public-bucket" {
  bucket = aws_s3_bucket.elementrec-public-bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: etime-face-auth-prod-face-images
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-etime-face-auth-images-stage" {
  bucket = "etime-face-auth-stage-face-images-${var.environment}"

  tags = {
    Name        = "ac-etime-face-auth-images-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "etime-face-auth-prod-face-images"
    Cost Center = "elementTIME"
    environment = "stage"
  }
}

resource "aws_s3_bucket_versioning" "ac-etime-face-auth-images-stage" {
  bucket = aws_s3_bucket.ac-etime-face-auth-images-stage.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-etime-face-auth-images-stage" {
  bucket = aws_s3_bucket.ac-etime-face-auth-images-stage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "ac-etime-face-auth-images-stage" {
  bucket = aws_s3_bucket.ac-etime-face-auth-images-stage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: elementtime-lambda-artifacts-prod
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "Lambda_Artifacts" {
  bucket = "elementtime-lambda-artifacts-stage-${var.environment}"

  tags = {
    Name        = "Lambda Artifacts"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "elementtime-lambda-artifacts-prod"
    Cost Center = "elementTIME"
    Project = "etime-face-auth"
    ManagedBy = "terraform"
    Terraform = "true"
    Environment = "stage"
    Service = "face-auth"
    Component = "lambda"
  }
}

resource "aws_s3_bucket_versioning" "Lambda_Artifacts" {
  bucket = aws_s3_bucket.Lambda_Artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "Lambda_Artifacts" {
  bucket = aws_s3_bucket.Lambda_Artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "Lambda_Artifacts" {
  bucket = aws_s3_bucket.Lambda_Artifacts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: elementstaff
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "elementstaff" {
  bucket = "elementstaff-${var.environment}"

  tags = {
    Name        = "elementstaff"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "elementstaff"
  }
}

resource "aws_s3_bucket_versioning" "elementstaff" {
  bucket = aws_s3_bucket.elementstaff.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "elementstaff" {
  bucket = aws_s3_bucket.elementstaff.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "elementstaff" {
  bucket = aws_s3_bucket.elementstaff.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: adroitcreations-trail-logs
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "adroitcreations-trail-logs" {
  bucket = "adroitcreations-trail-logs-${var.environment}"

  tags = {
    Name        = "adroitcreations-trail-logs"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "adroitcreations-trail-logs"
  }
}

resource "aws_s3_bucket_versioning" "adroitcreations-trail-logs" {
  bucket = aws_s3_bucket.adroitcreations-trail-logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "adroitcreations-trail-logs" {
  bucket = aws_s3_bucket.adroitcreations-trail-logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "adroitcreations-trail-logs" {
  bucket = aws_s3_bucket.adroitcreations-trail-logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: er-general-dev-leo
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "er-general-dev-leo" {
  bucket = "er-general-dev-leo-${var.environment}"

  tags = {
    Name        = "er-general-dev-leo"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "er-general-dev-leo"
  }
}

resource "aws_s3_bucket_versioning" "er-general-dev-leo" {
  bucket = aws_s3_bucket.er-general-dev-leo.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "er-general-dev-leo" {
  bucket = aws_s3_bucket.er-general-dev-leo.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "er-general-dev-leo" {
  bucket = aws_s3_bucket.er-general-dev-leo.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: adroitcreations-elementtime-app
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "adroitcreations-elementtime-app" {
  bucket = "adroitcreations-elementtime-app-${var.environment}"

  tags = {
    Name        = "adroitcreations-elementtime-app"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "adroitcreations-elementtime-app"
  }
}

resource "aws_s3_bucket_versioning" "adroitcreations-elementtime-app" {
  bucket = aws_s3_bucket.adroitcreations-elementtime-app.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "adroitcreations-elementtime-app" {
  bucket = aws_s3_bucket.adroitcreations-elementtime-app.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "adroitcreations-elementtime-app" {
  bucket = aws_s3_bucket.adroitcreations-elementtime-app.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: er-general
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "er-general" {
  bucket = "er-general-${var.environment}"

  tags = {
    Name        = "er-general"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "er-general"
  }
}

resource "aws_s3_bucket_versioning" "er-general" {
  bucket = aws_s3_bucket.er-general.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "er-general" {
  bucket = aws_s3_bucket.er-general.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "er-general" {
  bucket = aws_s3_bucket.er-general.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: adroitcreations-yorke-intranet
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "adroitcreations-yorke-intranet" {
  bucket = "adroitcreations-yorke-intranet-${var.environment}"

  tags = {
    Name        = "adroitcreations-yorke-intranet"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "adroitcreations-yorke-intranet"
  }
}

resource "aws_s3_bucket_versioning" "adroitcreations-yorke-intranet" {
  bucket = aws_s3_bucket.adroitcreations-yorke-intranet.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "adroitcreations-yorke-intranet" {
  bucket = aws_s3_bucket.adroitcreations-yorke-intranet.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "adroitcreations-yorke-intranet" {
  bucket = aws_s3_bucket.adroitcreations-yorke-intranet.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: elementrec-mountbarker
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "elementrec-mountbarker" {
  bucket = "elementrec-mountbarker-${var.environment}"

  tags = {
    Name        = "elementrec-mountbarker"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "elementrec-mountbarker"
  }
}

resource "aws_s3_bucket_versioning" "elementrec-mountbarker" {
  bucket = aws_s3_bucket.elementrec-mountbarker.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "elementrec-mountbarker" {
  bucket = aws_s3_bucket.elementrec-mountbarker.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "elementrec-mountbarker" {
  bucket = aws_s3_bucket.elementrec-mountbarker.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: codepipeline-ap-southeast-2-224625540070
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "codepipeline-ap-southeast-2-224625540070" {
  bucket = "codepipeline-ap-southeast-2-224625540070-${var.environment}"

  tags = {
    Name        = "codepipeline-ap-southeast-2-224625540070"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "codepipeline-ap-southeast-2-224625540070"
  }
}

resource "aws_s3_bucket_versioning" "codepipeline-ap-southeast-2-224625540070" {
  bucket = aws_s3_bucket.codepipeline-ap-southeast-2-224625540070.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "codepipeline-ap-southeast-2-224625540070" {
  bucket = aws_s3_bucket.codepipeline-ap-southeast-2-224625540070.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: elementrec-mountbarker-test
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "elementrec-mountbarker-test" {
  bucket = "elementrec-mountbarker-test-${var.environment}"

  tags = {
    Name        = "elementrec-mountbarker-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "elementrec-mountbarker-test"
  }
}

resource "aws_s3_bucket_versioning" "elementrec-mountbarker-test" {
  bucket = aws_s3_bucket.elementrec-mountbarker-test.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "elementrec-mountbarker-test" {
  bucket = aws_s3_bucket.elementrec-mountbarker-test.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "elementrec-mountbarker-test" {
  bucket = aws_s3_bucket.elementrec-mountbarker-test.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: adroitcreations-yorke-website
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "adroitcreations-yorke-website" {
  bucket = "adroitcreations-yorke-website-${var.environment}"

  tags = {
    Name        = "adroitcreations-yorke-website"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "adroitcreations-yorke-website"
  }
}

resource "aws_s3_bucket_versioning" "adroitcreations-yorke-website" {
  bucket = aws_s3_bucket.adroitcreations-yorke-website.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "adroitcreations-yorke-website" {
  bucket = aws_s3_bucket.adroitcreations-yorke-website.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "adroitcreations-yorke-website" {
  bucket = aws_s3_bucket.adroitcreations-yorke-website.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: aws-athena-query-results-542859091916-ap-southeast-2
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "aws-athena-query-results-542859091916-ap-southeast-2" {
  bucket = "aws-athena-query-results-542859091916-ap-southeast-2-${var.environment}"

  tags = {
    Name        = "aws-athena-query-results-542859091916-ap-southeast-2"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "aws-athena-query-results-542859091916-ap-southeast-2"
    Cost Center = "Platform"
    environment = "staging"
  }
}

resource "aws_s3_bucket_versioning" "aws-athena-query-results-542859091916-ap-southeast-2" {
  bucket = aws_s3_bucket.aws-athena-query-results-542859091916-ap-southeast-2.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "aws-athena-query-results-542859091916-ap-southeast-2" {
  bucket = aws_s3_bucket.aws-athena-query-results-542859091916-ap-southeast-2.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: adroitcreations-rmagent-ngsc
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "adroitcreations-rmagent-ngsc" {
  bucket = "adroitcreations-rmagent-ngsc-${var.environment}"

  tags = {
    Name        = "adroitcreations-rmagent-ngsc"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "adroitcreations-rmagent-ngsc"
  }
}

resource "aws_s3_bucket_versioning" "adroitcreations-rmagent-ngsc" {
  bucket = aws_s3_bucket.adroitcreations-rmagent-ngsc.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "adroitcreations-rmagent-ngsc" {
  bucket = aws_s3_bucket.adroitcreations-rmagent-ngsc.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "adroitcreations-rmagent-ngsc" {
  bucket = aws_s3_bucket.adroitcreations-rmagent-ngsc.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: adroitcreations-logs
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "adroitcreations-logs" {
  bucket = "adroitcreations-logs-${var.environment}"

  tags = {
    Name        = "adroitcreations-logs"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "adroitcreations-logs"
  }
}

resource "aws_s3_bucket_versioning" "adroitcreations-logs" {
  bucket = aws_s3_bucket.adroitcreations-logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "adroitcreations-logs" {
  bucket = aws_s3_bucket.adroitcreations-logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "adroitcreations-logs" {
  bucket = aws_s3_bucket.adroitcreations-logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: adroitcreations-rmagent-yorke
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "adroitcreations-rmagent-yorke" {
  bucket = "adroitcreations-rmagent-yorke-${var.environment}"

  tags = {
    Name        = "adroitcreations-rmagent-yorke"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "adroitcreations-rmagent-yorke"
  }
}

resource "aws_s3_bucket_versioning" "adroitcreations-rmagent-yorke" {
  bucket = aws_s3_bucket.adroitcreations-rmagent-yorke.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "adroitcreations-rmagent-yorke" {
  bucket = aws_s3_bucket.adroitcreations-rmagent-yorke.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "adroitcreations-rmagent-yorke" {
  bucket = aws_s3_bucket.adroitcreations-rmagent-yorke.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: adroitcreations-elementtime-app-test
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "adroitcreations-elementtime-app-test" {
  bucket = "adroitcreations-elementtime-app-test-${var.environment}"

  tags = {
    Name        = "adroitcreations-elementtime-app-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "adroitcreations-elementtime-app-test"
  }
}

resource "aws_s3_bucket_versioning" "adroitcreations-elementtime-app-test" {
  bucket = aws_s3_bucket.adroitcreations-elementtime-app-test.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "adroitcreations-elementtime-app-test" {
  bucket = aws_s3_bucket.adroitcreations-elementtime-app-test.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "adroitcreations-elementtime-app-test" {
  bucket = aws_s3_bucket.adroitcreations-elementtime-app-test.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: adroitcreations-rmagent-mtbarker
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "adroitcreations-rmagent-mtbarker" {
  bucket = "adroitcreations-rmagent-mtbarker-${var.environment}"

  tags = {
    Name        = "adroitcreations-rmagent-mtbarker"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "adroitcreations-rmagent-mtbarker"
  }
}

resource "aws_s3_bucket_versioning" "adroitcreations-rmagent-mtbarker" {
  bucket = aws_s3_bucket.adroitcreations-rmagent-mtbarker.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "adroitcreations-rmagent-mtbarker" {
  bucket = aws_s3_bucket.adroitcreations-rmagent-mtbarker.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "adroitcreations-rmagent-mtbarker" {
  bucket = aws_s3_bucket.adroitcreations-rmagent-mtbarker.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: adroitcreations-elementtime-app-sb
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "adroitcreations-elementtime-app-sb" {
  bucket = "adroitcreations-elementtime-app-sb-${var.environment}"

  tags = {
    Name        = "adroitcreations-elementtime-app-sb"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "adroitcreations-elementtime-app-sb"
  }
}

resource "aws_s3_bucket_versioning" "adroitcreations-elementtime-app-sb" {
  bucket = aws_s3_bucket.adroitcreations-elementtime-app-sb.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "adroitcreations-elementtime-app-sb" {
  bucket = aws_s3_bucket.adroitcreations-elementtime-app-sb.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "adroitcreations-elementtime-app-sb" {
  bucket = aws_s3_bucket.adroitcreations-elementtime-app-sb.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: adroitcreations-elementtime-app-local-leo
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "adroitcreations-elementtime-app-local-leo" {
  bucket = "adroitcreations-elementtime-app-local-leo-${var.environment}"

  tags = {
    Name        = "adroitcreations-elementtime-app-local-leo"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "adroitcreations-elementtime-app-local-leo"
  }
}

resource "aws_s3_bucket_versioning" "adroitcreations-elementtime-app-local-leo" {
  bucket = aws_s3_bucket.adroitcreations-elementtime-app-local-leo.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "adroitcreations-elementtime-app-local-leo" {
  bucket = aws_s3_bucket.adroitcreations-elementtime-app-local-leo.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "adroitcreations-elementtime-app-local-leo" {
  bucket = aws_s3_bucket.adroitcreations-elementtime-app-local-leo.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: adroitcreations-elementstaff2-app-test
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "adroitcreations-elementstaff2-app-test" {
  bucket = "adroitcreations-elementstaff2-app-test-${var.environment}"

  tags = {
    Name        = "adroitcreations-elementstaff2-app-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "adroitcreations-elementstaff2-app-test"
  }
}

resource "aws_s3_bucket_versioning" "adroitcreations-elementstaff2-app-test" {
  bucket = aws_s3_bucket.adroitcreations-elementstaff2-app-test.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "adroitcreations-elementstaff2-app-test" {
  bucket = aws_s3_bucket.adroitcreations-elementstaff2-app-test.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "adroitcreations-elementstaff2-app-test" {
  bucket = aws_s3_bucket.adroitcreations-elementstaff2-app-test.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: adroitcreations-elementstaff-app-test
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "adroitcreations-elementstaff-app-test" {
  bucket = "adroitcreations-elementstaff-app-test-${var.environment}"

  tags = {
    Name        = "adroitcreations-elementstaff-app-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "adroitcreations-elementstaff-app-test"
  }
}

resource "aws_s3_bucket_versioning" "adroitcreations-elementstaff-app-test" {
  bucket = aws_s3_bucket.adroitcreations-elementstaff-app-test.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "adroitcreations-elementstaff-app-test" {
  bucket = aws_s3_bucket.adroitcreations-elementstaff-app-test.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "adroitcreations-elementstaff-app-test" {
  bucket = aws_s3_bucket.adroitcreations-elementstaff-app-test.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: adroitcreations-elementstaff2-app-pub-test
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "adroitcreations-elementstaff2-app-pub-test" {
  bucket = "adroitcreations-elementstaff2-app-pub-test-${var.environment}"

  tags = {
    Name        = "adroitcreations-elementstaff2-app-pub-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "adroitcreations-elementstaff2-app-pub-test"
  }
}

resource "aws_s3_bucket_versioning" "adroitcreations-elementstaff2-app-pub-test" {
  bucket = aws_s3_bucket.adroitcreations-elementstaff2-app-pub-test.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "adroitcreations-elementstaff2-app-pub-test" {
  bucket = aws_s3_bucket.adroitcreations-elementstaff2-app-pub-test.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: adroitcreations-elementstaff-app
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "adroitcreations-elementstaff-app" {
  bucket = "adroitcreations-elementstaff-app-${var.environment}"

  tags = {
    Name        = "adroitcreations-elementstaff-app"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "adroitcreations-elementstaff-app"
  }
}

resource "aws_s3_bucket_versioning" "adroitcreations-elementstaff-app" {
  bucket = aws_s3_bucket.adroitcreations-elementstaff-app.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "adroitcreations-elementstaff-app" {
  bucket = aws_s3_bucket.adroitcreations-elementstaff-app.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "adroitcreations-elementstaff-app" {
  bucket = aws_s3_bucket.adroitcreations-elementstaff-app.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: adroitcreations-elementstaff2-app-pub
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "adroitcreations-elementstaff2-app-pub" {
  bucket = "adroitcreations-elementstaff2-app-pub-${var.environment}"

  tags = {
    Name        = "adroitcreations-elementstaff2-app-pub"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "adroitcreations-elementstaff2-app-pub"
  }
}

resource "aws_s3_bucket_versioning" "adroitcreations-elementstaff2-app-pub" {
  bucket = aws_s3_bucket.adroitcreations-elementstaff2-app-pub.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "adroitcreations-elementstaff2-app-pub" {
  bucket = aws_s3_bucket.adroitcreations-elementstaff2-app-pub.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: adroitcreations-elementstaff2-app
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "adroitcreations-elementstaff2-app" {
  bucket = "adroitcreations-elementstaff2-app-${var.environment}"

  tags = {
    Name        = "adroitcreations-elementstaff2-app"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "adroitcreations-elementstaff2-app"
  }
}

resource "aws_s3_bucket_versioning" "adroitcreations-elementstaff2-app" {
  bucket = aws_s3_bucket.adroitcreations-elementstaff2-app.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "adroitcreations-elementstaff2-app" {
  bucket = aws_s3_bucket.adroitcreations-elementstaff2-app.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "adroitcreations-elementstaff2-app" {
  bucket = aws_s3_bucket.adroitcreations-elementstaff2-app.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: adroitcreations-codedeploy
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "adroitcreations-codedeploy" {
  bucket = "adroitcreations-codedeploy-${var.environment}"

  tags = {
    Name        = "adroitcreations-codedeploy"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "adroitcreations-codedeploy"
  }
}

resource "aws_s3_bucket_versioning" "adroitcreations-codedeploy" {
  bucket = aws_s3_bucket.adroitcreations-codedeploy.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "adroitcreations-codedeploy" {
  bucket = aws_s3_bucket.adroitcreations-codedeploy.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "adroitcreations-codedeploy" {
  bucket = aws_s3_bucket.adroitcreations-codedeploy.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: ac-terraform-prod-current
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-terraform-stage-current" {
  bucket = "ac-terraform-stage-current-${var.environment}"

  tags = {
    Name        = "ac-terraform-stage-current"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-terraform-prod-current"
    Cost Center = "Platform"
    environment = "stage-current"
  }
}

resource "aws_s3_bucket_versioning" "ac-terraform-stage-current" {
  bucket = aws_s3_bucket.ac-terraform-stage-current.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-terraform-stage-current" {
  bucket = aws_s3_bucket.ac-terraform-stage-current.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: ac-sms-daily-reports
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-sms-daily-reports" {
  bucket = "ac-sms-daily-reports-${var.environment}"

  tags = {
    Name        = "ac-sms-daily-reports"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-sms-daily-reports"
  }
}

resource "aws_s3_bucket_versioning" "ac-sms-daily-reports" {
  bucket = aws_s3_bucket.ac-sms-daily-reports.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-sms-daily-reports" {
  bucket = aws_s3_bucket.ac-sms-daily-reports.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "ac-sms-daily-reports" {
  bucket = aws_s3_bucket.ac-sms-daily-reports.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: ac-terraform-prod
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-terraform-stage" {
  bucket = "ac-terraform-stage-${var.environment}"

  tags = {
    Name        = "ac-terraform-prod"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-terraform-prod"
    Cost Center = "Platform"
    Environment = "stage"
  }
}

resource "aws_s3_bucket_versioning" "ac-terraform-stage" {
  bucket = aws_s3_bucket.ac-terraform-stage.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-terraform-stage" {
  bucket = aws_s3_bucket.ac-terraform-stage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "ac-terraform-stage" {
  bucket = aws_s3_bucket.ac-terraform-stage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: ac-terraform-ci
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-terraform-ci" {
  bucket = "ac-terraform-ci-${var.environment}"

  tags = {
    Name        = "ac-terraform-ci"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-terraform-ci"
    Cost Center = "Platform"
    environment = "stage"
  }
}

resource "aws_s3_bucket_versioning" "ac-terraform-ci" {
  bucket = aws_s3_bucket.ac-terraform-ci.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-terraform-ci" {
  bucket = aws_s3_bucket.ac-terraform-ci.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: ac-soc-s3-bucket-server-access-logging
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-soc-s3-bucket-server-access-logging" {
  bucket = "ac-soc-s3-bucket-server-access-logging-${var.environment}"

  tags = {
    Name        = "ac-soc-s3-bucket-server-access-logging"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-soc-s3-bucket-server-access-logging"
    Cost Center = "platform"
    environment = "staging"
  }
}

resource "aws_s3_bucket_versioning" "ac-soc-s3-bucket-server-access-logging" {
  bucket = aws_s3_bucket.ac-soc-s3-bucket-server-access-logging.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-soc-s3-bucket-server-access-logging" {
  bucket = aws_s3_bucket.ac-soc-s3-bucket-server-access-logging.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "ac-soc-s3-bucket-server-access-logging" {
  bucket = aws_s3_bucket.ac-soc-s3-bucket-server-access-logging.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: ac-secrets-prod
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-secrets-stage" {
  bucket = "ac-secrets-stage-${var.environment}"

  tags = {
    Name        = "ac-secrets-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-secrets-prod"
    Cost Center = "Platform"
    environment = "staging"
  }
}

resource "aws_s3_bucket_versioning" "ac-secrets-stage" {
  bucket = aws_s3_bucket.ac-secrets-stage.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-secrets-stage" {
  bucket = aws_s3_bucket.ac-secrets-stage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: ac-platform-secure-prod-current
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-platform-secure-stage-current" {
  bucket = "ac-platform-secure-stage-current-${var.environment}"

  tags = {
    Name        = "ac-platform-secure-prod-current"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-platform-secure-prod-current"
    Cost Center = "Platform"
    Project Team = "Platform"
    environment = "stage-current"
  }
}

resource "aws_s3_bucket_versioning" "ac-platform-secure-stage-current" {
  bucket = aws_s3_bucket.ac-platform-secure-stage-current.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-platform-secure-stage-current" {
  bucket = aws_s3_bucket.ac-platform-secure-stage-current.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: ac-share-int-prod
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-share-int-stage" {
  bucket = "ac-share-int-stage-${var.environment}"

  tags = {
    Name        = "ac-share-int-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-share-int-prod"
    Cost Center = "Platform"
    environment = "staging"
  }
}

resource "aws_s3_bucket_versioning" "ac-share-int-stage" {
  bucket = aws_s3_bucket.ac-share-int-stage.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-share-int-stage" {
  bucket = aws_s3_bucket.ac-share-int-stage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "ac-share-int-stage" {
  bucket = aws_s3_bucket.ac-share-int-stage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: ac-platform-secure-prod
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-platform-secure-stage" {
  bucket = "ac-platform-secure-stage-${var.environment}"

  tags = {
    Name        = "ac-platform-secure-prod"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-platform-secure-prod"
    Cost Center = "Platform"
    Project Team = "Platform"
    environment = "stage"
  }
}

resource "aws_s3_bucket_versioning" "ac-platform-secure-stage" {
  bucket = aws_s3_bucket.ac-platform-secure-stage.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-platform-secure-stage" {
  bucket = aws_s3_bucket.ac-platform-secure-stage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: ac-eorg-edrms-integ-leeton
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-eorg-edrms-integ-leeton" {
  bucket = "ac-eorg-edrms-integ-leeton-${var.environment}"

  tags = {
    Name        = "ac-eorg-edrms-integ-leeton"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-eorg-edrms-integ-leeton"
    Cost Center = "elementOrg"
    environment = "stage"
  }
}

resource "aws_s3_bucket_versioning" "ac-eorg-edrms-integ-leeton" {
  bucket = aws_s3_bucket.ac-eorg-edrms-integ-leeton.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-eorg-edrms-integ-leeton" {
  bucket = aws_s3_bucket.ac-eorg-edrms-integ-leeton.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: ac-platform-lambdas
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-platform-lambdas" {
  bucket = "ac-platform-lambdas-${var.environment}"

  tags = {
    Name        = "ac-platform-lambdas"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-platform-lambdas"
    Cost Center = "Platform"
    environment = "staging"
  }
}

resource "aws_s3_bucket_versioning" "ac-platform-lambdas" {
  bucket = aws_s3_bucket.ac-platform-lambdas.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-platform-lambdas" {
  bucket = aws_s3_bucket.ac-platform-lambdas.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: ac-platform-lambdas-stage
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-platform-lambdas-stage" {
  bucket = "ac-platform-lambdas-stage-${var.environment}"

  tags = {
    Name        = "ac-platform-lambdas-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-platform-lambdas-stage"
    Cost Center = "Platform"
    environment = "staging"
  }
}

resource "aws_s3_bucket_versioning" "ac-platform-lambdas-stage" {
  bucket = aws_s3_bucket.ac-platform-lambdas-stage.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-platform-lambdas-stage" {
  bucket = aws_s3_bucket.ac-platform-lambdas-stage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "ac-platform-lambdas-stage" {
  bucket = aws_s3_bucket.ac-platform-lambdas-stage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: ac-backup-corner-prod
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-backup-corner-stage" {
  bucket = "ac-backup-corner-stage-${var.environment}"

  tags = {
    Name        = "ac-backup-corner-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-backup-corner-prod"
    Cost Center = "Platform"
    environment = "staging"
  }
}

resource "aws_s3_bucket_versioning" "ac-backup-corner-stage" {
  bucket = aws_s3_bucket.ac-backup-corner-stage.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-backup-corner-stage" {
  bucket = aws_s3_bucket.ac-backup-corner-stage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: ac-platform-lambdas-test
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-platform-lambdas-test" {
  bucket = "ac-platform-lambdas-test-${var.environment}"

  tags = {
    Name        = "ac-platform-lambdas-test"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-platform-lambdas-test"
    Cost Center = "Platform"
    environment = "staging"
  }
}

resource "aws_s3_bucket_versioning" "ac-platform-lambdas-test" {
  bucket = aws_s3_bucket.ac-platform-lambdas-test.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-platform-lambdas-test" {
  bucket = aws_s3_bucket.ac-platform-lambdas-test.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "ac-platform-lambdas-test" {
  bucket = aws_s3_bucket.ac-platform-lambdas-test.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: ac-platform-secure
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-platform-secure" {
  bucket = "ac-platform-secure-${var.environment}"

  tags = {
    Name        = "ac-platform-secure"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-platform-secure"
    Cost Center = "Platform"
    Project Team = "Platform"
    environment = "staging"
  }
}

resource "aws_s3_bucket_versioning" "ac-platform-secure" {
  bucket = aws_s3_bucket.ac-platform-secure.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-platform-secure" {
  bucket = aws_s3_bucket.ac-platform-secure.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: ac-lb-logs
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "S3_bucket_for_load_balancing_logs" {
  bucket = "ac-lb-logs-${var.environment}"

  tags = {
    Name        = "S3 bucket for load balancing logs"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-lb-logs"
    Cost Center = "Platform"
    Environment = "staging"
  }
}

resource "aws_s3_bucket_versioning" "S3_bucket_for_load_balancing_logs" {
  bucket = aws_s3_bucket.S3_bucket_for_load_balancing_logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "S3_bucket_for_load_balancing_logs" {
  bucket = aws_s3_bucket.S3_bucket_for_load_balancing_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: ac-flowlogs-vpc-prod
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-flowlogs-vpc-stage" {
  bucket = "ac-flowlogs-vpc-stage-${var.environment}"

  tags = {
    Name        = "ac-flowlogs-vpc-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-flowlogs-vpc-prod"
    Cost Center = "platform"
    Environment = "stage"
    Purpose = "Network Security Audit"
    Terraform = "true"
  }
}

resource "aws_s3_bucket_versioning" "ac-flowlogs-vpc-stage" {
  bucket = aws_s3_bucket.ac-flowlogs-vpc-stage.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-flowlogs-vpc-stage" {
  bucket = aws_s3_bucket.ac-flowlogs-vpc-stage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "ac-flowlogs-vpc-stage" {
  bucket = aws_s3_bucket.ac-flowlogs-vpc-stage.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: ac-elementtime-prod-current
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-elementtime-stage-current" {
  bucket = "ac-elementtime-stage-current-${var.environment}"

  tags = {
    Name        = "ac-elementtime-stage-current"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-elementtime-prod-current"
    Cost Center = "elementTIME"
    environment = "stage-current"
  }
}

resource "aws_s3_bucket_versioning" "ac-elementtime-stage-current" {
  bucket = aws_s3_bucket.ac-elementtime-stage-current.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-elementtime-stage-current" {
  bucket = aws_s3_bucket.ac-elementtime-stage-current.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: ac-eorg-edrms-integ-griffith
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-eorg-edrms-integ-griffith" {
  bucket = "ac-eorg-edrms-integ-griffith-${var.environment}"

  tags = {
    Name        = "ac-eorg-edrms-integ-griffith"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-eorg-edrms-integ-griffith"
    Cost Center = "elementOrg"
    environment = "stage"
  }
}

resource "aws_s3_bucket_versioning" "ac-eorg-edrms-integ-griffith" {
  bucket = aws_s3_bucket.ac-eorg-edrms-integ-griffith.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-eorg-edrms-integ-griffith" {
  bucket = aws_s3_bucket.ac-eorg-edrms-integ-griffith.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "ac-eorg-edrms-integ-griffith" {
  bucket = aws_s3_bucket.ac-eorg-edrms-integ-griffith.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


# S3 Bucket: ac-build-ci
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-build-ci" {
  bucket = "ac-build-ci-${var.environment}"

  tags = {
    Name        = "ac-build-ci"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-build-ci"
    Stage = "build"
    Namespace = "ac"
  }
}

resource "aws_s3_bucket_versioning" "ac-build-ci" {
  bucket = aws_s3_bucket.ac-build-ci.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-build-ci" {
  bucket = aws_s3_bucket.ac-build-ci.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: ac-build-artifacts
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-build-artifacts" {
  bucket = "ac-build-artifacts-${var.environment}"

  tags = {
    Name        = "ac-build-artifacts"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-build-artifacts"
    Cost Center = "Platform"
    environment = "staging"
  }
}

resource "aws_s3_bucket_versioning" "ac-build-artifacts" {
  bucket = aws_s3_bucket.ac-build-artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-build-artifacts" {
  bucket = aws_s3_bucket.ac-build-artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: ac-elementorg-prod
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-elementorg-stage" {
  bucket = "ac-elementorg-stage-${var.environment}"

  tags = {
    Name        = "ac-elementorg-stage"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-elementorg-prod"
    Cost Center = "elementOrg"
    environment = "stage"
  }
}

resource "aws_s3_bucket_versioning" "ac-elementorg-stage" {
  bucket = aws_s3_bucket.ac-elementorg-stage.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-elementorg-stage" {
  bucket = aws_s3_bucket.ac-elementorg-stage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: ac-elementorg-prod-current
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-elementorg-stage-current" {
  bucket = "ac-elementorg-stage-current-${var.environment}"

  tags = {
    Name        = "ac-elementorg-stage-current"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-elementorg-prod-current"
    Cost Center = "elementOrg"
    environment = "stage-current"
  }
}

resource "aws_s3_bucket_versioning" "ac-elementorg-stage-current" {
  bucket = aws_s3_bucket.ac-elementorg-stage-current.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-elementorg-stage-current" {
  bucket = aws_s3_bucket.ac-elementorg-stage-current.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket: ac-build-ci-build-ntpqiylzwtlk
# Note: S3 bucket names must be globally unique - consider adding a suffix
resource "aws_s3_bucket" "ac-build-ci-build" {
  bucket = "ac-build-ci-build-ntpqiylzwtlk-${var.environment}"

  tags = {
    Name        = "ac-build-ci-build"
    Environment = var.environment
    ManagedBy   = "replimap"
    SourceId    = "ac-build-ci-build-ntpqiylzwtlk"
    Attributes = "build"
    Stage = "build"
    Namespace = "ac"
  }
}

resource "aws_s3_bucket_versioning" "ac-build-ci-build" {
  bucket = aws_s3_bucket.ac-build-ci-build.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ac-build-ci-build" {
  bucket = aws_s3_bucket.ac-build-ci-build.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}



# S3 Bucket Policy: testmountbarker.elementrec.com
resource "aws_s3_bucket_policy" "testmountbarker_elementrec_com-policy" {
  bucket = aws_s3_bucket.testmountbarker_elementrec_com.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::testmountbarker.elementrec.com/*", "arn:aws:s3:::testmountbarker.elementrec.com"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: tenant.elementstaff.com
resource "aws_s3_bucket_policy" "tenant_elementstaff_com-policy" {
  bucket = aws_s3_bucket.tenant_elementstaff_com.id

  policy = jsonencode({"Statement": [{"Action": "s3:GetObject", "Effect": "Allow", "Principal": "*", "Resource": "arn:aws:s3:::tenant.elementstaff.com/*", "Sid": "PublicReadGetObject"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: zzz-leo-sync
resource "aws_s3_bucket_policy" "zzz-leo-sync-policy" {
  bucket = aws_s3_bucket.zzz-leo-sync.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::zzz-leo-sync/*", "arn:aws:s3:::zzz-leo-sync"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: tenant.elementstaff.test
resource "aws_s3_bucket_policy" "tenant_elementstaff_test-policy" {
  bucket = aws_s3_bucket.tenant_elementstaff_test.id

  policy = jsonencode({"Statement": [{"Action": "s3:GetObject", "Effect": "Allow", "Principal": "*", "Resource": "arn:aws:s3:::tenant.elementstaff.test/*", "Sid": "PublicReadGetObject"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: it-lambdas-sydney
resource "aws_s3_bucket_policy" "it-lambdas-sydney-policy" {
  bucket = aws_s3_bucket.it-lambdas-sydney.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::it-lambdas-sydney/*", "arn:aws:s3:::it-lambdas-sydney"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: stackset-aws-cost-report-pipelinebuiltartifactbuc-kvq8cnzxdzxw
resource "aws_s3_bucket_policy" "stackset-aws-cost-report-pipelinebuiltartifactbuc-kvq8cnzxdzxw-policy" {
  bucket = aws_s3_bucket.stackset-aws-cost-report-pipelinebuiltartifactbuc-kvq8cnzxdzxw.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::${var.aws_account_id}:root"}, "Resource": ["arn:aws:s3:::stackset-aws-cost-report-pipelinebuiltartifactbuc-kvq8cnzxdzxw", "arn:aws:s3:::stackset-aws-cost-report-pipelinebuiltartifactbuc-kvq8cnzxdzxw/*"]}, {"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::stackset-aws-cost-report-pipelinebuiltartifactbuc-kvq8cnzxdzxw/*", "arn:aws:s3:::stackset-aws-cost-report-pipelinebuiltartifactbuc-kvq8cnzxdzxw"], "Sid": "DenyInsecureConnections"}], "Version": "2008-10-17"})
}

# S3 Bucket Policy: remediate-athena-542859091916-ap-southeast-2
resource "aws_s3_bucket_policy" "remediate-athena-542859091916-ap-southeast-2-policy" {
  bucket = aws_s3_bucket.remediate-athena-542859091916-ap-southeast-2.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::remediate-athena-542859091916-ap-southeast-2/*", "arn:aws:s3:::remediate-athena-542859091916-ap-southeast-2"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: stackset-sms-report-infr-pipelinebuiltartifactbuc-rn9wu063pnet
resource "aws_s3_bucket_policy" "stackset-sms-report-infr-pipelinebuiltartifactbuc-rn9wu063pnet-policy" {
  bucket = aws_s3_bucket.stackset-sms-report-infr-pipelinebuiltartifactbuc-rn9wu063pnet.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::${var.aws_account_id}:root"}, "Resource": ["arn:aws:s3:::stackset-sms-report-infr-pipelinebuiltartifactbuc-rn9wu063pnet", "arn:aws:s3:::stackset-sms-report-infr-pipelinebuiltartifactbuc-rn9wu063pnet/*"]}, {"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::stackset-sms-report-infr-pipelinebuiltartifactbuc-rn9wu063pnet/*", "arn:aws:s3:::stackset-sms-report-infr-pipelinebuiltartifactbuc-rn9wu063pnet"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: stackset-check-aws-ri-in-pipelinebuiltartifactbuc-15f1th9a68wi0
resource "aws_s3_bucket_policy" "stackset-check-aws-ri-in-pipelinebuiltartifactbuc-15f1th9a68wi0-policy" {
  bucket = aws_s3_bucket.stackset-check-aws-ri-in-pipelinebuiltartifactbuc-15f1th9a68wi0.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::${var.aws_account_id}:root"}, "Resource": ["arn:aws:s3:::stackset-check-aws-ri-in-pipelinebuiltartifactbuc-15f1th9a68wi0", "arn:aws:s3:::stackset-check-aws-ri-in-pipelinebuiltartifactbuc-15f1th9a68wi0/*"]}, {"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::stackset-check-aws-ri-in-pipelinebuiltartifactbuc-15f1th9a68wi0/*", "arn:aws:s3:::stackset-check-aws-ri-in-pipelinebuiltartifactbuc-15f1th9a68wi0"], "Sid": "DenyInsecureConnections"}], "Version": "2008-10-17"})
}

# S3 Bucket Policy: stackset-security-report-pipelinebuiltartifactbuc-rkmerabp656e
resource "aws_s3_bucket_policy" "stackset-security-report-pipelinebuiltartifactbuc-rkmerabp656e-policy" {
  bucket = aws_s3_bucket.stackset-security-report-pipelinebuiltartifactbuc-rkmerabp656e.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::${var.aws_account_id}:root"}, "Resource": ["arn:aws:s3:::stackset-security-report-pipelinebuiltartifactbuc-rkmerabp656e", "arn:aws:s3:::stackset-security-report-pipelinebuiltartifactbuc-rkmerabp656e/*"]}, {"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::stackset-security-report-pipelinebuiltartifactbuc-rkmerabp656e/*", "arn:aws:s3:::stackset-security-report-pipelinebuiltartifactbuc-rkmerabp656e"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: mountbarker.elementrec.com
resource "aws_s3_bucket_policy" "mountbarker_elementrec_com-policy" {
  bucket = aws_s3_bucket.mountbarker_elementrec_com.id

  policy = jsonencode({"Statement": [{"Action": "s3:GetObject", "Effect": "Allow", "Principal": "*", "Resource": "arn:aws:s3:::mountbarker.elementrec.com/*", "Sid": "PublicReadGetObject"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: elementrec-public-bucket
resource "aws_s3_bucket_policy" "elementrec-public-bucket-policy" {
  bucket = aws_s3_bucket.elementrec-public-bucket.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::elementrec-public-bucket/*", "arn:aws:s3:::elementrec-public-bucket"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: etime-face-auth-stage-face-images
resource "aws_s3_bucket_policy" "etime-face-auth-stage-face-images-policy" {
  bucket = aws_s3_bucket.etime-face-auth-stage-face-images.id

  policy = jsonencode({"Statement": [{"Action": "s3:PutObject", "Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::${var.aws_account_id}:root"}, "Resource": "arn:aws:s3:::etime-face-auth-prod-face-images/*", "Sid": "ELBRegionAp-Southeast-2"}, {"Action": "s3:PutObject", "Effect": "Allow", "Principal": {"Service": "logdelivery.elasticloadbalancing.amazonaws.com"}, "Resource": "arn:aws:s3:::etime-face-auth-prod-face-images/*"}, {"Action": "s3:PutObject", "Condition": {"StringEquals": {"s3:x-amz-acl": "bucket-owner-full-control"}}, "Effect": "Allow", "Principal": {"Service": "delivery.logs.amazonaws.com"}, "Resource": "arn:aws:s3:::etime-face-auth-prod-face-images/*", "Sid": "AlbNlbLogDeliveryWrite"}, {"Action": ["s3:ListBucket", "s3:GetBucketAcl"], "Effect": "Allow", "Principal": {"Service": "delivery.logs.amazonaws.com"}, "Resource": "arn:aws:s3:::etime-face-auth-prod-face-images", "Sid": "AlbNlbLogDeliveryAclCheck"}, {"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::etime-face-auth-prod-face-images/*", "arn:aws:s3:::etime-face-auth-prod-face-images"], "Sid": "denyInsecureTransport"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: elementtime-lambda-artifacts-stage
resource "aws_s3_bucket_policy" "elementtime-lambda-artifacts-stage-policy" {
  bucket = aws_s3_bucket.elementtime-lambda-artifacts-stage.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::elementtime-lambda-artifacts-prod/*", "arn:aws:s3:::elementtime-lambda-artifacts-prod"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: elementstaff
resource "aws_s3_bucket_policy" "elementstaff-policy" {
  bucket = aws_s3_bucket.elementstaff.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::elementstaff/*", "arn:aws:s3:::elementstaff"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: adroitcreations-trail-logs
resource "aws_s3_bucket_policy" "adroitcreations-trail-logs-policy" {
  bucket = aws_s3_bucket.adroitcreations-trail-logs.id

  policy = jsonencode({"Statement": [{"Action": "s3:GetBucketAcl", "Effect": "Allow", "Principal": {"Service": "cloudtrail.amazonaws.com"}, "Resource": "arn:aws:s3:::adroitcreations-trail-logs", "Sid": "AWSCloudTrailAclCheck20150319"}, {"Action": "s3:PutObject", "Condition": {"StringEquals": {"s3:x-amz-acl": "bucket-owner-full-control"}}, "Effect": "Allow", "Principal": {"Service": "cloudtrail.amazonaws.com"}, "Resource": "arn:aws:s3:::adroitcreations-trail-logs/AWSLogs/${var.aws_account_id}/*", "Sid": "AWSCloudTrailWrite20150319"}, {"Action": "s3:GetBucketAcl", "Condition": {"StringEquals": {"AWS:SourceArn": "arn:aws:cloudtrail:ap-southeast-2:${var.aws_account_id}:trail/Management"}}, "Effect": "Allow", "Principal": {"Service": "cloudtrail.amazonaws.com"}, "Resource": "arn:aws:s3:::adroitcreations-trail-logs", "Sid": "AWSCloudTrailAclCheck20150319-5d87583a-943b-49ed-b993-75ee278c9c74"}, {"Action": "s3:PutObject", "Condition": {"StringEquals": {"AWS:SourceArn": "arn:aws:cloudtrail:ap-southeast-2:${var.aws_account_id}:trail/Management", "s3:x-amz-acl": "bucket-owner-full-control"}}, "Effect": "Allow", "Principal": {"Service": "cloudtrail.amazonaws.com"}, "Resource": "arn:aws:s3:::adroitcreations-trail-logs/AWSLogs/${var.aws_account_id}/*", "Sid": "AWSCloudTrailWrite20150319-e8204bcb-0f5b-4ee3-aa6a-778a30d1dfd6"}, {"Action": ["s3:GetBucketLocation", "s3:ListBucket"], "Condition": {"StringEquals": {"AWS:SourceArn": "arn:aws:cloudtrail:ap-southeast-2:${var.aws_account_id}:trail/Management"}}, "Effect": "Allow", "Principal": {"Service": "cloudtrail.amazonaws.com"}, "Resource": "arn:aws:s3:::adroitcreations-trail-logs", "Sid": "AWSCloudTrailKMSAccess"}, {"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::adroitcreations-trail-logs/*", "arn:aws:s3:::adroitcreations-trail-logs"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: er-general-dev-leo
resource "aws_s3_bucket_policy" "er-general-dev-leo-policy" {
  bucket = aws_s3_bucket.er-general-dev-leo.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::er-general-dev-leo/*", "arn:aws:s3:::er-general-dev-leo"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: adroitcreations-elementtime-app
resource "aws_s3_bucket_policy" "adroitcreations-elementtime-app-policy" {
  bucket = aws_s3_bucket.adroitcreations-elementtime-app.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::adroitcreations-elementtime-app/*", "arn:aws:s3:::adroitcreations-elementtime-app"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: er-general
resource "aws_s3_bucket_policy" "er-general-policy" {
  bucket = aws_s3_bucket.er-general.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::er-general/*", "arn:aws:s3:::er-general"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: adroitcreations-yorke-intranet
resource "aws_s3_bucket_policy" "adroitcreations-yorke-intranet-policy" {
  bucket = aws_s3_bucket.adroitcreations-yorke-intranet.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::adroitcreations-yorke-intranet/*", "arn:aws:s3:::adroitcreations-yorke-intranet"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: elementrec-mountbarker
resource "aws_s3_bucket_policy" "elementrec-mountbarker-policy" {
  bucket = aws_s3_bucket.elementrec-mountbarker.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::elementrec-mountbarker/*", "arn:aws:s3:::elementrec-mountbarker"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: codepipeline-ap-southeast-2-224625540070
resource "aws_s3_bucket_policy" "codepipeline-ap-southeast-2-224625540070-policy" {
  bucket = aws_s3_bucket.codepipeline-ap-southeast-2-224625540070.id

  policy = jsonencode({"Id": "SSEAndSSLPolicy", "Statement": [{"Action": "s3:PutObject", "Condition": {"StringNotEquals": {"s3:x-amz-server-side-encryption": "aws:kms"}}, "Effect": "Deny", "Principal": "*", "Resource": "arn:aws:s3:::codepipeline-ap-southeast-2-224625540070/*", "Sid": "DenyUnEncryptedObjectUploads"}, {"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": "arn:aws:s3:::codepipeline-ap-southeast-2-224625540070/*", "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: elementrec-mountbarker-test
resource "aws_s3_bucket_policy" "elementrec-mountbarker-test-policy" {
  bucket = aws_s3_bucket.elementrec-mountbarker-test.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::elementrec-mountbarker-test/*", "arn:aws:s3:::elementrec-mountbarker-test"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: adroitcreations-yorke-website
resource "aws_s3_bucket_policy" "adroitcreations-yorke-website-policy" {
  bucket = aws_s3_bucket.adroitcreations-yorke-website.id

  policy = jsonencode({"Id": "Policy1546414473940", "Statement": [{"Action": "s3:ListBucket", "Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::${var.aws_account_id}:user/yorkeweb-pit-store"}, "Resource": "arn:aws:s3:::adroitcreations-yorke-website", "Sid": "Stmt1546414471931"}, {"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::adroitcreations-yorke-website/*", "arn:aws:s3:::adroitcreations-yorke-website"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: aws-athena-query-results-542859091916-ap-southeast-2
resource "aws_s3_bucket_policy" "aws-athena-query-results-542859091916-ap-southeast-2-policy" {
  bucket = aws_s3_bucket.aws-athena-query-results-542859091916-ap-southeast-2.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::aws-athena-query-results-542859091916-ap-southeast-2/*", "arn:aws:s3:::aws-athena-query-results-542859091916-ap-southeast-2"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: adroitcreations-rmagent-ngsc
resource "aws_s3_bucket_policy" "adroitcreations-rmagent-ngsc-policy" {
  bucket = aws_s3_bucket.adroitcreations-rmagent-ngsc.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::adroitcreations-rmagent-ngsc/*", "arn:aws:s3:::adroitcreations-rmagent-ngsc"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: adroitcreations-logs
resource "aws_s3_bucket_policy" "adroitcreations-logs-policy" {
  bucket = aws_s3_bucket.adroitcreations-logs.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::adroitcreations-logs/*", "arn:aws:s3:::adroitcreations-logs"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: adroitcreations-rmagent-yorke
resource "aws_s3_bucket_policy" "adroitcreations-rmagent-yorke-policy" {
  bucket = aws_s3_bucket.adroitcreations-rmagent-yorke.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::adroitcreations-rmagent-yorke/*", "arn:aws:s3:::adroitcreations-rmagent-yorke"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: adroitcreations-elementtime-app-test
resource "aws_s3_bucket_policy" "adroitcreations-elementtime-app-test-policy" {
  bucket = aws_s3_bucket.adroitcreations-elementtime-app-test.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::adroitcreations-elementtime-app-test/*", "arn:aws:s3:::adroitcreations-elementtime-app-test"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: adroitcreations-rmagent-mtbarker
resource "aws_s3_bucket_policy" "adroitcreations-rmagent-mtbarker-policy" {
  bucket = aws_s3_bucket.adroitcreations-rmagent-mtbarker.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::adroitcreations-rmagent-mtbarker/*", "arn:aws:s3:::adroitcreations-rmagent-mtbarker"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: adroitcreations-elementtime-app-sb
resource "aws_s3_bucket_policy" "adroitcreations-elementtime-app-sb-policy" {
  bucket = aws_s3_bucket.adroitcreations-elementtime-app-sb.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::adroitcreations-elementtime-app-sb/*", "arn:aws:s3:::adroitcreations-elementtime-app-sb"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: adroitcreations-elementtime-app-local-leo
resource "aws_s3_bucket_policy" "adroitcreations-elementtime-app-local-leo-policy" {
  bucket = aws_s3_bucket.adroitcreations-elementtime-app-local-leo.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::adroitcreations-elementtime-app-local-leo/*", "arn:aws:s3:::adroitcreations-elementtime-app-local-leo"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: adroitcreations-elementstaff2-app-test
resource "aws_s3_bucket_policy" "adroitcreations-elementstaff2-app-test-policy" {
  bucket = aws_s3_bucket.adroitcreations-elementstaff2-app-test.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::adroitcreations-elementstaff2-app-test/*", "arn:aws:s3:::adroitcreations-elementstaff2-app-test"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: adroitcreations-elementstaff-app-test
resource "aws_s3_bucket_policy" "adroitcreations-elementstaff-app-test-policy" {
  bucket = aws_s3_bucket.adroitcreations-elementstaff-app-test.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::adroitcreations-elementstaff-app-test/*", "arn:aws:s3:::adroitcreations-elementstaff-app-test"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: adroitcreations-elementstaff2-app-pub-test
resource "aws_s3_bucket_policy" "adroitcreations-elementstaff2-app-pub-test-policy" {
  bucket = aws_s3_bucket.adroitcreations-elementstaff2-app-pub-test.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::adroitcreations-elementstaff2-app-pub-test/*", "arn:aws:s3:::adroitcreations-elementstaff2-app-pub-test"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: adroitcreations-elementstaff-app
resource "aws_s3_bucket_policy" "adroitcreations-elementstaff-app-policy" {
  bucket = aws_s3_bucket.adroitcreations-elementstaff-app.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::adroitcreations-elementstaff-app/*", "arn:aws:s3:::adroitcreations-elementstaff-app"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: adroitcreations-elementstaff2-app-pub
resource "aws_s3_bucket_policy" "adroitcreations-elementstaff2-app-pub-policy" {
  bucket = aws_s3_bucket.adroitcreations-elementstaff2-app-pub.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::adroitcreations-elementstaff2-app-pub/*", "arn:aws:s3:::adroitcreations-elementstaff2-app-pub"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: adroitcreations-elementstaff2-app
resource "aws_s3_bucket_policy" "adroitcreations-elementstaff2-app-policy" {
  bucket = aws_s3_bucket.adroitcreations-elementstaff2-app.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::adroitcreations-elementstaff2-app/*", "arn:aws:s3:::adroitcreations-elementstaff2-app"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: adroitcreations-codedeploy
resource "aws_s3_bucket_policy" "adroitcreations-codedeploy-policy" {
  bucket = aws_s3_bucket.adroitcreations-codedeploy.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::adroitcreations-codedeploy/*", "arn:aws:s3:::adroitcreations-codedeploy"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-terraform-stage-current
resource "aws_s3_bucket_policy" "ac-terraform-stage-current-policy" {
  bucket = aws_s3_bucket.ac-terraform-stage-current.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-terraform-prod-current/*", "arn:aws:s3:::ac-terraform-prod-current"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-sms-daily-reports
resource "aws_s3_bucket_policy" "ac-sms-daily-reports-policy" {
  bucket = aws_s3_bucket.ac-sms-daily-reports.id

  policy = jsonencode({"Statement": [{"Action": "s3:PutObject", "Condition": {"ArnLike": {"aws:SourceArn": "arn:aws:sns:ap-southeast-2:${var.aws_account_id}:*"}, "StringEquals": {"aws:SourceAccount": "${var.aws_account_id}"}}, "Effect": "Allow", "Principal": {"Service": "sns.amazonaws.com"}, "Resource": "arn:aws:s3:::ac-sms-daily-reports/*", "Sid": "AllowPutObject"}, {"Action": "s3:GetBucketLocation", "Condition": {"ArnLike": {"aws:SourceArn": "arn:aws:sns:ap-southeast-2:${var.aws_account_id}:*"}, "StringEquals": {"aws:SourceAccount": "${var.aws_account_id}"}}, "Effect": "Allow", "Principal": {"Service": "sns.amazonaws.com"}, "Resource": "arn:aws:s3:::ac-sms-daily-reports", "Sid": "AllowGetBucketLocation"}, {"Action": "s3:ListBucket", "Condition": {"ArnLike": {"aws:SourceArn": "arn:aws:sns:ap-southeast-2:${var.aws_account_id}:*"}, "StringEquals": {"aws:SourceAccount": "${var.aws_account_id}"}}, "Effect": "Allow", "Principal": {"Service": "sns.amazonaws.com"}, "Resource": "arn:aws:s3:::ac-sms-daily-reports", "Sid": "AllowListBucket"}, {"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-sms-daily-reports/*", "arn:aws:s3:::ac-sms-daily-reports"], "Sid": "DenyInsecureConnections"}], "Version": "2008-10-17"})
}

# S3 Bucket Policy: ac-terraform-stage
resource "aws_s3_bucket_policy" "ac-terraform-stage-policy" {
  bucket = aws_s3_bucket.ac-terraform-stage.id

  policy = jsonencode({"Statement": [{"Action": ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"], "Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::${var.aws_account_id}:role/privileged-admin"}, "Resource": "arn:aws:s3:::ac-terraform-prod/*", "Sid": "AllowTerraformAdminRoleAccess"}, {"Action": "s3:ListBucket", "Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::${var.aws_account_id}:role/privileged-admin"}, "Resource": "arn:aws:s3:::ac-terraform-prod", "Sid": "AllowTerraformAdminRoleList"}, {"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-terraform-prod/*", "arn:aws:s3:::ac-terraform-prod"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-terraform-ci
resource "aws_s3_bucket_policy" "ac-terraform-ci-policy" {
  bucket = aws_s3_bucket.ac-terraform-ci.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-terraform-ci/*", "arn:aws:s3:::ac-terraform-ci"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-soc-s3-bucket-server-access-logging
resource "aws_s3_bucket_policy" "ac-soc-s3-bucket-server-access-logging-policy" {
  bucket = aws_s3_bucket.ac-soc-s3-bucket-server-access-logging.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-soc-s3-bucket-server-access-logging/*", "arn:aws:s3:::ac-soc-s3-bucket-server-access-logging"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-secrets-stage
resource "aws_s3_bucket_policy" "ac-secrets-stage-policy" {
  bucket = aws_s3_bucket.ac-secrets-stage.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-secrets-prod/*", "arn:aws:s3:::ac-secrets-prod"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-platform-secure-stage-current
resource "aws_s3_bucket_policy" "ac-platform-secure-stage-current-policy" {
  bucket = aws_s3_bucket.ac-platform-secure-stage-current.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-platform-secure-prod-current/*", "arn:aws:s3:::ac-platform-secure-prod-current"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-share-int-stage
resource "aws_s3_bucket_policy" "ac-share-int-stage-policy" {
  bucket = aws_s3_bucket.ac-share-int-stage.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::${var.aws_account_id}:user/leo"}, "Resource": ["arn:aws:s3:::ac-share-int-prod", "arn:aws:s3:::ac-share-int-prod/*"]}, {"Action": ["s3:Get*", "s3:List*"], "Effect": "Allow", "Principal": {"AWS": ["arn:aws:iam::${var.aws_account_id}:user/david.lu", "arn:aws:iam::${var.aws_account_id}:user/isaac.santos", "arn:aws:iam::${var.aws_account_id}:user/matheus.mei", "arn:aws:iam::${var.aws_account_id}:user/rafael"]}, "Resource": ["arn:aws:s3:::ac-share-int-prod", "arn:aws:s3:::ac-share-int-prod/*"]}, {"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-share-int-prod/*", "arn:aws:s3:::ac-share-int-prod"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-platform-secure-stage
resource "aws_s3_bucket_policy" "ac-platform-secure-stage-policy" {
  bucket = aws_s3_bucket.ac-platform-secure-stage.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-platform-secure-prod/*", "arn:aws:s3:::ac-platform-secure-prod"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-eorg-edrms-integ-leeton
resource "aws_s3_bucket_policy" "ac-eorg-edrms-integ-leeton-policy" {
  bucket = aws_s3_bucket.ac-eorg-edrms-integ-leeton.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-eorg-edrms-integ-leeton/*", "arn:aws:s3:::ac-eorg-edrms-integ-leeton"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-platform-lambdas
resource "aws_s3_bucket_policy" "ac-platform-lambdas-policy" {
  bucket = aws_s3_bucket.ac-platform-lambdas.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-platform-lambdas/*", "arn:aws:s3:::ac-platform-lambdas"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-platform-lambdas-stage
resource "aws_s3_bucket_policy" "ac-platform-lambdas-stage-policy" {
  bucket = aws_s3_bucket.ac-platform-lambdas-stage.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-platform-lambdas-stage/*", "arn:aws:s3:::ac-platform-lambdas-stage"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-backup-corner-stage
resource "aws_s3_bucket_policy" "ac-backup-corner-stage-policy" {
  bucket = aws_s3_bucket.ac-backup-corner-stage.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-backup-corner-prod/*", "arn:aws:s3:::ac-backup-corner-prod"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-platform-lambdas-test
resource "aws_s3_bucket_policy" "ac-platform-lambdas-test-policy" {
  bucket = aws_s3_bucket.ac-platform-lambdas-test.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-platform-lambdas-test/*", "arn:aws:s3:::ac-platform-lambdas-test"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-platform-secure
resource "aws_s3_bucket_policy" "ac-platform-secure-policy" {
  bucket = aws_s3_bucket.ac-platform-secure.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-platform-secure/*", "arn:aws:s3:::ac-platform-secure"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-lb-logs
resource "aws_s3_bucket_policy" "ac-lb-logs-policy" {
  bucket = aws_s3_bucket.ac-lb-logs.id

  policy = jsonencode({"Statement": [{"Action": "s3:PutObject", "Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::${var.aws_account_id}:root"}, "Resource": "arn:aws:s3:::ac-lb-logs/*"}, {"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-lb-logs", "arn:aws:s3:::ac-lb-logs/*"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-flowlogs-vpc-stage
resource "aws_s3_bucket_policy" "ac-flowlogs-vpc-stage-policy" {
  bucket = aws_s3_bucket.ac-flowlogs-vpc-stage.id

  policy = jsonencode({"Statement": [{"Action": "s3:PutObject", "Effect": "Allow", "Principal": {"AWS": "arn:aws:iam::${var.aws_account_id}:root"}, "Resource": "arn:aws:s3:::ac-flowlogs-vpc-prod/*", "Sid": "ELBRegionAp-Southeast-2"}, {"Action": "s3:PutObject", "Effect": "Allow", "Principal": {"Service": "logdelivery.elasticloadbalancing.amazonaws.com"}, "Resource": "arn:aws:s3:::ac-flowlogs-vpc-prod/*"}, {"Action": "s3:PutObject", "Condition": {"StringEquals": {"s3:x-amz-acl": "bucket-owner-full-control"}}, "Effect": "Allow", "Principal": {"Service": "delivery.logs.amazonaws.com"}, "Resource": "arn:aws:s3:::ac-flowlogs-vpc-prod/*", "Sid": "AlbNlbLogDeliveryWrite"}, {"Action": ["s3:ListBucket", "s3:GetBucketAcl"], "Effect": "Allow", "Principal": {"Service": "delivery.logs.amazonaws.com"}, "Resource": "arn:aws:s3:::ac-flowlogs-vpc-prod", "Sid": "AlbNlbLogDeliveryAclCheck"}, {"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-flowlogs-vpc-prod/*", "arn:aws:s3:::ac-flowlogs-vpc-prod"], "Sid": "denyInsecureTransport"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-elementtime-stage-current
resource "aws_s3_bucket_policy" "ac-elementtime-stage-current-policy" {
  bucket = aws_s3_bucket.ac-elementtime-stage-current.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-elementtime-prod-current/*", "arn:aws:s3:::ac-elementtime-prod-current"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-eorg-edrms-integ-griffith
resource "aws_s3_bucket_policy" "ac-eorg-edrms-integ-griffith-policy" {
  bucket = aws_s3_bucket.ac-eorg-edrms-integ-griffith.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-eorg-edrms-integ-griffith/*", "arn:aws:s3:::ac-eorg-edrms-integ-griffith"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-build-ci
resource "aws_s3_bucket_policy" "ac-build-ci-policy" {
  bucket = aws_s3_bucket.ac-build-ci.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-build-ci/*", "arn:aws:s3:::ac-build-ci"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-build-artifacts
resource "aws_s3_bucket_policy" "ac-build-artifacts-policy" {
  bucket = aws_s3_bucket.ac-build-artifacts.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-build-artifacts/*", "arn:aws:s3:::ac-build-artifacts"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-elementorg-stage
resource "aws_s3_bucket_policy" "ac-elementorg-stage-policy" {
  bucket = aws_s3_bucket.ac-elementorg-stage.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-elementorg-prod/*", "arn:aws:s3:::ac-elementorg-prod"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-elementorg-stage-current
resource "aws_s3_bucket_policy" "ac-elementorg-stage-current-policy" {
  bucket = aws_s3_bucket.ac-elementorg-stage-current.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-elementorg-prod-current/*", "arn:aws:s3:::ac-elementorg-prod-current"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}

# S3 Bucket Policy: ac-build-ci-build-ntpqiylzwtlk
resource "aws_s3_bucket_policy" "ac-build-ci-build-ntpqiylzwtlk-policy" {
  bucket = aws_s3_bucket.ac-build-ci-build-ntpqiylzwtlk.id

  policy = jsonencode({"Statement": [{"Action": "s3:*", "Condition": {"Bool": {"aws:SecureTransport": "false"}}, "Effect": "Deny", "Principal": "*", "Resource": ["arn:aws:s3:::ac-build-ci-build-ntpqiylzwtlk/*", "arn:aws:s3:::ac-build-ci-build-ntpqiylzwtlk"], "Sid": "DenyInsecureConnections"}], "Version": "2012-10-17"})
}