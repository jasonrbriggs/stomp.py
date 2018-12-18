FROM stomppy-base

MAINTAINER Jason R Briggs <jasonrbriggs@gmail.com>

EXPOSE 8484

ENTRYPOINT /etc/init.d/activemq start && /etc/init.d/stompserver start && /etc/init.d/rabbitmq-server start && /bin/bash
