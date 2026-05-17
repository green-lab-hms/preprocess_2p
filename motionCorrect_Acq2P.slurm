#!/bin/bash
#SBATCH -t 0-6:00
#SBATCH -p short 
#SBATCH -J motionCorr
#SBATCH -o motionCorrect_Acq2P_%j.log
#SBATCH -e motionCorrect_Acq2P_%j.log
#SBATCH -c 8
#SBATCH --mem=32G
#SBATCH --mail-type=end

channel=Green
while getopts c: option 
do
 case "${option}"
 in
 c) channel=${OPTARG};;
 esac
done

movPath=${@:$OPTIND:1}
echo "Motion correcting $movPath on channel ${channel}."

module load matlab/2020a
matlab -batch "motionCorrect_Acq2P('$movPath', '$channel')"
