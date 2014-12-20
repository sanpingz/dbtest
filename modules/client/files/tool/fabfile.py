from fabric.api import run, env, put, get, roles, execute, local, parallel, serial, reboot, cd, settings, hosts, task, runs_once
from fabric.colors import green, blue, red
from fabric.contrib.console import confirm
import re, os, json, random
from hashlib import md5 as hash

N = env.get('n') or 24
PREFIX = env.get('p') or 'node'
N=int(N)

DB = env.get('db') or 'default'
COORDINATOR='node01'
WORKSHOP='/local/workshop/{0}'.format(DB)
LOGS_HOME='/local/logs/{0}'.format(DB)
MONITOR_HOME='/tmp/{0}'.format(DB)
if env.get('n') or env.get('p') or env.get('h'):
	env.hosts = env.get('h') or [ "%s%02d" % (PREFIX,x) for x in range(1,N+1)]

CLIENTS = ["%s%02d" % ('client',x) for x in range(1,10+1)]
DBS = ["%s%02d" % ('node',x) for x in range(1,N+1)]
env.roledefs = {
	#list of client hosts
	'clients': CLIENTS[:10],
	'state_clients': CLIENTS[:6],
	#list of DB server hosts
	'servers': DBS[:20],
	'state_servers': DBS[:20],
	'checkpoint_servers': DBS[20:22],
	#list of all available hosts
	'all_hosts': CLIENTS + DBS,
}

NODE_LIST = ",".join(env.roledefs['servers'])

#### Common ####
@roles('all_hosts')
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
		run('service {0} {1}'.format(name, action))

@parallel
def os_reboot():
	reboot()

#### Puppet ####
@parallel
@roles('servers', 'clients')
def puppet():
	run('puppet agent -t', warn_only=True, combine_stderr=False)

def init_puppet():
	name=run('hostname')
	try:
		local('puppet cert clean {0}.openstacklocal'.format(name), warn_only=True, combine_stderr=False)
	except: pass
	run('find /var/lib/puppet/ssl -name {0}.openstacklocal.pem -delete'.format(name), warn_only=True, combine_stderr=False)

#### Deploy ####
@roles('servers')
@parallel
def deploy_as():
	service = 'aerospike'
	pkg = 'aerospike.tgz'
	dist_home = '/local/dist'
	files_home = '/local/puppet/files'
	put('{0}/{1}'.format(files_home,pkg), dist_home)
	run('rm -rf /tmp/*{0}*'.format(service))
	run('tar -zxvf {0}/{1} -C /tmp/'.format(dist_home,pkg))
	run('if [ "$(rpm -qa|grep {0})" == "" ]; then test -f /tmp/*{0}*/asinstall && cd /tmp/*{0}*/ && ./asinstall; fi'.format(service), warn_only=True, combine_stderr=False)

#### Disk ####
@roles('servers')
@parallel
def disk_format():
	run('printf "n\np\n2\n\n\nw\n" | fdisk /dev/vda', warn_only=True, combine_stderr=False)

@roles('servers')
@parallel
def disk_mount():
	run('mkfs.ext3 /dev/vda2 && rm -rf /local/data && mkdir -p /local/data && mount /dev/vda2 /local/data && echo "/dev/vda2               /local/data             ext3    defaults        0 0" >> /etc/fstab', warn_only=True, combine_stderr=False)

@roles('servers')
def disk_space():
	run('df -h')

#### Monitor ####
@roles('servers')
@parallel
def monitor(mark, proc='asd', nic='eth0', device='vda2', duration=1):
	host = run('hostname -s')
	#log_file = 'monitor.{0}.log'.format(host)
	#log_dir = '%s/%s' % (LOGS_HOME, mark)
	#local_log = '%s/%s' % (log_dir, log_file)
	with settings(warn_only=True, combine_stderr=False):
		run('[ ! -d {0} ] && mkdir -p {0}'.format(MONITOR_HOME))
		#nic = 'eth1' if run('ifconfig eth0|grep 37.3.3') == '' else 'eth0'
		with cd(MONITOR_HOME):
			put('/local/tool/bin/monitor.py', MONITOR_HOME)
			run('chmod +x {0}/monitor.py'.format(MONITOR_HOME))
			return run('./monitor.py -p {0} -n {1} -d {2} -f {3} -u {4}'.format(proc, nic, device, 'json', duration))
			#get(log_file, local_log)

