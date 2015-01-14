from behave import *
import time
from time import sleep
#from os import system as run
from subprocess import call as run
from subprocess import Popen, PIPE, STDOUT

#DB = 'aerospike'
DB = 'infinispan'

log_file = '/local/logs/out.log'

SMP = 10
PROCS = {
	'aerospike': 'asd',
	'redis': 'redis-server',
	'infinispan': 'java',
	'cassandra': 'java'
}
WARMUPS = {
	'aerospike': 0.05,
	'redis': 1.7,
	'infinispan': 0.05,
	'cassandra': 0.05
}
MAX_TPS = {
	'aerospike': {
		'1k': {
			'1k_r100': 500000,
			'1k_r50w50': 500000,
			'1k_w100': 500000
		},
		'5k': {
			'1k_r100': 250000,
			'1k_r50w50': 250000,
			'1k_w100': 250000
		},
		'32k': {
			'1k_r100': 50000,
			'1k_r50w50': 50000,
			'1k_w100': 50000
		}
	},
	'redis' : {
		'1k': {
			'1k_r100': 500000,
			'1k_r50w50': 500000,
			'1k_w100': 500000
		},
		'5k': {
			'1k_r100': 250000,
			'1k_r50w50': 250000,
			'1k_w100': 250000
		},
		'32k': {
			'1k_r100': 50000,
			'1k_r50w50': 50000,
			'1k_w100': 50000
		}
	},
	'infinispan': {
		'1k': {
			'1k_r100': 500000,
			'1k_r50w50': 100000,
			'1k_w100': 50000
		},
		'5k': {
			'5k_r100': 250000,
			'5k_r50w50': 50000,
			'5k_w100': 50000
		},
		'32k': {
			'32k_r100': 50000,
			'32k_r50w50': 10000,
			'32k_w100': 10000
		}
	},
	'cassandra': {
		'1k': {
			'1k_r100': 500000,
			'1k_r50w50': 100000,
			'1k_w100': 100000
		},
		'5k': {
			'5k_r100': 250000,
			'5k_r50w50': 50000,
			'5k_w100': 50000
		},
		'32k': {
			'32k_r100': 50000,
			'32k_r50w50': 10000,
			'32k_w100': 10000
		}
	}
}
CONFIG = {
	'db': DB,
	'action': 'run',
	'workload': 'a',
	'recordcount': 4000000,
	'runtime': 3,
	'threads': 400,
	'target': 0,
	'mark': 'baseline',
	'save': 'true',
	'proc': PROCS[DB],
	'nic': 'eth0',
	'device': 'vda2',
}
CMDS = [
	'fab run_test:{action},workload={workload},recordcount={recordcount},runtime={runtime},threads={threads},target={target},mark={mark},save={save} --set db={db}',
	'fab monitorit:mark={mark},proc={proc},nic={nic},device={device},duration={runtime},save={save} --set db={db}'
]


def run_test(config):
	procs = []
	timeout = CONFIG['runtime']*60 + 30
	with open(log_file, 'a') as fdout:
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
					p[0].terminate()
					done_procs += 1
					p[1] = False
					print(' '*6 + '{1} stop at: {0}'.format(time.time(), p[2]))
					break

# steps

@given(u'stop cluster')
def step_impl(context):
	#run('fab service:{0},stop'.format(DB))
	pass

@given(u'clean disk')
def step_impl(context):
	#run("fab remote_run:'rm -rf /local/data/{0}/*'".format(DB))
	pass

@given(u'start cluster')
def step_impl(context):
	pass

@given(u'cluster is ready')
def step_impl(context):
	assert True

@when('load data into cluster')
def step_impl(context):
	assert True

@then('run the baseline cases')
def step_impl(context):
	config = {}
	config.update(CONFIG)
	config['runtime'] += WARMUPS[DB]
	for row in context.table:
		config['workload'] = row['workload']
		print('running workload: {0}'.format(config['workload']))
		assert len(context.tags) == 1
		case = list(context.tags)[0]
		max_tps = MAX_TPS[DB][case][config['workload']]
		interval = max_tps/SMP
		samples = range(interval, max_tps, interval)
		samples.append(max_tps)
		samples.append(0)
		count = 1
		for target in samples:
			config['target'] = target
			mark = 'bl_' + config['workload'] + '_' + str(count)
			count += 1
			config['mark'] = mark
			print('    target TPS: {0}'.format(config['target']))
			run_test(config)
			print(' '*8 + 'done')
			sleep(10)
