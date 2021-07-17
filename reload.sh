#!/bin/bash
rm mywebsite/ds/settings.py
cp settings.py mywebsite/ds/settings.py
rm mywebsite/static/miluogo/*.geojson
wget https://www.dropbox.com/s/ebg1wwb9f9r6ppf/social-pulse-milano.geojson -P mywebsite/static/miluogo/
wget https://www.dropbox.com/s/pomhzcilmqbw8ca/qaria_stazione.geojson -P mywebsite/static/miluogo/
wget https://www.dropbox.com/s/zg7hehl4umj5f9g/zonedecentramento.geojson -P mywebsite/static/miluogo/
rm mywebsite/static/instaseer/yolo.h5
wget https://www.dropbox.com/s/ykgbyrsj27vqi0w/yolo.h5 -P mywebsite/static/instaseer/
