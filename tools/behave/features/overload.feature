Feature: Overload testing
	traffic on

	Background: clean DB
		Given stop cluster
		and clean disk
		and start cluster
	@5k
	@capacity
	@simple
	@memory
	Scenario: capacity overload
		Given cluster is ready
		When load "2000000" records into cluster with "r50w50"
		Then capacity overload "30" mins with read "r50w50" and insert "i100" based on "2000000000" records
			"""
			keep "100%" traffic running "60" mins with "r50w50"
			load "2000000000" records into cluster with "i100"
			grow "node05" instances
			"""

	@5k
	@capacity
	@memory
	Scenario: capacity overload
		Given cluster is ready
		When load "2000000" records into cluster with "r50w50"
		Then capacity overload "60" mins with read "r50w50" and insert "i100" based on "2000000000" records
			"""
			keep "100%" traffic running "60" mins with "r50w50"
			load "2000000000" records into cluster with "i100"
			grow "node05" instances
			grow "node06" instances
			grow "node07" instances
			grow "node08" instances
			"""

	@5k
	@traffic
	Scenario: traffic overload
		Given cluster is ready
		When load "2000000" records into cluster with "r50w50"
		Then traffic overload base on "10" clients "10" threads repeat "10" with "5" mins and "r50w50" for each running
