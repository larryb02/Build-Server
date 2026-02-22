data "aws_ami" "rhel10" {
  most_recent = true
  owners      = ["309956199498"] # Red Hat

  filter {
    name   = "name"
    values = ["RHEL-10*"]
  }

  filter {
    name   = "architecture"
    values = ["x86_64"]
  }
}

resource "aws_key_pair" "buildserver" {
  key_name   = "buildserver"
  public_key = file(var.public_key_path)
}

resource "aws_instance" "server" {
  ami                    = data.aws_ami.rhel10.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.buildserver.key_name
  vpc_security_group_ids = [aws_security_group.k3s-server.id]

  tags = {
    Name = "k3s-server"
    Role = "server"
  }
}

resource "aws_instance" "agent" {
  count                  = var.agent_count
  ami                    = data.aws_ami.rhel10.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.buildserver.key_name
  vpc_security_group_ids = [aws_security_group.k3s-agent.id]

  tags = {
    Name = "k3s-agent-${count.index}"
    Role = "agent"
  }
}
