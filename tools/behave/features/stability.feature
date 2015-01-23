Feature: Stability testing
	stability running

	Background: clean DB
		Given stop cluster
		and clean disk
		and start cluster

	@5k
	@100%
	Scenario: long time running
		Given cluster is ready
		When load "2000000" records into cluster with "r50w50"
		Then keep "100%" traffic running "720" mins with "r50w50"

	@5k
	@50%
	Scenario: long time running
		Given cluster is ready
		When load "2000000" records into cluster with "r50w50"
		Then keep "100%" traffic running "10" mins with "r50w50"
		Then keep "50%" traffic running "720" mins with "r50w50"
