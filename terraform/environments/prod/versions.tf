terraform {
  required_version = ">= 1.5.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.28"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = ">= 3.5.0"
    }
  }
}
