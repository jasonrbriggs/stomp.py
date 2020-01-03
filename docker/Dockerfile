FROM debian

MAINTAINER Jason R Briggs <jasonrbriggs@gmail.com>

EXPOSE 8484

RUN apt update
RUN apt install -y rabbitmq-server
RUN apt install -y stompserver
RUN apt install -y activemq
RUN apt install -y vim
RUN apt install -y wget
RUN apt install -y haproxy

RUN rabbitmq-plugins enable rabbitmq_stomp

RUN ln -s /etc/activemq/instances-available/main/ /etc/activemq/instances-enabled/
RUN sed -i 's/<\/transportConnectors>/<transportConnector name="stomp" uri="stomp:\/\/0.0.0.0:62613"\/><transportConnector name="stomp+ssl" uri="stomp+ssl:\/\/0.0.0.0:62614"\/><\/transportConnectors>/g' /etc/activemq/instances-enabled/main/activemq.xml
RUN keytool -genkey -alias broker -keyalg RSA -keystore broker.ks -storepass changeit -dname "CN=test, OU=test, O=test, L=test, S=test, C=GB"
RUN keytool -export -alias broker -keystore broker.ks -file broker_cert -storepass changeit
ENV ACTIVEMQ_SSL_OPTS="-Djavax.net.ssl.keyStore=/broker.ks -Djavax.net.ssl.keyStorePassword=changeit"

RUN sed -i 's/port: .*/port: 63613/g' /etc/stompserver/stompserver.conf
RUN sed -i 's/host: .*/host: 172.17.0.2/g' /etc/stompserver/stompserver.conf

RUN echo "stomp.listeners.tcp.1 = 172.17.0.2:61613" > /etc/rabbitmq/rabbitmq.conf
RUN echo "loopback_users = none" >> /etc/rabbitmq/rabbitmq.conf

RUN openssl req -x509 -newkey rsa:2048 -keyout tmp/key1.pem -out tmp/cert1.pem -days 365 -nodes -subj "/CN=my.example.org"
RUN openssl req -x509 -newkey rsa:2048 -keyout tmp/key2.pem -out tmp/cert2.pem -days 365 -nodes -subj "/CN=my.example.com"
RUN cat tmp/cert1.pem tmp/key1.pem > tmp/myorg.pem
RUN cat tmp/cert2.pem tmp/key2.pem > tmp/mycom.pem

COPY haproxy.cfg /etc/haproxy/haproxy.cfg
COPY haproxy.sh /

EXPOSE 61613/tcp
EXPOSE 62613/tcp
EXPOSE 62614/tcp
EXPOSE 63613/tcp
EXPOSE 64613/tcp

#ENTRYPOINT /etc/init.d/activemq start && /etc/init.d/stompserver start && /etc/init.d/rabbitmq-server start && /haproxy.sh && /bin/bash
ENTRYPOINT /bin/bash