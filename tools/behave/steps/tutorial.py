from behave import *
from time import sleep

@given(u'some setup condition')
def step_impl(context):
	print('setup ... ')

@given(u'some other setup action')
def step_impl(context):
	sleep(3)
	print('another setup ... ')

@given('we have behave installed')
def step_impl(context):
	print('start to sleep')
	sleep(3)
	print('wake up')

@when('we implement a test')
def step_impl(context):
	assert True is not False

@then('behave will test it for us!')
def step_impl(context):
	assert context.failed is False

@then('sleep a while')
def step_impl(context):
	print('start to sleep')
	sleep(3)
	print('wake up')
