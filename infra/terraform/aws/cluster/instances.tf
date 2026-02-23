data "aws_ami" "amzlinux" {
  most_recent = true
  owners      = ["137112412989"] # Amazon

  filter {
    name   = "name"
    values = ["al2023-ami-2023*-x86_64"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
}

resource "aws_instance" "server" {
  ami                    = data.aws_ami.amzlinux.id
  instance_type          = var.instance_type
  vpc_security_group_ids = [aws_security_group.k3s-server.id]

  tags = {
    Name = "k3s-server"
    Role = "server"
  }
}

resource "aws_instance" "agent" {
  count                  = var.agent_count
  ami                    = data.aws_ami.amzlinux.id
  instance_type          = var.instance_type
  vpc_security_group_ids = [aws_security_group.k3s-agent.id]

  tags = {
    Name = "k3s-agent-${count.index}"
    Role = "agent"
  }
}
