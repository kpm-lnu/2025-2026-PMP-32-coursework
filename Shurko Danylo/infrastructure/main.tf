# ==========================================
# TERRAFORM & PROVIDER CONFIGURATION
# ==========================================
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "eu-north-1"

  default_tags {
    tags = {
      Project = "tech-skills-insights"
    }
  }
}

# ==========================================
# STORAGE (S3 & DynamoDB)
# ==========================================
resource "random_string" "bucket_suffix" {
  length  = 6
  special = false
  upper   = false
}

resource "aws_s3_bucket" "data_storage" {
  bucket = "tech-skills-insights-data-${random_string.bucket_suffix.result}"
}

resource "aws_s3_bucket_public_access_block" "data_storage_public_access" {
  bucket                  = aws_s3_bucket.data_storage.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_dynamodb_table" "state_table" {
  name           = "tech-skills-insights-state"
  billing_mode   = "PROVISIONED"
  read_capacity  = 5
  write_capacity = 5
  hash_key       = "Name"

  deletion_protection_enabled = true

  attribute {
    name = "Name"
    type = "S"
  }
}

# ==========================================
# MESSAGING (SQS)
# ==========================================
resource "aws_sqs_queue" "dou_urls_dlq" {
  name                       = "dou-urls-dlq"
  visibility_timeout_seconds = 30
  message_retention_seconds  = 1209600
}

resource "aws_sqs_queue" "dou_urls_queue" {
  name                       = "dou-urls-queue"
  visibility_timeout_seconds = 900
  message_retention_seconds  = 1209600
  receive_wait_time_seconds  = 20

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dou_urls_dlq.arn
    maxReceiveCount     = 3
  })
}

# ==========================================
# IAM ROLES & POLICIES
# ==========================================
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

data "aws_iam_policy" "lambda_basic_execution" {
  arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# 1. Dispatcher Role
resource "aws_iam_role" "dispatcher_role" {
  name               = "dispatcher-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "dispatcher_logs" {
  role       = aws_iam_role.dispatcher_role.name
  policy_arn = data.aws_iam_policy.lambda_basic_execution.arn
}

resource "aws_iam_role_policy" "dispatcher_policy" {
  name = "dispatcher-permissions"
  role = aws_iam_role.dispatcher_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Scan",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = aws_dynamodb_table.state_table.arn
      },
      {
        Effect   = "Allow"
        Action   = ["lambda:InvokeFunction"]
        Resource = aws_lambda_function.dou_producer.arn
      }
    ]
  })
}

# 2. Producer Role
resource "aws_iam_role" "producer_role" {
  name               = "producer-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "producer_logs" {
  role       = aws_iam_role.producer_role.name
  policy_arn = data.aws_iam_policy.lambda_basic_execution.arn
}

resource "aws_iam_role_policy" "producer_policy" {
  name = "producer-permissions"
  role = aws_iam_role.producer_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["sqs:SendMessage"]
      Resource = aws_sqs_queue.dou_urls_queue.arn
    }]
  })
}

# 3. Worker Role
resource "aws_iam_role" "worker_role" {
  name               = "worker-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "worker_logs" {
  role       = aws_iam_role.worker_role.name
  policy_arn = data.aws_iam_policy.lambda_basic_execution.arn
}

resource "aws_iam_role_policy" "worker_policy" {
  name = "worker-permissions"
  role = aws_iam_role.worker_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
        Resource = aws_sqs_queue.dou_urls_queue.arn
      },
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "${aws_s3_bucket.data_storage.arn}/*"
      }
    ]
  })
}

# 4. Aggregator Role
resource "aws_iam_role" "aggregator_role" {
  name               = "aggregator-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "aggregator_logs" {
  role       = aws_iam_role.aggregator_role.name
  policy_arn = data.aws_iam_policy.lambda_basic_execution.arn
}

resource "aws_iam_role_policy" "aggregator_policy" {
  name = "aggregator-permissions"
  role = aws_iam_role.aggregator_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject"]
        Resource = "${aws_s3_bucket.data_storage.arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = aws_s3_bucket.data_storage.arn
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Scan",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = aws_dynamodb_table.state_table.arn
      },
      {
        Effect   = "Allow"
        Action   = ["lambda:InvokeFunction"]
        Resource = aws_lambda_function.dou_aggregator.arn
      }
    ]
  })
}

