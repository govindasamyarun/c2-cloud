# Use an official Python runtime as the base image
FROM python:3.9.1

# Install dependencies 
RUN apt-get update && apt-get install -y netcat

# Set the working directory in the container
WORKDIR /app

# Copy the Python requirements file
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy config file 
COPY config.yaml .

# Copy your WebSocket server code into the container
COPY c2_telegram.py .

# Expose the port 
EXPOSE 9999

# Start the websocket server
CMD ["python", "-u", "c2_telegram.py"]
