from mouse_imaging import session as sess
from mouse_imaging import options
import numpy as np
import scipy.io
import subprocess
import importlib
import os
import time

importlib.reload(sess)
def oasis_sbatch(Fc, Fc_mat, g_init, ops):
    scipy.io.savemat(Fc_mat, {'Y': Fc, 'ops': ops})
    shell_script = f'sbatch $CODE/preprocess_2p/oasis_plane_RHEL9.slurm {Fc_mat} {g_init}'
    print(shell_script)
    out = subprocess.call(shell_script, shell=True)
    return out

def oasis_plane(key, ops, plane):
    path = sess.define_path(**key, ops=ops)
    md = sess.get_metadata(path)

    # Extract ops needed, and save with mat file later on
    oasis_ops = dict(baseline=ops['baseline'], prctile_baseline=ops['prctile_baseline'], 
        win_baseline=ops['win_baseline'], sig_baseline=ops['sig_baseline'],
        neucoeff=ops['neucoeff'], tau_s=ops['tau_s'], fs=md['volume_rate'],)

    # Load raw traces
    F = np.load(path['F_npy'].format(plane=plane))

    # Subtract neuropil
    Fneu = np.load(path['Fneu_npy'].format(plane=plane))
    Fc = F - Fneu * oasis_ops['neucoeff']

    # Subtract baseline
    Fb = sess.F_baseline(Fc, oasis_ops)
    Fc = Fc - Fb
    
    # If output mat file exists, rename to backup (otherwise script will not wait until matlab has finished)
    outfile = path['Fc_oasis_mat'].format(plane=plane)
    if os.path.isfile(outfile):
        os.rename(outfile, outfile + '.backup')
    
    # Run OASIS deconvolution (saves to mat file)
    tau_frames = oasis_ops['tau_s'] * oasis_ops['fs']
    g_init = np.exp(-1/tau_frames)
    Fc_mat = path['Fc_mat'].format(plane=plane)
    oasis_sbatch(Fc, Fc_mat, g_init, oasis_ops)

def main(mouse, date, session='session_1', ops=options.default_ops(), wait=True):
    key = dict(mouse=mouse, date=date, session=session)
    path = sess.define_path(**key)
    md = sess.get_metadata(path)
    planes = range(1, md['nslices']+1)
    
    for plane in planes:
        oasis_plane(key, ops, plane)

    if wait:
        # Wait until oasis has finished on all planes (wait for mat files to appear)
        outfiles = [path['Fc_oasis_mat'].format(plane=plane) for plane in planes]
        while not all([os.path.exists(outfile) for outfile in outfiles]):
            time.sleep(1)
        
        # Remove backup files
        for plane in planes:
            outfile = path['Fc_oasis_mat'].format(plane=plane)
            backupfile = outfile + '.backup'
            if os.path.isfile(backupfile):
                os.remove(backupfile)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Fluorescence trace processing into deconvolved signal.')
    parser.add_argument('--mouse', required=True, type=str)
    parser.add_argument('--date', required=True, type=str)
    parser.add_argument('--session', required=False, type=str, default='session_1')
    parser.add_argument('--ops', required=False, type=str, default='default_ops')
    args = vars(parser.parse_args())
    args['ops'] = getattr(options, args['ops'])()
    main(**args)
