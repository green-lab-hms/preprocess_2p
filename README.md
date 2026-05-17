# How to set up calcium imaging preprocessing on O2 using Jonathan Green's pipeline

Written by Tarek Jabri

<br/><br/>
**Pre-installation note:**

To minimize the changes you have to make, it is best if you save your raw data in your folder in Tier1 in the following manner:

- Inside your folder, have a folder called "Behavior_Imaging_Data"
- Inside that folder, you want to have 3 folders: 2P, Virmen, Sync
- In 2P, the raw tiff files will be in: mouse_id/YYMMDD/session_i/
- In ScanImage, use the following name for your raw tiff files: session_WAVELENGTH_CHANNELS/FILTERS_DEPTH_BRAINREGION (suffixes will be added to them by ScanImage like _0001_0001).
    - e.g., if you are imaging PPC at 920nm and you have Green in channel 1 and Red in channel 2 and we are naming the filters used for each one of them as #1, then your file name will look like this: session_920nm_G1R1_150um_PPC
- In Virmen, the sessionData.mat file will be in: mouse_id/YYMMDD/session_i/
- In Sync, the files will be in: mouse_id/YYMMDD and named session_000i

Where "i" is the session number for each mouse on each day.

<br/><br/>
1. Create a folder in which you will pull the following JG GitHub repositories:

    > **_NOTE:_**  To minimize the changes necessary, it would be better if you put all of them in a folder called "code" in your O2 home directory.
    - Acquisition2P_class
    - functions
    - mouse_imaging
    - preprocess_2p
    - source_classifier_syt
    - ViRMEn_jg 
</p>

2. Create the conda environments:
    - mouse_imaging:
      
        > **_NOTE:_** ```mouse_imaging_env.yml``` is found in this repository.
        ```
        $ conda env create -f mouse_imaging_env.yml
        $ conda activate mouse_imaging
        $ conda develop <path-to-directory-containing-repositories>
        $ conda develop <path-to-Acquisition2P_class>
        $ conda develop <path-to-functions>
        $ conda develop <path-to-preprocess_2p>
        ```
        > **_NOTE:_**  You might need to uninstall `pynndescent` and then `pip install pynndescent==0.5.8`
    - suite2p:
        ```
        $ conda create --name suite2p python=3.8
        $ conda activate suite2p
        $ conda install conda-build
        $ conda develop <path-to-directory-containing-repositories>
        $ conda develop <path-to-Acquisition2P_class>
        $ conda develop <path-to-functions>
        $ conda develop <path-to-mouse_imaging>
        $ conda develop <path-to-preprocess_2p>
        $ conda develop <path-to-source_classifier_syt>
        $ conda develop <path-to-ViRMEn_jg>
        $ pip install suite2p==0.8.1
        $ pip install seaborn
        $ pip install anndata 
        $ pip install umap-learn
        $ pip install igraph 
        $ pip install pyabf
        $ pip install pyqt5==5.12.3
        $ pip install pyqtgraph==0.11.0
        $ pip install tifffile==2020.7.24
        $ pip install rastermap==0.1.3
        $ pip install numpy==1.21.5
        $ pip install numba==0.57.0
        ```
    - cellpose:
        ```
        $ conda create --name cellpose-0.0.2.8 python=3.7.0
        $ conda activate cellpose-0.0.2.8
        $ pip install cellpose==0.0.2.8
        $ pip uninstall urllib 
        $ pip install urllib3==1.26.6
        $ conda uninstall numpy 
        $ conda install numpy=1.19.2
        ```

3. In the O2 cluster terminal, open your ```.bashrc``` file and add the following lines:

    ```
    export SCRATCH=/n/scratch/users/FIRST_LETTER_OF_YOUR_HMS_ID/HMS_ID/Behavior_Imaging_Data
    export CODE=/home/HMS_ID/code
    export O2DATA=/n/data2/hms/neurobio/harvey/WHERE_YOU_WANT_TO_SAVE_THE_PREPROCESSED_DATA
    export TIER1DATA=/n/files/Neurobio/HarveyLab/Tier1/YOUR_FOLDER/Behavior_Imaging_Data
    export MATLABPATH="$HOME/code/Acquisition2P_class/personal/Jonathan:$HOME/code/mouse_imaging:$HOME/code/preprocess_2p"
    ```

    > **_NOTE:_** if you didn't save the repositories in $HOME/code/ you will need to change THE THREE PATHS in MATLABPATH.

    > **_NOTE:_** the "Jonathan" part in MATLABPATH is correct, you shouldn't remove it!


5. Request scratch storage by running in the command line from a login node:
    
    ```
    $ /n/cluster/bin/scratch_create_directory.sh
    ```

6. Generate a ssh key for the O2 transfer cluster:
    - In transfer terminal:
        
        ```
        $ ssh-keygen -t rsa
        ```
       
        > **_NOTE:_**  keep file and passphrase blank
    - In your O2 home directory:
        ```
        $ cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
        $ chmod 0600 ~/.ssh/authorized_keys
        $ chmod 0700 ~/.ssh
        ```

7. Permanently add 'transfer' (ECDSA) to the list of known hosts by using the transfer ssh from your O2 cluster terminal. To do that, copy a random small file from Tier1 to your scratch directory.
    ```
    $ ssh transfer rsync -rlDvuziht /n/files/Neurobio/HarveyLab/Tier1/PATH_TO_YOUR_TEST_FILE /n/scratch/users/FIRST_LETTER_OF YOUR_HMS_ID/HMS_ID/
    ```
    > **_NOTE:_** You will be asked to answer "yes" to adding the host and use two-factor authentification then you will get a warning that the list of known hosts was updated.

8. In the mouse_imaging repository, edit the following files as follows (CAPITAL words not found in unedited files need to be changed):
    - options.py:
        - line 12: ```ops['preprocessed_root'] = ['/n/data2/hms/neurobio/harvey/WHERE_YOU_WANT_TO_SAVE_THE_PREPROCESSED_DATA']```
        - if you didn't save the repos in a folder called "code" in your home directory and used a different file name for your scratch folder, change ```ops['raw_root']``` and ``` ops['convnet_mat']``` in lines 18 & 21.
    - printMazeName.m, change the path to ViRMEn_jg only if you didn't save the repos in a folder called "code" in your home directory.
    - session.py, change ```path['code_dir']``` in line 206 if you didn't save the repos in a folder called "code" in your home directory.
 </p>

9. In Acquisition2P_class, change path in line 12 of personal/Jonathan/motionCorrect_Acq2P.m to your path to Acquisition2P_class.

 </p>
<br/><br/>

**For testing:**

- Change the Tier1 path in .bashrc to:
  ```
  export TIER1DATA=/n/files/Neurobio/HarveyLab/Tier1/Jonathan/Behavior_Imaging_Data
  ```
    > **_NOTE:_** Remember to change this back to your path once done with the test session
- Exit the O2 cluster terminal and open a new one (to update the bashrc)
- Create folder in O2 home directory for preprocessing logs
- Copy over preprocessImaging_linearMaze_TJ.slurm to this folder
- Run sbatch command from inside this folder as follows: 
    ```
    $ sbatch preprocessImaging_linearMaze_TJ.slurm JG655 240822 session_1
    ```

**Reinstallation for RHEL 9 OS:**

- Pull updated origin main for repos with modifications
    - preprocess_2p (for RHEL9 scripts and oasis changes)
    - Acquisition2P_class (for recompiled mex files)
- Follow the instructions above with new name for environments
    - mouse_imaging_RHEL9
    - suite2p_RHEL9
    - cellpose-0.0.2.8_RHEL9