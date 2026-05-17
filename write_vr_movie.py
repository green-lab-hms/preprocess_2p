from mouse_imaging import session as sess
import matplotlib.animation as animation
import scipy.io
import matplotlib.pyplot as plt
import os

def plot_vr_movie(key, trial, fps=60):
    path = sess.define_path(**key)
    trial_str = '%03d' %trial
    data = scipy.io.loadmat(path['frameGrabs_mat'].format(trial=trial_str))
    frames = data['frameData']
    # frames = frames[:, :, 500:510]

    iterations = frames.shape[2]
    fig = plt.figure(figsize=(10, 6.7))
    ax = plt.gca()
    for spine in ['top', 'bottom', 'left', 'right']:
        ax.spines[spine].set_visible(False)
    ax.xaxis.set_visible(False)
    ax.yaxis.set_visible(False)

    def update_img(i):
        if (i)%10==0:
            print(f'Plotting frame {i+1} out of {iterations}.')
        elif i+1==iterations:
            print(f'Plotting frame {i+1} out of {iterations}.')
            
        im = ax.pcolormesh(frames[:, :, i], cmap='Greys_r')
        return im

    #legend(loc=0)
    ani = animation.FuncAnimation(fig, update_img, iterations, interval=16.7)
    writer = animation.writers['ffmpeg'](fps=60)
    
    filepath = os.path.join(path['frameGrabs_dir'], f'Trial#{trial_str}_{fps}fps.mp4')
    ani.save(filepath, writer=writer, dpi=30)
    print('Done writing frames.')
    return ani

def main(mouse=None, date=None, session=None, trial=None, fps=60):
    key = dict(mouse=mouse, date=date, session=session)
    plot_vr_movie(key, trial, fps=fps)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Fluorescence trace processing into deconvolved signal.')
    parser.add_argument('--mouse', required=True, type=str)
    parser.add_argument('--date', required=True, type=str)
    parser.add_argument('--session', required=False, type=str, default='session_1')
    parser.add_argument('--trial', required=True, type=int)
    parser.add_argument('--fps', required=False, type=int, default=60)
    args = vars(parser.parse_args())
    main(**args)