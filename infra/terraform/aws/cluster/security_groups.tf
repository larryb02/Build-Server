data "aws_security_group" "bastion" {
  name = "bastion"
}

resource "aws_security_group" "k3s-server" {
  name        = "k3s-server"
  description = "Firewall rules for k3s-server nodes"

  tags = {
    Name = "k3s-server"
  }
}

resource "aws_security_group" "k3s-agent" {
  name        = "k3s-agent"
  description = "Firewall rules for k3s-agent nodes"

  tags = {
    Name = "k3s-agent"
  }
}

# k3s-server rules
resource "aws_vpc_security_group_ingress_rule" "k3s_server_ssh" {
  security_group_id = aws_security_group.k3s-server.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 22
  to_port           = 22
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "k3s_server_http" {
  security_group_id = aws_security_group.k3s-server.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "k3s_server_https" {
  security_group_id = aws_security_group.k3s-server.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "k3s_server_k3s_api" {
  security_group_id = aws_security_group.k3s-server.id
  referenced_security_group_id = data.aws_security_group.bastion
  # cidr_ipv4         = "0.0.0.0/0"
  from_port         = 6443
  to_port           = 6443
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "k3s_server_flannel_from_agents" {
  security_group_id            = aws_security_group.k3s-server.id
  referenced_security_group_id = aws_security_group.k3s-agent.id
  from_port                    = 8472
  to_port                      = 8472
  ip_protocol                  = "udp"
}

resource "aws_vpc_security_group_ingress_rule" "k3s_server_kubelet_from_agents" {
  security_group_id            = aws_security_group.k3s-server.id
  referenced_security_group_id = aws_security_group.k3s-agent.id
  from_port                    = 10250
  to_port                      = 10250
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_egress_rule" "k3s_server_allow_all_ipv4" {
  security_group_id = aws_security_group.k3s-server.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_vpc_security_group_egress_rule" "k3s_server_allow_all_ipv6" {
  security_group_id = aws_security_group.k3s-server.id
  cidr_ipv6         = "::/0"
  ip_protocol       = "-1"
}

#k3s-agent rules

resource "aws_vpc_security_group_egress_rule" "k3s_agent_allow_all_ipv4" {
  security_group_id = aws_security_group.k3s-agent.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_vpc_security_group_egress_rule" "k3s_agent_allow_all_ipv6" {
  security_group_id = aws_security_group.k3s-agent.id
  cidr_ipv6         = "::/0"
  ip_protocol       = "-1"
}
