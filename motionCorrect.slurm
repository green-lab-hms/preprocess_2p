#!/bin/bash
#SBATCH -t 0-06:00
#SBATCH -p short 
#SBATCH -J motionCorr
#SBATCH -o motionCorrect_%j.log
#SBATCH -e motionCorrect_%j.log
#SBATCH -c 6
#SBATCH --mem=64G

channel=Green
use_common_motion_ref_file=false
while getopts "rc:" option 
do
 case "${option}"
 in
 c) channel=${OPTARG};;
 r) use_common_motion_ref_file=true;;
 esac
done

movPath=${@:$OPTIND:1}
echo "Motion correcting $movPath on channel ${channel}. Using external ref file: ${use_common_motion_ref_file}."

module load matlab/2020a
matlab -batch "motionCorrect_session('$movPath', '$channel', ${use_common_motion_ref_file})"
