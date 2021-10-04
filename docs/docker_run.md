## Setting up a server from a Docker image

The beacon app is consisting of a **backend** that is used for:
- Creating and removing datasets
- Adding or removing variants for one of more samples of a dataset
- Loading demo data (not used in production, just in a test server)
- Updating the genes in the database

At the same time, the command `beacon run` starts a **frontend** server with the following API endpoints:
```
Endpoint           Methods    Rule
-----------------  ---------  ------------------------------
api_v1.add         POST       /apiv1.0/add
api_v1.delete      POST       /apiv1.0/delete
api_v1.info        GET        /apiv1.0/
api_v1.query       GET, POST  /apiv1.0/query
api_v1.query_form  GET, POST  /apiv1.0/query_form
```

A Docker image for creating both backend and frontend containers is available on [Docker Hub](https://hub.docker.com/repository/docker/clinicalgenomics/cgbeacon2).
Alternatively the Dockerfile used for creating the image is available in this repositiory.

A local image of the repository can be created by moving the Dockerfile in the root folder of the app and from the same location, in a terminal, running the following command:

```
docker build -t cgbeacon2 .
```

The container with the docker image contains only the beacon app and its required libraries. In order to work the container must be connected with at least one other container hosting a running mongodb instance.


## Setting up the app backend:

A simple running instance of the app backend connected to the database and ready to execute commands could be created in different ways. This is an example using docker-compose:

Create a file docker-compose.yml containing the following code:

```
version: '3'
# usage:
# sudo docker-compose build
# sudo docker-compose up
services:
  mongodb:
    image: mvertes/alpine-mongo
    container_name: mongodb
    ports:
      - '27017:27017'
    expose:
      - '27017'

  beacon-cli:
    environment:
      MONGODB_HOST: mongodb
    image: clinicalgenomics/cgbeacon2
    container_name: beacon-cli
    links:
      - mongodb
    stdin_open: true # docker run -i
    tty: true        # docker run -t
```

Run the containers and open an interactive shell for the backend by typing:
```
docker-compose run beacon-cli /bin/bash
```

To populate the database with demo data (dataset + case variants) type:
```
beacon add demo
```

Exit from the execution of the images by typing `exit`

## Starting an app server connected to the database

An app server instance connected to the server might be started in a similar way using Docker Compose. This is an example of a such server, listening for incoming requests on port 6000, from hosts outside the container.

Example of docker-compose.yml file:

```
version: '3'

services:
  mongodb:
    image: mvertes/alpine-mongo
    container_name: mongodb
    ports:
      - '27017:27017'
    expose:
      - '27017'

  beacon-web:
    environment:
      MONGODB_HOST: mongodb
    image: clinicalgenomics/cgbeacon2
    container_name: beacon-web
    links:
      - mongodb
    expose:
      - '6000'
    ports:
      - '6000:6000'
    command: bash -c 'beacon run --host 0.0.0.0'
```

Run the server as a service (detached mode) by typing
```
docker.compose up -d
```

The server should be now listing for requests. Test that it is working by sending a request to the beacon info endpoint from another terminal window:
```
curl -X GET 'http://127.0.0.1:6000/apiv1.0/'
```

Stop the server by typing:
```
docker.compose down
```
