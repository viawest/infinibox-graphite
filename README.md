# InfiniBox-Graphite
This project provides several Python scripts used to send InfiniBox operational data to Graphite. In addition, several 
Grafana dashboards have been provided to allow visualization of the data.

## Getting Started
There are three main functions that are required to setup this monitoring solution. Those functions are data collection, 
data storage, and data visualization. All three functions can be served by a single server or you can have a single
server for each function. We decided to go with the latter.

For the data collector, we use a Windows server that schedules the execution of these scripts. The scripts are responsible
for retrieving data from the InfiniBox storage arrays and Infinimetrics servers and then sends that data to our data
storage server. The data storage server is a Linux server running the time series database(TSDB) Graphite. While Graphite
does provide visualization capabilities, it is rudimentary in comparison to what Grafana offers. Grafana allows for easy
customization of dashboards and works across many different TSDBs.

## Requirements
* Infinimetrics 3.0.1 and newer
* Graphite 0.9.15 and newer
* Grafana 4.x and newer
  * Grafana "Pie Chart" plugin
* Python 2.7.x
* Python libraries
  * pyyaml
  * infinisdk
  * prettytable

## Data Collection\Transmission
These Python scripts collect information from the InfiniBox and Infinimetrics via API calls, formats the data, and then 
sends the data to Graphite. 

* **functions.py**: contains all functions used by the scripts in this project.

* **global_vars.py**: contains all global variables used by the scripts in this project.

* **settings.yaml**: contains graphite connection information per site.

* **infinibox_workload_graphite.py**: sends storage IOPS, throughput, and latency information to Graphite.

* **infinibox_space_graphite.py**: sends virtual and physical storage space utilization information to Graphite.

* **infinibox_hosts_workload_graphite.py**: sends host IOPS, throughput, and latency information to Graphite.

* **infinibox_volumes_workload_graphite.py**: send volume IOPS, throughput, and latency information to Graphite.

* **LICENSE.txt**: BSD 3-Clause open source license information.

## Dashboards
The Grafana directory includes several Grafana dashboards that you can import into your Grafana instance. The dashboards use 
a data source named "Graphite". Be sure the change the data source to fit your needs.

### Template Variables
All of the dashboards in this project contain two or more of the following template variables.  

* **site**: Location of InfiniBox storage array(s) or choose All  
* **host**: Hostname of InfiniBox array or choose All  
* **entity**: Choose volume, host, or both  
* **object**: Select volumes and hosts you want to view  

### Metrics
The following list provides a brief description of the dashboards and their associated metrics.  
* **Cloud_Storage_Entities.json**: Host and volume workload statistics.
  * **Volume\Host Throughput**: Read\Write bytes/sec
  * **Volume\Host IOPs**: Read\Write IOPs
  * **Volume\Host Latency**: Read\Write latency(ms)
* **Cloud_Storage_Performance.json**: InfiniBox workload statistics.
  * **Disk Throughput**: Read\Write bytes/sec
  * **Disk IOPs**: Read\Write IOPs
  * **Disk Latency**: Read\Write latency(ms)
* **Cloud_Storage_Space.json**: InfiniBox virtual and physical space utilization.
  * **Space Allocated**: Physical\virtual space allocated within pools. Not physical\virtual size of all pools.
  * **Space Used**: (Physical allocation within pools) + (snapshots) + (clones)
  * **Space Available**: (Physical\virtual Capacity) - (Physical\virtual allocation)
* **Cloud_Storage_Top_Offenders**: Top 5 hosts and volumes for each workload metric.
  * **Top Volume\Host Read\Write Throughput**: Read\Write bytes/sec
  * **Top Volume\Hhost Read\Write IOPs**: Read\Write IOPs
  * **Top Volume\Host Read\Write Latency**: Read\Write latency(ms)
* **Cloud_Storage_Space_All_Sites**: Aggregate virtual and physical space utilization for multiple locations/arrays.  
  * **InfiniBox Count**: Number of InfiniBox storage arrays being monitored
  * **InfiniBox List**: List of InfiniBox storage arrays being monitored. Format: site.hostname
  * **Virtual Capacity**: Virtual capacity
  * **Virtual Allocation**: Virtual allocation within pools. Not virtual size of all pools.
  * **Virtual Available**: (Virtual Capacity) - (Virtual allocation)
  * **Physical Capacity**: Physical capacity
  * **Physical Allocation**: Physical allocation within pools. Not physical size of all pools.
  * **Physical Used**: (Physical allocation within pools) + (snapshots) + (clones)
  * **Physical Available**: (Physical Capacity) - (Physical allocation)

## License
Please review the LICENSE.txt file
