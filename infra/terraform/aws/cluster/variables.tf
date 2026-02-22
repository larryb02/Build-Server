variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-west-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "agent_count" {
  description = "Number of k3s agent nodes"
  type        = number
  default     = 2
}

# variable "public_key_path" {
#   description = "Path to SSH public key"
#   type        = string
# }
