provider "aws" {
  region = "us-east-2"

  # Make it faster by skipping something
  skip_metadata_api_check     = true
  skip_region_validation      = true
  skip_credentials_validation = true
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
data "aws_ecr_authorization_token" "token" {}

provider "docker" {
  registry_auth {
    address  = format("%v.dkr.ecr.%v.amazonaws.com", data.aws_caller_identity.current.account_id, data.aws_region.current.region)
    username = data.aws_ecr_authorization_token.token.user_name
    password = data.aws_ecr_authorization_token.token.password
  }
}

locals {
  lambda_source_path = "${path.module}/../../../lambda"
  path_include       = ["**"]
  path_exclude       = ["**/__pycache__/**", ".venv/**"]
  files_include      = setunion([for f in local.path_include : fileset(local.lambda_source_path, f)]...)
  files_exclude      = setunion([for f in local.path_exclude : fileset(local.lambda_source_path, f)]...)
  files              = sort(setsubtract(local.files_include, local.files_exclude))
  dir_sha            = sha1(join("", [for f in local.files : filesha1("${local.lambda_source_path}/${f}")]))
}

module "docker_build" {
  source  = "terraform-aws-modules/lambda/aws//modules/docker-build"
  version = "~> 8.0"

  create_ecr_repo = true
  ecr_repo        = "data-pipeline-repository"
  ecr_repo_lifecycle_policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep only the last 2 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 2
        }
        action = {
          type = "expire"
        }
      }
    ]
  })

  use_image_tag    = false
  source_path      = local.lambda_source_path
  docker_file_path = "${local.lambda_source_path}/Dockerfile"
  platform         = "linux/amd64"

  triggers = {
    dir_sha = local.dir_sha
  }
}

module "eventbridge" {
  source = "../../modules/eventbridge"

  create_bus = false

  rules = {
    pedestrian_poll = {
      description         = "Poll Melbourne pedestrian counting API"
      schedule_expression = "rate(15 minutes)"
    }
  }

  targets = {
    pedestrian_poll = [
      {
        name = "pedestrian-api-to-snowflake-pipeline"
        arn  = module.lambda.lambda_function_arn
      }
    ]
  }
}

module "lambda" {
  source  = "terraform-aws-modules/lambda/aws"
  version = "~> 8.0"

  function_name = "pedestrian-api-to-snowflake-pipeline"
  description   = "Exports pedestrian counting data from Melbourne OpenDataSoft API to Snowflake"
  timeout       = 60

  reserved_concurrent_executions = 1

  create_package = false
  package_type   = "Image"
  architectures  = ["x86_64"]
  image_uri      = module.docker_build.image_uri

  create_current_version_allowed_triggers = false
  allowed_triggers = {
    PedestrianPollRule = {
      principal  = "events.amazonaws.com"
      source_arn = module.eventbridge.eventbridge_rule_arns["pedestrian_poll"]
    }
  }
}