@runs_once
#@parallel
#@roles('servers')
def monitorit(mark='monitor', proc='asd', nic='eth0', device='vda2', duration=1, save='true'):
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
	out = execute(monitor, mark, proc=proc, nic=nic, device=device, duration=duration)
	for k,v in out.items():
		try:
			data[k] = json.loads(str(v))
		except ValueError, e:
			print(e)
			exit(1)

	def cmm(prev, curr):
		return {
				'avg': prev.get('avg')+curr.get('avg'),
				'max': max(prev.get('max'), curr.get('max')),
				'min': min(prev.get('min'), curr.get('min'))
		}
	def pretty_print():
		prt = []
		prt.append('%CPU\navg\tmax\tmin\n{avg:.2f}\t{max:.2f}\t{min:.2f}'.format(**ret['cpu']))
		prt.append('%MEM\navg\tmax\tmin\n{avg:.2f}\t{max:.2f}\t{min:.2f}'.format(**ret['mem']))
		prt.append('Disk read ({{unit}})\navg\tmax\tmin\n{avg:.2f}\t{max:.2f}\t{min:.2f}'.format(**ret['disk']['read']).format(unit=unit['disk']))
		prt.append('Disk write ({{unit}})\navg\tmax\tmin\n{avg:.2f}\t{max:.2f}\t{min:.2f}'.format(**ret['disk']['write']).format(unit=unit['disk']))
		prt.append('Network recv ({{unit}})\navg\tmax\tmin\n{avg:.2f}\t{max:.2f}\t{min:.2f}'.format(**ret['net']['recv']).format(unit=unit['net']))
		prt.append('Network sent ({{unit}})\navg\tmax\tmin\n{avg:.2f}\t{max:.2f}\t{min:.2f}'.format(**ret['net']['sent']).format(unit=unit['net']))
		print('\n'.join(prt))
		if save == 'true':
			fil = LOGS_HOME+'/'+mark+'/'+'monitor.out'
			try:
				with open(fil, 'w') as f:
					f.write('\n'.join(prt))
					print('')
					print("Saved as " + fil)
			except IOError, e:
				print(e)

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
@roles('clients')
@parallel
def ycsb(action, workload='workloada', db=DB, mark='default', target=None, threads=50, runtime=10, recordcount=5000000, flag=None):
	threads = int(threads)
	recordcount = int(recordcount)
	clients_num = len(env.roledefs['clients'])
	_host = 'host'
	ops = ''
	hostname = run('hostname -s')
	if action not in ['load','run']:
		print('Bad action, {0}'.format(action))
		return None
	contact = random.choice(env.roledefs['servers'])
	if db == 'cassandra':
		_host += 's'
		contact = NODE_LIST
	elif db == 'redis':
		_host = 'redis.'+_host
	log_file = '{0}.{1}.{2}.{3}log'.format(mark, workload, action, flag) if flag else '{0}.{1}.{2}.log'.format(mark, workload, action)
	local_log_dir = '{0}/{1}'.format(LOGS_HOME, mark)
	local_log = local_log_dir + '/' + log_file.replace(mark, hostname)
	if not os.path.isdir(local_log_dir):
		local('mkdir -p {0}'.format(local_log_dir))
	ops = ops + " -p recordcount={0}".format(recordcount) if recordcount else ops
	ops = ops + " -p maxexecutiontime={0}".format(runtime)
	if clients_num > 1:
		if action == 'load':
			if recordcount is None:
				print('recordcount required when clients number > 1')
				return None
			idx = int(hostname[-2:])
			delta = int(recordcount)/clients_num
			insertstart = (idx-1)*delta
			insertcount = delta
			if idx == clients_num:
				insertcount = int(recordcount)-insertstart
			ops = ops + " -p insertstart={0} -p insertcount={1}".format(insertstart, insertcount)
		elif action == 'run':
			if target is None:
				print('target required when clients number > 1')
				return None

	if action == 'load':
		ops = ops + " -target 0"
	elif target:
		target = int(target)
		ops = ops + " -target {0}".format(target/clients_num)
	ops = ops + " -threads {0}".format(threads/clients_num)
	with settings(warn_only=True, combine_stderr=False):
		run('[ ! -d {0} ] && mkdir -p {0}'.format(WORKSHOP))
		with cd(WORKSHOP):
			run('ycsb {0} {1} -P ../workloads/{2} -p {3}={4} {5} -s > {6}'.format(action, db, workload, _host, contact, ops, log_file))
			get(log_file, local_log)
			#return local('get_sum {0}'.format(local_log))
			return run('get_sum {0}'.format(log_file))

