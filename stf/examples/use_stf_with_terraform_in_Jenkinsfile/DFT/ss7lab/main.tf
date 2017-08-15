provider "openstack" {
  user_name   = "${var.os_username}"
  tenant_name = "${var.os_tenant_name}"
  password    = "${var.os_password}"
  auth_url    = "${var.os_auth_url}"
  #region      = "${var.os_region_name}"
}

resource "random_id" "ran_num" {
  byte_length = 4
}

resource "openstack_compute_keypair_v2" "keypair" {
   name = "ss7decoder-gemfield-${random_id.ran_num.dec}"
   public_key = "${file("${var.ssh_key_file}.pub")}"
}

resource "openstack_compute_instance_v2" ss7_labs {
   count = "${var.ss7_lab_count}"
   name = "ss7_lab_${count.index + 1}"
   image_name = "${var.image}"
   flavor_name = "${var.flavor}"
   key_pair = "${openstack_compute_keypair_v2.keypair.name}"
   security_groups = ["default"]
   network {
     name = "${var.network}"
   }

}

output "ipaddress" {
  value = "${openstack_compute_instance_v2.ss7_labs.*.network.0.fixed_ip_v4}"
}

data "template_file" "stf_ini_template" {
    template = "${file("${path.module}/stf.ini.tpl")}"
    vars { 
        #ss7_lab_ip = "${openstack_compute_instance_v2.ss7_labs.*.network.0.fixed_ip_v4}"
        ss7_lab_ip = "${join("\n ",openstack_compute_instance_v2.ss7_labs.*.network.0.fixed_ip_v4)}"
    }
}

resource "null_resource" "render_stf_ini" {
    triggers {
        template_rendered = "${data.template_file.stf_ini_template.rendered}"
    }
    provisioner "local-exec" {
        command = "echo '${data.template_file.stf_ini_template.rendered}' > stf.ini"
    }
}
