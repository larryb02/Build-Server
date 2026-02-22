resource "aws_security_group" "bastion" {
  name        = "bastion"
  description = "Bastion host - SSM only (no inbound required)"

  tags = {
    Name = "bastion"
  }
}

resource "aws_vpc_security_group_egress_rule" "bastion_allow_all_ipv4" {
  security_group_id = aws_security_group.bastion.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_vpc_security_group_egress_rule" "bastion_allow_all_ipv6" {
  security_group_id = aws_security_group.bastion.id
  cidr_ipv6         = "::/0"
  ip_protocol       = "-1"
}
