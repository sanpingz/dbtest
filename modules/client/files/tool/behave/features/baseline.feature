Feature: Baseline testing
	baseline run

	Background: clean DB
		Given stop cluster
		and clean disk
		and start cluster

	@1k
	Scenario: 1k record size testing
		Given cluster is ready
		When load data into cluster
		Then run the baseline cases
			|workload	|
			|1k_r100	|
			|1k_r50w50	|
			|1k_w100	|

	@5k
	Scenario: 5k record size testing
		Given cluster is ready
		When load data into cluster
		Then run the baseline cases
			|workload	|
			|5k_r100	|
			|5k_r50w50	|
			|5k_w100	|

	@32k
	Scenario: 32k record size testing
		Given cluster is ready
		When load data into cluster
		Then run the baseline cases
			|workload	|
			|32k_r100	|
			|32k_r50w50	|
			|32k_w100	|
