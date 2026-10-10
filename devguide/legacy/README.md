# Retired ANM implementation

The inactive Python 2 `old_anm.py` was retired on 2026-10-10 under
[ElastNetMT #14](https://github.com/uibcdf/elastnetmt/issues/14). Its source remains
in [Git history](https://github.com/uibcdf/elastnetmt/blob/c4a9fb71c553f52081ebee23301a505ba7cd0509/elastnetmt/model/old_anm.py);
no implementation copy is maintained in the current tree.

Historical distribution tests create a synthetic resource placeholder in their
temporary fixtures. Current native wheels reject the retired module.
