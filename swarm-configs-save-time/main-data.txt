-----------------------------nginx.conf--------------------------------------------------------
worker_processes 1;
 
events { worker_connections 1024; }
 
http {
 
    sendfile on;
 
    upstream docker-nginx {
        server nginx:80;
    }
 
    upstream docker-apache {
        server apache:80;
    }
 
    server {
        listen 8080;
 
        location / {
            proxy_pass         http://docker-nginx;
            proxy_redirect     off;
            proxy_set_header   Host $host;
            proxy_set_header   X-Real-IP $remote_addr;
            proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Host $server_name;
        }
    }
 
    server {
        listen 8081;
 
        location / {
            proxy_pass         http://docker-apache;
            proxy_redirect     off;
            proxy_set_header   Host $host;
            proxy_set_header   X-Real-IP $remote_addr;
            proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header   X-Forwarded-Host $server_name;
        }
    }
}

---------------------------------------------------------------------------------------------
We set worker_processes explicitly to 1 which is the default value.
It is common practice to run 1 worker process per core.


The worker_connections sets the maximum number of simultaneous connections 
that can be opened by a worker process (default=1024).

The sendfile is usually essential to speed up any web server via passing the pointers
(without copying the whole object) straight to the socket descriptor.
However, we use NGINX as a reverse proxy to serve pages from an application server,
we can deactivate it.

The upstream directive in ngx_http_upstream_module defines a group of servers 
that can listen on different ports. So, the upstream directive is used to define a pool of servers.

Nginx can proxy requests to servers that communicate using the http(s), FastCGI,
SCGI, and uwsgi, or memcached protocols through separate sets of directives for 
each type of proxy (Module ngx_http_upstream_module).

After defining the upstream servers, we need to tell NGINX 
how to listen and how to react to requests.

The most straight-forward type of proxy involves handing off a request 
to servers that can communicate using http. This type of proxy is known as
a generic "proxy pass" and is handled by proxy_pass directive.

The proxy_pass directive is mainly found in location contexts, and it sets
the protocol and address of a proxied server. When a request matches a location
with a proxy_pass directive inside, the request is forwarded to the URL given by the directive.

The proxy_pass directive is what makes a configuration a reverse proxy. 
It specifies that all requests which match the location block (in this case 
the root / path) should be forwarded to a specific port on a specified host where the app is running.

In the above configuration snippet, no URI is given at the end of the server
in the proxy_pass definition. For definitions that fit this pattern, 
the URI requested by the client will be passed to the upstream server as-is.


So, if we try to access the host machine via port 8080, NGINX will act as a
reverse proxy and serve whatever is in the proxy_pass definition. 
In the above scenario, we have docker-nginx which is the name of 
one of our upstream servers, which means the nginx service will be served.

The request coming from NGINX on behalf of a client will look different than 
a request coming directly from a client. A big part of this is the headers that 
go along with the request. When NGINX proxies a request, it automatically makes
some adjustments to the request headers it receives from the client:

NGINX gets rid of any empty headers.
The "Host" header is re-written to the value defined by the $proxy_host variable.
This will be the IP address or name and port number of the upstream, directly
as defined by the proxy_pass directive.
------------------------------------------------------------------------------------------------------
Host, X-Real-IP, and X-Forwarded-For
To adjust or set headers for proxy connections, we can use the proxy_set_header directive. 
The proxy_set_header allows redefining or appending fields to the request header passed 
to the proxied server. The syntax looks like this:

proxy_set_header field value;

In the configuration, we're passing an unchanged "Host" request header field like this:

proxy_set_header Host $host;

The above request sets the "Host" header to the $host variable, which should 
contain information about the original host being requested. The X-Real-IP is set
to the IP address of the client so that the proxy can correctly make decisions or
log based on this information.

The X-Forwarded-For (XFF) header is a list containing the IP addresses of every 
server the client has been proxied through up to this point.

The XFF header is a standard header for identifying the originating IP address of 
a client connecting to a web server through an HTTP proxy or a load balancer. 
When traffic is intercepted between clients and servers, server access logs 
contain the IP address of the proxy or load balancer only. To see the original
IP address of the client, the XFF request header is used.

The XFF header is typically set by a proxy server or a load balancer to 
indicate who the real requester is.

This header is used for debugging, statistics, and generating location-dependent
content and by design it exposes privacy sensitive information, such as the IP
address of the client. Therefore the user's privacy must be kept in mind when deploying this header.

In our case, we set this to the $proxy_add_x_forwarded_for variable. 
This variable takes the value of the original XFF header retrieved from the 
client and adds the NGINX server's IP address to the end. In other words, 
the $proxy_add_x_forwarded_for variable is used to automatically append $remote_addr to any incoming XFF headers.



For more readable code, we could move the proxy_set_header directives 
out to the server or http context, allowing it to be referenced in more than one location:
----------------------------------------nginx.conf   with proxy_header--------------------------------------------------------------------
worker_processes 1;
  
events { worker_connections 1024; }

http {

    sendfile on;

    upstream docker-nginx {
        server nginx:80;
    }

    upstream docker-apache {
        server apache:80;
    }
    
    proxy_set_header   Host $host;
    proxy_set_header   X-Real-IP $remote_addr;
    proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header   X-Forwarded-Host $server_name;
    
    server {
        listen 8080;
 
        location / {
            proxy_pass         http://docker-nginx;
            proxy_redirect     off;
        }
    }
 
    server {
        listen 8081;
 
        location / {
            proxy_pass         http://docker-apache;
            proxy_redirect     off;
        }
    }
}

---------------------------------------------------------------------------------------------
FROM nginx:alpine
COPY nginx.conf /etc/nginx/nginx.conf
RUN apk update && apk add bash

---------Then, check its version---------------------------------------------------------------
$ docker build -t nginx-alpine .

$ docker run -t -i nginx-alpine /bin/bash
bash-4.4# nginx -v
nginx version: nginx/1.19.3

-------------------------------------------------------------------------------------------------
$ docker build -t reverseproxy .

$ docker images

