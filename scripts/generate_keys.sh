#!/bin/bash

generate_api_key() {
    openssl rand -base64 32 | tr -d "/+=" | cut -c1-32
}

num_keys=1

if [ $# -eq 1 ]; then
    num_keys=$1
fi

for i in $(seq 1 $num_keys); do
    echo $(generate_api_key)
done
