FROM python:3.9.1

# Install dependencies 
RUN apt-get update && apt-get install -y netcat

# Copy the source code to application home directory 
ADD . /usr/src/app/

RUN chmod -R 764 /usr/src/app

# Set the working directory 
WORKDIR /usr/src/app/

# Install python dependencies 
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org --no-cache-dir -r /usr/src/app/requirements.txt

# Start the application  
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]
