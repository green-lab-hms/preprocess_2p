#!/bin/bash
#SBATCH -t 0-12:00
#SBATCH -p short 
#SBATCH -J oasis_plane
#SBATCH -o oasis_plane_%j.log
#SBATCH -e oasis_plane_%j.log
#SBATCH -c 4
#SBATCH --mem=16G

F_mat=$1
g_init=$2
echo "Performing OASIS deconvolution on $F_mat with g_init=${g_init} and g_range=${g_range}."

module load matlab/2018b
matlab -batch "oasis('$F_mat', $g_init);"
