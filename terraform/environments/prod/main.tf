provider "aws" {
  region = "us-east-2"

  # Make it faster by skipping something
  skip_metadata_api_check     = true
  skip_region_validation      = true
  skip_credentials_validation = true
}

locals {
  lambda_source_path = "${path.module}/../../../lambda"
}

module "eventbridge" {
  source = "../../modules/eventbridge"

  create_bus = false

  rules = {
    pedestrian_poll = {
      description         = "Poll Melbourne pedestrian counting API every minute"
      schedule_expression = "rate(1 minute)"
    }
  }

  targets = {
    pedestrian_poll = [
      {
        name = "pedestrian-api-poller"
        arn  = module.lambda.lambda_function_arn
      }
    ]
  }
}

module "lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "~> 8.0"

  function_name = "pedestrian-counting-poller"
  description   = "Polls Melbourne OpenDataSoft pedestrian counting API"
  handler       = "handler.lambda_handler"
  runtime       = "python3.12"
  timeout       = 60

  reserved_concurrent_executions = 1

  source_path = local.lambda_source_path

  create_current_version_allowed_triggers = false
  allowed_triggers = {
    PedestrianPollRule = {
      principal  = "events.amazonaws.com"
      source_arn = module.eventbridge.eventbridge_rule_arns["pedestrian_poll"]
    }
  }
}
