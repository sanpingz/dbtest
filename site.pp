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

node /^node0\d{1}\.openstacklocal$/ {
	include basic
	include server
	include aerospike
	#include infinispan
	#include redis
	#include redispair
	#include cassandra
}

node /^node1\d{1}\.openstacklocal$/ {
	include basic
	include server
	#include aerospike
	include infinispan
	#include redis
	#include redispair
	#include cassandra
}
