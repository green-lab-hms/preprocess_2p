#!/bin/bash
#SBATCH -t 0-0:30
#SBATCH -p short
#SBATCH -J regsess
#SBATCH -o register_sessions_%j.log
#SBATCH -e register_sessions_%j.log
#SBATCH -c 1
#SBATCH --mem=64G # 128G

mouse=$1
dates=$2
min_corr=0.5

ichannel_source=1
ichannel_ref=1

source /n/app/conda2/etc/profile.d/conda.sh
conda activate caiman

echo "Registering sessions for ${mouse} dates ${dates} with min_corr=${min_corr}."
time python $CODE/preprocess_2p/register_sessions.py --mouse $mouse --dates ${dates} --ichannel_source $ichannel_source --ichannel_ref $ichannel_ref --min_corr $min_corr --keep_source last
