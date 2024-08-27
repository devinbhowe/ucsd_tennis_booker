## Description

Automatic booking of tennis court reservations via recreation.ucsd.edu.
Uses Selenium to interface with the site. Configuration is stored in DynamoDB.
Docker images are uploaded to ECR and run nightly via Fargate.

## Running Locally

- You must mount your AWS credentials to the docker container (`/root/.aws/credentials`) at runtime.

## Deployment

1. `docker build -t ucsd_tennis_booking .`
2. `docker push [URI]:latest`