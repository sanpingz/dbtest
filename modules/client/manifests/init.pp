class client {
	case $operatingsystem {
		centos, redhat: {
			$dist_home = '/local/dist'
			$apps_home = '/local/apps'
			$tool_home = '/local/tool'
			$ycsb_tar = 'ycsb-0.1.5.tar.gz'
			$cassandra_tar = 'apache-cassandra-2.1.0-bin.tar.gz'
			$redis_tar = 'redis-3.0.tar.gz'
			$cluster_conf = 'cluster.conf'
			$files_home = 'puppet:///modules/client'
			$extra_home = 'puppet:///extra_files'
		}
	}
	file { '/local/workshop':
		mode => 644,
		owner => root,
		group => root,
		source => "$files_home/workshop",
		purge => true,
		recurse => true,
	}
	file { "$tool_home":
		mode => 755,
		owner => root,
		group => root,
		source => "$files_home/tool",
		purge => true,
		recurse => true,
	}
	file { "$ycsb_tar":
		mode => 644,
		owner => root,
		group => root,
		path => "$dist_home/${ycsb_tar}",
		ensure => file,
		source => "$extra_home/files/${ycsb_tar}",
		notify => Exec["install_ycsb"],
	}
	file { "$cassandra_tar":
        mode => 644,
        owner => root,
        group => root,
        path => "$dist_home/${cassandra_tar}",
        ensure => file,
        source => "$extra_home/files/${cassandra_tar}",
        notify => Exec["install_cassandra"],
    }
	file { "$redis_tar":
        mode => 644,
        owner => root,
        group => root,
        path => "$dist_home/${redis_tar}",
        ensure => file,
        source => "$extra_home/files/${redis_tar}",
        notify => Exec["install_redis"],
    }
	exec { "install_ycsb":
		cwd => "$apps_home",
		path => '/usr/bin:/bin',
		command => "rm -rf $apps_home/ycsb && \
		tar -zxvf $dist_home/${ycsb_tar} -C $apps_home/ && \
		mv $apps_home/*ycsb* $apps_home/ycsb && > /dev/null",
		onlyif => "test -f $dist_home/${ycsb_tar}",
		refreshonly => true,
	}
	exec { "install_cassandra":
		cwd => "$apps_home",
		path => '/usr/bin:/bin',
		command => "rm -rf $apps_home/cassandra && \
		tar -zxvf $dist_home/${cassandra_tar} -C $apps_home/ && \
		mv $apps_home/*cassandra* $apps_home/cassandra && > /dev/null",
		onlyif => "test -f $dist_home/${cassandra_tar}",
		refreshonly => true,
	}
	exec { "install_redis":
		cwd => "$apps_home",
		path => '/usr/bin:/bin',
		command => "rm -rf $apps_home/redis && \
		tar -zxvf $dist_home/${redis_tar} -C $apps_home/ && \
		mv $apps_home/*redis* $apps_home/redis && > /dev/null",
		onlyif => "test -f $dist_home/${redis_tar}",
		refreshonly => true,
	}
}
