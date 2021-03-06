class client {
	case $operatingsystem {
		centos, redhat: {
			$dist_home = '/local/dist'
			$apps_home = '/local/apps'
			$tools_home = '/local/tools'
			$work_home = '/local/workshop'
			$ycsb_pkg = 'ycsb-0.1.5.tar.gz'
			$files_home = 'puppet:///modules/client'
			$extra_home = 'puppet:///extra_files'
		}
	}
#	file { '/boot/grub/grub.conf':
#	    mode => 600,
#		owner => root,
#		group => root,
#		ensure => file,
#		source => "$files_home/grub.conf",
#	}
	file { "$tools_home/bin":
		mode => 755,
		owner => root,
		group => root,
		source => "$files_home/bin",
		purge => true,
		recurse => true,
	}
	file { "$work_home":
		mode => 644,
		owner => root,
		group => root,
		source => "$files_home/workshop",
		purge => true,
		recurse => true,
	}
	file { "$ycsb_pkg":
		mode => 644,
		owner => root,
		group => root,
		path => "$dist_home/${ycsb_pkg}",
		ensure => file,
		source => "$extra_home/files/${ycsb_pkg}",
		notify => Exec["install_ycsb"],
	}
	exec { "install_ycsb":
		cwd => "$apps_home",
		path => '/usr/bin:/bin',
		command => "rm -rf $apps_home/ycsb && \
		tar -zxvf $dist_home/${ycsb_pkg} -C $apps_home/ && \
		mv $apps_home/*ycsb* $apps_home/ycsb && > /dev/null",
		onlyif => "test -f $dist_home/${ycsb_pkg}",
		refreshonly => true,
	}
}
