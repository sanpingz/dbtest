from fabric.api import run, env, put, get, roles, execute, local, parallel, serial, reboot, cd, settings, hosts, task, runs_once
from fabric.colors import green, blue, red
from fabric.contrib.console import confirm
import re, os, json

N = env.get('n') or 20
PREFIX = env.get('p') or 'node'
N=int(N)

DB = env.get('db') or 'aerospike'
COORDINATOR='node01'
WORKSHOP='/local/workshop/%s' % DB
LOGS_HOME='/local/logs/%s' % DB
if env.get('n') or env.get('p') or env.get('h'):
	env.hosts = env.get('h') or [ "%s%02d" % (PREFIX,x) for x in range(1,N+1)]

CLIENTS = ["%s%02d" % ('client',x) for x in range(1,8+1)]
DBS = ["%s%02d" % ('node',x) for x in range(1,N+1)]
env.roledefs = {
	#list of client hosts
	'client': ['client02'],
	'clients': CLIENTS,
	'state_clients': ['client02', 'client04', 'client05', 'client06'],
	#list of DB server hosts
	'servers': DBS,
	#list of all available hosts
	'all_hosts': CLIENTS + DBS,
}

NODE_LIST = ",".join(DBS)

#### Common ####
def hostname():
	run('hostname -s')

@parallel
def copy(src, dst):
	put(src, dst)

@parallel
def fetch(src, dst):
	get(src, dst)

@parallel
def remote_run(cmd):
	run(cmd)

@parallel
def service(name, action):
	if name and action:
		run('service %s %s' % (name, action))

@parallel
def os_reboot():
	reboot()

#### Puppet ####
@parallel
def puppet():
	run('puppet agent -t', warn_only=True, combine_stderr=False)

def init_puppet():
	name=run('hostname')
	try:
		local('puppet cert clean %s.openstacklocal' % name, warn_only=True, combine_stderr=False)
	except: pass
	run('find /var/lib/puppet/ssl -name %s.openstacklocal.pem -delete' % name, warn_only=True, combine_stderr=False)

#### Deploy ####
@parallel
def deploy_as():
	service = 'aerospike'
	pkg = 'aerospike.tgz'
	dist_home = '/local/dist'
	files_home = '/local/puppet/files'
	put('%s/%s' % (files_home,pkg), dist_home)
	run('rm -rf /tmp/*%s*' % service)
	run('tar -zxvf %s/%s -C /tmp/' % (dist_home,pkg))
	run('if [ "$(rpm -qa|grep %s)" == "" ]; then test -f /tmp/*%s*/asinstall && cd /tmp/*%s*/ && ./asinstall; fi' % (service,service,service), warn_only=True, combine_stderr=False)

#### Disk ####
@parallel
def disk_format():
	run('printf "n\np\n2\n\n\nw\n" | fdisk /dev/vda', warn_only=True, combine_stderr=False)

@parallel
def disk_mount():
	run('mkfs.ext3 /dev/vda2 && rm -rf /local/data && mkdir -p /local/data && mount /dev/vda2 /local/data && echo "/dev/vda2               /local/data             ext3    defaults        0 0" >> /etc/fstab', warn_only=True, combine_stderr=False)

def disk_space():
	run('df -h')

#### Monitor ####
@roles('servers')
@parallel
def monitor(mark, proc='asd', duration=1):
	host = run('hostname -s')
	#log_file = 'monitor.{0}.log'.format(host)
	#log_dir = '%s/%s' % (LOGS_HOME, mark)
	#local_log = '%s/%s' % (log_dir, log_file)
	device = 'vda2'
	with settings(warn_only=True, combine_stderr=False):
		run('mkdir -p /tmp/monitor')
		nic = 'eth1' if run('ifconfig eth0|grep 37.3.3') == '' else 'eth0'
		with cd("/tmp/monitor"):
			put('/local/tool/bin/monitor.py', '/tmp/monitor/')
			run('chmod +x /tmp/monitor/monitor.py')
			return run('./monitor.py -p {0} -n {1} -d {2} -f {3} -u {4}'.format(proc, nic, device, 'json', duration))
			#get(log_file, local_log)

