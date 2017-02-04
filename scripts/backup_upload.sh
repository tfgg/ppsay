#!/bin/bash -e
source ~/venv/bin/activate

d=`date -I`
n=backup_$d

mongodump -d news -o $n

time tar -jcvf $n.tar.bz2 $n

s3cmd sync $n.tar.bz2 s3://electionmentions/backups/

rm -rf $n
rm $n.tar.bz2

