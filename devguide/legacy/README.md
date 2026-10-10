# Historical ANM source

`old_anm.py.txt` preserves the original inactive Python 2 implementation byte
for byte, moved from `elastnetmt/model/old_anm.py` on 2026-10-10 under
[ElastNetMT #14](https://github.com/uibcdf/elastnetmt/issues/14).

It remains repository history, outside the installed Python package. Its direct
molecular manipulation and file writer are historical code, not supported tools.
The maintained models delegate molecular operations to public MolSysMT APIs.

The archived pure-Python distribution fixtures still describe their original
payload; their tests reconstruct this old source only in a temporary historical
fixture. Current native wheels reject the retired module.
