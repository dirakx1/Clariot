#!/usr/bin/env bash
#
# Description:
#	This script is the entrypoint of a clariot container and is needed
# when building the container based on Dockerfile.flask
#

set -e

APPDIR="/app/"
APPNAME="clariot-test"

cd $APPDIR

if [ "$1" = 'uwsgi' ] || [ "${#}" -eq 0 ]; then
        # only do it once  
        #echo "[INFO] Running 'python manage.py db init'..."
        #python manage.py db init
        
        echo "[INFO] Running 'python manage.py db migrate'..."
        python3 manage.py db migrate
        
        echo "[INFO] Running 'python manage.py db upgrade'..."
        python3 manage.py db upgrade
 

	## start uWSGI
        uwsgi --master --http 0.0.0.0:8000 --manage-script-name --mount /=application:app        
else
	exec "$@"
fi
