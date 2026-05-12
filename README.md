## stomp.py

[![PyPI version](https://badge.fury.io/py/stomp.py.svg)](https://badge.fury.io/py/stomp.py)

***NOTE: MOVING TO CODEBERG - new repo: https://codeberg.org/jasonrbriggs/stomp.py***

"stomp.py" is a Python client library for accessing messaging servers (such as ActiveMQ Classic, ActiveMQ Artemis or RabbitMQ) using the [STOMP](http://stomp.github.io) protocol ([STOMP v1.0](http://stomp.github.io/stomp-specification-1.0.html), [STOMP v1.1](http://stomp.github.io/stomp-specification-1.1.html) and [STOMP v1.2](http://stomp.github.io/stomp-specification-1.2.html)). It can also be run as a standalone, command-line client for testing.  NOTE: Stomp.py has officially ended support for Python2.x. See [python3statement.org](http://python3statement.org/) for more information. 

### Quick Start

You can connect to a message broker running on the local machine, and send a message using the following example.

```python
import stomp

conn = stomp.Connection()
conn.connect('admin', 'password', wait=True)
conn.send(body=' '.join(sys.argv[1:]), destination='/queue/test')
conn.disconnect()
```

### Documentation and Resources

- [Main documentation](https://jasonrbriggs.codeberg.page/stomp.py.pages/)
- [API documentation](https://jasonrbriggs.codeberg.page/stomp.py.pages/api.html) - see [stomp.github.io](https://stomp.github.io) for details on the STOMP protocol itself
- A basic example of using stomp.py with a message listener can be found in the [quick start](https://jasonrbriggs.codeberg.page/stomp.py.pages/quickstart.html) section of the main documentation
- Description of the [command-line interface](https://jasonrbriggs.codeberg.page/stomp.py.pages/quickstart.html#command-line-client)
- [PyPi stomp.py page](https://pypi.org/project/stomp.py/)

The current version of stomp.py supports:

- Python 3.x (Python2 support ended as of Jan 2020)
- STOMP version 1.0, 1.1 and 1.2

There is also legacy 3.1.7 version using the old 3-series code (see [3.1.7 on PyPi](https://pypi.org/project/stomp.py/3.1.7/). This is no longer supported, but (at least as of 2018) there were still a couple of reports of this version still being used in the wild.

Note: stomp.py now follows [semantic versioning](https://semver.org):

- MAJOR version for incompatible API changes,
- MINOR version for functionality added in a backwards compatible manner, and
- PATCH version for backwards compatible bug fixes.



### Testing

stomp.py has been perfunctorily tested on:

- [RabbitMQ](https://www.rabbitmq.com/) ([test_rabbitmq.py](https://codeberg.org/jasonrbriggs/stomp.py/src/branch/dev/tests/test_rabbitmq.py))
- [Apache Activemq Classic](https://activemq.apache.org/components/classic/) ([test_activemq.py](https://codeberg.org/jasonrbriggs/stomp.py/src/branch/dev/tests/test_activemq.py))
- [Apache ActiveMQ Artemis](https://artemis.apache.org/) ([test_artemis.py](https://codeberg.org/jasonrbriggs/stomp.py/src/branch/dev/tests/test_artemis.py))
- [stompserver](https://manpages.debian.org/trixie/stompserver/stompserver.1.en.html) ([test_stompserver.py](https://codeberg.org/jasonrbriggs/stomp.py/src/branch/dev/tests/test_stompserver.py))

For testing locally, you'll need to install docker (or [podman](https://podman.io/)). Once installed:

#. Install dependencies:
        `poetry install`
#. Create the docker (or podman) image:
        `make docker-image` (or `make podman-image`)
#. Run the container:
        `make run-docker` (or `make run-podman`)
#. Run stomp.py unit tests:
        `make test`
#. Cleanup the container afterwards if you don't need it any more:
        `make remove-docker` (or `make remove-podman`)

If you want to connect to the test services locally (other than from the included tests), you'll want to add test domain names to your hosts file like so:

> 172.17.0.2  my.example.com  
> 172.17.0.2  my.example.org  
> 172.17.0.2  my.example.net  

If you're using `podman` and you want to access services via their private IP addresses, you'll want to run your commands with::

```bash
  podman unshare --rootless-netns <command>
```

so that <command> has access to the private container network. Service ports are also exposed to the host and can be accessed directly.
