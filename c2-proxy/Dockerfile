FROM nginx:1.19.6

# # Copy default and nginx conf files  
COPY default.conf /etc/nginx/conf.d/
COPY nginx.conf /etc/nginx/

# Copy the source code to application home directory 
COPY . /usr/share/nginx

# Set the working directory 
WORKDIR /usr/share/nginx

# Expose ports 
EXPOSE 9000

# Start the application  
CMD ["nginx", "-g", "daemon off;"]
