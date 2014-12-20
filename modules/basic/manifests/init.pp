class basic {
	case $operatingsystem {
		centos, redhat: {
			$files_home = 'puppet:///modules/basic'
		}
	}
	file { 'profile':
		mode => 644,
		owner => root,
		group => root,
		path => '/etc/profile',
		ensure => file,
		source => "$files_home/profile",
	}
	file { '/etc/hosts':
		mode => 644,
		owner => root,
		group => root,
		ensure => file,
		source => "$files_home/hosts",
	}
	file { '/etc/crontab':
		mode => 644,
		owner => root,
		group => root,
		ensure => file,
		source => "$files_home/crontab",
	}
	file { 'puppet.conf':
		mode => 644,
		owner => root,
		group => root,
		ensure => file,
		path => "/etc/puppet/puppet.conf",
		source => "$files_home/puppet.conf",
	}
	file { 'auth.conf':
		mode => 644,
		owner => root,
		group => root,
		ensure => file,
		path => "/etc/puppet/auth.conf",
		source => "$files_home/auth.conf",
	}
	file { 'puppet':
		mode => 755,
		owner => root,
		group => root,
		ensure => file,
		path => "/etc/init.d/puppet",
		source => "$files_home/puppet",
	}
	service { 'crond':
		name => 'crond',
		ensure => running,
		enable => true,
		subscribe => File['/etc/crontab'],
	}
	service { 'iptables':
		name => 'iptables',
		ensure => stopped,
		enable => false,
	}
	service { 'puppet':
		name => 'puppet',
		ensure => stopped,
		enable => false,
		subscribe => File['puppet.conf', 'puppet', 'auth.conf'],
	}
	file { '/local':
		mode => 644,
		owner => root,
		group => root,
		ensure => directory,
	}
	file { '/local/conf':
		mode => 644,
		owner => root,
		group => root,
		ensure => directory,
	}
	file { '/local/dist':
		mode => 644,
		owner => root,
		group => root,
		ensure => directory,
	}
	file { '/local/apps':
		mode => 644,
		owner => root,
		group => root,
		ensure => directory,
	}
	file { '/local/logs':
		mode => 644,
		owner => root,
		group => root,
		ensure => directory,
	}
	file { '/local/data':
		mode => 644,
		owner => root,
		group => root,
		ensure => directory,
	}
}
