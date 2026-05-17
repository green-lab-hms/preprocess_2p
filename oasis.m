function [C, S, B, G, Lam] = oasis(F_mat, g_init)
    % Run harvey_constrained_oasisAR1_jg on multiple fluorescence traces.
    %   F_mat: Y=(n_cells x n_time_bins)
    %   g_init: g value used to initialize fitting. Recommended to initialize g below optimal value.
    addpath(genpath('$CODE/preprocess_2p'));
    load(F_mat); % loads fluorescence traces into Y, ops into ops
    n_cells = size(Y, 1);
    C = zeros(size(Y));
    S = zeros(size(Y));
    B = zeros(size(Y,1),1);
    G = zeros(size(Y,1),1);
    Lam = zeros(size(Y,1),1);
%     Active_set = zeros(size(Y,1), cell(size(Y,1),1);
    parfor i=1:n_cells
        fprintf("Running OASIS on cell %i of %i.\n", i, n_cells)
        [c, s, b, g, lam, active_set] = harvey_constrained_oasisAR1(Y(i, :)', g_init);
        C(i,:) = c;
        S(i,:) = s;
        B(i,:) = b;
        G(i,:) = g;
        Lam(i,:) = lam;
%         Active_set{end+1} = active_set;
    end
    [p,f,e]=fileparts(F_mat);
    save(fullfile(p, [f '_oasis.mat']), '-v7.3')
end


