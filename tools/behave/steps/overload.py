from behave import *
from config import *
import os

OVER_INTV = 10*60

# -- REGISTER TYPE-CONVERTER: With behave
register_type(Integer=parse_int)
register_type(Float=parse_float)

@then('capacity overload "{runtime:Integer}" mins with read "{rworkload}" and insert "{iworkload}" based on "{recordcount:Integer}" records')
def step_impl(context, runtime, rworkload, iworkload, recordcount):
	mark_t = 'capacity'
	sleep_time = runtime/6*60
	config = {}
	config.update(CONFIG)
	case = list(set(RECORD_SIZES) & context.tags)
	assert len(case) == 1
	case = case[0]
	config['target'] = 0
	config['threads'] /= 2

	steps_list = map(unicode.strip, context.text.split('\n'))

	def insert_func(context, sleep_time):
		print(' '*4 + steps_list[1])
		for stp in steps_list[2:]:
			sleep_status(sleep_time)
			print(' '*6 + stp)
			context.execute_steps(u'Then ' + stp)
			print(' '*8 + 'done')
		sleep_status(sleep_time)

	def read_func(context, sleep_time):
		config['recordcount'] = recordcount
		config['runtime'] = runtime - sleep_time/60
		config['workload'] = case + '_' + iworkload
		config['mark'] = context.mark + '_' + mark_t + '_' + iworkload
		sleep_status(sleep_time)
		run_test(config, insert_func, context, sleep_time)

	print(' '*4 + steps_list[0])
	config['runtime'] = runtime
	config['workload'] = case + '_' + rworkload
	config['mark'] = context.mark + '_' + mark_t + '_' + rworkload
	run_test(config, read_func, context, sleep_time)

@then('traffic overload base on "{clientcount}" clients "{base_threads:Integer}" threads repeat "{repeats:Integer}" with "{runtime:Integer}" mins and "{workload}" for each running')
def step_impl(context, clientcount, base_threads, repeats, runtime, workload):
	mark_t = 'traffic'
	config = {}
	config.update(CONFIG)
	case = list(set(RECORD_SIZES) & context.tags)
	assert len(case) == 1
	case = case[0]
	config['workload'] = case + '_' + workload
	config['target'] = 0
	config['runtime'] = runtime
	config['clientcount'] = clientcount

	for thread in map(lambda x: base_threads*2**x, range(repeats)):
		config['threads'] = thread
		config['mark'] = context.mark + '_' + mark_t + '_' + str(thread)
		print('    Threads: {0}'.format(config['threads']))
		run_test(config)
		print(' '*8 + 'done')

