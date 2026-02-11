variable "config_path" {
  description = "Path to kubeconfig file"
  type = string
  default = "~/.kube/config"
}

variable "api_labels" {
  description = "buildserver apiserver labels"
  type = map(string)
  default = {
    app = "buildserver-api"
  }
}

variable "api_port" {
  description = "buildserver apiserver port"
  type = number
  default = 8000
}

variable "api_image" {
  description = "buildserver apiserver image"
  type = string
  default = "ghcr.io/larryb02/buildserver-api:latest"
}

variable "runner_labels" {
  description = "buildserver runner labels"
  type = map(string)
  default = {
    app = "buildserver-runner"
  }
}

variable "runner_image" {
  description = "buildserver runner image"
  type = string
  default = "ghcr.io/larryb02/buildserver-runner:latest"
}

# Database
variable "database_hostname" {
  description = "PostgreSQL hostname"
  type        = string
  default     = "postgres"
}

variable "database_port" {
  description = "PostgreSQL port"
  type        = number
  default     = 5432
}

variable "database_user" {
  description = "PostgreSQL user"
  type        = string
  default     = "postgres"
}

variable "database_password" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

variable "database_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "postgres"
}

# RabbitMQ
variable "rabbitmq_host" {
  description = "RabbitMQ hostname"
  type        = string
  default     = "rabbitmq"
}

variable "rabbitmq_port" {
  description = "RabbitMQ port"
  type        = number
  default     = 5672
}

variable "rabbitmq_user" {
  description = "RabbitMQ user"
  type        = string
  default     = "guest"
}

variable "rabbitmq_password" {
  description = "RabbitMQ password"
  type        = string
  sensitive   = true
}