@runs_once
#@parallel
#@roles('servers')
def monitorit(mark='monitor', proc='asd', duration=1):
	data = {}
	ret = None
	unit = {}
	'''
	ret = {
		'cpu': {'avg': 0.0, 'max': 0.0, 'min': 0.0},
		'disk': {
			'read': {'avg': 0.0, 'max': 0.0, 'min': 0.0},
			'write': {'avg': 0.0, 'max': 0.0, 'min': 0.0},
			'unit': 'MBytes/s'
			},
		'mem': {
			'avg': 0.0,
			'max': 0.0,
			'min': 0.0
		},
		'net': {
			'recv': {'avg': 0.0, 'max': 0.0, 'min': 0.0},
			'sent': {'avg': 0.0, 'max': 0.0, 'min': 0.0},
			'unit': 'MBytes/s'
		}
	}
	'''
	out = execute(monitor, mark, proc=proc, duration=duration)
	for k,v in out.items():
		data[k] = json.loads(str(v))
	def cmm(prev, curr):
		return {
				'avg': prev.get('avg')+curr.get('avg'),
				'max': max(prev.get('max'), curr.get('max')),
				'min': min(prev.get('min'), curr.get('min'))
		}
	def pretty_print():
		print('%CPU\navg\tmax\tmin\n{avg:.2f}\t{max:.2f}\t{min:.2f}'.format(**ret['cpu']))
		print('%MEM\navg\tmax\tmin\n{avg:.2f}\t{max:.2f}\t{min:.2f}'.format(**ret['mem']))
		print('Disk read ({{unit}})\navg\tmax\tmin\n{avg:.2f}\t{max:.2f}\t{min:.2f}'.format(**ret['disk']['read']).format(unit=unit['disk']))
		print('Disk write ({{unit}})\navg\tmax\tmin\n{avg:.2f}\t{max:.2f}\t{min:.2f}'.format(**ret['disk']['write']).format(unit=unit['disk']))
		print('Network recv ({{unit}})\navg\tmax\tmin\n{avg:.2f}\t{max:.2f}\t{min:.2f}'.format(**ret['net']['recv']).format(unit=unit['net']))
		print('Network sent ({{unit}})\navg\tmax\tmin\n{avg:.2f}\t{max:.2f}\t{min:.2f}'.format(**ret['net']['sent']).format(unit=unit['net']))

	for k,v in data.items():
		ret = ret or v
		unit['disk'] =  unit.get('disk') or v['disk']['unit']
		unit['net'] =  unit.get('net') or v['net']['unit']
		ret['cpu'] = cmm(ret['cpu'], v['cpu'])
		ret['mem'] = cmm(ret['mem'], v['mem'])
		ret['disk']['read'] = cmm(ret['disk']['read'], v['disk']['read'])
		ret['disk']['write'] = cmm(ret['disk']['write'], v['disk']['write'])
		ret['net']['sent'] = cmm(ret['net']['sent'], v['net']['sent'])
		ret['net']['recv'] = cmm(ret['net']['recv'], v['net']['recv'])
	s = len(data)
	ret['cpu']['avg'] /= s
	ret['mem']['avg'] /= s
	ret['disk']['read']['avg'] /= s
	ret['disk']['write']['avg'] /= s
	ret['net']['sent']['avg'] /= s
	ret['net']['recv']['avg'] /= s
	pretty_print()


