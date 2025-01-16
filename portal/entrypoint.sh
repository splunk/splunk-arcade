#!/bin/bash

flask db init
flask db migrate
flask db upgrade
splunk-py-trace python app.py