# 5. Djinni Parser Role
resource "aws_iam_role" "djinni_parser_role" {
  name               = "djinni-parser-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json
}

resource "aws_iam_role_policy_attachment" "djinni_parser_logs" {
  role       = aws_iam_role.djinni_parser_role.name
  policy_arn = data.aws_iam_policy.lambda_basic_execution.arn
}

resource "aws_iam_role_policy" "djinni_parser_policy" {
  name = "djinni-parser-permissions"
  role = aws_iam_role.djinni_parser_role.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:PutObject"]
        Resource = "${aws_s3_bucket.data_storage.arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = aws_s3_bucket.data_storage.arn
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Scan",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = aws_dynamodb_table.state_table.arn
      }
    ]
  })
}

# 6. EventBridge Scheduler Role
resource "aws_iam_role" "scheduler_role" {
  name = "eventbridge-scheduler-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "scheduler.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "scheduler_lambda_invoke" {
  name = "scheduler-lambda-invoke"
  role = aws_iam_role.scheduler_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "lambda:InvokeFunction"
      Effect = "Allow"
      Resource = [
        aws_lambda_function.djinni_parser.arn,
        aws_lambda_function.dou_dispatcher.arn,
        aws_lambda_function.dou_aggregator.arn
      ]
    }]
  })
}

# ==========================================
# LAMBDA LAYERS
# ==========================================
data "archive_file" "scraping_layer_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../layers/scraping_layer"
  output_path = "${path.module}/../layers/scraping_layer.zip"
}

resource "aws_lambda_layer_version" "scraping_layer" {
  layer_name          = "scraping-dependencies"
  description         = "Layer with requests, beautifulsoup4, emoji, and s3fs"
  filename            = data.archive_file.scraping_layer_zip.output_path
  source_code_hash    = data.archive_file.scraping_layer_zip.output_base64sha256
  compatible_runtimes = ["python3.13"]
}

# ==========================================
# LAMBDA FUNCTIONS
# ==========================================

# 1. Dispatcher
data "archive_file" "dou_dispatcher_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambdas/dou/dou_dispatcher.py"
  output_path = "${path.module}/../lambdas/dou/dou_dispatcher.zip"
}

resource "aws_lambda_function" "dou_dispatcher" {
  function_name    = "dou-dispatcher"
  role             = aws_iam_role.dispatcher_role.arn
  handler          = "dou_dispatcher.lambda_handler"
  runtime          = "python3.13"
  timeout          = 900
  memory_size      = 128
  filename         = data.archive_file.dou_dispatcher_zip.output_path
  source_code_hash = data.archive_file.dou_dispatcher_zip.output_base64sha256

  environment {
    variables = {
      DYNAMODB_TABLE_NAME    = aws_dynamodb_table.state_table.name
      PRODUCER_FUNCTION_NAME = aws_lambda_function.dou_producer.function_name
    }
  }
}

# 2. Producer
data "archive_file" "dou_producer_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambdas/dou/dou_producer.py"
  output_path = "${path.module}/../lambdas/dou/dou_producer.zip"
}

resource "aws_lambda_function" "dou_producer" {
  function_name    = "dou-producer"
  role             = aws_iam_role.producer_role.arn
  handler          = "dou_producer.lambda_handler"
  runtime          = "python3.13"
  timeout          = 900
  memory_size      = 256
  filename         = data.archive_file.dou_producer_zip.output_path
  source_code_hash = data.archive_file.dou_producer_zip.output_base64sha256

  layers = [
    aws_lambda_layer_version.scraping_layer.arn
  ]

  environment {
    variables = {
      SQS_QUEUE_URL = aws_sqs_queue.dou_urls_queue.url
    }
  }
}

# 3. Worker
data "archive_file" "dou_worker_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambdas/dou/dou_worker.py"
  output_path = "${path.module}/../lambdas/dou/dou_worker.zip"
}

