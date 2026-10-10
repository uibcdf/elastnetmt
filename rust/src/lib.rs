//! Serial, owned-buffer ENM matrix kernels. No contact selection or spectral solver.
use numpy::ndarray::Array2;
use numpy::{IntoPyArray, PyArray2, PyReadonlyArray2};
use pyo3::exceptions::{PyMemoryError, PyValueError};
use pyo3::prelude::*;

fn zeros(rows: usize) -> PyResult<Vec<f64>> {
    let size = rows
        .checked_mul(rows)
        .ok_or_else(|| PyMemoryError::new_err("matrix size overflow"))?;
    let mut data = Vec::new();
    data.try_reserve_exact(size)
        .map_err(|_| PyMemoryError::new_err("matrix allocation failed"))?;
    data.resize(size, 0.0);
    Ok(data)
}

fn snapshot_values<T>(values: impl ExactSizeIterator<Item = T>) -> PyResult<Vec<T>> {
    let mut data = Vec::new();
    data.try_reserve_exact(values.len())
        .map_err(|_| PyMemoryError::new_err("input snapshot allocation failed"))?;
    data.extend(values);
    Ok(data)
}

fn contact_snapshot(contacts: PyReadonlyArray2<'_, bool>) -> PyResult<(usize, Vec<bool>)> {
    // NumPy bool permits any nonzero byte, unlike Rust bool's 0/1 validity.
    // Inspect a same-width uint8 view without constructing Rust bool references.
    let bytes = contacts.call_method1("view", ("uint8",))?;
    let bytes = bytes.extract::<PyReadonlyArray2<'_, u8>>()?;
    let view = bytes.as_array();
    let n = view.shape()[0];
    if view.shape()[1] != n {
        return Err(PyValueError::new_err("contacts must have shape (N, N)"));
    }
    for i in 0..n {
        if view[[i, i]] != 0 {
            return Err(PyValueError::new_err("contacts diagonal must be false"));
        }
        for j in 0..i {
            if (view[[i, j]] != 0) != (view[[j, i]] != 0) {
                return Err(PyValueError::new_err("contacts must be symmetric"));
            }
        }
    }
    // Snapshot even strided inputs before releasing the GIL. Never retain Python
    // buffers during detached computation or write through caller-owned arrays.
    Ok((n, snapshot_values(view.iter().map(|&value| value != 0))?))
}

fn kirchhoff(contacts: &[bool], n: usize) -> PyResult<Vec<f64>> {
    let mut out = zeros(n)?;
    for i in 0..n {
        let mut degree = 0.0;
        for j in 0..n {
            if contacts[i * n + j] {
                out[i * n + j] = -1.0;
                degree += 1.0;
            }
        }
        out[i * n + i] = degree;
    }
    Ok(out)
}

fn hessian(coords: &[f64], contacts: &[bool], n: usize) -> PyResult<Vec<f64>> {
    let dim = n
        .checked_mul(3)
        .ok_or_else(|| PyMemoryError::new_err("matrix size overflow"))?;
    let mut out = zeros(dim)?;
    for i in 0..n {
        for j in 0..n {
            if !contacts[i * n + j] {
                continue;
            }
            let d = [
                coords[3 * i] - coords[3 * j],
                coords[3 * i + 1] - coords[3 * j + 1],
                coords[3 * i + 2] - coords[3 * j + 2],
            ];
            let r2 = d[0] * d[0] + d[1] * d[1] + d[2] * d[2];
            if !r2.is_finite() || r2 <= 0.0 {
                return Err(PyValueError::new_err(
                    "contact distance squared must be finite and positive",
                ));
            }
            for a in 0..3 {
                for b in 0..3 {
                    let value = -d[a] * d[b] / r2;
                    out[(3 * i + a) * dim + 3 * j + b] = value;
                    out[(3 * i + a) * dim + 3 * i + b] -= value;
                }
            }
        }
    }
    Ok(out)
}

fn output<'py>(
    py: Python<'py>,
    dim: usize,
    values: Vec<f64>,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    let array = Array2::from_shape_vec((dim, dim), values)
        .map_err(|_| PyValueError::new_err("matrix shape overflow"))?;
    Ok(array.into_pyarray(py))
}

#[pyfunction]
fn build_kirchhoff<'py>(
    py: Python<'py>,
    contacts: PyReadonlyArray2<'py, bool>,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    let (n, snapshot) = contact_snapshot(contacts)?;
    let data = py.detach(move || kirchhoff(&snapshot, n))?;
    output(py, n, data)
}

#[pyfunction]
fn build_hessian<'py>(
    py: Python<'py>,
    coords: PyReadonlyArray2<'py, f64>,
    contacts: PyReadonlyArray2<'py, bool>,
) -> PyResult<Bound<'py, PyArray2<f64>>> {
    let (n, snapshot) = contact_snapshot(contacts)?;
    let view = coords.as_array();
    if view.shape() != [n, 3] || view.iter().any(|x| !x.is_finite()) {
        return Err(PyValueError::new_err(
            "coords must be finite with shape (N, 3)",
        ));
    }
    let positions = snapshot_values(view.iter().copied())?;
    let data = py.detach(move || hessian(&positions, &snapshot, n))?;
    output(py, n * 3, data)
}

#[pymodule]
fn _rust(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(build_kirchhoff, m)?)?;
    m.add_function(wrap_pyfunction!(build_hessian, m)?)?;
    m.add("NUM_THREADS", 1)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn laplacian_chain() {
        let contacts = [false, true, false, true, false, true, false, true, false];
        assert_eq!(
            kirchhoff(&contacts, 3).unwrap(),
            [1., -1., 0., -1., 2., -1., 0., -1., 1.]
        );
    }

    #[test]
    fn axial_spring_only_resists_axial_motion() {
        let out = hessian(&[0., 0., 0., 2., 0., 0.], &[false, true, true, false], 2).unwrap();
        assert_eq!(out[0], 1.);
        assert_eq!(out[3], -1.);
        assert_eq!(out[18], -1.);
        assert_eq!(out[21], 1.);
        assert_eq!(out.iter().filter(|x| **x != 0.).count(), 4);
    }

    #[test]
    fn empty_matrices() {
        assert!(kirchhoff(&[], 0).unwrap().is_empty());
        assert!(hessian(&[], &[], 0).unwrap().is_empty());
    }
}
