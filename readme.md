[![Watch the video](https://img.youtube.com/vi/pEfbLCmB3Vg/sddefault.jpg)](https://www.youtube.com/watch?v=pEfbLCmB3Vg)


# Project Setup and Deployment

This guide provides instructions for setting up a development environment using Docker for running an Oracle Database, RabbitMQ, and two custom applications - a Tornado web application and a Slot Machine application.

## Prerequisites

Before you begin, ensure that you have the following prerequisites installed on your system:

- [Docker](https://www.docker.com/) - Version 20.10.0 or higher
- [curl](https://curl.se/) - For downloading scripts
- Internet connection - Required for downloading Docker images

## Getting Started

To get started, follow these steps:

1. Download and install Docker:

    ```bash
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    ```

2. Pull Docker images for Oracle Database, RabbitMQ, and Python:

    ```bash
    sudo docker pull container-registry.oracle.com/database/express:21.3.0-xe
    sudo docker pull rabbitmq:3-management
    sudo docker pull python:3.8
    ```

3. Clone the project repository:

    ```bash
    git clone https://github.com/DrZuse/slotmachine_microservices.git
    cd slotmachine_microservices
    ```

## Building and Running Docker Containers

### Build Tornado Application Docker Image

```bash
cd tornado-app
sudo docker build -t tornado-app .
```

### Build Slot Machine Application Docker Image

```bash
cd ../slotmachine-app
sudo docker build -t slotmachine-app .
```

### Create Docker Network

```bash
sudo docker network create mynetwork
```

### Run Oracle Database Container

```bash
sudo docker run --rm -d \
  --name oracle-db \
  --network mynetwork \
  -p 1521:1521 -p 5500:5500 \
  -e ORACLE_PWD=psWd123 \
  -e ORACLE_CHARACTERSET=AL32UTF8 \
  -v /opt/oracle/oradata \
  container-registry.oracle.com/database/express:21.3.0-xe
```

### Run RabbitMQ Container

```bash
sudo docker run --rm -d \
  --hostname my-rabbit \
  --name rabbitmq-container \
  --network mynetwork \
  -p 15672:15672 -p 5672:5672 \
  rabbitmq:3-management
```

### Run Tornado Application Container

```bash
sudo docker run --rm -d \
  --name tornado \
  --network mynetwork \
  -p 80:8888 -p 443:8888 \
  tornado-app
```

### Run Slot Machine Application Container

```bash
sudo docker run --rm -d \
  --name slotmachine \
  --network mynetwork \
  slotmachine-app
```

### View Running Containers

```bash
sudo docker ps --format 'table {{.Names}}\t{{.Command}}\t{{.Status}}'
```

This will display the names, commands, and status of the running Docker containers.

Now, your development environment is set up, and you can access the Tornado web application at http://localhost/ and the RabbitMQ management interface at http://localhost:15672/.

