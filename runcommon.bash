 #!/bin/bash
 # arg1 : image name
 # arg2 : python script in app/
docker-compose --f docker-compose-dev.yml run $1 watchmedo auto-restart -d /app --patterns="*.py;*.crt;*.key;*.pem" --recursive -- python3 /app/common/$2