@parallel
def run_test(action, workload='a', runtime=10, threads=50, target=None, recordcount=5000000, mark='default', flag=None, save='true'):
	runtime=int(float(runtime)*60)
	workload = 'workload'+workload
	if DB == 'default':
		print('Bad db name, {0}'.format(DB))
		exit(1)
	if action not in ['load','run']:
		print('Bad action, {0}'.format(action))
		exit(1)
	out = ''
	sum_list = ['Operations', 'Retries', 'Return=0', 'Reconnections', 'Throughput(ops/sec)']
	avg_list = ['AverageLatency(ms)', '95thPercentileLatency(ms)', '99thPercentileLatency(ms)', '99.99thPercentileLatency(ms)']
	max_list = ['MaxLatency(ms)', 'RunTime(ms)']
	min_list = ['MinLatency(ms)']
	def converte(x):
		x[0] = x[0][1:-1]
		try:
			x[2] = float(re.findall(r'[\d.]+', x[2])[0])
		except Exception, e:
			print(e)
			print(x)
			exit(1)
		return x
	
	def gen_key(a):
		return hash(a[0]+a[1]).hexdigest()

	def handle(prev, curr):
		if prev is None:
			return curr
		if len(prev) < len(curr):
			prev, curr = curr, prev
		while True:
			found = False
			c = curr.pop(0)
			for p in prev:
				if c[0]+c[1] == p[0]+p[1]:
					if p[1] in max_list:
						p[2] = max(p[2], c[2])
					elif p[1] in min_list:
						p[2] = min(p[2], c[2])
					else:
						p[2] += c[2]
					found = True
					break
			if curr == []:
			   break
			if found == False:
			   p.append(c)
		return prev
					
	def aggregate():
		ret = None
		count = 0
		for lines in out.values():
			tmp = []
			if lines is None:
				print('No results returned')
				exit(1)
			for line in lines.splitlines():
				rec = converte(map(lambda x: x.strip(), line.split(',')))
				tmp.append(rec)
			ret = handle(ret, tmp)
			if ret is None:
				ret = tmp
			count += 1
		for i in range(len(ret)):
			if ret[i][1] in avg_list:
				ret[i][2] /= count
		return ret
	
	def pretty_print(ret):
		print workload
		for rec in ret:
			rec[2] = '{0:.2f}'.format(rec[2])
			print '\t'.join(rec)
		if save == 'true' and ret:
			fil = LOGS_HOME+'/'+mark+'/'+workload+'.out'
			try:
				with open(fil, 'w') as f:
					f.writelines(map(lambda x: '\t'.join(x)+'\n', ret))
					print("Saved as "+fil)
			except IOError, e:
				print(e)

	out = execute(ycsb, action, workload=workload, mark=mark, threads=threads, target=target, recordcount=recordcount, runtime=runtime, flag=flag)
	ret = aggregate()
	pretty_print(ret)

