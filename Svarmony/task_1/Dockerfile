FROM docker.io/clearlinux:latest

RUN mkdir -p /app
WORKDIR /app
COPY ./tester/build/tester /app
COPY ./tester/first.txt /app
COPY ./tester/second.txt /app
RUN chmod +x /app/tester
CMD [ "/app/tester" ]
