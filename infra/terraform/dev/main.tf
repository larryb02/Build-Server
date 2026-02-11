provider "kubernetes" {
  config_path = var.config_path
}

resource "kubernetes_config_map_v1" "buildserver" {
  metadata {
    name = "buildserver-config"
  }

  data = {
    DATABASE_HOSTNAME = var.database_hostname
    DATABASE_PORT     = tostring(var.database_port)
    DATABASE_USER     = var.database_user
    DATABASE_NAME     = var.database_name
    RABBITMQ_HOST     = var.rabbitmq_host
    RABBITMQ_PORT     = tostring(var.rabbitmq_port)
    RABBITMQ_USER     = var.rabbitmq_user
  }
}

resource "kubernetes_secret_v1" "buildserver" {
  metadata {
    name = "buildserver-secrets"
  }

  data = {
    DATABASE_PASSWORD = var.database_password
    RABBITMQ_PASSWORD = var.rabbitmq_password
  }
}

resource "kubernetes_deployment_v1" "buildserver-api" {
  metadata {
    name   = "buildserver-api"
    labels = var.api_labels
  }

  spec {
    replicas = 1

    selector {
      match_labels = var.api_labels
    }

    template {
      metadata {
        labels = var.api_labels
      }

      spec {
        container {
          name  = "buildserver-api"
          image = var.api_image

          port {
            container_port = var.api_port
          }

          env_from {
            config_map_ref {
              name = kubernetes_config_map_v1.buildserver.metadata[0].name
            }
          }

          env_from {
            secret_ref {
              name = kubernetes_secret_v1.buildserver.metadata[0].name
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_deployment_v1" "buildserver-runner" {
  metadata {
    name   = "buildserver-runner"
    labels = var.runner_labels
  }
  spec {
    replicas = 1

    selector {
      match_labels = var.runner_labels
    }

    template {
      metadata {
        labels = var.runner_labels
      }
      spec {
        container {
          name  = "buildserver-runner"
          image = var.runner_image

          env_from {
            config_map_ref {
              name = kubernetes_config_map_v1.buildserver.metadata[0].name
            }
          }

          env_from {
            secret_ref {
              name = kubernetes_secret_v1.buildserver.metadata[0].name
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service_v1" "buildserver-api" {
  metadata {
    name = "buildserver-api"
  }

  spec {
    selector = var.api_labels

    port {
      port        = var.api_port
      target_port = var.api_port
    }
  }
}

resource "kubernetes_ingress_v1" "buildserver-api" {
  metadata {
    name = "buildserver-api"
    annotations = {
      "kubernetes.io/ingress.class" = "traefik"
    }
  }

  spec {
    rule {
      http {
        path {
          path      = "/"
          path_type = "Prefix"

          backend {
            service {
              name = kubernetes_service_v1.buildserver-api.metadata[0].name

              port {
                number = var.api_port
              }
            }
          }
        }
      }
    }
  }
}
