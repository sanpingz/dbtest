#!/usr/bin/env python
__author__ = 'sanpingz'
__doc__ = """The default unit for bandwidth and disk read/write speed are MBytes/s"""

import time
import socket
import pprint
import argparse
import json

try:
	import psutil as ps
except ImportError, e:
	print(e)

pp = pprint.PrettyPrinter(depth=4)

# The default UNIT is fine at most time, if you change UNIT, you also need to change M.
# UNIT = 'KBytes/s', M = 1000.0
# UNIT = 'GBytes/s', M = 1000000000.0
UNIT = 'MBytes/s'
M = 1000000.0

def get_process(name):
	procs = filter(lambda proc: proc.as_dict(attrs=['name']).get('name') == name, ps.process_iter())
	return procs and procs[0]

def get_cpu_mem(name=None, interval=1.0):
	ret = dict(cpu=0, mem=0)
	if name:
		proc = get_process(name)
		if 'cpu_percent' in dir(proc):
			ret['cpu'] = proc.cpu_percent(interval=interval)
		elif 'get_cpu_percent' in dir(proc):
			ret['cpu'] = proc.get_cpu_percent(interval=interval)
		if 'memory_percent' in dir(proc):
			ret['mem'] = proc.memory_percent()
		elif 'get_memory_percent' in dir(proc):
			ret['mem'] = proc.get_memory_percent()
		return ret
	if 'cpu_percent' in dir(ps):
		ret['cpu'] = ps.cpu_percent(interval=interval)
	elif 'get_cpu_percent' in dir(ps):
		ret['cpu'] = ps.get_cpu_percent(interval=interval)
	ret['mem'] = ps.virtual_memory().percent
	return ret

def get_disk_iostat(device=None):
	'''
	wirte_time, read_time is in milliseconds
	'''
	if not device:
		return ps.disk_io_counters(perdisk=False)
	return ps.disk_io_counters(perdisk=True).get(device)

def get_disk_io(device=None, interval=1.0):
	try:
		iostat = get_disk_iostat(device=device)
		_read = iostat.read_bytes
		_write= iostat.write_bytes
		time.sleep(interval)
		iostat = get_disk_iostat(device=device)
		read_bytes = iostat.read_bytes - _read
		write_bytes = iostat.write_bytes - _write
	except:
		read_bytes = 0
		write_bytes = 0
	return dict(read=read_bytes/M/interval, write=write_bytes/M/interval)

def get_net_iostat(nic=None):
	if not nic:
		if 'net_io_counters' in dir(ps):
			return ps.net_io_counters(pernic=False)
		return ps.network_io_counters(pernic=False)
	if 'net_io_counters' in dir(ps):
		return ps.net_io_counters(pernic=False)
	return ps.network_io_counters(pernic=True).get(nic)

def get_net_io(nic=None, interval=1.0):
	iostat = get_net_iostat(nic=nic)
	d = iostat._asdict()
	_sent = iostat.bytes_sent
	_recv= iostat.bytes_recv
	time.sleep(interval)
	iostat = get_net_iostat(nic=nic)
	bytes_sent = iostat.bytes_sent - _sent
	bytes_recv = iostat.bytes_recv - _recv
	return dict(sent=bytes_sent/M/interval, recv=bytes_recv/M/interval)

def system_info(mounted_point='/'):
	return dict(
			hostname=socket.gethostname().split('.')[0],
			psutil_version='.'.join(map(str, ps.version_info)),
			mem_total=ps.virtual_memory().total/M,
			mem_used=ps.virtual_memory().used/M,
			disk_total=ps.disk_usage(mounted_point).total/M,
			disk_used=ps.disk_usage(mounted_point).used/M
		)

def get_summary(tmp):
	ret = {}
	if filter(lambda x: x not in tmp.keys(), ['cm', 'disk', 'net']):
		return ret
	ret['cpu'] = dict(avg=tmp['cm'][0]/tmp['cm'][6], max=tmp['cm'][1], min=tmp['cm'][2])
	ret['mem'] = dict(avg=tmp['cm'][3]/tmp['cm'][6], max=tmp['cm'][4], min=tmp['cm'][5])
	ret['disk'] = dict(
		read=dict(avg=tmp['disk'][0]/tmp['disk'][6], max=tmp['disk'][1], min=tmp['disk'][2]),
		write=dict(avg=tmp['disk'][3]/tmp['disk'][6], max=tmp['disk'][4], min=tmp['disk'][5]),
		unit=UNIT
	)
 	ret['net'] = dict(
		recv=dict(avg=tmp['net'][0]/tmp['net'][6], max=tmp['net'][1], min=tmp['net'][2]),
		sent=dict(avg=tmp['net'][3]/tmp['net'][6], max=tmp['net'][4], min=tmp['net'][5]),
		unit=UNIT
	)
	return ret

