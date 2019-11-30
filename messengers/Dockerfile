# Use an official Python runtime as a parent image
FROM python:3.6.8

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
ADD . /app

# Install any needed packages
RUN pip install -r requirements.txt

CMD python server.py

# Make port 8081 available to the world outside this container
EXPOSE 8081
