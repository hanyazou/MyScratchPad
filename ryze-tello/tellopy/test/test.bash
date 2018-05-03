#!/bin/bash

source wait_wifi_connection.bash

wait_wifi_connection
python test.py
