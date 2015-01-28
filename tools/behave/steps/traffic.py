from behave import *
from config import *
import os
import re

# -- REGISTER TYPE-CONVERTER: With behave
register_type(Integer=parse_int)
register_type(Float=parse_float)

@then('keep "{target}" traffic running "{runtime:Integer}" mins with "{workload}"')
def step_impl(context, target, runtime, workload):
	# assert target[-1] == '%'
	assert workload in WORKLOADS
	# get target TPS
	if target == '100%':
		target = 0
	elif 'max_tps' in context.response and target[-1] == '%':
		target = int(float(context.response['max_tps'])*float(target[:-1])/100)
	else:
		target = int(float(target))

	config = {}
	config.update(CONFIG)
	config['runtime'] = runtime
	config['runtime'] += WARMUPS[DB]
	case = list(set(RECORD_SIZES) & context.tags)
	assert len(case) == 1
	case = case[0]
	config['workload'] = case + '_' + workload
	print('running workload: {0}'.format(config['workload']))
	config['target'] = target
	config['mark'] = context.mark + '_' + config['workload']

	print('    target TPS: {0}'.format(config['target']))
	run_test(config)
	print(' '*8 + 'done')
	out_file = os.path.join(LOG_HOME, r'{0}/{1}_{2}/workload{2}.out'.format(DB, context.mark, config['workload']))
	max_tps = os.popen('grep Throughput {0} | cut -f 3'.format(out_file)).read()
	max_tps = re.findall('[\d.]+', max_tps)
	assert max_tps != []
	context.response = dict(max_tps=max_tps[0])

