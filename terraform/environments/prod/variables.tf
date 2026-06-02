variable "aws_profile" {
  description = "AWS profile for Terraform. Uses aws-config with credential_process to bridge `aws login`. Set to an empty string to use the default credential chain (e.g. CI environment variables)."
  type        = string
  default     = "melbourne-pedestrian"
}

variable "docker_host" {
  description = "Docker daemon socket for the docker-build module (kreuzwerker/docker provider). Leave empty to auto-detect Docker Desktop on Linux, otherwise unix:///var/run/docker.sock."
  type        = string
  default     = ""
}
