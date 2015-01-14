class redispair {
	case $operatingsystem {
		centos, redhat: {
			$service = 'redispair'
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
	file { "redis1":
		mode => 755,
		owner => root,
		group => root,
		path => "/etc/init.d/redis1",
		ensure => file,
		source => "$files_home/redis1"
	}
	file { "redis2":
		mode => 755,
		owner => root,
		group => root,
		path => "/etc/init.d/redis2",
		ensure => file,
		source => "$files_home/redis2"
	}
	file { "$data_home/$service":
		mode => 644,
		owner => root,
		group => root,
		ensure => directory,
	}
	file { "$data_home/$service/redis1":
		mode => 644,
		owner => root,
		group => root,
		ensure => directory,
	}
	file { "$data_home/$service/redis2":
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
	file { "redis1.conf":
		mode => 644,
		owner => root,
		group => root,
		path => "$conf_home/$service/redis1.conf",
		ensure => file,
		source => "$extra_home/conf/$service/redis1.conf",
		notify => Service["redis1"],
	}
	file { "redis2.conf":
		mode => 644,
		owner => root,
		group => root,
		path => "$conf_home/$service/redis2.conf",
		ensure => file,
		source => "$extra_home/conf/$service/redis2.conf",
		notify => Service["redis2"],
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
    exec { "reinstall_redis":
        cwd => '/local/apps',
        path => '/usr/bin:/bin',
        command => "rm -rf $apps_home/redis && \
        tar -zxvf $dist_home/${pkg_file} -C $apps_home/ && \
        mv $apps_home/*redis* $apps_home/redis && \
        rm -rf $data_home/$service/* > /dev/null",
        onlyif => "test -f $dist_home/${pkg_file}",
        notify => Service["redis1", "redis2"],
        refreshonly => true,
    }
	service { "redis1":
		name => "redis1",
		ensure => running,
		hasstatus => true,
		hasrestart => true,
		enable => false,
	}
	service { "redis2":
		name => "redis2",
		ensure => running,
		hasstatus => true,
		hasrestart => true,
		enable => false,
	}
}