def monitorit(name=None, device=None, nic=None, interval=1, wait=0, duration=60, status=False):
	'''
	Parameters:
	name: process name
	device: disk device name
	nic: network interface card
	interval: interval for capture CPU, Bandwidth, and Disk
	wait: interval for each capture
	duration: duration for monitoring
	status: print status or not

	Return:
	a dict looks like
	{
		'cpu': {'avg': 1.5, 'max': 2.0, 'min': 1.0},
		'disk': {
			'read': {'avg': 0.0, 'max': 0.0, 'min': 0.0},
			'write': {'avg': 0.0, 'max': 0.0, 'min': 0.0}
			'unit': 'MBytes/s'
		},
		'mem': {
			'avg': 83.00,
			'max': 83.00,
			'min': 83.007
		},
		'net': {
			'recv': {'avg': 0.06, 'max': 0.06, 'min': 0.06},
			'sent': {'avg': 0.07, 'max': 0.07, 'min': 0.07},
			'unit': 'MBytes/s'
		}
	}
	'''
	count = 0
	ret = {}
	st = time.time()
	tmp = {
		'cm': [0, 0, 0, 0, 0, 0, 0],	# the [:3] ([sum, max, min]) for cpu, [:3] for mem, the last is for recording count
		'disk': [0, 0, 0, 0, 0, 0, 0],	# [:3] for read, [3:] for write
		'net': [0, 0, 0, 0, 0, 0, 0]	# [:3] for recv, [3:] for send
	}
	info = {}
	def update(prev, curr):
		if count == 0:
			return [curr[0], curr[0], curr[0], curr[1], curr[1], curr[1], count+1]
		return [prev[0]+curr[0], max(prev[1],curr[0]), min(prev[2],curr[0]), prev[3]+curr[1], max(prev[4],curr[1]), min(prev[5],curr[1]), count+1]
	def sprint():
		print('%CPU\t%MEM\tRead\tWrite\tRecv\tSent')
		print('{cpu:.2f}\t{mem:.2f}\t{read:.2f}\t{write:.2f}\t{recv:.2f}\t{sent:.2f}\n'.format(**info))

	try:
		while True:
			#sprint('count: {0}'.format(count))
			cm = get_cpu_mem(name=name, interval=interval)
			tmp['cm'] = update(tmp['cm'], [cm.get('cpu'), cm.get('mem')])
			disk = get_disk_io(device=device, interval=interval)
			tmp['disk'] = update(tmp['disk'], [disk.get('read'), disk.get('write')])
			net = get_net_io(nic=nic, interval=interval)
			tmp['net'] = update(tmp['net'], [net.get('recv'), net.get('sent')])
			if status:
				info.update(cm)
				info.update(disk)
				info.update(net)
				sprint()

			count += 1
			if time.time() - st >= duration:
				break
			time.sleep(wait)
	except KeyboardInterrupt:
		print('')
	except Exception, e:
	 	print(e)
	finally:
		if count == 0:
			return {}
		if status:
			print("Summary:")
		ret = get_summary(tmp)

	return ret

def pretty_print(obj, _type='table'):
	if not isinstance(obj, dict):
		pp.pprint(obj)
	elif _type == 'json':
		print(json.dumps(obj, sort_keys=True, indent=4, separators=(',', ': ')))
	elif _type == 'table':
		print('%CPU\navg\tmax\tmin\n{avg:.2f}\t{max:.2f}\t{min:.2f}'.format(**obj['cpu']))
		print('%MEM\navg\tmax\tmin\n{avg:.2f}\t{max:.2f}\t{min:.2f}'.format(**obj['mem']))
		print('Disk read ({{unit}})\navg\tmax\tmin\n{avg:.2f}\t{max:.2f}\t{min:.2f}'.format(**obj['disk']['read']).format(unit=UNIT))
		print('Disk write ({{unit}})\navg\tmax\tmin\n{avg:.2f}\t{max:.2f}\t{min:.2f}'.format(**obj['disk']['write']).format(unit=UNIT))
		print('Network recv ({{unit}})\navg\tmax\tmin\n{avg:.2f}\t{max:.2f}\t{min:.2f}'.format(**obj['net']['recv']).format(unit=UNIT))
		print('Network sent ({{unit}})\navg\tmax\tmin\n{avg:.2f}\t{max:.2f}\t{min:.2f}'.format(**obj['net']['sent']).format(unit=UNIT))
	else:
		pp.pprint(obj)
		

if __name__ == '__main__':
	# print ps.test()
	# pp.pprint(system_info())
	# pp.pprint(monitorit(name='asd', device='vda2', nic='eth1', interval=1, wait=0, duration=20, status=True))
	# pp.pprint(monitorit(interval=1, wait=0, duration=20, status=True))
	parser = argparse.ArgumentParser(description='Performance measurement')
	parser.add_argument('-p', '--process', action='store', type=str, dest='name', default=None,
			help="The process name to be monitored")
	parser.add_argument('-d', '--device', action='store', type=str, dest='device', default=None,
			help="The disk device name to be monitored")
	parser.add_argument('-n', '--nics', action='store', type=str, dest='nic', default=None,
			help="The nic name to be monitored")
	parser.add_argument('-i', '--interval', action='store', type=int, dest='interval', default=1,
			help="The interval for capture CPU, Bandwidth, and Disk")
	parser.add_argument('-w', '--wait', action='store', type=int, dest='wait', default=0,
			help="The interval for each monitor")
	parser.add_argument('-u', '--duration', action='store', type=float, dest='duration', default=1,
			help="The duration(minutes) for monitoring")
	parser.add_argument('-s', '--status', action='store_true', dest='status', default=False,
			help="Print monitor status or not")
	parser.add_argument('-f', '--format', action='store', dest='format', default='table',
			help="Output format: (json, dict, table)")
	args = parser.parse_args()

	try:
		ret = monitorit(name=args.name, device=args.device, nic=args.nic, interval=args.interval, wait=args.wait, duration=int(args.duration*60), status=args.status)
	except:
		pass
	pretty_print(ret, args.format)

