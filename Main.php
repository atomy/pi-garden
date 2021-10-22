<?php

require 'vendor/autoload.php';

$encoder = new \Nats\Encoders\JSONEncoder();
$options = new \Nats\ConnectionOptions();
$options->setHost('10.8.0.3')->setPort(4222);

$client = new \Nats\Connection($options);
$client->connect();

printf('Connected to NATS at %s' . PHP_EOL, $client->connectedServerId());

// Simple Subscriber.
$client->subscribe(
    'garden',
    function ($message) {
        $msg = $message->getBody();
        printf("Data: %s\r\n", $message->getBody());
        $fp = fopen('data.txt', 'a');
        fwrite($fp, $msg . PHP_EOL);
        fclose($fp);
    }
);

#while (true) {
#    sleep(1);
#}

$client->wait();
