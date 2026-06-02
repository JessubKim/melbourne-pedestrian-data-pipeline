# EventBridge Lambda & Scheduled Events Example

Configuration in this directory creates EventBridge resource configuration including an Lambda service.

## Usage

### AWS credentials

This stack expects AWS credentials from [`aws login`](https://aws.amazon.com/blogs/security/simplified-developer-access-to-aws-with-aws-login/) (or any profile that `aws configure export-credentials` can read). Terraform does not use `login_session` / `~/.aws/login/cache` directly, so the provider uses a `credential_process` bridge in [`aws-config`](aws-config).

Before plan or apply:

```bash
aws login   # refresh if your session expired
```

For CI or long-lived keys, use the default credential chain instead of the bridge profile:

```bash
export AWS_ACCESS_KEY_ID=...
export AWS_SECRET_ACCESS_KEY=...
terraform plan -var='aws_profile='
```

If your login profile is not `default`, set `AWS_LOGIN_PROFILE` when running Terraform.

### Terraform

```bash
terraform init
terraform plan
terraform apply
```

If apply fails with `Function already exist` after a partial or failed apply, the Lambda may be tainted in state while it already exists in AWS. Refresh and adopt it:

```bash
terraform untaint 'module.lambda.aws_lambda_function.this[0]'
terraform plan -out=tfplan
terraform apply tfplan
```

The Lambda container image is built locally during apply via the Docker provider (`terraform/modules/docker-build-lambda`). Builds disable BuildKit provenance/SBOM attestations so ECR receives a single Docker v2 manifest (required by Lambda; OCI image indexes fail with `InvalidParameterValueException`).

On Linux with Docker Desktop, Terraform auto-detects `~/.docker/desktop/docker.sock` (the CLI default context). On a native Docker Engine host, your user must be in the `docker` group, or set `-var='docker_host=unix:///var/run/docker.sock'` if you use a non-default socket.

Note that this example may create resources which cost money. Run `terraform destroy` when you don't need these resources.

<!-- BEGIN_TF_DOCS -->
## Requirements

| Name | Version |
|------|---------|
| <a name="requirement_terraform"></a> [terraform](#requirement\_terraform) | >= 1.5.7 |
| <a name="requirement_aws"></a> [aws](#requirement\_aws) | >= 6.28 |
| <a name="requirement_null"></a> [null](#requirement\_null) | >= 2.0 |
| <a name="requirement_random"></a> [random](#requirement\_random) | >= 3.0 |

## Providers

| Name | Version |
|------|---------|
| <a name="provider_null"></a> [null](#provider\_null) | >= 2.0 |
| <a name="provider_random"></a> [random](#provider\_random) | >= 3.0 |

## Modules

| Name | Source | Version |
|------|--------|---------|
| <a name="module_eventbridge"></a> [eventbridge](#module\_eventbridge) | ../../ | n/a |
| <a name="module_lambda"></a> [lambda](#module\_lambda) | terraform-aws-modules/lambda/aws | ~> 8.0 |

## Resources

| Name | Type |
|------|------|
| [null_resource.download_package](https://registry.terraform.io/providers/hashicorp/null/latest/docs/resources/resource) | resource |
| [random_pet.this](https://registry.terraform.io/providers/hashicorp/random/latest/docs/resources/pet) | resource |

## Inputs

No inputs.

## Outputs

| Name | Description |
|------|-------------|
| <a name="output_eventbridge_rule_arns"></a> [eventbridge\_rule\_arns](#output\_eventbridge\_rule\_arns) | The EventBridge Rule ARNs |
| <a name="output_lambda_function_arn"></a> [lambda\_function\_arn](#output\_lambda\_function\_arn) | The ARN of the Lambda Function |
| <a name="output_lambda_function_name"></a> [lambda\_function\_name](#output\_lambda\_function\_name) | The name of the Lambda Function |
<!-- END_TF_DOCS -->