resource "aws_lambda_function" "dou_worker" {
  function_name    = "dou-worker"
  role             = aws_iam_role.worker_role.arn
  handler          = "dou_worker.lambda_handler"
  runtime          = "python3.13"
  timeout          = 180
  memory_size      = 256
  filename         = data.archive_file.dou_worker_zip.output_path
  source_code_hash = data.archive_file.dou_worker_zip.output_base64sha256

  layers = [
    aws_lambda_layer_version.scraping_layer.arn
  ]

  environment {
    variables = {
      S3_BUCKET_NAME = aws_s3_bucket.data_storage.bucket
    }
  }
}

# 4. Aggregator
data "archive_file" "dou_aggregator_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambdas/dou/dou_aggregator.py"
  output_path = "${path.module}/../lambdas/dou/dou_aggregator.zip"
}

resource "aws_lambda_function" "dou_aggregator" {
  function_name    = "dou-aggregator"
  role             = aws_iam_role.aggregator_role.arn
  handler          = "dou_aggregator.lambda_handler"
  runtime          = "python3.13"
  timeout          = 900
  memory_size      = 512
  filename         = data.archive_file.dou_aggregator_zip.output_path
  source_code_hash = data.archive_file.dou_aggregator_zip.output_base64sha256

  layers = [
    "arn:aws:lambda:eu-north-1:336392948345:layer:AWSSDKPandas-Python313:9"
  ]

  environment {
    variables = {
      S3_BUCKET_NAME      = aws_s3_bucket.data_storage.bucket
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.state_table.name
      MAX_RECURSION_DEPTH = 3
    }
  }
}

# 5. Djinni Parser
data "archive_file" "djinni_parser_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambdas/djinni/djinni_parser.py"
  output_path = "${path.module}/../lambdas/djinni/djinni_parser.zip"
}

resource "aws_lambda_function" "djinni_parser" {
  function_name    = "djinni-parser"
  role             = aws_iam_role.djinni_parser_role.arn
  handler          = "djinni_parser.lambda_handler"
  runtime          = "python3.13"
  timeout          = 900
  memory_size      = 512
  filename         = data.archive_file.djinni_parser_zip.output_path
  source_code_hash = data.archive_file.djinni_parser_zip.output_base64sha256

  layers = [
    "arn:aws:lambda:eu-north-1:336392948345:layer:AWSSDKPandas-Python313:9",
    aws_lambda_layer_version.scraping_layer.arn
  ]

  environment {
    variables = {
      S3_BUCKET_NAME      = aws_s3_bucket.data_storage.bucket
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.state_table.name
    }
  }
}

# ==========================================
# EVENT SOURCE MAPPINGS (TRIGGERS)
# ==========================================
resource "aws_lambda_event_source_mapping" "sqs_to_worker" {
  event_source_arn                   = aws_sqs_queue.dou_urls_queue.arn
  function_name                      = aws_lambda_function.dou_worker.arn
  batch_size                         = 5
  maximum_batching_window_in_seconds = 0

  scaling_config {
    maximum_concurrency = 3
  }
}

# ==========================================
# EVENTBRIDGE SCHEDULER (With Timezone)
# ==========================================

# 1. Djinni Parser Schedule (04:00 Kyiv)
resource "aws_scheduler_schedule" "daily_scraping" {
  name = "daily-scraping-schedule"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression          = "cron(0 4 * * ? *)"
  schedule_expression_timezone = "Europe/Kyiv"

  target {
    arn      = aws_lambda_function.djinni_parser.arn
    role_arn = aws_iam_role.scheduler_role.arn
  }
}

# 2. DOU Dispatcher Schedule (04:00 Kyiv)
resource "aws_scheduler_schedule" "daily_dispatcher" {
  name = "daily-dispatcher-schedule"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression          = "cron(0 4 * * ? *)"
  schedule_expression_timezone = "Europe/Kyiv"

  target {
    arn      = aws_lambda_function.dou_dispatcher.arn
    role_arn = aws_iam_role.scheduler_role.arn
  }
}

# 3. DOU Aggregator Schedule (07:00 Kyiv)
resource "aws_scheduler_schedule" "daily_aggregation" {
  name = "daily-aggregation-schedule"

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression          = "cron(0 7 * * ? *)"
  schedule_expression_timezone = "Europe/Kyiv"

  target {
    arn      = aws_lambda_function.dou_aggregator.arn
    role_arn = aws_iam_role.scheduler_role.arn
  }
}
