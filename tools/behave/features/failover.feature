Feature: Failover testing
	traffic on

	Background: clean DB
		Given stop cluster
		and clean disk
		and start cluster

	@5k
	@75%
	@cold
	Scenario: failover with 75% traffic
		Given cluster is ready
		When load "2000000" records into cluster with "r50w50"
		Then keep "100%" traffic running "5" mins with "r50w50"
		And failover "30" mins with "75%" "r50w50" by "cold"
			"""
			keep "75%" traffic running "30" mins with "r50w50"
			stop "node01" instances
			start "node01" instances
			"""

	@5k
	@100%
	@cold
	Scenario: failover with 100% traffic
		Given cluster is ready
		When load "2000000" records into cluster with "r50w50"
		Then failover "30" mins with "100%" "r50w50" by "cold"
			"""
			keep "100%" traffic running "30" mins with "r50w50"
			stop "node01" instances
			start "node01" instances
			"""

	@5k
	@75%
	@hot
	Scenario: failover with 75% traffic
		Given cluster is ready
		When load "2000000" records into cluster with "r50w50"
		Then keep "100%" traffic running "5" mins with "r50w50"
		And failover "30" mins with "75%" "r50w50" by "hot"
			"""
			keep "75%" traffic running "30" mins with "r50w50"
			stop "node01" instances
			start "node01" instances
			"""

	@5k
	@100%
	@hot
	Scenario: failover with 100% traffic
		Given cluster is ready
		When load "2000000" records into cluster with "r50w50"
		Then failover "30" mins with "100%" "r50w50" by "hot"
			"""
			keep "100%" traffic running "30" mins with "r50w50"
			stop "node01" instances
			start "node01" instances
			"""
