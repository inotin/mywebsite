#!/bin/bash
rm mywebsite/static/miluogo/data/*.geojson
wget https://www.dropbox.com/s/pomhzcilmqbw8ca/qaria_stazione.geojson -P mywebsite/static/miluogo/data/
wget https://www.dropbox.com/s/ebg1wwb9f9r6ppf/social-pulse-milano.geojson -P mywebsite/static/miluogo/data/
wget https://www.dropbox.com/s/zg7hehl4umj5f9g/zonedecentramento.geojson -P mywebsite/static/miluogo/data/
rm mywebsite/static/instaSeer/models/yolo.h5
wget https://www.dropbox.com/s/ykgbyrsj27vqi0w/yolo.h5 -P mywebsite/static/instaSeer/models/
