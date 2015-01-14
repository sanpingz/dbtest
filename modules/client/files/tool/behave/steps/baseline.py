from behave import *
from config import *
from time import sleep
import os


@given(u'stop cluster')
def step_impl(context):
	if DB == 'redis':
		run("fab remote_run:'pkill -9 redis-server' -R servers")
	else:
		run('fab service:{0},stop -R servers'.format(DB))
	#print('Stopped {0} cluster'.format(DB))

@given(u'clean disk')
def step_impl(context):
	run("fab remote_run:'rm -rf /local/data/{0}*' -R servers".format(DB))
	#print('Cleaned {0} disk'.format(DB))

@given(u'start cluster')
def step_impl(context):
	run('fab puppet -R servers'.format(DB))
	#print('Started {0} cluster'.format(DB))

@given(u'cluster is ready')
def step_impl(context):
	sleep(10)
	if DB == 'redis':
		# create cluster
		run('{0} create'.format(REDIS_TRIB))
		sleep(50)
	else:
		sleep(50)
	assert True

@when('load data into cluster')
def step_impl(context):
	assert len(context.tags) == 1
	sz = list(context.tags)[0]
	config = {}
	config.update(CONFIG)
	config['action'] = 'load'
	config['workload'] = sz + '_w100'
	config['runtime'] = 30
	config['threads'] = LOAD_THREADS
	config['target'] = 0
	config['mark'] = MARK_PREFIX + '_' + sz
	cmd = CMDS[0].format(**config)
	with open(LOG_FILE, 'a') as fdout:
		p = Popen(cmd, stdout=fdout, stderr=STDOUT, shell=True)
		p.wait()
	#print('Loaded {0} {1} data'.format(config['recordcount'], sz))

@then('run the baseline cases')
def step_impl(context):
	config = {}
	config.update(CONFIG)
	config['runtime'] += WARMUPS[DB]
	def max_adjust(t):
		t = int(float(t))
		if t < 10:
			return t
		t = str(t)
		str_t = t[0]
		str_t += '5' if int(t[1]) > 5 else '0'
		str_t += (len(t)-2)*'0'
		return int(str_t)

	for row in context.table:
		config['workload'] = row['workload']
		print('running workload: {0}'.format(config['workload']))
		assert len(context.tags) == 1
		case = list(context.tags)[0]
		# find max tps
		config['target'] = 0
		config['mark'] = MARK_PREFIX + '_' + config['workload'] + '_' + str(SMP+1)
		print('    target TPS: {0}'.format(config['target']))
		run_test(config)
		print(' '*8 + 'done')
		sleep(10)
		out_file = os.path.join(LOG_HOME, r'{0}/{1}_{2}_{3}/workload{2}.out'.format(DB, MARK_PREFIX, config['workload'], SMP+1))
		assert os.path.isfile(out_file)
		_tps = os.popen('grep Throughput {0}|cut -f 3'.format(out_file)).read()
		assert _tps != ''
		max_tps_adjust = max_adjust(_tps)
		interval = max_tps_adjust/SMP
		samples = range(interval, max_tps_adjust, interval)
		samples.append(max_tps_adjust)
		count = 1
		for target in samples:
			config['target'] = target
			mark = MARK_PREFIX + '_' + config['workload'] + '_' + str(count)
			count += 1
			config['mark'] = mark
			print('    target TPS: {0}'.format(config['target']))
			run_test(config)
			print(' '*8 + 'done')
			sleep(10)
