FROM debian

MAINTAINER Jason R Briggs <jasonrbriggs@gmail.com>

EXPOSE 8484

RUN apt update && apt install -y \
    activemq \
    haproxy \
    haproxy \
    rabbitmq-server \
    stompserver \
    vim \
    && rm -rf /var/lib/apt/lists/*

# rabbitmq setup
RUN rabbitmq-plugins enable rabbitmq_stomp
RUN echo "stomp.listeners.tcp.1 = 172.17.0.2:61613" > /etc/rabbitmq/rabbitmq.conf
RUN echo "loopback_users = none" >> /etc/rabbitmq/rabbitmq.conf

# activemq setup
RUN ln -s /etc/activemq/instances-available/main/ /etc/activemq/instances-enabled/
RUN sed -i 's/<\/transportConnectors>/<transportConnector name="stomp" uri="stomp:\/\/0.0.0.0:62613"\/><transportConnector name="stomp+ssl" uri="stomp+ssl:\/\/0.0.0.0:62614"\/><\/transportConnectors>/g' /etc/activemq/instances-enabled/main/activemq.xml
RUN keytool -genkey -alias broker -keyalg RSA -keystore broker.ks -storepass changeit -dname "CN=test, OU=test, O=test, L=test, S=test, C=GB"
RUN keytool -export -alias broker -keystore broker.ks -file broker_cert -storepass changeit
ENV ACTIVEMQ_SSL_OPTS="-Djavax.net.ssl.keyStore=/broker.ks -Djavax.net.ssl.keyStorePassword=changeit"

# stompserver setup
RUN sed -i 's/port: .*/port: 63613/g' /etc/stompserver/stompserver.conf
RUN sed -i 's/host: .*/host: 172.17.0.2/g' /etc/stompserver/stompserver.conf

# ssl setup
RUN openssl req -x509 -newkey rsa:2048 -keyout tmp/key1.pem -out tmp/cert1.pem -days 365 -nodes -subj "/CN=my.example.org"
RUN openssl req -x509 -newkey rsa:2048 -keyout tmp/key2.pem -out tmp/cert2.pem -days 365 -nodes -subj "/CN=my.example.com"
RUN cat tmp/cert1.pem tmp/key1.pem > tmp/myorg.pem
RUN cat tmp/cert2.pem tmp/key2.pem > tmp/mycom.pem

# haproxy
COPY haproxy.cfg /etc/haproxy/haproxy.cfg
COPY haproxy.sh /

# activemq artemis
COPY tmp/activemq-artemis-bin.tar.gz /
RUN tar -xvzf activemq-artemis-bin.tar.gz
RUN apache-artemis-2.13.0/bin/artemis create testbroker --user testuser --password password --allow-anonymous --no-amqp-acceptor --no-hornetq-acceptor --default-port 61619
RUN sed -i 's/acceptor name="stomp">tcp:\/\/0.0.0.0:61613/acceptor name="stomp">tcp:\/\/0.0.0.0:61615/g' testbroker/etc/broker.xml

# expose ports
EXPOSE 61613/tcp
EXPOSE 62613/tcp
EXPOSE 62614/tcp
EXPOSE 63613/tcp
EXPOSE 64613/tcp

ENTRYPOINT /bin/bash
