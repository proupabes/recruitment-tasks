# Question 1.
Were thorough profile tests of application performance performed?

The information presented on the use of one CPU core is very general because there are different processors with different numbers of threads per core and different clock speeds.

More precise data will be needed. Did the data on the RAM used refer to DDR5 or DDR4? This has a big impact on data throughput.

It would also be useful to know what memory the data is stored on. Reading the saved data as well as saving them is important and this is affected by the speed of the disk.
It is worth telling specific information about the hard drives used and performing performance tests.

How have they tried to optimize the data transfer time?

What was the problem with applications processing two photos at the same time?

Which of the processes and libraries take the most space, CPU and RAM?




# Question 2.
Assuming that the application has been written in a stable and secure manner based on high standards and code quality as well as modularity.

First, I would conduct brain storming with the team to determine in which regions of the world we expect the greatest user activity, this is important information when creating a cloud based on location. It would also be necessary to initially determine the scope of funds that we can allocate to deploy the application. Also during such a meeting we would determine which clouds we want to choose. This is information that can be important for the company, so it is worth bringing it up in the team. There are known international clouds such as Azure, AWS, GCP, but also national clouds such as Oktawave for Poland.
We can combine the advantages of all clouds or share them on a percentage basis.

Assuming successful brain storming.
I would start documenting everything in LaTeX so that later we could easily keep clean and automate the documentation.
The combination of Lua with LaTeX can automatically pull data from the clouds into documentation.

After starting the documentation, I would start creating the file in Terraform using the best practices.
Separate file for variable declaration, separate file for variable definition, etc.


Having a well-created Terraform file to automate the creation of infrastructure, I would prepare various playbooks in Ansible to configure additional system parameters and manage systems.
If there were no obstacles, I would like to introduce Kubernetes management by Helm.

If our infrastructure does not yet have any pipelines in CD/CI, I would configure such a pipeline in the cloud to build applications and deploy after updating the code on the company's Gitea.

Based on the application, I would also introduce an automated testing system, but it also depends on the language in which the application is written, because certain frameworks can be integrated in the application code.
Selenium is useful for WEB testing, but it will not check most cases.

In the final phase, I would also integrate SonarQube and Sentry to collect error information and ElasticSearch to collect logs.



# Bonus 1:

If the client is not connected to the company's infrastructure, then he will not have access to support and software updates, which may threaten security and lead to operational errors.
Client will be full responsibility for any damage that may result from such action.

The question is what would happen in this cloud.
If the application was only to collect data and analyze it, scripts in any programming language and connection settings are enough.

If we would like to have some influence on the operation of the client's cloud, a third device can be introduced like Raspberry Pi, which would be a gateway for connecting for administrative purposes, e.g. via VPN WireGuard.



# Bonus 2:
Each large cloud, such as AWS or Azure, allows you to configure the infrastructure for such cases by properly setting load balancers that will divide the traffic into small parts.

This is just an example for AWS.
https://aws.amazon.com/elasticloadbalancing/


Otherwise, it would be necessary to integrate, e.g. pfSense and HAProxy as Load Balancer and Kubernetes.