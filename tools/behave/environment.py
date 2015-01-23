def before_all(context):
	context.config.setup_logging()

def before_feature(context, feature):
	context.mark = feature.name.split()[0].lower()
