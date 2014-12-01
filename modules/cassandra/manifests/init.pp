class cassandra {
	case $operatingsystem {
		centos, redhat: {
			$service = 'cassandra'
			$zip_file = 'apache-cassandra-2.1.0-bin.tar.gz'
			$jna_jar = 'jna-4.1.0.jar'
			$conf_home = '/local/conf'
			$apps_home = '/local/apps'
			$data_home = '/local/data'
			$dist_home = '/local/dist'
			$tool_home = '/local/tool'
			$files_home = "puppet:///modules/$service"
			$extra_home = 'puppet:///extra_files'
			$KS = 'state'
		}
	}
	file { "/etc/init.d/$service":
		mode => 755,
		owner => root,
		group => root,
		ensure => file,
		source => "$files_home/$service"
	}
	file { "/etc/security/limits.conf":
		mode => 644,
		owner => root,
		group => root,
		ensure => file,
		source => "$files_home/limits.conf"
	}
	file { "/etc/security/limits.d/90-nproc.conf":
		mode => 644,
		owner => root,
		group => root,
		ensure => file,
		source => "$files_home/90-nproc.conf"
	}
	file { "/etc/sysctl.conf":
		mode => 644,
		owner => root,
		group => root,
		ensure => file,
		source => "$files_home/sysctl.conf"
	}
	file { "$data_home/$service":
		mode => 644,
		owner => root,
		group => root,
		ensure => directory,
	}
	file { "$apps_home/$service":
		mode => 644,
		owner => root,
		group => root,
		ensure => directory,
	}
	file { "$conf_home/$service":
		mode => 755,
		owner => root,
		group => root,
		source => "$extra_home/conf/$service",
		purge => "true",
		recurse => "true",
	}
	file { "$zip_file":
		mode => 644,
		owner => root,
		group => root,
		path => "$dist_home/${zip_file}",
		ensure => file,
		source => "$extra_home/files/${zip_file}",
		notify => Exec["reinstall_$service"],
	}
	file { "$jna_jar":
		mode => 644,
		owner => root,
		group => root,
		path => "$tool_home/lib/${jna_jar}",
		ensure => file,
		source => "$extra_home/files/${jna_jar}",
	}
	exec { "reinstall_$service":
		cwd => "$apps_home",
		path => '/usr/bin:/bin',
		command => "rm -rf $apps_home/$service && \
		tar -zxvf $dist_home/${zip_file} -C $apps_home/ && \
		mv $apps_home/*$service* $apps_home/$service && \
		rm -rf $data_home/$service/* > /dev/null",
		onlyif => "test -f $dist_home/${zip_file}",
		refreshonly => true,
		notify => Service["$service"],
	}
	service { "$service":
		name => "$service",
		ensure => running,
		hasstatus => true,
		hasrestart => true,
		enable => false,
		subscribe => File["$conf_home/$service"],
	}
	service { 'datastax-agent':
		name => 'datastax-agent',
		ensure => running,
		enable => true,
	}
}
