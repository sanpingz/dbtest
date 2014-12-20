node default {
	file {
		"/tmp/puppet.txt": content => "Hello Puppet!\n";
		}
}

node 'base.openstacklocal' {
	#include basic
}

node /^client\d{2}\.openstacklocal$/ {
	include basic
	include client
}

node /^node\d{2}\.openstacklocal$/ {
	include basic
	include server
	#include infinispan
	include aerospike
	#include redis
	#include cassandra
}
