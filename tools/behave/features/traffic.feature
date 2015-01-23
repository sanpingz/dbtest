Feature: Traffic for non-performance testing
	traffic on

	Background: clean DB
		Given stop cluster
		and clean disk
		and start cluster

	@5k
	Scenario: keep traffic on
		Given cluster is ready
		When load "2000000" records into cluster with "r50w50"
		Then keep "100%" traffic running "10" mins with "r50w50"