@roles('client')
@parallel
def get_log(action,mark):
	log_file = 'results/{0}.{1}.log'.format(mark, action)
	with cd(WORKSHOP):
		get(log_file, LOGS_HOME)
			
@roles('clients')
def kill(force=False):
	"""Kills YCSB processes"""
	with settings(warn_only=True):
		run('ps -f -C java')
		run('killall java')
		#if force or confirm(red("Do you want to kill Java on the client?")):
		#	run('killall java')

@roles('clients')
@parallel
def scanning(fc=1, threads=5, target=0, repeat=10, ra='false', rs='false'):
	hostname = run('hostname -s')
	target = int(target)
	PARTITIONS=4096
	N = len(env.roledefs['clients'])
	ppc = PARTITIONS/N
	idx = int(hostname[-2:])
	r1 = (idx-1)*ppc
	r2 = idx*ppc
	if idx == N:
		r2 = PARTITIONS
	partition = '{0}-{1}'.format(r1, r2)
	with settings(warn_only=True, combine_stderr=False):
		with cd('/local/tool/scan'):
			cmd = './multi_scan -f {0} -t {1} -r {2} -P {3} -g {4} -d'.format(fc, threads, repeat, partition, target/N)
			if ra == 'true':
				cmd += ' -a'
			if rs == 'true':
				cmd += ' -s'
			return run(cmd)

@parallel
@runs_once
def run_scan(fc=1, threads=5, target=0, repeat=10, ra='false', rs='false'):
	count = 0
	stime = 0
	rtime = 0
	mtime = 0
	tps = 0
	out = execute(scanning, fc=fc, threads=threads, target=target, repeat=repeat, ra=ra, rs=rs)
	n = len(out.values())
	for lines in out.values():
		for line in lines.splitlines():
			if re.match('Total run time:', line):
				rtime += float(line.split(':')[-1].strip()[:-1])
			elif re.match('Average scanning count:', line):
				count += int(line.split(':')[-1].strip())
			elif re.match('Average scanning time:', line):
				t = float(line.split(':')[-1].strip()[:-1])
				mtime = max(mtime, t)
				stime += t
			elif re.match('Total TPS:', line):
				tps += float(line.split(':')[-1].strip())
				break
	print('Scanning count: {0}'.format(count))
	print('Average scanning time: {0:.2f}s'.format(stime/n))
	print('Max scanning time: {0:.2f}s'.format(mtime))
	print('Average run time: {0:.2f}s'.format(rtime/n))
	print('Total TPS (ops/sec): {0:.2f}'.format(tps))

#### stress tool ####
@roles('client')
def stress(action='run', n=5000000, threads=50, mark='stress', flag=None):
	n = int(n)
	if action not in ('run', 'load') or n < 1 or n > 5000000:
		return
	node_list = NODE_LIST
	conf_file = "stress_reg.yaml"
	ops = "ops\(insert=53,read=46,delete=1\)" if action == 'run' else "ops\(insert=1\)"
	log_file = "stress.{0}.{1}.{2}.log".format(action, n, flag) if flag else "stress.{0}.{1}.log".format(action, n)
	local_dir = '/local/logs/{0}/{1}'.format('cassandra', mark)
	workshop = '/local/workshop/stress'
	if not os.path.isdir(local_dir):
		local('mkdir -p {0}'.format(local_dir))
	cmd = 'cassandra-stress user profile=conf/{0} {1} n={2} cl=QUORUM no_warmup -rate threads={3} -mode native cql3 -key populate=1..{4} -node {5} -log file=out/{6}'.format(conf_file, ops, n, threads, n, node_list, log_file)
	with settings(warn_only=True, combine_stderr=False):
		with cd(workshop):
			run(cmd)
			get('out/{0}'.format(log_file), local_dir)
		local('cat {0}/{1}'.format(local_dir, log_file))

@parallel
@roles('servers')
def cleanup(db='aerospike'):
	with settings(warn_only=True, combine_stderr=False):
		run('service {0} stop'.format(db))
		run('rm -rf /local/data/{0}/*'.format(db))
