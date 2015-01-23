from behave import *
from config import *
import os

# -- REGISTER TYPE-CONVERTER: With behave
register_type(Float=parse_float)

@then('kill "{nodes}" instances')
def step_impl(context, nodes):
	run('fab remote_run:"pkill -9 {0}" -H {1}'.format(PROCS[DB], nodes))

@then('stop "{nodes}" instances')
def step_impl(context, nodes):
	run('fab os_reboot -H {0}'.format(nodes))

@then('start "{nodes}" instances')
def step_impl(context, nodes):
	run('fab puppet -H {0}'.format(nodes))

@then('failover "{runtime:Float}" mins with "{target:Float}" "{workload}" by "{mode}"')
def step_impl(context, runtime, target, workload, mode):
	assert mode in ('hot', 'cold')
	sleep_time = runtime/3*60
	mark_t = mode + '_' + str(int(target*100))
	config = {}
	config.update(CONFIG)
	config['runtime'] = runtime
	if target == 1:
		config['target'] = 0
	else:
		assert 'max_tps' in context.response
		config['target'] = int(target*float(context.response['max_tps']))
	case = list(set(RECORD_SIZES) & context.tags)
	assert len(case) == 1
	case = case[0]
	config['workload'] = case + '_' + workload
	config['mark'] = context.mark + '_' + mark_t

	def func(context, sleep_time):
		steps_list = map(unicode.strip, context.text.split('\n'))
		print(' '*4 + steps_list[0])
		sleep_status(sleep_time)
		for stp in steps_list[1:]:
			print(' '*6 + stp)
			context.execute_steps(u'Then ' + stp)
			print(' '*8 + 'done')
			if mode == 'cold':
				sleep_status(sleep_time)
		if mode == 'hot':
			sleep_status(2*sleep_time)

	run_test(config, func, context, sleep_time)
