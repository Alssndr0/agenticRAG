# Use Python 3.10 slim image as the base
FROM python:3.10-slim

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV_ARG=false

ARG UID=1001
ARG GID=1001
# use the value to set the ENV var default (run time)
ENV UID=$UID
ENV GID=$GID

RUN addgroup --system --gid $GID sc && adduser --system -u $UID --gid $GID sc

ENV HOME=/home/sq-rg
ENV APP_HOME=/home/sq-rg/aimw
WORKDIR $HOME

# Create necessary directories and set permissions
RUN mkdir -p aimw logs
RUN chown -R $UID:$GID $HOME

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy the requirements file into the container
COPY requirements.txt $HOME/requirements.txt

# Using UV package manger for speed up
RUN pip install uv==0.6.5
# Install any needed packages specified in requirements.txt
RUN uv pip install --system --no-cache-dir --upgrade -r $HOME/requirements.txt

# Copy the entire app directory into the Docker image
COPY ./app $APP_HOME/app

# Copy run.sh and ensure it’s executable
COPY run.sh $APP_HOME
RUN chmod +x $APP_HOME/run.sh

# Switch to a non-root user, which is recommended by most cloud providers.
USER $UID

WORKDIR $APP_HOME

# Run the application with Uvicorn
CMD ["./run.sh"]
