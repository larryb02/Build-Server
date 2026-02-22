output "server_ip" {
  description = "Public IP of the k3s server node"
  value       = aws_instance.server.public_ip
}

output "agent_ips" {
  description = "Public IPs of the k3s agent nodes"
  value       = aws_instance.agent[*].public_ip
}
