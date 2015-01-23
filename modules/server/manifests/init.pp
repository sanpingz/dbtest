class server {
	case $operatingsystem {
		centos, redhat: {
			$files_home = 'puppet:///modules/server'
		}
	}
#	file { '/boot/grub/grub.conf':
#		mode => 600,
#		owner => root,
#		group => root,
#		ensure => file,
#		source => "$files_home/grub.conf",
#	}
}
