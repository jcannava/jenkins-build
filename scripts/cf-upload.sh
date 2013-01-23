#!/bin/sh

# ./push.sh put images/fedora15_x86_64.img.gz "RCB OPS" fedora15_x86_64.img.gz

TMPFILE=`mktemp`

# SOURCE API AND USER_NAME HERE

curl -s -D - -H "X-Auth-Key: $API" -H "X-Auth-User: $USER_NAME" https://api.mosso.com/auth > $TMPFILE

STORAGE_URL="`cat $TMPFILE | grep ^X-Storage-Url | cut -d \" \" -f 2`"
AUTH_TOKEN="`cat $TMPFILE | grep ^X-Auth-Token | cut -d \" \" -f 2`"
#echo "Storage URL: $STORAGE_URL"
#echo " Auth Token: $AUTH_TOKEN"

if [ "$1" == "put" ]; then
    FNAME=$2
    CONTAINER="`echo $3 | sed 's/ /%20/g'`"
    DEST_FNAME="`echo $4 | sed 's/ /%20/g'`"
    if [ -z $4 ]; then
        echo "usage: put <local file name> <container name> <file name>"
        exit 1;
    fi
    MD5="`md5sum $FNAME | cut -d \" \" -f 1`"
    #echo "    MD5 Sum: $MD5"

    echo "Uploading $FNAME to cloudfiles container $3..."
    curl -s -X "PUT" -T "$FNAME" -D - -H "ETag: $MD5" -H "Content-Type: application/x-compressed" -H "X-Auth-Token: $AUTH_TOKEN" -H "X-Object-Meta-Author
: Jenkins" "${STORAGE_URL%?}/$CONTAINER/$DEST_FNAME" > /dev/null
    if [ $? -ne 0 ]; then
        echo "Upload of $FNAME failed"
        rm -f $TMPFILE
        exit 1
    fi
fi

rm -f $TMPFILE
