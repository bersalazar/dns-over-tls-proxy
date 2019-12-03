FROM ubuntu:latest
EXPOSE 53
RUN apt update && apt install -y python2.7 
COPY server.py /
COPY cert.crt /
CMD ["/usr/bin/python2.7","server.py"]