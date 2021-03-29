#!/bin/bash
if [ -z "$1" ]
  then
    echo "Usage: ./runLinear.sh [Clients Issuing Queries]"
    exit 0
fi

set -m

C=$1
N=10 # How many peers

OUT="../out/linear/c$1/"
mkdir -p ${OUT}
rm ${OUT}*
./createPeer.sh ${N} 5 128

SUPER='python ../src/superPeer.py'
WEAK='python ../src/weakPeer.py'

# port base number
TBASE=30000
UBASE=40000
WBASE=50000

# QUERY 300 times
ACT='WAIT\n'
for i in {1..300}
do
    ACT=$ACT'QUERY data1.txt\n0\n'
done
ACT=$ACT'WAIT\nEXIT\n'

# start the indexing server

for (( i=1; i<=$N; i++ ))
do
    TPORT=$(( $TBASE + $i ))
    UPORT=$(( $UBASE + $i ))
    WPORT=$(( $WBASE + $i*2 ))

    # create lenear topology
    NEIGHBORS=''
    if [[ $i -eq 1 ]]
    then
        NEIGHBORS=${NEIGHBORS}' -n  127.0.0.1:'$(( $UPORT + 1 ))
        NEIGHBORS=${NEIGHBORS}' -n  127.0.0.1:'$(( $UBASE + $N ))
    elif [[ $i -eq $N ]]
    then
        NEIGHBORS=${NEIGHBORS}' -n  127.0.0.1:'$(( $UPORT - 1 ))
        NEIGHBORS=${NEIGHBORS}' -n  127.0.0.1:'$(( $UBASE + 1 ))
    else
        NEIGHBORS=${NEIGHBORS}' -n  127.0.0.1:'$(( $UPORT - 1 ))
        NEIGHBORS=${NEIGHBORS}' -n  127.0.0.1:'$(( $UPORT + 1 ))
    fi

    ${SUPER} -t ${TPORT} -u ${UPORT} ${NEIGHBORS} --ttl 5 > ${OUT}super${i}.txt 2>&1 &
    spids[${i}]=$!

    if [[ $i -gt $C ]]
    then
        ${WEAK} ${WPORT} --dir peer_folder${i} --server 127.0.0.1:${TPORT} > ${OUT}weak${i}.txt 2>&1 &
    else
        # Spawning clients with query commands
        echo -e $ACT | ${WEAK} ${WPORT} --dir peer_folder${i} --server 127.0.0.1:${TPORT} > ${OUT}weak${i}.txt 2>&1 &
    fi
    wpids[${i}]=$!
done

# wait for all peers
for pid in ${wpids[*]}; do
    wait $pid
done

echo "All peer is done!"
rm -rf peer_folder*

for pid in ${spids[*]}; do
    kill -SIGINT $pid
done