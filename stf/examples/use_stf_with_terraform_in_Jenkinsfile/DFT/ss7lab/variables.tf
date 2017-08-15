variable "os_username" {
}

variable "os_password" {
}

variable "os_tenant_name" {
  default = "v1445_CSF"
}

variable "os_auth_url" {
  default = "http://135.111.16.134:5000/v2.0"
}

variable "os_region_name" {
  default = "regionOne"
}

variable "image" {
  default = "rhel-guest-image-7.3-35.x86_64.qcow2"
}

variable "flavor" {
  default = "m1.medium"
}

variable "network" {
   type = "string"
   default = "v1445-Access-177"
}

variable "ssh_key_file" {
  default = "~/.ssh/id_rsa"
}

variable "ss7_lab_count" {
   type = "string"
   default = "2"
}
