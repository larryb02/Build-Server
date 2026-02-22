output "instance_id" {
  description = "Bastion instance ID - use with: aws ssm start-session --target <instance_id>"
  value       = aws_instance.bastion.id
}
