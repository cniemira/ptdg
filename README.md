Prometheus Test Data Generator
==============================

PTDG launches one or more listeners which produce test data that can be
scraped by a Prometheus collector. The listener is very simple and is not
a complete HTTP Server. It can, however, efficiently produce a very large
amount of data.

Basic usage is very simple:

    ptdg [-c COUNT] [-l IADDR] [-p PORTS] [-t TAGS]

By default, one listener on `0:9090` is started. It produces two metrics
(one test metric and an iteration counter) with no tags:

    $ ptdg
    -
    $ curl 0.0.0.0:9090/metrics
    # HELP iteration Value of iteration.
    # TYPE iteration counter
    iteration 1
    # HELP test_1 Value of test_1.
    # TYPE test_1 gauge
    test_1 0.2064769331133134

Tags can be added like so (note the escaped quotes if adding a complete
tag specification):

    $ ptdg -t foo=bar -t baz
    -
    $ curl 0.0.0.0:9090/metrics
    # HELP iteration Value of iteration.
    # TYPE iteration counter
    iteration 1
    # HELP test_1 Value of test_1.
    # TYPE test_1 gauge
    test_1{foo="bar"} 0.2084875079195172
    # HELP test_1 Value of test_1.
    # TYPE test_1 gauge
    test_1{baz="lorem"} 0.18845666560022567

To specify ports, you can use ranges (start-stop) or individual ports
or comma separated values for either:

    $ptdg -p 8001-8010,8020,8030,8040-8049

The above would result in a total of 22 listeners.
