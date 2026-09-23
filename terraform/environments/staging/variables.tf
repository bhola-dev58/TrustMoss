variable "aws_region" {
  description = "AWS deployment region"
  type        = string
  default     = "us-east-1"
}

variable "api_image_tag" {
  description = "Docker image tag for API"
  type        = string
  default     = "staging-latest"
}

variable "web_image_tag" {
  description = "Docker image tag for Web"
  type        = string
  default     = "staging-latest"
}