#### YCSB ####
#@roles('client')
@parallel
def ycsb(action,workload='workloadb', contact=COORDINATOR, ns='state', set='reg',  mark=DB, target=None, threads=50, runtime=10, recordcount=None, flag=None, init=False):
	_host = 'host'
	ops = ''
	if action not in ['load','run']:
		print('Bad action, %s' % action)
		return
	if DB == 'cassandra':
		_host += 's'
		contact = NODE_LIST
		if action == 'load' and init:
			with settings(warn_only=True, combine_stderr=False):
				run("printf \"drop keyspace %s;\nCREATE KEYSPACE %s\n\twith placement_strategy = 'org.apache.cassandra.locator.SimpleStrategy' and strategy_options = {replication_factor:3};\nuse %s;\ncreate column family %s with column_type = 'Standard' and comparator = 'UTF8Type'\n\twith populate_io_cache_on_flush = true;\n\" > /tmp/state.cql" % (ns, ns, ns, set))
				run('cassandra-cli -h node01 < /tmp/state.cql')
	log_file = 'results/%s.%s.%s.%s.log' % (mark, set, action, flag) if flag else 'results/%s.%s.%s.log' % (mark, set, action)
	log_dir = '%s/%s' % (LOGS_HOME, mark)
	local_log = '%s/%s.%s.%s.log' % (log_dir, action, set, flag) if flag else '%s/%s.%s.log' % (log_dir, action, set)
	if not os.path.isdir(log_dir):
		local('mkdir -p %s' % log_dir)
	if target:
		ops = ops + " -p target=%s" % target
	else:
		ops = ops + " -p target=%s" % '0' if action == 'load' else ops
	ops = ops + " -p recordcount=%s" % recordcount if recordcount else ops
	ops = ops + " -p threads=%s" % threads
	ops = ops + " -p maxexecutiontime=%d" % int(float(runtime)*60)
	with settings(warn_only=True, combine_stderr=False):
		run('[ ! -d %s ] && mkdir -p %s' % (WORKSHOP, WORKSHOP))
		with cd(WORKSHOP):
			run('ycsb %s %s -P workloads/%s -p %s=%s %s -s > %s' % (action, DB, workload, _host, contact, ops, log_file))
			get(log_file, local_log)
			local('get_sum %s' % local_log)

@roles('state_clients')
@parallel
def run_test(action, runtime=10, flag=None, mark='all'):
	host = run('hostname -s')
	flag = '.%s' % flag if flag else ''
	flag = host + flag
	if host == 'client02':
		execute(ycsb, action, workload='workloada', contact='node01', set='assign', mark=mark, threads=50, runtime=runtime, flag=flag)
	elif host == 'client04':
		execute(ycsb, action, workload='workloadb', contact='node05', set='reg', mark=mark, threads=50, runtime=runtime, flag=flag)
		#execute(ycsb, action, workload='workloadb', contact='node05', set='reg', mark=mark, threads=50, recordcount=3400000, runtime=runtime, flag=flag)
	elif host == 'client05':
		execute(ycsb, action, workload='workloadd', contact='node10', set='puid', mark=mark, threads=50, runtime=runtime, flag=flag)
	elif host == 'client06':
		execute(ycsb, action, workload='workloade', contact='node15', set='prid', mark=mark, threads=50, runtime=runtime, flag=flag)

@roles('client')
@parallel
def get_log(action,mark):
	log_file = 'results/%s.%s.log' % (mark, action)
	with cd(WORKSHOP):
		get(log_file, LOGS_HOME)
			
@roles('state_clients')
def kill(force=False):
	"""Kills YCSB processes"""
	with settings(warn_only=True):
		run('ps -f -C java')
		run('killall java')
		#if force or confirm(red("Do you want to kill Java on the client?")):
		#	run('killall java')

#### stress tool ####
@roles('client')
def stress(action='run', n=5000000, threads=50, mark='stress', flag=None):
	n = int(n)
	if action not in ('run', 'load') or n < 1 or n > 5000000:
		return
	node_list = NODE_LIST
	conf_file = "stress_reg.yaml"
	ops = "ops\(insert=53,read=46,delete=1\)" if action == 'run' else "ops\(insert=1\)"
	log_file = "stress.%s.%d.%s.log" % (action, n, flag) if flag else "stress.%s.%d.log" % (action, n)
	local_dir = '/local/logs/%s/%s' % ('cassandra', mark)
	workshop = '/local/workshop/stress'
	if not os.path.isdir(local_dir):
		local('mkdir -p %s' % local_dir)
	cmd = 'cassandra-stress user profile=conf/%s %s n=%d cl=QUORUM no_warmup -rate threads=%s -mode native cql3 -key populate=1..%d -node %s -log file=out/%s' % (conf_file, ops, n, threads, n, node_list, log_file)
	with settings(warn_only=True, combine_stderr=False):
		with cd(workshop):
			run(cmd)
			get('out/%s' % log_file, local_dir)
		local('cat %s/%s' % (local_dir, log_file))

@parallel
@roles('servers')
def cleanup(db='aerospike'):
	with settings(warn_only=True, combine_stderr=False):
		run('service {0} stop'.format(db))
		run('rm -rf /local/data/{0}/*'.format(db))
