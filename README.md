## About The Project

The C2 Cloud is a robust web-based C2 framework, designed to simplify the life of penetration testers. It allows easy access to compromised backdoors, just like accessing an EC2 instance in the AWS cloud. It can manage several simultaneous backdoor sessions with a user-friendly interface. 

The C2 Cloud supports the following reverse shells. 

1. Reverse TCP
2. Reverse HTTP
3. Reverse HTTPS (configure it behind an LB) 

## Demo 
https://youtu.be/hrHT_RDcGj8

## Key Features
🔒 **Anywhere Access:** Reach the C2 Cloud from any location. <br>
🔄 **Multiple Backdoor Sessions:** Manage and support multiple sessions effortlessly. <br>
🖱️ **One-Click Backdoor Access:** Seamlessly navigate to backdoors with a simple click. <br>
📜 **Session History Maintenance:** Track and retain complete command and response history for comprehensive analysis. <br>

## Tech Stack  
🛠️ **Flask:** Serving web and API traffic, facilitating reverse HTTP(s) requests. <br>
🔗 **TCP Socket:** Serving reverse TCP requests for enhanced functionality. <br>
🌐 **Nginx:** Effortlessly routing traffic between web and backend systems. <br>
📨 **Redis PubSub:** Serving as a robust message broker for seamless communication. <br>
🚀 **Websockets:** Delivering real-time updates to browser clients for enhanced user experience. <br>
💾 **Postgres DB:** Ensuring persistent storage for seamless continuity. <br>

## Architecture 
<img width="1354" alt="c2_cloud_architecture_diagram" src="https://github.com/govindasamyarun/c2-cloud/assets/69586504/8349b580-89de-44dd-b18a-aa67d52ba39d">

## Application setup

* **Management port:** 9000 <br>
* **Reversse HTTP port:** 8000 <br>
* **Reverse TCP port:** 8888 <br>

1. Clone the repo
2. Execute docker-compose up -d to start the containers
   Note: The c2-api service will not start up until the database is initialized. If you receive 500 errors, please try after some time. 

## Credits 
Inspired by [Villain](https://github.com/t3l3machus/Villain), a CLI-based C2 developed by [Panagiotis Chartas](https://github.com/t3l3machus).

## License

Distributed under the MIT License. See LICENSE for more information. 

## Contact

* [LinkedIn](https://www.linkedin.com/in/arungovindasamy/)
* [Twitter](https://twitter.com/ArunGovindasamy)
