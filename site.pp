node default {
	file {
		"/tmp/puppet.txt": content => "Hello Puppet!\n";
		}
}

node 'agent.openstacklocal' {
	#include basic
}

node /^client\d{2}\.openstacklocal$/ {
	include basic
	include client
}

node /^node\d{2}\.openstacklocal$/ {
	include basic
	include server
	include aerospike
	#include infinispan
	#include redis
	#include redispair
	#include cassandra
}

