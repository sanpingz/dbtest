import time
from time import sleep
from subprocess import Popen, PIPE, STDOUT, call

DB = 'aerospike'
MARK_PREFIX = 'baseline'

LOG_FILE = r'/local/logs/out.log'
LOG_HOME = r'/local/logs'


SMP = 10
LOAD_THREADS = 200
REDIS_TRIB = '/local/tool/redis-trib'

PROCS = {
	'aerospike': 'asd',
	'redis': 'redis-server',
	'infinispan': 'java',
	'cassandra': 'java'
}

CONFIG = {
	'db': DB,
	'action': 'run',
	'workload': 'a',
	'recordcount': 4000000,
	'runtime': 5,
	'threads': 400,
	'target': 0,
	'mark': 'baseline',
	'save': 'true',
	'proc': PROCS[DB],
	'nic': 'eth0',
	'device': 'vda2',
}

WARMUPS = {
	'aerospike': 0.05,
	'redis': 1.7,
	'infinispan': 0.05,
	'cassandra': 0.05
}

CMDS = [
	'fab run_test:{action},workload={workload},recordcount={recordcount},runtime={runtime},threads={threads},target={target},mark={mark},save={save} --set db={db}',
	'fab monitorit:mark={mark},proc={proc},nic={nic},device={device},duration={runtime},save={save} --set db={db}'
]


def run(cmd, *args, **kwargs):
	with open(LOG_FILE, 'a') as fdout:
		call(cmd, *args, shell=True, stdout=fdout, stderr=STDOUT, **kwargs)

def run_test(config):
	procs = []
	timeout = CONFIG['runtime']*60 + 30
	with open(LOG_FILE, 'a') as fdout:
		for cmd in CMDS:
			cmd = cmd.format(**config)
			p = Popen(cmd, stdout=fdout, stderr=STDOUT, shell=True)
			print(' '*4 + cmd)
			print(' '*6 + 'start at: {0}'.format(time.time()))
			procs.append([p, True, cmd.split(':')[0].split()[-1]])
			sleep(WARMUPS[DB]*60)
		all_procs = len(procs)
		done_procs = 0
		sleep(CONFIG['runtime']*60)
		count = CONFIG['runtime']*60
		while done_procs < all_procs:
			sleep(1)
			count += 1
			for p in procs:
				if p[1] and p[0].poll() is not None:
					done_procs += 1
					p[1] = False
					print(' '*6 + '{1} stop at: {0}'.format(time.time(), p[2]))
					#do something done this process
				else:
					continue
				if count > timeout:
					try: 
						if p[2] == 'run_test':
							call('fab kill:proc=java -R clients', shell=True)
						else:
							p[0].kill()
					except OSError,e:
						print(e)
					done_procs += 1
					p[1] = False
					print(' '*6 + '{1} stop at: {0}'.format(time.time(), p[2]))
					break

