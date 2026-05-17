def export_photostim_average_frames(adata, t_range=(-1, 2)):
    # Find frame numbers
    photostim_sequence = adata.uns['photostim_sequence']
    trig = an.trigger_df(adata.obs, trigger_t=photostim_sequence['t'], t_range=t_range, safe=False)
    ind0 = np.where(adata.uns['triggers']['scan2vr_idx'])[0][0] # first frame after VR start
    idyx = trig['idyx'] + ind0 + 1 # +1 for matlab indexing
    assert len(photostim_sequence) == len(idyx)

    groups = sorted(photostim_sequence['group'].unique())
    adata.uns['path']['photostim_frames_mat'] = os.path.join(adata.uns['path']['preprocessed_dir'], 'photostim', 'photostim_frames_{condition}.mat')
    session_mat = os.path.join(adata.uns['path']['raw2P_dir'], 'session.mat')

    # Export average frame for each stim group
    for group in groups:  
        idyx_i = idyx[photostim_sequence['group'] == group]
        # export_mat_frame_index(idyx_i, 'frameIndex.mat')
        frames_mat = adata.uns['path']['photostim_frames_mat'].format(condition=f'group{group}')
        mat = export_mat_frames(idyx_i, session_mat, frames_mat)

    # Export average from with stim groups shuffled
    sequence_shuffle = photostim_sequence_shuffle['group'].sample(frac=1, replace=False).values
    for group in groups:
        idyx_i = idyx[sequence_shuffle == group]
        frames_mat = adata.uns['path']['photostim_frames_mat'].format(condition=f'group{group}_shuffle')
        mat = export_mat_frames(idyx_i, session_mat, frames_mat)

    # Export average frame for correct right v correct left trials
    trials = adata.uns['trials'].iloc[1:] # No stimulation on the first trial
    assert len(trials) == len(photostim_sequence)
    photostim_sequence['world'] = trials['world'].values
    
    trial_keys = an.split_keys(trials, ['world'], constant=dict(correct=True))
    for trial_key in trial_keys:
        trial_idx = an.fetch_index(trials, trial_key)
        for group in groups:
            idyx_i = 


def main(mouse, date, session='session_1'):
    t0 = time.perf_counter()
    adata = load_as_anndata(mouse=mouse, date=date, session=session, recompute=False, save=False)

    # Compute average photostim frames
    export_photostim_average_frames(adata, t_range=(-2, 5))

    t1 = time.perf_counter()
    print('Time to export frames: %.2f' %(t1-t0))
    # adata.write(adata.uns['path']['adata_h5ad']) # if path is updated, might want to save
    
if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Export frames triggered on photostimulation.')
    parser.add_argument('--mouse', required=True, type=str)
    parser.add_argument('--date', required=True, type=str)
    parser.add_argument('--session', required=False, type=str, default='session_1')
    args = parser.parse_args()
    main(**vars(args))