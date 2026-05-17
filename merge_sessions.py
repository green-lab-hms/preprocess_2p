import pandas as pd
import numpy as np
import anndata

def match_var_names(adata, sourcemap):
    md = adata.uns['metadata']
    key = {keyi: md[keyi] for keyi in ['mouse', 'date', 'session']}
    date = adata.uns['metadata']['date']
    ref_to_adata = sourcemap[str(key)].dropna()
    adata_to_ref = pd.Series(ref_to_adata.index.values, index=ref_to_adata)
    var_names = adata.var_names.map(adata_to_ref)
    return var_names

def mean_vars_col(adatas, col):
    df = pd.DataFrame()
    for i, adata in enumerate(adatas):
        df = pd.concat([df, adata.var[col]], axis=1)
    
    sr = df.astype(float).mean(axis=1, skipna=True)
    return sr

def mean_vars(adatas, var_names, columns):
    var = pd.DataFrame(index=var_names)
    for col in columns:
        var[col] = mean_vars_col(adatas, col)
    return var

def merge(adatas, sourcemap):
    # Assert all from same region
    regions = [adata.uns['metadata']['region'] for adata in adatas]
    assert len(set(regions)) == 1

    # Match var_names
    adatas = adatas.copy()
    for adata in adatas:
        adata.var_names = match_var_names(adata, sourcemap)
    
    # Concatenate along obs axis, append session id to obs
    sessions = [f"{adata.uns['metadata']['date']}_{adata.uns['metadata']['session']}" for adata in adatas]
    adata_m = anndata.concat(adatas, join='outer', axis=0, keys=sessions, label='session', fill_value=np.nan, merge=None)
    adata_m.obs_names_make_unique()  
    
    # Append maze to obs
    mazes = [maze_id(adata.uns['path']) for adata in adatas]    
    for session, maze in zip(sessions, mazes):
        adata_m.obs.loc[adata_m.obs.session==session, 'maze'] = maze
    
    # Take mean of vars, excluding UMAP projection
    columns = [col for col in adatas[0].var.columns if not col.startswith('Xumap')]
    adata_m.var = mean_vars(adatas, adata_m.var_names, columns)
    
    return adata_m