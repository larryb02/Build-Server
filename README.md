# Build-Server

Proof of concept build server for C programs

# Architecture
###  API
HTTP Server REST API 
### Routes:
- builds
- artifacts  

For api documentation visit [here](localhost:8000/docs)
###  Agent
Long running process that manages jobs and workers
###  Builder
API for building C programs and generating artifacts  
###  Database
Postgresql server

The entry point of this application resides in /api/main.py this is where the http server and other core components, such as the agent are started.
