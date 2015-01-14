class redis {
	case $operatingsystem {
		centos, redhat: {
			$service = 'redis'
			$conf_file = 'redis.conf'
			$pkg_file = 'redis-3.0.tar.gz'
			$apps_home = '/local/apps'
			$dist_home = '/local/dist'
			$conf_home = '/local/conf'
			$data_home = '/local/data'
			$logs_home = '/local/logs'
			$files_home = "puppet:///modules/$service"
			$extra_home = 'puppet:///extra_files'
		}
	}
	file { "$service":
		mode => 755,
		owner => root,
		group => root,
		path => "/etc/init.d/$service",
		ensure => file,
		source => "$files_home/$service"
	}
	file { "$data_home/$service":
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
	file { "$conf_file":
		mode => 644,
		owner => root,
		group => root,
		path => "$conf_home/$service/$conf_file",
		ensure => file,
		source => "$extra_home/conf/$service/${conf_file}",
		notify => Service["$service"],
	}
	file { "$pkg_file":
		mode => 644,
		owner => root,
		group => root,
		path => "$dist_home/${pkg_file}",
		ensure => file,
		source => "$extra_home/files/${pkg_file}",
		notify => Exec['reinstall_redis'],
	}
	exec { "reinstall_$service":
		cwd => '/local/apps',
		path => '/usr/bin:/bin',
		command => "rm -rf $apps_home/$service && \
		tar -zxvf $dist_home/${pkg_file} -C $apps_home/ && \
		mv $apps_home/*$service* $apps_home/$service && \
		rm -rf $data_home/$service/* > /dev/null",
		onlyif => "test -f $dist_home/${pkg_file}",
		notify => Service["$service"],
		refreshonly => true,
	}
	service { "$service":
		name => "$service",
		ensure => running,
		hasstatus => true,
		hasrestart => true,
		enable => false,
	}
}
