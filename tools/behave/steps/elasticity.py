from behave import *
from config import *
import os
import re

# -- REGISTER TYPE-CONVERTER: With behave
register_type(Float=parse_float)
register_type(Integer=parse_int)

@then('grow "{nodes}" instances')
def step_impl(context, nodes):
	run('fab puppet -H {0}'.format(nodes))

@then('degrow "{nodes}" instances')
def step_impl(context, nodes):
	run('fab service:{0},stop -H {1}'.format(DB, nodes))

@then('grow new node from "{from_nodes:Integer}" to "{to_nodes:Integer}" with "{runtime:Integer}" mins and "{workload}"')
def step_impl(context, from_nodes, to_nodes, runtime, workload):
	mark_t = 'growth'
	sleep_time = runtime/(to_nodes-from_nodes +1)*60
	for t in context.tags:
		if re.match('\d+M', t):
			mark_t = mark_t + '_' + t
			break
	config = {}
	config.update(CONFIG)
	config['runtime'] = runtime
	config['target'] = 0
	case = list(set(RECORD_SIZES) & context.tags)
	assert len(case) == 1
	case = case[0]
	config['workload'] = case + '_' + workload
	config['mark'] = context.mark + '_' + mark_t

	## additional config
	config['threads'] *= 2
	config['clientcount'] *= 2
	config['servercount'] = from_nodes

	def func(context, sleep_time):
		steps_list = map(unicode.strip, context.text.split('\n'))
		print(' '*4 + steps_list[0])
		for stp in steps_list[1:]:
			sleep_status(sleep_time)
			print(' '*6 + stp)
			context.execute_steps(u'Then ' + stp)
			print(' '*8 + 'done')
		sleep_status(sleep_time)
	
	run_test(config, func, context, sleep_time)

@then('degrow node from "{from_nodes:Integer}" to "{to_nodes:Integer}" with "{runtime:Integer}" mins and "{workload}"')
def step_impl(context, from_nodes, to_nodes, runtime, workload):
	mark_t = 'degrowth'
	sleep_time = runtime/(from_nodes-to_nodes +1)*60
	for t in context.tags:
		if re.match('\d+M', t):
			mark_t = mark_t + '_' + t
			break
	config = {}
	config.update(CONFIG)
	config['runtime'] = runtime + WARMUPS[DB]
	config['target'] = 0
	case = list(set(RECORD_SIZES) & context.tags)
	assert len(case) == 1
	case = case[0]
	config['workload'] = case + '_' + workload
	config['mark'] = context.mark + '_' + mark_t

	## additional config
	config['threads'] *= 2
	config['clientcount'] *= 2
	config['servercount'] = from_nodes

	def func(context, sleep_time):
		steps_list = map(unicode.strip, context.text.split('\n'))
		print(' '*4 + steps_list[0])
		for stp in steps_list[1:]:
			sleep_status(sleep_time)
			print(' '*6 + stp)
			context.execute_steps(u'Then ' + stp)
			print(' '*8 + 'done')
		sleep_status(sleep_time)

	run_test(config, func, context, sleep_time)
