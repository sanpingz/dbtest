Feature: Elasticity testing
	traffic on

	Background: clean DB
		Given stop cluster
		and clean disk
		and start cluster

	@5k
	@grow
	@4M
	Scenario: grow with 100% traffic
		Given cluster is ready
		When load "4000000" records into cluster with "r50w50"
		Then grow new node from "4" to "8" with "50" mins and "r50w50"
			"""
			keep "100%" traffic running "50" mins with "r50w50"
			grow "node05" instances
			grow "node06" instances
			grow "node07" instances
			grow "node08" instances
			"""

	@5k
	@grow
	@2M
	Scenario: grow with 100% traffic
		Given cluster is ready
		When load "2000000" records into cluster with "r50w50"
		Then grow new node from "4" to "8" with "50" mins and "r50w50"
			"""
			keep "100%" traffic running "50" mins with "r50w50"
			grow "node05" instances
			grow "node06" instances
			grow "node07" instances
			grow "node08" instances
			"""

	@5k
	@degrow
	@4M
	Scenario: degrow with 100% traffic
		Given start cluster size "8"
		And cluster is ready
		When load "4000000" records into cluster with "r50w50"
		Then degrow node from "8" to "4" with "50" mins and "r50w50"
			"""
			keep "100%" traffic running "50" mins with "r50w50"
			degrow "node05" instances
			degrow "node06" instances
			degrow "node07" instances
			degrow "node08" instances
			"""

	@5k
	@degrow
	@2M
	Scenario: degrow with 100% traffic
		Given start cluster size "8"
		And cluster is ready
		When load "2000000" records into cluster with "r50w50"
		Then degrow node from "8" to "4" with "50" mins and "r50w50"
			"""
			keep "100%" traffic running "50" mins with "r50w50"
			degrow "node05" instances
			degrow "node06" instances
			degrow "node07" instances
			degrow "node08" instances
			"""
