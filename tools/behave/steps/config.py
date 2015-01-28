import time
import os
import sys
import parse
import time
from subprocess import Popen, PIPE, STDOUT, call

DB = 'aerospike'
LOG_HOME = r'/local/logs'
LOG_FILE = os.path.join(LOG_HOME, 'out.log')

LOAD_THREADS = 100
RUN_THREADS = 100
#LOAD_THREADS = 200
#RUN_THREADS = 400
SAMPLE_POINTS = 10
REDIS_TRIB = '/local/tools/redis-trib'

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
	'recordcount': 2000000,
	'runtime': 30,
	'threads': RUN_THREADS,
	'target': 0,
	'clientcount': 2,
	'servercount': 4,
	'mark': 'baseline',
	'save': 'true',
	'proc': PROCS[DB],
	'nic': 'eth0',
	'device': 'vda2',
}

WARMUPS = {
	'aerospike': 0.05,
	'redis': 1.0,
	'infinispan': 0.05,
	'cassandra': 0.05
}

RECORD_SIZES = ['1k', '5k', '32k']
WORKLOADS = ['r100', 'r50w50', 'w100', 'i100']

CMDS = [
	'fab run_test:{action},workload={workload},recordcount={recordcount},runtime={runtime},threads={threads},target={target},mark={mark},save={save} --set db={db},cc={clientcount},sc={servercount}',
	'fab monitorit:mark={mark},proc={proc},nic={nic},device={device},duration={runtime},save={save} --set db={db},sc={servercount}'
]

# -- TYPE CONVERTER: For a simple, positive integer number.
@parse.with_pattern(r"\d+")
def parse_int(text):
	return int(text)

@parse.with_pattern(r"\d+\.?\d*%?")
def parse_float(text):
	if text[-1] == '%':
		return float(text[:-1])/100
	return float(text)

def sleep_status(sleep_time, status=True, rjust=6):
	sleep_time = int(sleep_time)
	if sleep_time <= 60 or not status:
		time.sleep(sleep_time)
	else:
		flush_intv = 10
		count = 0
		time.sleep(sleep_time-sleep_time/flush_intv*flush_intv)
		while True:
			msg = ' '*rjust + 'sleep {0} mins, remaining: {1} seconds    '.format(sleep_time/60, sleep_time - count*flush_intv)
			sys.stdout.write("\r{0}".format(msg))
			sys.stdout.flush()
			if count*flush_intv >= sleep_time:
				print('')
				break
			time.sleep(flush_intv)
			count += 1

def run(cmd, *args, **kwargs):
	with open(LOG_FILE, 'a') as fdout:
		call(cmd, *args, shell=True, stdout=fdout, stderr=STDOUT, **kwargs)

def run_test(config, func=None, *args, **kargs):
	procs = []
	timeout = 30
	with open(LOG_FILE, 'a') as fdout:
		for cmd in CMDS:
			cmd = cmd.format(**config)
			p = Popen(cmd, stdout=fdout, stderr=STDOUT, shell=True)
			print(' '*4 + cmd)
			print(' '*6 + 'start at: {0}'.format(time.time()))
			procs.append([p, True, cmd.split(':')[0].split()[-1]])
			sleep_status(WARMUPS[DB]*60)
		all_procs = len(procs)
		done_procs = 0
		count = 0

		if func is None:
			sleep_status(config['runtime']*60)
		else:
			func(*args, **kargs)

		while done_procs < all_procs:
			time.sleep(1)
			count += 1
			for p in procs:
				if p[1] and p[0].poll() is not None:
					done_procs += 1
					p[1] = False
					print(' '*6 + '{1} stop at: {0}'.format(time.time(), p[2]))
					#do something done this process
				elif count > timeout:
					try: 
						if p[2] == 'run_test':
							call('fab kill:proc=java -R clients --set cc={0}'.format(config['clientcount']), shell=True)
						else:
							p[0].kill()
					except OSError,e:
						print(e)
					done_procs += 1
					p[1] = False
					print(' '*6 + '{1} stop at: {0}'.format(time.time(), p[2]))
	
