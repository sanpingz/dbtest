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
	file { '/local/tools/bin':
		mode => 755,
		owner => root,
		group => root,
		source => "$files_home/bin",
		purge => true,
		recurse => true,
	}
}
