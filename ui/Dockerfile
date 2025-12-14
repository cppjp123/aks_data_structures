FROM nginx:alpine
# Clean default files
RUN rm -rf /usr/share/nginx/html/*
# Copy our web files
COPY index.html app.js styles.css /usr/share/nginx/html/
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]