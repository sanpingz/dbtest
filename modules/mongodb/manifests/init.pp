class mongodb {
	case $operatingsystem {
		centos, redhat: {
			$service_file = 'mongod'
			$conf_file = 'mongod.conf'
			$pkg_file = 'mongodb.zip'
			$files_home = 'puppet:///modules/mongodb'
			$extra_home = 'puppet:///extra_files'
		}
	}
	file { 'mongod':
		mode => 755,
		owner => root,
		group => root,
		path => '/etc/init.d/mongod',
		ensure => file,
		source => "$files_home/${service_file}"
	}
	file { '/local/data/mongodb':
		mode => 644,
		owner => root,
		group => root,
		ensure => directory,
	}
	file { '/local/conf/mongodb':
		mode => 644,
		owner => root,
		group => root,
		ensure => directory,
	}
	file { 'mongod.conf':
		mode => 644,
		owner => root,
		group => root,
		path => '/local/conf/mongodb/mongod.conf',
		ensure => file,
		source => "$extra_home/conf/mongodb/${conf_file}",
	}
	file { 'mongodb.zip':
		mode => 644,
		owner => root,
		group => root,
		path => '/local/dist/mongodb.zip',
		ensure => file,
		source => "$extra_home/files/${pkg_file}",
		notify => Exec['reinstall mongodb'],
	}
	exec { 'reinstall mongodb':
		cwd => '/local/apps',
		path => '/usr/bin',
		command => "unzip -qo /local/dist/${pkg_file} -d /local/apps/",
		onlyif => "test -f /local/dist/${pkg_file}",
		notify => Service['mongod'],
		refreshonly => true,
	}
	service { 'mongod':
		name => 'mongod',
		ensure => stopped,
		hasstatus => true,
		hasrestart => true,
		enable => false,
		subscribe => File['mongod.conf'], 
	}
}
