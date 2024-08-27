## Running Locally

- You must mount your AWS credentials to the docker container (`/root/.aws/credentials`) at runtime.

## Deployment

1. `docker build -t ucsd_tennis_booking .`
2. `docker push [URI]:latest`