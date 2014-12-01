class aerospike {
	case $operatingsystem {
		centos, redhat: {
			$service = 'aerospike'
			$zip_file = 'aerospike.tgz'
			$conf_home = '/local/conf'
			$apps_home = '/local/apps'
			$data_home = '/local/data'
			$dist_home = '/local/dist'
			$logs_home = '/local/logs'
			$tool_home = '/local/tool'
			$files_home = "puppet:///modules/$service"
			$extra_home = 'puppet:///extra_files'
		}
	}

	file { "/etc/init.d/$service":
		mode => 755,
		owner => root,
		group => root,
		ensure => file,
		source => "$files_home/$service"
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
		mode => 644,
		owner => root,
		group => root,
		ensure => directory,
	}
	file { "$logs_home/$service":
		mode => 644,
		owner => root,
		group => root,
		ensure => directory,
	}
	file { "$service.conf":
		mode => 644,
		owner => root,
		group => root,
		ensure => file,
		path => "$conf_home/$service/$service.conf",
		content => template("$service/$service.erb"),
		notify => Service["$service"],
	}
#	file { "$conf_home/$service":
#		mode => 755,
#		owner => root,
#		group => root,
#		source => "$extra_home/conf/$service",
#		purge => "true",
#		recurse => "true",
#	}
#	file { "$zip_file":
#		mode => 644,
#		owner => root,
#		group => root,
#		path => "$dist_home/${zip_file}",
#		ensure => file,
#		source => "$extra_home/files/${zip_file}",
#		notify => Exec["reinstall_$service"],
#	}
	service { "$service":
		name => "$service",
		ensure => running,
		hasstatus => true,
		hasrestart => true,
		enable => false,
		#subscribe => File["$conf_home/$service"],
	}
}
