from behave import *
from config import *
import os

register_type(Integer=parse_int)
register_type(Float=parse_float)

@given(u'stop cluster')
def step_impl(context):
	if DB == 'redis':
		run("fab remote_run:'pkill -9 redis-server' -R all_servers")
	else:
		run('fab service:{0},stop -R all_servers'.format(DB))
	#print('Stopped {0} cluster'.format(DB))

@given(u'clean disk')
def step_impl(context):
	run("fab remote_run:'rm -rf /local/data/{0}*' -R all_servers".format(DB))
	#print('Cleaned {0} disk'.format(DB))

@given(u'start cluster')
def step_impl(context):
	run('fab puppet -R servers'.format(DB))
	#print('Started {0} cluster'.format(DB))

@given(u'start cluster size "{servercount:Integer}"')
def step_impl(context, servercount):
	run('fab puppet -R servers --set sc={1}'.format(DB, servercount))
	#print('Started {0} cluster'.format(DB))

@given(u'cluster is ready')
def step_impl(context):
	sleep_status(10)
	if DB == 'redis':
		# create cluster
		run('{0} create'.format(REDIS_TRIB))
	sleep_status(50)
	assert True

@when('load "{recordcount:Integer}" records into cluster with "{workload}"')
def step_impl(context, recordcount, workload):
	assert workload in WORKLOADS
	sz = list(set(RECORD_SIZES) & context.tags)
	assert len(sz) == 1
	sz = sz[0]
	config = {}
	config.update(CONFIG)
	config['action'] = 'load'
	config['workload'] = sz + '_' + workload
	config['runtime'] = 30
	config['threads'] = LOAD_THREADS
	config['target'] = 0
	config['recordcount'] = recordcount
	config['mark'] = context.mark + '_' + sz + '_' + 'load'
	cmd = CMDS[0].format(**config)
	with open(LOG_FILE, 'a') as fdout:
		p = Popen(cmd, stdout=fdout, stderr=STDOUT, shell=True)
		p.wait()
	#print('Loaded {0} {1} data'.format(config['recordcount'], sz))

@then('run the baseline cases')
def step_impl(context):
	sleep_time = 10
	config = {}
	config.update(CONFIG)
	config['runtime'] += WARMUPS[DB]

	for row in context.table:
		config['workload'] = row['workload']
		print('running workload: {0}'.format(config['workload']))
		case = list(set(RECORD_SIZES) & context.tags)
		assert len(case) == 1
		case = case[0]
		# find max tps
		config['target'] = 0
		config['mark'] = context.mark + '_' + config['workload'] + '_' + str(SAMPLE_POINTS+1)
		print('    target TPS: {0}'.format(config['target']))
		run_test(config)
		print(' '*8 + 'done')
		sleep_status(sleep_time)
		out_file = os.path.join(LOG_HOME, r'{0}/{1}_{2}_{3}/workload{2}.out'.format(DB, context.mark, config['workload'], SAMPLE_POINTS+1))
		assert os.path.isfile(out_file)
		_tps = os.popen('grep Throughput {0}|cut -f 3'.format(out_file)).read()
		assert _tps != ''
		max_tps = int(float(_tps))
		interval = max_tps/SAMPLE_POINTS
		samples = range(interval, max_tps, interval)
		samples.append(max_tps)
		count = 1
		for target in samples:
			config['target'] = target
			mark = context.mark + '_' + config['workload'] + '_' + str(count)
			count += 1
			config['mark'] = mark
			print('    target TPS: {0}'.format(config['target']))
			run_test(config)
			print(' '*8 + 'done')
			sleep_status(sleep_time)
