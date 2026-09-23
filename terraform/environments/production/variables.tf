variable "aws_region" {
  description = "AWS deployment region"
  type        = string
  default     = "us-east-1"
}

variable "api_image_tag" {
  description = "Docker image tag for API"
  type        = string
  default     = "latest"
}

variable "web_image_tag" {
  description = "Docker image tag for Web"
  type        = string
  default     = "latest"
}

variable "api_desired_count" {
  description = "Desired count for API containers in production"
  type        = number
  default     = 3
}

variable "web_desired_count" {
  description = "Desired count for Web containers in production"
  type        = number
  default     = 3
}
