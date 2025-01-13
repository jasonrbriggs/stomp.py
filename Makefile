PYTHON:=`which python`
DESTDIR=/
PROJECT=stomp.py
PYTHON_VERSION_MAJOR:=$(shell $(PYTHON) -c "import sys;print(sys.version_info[0])")
PLATFORM := $(shell uname)
VERSION :=$(shell poetry version | sed 's/stomp.py\s*//g' | sed 's/\./, /g')
SHELL=/bin/bash
ARTEMIS_VERSION=2.38.0
TEST_CMD := $(shell podman network exists stomptest &> /dev/null && echo "podman unshare --rootless-netns poetry" || echo "poetry")

all: test install


.PHONY: docs


docs:
	cd docs && make html


install: updateversion test
	poetry update
	poetry build
	poetry export -f requirements.txt --dev -o requirements.txt


test:
	$(TEST_CMD) run pytest tests/ --cov=stomp --log-cli-level=DEBUG -v -ra --full-trace --cov-report=html:../stomppy-docs/htmlcov/ --html=tmp/report.html


testsingle:
	$(TEST_CMD) run pytest tests/${TEST} --log-cli-level=DEBUG -v -ra --full-trace


clean:
	rm -rf build/ MANIFEST dist/ *.egg-info/ tmp/ docker/tmp
	find . -name '*.pyc' -delete


release: updateversion
	poetry build
	poetry publish


docker/tmp/activemq-artemis-bin.tar.gz:
	mkdir -p docker/tmp
	wget http://www.apache.org/dist/activemq/activemq-artemis/${ARTEMIS_VERSION}/apache-artemis-${ARTEMIS_VERSION}-bin.tar.gz -O $@ || rm $@


ssl-setup:
	rm -f docker/tmp/broker*
	rm -f docker/tmp/expiredbroker*
	rm -f tmp/client*
	rm -f tmp/broker*
	rm -f tmp/expiredbroker
	mkdir -p docker/tmp
	mkdir -p tmp

	keytool -genkey -alias broker -keyalg RSA -keystore docker/tmp/broker.ks -storepass changeit -storetype pkcs12 -keypass changeit -dname "CN=test, OU=test, O=test, L=test, S=test, C=GB" -ext "san=ip:172.17.0.2"
	keytool -genkey -alias broker2 -keyalg RSA -keystore docker/tmp/broker2.ks -storepass changeit -storetype pkcs12 -keypass changeit -dname "CN=test2, OU=test2, O=test2, L=test2, S=test2, C=GB" -ext "san=ip:172.17.0.2"
	keytool -genkey -alias client -keyalg RSA -keystore tmp/client.ks -storepass changeit -storetype pkcs12 -keypass changeit -dname "CN=testclient, OU=testclient, O=testclient, L=testclient, S=testclient, C=GB"
	keytool -genkey -alias expiredbroker -keyalg RSA -keystore docker/tmp/expiredbroker.ks -storepass changeit -storetype pkcs12 -keypass changeit -dname "CN=test, OU=test, O=test, L=test, S=test, C=GB" -ext "san=ip:172.17.0.2" -startdate "2020/01/01 00:00:00" -validity 1
	openssl pkcs12 -in tmp/client.ks  -nodes -nocerts -out tmp/client.key -passin pass:changeit
	keytool -exportcert -rfc -alias client -keystore tmp/client.ks -file tmp/client.pem -storepass changeit
	keytool -import -alias client -keystore docker/tmp/broker.ts -file tmp/client.pem -storepass changeit -noprompt
	keytool -exportcert -rfc -alias broker -keystore docker/tmp/broker.ks -file tmp/broker.pem -storepass changeit
	keytool -exportcert -rfc -alias broker2 -keystore docker/tmp/broker2.ks -file tmp/broker2.pem -storepass changeit
	keytool -exportcert -rfc -alias expiredbroker -keystore docker/tmp/expiredbroker.ks -file tmp/expiredbroker.pem -storepass changeit


docker-image: docker/tmp/activemq-artemis-bin.tar.gz ssl-setup
	docker build --build-arg ARTEMIS_VERSION=${ARTEMIS_VERSION} -t stomppy docker/


run-docker:
	docker run --add-host="my.example.com:127.0.0.1" --add-host="my.example.org:127.0.0.1" --add-host="my.example.net:127.0.0.1" -d -p 61613:61613 -p 62613:62613 -p 62614:62614 -p 63613:63613 -p 64613:64613 -p 15674:15674 --name stomppy -it stomppy
	docker ps
	docker exec -it stomppy /bin/sh -c "/etc/init.d/activemq start"
	docker exec -it stomppy /bin/sh -c "/etc/init.d/stompserver start"
	docker exec -it stomppy /bin/sh -c "/etc/init.d/rabbitmq-server start"
	docker exec -it stomppy /bin/sh -c "start-stop-daemon --start --background --exec /usr/sbin/haproxy -- -f /etc/haproxy/haproxy.cfg"
	docker exec -it stomppy /bin/sh -c "testbroker/bin/artemis-service start"


remove-docker:
	docker stop stomppy
	docker rm stomppy


docker: remove-docker docker-image run-docker


podman-image: docker/tmp/activemq-artemis-bin.tar.gz ssl-setup
	podman build --build-arg ARTEMIS_VERSION=${ARTEMIS_VERSION} -t stomppy docker/


run-podman:
	podman network create --ipv6 --subnet 172.17.0.0/24 --subnet fddf:aaaa:bbbb:cccc::/64 stomptest
	podman run --network stomptest:ip=172.17.0.2 --add-host="my.example.com:127.0.0.1" --add-host="my.example.org:127.0.0.1" --add-host="my.example.net:127.0.0.1" -d -p 61613:61613 -p 62613:62613 -p 62614:62614 -p 63613:63613 -p 64613:64613 -p 15674:15674 --name stomppy -it stomppy
	podman ps
	podman exec -it stomppy /bin/sh -c "/etc/init.d/activemq start"
	podman exec -it stomppy /bin/sh -c "/etc/init.d/stompserver start"
	podman exec -it stomppy /bin/sh -c "/etc/init.d/rabbitmq-server start"
	podman exec -it stomppy /bin/sh -c "start-stop-daemon --start --background --exec /usr/sbin/haproxy -- -f /etc/haproxy/haproxy.cfg"
	podman exec -it stomppy /bin/sh -c "testbroker/bin/artemis-service start"


remove-podman:
	podman stop -i stomppy
	podman rm -vi stomppy
	podman network exists stomptest && podman network rm stomptest || :


podman: remove-podman podman-image run-podman
